"""Bind a bundle inventory to inspected wheel identity, not trusted attestation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any

MANIFEST_NAME = "BUNDLE-PROVENANCE.json"
LOCKSTEP_PACKAGES = {"omnigent", "omnigent-client", "omnigent-ui-sdk"}
MAX_BUNDLE_ENTRIES = 10000
MAX_WHEEL_ENTRIES = 50000
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
SOURCE_FINGERPRINTS = (
    "omnigent/runner/content_search.py",
    "omnigent/inner/pi_windows.py",
    "omnigent/native/windows_cost_popup.py",
)


class ProvenanceError(ValueError):
    """The inspected bundle contradicts the requested release identity."""


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_member(archive: zipfile.ZipFile, name: str, limit: int = 1024 * 1024) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > limit:
        raise ProvenanceError(f"Oversized wheel metadata/resource: {name}")
    with archive.open(info) as source:
        value = source.read(limit + 1)
    if len(value) > limit:
        raise ProvenanceError(f"Oversized wheel metadata/resource: {name}")
    return value


def _wheel_identity(
    path: Path, expected_version: str, source_sha: str, repository_root: Path | None
) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) > MAX_WHEEL_ENTRIES:
            raise ProvenanceError(f"Too many wheel archive entries: {path.name}")
        if len(names) != len(set(names)):
            raise ProvenanceError(f"Duplicate wheel archive entries: {path.name}")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise ProvenanceError(f"Expected one wheel METADATA: {path.name}")
        metadata = BytesParser().parsebytes(_read_member(archive, metadata_names[0]))
        if len(metadata.get_all("Name", [])) != 1 or len(metadata.get_all("Version", [])) != 1:
            raise ProvenanceError(f"Ambiguous wheel Name/Version: {path.name}")
        name = re.sub(r"[-_.]+", "-", metadata["Name"]).lower()
        version = metadata["Version"]
        if name in LOCKSTEP_PACKAGES and version != expected_version:
            raise ProvenanceError(f"Lockstep wheel version mismatch: {name}={version}")
        filename_prefix = f"{name.replace('-', '_')}-{version}-"
        if not path.name.startswith(filename_prefix):
            raise ProvenanceError(f"Wheel filename/metadata mismatch: {path.name}")
        identity: dict[str, Any] = {"name": name, "version": version, "filename": path.name}
        if name == "omnigent":
            tree = ast.parse(_read_member(archive, "omnigent/_build_info.py"))
            commits = [
                node.value
                for node in tree.body
                if isinstance(node, (ast.Assign, ast.AnnAssign))
                and any(
                    isinstance(target, ast.Name) and target.id == "COMMIT_SHA"
                    for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                )
            ]
            if (
                len(commits) != 1
                or not isinstance(commits[0], ast.Constant)
                or commits[0].value not in ("", source_sha)
            ):
                raise ProvenanceError("Core embedded COMMIT_SHA does not match requested source")
            embedded_commit = commits[0].value
            fingerprints = []
            if not embedded_commit:
                if repository_root is None:
                    raise ProvenanceError(
                        "Empty embedded COMMIT_SHA requires Git source fingerprints"
                    )
                for member in SOURCE_FINGERPRINTS:
                    reference = subprocess.run(
                        ["git", "-C", str(repository_root), "show", f"{source_sha}:{member}"],
                        capture_output=True,
                        check=False,
                        timeout=10,
                    )
                    if reference.returncode:
                        raise ProvenanceError(f"Cannot resolve source fingerprint: {member}")
                    source = reference.stdout.replace(b"\r\n", b"\n")
                    packaged = _read_member(archive, member).replace(b"\r\n", b"\n")
                    if source != packaged:
                        raise ProvenanceError(f"Packaged source fingerprint mismatch: {member}")
                    fingerprints.append(
                        {
                            "path": member,
                            "lf_normalized_sha256": hashlib.sha256(source).hexdigest(),
                        }
                    )
            native_root = "omnigent/resources/windows_launcher/"
            native = json.loads(_read_member(archive, native_root + "manifest.json"))
            if not isinstance(native, dict):
                raise ProvenanceError("Native resource manifest must be an object")
            filename = native["filename"]
            if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
                raise ProvenanceError("Invalid native resource filename")
            asset_digest = hashlib.sha256(
                _read_member(archive, native_root + filename, 16 * 1024 * 1024)
            ).hexdigest()
            if asset_digest != native["sha256"]:
                raise ProvenanceError("Native resource digest mismatch")
            identity["embedded_commit_sha"] = embedded_commit
            identity["source_fingerprints"] = fingerprints
            identity["native_resource"] = {
                "filename": filename,
                "sha256": asset_digest,
                "release_approved": native.get("release_approved"),
                "signing": native.get("signing"),
            }
    return identity


def inspect_bundle(
    bundle: Path,
    *,
    expected_version: str,
    source_sha: str,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Inspect artifacts without importing their Python code or extracting archives."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ProvenanceError("A full lowercase source SHA is required")
    if not expected_version or any(character.isspace() for character in expected_version):
        raise ProvenanceError("An explicit version without whitespace is required")
    if not bundle.is_dir():
        raise ProvenanceError("Bundle directory is missing")
    if bundle.is_symlink() or bundle.is_junction():
        raise ProvenanceError("Linked bundle root is not supported")
    files = []
    for path in bundle.rglob("*"):
        if len(files) == MAX_BUNDLE_ENTRIES:
            raise ProvenanceError("Too many bundle entries")
        if path.is_symlink() or path.is_junction():
            raise ProvenanceError(f"Linked bundle entry is not supported: {path.name}")
        files.append(path)
    files.sort(key=lambda path: path.relative_to(bundle).as_posix())
    inventory = []
    for path in files:
        if path.is_file() and path != bundle / MANIFEST_NAME:
            inventory.append(
                {
                    "path": path.relative_to(bundle).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _digest(path),
                }
            )
    wheels = [
        _wheel_identity(path, expected_version, source_sha, repository_root)
        for path in sorted((bundle / "wheels").glob("*.whl"))
    ]
    for name in LOCKSTEP_PACKAGES:
        if sum(wheel["name"] == name for wheel in wheels) != 1:
            raise ProvenanceError(f"Expected exactly one lockstep wheel: {name}")
    sums = (bundle / "SHA256SUMS.txt").read_text(encoding="ascii")
    expected_sums = "".join(
        f"{entry['sha256']}  {Path(entry['path']).name}\n"
        for entry in inventory
        if entry["path"].startswith("wheels/") and entry["path"].endswith(".whl")
    )
    if sums != expected_sums:
        raise ProvenanceError("Existing wheel checksums do not match inspected bytes")
    return {
        "schema_version": 1,
        "expected_version": expected_version,
        "source_sha": source_sha,
        "source_basis": (
            "core-embedded-commit-or-selected-git-fingerprints; not-trusted-attestation"
        ),
        "wheels": wheels,
        "files": inventory,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        report = inspect_bundle(
            arguments.bundle_dir,
            expected_version=arguments.expected_version,
            source_sha=arguments.source_sha,
            repository_root=arguments.repository_root,
        )
        manifest_path = arguments.bundle_dir / MANIFEST_NAME
        if arguments.write_manifest:
            with manifest_path.open("x", encoding="utf-8", newline="\n") as output:
                output.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        else:
            if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
                raise ProvenanceError("Recorded provenance manifest is oversized")
            with manifest_path.open("rb") as source:
                recorded = source.read(MAX_MANIFEST_BYTES + 1)
            if len(recorded) > MAX_MANIFEST_BYTES:
                raise ProvenanceError("Recorded provenance manifest is oversized")
            if json.loads(recorded) != report:
                raise ProvenanceError("Recorded provenance does not match live bundle contents")
        print(
            json.dumps({"ok": True, "manifest": MANIFEST_NAME, "source_sha": report["source_sha"]})
        )
    except (
        OSError,
        ValueError,
        KeyError,
        SyntaxError,
        zipfile.BadZipFile,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"Bundle provenance verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
