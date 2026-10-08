"""Windows python command builder for filesystem probes.

Windows has no reliable ``python3`` command; App alias stubs can be non-runnable.
"""

from __future__ import annotations

import base64
import subprocess


def windows_python_command(python: str, script: str) -> str:
    """Build a Windows-safe command string for ``python -c`` script execution.

    :param python: Interpreter path, normally the runner's ``sys.executable``.
    :param script: Python source to run.
    """
    encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
    bootstrap = (
        "exec(compile(__import__('base64').b64decode('"
        + encoded
        + "'),'omnigent-filesystem','exec'))"
    )
    return subprocess.list2cmdline([python, "-c", bootstrap])
