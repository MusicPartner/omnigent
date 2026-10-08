"""Tests for the Windows-only Claude native hook command builders."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from omnigent.harnesses.claude_native import bridge as claude_native_bridge
from omnigent.harnesses.claude_native.bridge import build_hook_settings
from omnigent.harnesses.claude_native.windows_hooks import (
    message_display_command,
    status_line_command,
)
from omnigent.native import shell as native_shell


@pytest.fixture(autouse=True)
def _force_windows_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(native_shell, "IS_WINDOWS", True)


def test_message_display_command_invokes_stdlib_hook_module(tmp_path: Path) -> None:
    bridge_dir = tmp_path / "bridge"
    command = message_display_command("C:/venv/Scripts/python.exe", bridge_dir)
    assert "omnigent.harnesses.claude_native.message_display_hook" in command
    assert str(bridge_dir).replace("\\", "/") in command
    assert "--bridge-dir" in command


def test_status_line_command_without_chain_omits_chain_flag(tmp_path: Path) -> None:
    bridge_dir = tmp_path / "bridge"
    command = status_line_command("C:/venv/Scripts/python.exe", bridge_dir, None)
    assert "omnigent.harnesses.claude_native.status" in command
    assert "--chain-b64" not in command


def test_status_line_command_with_chain_roundtrips_base64(tmp_path: Path) -> None:
    bridge_dir = tmp_path / "bridge"
    chain_command = "bun run hud"
    command = status_line_command("C:/venv/Scripts/python.exe", bridge_dir, chain_command)
    assert "--chain-b64" in command
    tokens = command.split()
    encoded = tokens[tokens.index("--chain-b64") + 1]
    assert base64.b64decode(encoded).decode("utf-8") == chain_command


def test_build_hook_settings_message_display_matches_windows_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``build_hook_settings`` must delegate to :func:`message_display_command`."""
    monkeypatch.setattr(claude_native_bridge, "IS_WINDOWS", True)
    monkeypatch.setattr(claude_native_bridge, "read_user_status_line_command", lambda: None)
    bridge_dir = tmp_path / "bridge"
    python_executable = "C:/venv/Scripts/python.exe"

    settings = build_hook_settings(bridge_dir, python_executable=python_executable)

    expected = message_display_command(python_executable, bridge_dir)
    actual = settings["hooks"]["MessageDisplay"][0]["hooks"][0]["command"]
    assert actual == expected


def test_build_hook_settings_status_line_matches_windows_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``build_hook_settings`` must delegate to :func:`status_line_command`."""
    monkeypatch.setattr(claude_native_bridge, "IS_WINDOWS", True)
    chain_command = "bun run hud"
    monkeypatch.setattr(
        claude_native_bridge, "read_user_status_line_command", lambda: chain_command
    )
    bridge_dir = tmp_path / "bridge"
    python_executable = "C:/venv/Scripts/python.exe"

    settings = build_hook_settings(bridge_dir, python_executable=python_executable)

    expected = status_line_command(python_executable, bridge_dir, chain_command)
    actual = settings["statusLine"]["command"]
    assert actual == expected
