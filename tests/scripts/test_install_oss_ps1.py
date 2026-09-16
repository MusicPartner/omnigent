"""Tests for the Windows PowerShell OSS installer."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

INSTALLER = Path(__file__).resolve().parents[2] / "scripts" / "install_oss.ps1"
PWSH = shutil.which("pwsh") or shutil.which("powershell")
_STRIP_ENV = ("DATABRICKS_TOKEN", "ANTHROPIC_API_KEY", "CODEX", "CLAUDE_CODE")


def run_ps(snippet: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Dot-source the installer as a library and run a PowerShell snippet."""
    if PWSH is None:
        pytest.skip("PowerShell is not available")
    base = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV}
    base["OMNIGENT_INSTALL_OSS_PS1_LIB_ONLY"] = "1"
    if env:
        base.update(env)
    program = f". '{INSTALLER}'\n{snippet}\n"
    return subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-Command", program],
        capture_output=True,
        text=True,
        env=base,
        timeout=30,
    )


def test_join_extras_splits_commas_and_omits_empty_values() -> None:
    r = run_ps("Join-Extras @('databricks,s3', '', 'vertex')")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "databricks,s3,vertex"


@pytest.mark.parametrize(
    ("repo_url", "expected"),
    [
        ("https://github.com/o/r", "git+https://github.com/o/r"),
        ("http://example.com/o/r", "git+http://example.com/o/r"),
        ("git+https://github.com/o/r", "git+https://github.com/o/r"),
        ("ssh://git@host/o/r", "git+ssh://git@host/o/r"),
        ("git@host:org/repo.git", "git+ssh://git@host/org/repo.git"),
    ],
)
def test_normalize_repo_url_shapes(repo_url: str, expected: str) -> None:
    r = run_ps(f"Normalize-RepoUrl '{repo_url}' ''")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == expected


def test_normalize_repo_url_rejects_version_repo_conflict() -> None:
    r = run_ps("Normalize-RepoUrl 'https://github.com/o/r' '1.2.3'")
    assert r.returncode != 0
    assert "--version" in r.stderr and "--repo" in r.stderr


def test_normalize_repo_url_rejects_unsupported_shape() -> None:
    r = run_ps("Normalize-RepoUrl 'not-a-url' ''")
    assert r.returncode != 0
    assert "Unsupported --repo URL" in r.stderr


@pytest.mark.parametrize(
    ("install_url", "version", "extras", "expected"),
    [
        ("", "", "", "omnigent"),
        ("", "1.2.3", "", "omnigent==1.2.3"),
        ("", "", "databricks", "omnigent[databricks]"),
        ("", "1.2.3", "databricks", "omnigent[databricks]==1.2.3"),
        ("git+https://github.com/o/r", "", "", "git+https://github.com/o/r"),
    ],
)
def test_get_uv_install_target(
    install_url: str, version: str, extras: str, expected: str
) -> None:
    r = run_ps(f"Get-UvInstallTarget '{install_url}' '{version}' '{extras}'")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == expected


def test_check_only_does_not_run_uv_install(tmp_path: Path) -> None:
    uv = tmp_path / ("uv.cmd" if os.name == "nt" else "uv")
    uv.write_text("@echo off\necho uv called %*\nexit /b 0\n" if os.name == "nt" else "#!/bin/sh\necho uv called \"$@\"\n")
    uv.chmod(0o755)
    env = {"PATH": f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}"}
    r = subprocess.run(
        [
            PWSH or "pwsh",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(INSTALLER),
            "-CheckOnly",
            "-NonInteractive",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert "Check-only mode complete" in r.stdout
    assert "tool install" not in r.stdout


def test_missing_uv_fails_with_winget_guidance(tmp_path: Path) -> None:
    env = {"PATH": str(tmp_path)}
    r = run_ps("Show-DependencySummary", env=env)
    assert r.returncode != 0
    assert "winget install --id Astral-sh.Uv" in r.stderr


def test_capability_summary_reports_psmux_terminal_boundary(tmp_path: Path) -> None:
    env = {"PATH": str(tmp_path)}
    r = run_ps("Show-CapabilitySummary", env=env)
    assert r.returncode == 0, r.stderr
    assert "Windows Job Object backend" in r.stdout
    assert "filesystem/network sandboxing and L7 egress proxy" in r.stdout
    assert "native Omnigent-managed terminals require psmux" in r.stdout
