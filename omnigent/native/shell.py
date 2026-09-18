"""Shell command formatting shared by native-harness hook settings."""

from __future__ import annotations

import shlex
import subprocess

from omnigent._platform import IS_WINDOWS


def shell_join(parts: list[str]) -> str:
    """Join argv for the shell that executes native-harness hooks.

    Claude and the other native CLIs may execute hook commands through a
    POSIX shell even on Windows. Forward slashes keep native Windows paths
    intact in that shell and remain valid to Windows process APIs.

    :param parts: Argument vector to serialize.
    :returns: Shell command string.
    """
    if IS_WINDOWS:
        return subprocess.list2cmdline([part.replace("\\", "/") for part in parts])
    return shlex.join(parts)
