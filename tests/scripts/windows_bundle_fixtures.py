"""Synthetic release artifacts for provenance unit and CLI scenarios."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

SOURCE_SHA = "a" * 40
VERSION = "0.20.0"


def make_bundle(root: Path, *, version: str = VERSION, commit: str = SOURCE_SHA) -> Path:
    wheels = root / "wheels"
    wheels.mkdir(parents=True)
    asset = b"synthetic native resource"
    for name in ("omnigent", "omnigent-client", "omnigent-ui-sdk"):
        filename = f"{name.replace('-', '_')}-{version}-py3-none-any.whl"
        with zipfile.ZipFile(wheels / filename, "w") as archive:
            archive.writestr(
                f"{name.replace('-', '_')}-{version}.dist-info/METADATA",
                f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n",
            )
            if name == "omnigent":
                archive.writestr("omnigent/_build_info.py", f"COMMIT_SHA: str = {commit!r}\n")
                archive.writestr(
                    "omnigent/resources/windows_launcher/manifest.json",
                    json.dumps(
                        {
                            "filename": "launcher.exe",
                            "sha256": hashlib.sha256(asset).hexdigest(),
                            "release_approved": False,
                            "signing": {"status": "unsigned"},
                        }
                    ),
                )
                archive.writestr("omnigent/resources/windows_launcher/launcher.exe", asset)
    (root / "install.ps1").write_bytes(b"synthetic installer\r\n")
    write_checksums(root)
    return root


def write_checksums(root: Path) -> None:
    lines = [
        f"{hashlib.sha256(wheel.read_bytes()).hexdigest()}  {wheel.name}\r\n"
        for wheel in sorted((root / "wheels").glob("*.whl"))
    ]
    (root / "SHA256SUMS.txt").write_bytes("".join(lines).encode("ascii"))


def replace_wheel_member(root: Path, name: str, contents: bytes | None) -> None:
    """Rewrite one synthetic core-wheel member and refresh its outer checksum."""
    wheel = next((root / "wheels").glob("omnigent-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        members = {info.filename: archive.read(info) for info in archive.infolist()}
    if contents is None:
        members.pop(name)
    else:
        members[name] = contents
    with zipfile.ZipFile(wheel, "w") as archive:
        for member, data in members.items():
            archive.writestr(member, data)
    write_checksums(root)
