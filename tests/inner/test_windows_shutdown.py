"""Tests for omnigent.inner._windows_shutdown and its use in _proc.terminate_tree."""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from omnigent.inner import _proc, _windows_shutdown

# --------------------------------------------------------------------------
# send_ctrl_break
# --------------------------------------------------------------------------


def test_send_ctrl_break_false_when_event_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_windows_shutdown, "CTRL_BREAK_EVENT", None)
    calls: list[object] = []
    monkeypatch.setattr(_windows_shutdown.os, "kill", lambda *a: calls.append(a))
    assert _windows_shutdown.send_ctrl_break(1234) is False
    assert calls == []


def test_send_ctrl_break_false_when_os_kill_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_windows_shutdown, "CTRL_BREAK_EVENT", 9999)

    def _raise(pid: int, sig: int) -> None:
        raise OSError("no such process")

    monkeypatch.setattr(_windows_shutdown.os, "kill", _raise)
    assert _windows_shutdown.send_ctrl_break(1234) is False


def test_send_ctrl_break_true_when_os_kill_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_windows_shutdown, "CTRL_BREAK_EVENT", 9999)
    sent: list[tuple[int, int]] = []
    monkeypatch.setattr(_windows_shutdown.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    assert _windows_shutdown.send_ctrl_break(1234) is True
    assert sent == [(1234, 9999)]


# --------------------------------------------------------------------------
# install_ctrl_break_handler
# --------------------------------------------------------------------------


def test_install_ctrl_break_handler_noop_when_sigbreak_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_windows_shutdown, "SIGBREAK", None)
    calls: list[object] = []
    monkeypatch.setattr(_windows_shutdown.signal, "signal", lambda *a: calls.append(a))
    _windows_shutdown.install_ctrl_break_handler(lambda sig, frame: None)
    assert calls == []


def test_install_ctrl_break_handler_installs_when_sigbreak_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_windows_shutdown, "SIGBREAK", 21)
    installed: list[tuple[int, object]] = []
    monkeypatch.setattr(
        _windows_shutdown.signal, "signal", lambda sig, handler: installed.append((sig, handler))
    )
    handler = lambda sig, frame: None  # noqa: E731
    _windows_shutdown.install_ctrl_break_handler(handler)
    assert installed == [(21, handler)]


# --------------------------------------------------------------------------
# _proc.terminate_tree Windows path
# --------------------------------------------------------------------------


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.returncode: int | None = None

    def terminate(self) -> None:
        raise AssertionError("terminate() should not be called on the CTRL_BREAK path")

    def kill(self) -> None:
        raise AssertionError("kill() should not be called on the CTRL_BREAK path")


