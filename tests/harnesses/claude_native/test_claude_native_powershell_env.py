"""Native Claude terminal shell discovery stays invocation-local."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from omnigent.harnesses.claude_native.main import build_native_claude_terminal_env
from omnigent.inner import windows_powershell


@pytest.mark.parametrize("store_first", [False, True])
def test_terminal_prefers_native_powershell_without_forwarding_ambient_secrets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, store_first: bool
) -> None:
    native = tmp_path / "Program Files" / "PowerShell" / "7"
    native.mkdir(parents=True)
    (native / "pwsh.exe").touch()
    original_path = str(tmp_path / "existing-tools")
    if store_first:
        store = tmp_path / "WindowsApps"
        store.mkdir()
        (store / "pwsh.exe").touch()
        original_path = f"{store};{original_path}"
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.setenv("PATH", original_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "parent-secret")

    env = build_native_claude_terminal_env(None)

    assert env["PATH"] == f"{native.resolve()};{original_path}"
    assert env["ENABLE_TOOL_SEARCH"] == "true"
    assert "ANTHROPIC_API_KEY" not in env
    assert "ProgramFiles" not in env
    assert os.environ["PATH"] == original_path
