"""Windows runner shutdown dispatch preserves graceful lifecycle callbacks."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from omnigent.runner._entry import _install_signal_handlers

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows shutdown endpoint")


async def test_runner_console_shutdown_marks_state_and_records_reason() -> None:
    event = asyncio.Event()
    reasons: list[str] = []
    marked: list[bool] = []
    signals = (signal.SIGINT, signal.SIGTERM, signal.SIGBREAK)
    previous = {sig: signal.getsignal(sig) for sig in signals}
    listener = _install_signal_handlers(
        event, record_reason=reasons.append, mark_shutting_down=lambda: marked.append(True)
    )
    try:
        handler = signal.getsignal(signal.SIGBREAK)
        assert callable(handler)
        handler(signal.SIGBREAK, None)
        await asyncio.wait_for(event.wait(), timeout=2)
        assert reasons == ["received SIGBREAK"]
        assert marked == [True]
    finally:
        assert listener is not None
        listener.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def test_parent_death_snapshots_children_before_graceful_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from omnigent.inner import windows_process_shutdown
    from omnigent.runner import _entry

    events: list[object] = []
    child = object()
    scope = SimpleNamespace(kill=lambda: events.append("kill") or True)
    monkeypatch.setattr(_entry, "_parent_is_orphaned", lambda _pid: True)
    monkeypatch.setattr(
        windows_process_shutdown.psutil,
        "Process",
        lambda: SimpleNamespace(children=lambda: [child]),
    )
    monkeypatch.setattr(
        windows_process_shutdown,
        "snapshot_processes",
        lambda children: events.append(("snapshot", children)) or scope,
    )
    monkeypatch.setattr(_entry.time, "sleep", lambda duration: events.append(("grace", duration)))
    _entry._run_parent_death_killer(
        123456,
        lambda: events.append("shutdown"),
        exit_fn=lambda code: events.append(("exit", code)),
    )
    assert events == [
        ("snapshot", [child]),
        "shutdown",
        ("grace", 30.0),
        ("snapshot", [child]),
        "kill",
        "kill",
        ("exit", 0),
    ]


def test_parent_death_reaps_children_started_during_shutdown_grace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from omnigent.inner import windows_process_shutdown
    from omnigent.runner import _entry

    events: list[object] = []
    late_child = object()
    generations = iter([[], [late_child]])
    monkeypatch.setattr(_entry, "_parent_is_orphaned", lambda _pid: True)
    monkeypatch.setattr(
        windows_process_shutdown.psutil,
        "Process",
        lambda: SimpleNamespace(children=lambda: next(generations)),
    )

    def snapshot(children: list[object]) -> SimpleNamespace:
        events.append(("snapshot", children))
        return SimpleNamespace(kill=lambda: events.append(("kill", children)) or True)

    monkeypatch.setattr(windows_process_shutdown, "snapshot_processes", snapshot)
    monkeypatch.setattr(_entry.time, "sleep", lambda duration: events.append(("grace", duration)))
    _entry._run_parent_death_killer(
        123456,
        lambda: events.append("shutdown"),
        exit_fn=lambda code: events.append(("exit", code)),
    )
    assert events == [
        ("snapshot", []),
        "shutdown",
        ("grace", 30.0),
        ("snapshot", [late_child]),
        ("kill", [late_child]),
        ("kill", []),
        ("exit", 0),
    ]


def test_owned_native_codex_stops_with_runner_and_preserves_neighbor(tmp_path: Path) -> None:
    """Opt in with OMNIGENT_TEST_CODEX_EXE to exercise an installed native binary."""
    import psutil

    from omnigent.host.connect import HostProcess
    from omnigent.inner.windows_process_shutdown import stop_processes

    executable = os.environ.get("OMNIGENT_TEST_CODEX_EXE")
    if executable is None or not Path(executable).is_file():
        pytest.skip("Set OMNIGENT_TEST_CODEX_EXE to an installed native Codex executable")
    owned_home, neighbor_home = tmp_path / "owned-home", tmp_path / "neighbor-home"
    owned_home.mkdir()
    neighbor_home.mkdir()
    ready, finished = tmp_path / "ready.json", tmp_path / "finished"
    script = r"""
import asyncio, json, os, sys
from pathlib import Path
from omnigent.harnesses.codex_native.app_server import CodexNativeAppServer
from omnigent.inner import _proc
from omnigent.runner._entry import _install_signal_handlers
async def main():
    home, ready, finished = map(Path, sys.argv[2:5])
    env = dict(os.environ, CODEX_HOME=str(home))
    proc = await asyncio.create_subprocess_exec(
        sys.argv[1], 'app-server', env=env, cwd=str(home),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL, **_proc.spawn_kwargs(),
    )
    server = CodexNativeAppServer(
        codex_path=sys.argv[1], socket_path=home/'unused.sock', codex_home=home,
        env=env, config_overrides=[], cwd=home, bridge_dir=home, proc=proc,
    )
    event = asyncio.Event()
    listener = _install_signal_handlers(event)
    try:
        initialize = {
            'id': 1, 'method': 'initialize',
            'params': {'clientInfo': {'name': 'shutdown-smoke', 'version': '1'}},
        }
        proc.stdin.write((json.dumps(initialize)+'\n').encode())
        await proc.stdin.drain()
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
            if not line:
                raise RuntimeError('Codex exited before initialize response')
            response = json.loads(line)
            if response.get('id') == 1:
                if 'error' in response:
                    raise RuntimeError(response['error'])
                break
        ready.write_text(json.dumps({'codex_pid': proc.pid, 'runner_pid': os.getpid()}))
        await event.wait()
    finally:
        await server.close()
        listener.close()
    finished.write_text('native Codex closed during runner cleanup')
asyncio.run(main())
"""
    neighbor = subprocess.Popen(
        [executable, "app-server"],
        env=dict(os.environ, CODEX_HOME=str(neighbor_home)),
        cwd=neighbor_home,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    runner = subprocess.Popen(
        [sys.executable, "-c", script, executable, str(owned_home), str(ready), str(finished)],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        deadline = time.monotonic() + 20
        while not ready.exists():
            assert runner.poll() is None, "Owned runner exited before native initialization"
            assert time.monotonic() < deadline, "Owned native Codex did not initialize"
            time.sleep(0.02)
        codex_pid = json.loads(ready.read_text())["codex_pid"]
        assert psutil.Process(codex_pid).is_running()
        assert neighbor.poll() is None
        HostProcess._stop_runner_proc(runner)
        assert runner.poll() == 0
        assert not psutil.pid_exists(codex_pid)
        assert finished.read_text() == "native Codex closed during runner cleanup"
        assert neighbor.poll() is None
    finally:
        stop_processes([runner, neighbor], grace_seconds=0)
        for process in (runner, neighbor):
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=3)
        if neighbor.stdin is not None:
            neighbor.stdin.close()
