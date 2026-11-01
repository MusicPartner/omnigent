"""Exercise artifact provenance CLI recording and independent verification."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.scripts.windows_bundle_fixtures import SOURCE_SHA, VERSION, make_bundle

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/ci/verify-windows-bundle-provenance.py"


@pytest.fixture(autouse=True)
def _enforce_min_server_version() -> None:
    """Artifact subprocesses do not require a live server or provider."""


def test_provenance_cli_records_and_verifies_real_synthetic_wheel_bundle(tmp_path: Path) -> None:
    bundle = make_bundle(tmp_path / "bundle with spaces")
    command = [
        sys.executable,
        str(SCRIPT),
        "--bundle-dir",
        str(bundle),
        "--expected-version",
        VERSION,
        "--source-sha",
        SOURCE_SHA,
    ]
    for flags in (["--write-manifest"], []):
        result = subprocess.run(
            [*command, *flags], capture_output=True, text=True, check=False, timeout=20, cwd=ROOT
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["ok"] is True
    (bundle / "extra.txt").write_text("unexpected artifact", encoding="utf-8")
    refused = subprocess.run(
        command, capture_output=True, text=True, check=False, timeout=20, cwd=ROOT
    )
    assert refused.returncode == 1
    assert "does not match live bundle" in refused.stderr
