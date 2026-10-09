"""Owned Windows host shutdown through the headless notification endpoint."""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from pathlib import Path

import pytest

from omnigent.host.connect import HostProcess, _RunnerHandle
from omnigent.inner.windows_process_shutdown import request_shutdown, stop_processes

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows shutdown endpoint")


def _wait_file(path: Path, proc: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 15
    while not path.exists():
        assert proc.poll() is None, "Owned test process exited before it was ready"
        assert time.monotonic() < deadline, "Owned test process did not become ready"
        time.sleep(0.02)


def test_host_shutdown_runs_cleanup_once_without_a_console(tmp_path: Path) -> None:
    ready, finished = tmp_path / "ready", tmp_path / "finished"
    script = """
import asyncio, os, sys
from pathlib import Path
from omnigent.host.connect import _run_host_with_windows_shutdown
class Host:
    async def run(self):
        Path(sys.argv[1]).write_text(str(os.getpid()))
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0.2)
            Path(sys.argv[2]).write_text('cleaned')
asyncio.run(_run_host_with_windows_shutdown(Host()))
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", script, str(ready), str(finished)],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        _wait_file(ready, proc)
        listener_pid = int(ready.read_text())
        assert request_shutdown(listener_pid)
        request_shutdown(listener_pid)
        assert proc.wait(timeout=10) == 0
        assert finished.read_text() == "cleaned"
    finally:
        stop_processes([proc], grace_seconds=0)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=3)


def test_host_batch_shutdown_runs_every_runner_cleanup_and_preserves_neighbor(
    tmp_path: Path,
) -> None:
    script = """
import asyncio, sys
from pathlib import Path
from omnigent.runner._entry import _install_signal_handlers
async def main():
    event = asyncio.Event()
    listener = _install_signal_handlers(event)
    try:
        Path(sys.argv[1]).touch()
        await event.wait()
        await asyncio.sleep(0.1)
        Path(sys.argv[2]).write_text('cleaned')
    finally:
        listener.close()
asyncio.run(main())
"""
    procs = []
    neighbor = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    host = object.__new__(HostProcess)
    host._runners = {}
    try:
        for index in range(3):
            ready, finished = tmp_path / f"ready{index}", tmp_path / f"finished{index}"
            proc = subprocess.Popen(
                [sys.executable, "-c", script, str(ready), str(finished)],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            procs.append(proc)
            host._runners[str(index)] = _RunnerHandle(proc=proc, log_path=tmp_path / "log")
            _wait_file(ready, proc)
        host._cleanup_runners()
        assert host._runners == {}
        assert all(proc.poll() == 0 for proc in procs)
        assert all((tmp_path / f"finished{index}").read_text() == "cleaned" for index in range(3))
        assert neighbor.poll() is None
    finally:
        stop_processes([*procs, neighbor], grace_seconds=0)
        for proc in [*procs, neighbor]:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=3)
