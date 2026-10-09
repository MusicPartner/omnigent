"""Native fixture factory sharing the private invocation-file implementation."""

from __future__ import annotations

import ctypes
import shutil
import uuid
from pathlib import Path

import pytest

from omnigent.inner.windows_exec_launcher import (
    _create_invocation,
    _known_profile,
    _private_security,
    _windows,
)

_OWNED_LAUNCHERS: set[Path] = set()


@pytest.fixture
def private_test_directory():
    """Use a private profile-root fixture; inherited AppData ACLs may be unsafe."""
    parent = _known_profile()
    path = parent / f"Omnigent-LauncherTests-{uuid.uuid4().hex}"
    kernel, security = _windows()
    attributes = _private_security(kernel, security)
    try:
        assert kernel.CreateDirectoryW(str(path), ctypes.byref(attributes))
    finally:
        kernel.LocalFree(attributes.descriptor)
    try:
        yield path
    finally:
        assert path.parent == parent and path.name.startswith("Omnigent-LauncherTests-")
        shutil.rmtree(path)


def create_private_job_launcher(
    source: str, interpreter: str, executable: Path, *, active: bool, directory: Path | None = None
) -> str:
    """Create a private executable/config stream; never bypass release gates in runtime."""
    launcher = Path(
        _create_invocation(source, interpreter, executable, active=active, directory=directory)
    )
    _OWNED_LAUNCHERS.add(launcher.resolve())
    return str(launcher)


def remove_private_job_launcher(launcher: str) -> None:
    """Unlink only a fixture-owned executable, including its attached config."""
    resolved = Path(launcher).resolve()
    if resolved not in _OWNED_LAUNCHERS:
        raise ValueError("Refusing to remove a directory not owned by the launcher factory")
    resolved.unlink()
    _OWNED_LAUNCHERS.remove(resolved)
