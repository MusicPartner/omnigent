"""Exercise the delta CLI against a disposable synthetic Git history only."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / ".github" / "scripts" / "ci" / "audit-windows-delta.py"
OWNER_MAP = ROOT / "docs" / "windows" / "WINDOWS-INTEGRATION-MAP.json"


@pytest.fixture(autouse=True)
def _enforce_min_server_version() -> None:
    """This subprocess-only scenario has no live server version to enforce."""


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        env=_isolated_environment(),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _commit(repository: Path, message: str) -> str:
    _git(
        repository,
        "-c",
        "user.name=Windows delta test",
        "-c",
        "user.email=windows-delta@example.invalid",
        "commit",
        "--quiet",
        "-m",
        message,
    )
    return _git(repository, "rev-parse", "HEAD")


def _isolated_environment() -> dict[str, str]:
    allowed = (
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
    )
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def test_delta_cli_reports_rename_overlap_and_unmapped_review_without_services(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "synthetic-repository"
    repository.mkdir()
    _git(repository, "-c", "init.defaultBranch=main", "init", "--quiet")

    original = repository / "web" / "src" / "shell" / "hostPaths.ts"
    original.parent.mkdir(parents=True)
    original.write_text("export const pathFlavor = 'base';\n", encoding="utf-8")
    _git(repository, "add", "--all")
    base_sha = _commit(repository, "base")

    _git(repository, "switch", "--create", "fork")
    _git(repository, "mv", "web/src/shell/hostPaths.ts", "web/src/shell/windowsHostPaths.ts")
    general_fix = repository / "general" / "shared_fix.py"
    general_fix.parent.mkdir()
    general_fix.write_text("value = 1\n", encoding="utf-8")
    _git(repository, "add", "--all")
    fork_sha = _commit(repository, "fork changes")

    _git(repository, "switch", "main")
    original.write_text("export const pathFlavor = 'target';\n", encoding="utf-8")
    _git(repository, "add", "--all")
    target_sha = _commit(repository, "target change")

    output_path = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repository",
            str(repository),
            "--base-sha",
            base_sha,
            "--fork-sha",
            fork_sha,
            "--target-sha",
            target_sha,
            "--map",
            str(OWNER_MAP),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_isolated_environment(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    report_bytes = output_path.read_bytes()
    assert report_bytes.endswith(b"\n") and not report_bytes.endswith(b"\r\n")
    report = json.loads(report_bytes.decode("utf-8"))
    renamed_record = next(
        record for record in report["fork_cumulative"] if record["status"].startswith("R")
    )
    unmapped_record = next(
        record
        for record in report["fork_cumulative"]
        if record["new_path"] == "general/shared_fix.py"
    )
    assert renamed_record["old_path"] == "web/src/shell/hostPaths.ts"
    assert renamed_record["new_path"] == "web/src/shell/windowsHostPaths.ts"
    assert 7 in renamed_record["owner_roadmap_ids"]
    assert renamed_record["overlap_review"][0]["new_path"] == "web/src/shell/hostPaths.ts"
    assert unmapped_record["mapping"] == "UNMAPPED_REVIEW"
    assert report["policy"]["owner_disposition"] == "no automatic DROP or RECONCILE decisions"
