"""Exercise launcher release gates without compiler or signing credentials."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
from pathlib import Path

import pytest

from dev.windows_launcher import package

TOOLSET = "14.51.36231"
SDK = "10.0.26100.0"
THUMBPRINT = "AB" * 20


def _pe_fixture() -> bytes:
    image = bytearray(512)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 128)
    image[128:132] = b"PE\0\0"
    struct.pack_into("<H", image, 132, 0x8664)
    struct.pack_into("<H", image, 148, 240)
    struct.pack_into("<H", image, 152, 0x20B)
    struct.pack_into("<I", image, 152 + 108, 16)
    image[480:512] = b"native-code-placeholder".ljust(32, b"\0")
    return bytes(image)


UNSIGNED = _pe_fixture()


def _signed_fixture(unsigned: bytes = UNSIGNED) -> bytes:
    image = bytearray(unsigned)
    struct.pack_into("<I", image, 152 + 64, 77)
    struct.pack_into("<II", image, 152 + 112 + 4 * 8, len(image), 16)
    image += struct.pack("<IHH", 16, 0x200, 2) + b"fakecert"
    return bytes(image)


SIGNED = _signed_fixture()


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _build_metadata() -> dict:
    return {
        "architecture": "x64",
        "configuration_magic": "OJLCFG01",
        "configuration_stream": ":omnigent.config",
        "test_checkpoints": False,
        "pinned_toolchain": True,
        "reproducible_verified": True,
        "toolset_version": TOOLSET,
        "windows_sdk_version": SDK,
        "source_sha256": _digest(b"native-source"),
        "compiler_sha256": _digest(b"compiler"),
        "executable_sha256": _digest(UNSIGNED),
        "authenticode_signed": False,
    }


def _compiler(monkeypatch, metadata: dict, *, failure=None) -> list[dict]:
    calls = []

    def compile_candidate(output: Path, **options) -> Path:
        calls.append(options)
        output.write_bytes(UNSIGNED)
        output.with_suffix(".build.json").write_text(json.dumps(metadata), encoding="utf-8")
        if failure is not None:
            raise failure
        return output

    monkeypatch.setattr(package, "build_launcher", compile_candidate)
    return calls


def _prepare(monkeypatch, directory: Path) -> tuple[Path, dict]:
    metadata = _build_metadata()
    _compiler(monkeypatch, metadata)
    executable = package.prepare_candidate(directory, toolset_version=TOOLSET, sdk_version=SDK)
    return executable, metadata


def _manifest(directory: Path) -> dict:
    return json.loads((directory / "manifest.json").read_text(encoding="utf-8"))


def _signature(monkeypatch, signature: dict, *, during_verification=None) -> list[dict]:
    calls = []

    def verify(command, **options):
        calls.append({"command": command, **options})
        if during_verification is not None:
            during_verification()
        payload = {"type": "Authenticode", **signature}
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(package.subprocess, "run", verify)
    return calls


def test_candidate_is_unapproved_and_fingerprints_actual_build(monkeypatch, tmp_path):
    metadata = _build_metadata()
    calls = _compiler(monkeypatch, metadata)

    executable = package.prepare_candidate(tmp_path, toolset_version=TOOLSET, sdk_version=SDK)

    assert executable == tmp_path / package.FILENAME
    assert calls == [{"toolset_version": TOOLSET, "sdk_version": SDK, "verify_reproducible": True}]
    manifest = _manifest(tmp_path)
    assert manifest["schema"] == 1
    assert manifest["architecture"] == "amd64"
    assert manifest["filename"] == package.FILENAME
    assert manifest["sha256"] == _digest(executable.read_bytes())
    assert manifest["release_approved"] is False
    assert manifest["signing"] == {"status": "unsigned"}
    assert manifest["build"] == metadata
    assert manifest["candidate_signable_sha256"] == _digest(UNSIGNED)
    assert not (tmp_path / "manifest.json.tmp").exists()


@pytest.mark.parametrize("failure", [RuntimeError("compiler interrupted"), KeyboardInterrupt()])
def test_interrupted_rebuild_removes_previous_release_approval(monkeypatch, tmp_path, failure):
    (tmp_path / "manifest.json").write_text(
        json.dumps({"release_approved": True, "sha256": _digest(b"old-approved-asset")}),
        encoding="utf-8",
    )
    _compiler(monkeypatch, _build_metadata(), failure=failure)

    with pytest.raises(type(failure)):
        package.prepare_candidate(tmp_path, toolset_version=TOOLSET, sdk_version=SDK)

    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize(
    ("field", "unsafe"),
    [
        ("test_checkpoints", True),
        ("test_checkpoints", 0),
        ("pinned_toolchain", False),
        ("pinned_toolchain", 1),
        ("reproducible_verified", False),
        ("toolset_version", "14.44.35207"),
        ("windows_sdk_version", "10.0.22621.0"),
        ("architecture", "arm64"),
        ("executable_sha256", _digest(b"other-build")),
    ],
)
def test_candidate_rejects_unsafe_or_mismatched_build_metadata(
    monkeypatch, tmp_path, field, unsafe
):
    metadata = {**_build_metadata(), field: unsafe}
    _compiler(monkeypatch, metadata)

    with pytest.raises(RuntimeError):
        package.prepare_candidate(tmp_path, toolset_version=TOOLSET, sdk_version=SDK)

    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize(
    "signature",
    [
        {"status": "NotSigned", "thumbprint": THUMBPRINT},
        {"status": "HashMismatch", "thumbprint": THUMBPRINT},
        {"status": "UnknownError", "thumbprint": THUMBPRINT},
        {"status": "valid", "thumbprint": THUMBPRINT},
        {"status": "Valid", "thumbprint": "CD" * 20},
        {"status": "Valid", "thumbprint": ""},
        {"status": "Valid"},
        {"status": "Valid", "thumbprint": None},
    ],
)
def test_invalid_or_unexpected_signer_cannot_approve_candidate(monkeypatch, tmp_path, signature):
    _prepare(monkeypatch, tmp_path)
    previous = (tmp_path / "manifest.json").read_bytes()
    _signature(monkeypatch, signature)

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert (tmp_path / "manifest.json").read_bytes() == previous
    assert _manifest(tmp_path)["release_approved"] is False


@pytest.mark.parametrize("signature_type", ["Catalog", "None", "", None])
def test_valid_signature_requires_embedded_authenticode(monkeypatch, tmp_path, signature_type):
    executable, _ = _prepare(monkeypatch, tmp_path)
    executable.write_bytes(SIGNED)
    previous = (tmp_path / "manifest.json").read_bytes()
    _signature(
        monkeypatch,
        {"status": "Valid", "thumbprint": THUMBPRINT, "type": signature_type},
    )

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert (tmp_path / "manifest.json").read_bytes() == previous
    assert _manifest(tmp_path)["release_approved"] is False


@pytest.mark.parametrize("expected", ["", "AB" * 19, "G" * 40, "AB" * 21])
def test_finalization_requires_an_exact_certificate_thumbprint(monkeypatch, tmp_path, expected):
    calls = _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT})

    with pytest.raises(ValueError):
        package.finalize_signed(tmp_path, expected)

    assert calls == []
    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize(
    ("field", "unsafe"),
    [
        ("test_checkpoints", True),
        ("pinned_toolchain", False),
        ("reproducible_verified", False),
    ],
)
def test_finalization_rejects_unreviewable_build_before_signature_check(
    monkeypatch, tmp_path, field, unsafe
):
    _prepare(monkeypatch, tmp_path)
    manifest = _manifest(tmp_path)
    manifest["build"][field] = unsafe
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    calls = _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT})

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert calls == []
    assert _manifest(tmp_path)["release_approved"] is False


def test_finalization_fingerprints_signed_bytes_and_preserves_build_provenance(
    monkeypatch, tmp_path
):
    executable, provenance = _prepare(monkeypatch, tmp_path)
    executable.write_bytes(SIGNED)
    calls = _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT.lower()})

    finalized = package.finalize_signed(tmp_path, " ".join(["ab"] * 20))

    manifest = _manifest(tmp_path)
    assert finalized == executable.resolve()
    assert manifest["sha256"] == _digest(SIGNED)
    assert manifest["sha256"] != provenance["executable_sha256"]
    assert manifest["build"] == provenance
    assert manifest["candidate_signable_sha256"] == _digest(UNSIGNED)
    assert manifest["release_approved"] is True
    assert manifest["signing"] == {
        "status": "authenticode",
        "certificate_thumbprint": THUMBPRINT,
    }
    assert len(calls) == 1
    assert calls[0]["env"]["OMNIGENT_SIGNED_LAUNCHER"] == str(executable.resolve())
    assert calls[0]["check"] is True
    assert calls[0]["timeout"] == 60
    assert not (tmp_path / "manifest.json.tmp").exists()


def test_finalization_rejects_asset_mutation_during_signature_verification(monkeypatch, tmp_path):
    executable, _ = _prepare(monkeypatch, tmp_path)
    executable.write_bytes(SIGNED)
    _signature(
        monkeypatch,
        {"status": "Valid", "thumbprint": THUMBPRINT},
        during_verification=lambda: executable.write_bytes(b"unsigned-replacement"),
    )

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert _manifest(tmp_path)["release_approved"] is False


def test_finalization_rejects_original_payload_changes_even_for_expected_signer(
    monkeypatch, tmp_path
):
    executable, _ = _prepare(monkeypatch, tmp_path)
    changed = bytearray(UNSIGNED)
    changed[480] ^= 1
    executable.write_bytes(_signed_fixture(bytes(changed)))
    _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT})

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert _manifest(tmp_path)["release_approved"] is False


@pytest.mark.parametrize(
    ("field", "unsafe"),
    [("architecture", "arm64"), ("release_approved", True)],
)
def test_finalization_requires_an_unapproved_x64_candidate(monkeypatch, tmp_path, field, unsafe):
    executable, _ = _prepare(monkeypatch, tmp_path)
    executable.write_bytes(SIGNED)
    manifest = _manifest(tmp_path)
    manifest[field] = unsafe
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    previous = (tmp_path / "manifest.json").read_bytes()
    calls = _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT})

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert calls == []
    assert (tmp_path / "manifest.json").read_bytes() == previous


@pytest.mark.parametrize(
    "corruption",
    ["not_pe", "wrong_machine", "wrong_magic", "certificate_inside_image", "trailing_payload"],
)
def test_finalization_rejects_invalid_signed_image_layout(monkeypatch, tmp_path, corruption):
    executable, _ = _prepare(monkeypatch, tmp_path)
    malformed = bytearray(SIGNED)
    if corruption == "not_pe":
        malformed[:2] = b"NO"
    elif corruption == "wrong_machine":
        struct.pack_into("<H", malformed, 132, 0xAA64)
    elif corruption == "wrong_magic":
        struct.pack_into("<H", malformed, 152, 0x10B)
    elif corruption == "certificate_inside_image":
        struct.pack_into("<II", malformed, 152 + 112 + 4 * 8, 480, 16)
    else:
        malformed += b"unexpected-overlay"
    executable.write_bytes(malformed)
    _signature(monkeypatch, {"status": "Valid", "thumbprint": THUMBPRINT})

    with pytest.raises(RuntimeError):
        package.finalize_signed(tmp_path, THUMBPRINT)

    assert _manifest(tmp_path)["release_approved"] is False
