"""Provenance consistency is separate from signing and bundle ownership."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from tests.scripts.windows_bundle_fixtures import (
    SOURCE_SHA,
    VERSION,
    make_bundle,
    replace_wheel_member,
    write_checksums,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/ci/verify-windows-bundle-provenance.py"
SPEC = importlib.util.spec_from_file_location("bundle_provenance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_inspection_binds_actual_metadata_commit_resource_and_all_files(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    report = CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)
    assert len(report["wheels"]) == 3
    assert len(report["files"]) == 5
    core = next(wheel for wheel in report["wheels"] if wheel["name"] == "omnigent")
    assert core["embedded_commit_sha"] == SOURCE_SHA
    assert core["native_resource"]["release_approved"] is False
    assert core["native_resource"]["signing"] == {"status": "unsigned"}
    assert "not-trusted-attestation" in report["source_basis"]


@pytest.mark.parametrize(
    ("version", "commit", "failure"),
    [("0.19.0", SOURCE_SHA, "version mismatch"), (VERSION, "b" * 40, "COMMIT_SHA")],
)
def test_inspection_refuses_wrong_actual_version_or_commit(
    tmp_path: Path, version: str, commit: str, failure: str
) -> None:
    bundle = make_bundle(tmp_path / "bundle", version=version, commit=commit)
    with pytest.raises(CHECKER.ProvenanceError, match=failure):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_inspection_refuses_missing_sdk_and_stale_wheel_checksums(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    sdk = next((bundle / "wheels").glob("omnigent_ui_sdk-*.whl"))
    saved = sdk.read_bytes()
    sdk.unlink()
    with pytest.raises(CHECKER.ProvenanceError, match="exactly one lockstep wheel"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)
    sdk.write_bytes(saved)
    (bundle / "SHA256SUMS.txt").write_text("stale\n", encoding="ascii")
    with pytest.raises(CHECKER.ProvenanceError, match="checksums"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_record_then_verify_detects_installer_tamper_without_overwriting_record(
    tmp_path: Path,
) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    arguments = [
        "--bundle-dir",
        str(bundle),
        "--expected-version",
        VERSION,
        "--source-sha",
        SOURCE_SHA,
    ]
    assert CHECKER.main([*arguments, "--write-manifest"]) == 0
    manifest = bundle / CHECKER.MANIFEST_NAME
    saved = manifest.read_bytes()
    assert b"\r\n" not in saved
    assert CHECKER.main(arguments) == 0
    (bundle / "install.ps1").write_bytes(b"different installer")
    assert CHECKER.main(arguments) == 1
    assert manifest.read_bytes() == saved
    assert CHECKER.main([*arguments, "--write-manifest"]) == 1
    assert json.loads(saved)["expected_version"] == VERSION


@pytest.mark.parametrize(
    ("member", "contents"),
    [
        ("omnigent/_build_info.py", b"COMMIT_SHA = str('untrusted')\n"),
        ("omnigent/_build_info.py", None),
        ("omnigent/resources/windows_launcher/manifest.json", b"not-json"),
        ("omnigent/resources/windows_launcher/manifest.json", b"[]"),
        ("omnigent/resources/windows_launcher/manifest.json", b"{}"),
        ("omnigent/resources/windows_launcher/launcher.exe", b"wrong bytes"),
        (
            "omnigent-0.20.0.dist-info/METADATA",
            b"Name: omnigent\nName: other\nVersion: 0.20.0\n",
        ),
    ],
)
def test_cli_refuses_malformed_metadata_without_importing_artifact_code(
    tmp_path: Path, member: str, contents: bytes | None
) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    replace_wheel_member(bundle, member, contents)
    assert (
        CHECKER.main(
            [
                "--bundle-dir",
                str(bundle),
                "--expected-version",
                VERSION,
                "--source-sha",
                SOURCE_SHA,
                "--write-manifest",
            ]
        )
        == 1
    )
    assert not (bundle / CHECKER.MANIFEST_NAME).exists()


def test_duplicate_archive_entries_are_refused(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    wheel = next((bundle / "wheels").glob("omnigent-*.whl"))
    with zipfile.ZipFile(wheel, "a") as archive, pytest.warns(UserWarning, match="Duplicate"):
        archive.writestr("omnigent/_build_info.py", "COMMIT_SHA = 'duplicate'\n")
    write_checksums(bundle)
    with pytest.raises(CHECKER.ProvenanceError, match="Duplicate wheel archive"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_file_archive_member_and_manifest_limits_fail_explicitly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    with monkeypatch.context() as patch:
        patch.setattr(CHECKER, "MAX_BUNDLE_ENTRIES", 1)
        with pytest.raises(CHECKER.ProvenanceError, match="Too many bundle"):
            CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)
    with monkeypatch.context() as patch:
        patch.setattr(CHECKER, "MAX_WHEEL_ENTRIES", 1)
        with pytest.raises(CHECKER.ProvenanceError, match="Too many wheel"):
            CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)
    arguments = [
        "--bundle-dir",
        str(bundle),
        "--expected-version",
        VERSION,
        "--source-sha",
        SOURCE_SHA,
    ]
    assert CHECKER.main([*arguments, "--write-manifest"]) == 0
    monkeypatch.setattr(CHECKER, "MAX_MANIFEST_BYTES", 1)
    assert CHECKER.main(arguments) == 1


def test_wheel_filename_must_match_actual_metadata(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    wheel = next((bundle / "wheels").glob("omnigent_client-*.whl"))
    wheel.rename(wheel.with_name("other-0.20.0-py3-none-any.whl"))
    write_checksums(bundle)
    with pytest.raises(CHECKER.ProvenanceError, match="filename/metadata mismatch"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_oversized_metadata_member_fails_before_parsing(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    replace_wheel_member(bundle, "omnigent/_build_info.py", b"#" * (1024 * 1024 + 1))
    with pytest.raises(CHECKER.ProvenanceError, match="Oversized wheel"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_detected_junction_is_refused_before_inventory_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = make_bundle(tmp_path / "bundle")
    original = Path.is_junction
    monkeypatch.setattr(
        Path, "is_junction", lambda path: path == bundle / "wheels" or original(path)
    )
    with pytest.raises(CHECKER.ProvenanceError, match="Linked bundle entry"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=SOURCE_SHA)


def test_empty_build_commit_requires_matching_actual_git_blob_fingerprints(tmp_path: Path) -> None:
    repository = tmp_path / "source"
    repository.mkdir()

    def git(*arguments: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(repository), *arguments])

    git("init", "-q")
    for member in CHECKER.SOURCE_FINGERPRINTS:
        path = repository / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SYNTHETIC_SOURCE = 1\n")
    git("add", "--", "omnigent")
    git(
        "-c",
        "user.name=Synthetic",
        "-c",
        "user.email=synthetic@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "synthetic",
    )
    sha = git("rev-parse", "HEAD").decode("ascii").strip()
    bundle = make_bundle(tmp_path / "bundle", commit="")
    for member in CHECKER.SOURCE_FINGERPRINTS:
        replace_wheel_member(bundle, member, b"SYNTHETIC_SOURCE = 1\r\n")
    with pytest.raises(CHECKER.ProvenanceError, match="requires Git source fingerprints"):
        CHECKER.inspect_bundle(bundle, expected_version=VERSION, source_sha=sha)
    report = CHECKER.inspect_bundle(
        bundle, expected_version=VERSION, source_sha=sha, repository_root=repository
    )
    core = next(wheel for wheel in report["wheels"] if wheel["name"] == "omnigent")
    assert core["embedded_commit_sha"] == ""
    assert len(core["source_fingerprints"]) == len(CHECKER.SOURCE_FINGERPRINTS)
    replace_wheel_member(bundle, CHECKER.SOURCE_FINGERPRINTS[0], b"DIFFERENT = 2\n")
    with pytest.raises(CHECKER.ProvenanceError, match="source fingerprint mismatch"):
        CHECKER.inspect_bundle(
            bundle, expected_version=VERSION, source_sha=sha, repository_root=repository
        )
