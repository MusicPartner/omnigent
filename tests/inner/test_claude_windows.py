"""Windows Claude executable selection without invoking npm batch shims."""

from __future__ import annotations

from pathlib import Path

import pytest

from omnigent.inner import claude_windows


@pytest.mark.parametrize("command", [r"C:\bin\claude.exe", "claude", "custom.cmd"])
def test_preserves_non_claude_shim(command: str) -> None:
    assert claude_windows.prefer_native_claude_exe(command) == command


@pytest.mark.parametrize("suffix", ["cmd", "CMD", "bat"])
def test_resolves_installed_binary_behind_npm_shim(tmp_path: Path, suffix: str) -> None:
    shim = tmp_path / f"claude.{suffix}"
    native = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    native.parent.mkdir(parents=True)
    native.write_bytes(b"MZnative")
    assert claude_windows.prefer_native_claude_exe(str(shim)) == str(native)


@pytest.mark.parametrize("content", [None, b"#!/bin/sh\n", b""])
def test_skips_missing_or_placeholder_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: bytes | None
) -> None:
    shim = tmp_path / "claude.cmd"
    native = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    if content is not None:
        native.parent.mkdir(parents=True)
        native.write_bytes(content)
    calls = []

    def resolve(name: str) -> str:
        calls.append(name)
        return r"C:\bin\claude.exe"

    monkeypatch.setattr(claude_windows, "resolve_cli_binary", resolve)
    assert claude_windows.prefer_native_claude_exe(str(shim)) == r"C:\bin\claude.exe"
    assert calls == ["claude.exe"]


def test_preserves_shim_when_no_native_install_is_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shim = str(tmp_path / "claude.cmd")
    monkeypatch.setattr(claude_windows, "resolve_cli_binary", lambda name: None)
    assert claude_windows.prefer_native_claude_exe(shim) == shim


@pytest.mark.parametrize("platform", ["win32", "linux"])
def test_sdk_only_normalizes_windows_shims(monkeypatch: pytest.MonkeyPatch, platform: str) -> None:
    from types import SimpleNamespace
    from unittest.mock import Mock

    from omnigent.inner import claude_sdk_executor as sdk

    resolve = Mock(return_value="claude.cmd")
    prefer = Mock(return_value="claude.exe")
    monkeypatch.setattr(sdk, "sys", SimpleNamespace(platform=platform))
    monkeypatch.setattr(sdk, "resolve_cli_binary", resolve)
    monkeypatch.setattr(sdk, "prefer_native_claude_exe", prefer)
    assert sdk._find_system_claude() == ("claude.exe" if platform == "win32" else "claude.cmd")
    resolve.assert_called_once_with("claude", env_var="OMNIGENT_CLAUDE_PATH")
    if platform == "win32":
        prefer.assert_called_once_with("claude.cmd")
    else:
        prefer.assert_not_called()
