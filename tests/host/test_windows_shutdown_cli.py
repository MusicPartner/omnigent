"""Ownership checks for the private Windows desktop shutdown bridge."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import click
import psutil
import pytest
from click.testing import CliRunner

from omnigent.inner import windows_process_shutdown, windows_shutdown_cli


@pytest.fixture
def shutdown_command(monkeypatch: pytest.MonkeyPatch) -> tuple[click.Group, Mock]:
    group = click.Group("internal")
    windows_shutdown_cli.register_shutdown_command(group)
    monkeypatch.setattr(windows_shutdown_cli, "IS_WINDOWS", True)
    monkeypatch.setattr(psutil, "Process", lambda _pid: SimpleNamespace(create_time=lambda: 100.0))
    stop = Mock(return_value=True)
    monkeypatch.setattr(windows_process_shutdown, "stop_process", stop)
    return group, stop


def test_desktop_request_preserves_process_birth_and_grace(
    shutdown_command: tuple[click.Group, Mock],
) -> None:
    group, stop = shutdown_command
    result = CliRunner().invoke(
        group,
        ["windows-shutdown", "4242", "--created-before-ms", "100001", "--grace-seconds", "7"],
    )
    assert result.exit_code == 0, result.output
    stop.assert_called_once_with(4242, grace_seconds=7.0, expected_create_time=100.0)


def test_desktop_request_rejects_recycled_pid(shutdown_command: tuple[click.Group, Mock]) -> None:
    group, stop = shutdown_command
    result = CliRunner().invoke(
        group, ["windows-shutdown", "4242", "--created-before-ms", "99999"]
    )
    assert result.exit_code == 1
    assert "reused" in result.output
    stop.assert_not_called()


def test_desktop_request_rejects_unreadable_identity(
    shutdown_command: tuple[click.Group, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    group, stop = shutdown_command

    def denied(pid: int) -> None:
        raise psutil.AccessDenied(pid)

    monkeypatch.setattr(psutil, "Process", denied)
    result = CliRunner().invoke(
        group, ["windows-shutdown", "4242", "--created-before-ms", "100001"]
    )
    assert result.exit_code == 1
    assert "verify" in result.output
    stop.assert_not_called()


def test_desktop_request_reports_surviving_process(
    shutdown_command: tuple[click.Group, Mock],
) -> None:
    group, stop = shutdown_command
    stop.return_value = False
    result = CliRunner().invoke(
        group, ["windows-shutdown", "4242", "--created-before-ms", "100001"]
    )
    assert result.exit_code == 1
    assert "did not stop" in result.output


def test_desktop_request_already_exited_is_idempotent(
    shutdown_command: tuple[click.Group, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    group, stop = shutdown_command

    def gone(pid: int) -> None:
        raise psutil.NoSuchProcess(pid)

    monkeypatch.setattr(psutil, "Process", gone)
    result = CliRunner().invoke(
        group, ["windows-shutdown", "4242", "--created-before-ms", "100001"]
    )
    assert result.exit_code == 0
    stop.assert_not_called()


def test_server_stop_finishes_cleanup_but_reports_windows_daemon_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    cli = importlib.import_module("omnigent.cli")
    monkeypatch.setattr(cli, "IS_WINDOWS", True)
    monkeypatch.setattr(cli, "local_server_url_if_healthy", lambda: "http://localhost:6767")
    monkeypatch.setattr(cli, "_find_daemon_record", lambda _target: object())
    monkeypatch.setattr(
        cli, "_terminate_daemon", Mock(side_effect=click.ClickException("still alive"))
    )
    server_stop = Mock()
    orphan_stop = Mock(return_value=None)
    monkeypatch.setattr(cli, "stop_local_omnigent_server", server_stop)
    monkeypatch.setattr(cli, "stop_untracked_local_server", orphan_stop)

    with pytest.raises(click.ClickException, match="still alive"):
        cli._stop_local_server_and_daemon(force=False)
    server_stop.assert_called_once_with()
    orphan_stop.assert_called_once_with()


def test_daemon_shutdown_pins_verified_birth_and_preserves_record_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    cli = importlib.import_module("omnigent.cli")
    record = cli._HostDaemonRecord(
        pid=4242, target="local", mode="local", server_url=None, log_path=None, started_at=100.0
    )
    monkeypatch.setattr(cli, "IS_WINDOWS", True)
    monkeypatch.setattr(psutil, "Process", lambda _pid: SimpleNamespace(create_time=lambda: 99.0))
    monkeypatch.setattr(cli, "_pid_is_recorded_daemon", lambda _record: True)
    delete = Mock()
    stop = Mock(return_value=False)
    monkeypatch.setattr(cli, "_delete_daemon_record", delete)
    monkeypatch.setattr(windows_process_shutdown, "stop_process", stop)

    with pytest.raises(click.ClickException, match="did not exit"):
        cli._terminate_daemon(record, force=False)
    stop.assert_called_once_with(4242, expected_create_time=99.0, grace_seconds=35.0, force=False)
    delete.assert_not_called()

    stop.return_value = True
    cli._terminate_daemon(record, force=True)
    delete.assert_called_once_with(record)


def test_daemon_shutdown_retains_unreadable_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    cli = importlib.import_module("omnigent.cli")
    record = cli._HostDaemonRecord(
        pid=4242, target="local", mode="local", server_url=None, log_path=None, started_at=100.0
    )
    monkeypatch.setattr(cli, "IS_WINDOWS", True)
    monkeypatch.setattr(psutil, "Process", Mock(side_effect=psutil.AccessDenied(4242)))
    delete = Mock()
    stop = Mock()
    monkeypatch.setattr(cli, "_delete_daemon_record", delete)
    monkeypatch.setattr(windows_process_shutdown, "stop_process", stop)
    with pytest.raises(click.ClickException, match="Cannot verify"):
        cli._terminate_daemon(record, force=True)
    stop.assert_not_called()
    delete.assert_not_called()


def test_daemon_shutdown_discards_recycled_identity_without_stopping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    cli = importlib.import_module("omnigent.cli")
    record = cli._HostDaemonRecord(
        pid=4242, target="local", mode="local", server_url=None, log_path=None, started_at=100.0
    )
    monkeypatch.setattr(cli, "IS_WINDOWS", True)
    monkeypatch.setattr(psutil, "Process", lambda _pid: SimpleNamespace(create_time=lambda: 200.0))
    monkeypatch.setattr(cli, "_pid_is_recorded_daemon", lambda _record: False)
    monkeypatch.setattr(cli, "_pid_alive", lambda _pid: True)
    monkeypatch.setattr(cli, "_describe_pid", lambda _pid: "recycled PID")
    delete = Mock()
    stop = Mock()
    monkeypatch.setattr(cli, "_delete_daemon_record", delete)
    monkeypatch.setattr(windows_process_shutdown, "stop_process", stop)
    cli._terminate_daemon(record, force=True)
    stop.assert_not_called()
    delete.assert_called_once_with(record)
