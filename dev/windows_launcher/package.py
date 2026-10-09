"""Prepare the optional Windows launcher resource before building a wheel.

Run from the repository root with ``python -m dev.windows_launcher.package``.
Signing happens in the release's external signing service, never in this helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path

from dev.windows_launcher.build import build_launcher

FILENAME = "private_job_launcher-x64.exe"
RESOURCE = Path(__file__).resolve().parents[2] / "omnigent/resources/windows_launcher"


def _signable_digest(content: bytes) -> str:
    """Fingerprint a PE allowing only checksum and appended signing data to change."""
    data = bytearray(content)
    if len(data) < 64 or data[:2] != b"MZ":
        raise RuntimeError("Launcher must be a PE32+ x64 executable")
    header = struct.unpack_from("<I", data, 60)[0]
    optional = header + 24
    if (
        optional + 240 > len(data)
        or data[header : header + 4] != b"PE\0\0"
        or struct.unpack_from("<H", data, header + 4)[0] != 0x8664
        or struct.unpack_from("<H", data, header + 20)[0] < 240
        or struct.unpack_from("<H", data, optional)[0] != 0x20B
        or struct.unpack_from("<I", data, optional + 108)[0] < 5
    ):
        raise RuntimeError("Launcher must be a PE32+ x64 executable")
    certificate_entry = optional + 112 + 8 * 4
    offset, size = struct.unpack_from("<II", data, certificate_entry)
    if offset or size:
        if (
            offset < optional + 240
            or offset % 8
            or size < 8
            or size % 8
            or offset + size != len(data)
        ):
            raise RuntimeError("Launcher certificate table must be aligned at EOF")
        position = offset
        while position < len(data):
            length, revision, kind = struct.unpack_from("<IHH", data, position)
            if length < 8 or position + length > len(data) or revision != 0x200 or kind != 2:
                raise RuntimeError("Launcher has an invalid certificate table")
            position += (length + 7) & ~7
        if position != len(data):
            raise RuntimeError("Launcher has invalid certificate padding")
        del data[offset:]
    data[optional + 64 : optional + 68] = b"\0" * 4
    data[certificate_entry : certificate_entry + 8] = b"\0" * 8
    data.extend(b"\0" * (-len(data) % 8))
    return hashlib.sha256(data).hexdigest()


def _write_manifest(destination: Path, manifest: dict) -> None:
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)


def prepare_candidate(destination: Path, *, toolset_version: str, sdk_version: str) -> Path:
    """Build and fingerprint an unsigned candidate with an explicit toolchain."""
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "manifest.json"
    # An interrupted rebuild must never retain an approval for an older asset.
    manifest_path.unlink(missing_ok=True)
    executable = build_launcher(
        destination / FILENAME,
        toolset_version=toolset_version,
        sdk_version=sdk_version,
        verify_reproducible=True,
    )
    build = json.loads(executable.with_suffix(".build.json").read_text(encoding="utf-8"))
    if (
        build.get("test_checkpoints") is not False
        or build.get("pinned_toolchain") is not True
        or build.get("reproducible_verified") is not True
        or build.get("architecture") != "x64"
        or build.get("toolset_version") != toolset_version
        or build.get("windows_sdk_version") != sdk_version
    ):
        raise RuntimeError(
            "Only a normal, pinned, reproducible x64 launcher build can be packaged"
        )
    content = executable.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != build["executable_sha256"]:
        raise RuntimeError("Launcher changed after compilation")
    _write_manifest(
        manifest_path,
        {
            "schema": 1,
            "architecture": "amd64",
            "filename": FILENAME,
            "sha256": digest,
            "candidate_signable_sha256": _signable_digest(content),
            "release_approved": False,
            "signing": {"status": "unsigned"},
            "build": build,
        },
    )
    return executable


def finalize_signed(destination: Path, signer_thumbprint: str) -> Path:
    """Approve externally signed bytes only after matching a trusted signer."""
    expected = signer_thumbprint.replace(" ", "").upper()
    if not re.fullmatch(r"[0-9A-F]{40}", expected):
        raise ValueError("Supply the expected signing certificate's SHA-1 thumbprint")
    executable = (destination / FILENAME).resolve()
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    build = manifest.get("build", {})
    if (
        manifest.get("schema") != 1
        or manifest.get("filename") != FILENAME
        or manifest.get("architecture") != "amd64"
        or build.get("architecture") != "x64"
        or manifest.get("release_approved") is not False
        or manifest.get("signing") != {"status": "unsigned"}
        or build.get("test_checkpoints") is not False
        or build.get("pinned_toolchain") is not True
        or build.get("reproducible_verified") is not True
    ):
        raise RuntimeError("A pinned, reproducible normal build manifest is required")
    content = executable.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if _signable_digest(content) != manifest.get("candidate_signable_sha256"):
        raise RuntimeError("Signed launcher does not match the compiled candidate")
    powershell = Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
    powershell /= "System32/WindowsPowerShell/v1.0/powershell.exe"
    command = (
        "$ErrorActionPreference='Stop'; "
        "$env:PSModulePath=$PSHOME+'\\Modules'; "
        "$s=Get-AuthenticodeSignature -LiteralPath $env:OMNIGENT_SIGNED_LAUNCHER; "
        "@{status=$s.Status.ToString(); thumbprint=$s.SignerCertificate.Thumbprint; "
        "type=$s.SignatureType.ToString()}"
        " | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-NonInteractive", "-Command", command],
        env={**os.environ, "OMNIGENT_SIGNED_LAUNCHER": str(executable)},
        capture_output=True,
        check=True,
        text=True,
        timeout=60,
    )
    signature = json.loads(result.stdout)
    actual = signature.get("thumbprint")
    if (
        signature.get("status") != "Valid"
        or signature.get("type") != "Authenticode"
        or not isinstance(actual, str)
        or actual.upper() != expected
    ):
        raise RuntimeError("Authenticode is invalid or the signer does not match release policy")
    if hashlib.sha256(executable.read_bytes()).hexdigest() != digest:
        raise RuntimeError("Launcher changed during signature verification")
    manifest["sha256"] = digest
    manifest["signing"] = {"status": "authenticode", "certificate_thumbprint": expected}
    manifest["release_approved"] = True
    _write_manifest(manifest_path, manifest)
    return executable


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=RESOURCE)
    parser.add_argument("--toolset-version")
    parser.add_argument("--sdk-version")
    parser.add_argument("--finalize-signed", action="store_true")
    parser.add_argument("--signer-thumbprint")
    arguments = parser.parse_args()
    if arguments.finalize_signed:
        if not arguments.signer_thumbprint:
            parser.error("--finalize-signed requires --signer-thumbprint")
        executable = finalize_signed(arguments.output_dir, arguments.signer_thumbprint)
    else:
        if not arguments.toolset_version or not arguments.sdk_version:
            parser.error("Candidate builds require --toolset-version and --sdk-version")
        executable = prepare_candidate(
            arguments.output_dir,
            toolset_version=arguments.toolset_version,
            sdk_version=arguments.sdk_version,
        )
    print(executable)


if __name__ == "__main__":
    main()
