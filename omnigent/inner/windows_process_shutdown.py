"""Headless Windows shutdown requests and bounded owned-process cleanup."""

from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any

import psutil

_logger = logging.getLogger(__name__)
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_EVENT_MODIFY_STATE = 0x0002
_WAIT_OBJECT_0 = 0
_INFINITE = 0xFFFFFFFF
_WINDOWS_EPOCH_SECONDS = 11644473600


def _windows_ctypes(name: str) -> Any:
    return getattr(ctypes, name)


@lru_cache(maxsize=1)
def _kernel32() -> Any:
    from ctypes import wintypes

    kernel = _windows_ctypes("WinDLL")("kernel32", use_last_error=True)
    signatures = {
        "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        "GetProcessTimes": (
            [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)],
            wintypes.BOOL,
        ),
        "CreateEventW": (
            [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR],
            wintypes.HANDLE,
        ),
        "OpenEventW": ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetEvent": ([wintypes.HANDLE], wintypes.BOOL),
        "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = arguments
        function.restype = result
    return kernel


def _creation_ticks(handle: object) -> int:
    from ctypes import wintypes

    values = [wintypes.FILETIME() for _ in range(4)]
    if not _kernel32().GetProcessTimes(handle, *(ctypes.byref(value) for value in values)):
        raise _windows_ctypes("WinError")(_windows_ctypes("get_last_error")())
    return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime


def _event_name(pid: int, ticks: int) -> str:
    return f"Local\\OmnigentShutdown-{pid}-{ticks:x}"


class ShutdownListener:
    """A one-shot shutdown listener whose kernel handle closes with its thread."""

    def __init__(self, callback: Callable[[], None]) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows shutdown listeners require Windows")
        kernel = _kernel32()
        process = kernel.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, os.getpid())
        if not process:
            raise _windows_ctypes("WinError")(_windows_ctypes("get_last_error")())
        try:
            name = _event_name(os.getpid(), _creation_ticks(process))
        finally:
            kernel.CloseHandle(process)
        self._handle = kernel.CreateEventW(None, True, False, name)
        if not self._handle:
            raise _windows_ctypes("WinError")(_windows_ctypes("get_last_error")())
        self._closed = threading.Event()
        self._lock = threading.Lock()
        self._callback = callback
        self._thread = threading.Thread(target=self._wait, name="windows-shutdown", daemon=True)
        try:
            self._thread.start()
        except BaseException:
            kernel.CloseHandle(self._handle)
            raise

    def _wait(self) -> None:
        kernel = _kernel32()
        try:
            result = kernel.WaitForSingleObject(self._handle, _INFINITE)
            if result == _WAIT_OBJECT_0 and not self._closed.is_set():
                try:
                    self._callback()
                except Exception:
                    _logger.exception("Windows shutdown callback failed")
        finally:
            with self._lock:
                kernel.CloseHandle(self._handle)
                self._handle = None

    def close(self) -> None:
        """Wake and join the listener without invoking its shutdown callback."""
        self._closed.set()
        with self._lock:
            if self._handle:
                _kernel32().SetEvent(self._handle)
        if threading.current_thread() is not self._thread:
            self._thread.join()

    def __enter__(self) -> ShutdownListener:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def install_shutdown_listener(callback: Callable[[], None]) -> ShutdownListener:
    """Register a console-independent shutdown callback for this Windows process."""
    return ShutdownListener(callback)


def request_shutdown(pid: int, expected_create_time: float | None = None) -> bool:
    """Signal the event of this exact process incarnation, if registered."""
    if sys.platform != "win32" or pid <= 0 or pid == os.getpid():
        return False
    try:
        observed = psutil.Process(pid).create_time()
        if expected_create_time is not None and observed != expected_create_time:
            return False
        kernel = _kernel32()
        process = kernel.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not process:
            return False
        try:
            ticks = _creation_ticks(process)
            # Validate the opened handle as well as the preceding process lookup.
            if (
                psutil.Process(pid).create_time() != observed
                or abs(ticks / 10_000_000 - _WINDOWS_EPOCH_SECONDS - observed) > 0.00001
            ):
                return False
            event = kernel.OpenEventW(_EVENT_MODIFY_STATE, False, _event_name(pid, ticks))
            if not event:
                return False
            try:
                return bool(kernel.SetEvent(event))
            finally:
                kernel.CloseHandle(event)
        finally:
            kernel.CloseHandle(process)
    except (OSError, psutil.Error):
        return False


def _owned_process(pid: int, birth: float) -> psutil.Process | None:
    try:
        process = psutil.Process(pid)
        if process.create_time() != birth or process.status() == psutil.STATUS_ZOMBIE:
            return None
        return process
    except psutil.NoSuchProcess:
        return None


