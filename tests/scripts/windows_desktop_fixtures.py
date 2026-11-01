"""Small synthetic Electron ASAR artifacts for provenance tests."""

from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from pathlib import Path
from typing import Any

SOURCE_SHA = "a" * 40
VERSION = "0.20.0"
PACKAGE_NAME = "omnigent-desktop-electron"


def make_asar(
    *,
    package_metadata: dict[str, Any] | None = None,
    package_bytes: bytes | None = None,
    main_bytes: bytes = b"synthetic Electron entry point",
    include_main: bool = True,
) -> bytes:
    """Build a compact ASAR with package and main entries in its payload."""
    package = (
        package_metadata
        if package_metadata is not None
        else {
            "name": PACKAGE_NAME,
            "version": VERSION,
            "omnigentSourceCommit": SOURCE_SHA,
            "omnigentBuild": "dev",
            "main": "src/main.js",
        }
    )
    package_payload = (
        package_bytes
        if package_bytes is not None
        else json.dumps(package, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    files: dict[str, Any] = {
        "package.json": {
            "size": len(package_payload),
            "offset": "0",
            "integrity": {
                "algorithm": "SHA256",
                "hash": hashlib.sha256(package_payload).hexdigest(),
            },
        }
    }
    if include_main:
        files["src"] = {
            "files": {"main.js": {"size": len(main_bytes), "offset": str(len(package_payload))}}
        }
    index = {"files": files}
    header_json = json.dumps(index, separators=(",", ":"), sort_keys=True).encode("utf-8")
    aligned_json_size = (len(header_json) + 3) & ~3
    header_size = 8 + aligned_json_size
    prefix = struct.pack("<4I", 4, header_size, header_size - 4, len(header_json))
    return (
        prefix
        + header_json
        + bytes(aligned_json_size - len(header_json))
        + package_payload
        + main_bytes
    )


def make_desktop_archive(
    path: Path,
    *,
    package_metadata: dict[str, Any] | None = None,
    raw_asar: bytes | None = None,
    include_main: bool = True,
) -> Path:
    """Write a ZIP containing a synthetic desktop executable and app.asar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    asar = (
        raw_asar
        if raw_asar is not None
        else make_asar(package_metadata=package_metadata, include_main=include_main)
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Omnigent Desktop.exe", b"synthetic executable")
        archive.writestr("resources/app.asar", asar)
    return path
