"""PowerShell selection reaches Codex SDK, app-server, and remote terminal."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest

from omnigent.harnesses.codex_native import app_server as native
from omnigent.inner import codex_executor, windows_powershell
from tests.harnesses.codex_native.app_server._support import _test_app_server


@pytest.fixture
def powershell_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    executable = tmp_path / "Program Files" / "PowerShell" / "7" / "pwsh.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test executable")
    store = tmp_path / "WindowsApps"
    store.mkdir()
    (store / "pwsh.exe").write_bytes(b"test Store alias")
    path = f"{store};{tmp_path / 'other-tools'}"
    monkeypatch.setenv("PATH", path)
    monkeypatch.setenv("ProgramW6432", str(tmp_path / "Program Files"))
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", True)
    monkeypatch.setattr(native, "IS_WINDOWS", True)
    return executable, path


def test_sdk_env_discovers_installation_without_host_path_edit(
    powershell_install: tuple[Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    executable, original_path = powershell_install
    monkeypatch.setenv("OPENAI_API_KEY", "secret-not-for-codex")
    env = codex_executor._clean_codex_env()
    assert env["PATH"] == f"{executable.parent};{original_path}"
    assert "OPENAI_API_KEY" not in env
    assert os.environ["PATH"] == original_path


async def test_app_server_and_remote_terminal_select_same_powershell(
    powershell_install: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable, original_path = powershell_install
    source = tmp_path / "source-home"
    source.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(source))
    server = _test_app_server(
        tmp_path,
        tmp_path / "codex-home",
        tmp_path / "bridge",
        tmp_path,
        env={"PATH": original_path, "OTEL_RESOURCE_ATTRIBUTES": "deployment=test"},
    )
    original_env = dict(server.env)
    captured: dict[str, str] = {}

    async def version(_path: str) -> tuple[int, int, int]:
        return (0, 162, 0)

    async def capture_spawn(*args: object, **kwargs: object) -> None:
        captured.update(cast("dict[str, str]", kwargs["env"]))
        raise RuntimeError("spawn observed")

    monkeypatch.setattr(native, "_codex_cli_version", version)
    monkeypatch.setattr(native, "acquire_codex_native_process_owner_lock", lambda: None)
    monkeypatch.setattr(native.asyncio, "create_subprocess_exec", capture_spawn)
    with pytest.raises(RuntimeError, match="spawn observed"):
        await server.start()
    terminal = native.codex_terminal_env(server)
    assert captured["PATH"] == terminal["PATH"] == f"{executable.parent};{original_path}"
    assert captured["CODEX_HOME"] == terminal["CODEX_HOME"] == str(server.codex_home)
    assert server.env == original_env
    assert os.environ["PATH"] == original_path


def test_non_windows_terminal_does_not_override_shell_path(
    powershell_install: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", False)
    monkeypatch.setattr(native, "IS_WINDOWS", False)
    server = _test_app_server(
        tmp_path,
        tmp_path / "codex-home",
        tmp_path / "bridge",
        tmp_path,
        env={"PATH": "/usr/bin", "CODEX_HOME": "old"},
    )
    assert "PATH" not in native.codex_terminal_env(server)
    assert server.env["PATH"] == "/usr/bin"
