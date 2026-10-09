"""Windows shutdown events preserve cleanup for headless owned process trees."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from omnigent.inner import windows_process_shutdown as shutdown


def test_request_rejects_recycled_pid_before_opening_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutdown.sys, "platform", "win32")
    monkeypatch.setattr(
        shutdown.psutil, "Process", lambda pid: SimpleNamespace(create_time=lambda: 2.0)
    )
    monkeypatch.setattr(shutdown, "_kernel32", lambda: pytest.fail("reused PID reached Win32"))
    assert not shutdown.request_shutdown(999999, expected_create_time=1.0)


def test_owned_process_rejects_recycled_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    process = SimpleNamespace(create_time=lambda: 2.0, status=lambda: psutil.STATUS_RUNNING)
    monkeypatch.setattr(shutdown.psutil, "Process", lambda pid: process)
    assert shutdown._owned_process(12345, 1.0) is None


def _spawn(script: str, *arguments: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-u", "-c", script, *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _ready(process: subprocess.Popen[str]) -> str:
    assert process.stdout is not None
    line = process.stdout.readline().strip()
    if not line:
        assert process.stderr is not None
        pytest.fail(f"child failed to initialize: {process.stderr.read()}")
    return line


def _cleanup(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        process.stderr.close()


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows named events")
def test_headless_event_runs_cleanup_once(tmp_path: Path) -> None:
    marker = tmp_path / "cleanup.txt"
    process = _spawn(
        "import os, pathlib, sys, threading\n"
        "from omnigent.inner.windows_process_shutdown import install_shutdown_listener\n"
        "stopped = threading.Event()\n"
        "count = []\n"
        "def stop():\n"
        "    count.append(1)\n"
        "    stopped.set()\n"
        "with install_shutdown_listener(stop):\n"
        "    print(os.getpid(), flush=True)\n"
        "    try:\n"
        "        assert stopped.wait(30)\n"
        "    finally:\n"
        "        pathlib.Path(sys.argv[1]).write_text(str(len(count)))\n",
        str(marker),
    )
    try:
        listener_pid = int(_ready(process))
        birth = psutil.Process(listener_pid).create_time()
        assert shutdown.request_shutdown(listener_pid, expected_create_time=birth)
        assert process.wait(timeout=5) == 0
        assert marker.read_text() == "1"
    finally:
        _cleanup(process)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows named events")
def test_close_listener_does_not_call_callback() -> None:
    called = []
    listener = shutdown.install_shutdown_listener(lambda: called.append(True))
    listener.close()
    listener.close()
    assert called == []
    assert not listener._thread.is_alive()


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_stubborn_owned_process_is_killed_and_neighbor_survives() -> None:
    script = "import time; print('ready', flush=True); time.sleep(30)"
    process = _spawn(script)
    neighbor = _spawn(script)
    try:
        assert _ready(process) == "ready"
        assert _ready(neighbor) == "ready"
        assert shutdown.stop_processes([process], grace_seconds=0.1, kill_seconds=3)
        assert process.wait(timeout=5) is not None
        assert neighbor.poll() is None
    finally:
        _cleanup(process)
        _cleanup(neighbor)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_no_force_leaves_unresponsive_owned_process_alive() -> None:
    process = _spawn("import time; print('ready', flush=True); time.sleep(30)")
    try:
        assert _ready(process) == "ready"
        assert not shutdown.stop_processes([process], grace_seconds=0.1, force=False)
        assert process.poll() is None
    finally:
        _cleanup(process)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows named events")
def test_root_exit_does_not_abandon_captured_child() -> None:
    process = _spawn(
        "import subprocess, sys, threading\n"
        "from omnigent.inner.windows_process_shutdown import install_shutdown_listener\n"
        "stopped = threading.Event()\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "with install_shutdown_listener(stopped.set):\n"
        "    print(child.pid, flush=True)\n"
        "    stopped.wait(30)\n",
    )
    child = None
    try:
        child = psutil.Process(int(_ready(process)))
        birth = child.create_time()
        assert shutdown.stop_processes([process], grace_seconds=0.3, kill_seconds=3)
        assert process.wait(timeout=5) == 0
        assert shutdown._owned_process(child.pid, birth) is None
    finally:
        _cleanup(process)
        if child is not None:
            try:
                child.kill()
                child.wait(timeout=5)
            except psutil.NoSuchProcess:
                pass


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_snapshot_never_captures_caller_or_ancestors() -> None:
    caller = psutil.Process()
    scope = shutdown.snapshot_processes([caller, *caller.parents()])
    assert scope._known == {}
    assert not scope.kill(kill_seconds=0)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows named events")
def test_snapshot_retains_child_after_separate_graceful_root_exit() -> None:
    process = _spawn(
        "import os, subprocess, sys, threading\n"
        "from omnigent.inner.windows_process_shutdown import install_shutdown_listener\n"
        "stopped = threading.Event()\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "with install_shutdown_listener(stopped.set):\n"
        "    print(os.getpid(), child.pid, flush=True)\n"
        "    stopped.wait(30)\n",
    )
    child = None
    try:
        root_pid, child_pid = map(int, _ready(process).split())
        child = psutil.Process(child_pid)
        birth = child.create_time()
        scope = shutdown.snapshot_processes([process])
        assert shutdown.request_shutdown(root_pid)
        assert process.wait(timeout=5) == 0
        assert child.is_running()
        assert scope.kill(kill_seconds=3)
        assert shutdown._owned_process(child.pid, birth) is None
    finally:
        _cleanup(process)
        if child is not None:
            try:
                child.kill()
                child.wait(timeout=5)
            except psutil.NoSuchProcess:
                pass


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows named events")
def test_shutdown_retries_listener_registered_during_startup(tmp_path: Path) -> None:
    marker = tmp_path / "cleanup.txt"
    process = _spawn(
        "import pathlib, sys, threading, time\n"
        "from omnigent.inner.windows_process_shutdown import install_shutdown_listener\n"
        "stopped = threading.Event()\n"
        "print('ready', flush=True)\n"
        "time.sleep(0.3)\n"
        "with install_shutdown_listener(stopped.set):\n"
        "    if stopped.wait(30):\n"
        "        pathlib.Path(sys.argv[1]).write_text('clean')\n",
        str(marker),
    )
    try:
        assert _ready(process) == "ready"
        assert shutdown.stop_processes([process], grace_seconds=3, kill_seconds=3)
        assert process.wait(timeout=5) == 0
        assert marker.read_text() == "clean"
    finally:
        _cleanup(process)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_public_stop_refuses_caller_and_ancestors() -> None:
    caller = psutil.Process()
    for process in [caller, *caller.parents()]:
        assert not shutdown.stop_process(process.pid, grace_seconds=0, kill_seconds=0)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_public_stop_refuses_mismatched_creation_time() -> None:
    process = _spawn("import time; print('ready', flush=True); time.sleep(30)")
    try:
        assert _ready(process) == "ready"
        birth = psutil.Process(process.pid).create_time()
        assert not shutdown.stop_process(
            process.pid, expected_create_time=birth - 1, grace_seconds=0, kill_seconds=0
        )
        assert process.poll() is None
    finally:
        _cleanup(process)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_unreadable_live_root_is_not_reported_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _spawn("import time; print('ready', flush=True); time.sleep(30)")
    original = psutil.Process.create_time

    def unreadable(handle: psutil.Process) -> float:
        if handle.pid == process.pid:
            raise psutil.AccessDenied(handle.pid)
        return original(handle)

    try:
        assert _ready(process) == "ready"
        monkeypatch.setattr(psutil.Process, "create_time", unreadable)
        assert not shutdown.stop_processes([process], grace_seconds=0, kill_seconds=0)
        assert process.poll() is None
    finally:
        _cleanup(process)


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows process cleanup")
def test_captured_root_reuse_is_refused_before_signaling(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _spawn("import time; print('ready', flush=True); time.sleep(30)")
    original = psutil.Process.create_time
    try:
        assert _ready(process) == "ready"
        captured = psutil.Process(process.pid)
        birth = captured.create_time()

        def reused(handle: psutil.Process) -> float:
            if handle.pid == process.pid:
                return birth if handle is captured else birth + 1
            return original(handle)

        monkeypatch.setattr(psutil.Process, "create_time", reused)
        monkeypatch.setattr(
            shutdown, "request_shutdown", lambda *a, **k: pytest.fail("reused PID")
        )
        assert not shutdown.stop_processes([captured], grace_seconds=0, kill_seconds=0)
        assert process.poll() is None
    finally:
        _cleanup(process)
