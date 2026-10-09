"""Ownership and lifecycle checks for Windows same-session Codex cleanup."""

from pathlib import Path
from unittest.mock import Mock

import psutil
import pytest

from omnigent.harnesses.codex_native import windows_process_cleanup as cleanup


@pytest.fixture
def processes(monkeypatch: pytest.MonkeyPatch) -> dict[int, Mock]:
    """Supply isolated process identities; tests never enumerate the host."""
    known: dict[int, Mock] = {}
    caller = Mock(pid=1)
    caller.parents.return_value = [Mock(pid=2)]
    monkeypatch.setattr(cleanup.os, "getpid", lambda: 1)
    monkeypatch.setattr(
        cleanup.psutil, "Process", lambda pid=None: caller if pid is None else known[pid]
    )
    monkeypatch.setattr(cleanup.psutil, "process_iter", lambda: list(known.values()))
    monkeypatch.setattr(cleanup.psutil, "wait_procs", Mock(return_value=([], [])))
    return known


def server(pid: int, home: str) -> Mock:
    """Build a candidate with stable birth identity and native server arguments."""
    process = Mock(pid=pid)
    process.name.return_value = "codex.exe"
    process.cmdline.return_value = ["codex.exe", "app-server", "--listen", "ws://local"]
    process.environ.return_value = {"CODEX_HOME": home}
    process.create_time.return_value = float(pid)
    process.children.return_value = []
    process.parents.return_value = []
    return process


@pytest.mark.parametrize(
    "mismatch",
    [
        "neighbor",
        "missing-home",
        "denied-home",
        "non-codex",
        "tui",
        "exec-app-server",
        "self",
        "ancestor",
    ],
)
def test_cleanup_preserves_unowned_processes(processes: dict[int, Mock], mismatch: str) -> None:
    """A path prefix or server-looking command never establishes session ownership."""
    state = Path("C:/sessions/target")
    process = server(3, str(state / "codex-home"))
    if mismatch == "neighbor":
        process.environ.return_value = {"CODEX_HOME": "C:/sessions/target-other/codex-home"}
    elif mismatch == "missing-home":
        process.environ.return_value = {}
    elif mismatch == "denied-home":
        process.environ.side_effect = psutil.AccessDenied(3)
    elif mismatch == "non-codex":
        process.name.return_value = "python.exe"
    elif mismatch == "tui":
        process.cmdline.return_value = ["codex.exe", "resume", "thread"]
    elif mismatch == "exec-app-server":
        process.cmdline.return_value = ["codex.exe", "exec", "app-server"]
    elif mismatch == "self":
        process.pid = 1
    elif mismatch == "ancestor":
        process.pid = 2
    processes[process.pid] = process

    assert cleanup.reap_windows_codex_processes_for_state_dir(state, grace_s=0.1) == 0
    process.kill.assert_not_called()


def test_cleanup_reaps_exact_home_and_descendants(processes: dict[int, Mock]) -> None:
    """Windows case and separators normalize; descendants exit before their server."""
    state = Path("C:/sessions/target")
    root = server(3, "c:\\SESSIONS\\target\\codex-home")
    child = server(4, "irrelevant")
    child.name.return_value = "python.exe"
    child.parents.return_value = [root]
    root.children.return_value = [child]
    processes.update({3: root, 4: child})
    calls: list[int] = []
    root.kill.side_effect = lambda: calls.append(3)
    child.kill.side_effect = lambda: calls.append(4)

    assert cleanup.reap_windows_codex_processes_for_state_dir(state, grace_s=0.1) == 1
    assert calls == [4, 3]
    cleanup.psutil.wait_procs.assert_called_once_with([child, root], timeout=0.1)


def test_cleanup_preserves_reused_pid(processes: dict[int, Mock]) -> None:
    """A PID that changes birth identity after selection cannot be signalled."""
    state = Path("C:/sessions/target")
    process = server(3, str(state / "codex-home"))
    process.create_time.side_effect = [3.0, 3.0, 99.0]
    processes[3] = process
    assert cleanup.reap_windows_codex_processes_for_state_dir(state, grace_s=0.1) == 0
    process.kill.assert_not_called()


def test_cleanup_preserves_reparented_child(processes: dict[int, Mock]) -> None:
    """A descendant that no longer belongs to the selected server is preserved."""
    state = Path("C:/sessions/target")
    root = server(3, str(state / "codex-home"))
    child = server(4, "irrelevant")
    child.name.return_value = "python.exe"
    root.children.return_value = [child]
    processes.update({3: root, 4: child})
    assert cleanup.reap_windows_codex_processes_for_state_dir(state, grace_s=0.1) == 1
    child.kill.assert_not_called()


@pytest.mark.parametrize("failure", ["denied", "timeout"])
def test_cleanup_requires_confirmed_exit(processes: dict[int, Mock], failure: str) -> None:
    """History refresh must not proceed while its previous writer may still be alive."""
    state = Path("C:/sessions/target")
    root = server(3, str(state / "codex-home"))
    processes[3] = root
    if failure == "denied":
        root.kill.side_effect = psutil.AccessDenied(3)
    else:
        cleanup.psutil.wait_procs.return_value = ([], [root])
    with pytest.raises(RuntimeError, match="Codex resume writer"):
        cleanup.reap_windows_codex_processes_for_state_dir(state, grace_s=0.1)
