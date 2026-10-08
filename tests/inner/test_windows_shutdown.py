"""Tests for omnigent.inner._windows_shutdown and its use in _proc.terminate_tree."""

from __future__ import annotations

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


def test_terminate_tree_windows_path_uses_ctrl_break(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_proc, "IS_WINDOWS", True)
    monkeypatch.setattr(_proc, "_killpg", lambda pid, sig: False)
    monkeypatch.setattr(_proc, "send_ctrl_break", lambda pid: True)
    waited: list[tuple[int, float]] = []
    monkeypatch.setattr(_proc, "_wait_gone", lambda pid, grace: waited.append((pid, grace)))

    def _boom(pid: int) -> list[object]:
        raise AssertionError("psutil fallback should not run when CTRL_BREAK succeeds")

    monkeypatch.setattr(_proc, "_walk_descendants", _boom)

    _proc.terminate_tree(_FakeProcess(4242), grace=5)
    assert waited == [(4242, 5)]


def test_terminate_tree_windows_path_falls_back_when_ctrl_break_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_proc, "IS_WINDOWS", True)
    monkeypatch.setattr(_proc, "_killpg", lambda pid, sig: False)
    monkeypatch.setattr(_proc, "send_ctrl_break", lambda pid: False)
    walked: list[int] = []
    monkeypatch.setattr(_proc, "_walk_descendants", lambda pid: walked.append(pid) or [])

    class _FallbackProcess(_FakeProcess):
        def terminate(self) -> None:
            pass

    _proc.terminate_tree(_FallbackProcess(4242), grace=0)
    assert walked == [4242]