class ShutdownProcessScope:
    """Captured process identities that survive root exits and PID reuse."""

    def __init__(self, processes: Sequence[subprocess.Popen | psutil.Process]) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows process shutdown requires Windows")
        self._protected = {os.getpid()}
        self._protected.update(process.pid for process in psutil.Process().parents())
        self._known: dict[int, tuple[float, int]] = {}
        self._requested: set[tuple[int, float]] = set()
        self._refused = False
        for handle in processes:
            if handle.pid in self._protected:
                self._refused = True
                continue
            try:
                if isinstance(handle, subprocess.Popen) and handle.poll() is not None:
                    continue
                process = psutil.Process(handle.pid)
                if (
                    isinstance(handle, psutil.Process)
                    and process.create_time() != handle.create_time()
                ):
                    self._refused = True
                    continue
                self._observe(process, 0)
            except psutil.NoSuchProcess:
                continue
            except psutil.Error:
                self._refused = True
        self.refresh()

    def _observe(self, process: psutil.Process, depth: int) -> None:
        if process.pid in self._protected:
            return
        try:
            birth = process.create_time()
            if process.status() == psutil.STATUS_ZOMBIE:
                return
        except psutil.NoSuchProcess:
            return
        except psutil.Error:
            self._refused = True
            return
        if process.pid not in self._known:
            self._known[process.pid] = (birth, depth)

    def refresh(self) -> None:
        """Capture new children of still-owned identities without signaling."""
        pending = list(self._known)
        visited: set[int] = set()
        while pending:
            pid = pending.pop()
            if pid in visited:
                continue
            visited.add(pid)
            birth, depth = self._known[pid]
            try:
                process = _owned_process(pid, birth)
                if process is None:
                    continue
                for child in process.children():
                    self._observe(child, depth + 1)
                    if child.pid in self._known and child.pid not in visited:
                        pending.append(child.pid)
            except psutil.NoSuchProcess:
                continue
            except psutil.Error:
                self._refused = True

    def _alive(self) -> list[tuple[int, float, int]]:
        remaining = []
        for pid, (birth, depth) in self._known.items():
            try:
                if _owned_process(pid, birth) is not None:
                    remaining.append((pid, birth, depth))
            except psutil.AccessDenied:
                remaining.append((pid, birth, depth))
        return remaining

    def request(self) -> None:
        """Fan out graceful requests to all newly captured live identities."""
        self.refresh()
        for pid, birth, _depth in self._alive():
            identity = (pid, birth)
            if identity not in self._requested and request_shutdown(
                pid, expected_create_time=birth
            ):
                self._requested.add(identity)

    def kill(self, *, kill_seconds: float = 3.0) -> bool:
        """Force captured survivors leaves-first and wait a bounded interval."""
        self.refresh()
        for pid, birth, _depth in sorted(self._alive(), key=lambda item: item[2], reverse=True):
            try:
                process = _owned_process(pid, birth)
                if process is not None:
                    process.kill()
            except psutil.Error:
                continue
        deadline = time.monotonic() + max(0.0, kill_seconds)
        while self._alive() and time.monotonic() < deadline:
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
        return not self._alive() and not self._refused


def snapshot_processes(
    processes: Sequence[subprocess.Popen | psutil.Process],
) -> ShutdownProcessScope:
    """Capture owned roots and descendants without requesting shutdown."""
    return ShutdownProcessScope(processes)


def stop_processes(
    processes: Sequence[subprocess.Popen | psutil.Process],
    *,
    grace_seconds: float = 30.0,
    kill_seconds: float = 3.0,
    force: bool = True,
) -> bool:
    """Request shutdown together, retain descendants, and bound cleanup."""
    try:
        scope = snapshot_processes(processes)
    except psutil.Error:
        return False
    deadline = time.monotonic() + max(0.0, grace_seconds)
    while True:
        scope.request()
        if not scope._alive():
            return not scope._refused
        if time.monotonic() >= deadline:
            break
        time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
    if not force:
        return False
    return scope.kill(kill_seconds=kill_seconds)


def stop_process(
    pid: int,
    *,
    expected_create_time: float | None = None,
    grace_seconds: float = 30.0,
    kill_seconds: float = 3.0,
    force: bool = True,
) -> bool:
    """Stop one PID and its descendants, preserving the captured identity."""
    if pid <= 0:
        return False
    try:
        if pid == os.getpid() or pid in {parent.pid for parent in psutil.Process().parents()}:
            return False
        process = psutil.Process(pid)
        birth = process.create_time()
        if expected_create_time is not None and birth != expected_create_time:
            return False
    except psutil.NoSuchProcess:
        return True
    except psutil.Error:
        return False
    return stop_processes(
        [process], grace_seconds=grace_seconds, kill_seconds=kill_seconds, force=force
    )
