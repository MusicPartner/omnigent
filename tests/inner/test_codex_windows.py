"""Tests for Windows Codex CLI shim resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from omnigent.inner import codex_windows


def test_prefer_native_codex_exe_leaves_non_shim_path_unchanged() -> None:
    assert codex_windows.prefer_native_codex_exe(r"C:\bin\codex.exe") == r"C:\bin\codex.exe"


def test_prefer_native_codex_exe_finds_vendor_exe_behind_cmd_shim(tmp_path: Path) -> None:
    shim = tmp_path / "npm" / "codex.cmd"
    native = (
        shim.parent
        / "node_modules"
        / "@openai"
        / "codex"
        / "node_modules"
        / "@openai"
        / "codex-win32-x64"
        / "vendor"
        / "x86_64-pc-windows-msvc"
        / "bin"
        / "codex.exe"
    )
    shim.parent.mkdir(parents=True)
    shim.write_text("@echo off\n", encoding="utf-8")
    native.parent.mkdir(parents=True)
    native.write_bytes(b"native")

    assert codex_windows.prefer_native_codex_exe(str(shim)) == str(native)


def test_prefer_native_codex_exe_handles_uppercase_cmd_suffix(tmp_path: Path) -> None:
    shim = tmp_path / "npm" / "codex.CMD"
    native = shim.parent / "node_modules" / "@openai" / "codex" / "vendor" / "win" / "codex.exe"
    shim.parent.mkdir(parents=True)
    shim.write_text("@echo off\n", encoding="utf-8")
    native.parent.mkdir(parents=True)
    native.write_bytes(b"native")

    assert codex_windows.prefer_native_codex_exe(str(shim)) == str(native)


def test_prefer_native_codex_exe_falls_back_to_resolver_without_vendor_exe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    shim = tmp_path / "npm" / "codex.cmd"
    shim.parent.mkdir(parents=True)
    shim.write_text("@echo off\n", encoding="utf-8")

    monkeypatch.setattr(codex_windows, "resolve_cli_binary", lambda name: r"C:\bin\codex.exe")
    assert codex_windows.prefer_native_codex_exe(str(shim)) == r"C:\bin\codex.exe"


def test_prefer_native_codex_exe_returns_shim_when_resolver_finds_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    shim = tmp_path / "npm" / "codex.cmd"
    shim.parent.mkdir(parents=True)
    shim.write_text("@echo off\n", encoding="utf-8")

    monkeypatch.setattr(codex_windows, "resolve_cli_binary", lambda name: None)
    assert codex_windows.prefer_native_codex_exe(str(shim)) == str(shim)


def test_find_codex_cli_on_non_windows_returns_resolver_value_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``.cmd`` path is never shim-resolved off Windows."""
    from omnigent.inner import codex_executor as ce

    monkeypatch.setattr(ce, "IS_WINDOWS", False)
    monkeypatch.setattr(ce, "resolve_cli_binary", lambda name, **_kwargs: r"C:\npm\codex.cmd")
    assert ce._find_codex_cli() == r"C:\npm\codex.cmd"
