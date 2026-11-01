"""Unit coverage for the Windows desktop archive provenance checker."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

from tests.scripts.windows_desktop_fixtures import (
    PACKAGE_NAME,
    SOURCE_SHA,
    VERSION,
    make_asar,
    make_desktop_archive,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/ci/verify-windows-desktop-provenance.py"
SPEC = importlib.util.spec_from_file_location("windows_desktop_provenance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def _rewrite_asar_index(raw: bytes, update: Any) -> bytes:
    """Change the ASAR header while preserving a valid length/alignment prefix."""
    _pickle, _header_size, _string_size, json_size = struct.unpack("<4I", raw[:16])
    start = 16
    header = json.loads(raw[start : start + json_size])
    payload = raw[start + _header_size - 8 :]
    update(header)
    encoded = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _rewrite_asar_header(encoded, payload)


def _rewrite_asar_header(encoded: bytes, payload: bytes) -> bytes:
    """Rebuild an ASAR prefix around raw header JSON and its existing payload."""
    aligned_size = (len(encoded) + 3) & ~3
    header_size = 8 + aligned_size
    return (
        struct.pack("<4I", 4, header_size, header_size - 4, len(encoded))
        + encoded
        + bytes(aligned_size - len(encoded))
        + payload
    )


def _asar_entry(index: dict[str, Any], path: str) -> dict[str, Any]:
    entry = index["files"]
    for component in path.split("/"):
        entry = entry[component].get("files", entry[component])
    return entry


def _inspect(path: Path) -> dict[str, Any]:
    return CHECKER.inspect_desktop(path, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_inspection_reports_actual_archive_digest_and_embedded_identity(tmp_path: Path) -> None:
    archive = make_desktop_archive(tmp_path / "desktop.zip")

    report = _inspect(archive)

    assert report == {
        "schema_version": 1,
        "artifact": archive.name,
        "size": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "source_sha": SOURCE_SHA,
        "source_basis": "embedded-desktop-metadata; not-trusted-attestation",
        "package": {
            "name": PACKAGE_NAME,
            "version": VERSION,
            "omnigentSourceCommit": SOURCE_SHA,
            "omnigentBuild": "dev",
            "main": "src/main.js",
        },
        "asar_member": "resources/app.asar",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "unexpected-desktop-name"),
        ("version", "0.19.0"),
        ("omnigentSourceCommit", "b" * 40),
        ("omnigentBuild", "release"),
        ("main", "src/missing.js"),
    ],
)
def test_inspection_rejects_mismatched_embedded_metadata(
    tmp_path: Path, field: str, value: str
) -> None:
    metadata = {
        "name": PACKAGE_NAME,
        "version": VERSION,
        "omnigentSourceCommit": SOURCE_SHA,
        "omnigentBuild": "dev",
        "main": "src/main.js",
    }
    metadata[field] = value
    archive = make_desktop_archive(tmp_path / "desktop.zip", package_metadata=metadata)

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


@pytest.mark.parametrize(
    "field", ["name", "version", "omnigentSourceCommit", "omnigentBuild", "main"]
)
def test_inspection_rejects_missing_embedded_identity_field(tmp_path: Path, field: str) -> None:
    metadata = {
        "name": PACKAGE_NAME,
        "version": VERSION,
        "omnigentSourceCommit": SOURCE_SHA,
        "omnigentBuild": "dev",
        "main": "src/main.js",
    }
    metadata.pop(field)
    archive = make_desktop_archive(tmp_path / "missing-field.zip", package_metadata=metadata)

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


def test_inspection_rejects_missing_main_entry(tmp_path: Path) -> None:
    archive = make_desktop_archive(tmp_path / "desktop.zip", include_main=False)

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


def test_inspection_rejects_empty_main_entry(tmp_path: Path) -> None:
    archive = make_desktop_archive(tmp_path / "empty-main.zip", raw_asar=make_asar(main_bytes=b""))
    with pytest.raises(CHECKER.DesktopProvenanceError, match="Empty desktop entry point"):
        _inspect(archive)


@pytest.mark.parametrize(
    "raw_asar",
    [
        b"not-an-asar" + bytes(64),
        _rewrite_asar_index(
            make_asar(),
            lambda index: index["files"]["package.json"].update({"offset": "999999"}),
        ),
        _rewrite_asar_index(
            make_asar(),
            lambda index: index["files"]["package.json"].update({"size": 999999}),
        ),
        _rewrite_asar_index(
            make_asar(),
            lambda index: index["files"]["src"]["files"]["main.js"].update({"offset": "999999"}),
        ),
        _rewrite_asar_index(
            make_asar(),
            lambda index: index["files"]["package.json"]["integrity"].update({"hash": "0" * 64}),
        ),
    ],
)
def test_inspection_rejects_invalid_prefix_bounds_and_integrity(
    tmp_path: Path, raw_asar: bytes
) -> None:
    archive = make_desktop_archive(tmp_path / "desktop.zip", raw_asar=raw_asar)

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


def test_inspection_rejects_duplicate_zip_member_and_missing_asar(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as output:
        output.writestr("resources/app.asar", make_asar())
        with pytest.warns(UserWarning, match="Duplicate"):
            output.writestr("resources/app.asar", make_asar())
    missing = tmp_path / "missing.zip"
    with zipfile.ZipFile(missing, "w") as output:
        output.writestr("Omnigent Desktop.exe", b"synthetic executable")

    for archive in (duplicate, missing):
        with pytest.raises(CHECKER.DesktopProvenanceError):
            _inspect(archive)


def test_inspection_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    package = (
        b'{"name":"omnigent-desktop-electron","name":"omnigent-desktop-electron",'
        b'"version":"0.20.0","omnigentSourceCommit":"' + SOURCE_SHA.encode() + b'",'
        b'"omnigentBuild":"dev","main":"src/main.js"}'
    )
    archive = make_desktop_archive(
        tmp_path / "duplicate-json.zip", raw_asar=make_asar(package_bytes=package)
    )

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


@pytest.mark.parametrize("package_bytes", [b"null", b"[]", b'"not an object"', b"{"])
def test_inspection_rejects_non_object_or_malformed_package_json(
    tmp_path: Path, package_bytes: bytes
) -> None:
    archive = make_desktop_archive(
        tmp_path / "invalid-package-json.zip",
        raw_asar=make_asar(package_bytes=package_bytes),
    )

    with pytest.raises(ValueError):
        _inspect(archive)


def test_inspection_rejects_duplicate_asar_index_json_keys(tmp_path: Path) -> None:
    raw = make_asar()
    _pickle, header_size, _string_size, json_size = struct.unpack("<4I", raw[:16])
    header_start = 16
    header_text = raw[header_start : header_start + json_size].decode("utf-8")
    files_start = len('{"files":')
    _files, files_end = json.JSONDecoder().raw_decode(header_text, files_start)
    files_json = header_text[files_start:files_end]
    duplicate_header = ('{"files":' + files_json + ',"files":' + files_json + "}").encode("utf-8")
    payload = raw[header_start + header_size - 8 :]
    archive = make_desktop_archive(
        tmp_path / "duplicate-index-key.zip",
        raw_asar=_rewrite_asar_header(duplicate_header, payload),
    )

    with pytest.raises(CHECKER.DesktopProvenanceError, match="Duplicate JSON key"):
        _inspect(archive)


@pytest.mark.parametrize(
    "update",
    [
        lambda index: index.update({"files": []}),
        lambda index: index["files"].update({"unexpected": "not an entry"}),
    ],
)
def test_inspection_rejects_unexpected_asar_index_types(tmp_path: Path, update: Any) -> None:
    archive = make_desktop_archive(
        tmp_path / "unexpected-index-type.zip",
        raw_asar=_rewrite_asar_index(make_asar(), update),
    )

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


@pytest.mark.parametrize(
    ("path", "field", "value"),
    [(path, "link", "somewhere") for path in ("package.json", "src/main.js")]
    + [(path, "unpacked", True) for path in ("package.json", "src/main.js")]
    + [(path, "size", True) for path in ("package.json", "src/main.js")]
    + [
        (path, "offset", value)
        for path in ("package.json", "src/main.js")
        for value in ("", "-1", "not-an-offset")
    ],
)
def test_inspection_rejects_invalid_packed_entries(
    tmp_path: Path, path: str, field: str, value: Any
) -> None:
    def update(index: dict[str, Any]) -> None:
        _asar_entry(index, path)[field] = value

    archive = make_desktop_archive(
        tmp_path / "invalid-packed-entry.zip",
        raw_asar=_rewrite_asar_index(make_asar(), update),
    )

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


def test_inspection_rejects_missing_package_integrity(tmp_path: Path) -> None:
    def update(index: dict[str, Any]) -> None:
        _asar_entry(index, "package.json").pop("integrity")

    archive = make_desktop_archive(
        tmp_path / "missing-integrity.zip",
        raw_asar=_rewrite_asar_index(make_asar(), update),
    )

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


@pytest.mark.parametrize(
    ("limit", "value"),
    [
        ("MAX_ZIP_ENTRIES", 1),
        ("MAX_ASAR_BYTES", 1),
        ("MAX_HEADER_BYTES", 1),
        ("MAX_PACKAGE_BYTES", 1),
        ("MAX_ASAR_ENTRIES", 1),
    ],
)
def test_inspection_enforces_archive_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str, value: int
) -> None:
    archive = make_desktop_archive(tmp_path / "limited.zip")
    monkeypatch.setattr(CHECKER, limit, value)

    with pytest.raises(CHECKER.DesktopProvenanceError):
        _inspect(archive)


def test_inspection_rejects_invalid_expected_identity(tmp_path: Path) -> None:
    archive = make_desktop_archive(tmp_path / "desktop.zip")

    with pytest.raises(CHECKER.DesktopProvenanceError):
        CHECKER.inspect_desktop(archive, expected_version=VERSION, source_sha="bad")
