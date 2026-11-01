"""Exercise the desktop provenance CLI across a real subprocess boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.scripts.windows_desktop_fixtures import SOURCE_SHA, VERSION, make_desktop_archive

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".github/scripts/ci/verify-windows-desktop-provenance.py"


@pytest.fixture(autouse=True)
def _enforce_min_server_version() -> None:
    """This artifact-only CLI scenario does not require the live-server fixture."""


def _run_checker(archive: Path, source_sha: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--archive",
            str(archive),
            "--expected-version",
            VERSION,
            "--source-sha",
            source_sha,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_desktop_provenance_cli_accepts_bundle_and_rejects_wrong_source_sha(
    tmp_path: Path,
) -> None:
    archive = make_desktop_archive(tmp_path / "path with spaces" / "Omnigent Desktop.zip")

    valid = _run_checker(archive, SOURCE_SHA)
    assert valid.returncode == 0, valid.stderr
    report = json.loads(valid.stdout)
    assert report["artifact"] == archive.name
    assert report["source_sha"] == SOURCE_SHA
    assert report["package"]["omnigentSourceCommit"] == SOURCE_SHA

    invalid = _run_checker(archive, "b" * 40)
    assert invalid.returncode == 1
    assert not invalid.stdout
    assert invalid.stderr
