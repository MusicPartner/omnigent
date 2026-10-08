"""Tests for omnigent.runner.native.windows_env.psmux_claude_env_unset."""

from __future__ import annotations

import pytest

from omnigent.runner.native.windows_env import psmux_claude_env_unset


def test_unsets_claude_config_dir_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    assert psmux_claude_env_unset() == ["CLAUDE_CONFIG_DIR"]


def test_unsets_claude_config_dir_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "")
    assert psmux_claude_env_unset() == ["CLAUDE_CONFIG_DIR"]


def test_keeps_claude_config_dir_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/custom/cfg")
    assert psmux_claude_env_unset() == []
