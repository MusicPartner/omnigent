"""Direct Windows Python argv for filesystem probes.

Windows has no reliable ``python3`` command; App alias stubs can be non-runnable.
"""

from __future__ import annotations


def windows_python_argv(python: str, script: str) -> list[str]:
    """Build interpreter argv without sending the path or script through a shell.

    :param python: Interpreter path, normally the runner's ``sys.executable``.
    :param script: Python source to run.
    :returns: Interpreter, ``-c``, and the original script.
    """
    return [python, "-c", script]