@pytest.fixture
def windows_tree(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    process = _FakeProcess(4242)
    state = SimpleNamespace(process=process, sent=[], waited=[], census=[])
    monkeypatch.setattr(_proc, "IS_WINDOWS", True)
    monkeypatch.setattr(_proc, "IS_POSIX", False)
    monkeypatch.setattr(_proc, "_killpg", lambda *args, **kwargs: False)
    monkeypatch.setattr(_proc, "_snapshot_identities", lambda pid: {pid: 1.0, 4343: 2.0})
    monkeypatch.setattr(
        _proc.psutil, "Process", lambda pid: SimpleNamespace(create_time=lambda: 1.0)
    )
    monkeypatch.setattr(_proc, "send_ctrl_break", lambda pid: state.sent.append(pid) or True)
    monkeypatch.setattr(_proc, "_wait_gone", lambda pid, grace: state.waited.append((pid, grace)))

    def census(process, pid, **kwargs):
        state.census.append(kwargs)
        return _proc._remember_identities(process, {}, remove=kwargs["remove"])

    monkeypatch.setattr(_proc, "_signal_tree_census", census)
    return state


def test_terminate_tree_windows_path_uses_ctrl_break(
    monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    def _boom(pid: int) -> list[object]:
        raise AssertionError("psutil fallback should not run when CTRL_BREAK succeeds")

    monkeypatch.setattr(_proc, "_walk_descendants", _boom)
    _proc.terminate_tree(windows_tree.process, grace=5)
    assert windows_tree.sent == [4242]
    assert windows_tree.waited == [(4242, 5)]
    assert windows_tree.census == []
    assert _proc._remember_identities(windows_tree.process, {}) == {4242: 1.0, 4343: 2.0}


def test_terminate_tree_windows_path_falls_back_when_ctrl_break_fails(
    monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    monkeypatch.setattr(
        _proc, "send_ctrl_break", lambda pid: windows_tree.sent.append(pid) or False
    )
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == [4242]
    assert windows_tree.census == [{"force": False, "remove": False, "snapshot_root": True}]


def test_terminate_tree_escalates_when_ctrl_break_is_ignored(
    monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    def wait_gone(pid: int, grace: float) -> None:
        windows_tree.waited.append((pid, grace))
        if len(windows_tree.waited) == 1:
            raise _proc.psutil.TimeoutExpired(grace, pid)

    monkeypatch.setattr(_proc, "_wait_gone", wait_gone)
    _proc.terminate_tree(windows_tree.process, grace=5)
    assert windows_tree.sent == [4242]
    assert windows_tree.census == [{"force": False, "remove": False, "snapshot_root": True}]
    assert windows_tree.waited == [(4242, 5), (4242, 5)]


@pytest.mark.skipif(sys.platform != "win32", reason="CTRL_BREAK is Windows-only")
def test_terminate_tree_stops_a_child_that_ignores_ctrl_break() -> None:
    script = (
        "import signal, sys, time\n"
        "signal.signal(signal.SIGBREAK, signal.SIG_IGN)\n"
        "print('ready', flush=True)\n"
        "time.sleep(60)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script], stdout=subprocess.PIPE, **_proc.spawn_kwargs()
    )
    try:
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == b"ready"
        _proc.terminate_tree(proc, grace=1)
        assert proc.wait(timeout=5) is not None
    finally:
        _proc.kill_tree(proc)
        proc.wait(timeout=5)


def test_terminate_tree_never_breaks_a_previously_reused_root(
    windows_tree: SimpleNamespace,
) -> None:
    _proc._remember_identities(windows_tree.process, {4242: 0.5})
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert windows_tree.census == [{"force": False, "remove": False, "snapshot_root": False}]
    assert _proc._remember_identities(windows_tree.process, {}) == {4242: 0.5}


def test_terminate_tree_rechecks_identity_before_ctrl_break(
    monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    monkeypatch.setattr(
        _proc.psutil, "Process", lambda pid: SimpleNamespace(create_time=lambda: 9.0)
    )
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert windows_tree.census == [{"force": False, "remove": False, "snapshot_root": True}]


@pytest.mark.parametrize("error", [_proc.psutil.NoSuchProcess, _proc.psutil.AccessDenied])
def test_terminate_tree_does_not_break_an_unverifiable_root(
    error, monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    def inaccessible(pid):
        raise error(pid)

    monkeypatch.setattr(_proc.psutil, "Process", inaccessible)
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert len(windows_tree.census) == 1


@pytest.mark.parametrize("pid", [0, 1, -1, _proc.os.getpid()])
def test_terminate_tree_does_not_break_invalid_or_self_pid(
    pid: int, windows_tree: SimpleNamespace
) -> None:
    windows_tree.process.pid = pid
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert len(windows_tree.census) == 1


def test_terminate_tree_does_not_break_a_root_missing_from_snapshot(
    monkeypatch: pytest.MonkeyPatch, windows_tree: SimpleNamespace
) -> None:
    monkeypatch.setattr(_proc, "_snapshot_identities", lambda pid: {4343: 2.0})
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert len(windows_tree.census) == 1


def test_terminate_tree_does_not_break_an_exited_process(windows_tree: SimpleNamespace) -> None:
    windows_tree.process.returncode = 0
    _proc.terminate_tree(windows_tree.process)
    assert windows_tree.sent == []
    assert windows_tree.census == []


def test_ctrl_break_retains_descendants_for_force_cleanup(windows_tree: SimpleNamespace) -> None:
    _proc.terminate_tree(windows_tree.process)
    _proc.kill_tree(windows_tree.process)
    assert windows_tree.sent == [4242]
    assert windows_tree.census == [{"force": True, "remove": True, "snapshot_root": True}]


def test_harness_runner_installs_handler_before_serving(monkeypatch: pytest.MonkeyPatch) -> None:
    from omnigent.runtime import telemetry
    from omnigent.runtime.harnesses import _runner

    events = []
    server = SimpleNamespace(handle_exit=object(), run=lambda: events.append("run"))
    monkeypatch.setattr(_runner, "_configure_logging", lambda *args: None)
    monkeypatch.setattr(telemetry, "init", lambda *args: None)
    monkeypatch.setattr(_runner, "_load_harness_app", lambda *args: object())
    monkeypatch.setattr(_runner, "_create_uvicorn_config", lambda *args: object())
    monkeypatch.setattr(_runner, "_HardExitServer", lambda config: server)
    monkeypatch.setattr(_runner, "install_ctrl_break_handler", events.append)
    _runner.main(
        [
            "--harness",
            "test",
            "--module",
            "test.module",
            "--bind",
            "127.0.0.1:8765",
            "--conversation-id",
            "conv_test",
        ]
    )
    assert events == [server.handle_exit, "run"]


async def test_harness_spawn_isolates_windows_console_group(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from omnigent.runtime.harnesses import process_manager

    calls = []
    process = object()

    async def spawn(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    monkeypatch.setattr(process_manager.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(_proc, "IS_POSIX", False)
    monkeypatch.setattr(_proc, "_CREATE_NEW_PROCESS_GROUP", 512)
    manager = process_manager.HarnessProcessManager(tmp_parent=tmp_path)
    env = {"ENV": "test"}
    try:
        assert await manager._spawn_harness_process(["--harness", "test"], env) is process
        assert len(calls) == 1
        assert calls[0][1]["creationflags"] == 512
        assert "start_new_session" not in calls[0][1]
        assert calls[0][1]["env"] is env
    finally:
        await manager.shutdown()
