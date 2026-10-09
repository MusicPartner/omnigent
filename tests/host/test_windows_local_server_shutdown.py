"""Windows server stop verifies ownership before granting tree cleanup."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import click
import psutil
import pytest

from omnigent import _platform
from omnigent.host import local_server
from omnigent.inner import windows_process_shutdown


@pytest.fixture
def windows_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> SimpleNamespace:
    monkeypatch.setattr(_platform, "IS_WINDOWS", True)
    pidfile = tmp_path / "local_server.pid"
    pidfile.write_text("7777\n8123\n")
    os.utime(pidfile, (20.0, 20.0))
    monkeypatch.setattr(local_server, "_LOCAL_SERVER_PID_PATH", pidfile)
    for name in (
        "_LOCAL_SERVER_SIG_PATH",
        "_LOCAL_SERVER_BASE_PATH_PATH",
        "_LOCAL_SERVER_LOG_REF_PATH",
    ):
        monkeypatch.setattr(local_server, name, tmp_path / name)
    monkeypatch.setattr(local_server, "_pid_alive", lambda pid: True)
    process = SimpleNamespace(
        create_time=lambda: 10.0,
        cmdline=lambda: [r"C:\Python\python.exe", "-P", "-m", "omnigent.cli", "server"],
    )
    state = SimpleNamespace(pidfile=pidfile, process=process, stopped=[])
    monkeypatch.setattr(local_server.psutil, "Process", lambda pid: process)
    monkeypatch.setattr(
        windows_process_shutdown,
        "stop_process",
        lambda pid, **kwargs: state.stopped.append((pid, kwargs)) or True,
    )
    return state


def test_verified_server_birth_is_pinned(windows_server: SimpleNamespace) -> None:
    local_server.stop_local_omnigent_server()
    assert windows_server.stopped == [
        (7777, {"grace_seconds": 30.0, "expected_create_time": 10.0})
    ]
    assert not windows_server.pidfile.exists()


def test_stale_unrelated_pidfile_never_requests_cleanup(windows_server: SimpleNamespace) -> None:
    windows_server.process.cmdline = lambda: [r"C:\Python\python.exe", "unrelated.py"]
    local_server.stop_local_omnigent_server()
    assert windows_server.stopped == []
    assert not windows_server.pidfile.exists()


def test_recycled_server_pid_is_not_owned_by_old_record(windows_server: SimpleNamespace) -> None:
    windows_server.process.create_time = lambda: 30.0
    local_server.stop_local_omnigent_server()
    assert windows_server.stopped == []
    assert not windows_server.pidfile.exists()


def test_unreadable_ownership_keeps_record(windows_server: SimpleNamespace) -> None:
    def inaccessible() -> list[str]:
        raise psutil.AccessDenied(7777)

    windows_server.process.cmdline = inaccessible
    with pytest.raises(click.ClickException, match="Cannot verify"):
        local_server.stop_local_omnigent_server()
    assert windows_server.stopped == []
    assert windows_server.pidfile.exists()


def test_failed_pinned_cleanup_keeps_record(
    monkeypatch: pytest.MonkeyPatch, windows_server: SimpleNamespace
) -> None:
    monkeypatch.setattr(windows_process_shutdown, "stop_process", lambda *args, **kwargs: False)
    with pytest.raises(click.ClickException, match="did not stop"):
        local_server.stop_local_omnigent_server()
    assert windows_server.pidfile.exists()


@pytest.mark.parametrize(
    "arguments",
    [
        [r"C:\Python\python.exe", "-m", "omnigent", "server"],
        [r"C:\Tools\omni.exe", "server", "--port", "8123"],
        [r"C:\Tools\omnigent.exe", "server"],
    ],
)
def test_installed_server_commands_are_recognized(
    windows_server: SimpleNamespace, arguments: list[str]
) -> None:
    windows_server.process.cmdline = lambda: arguments
    assert local_server._windows_server_birth(7777) == 10.0


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        [r"C:\Python\python.exe", "unrelated.py", "-m", "omnigent.cli", "server"],
        [r"C:\Tools\other.exe", "-m", "omnigent.cli", "server"],
        [r"C:\Tools\omni.exe", "host", "--server", "http://127.0.0.1:8123"],
        [r"C:\Python\python.exe", "-m", "omnigent.cli", "host"],
    ],
)
def test_unrelated_command_arguments_do_not_grant_server_ownership(
    windows_server: SimpleNamespace, arguments: list[str]
) -> None:
    windows_server.process.cmdline = lambda: arguments
    assert local_server._windows_server_birth(7777) is None


def test_concurrently_cleared_record_is_a_safe_noop(
    monkeypatch: pytest.MonkeyPatch, windows_server: SimpleNamespace
) -> None:
    def read_then_clear() -> tuple[int, int]:
        windows_server.pidfile.unlink()
        return (7777, 8123)

    monkeypatch.setattr(local_server, "_read_local_server_pid_file", read_then_clear)
    local_server.stop_local_omnigent_server()
    assert windows_server.stopped == []
