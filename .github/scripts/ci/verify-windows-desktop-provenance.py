"""Inspect desktop ZIP/ASAR identity without launching Electron or claiming attestation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any, BinaryIO

MAX_ZIP_ENTRIES = 10000
MAX_ASAR_BYTES = 256 * 1024 * 1024
MAX_HEADER_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 64 * 1024
MAX_ASAR_ENTRIES = 50000


class DesktopProvenanceError(ValueError):
    """Packaged identity or archive metadata contradicts the expected build."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DesktopProvenanceError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_exact(source: BinaryIO, size: int) -> bytes:
    result = source.read(size)
    if len(result) != size:
        raise DesktopProvenanceError("Truncated ASAR metadata")
    return result


def _file_entry(index: dict[str, Any], path: str, payload_size: int) -> tuple[int, int, dict]:
    entry = index
    for component in path.split("/"):
        files = entry.get("files")
        if not isinstance(files, dict) or not isinstance(files.get(component), dict):
            raise DesktopProvenanceError(f"Missing packed ASAR entry: {path}")
        entry = files[component]
    offset, size = entry.get("offset"), entry.get("size")
    if (
        "link" in entry
        or entry.get("unpacked")
        or "files" in entry
        or not isinstance(offset, str)
        or not re.fullmatch(r"[0-9]+", offset)
        or type(size) is not int
        or size < 0
    ):
        raise DesktopProvenanceError(f"Invalid packed ASAR entry: {path}")
    offset_value = int(offset)
    if offset_value + size > payload_size:
        raise DesktopProvenanceError(f"ASAR entry outside payload: {path}")
    return offset_value, size, entry


def _package_from_asar(source: BinaryIO, asar_size: int) -> dict[str, Any]:
    marker, header_size, pickle_size, json_size = struct.unpack("<4I", _read_exact(source, 16))
    if (
        marker != 4
        or header_size != 8 + ((json_size + 3) & ~3)
        or pickle_size != header_size - 4
        or not 0 < json_size <= MAX_HEADER_BYTES
        or 8 + header_size > asar_size
    ):
        raise DesktopProvenanceError("Invalid or oversized ASAR header")
    index = json.loads(_read_exact(source, json_size), object_pairs_hook=_unique_object)
    if not isinstance(index, dict) or not isinstance(index.get("files"), dict):
        raise DesktopProvenanceError("ASAR index must contain a files object")
    pending = [index["files"]]
    count = 0
    while pending:
        files = pending.pop()
        count += len(files)
        if count > MAX_ASAR_ENTRIES:
            raise DesktopProvenanceError("Too many ASAR entries")
        for entry in files.values():
            if not isinstance(entry, dict):
                raise DesktopProvenanceError("Invalid ASAR index entry")
            if "files" in entry:
                if not isinstance(entry["files"], dict):
                    raise DesktopProvenanceError("Invalid ASAR directory")
                pending.append(entry["files"])
    payload_start = 8 + header_size
    payload_size = asar_size - payload_start
    offset, size, entry = _file_entry(index, "package.json", payload_size)
    if size > MAX_PACKAGE_BYTES:
        raise DesktopProvenanceError("Oversized packaged package.json")
    source.seek(payload_start + offset)
    packaged = _read_exact(source, size)
    integrity = entry.get("integrity")
    if (
        not isinstance(integrity, dict)
        or integrity.get("algorithm") != "SHA256"
        or integrity.get("hash") != hashlib.sha256(packaged).hexdigest()
    ):
        raise DesktopProvenanceError("Packaged package.json integrity mismatch")
    package = json.loads(packaged, object_pairs_hook=_unique_object)
    if not isinstance(package, dict):
        raise DesktopProvenanceError("Packaged package.json must be an object")
    if package.get("main") != "src/main.js":
        raise DesktopProvenanceError("Unexpected packaged desktop entry point")
    _, main_size, _ = _file_entry(index, "src/main.js", payload_size)
    if not main_size:
        raise DesktopProvenanceError("Empty desktop entry point")
    return package


def inspect_desktop(archive: Path, *, expected_version: str, source_sha: str) -> dict[str, Any]:
    """Check builder-authored identity and exact ZIP digest, not source authenticity."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise DesktopProvenanceError("A full lowercase source SHA is required")
    if not expected_version or any(character.isspace() for character in expected_version):
        raise DesktopProvenanceError("An explicit version without whitespace is required")
    if not archive.is_file() or archive.is_symlink():
        raise DesktopProvenanceError("An ordinary desktop ZIP file is required")
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) > MAX_ZIP_ENTRIES or len(names) != len(set(names)):
            raise DesktopProvenanceError("Too many or duplicate desktop ZIP entries")
        members = [name for name in names if name == "resources/app.asar"]
        if len(members) != 1:
            raise DesktopProvenanceError("Expected exactly one resources/app.asar")
        info = bundle.getinfo(members[0])
        if info.file_size > MAX_ASAR_BYTES:
            raise DesktopProvenanceError("Oversized app.asar")
        with bundle.open(info) as source:
            package = _package_from_asar(source, info.file_size)
    expected = {
        "name": "omnigent-desktop-electron",
        "version": expected_version,
        "omnigentSourceCommit": source_sha,
        "omnigentBuild": "dev",
        "main": "src/main.js",
    }
    for key, value in expected.items():
        if package.get(key) != value:
            raise DesktopProvenanceError(f"Packaged desktop identity mismatch: {key}")
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {
        "schema_version": 1,
        "artifact": archive.name,
        "size": archive.stat().st_size,
        "sha256": digest,
        "source_sha": source_sha,
        "source_basis": "embedded-desktop-metadata; not-trusted-attestation",
        "package": expected,
        "asar_member": members[0],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--source-sha", required=True)
    arguments = parser.parse_args(argv)
    try:
        report = inspect_desktop(
            arguments.archive,
            expected_version=arguments.expected_version,
            source_sha=arguments.source_sha,
        )
        print(json.dumps(report, sort_keys=True))
    except (
        OSError,
        ValueError,
        KeyError,
        RecursionError,
        struct.error,
        zipfile.BadZipFile,
    ) as error:
        print(f"Desktop provenance verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
