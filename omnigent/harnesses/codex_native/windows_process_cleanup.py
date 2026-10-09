"""Windows cleanup for a native Codex session being resumed."""

from __future__ import annotations

import logging
import ntpath
import os
from pathlib import Path

import psutil

_logger = logging.getLogger(__name__)


def reap_windows_codex_processes_for_state_dir(state_dir: Path, *, grace_s: float) -> int:
    """Take over this session's Windows writers after the caller cancels its forwarder."""
    expected_home = ntpath.normcase(ntpath.normpath(str(state_dir / "codex-home")))
    protected_pids = {os.getpid(), *(parent.pid for parent in psutil.Process().parents())}
    victims: dict[int, tuple[psutil.Process, float, int]] = {}
    matched_servers = 0
    for candidate in psutil.process_iter():
        try:
            process = psutil.Process(candidate.pid)
            identity = process.create_time()
            if process.pid in protected_pids or process.name().casefold() != "codex.exe":
                continue
            if process.cmdline()[1:2] != ["app-server"]:
                continue
            actual_home = process.environ().get("CODEX_HOME")
            if (
                actual_home is None
                or ntpath.normcase(ntpath.normpath(actual_home)) != expected_home
            ):
                continue
            if psutil.Process(process.pid).create_time() != identity:
                continue
            children = process.children(recursive=True)
            victims[process.pid] = (process, identity, process.pid)
            for child in children:
                try:
                    if child.pid not in protected_pids:
                        victims[child.pid] = (child, child.create_time(), process.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    stopped: list[psutil.Process] = []
    for process, identity, root_pid in reversed(list(victims.values())):
        try:
            # Construct a fresh handle: psutil caches create_time on existing objects.
            current = psutil.Process(process.pid)
            if current.create_time() != identity:
                continue
            if current.pid != root_pid and root_pid not in {
                parent.pid for parent in current.parents()
            }:
                continue
            if psutil.Process(root_pid).create_time() != victims[root_pid][1]:
                continue
            current.kill()
            stopped.append(current)
            if current.pid == root_pid:
                matched_servers += 1
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied as exc:
            raise RuntimeError(
                f"Cannot stop the Codex resume writer for session directory {state_dir}"
            ) from exc
    _gone, alive = psutil.wait_procs(stopped, timeout=grace_s)
    if alive:
        raise RuntimeError(f"Codex resume writer did not exit for session directory {state_dir}")
    if matched_servers:
        _logger.warning(
            "reaped %d stale codex app-server process(es) for state dir %s",
            matched_servers,
            state_dir.name,
        )
    return matched_servers
