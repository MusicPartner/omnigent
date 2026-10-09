"""Shell command formatting shared by native-harness hook settings."""

from __future__ import annotations

import shlex
import subprocess

from omnigent._platform import IS_WINDOWS


def split_command(command: str, *, windows: bool) -> list[str]:
    """Split a command line into argv, Windows-path-safe.

    POSIX-mode ``shlex.split`` treats backslash as an escape character,
    which would mangle a Windows path's separators, so on ``windows``
    this splits in non-POSIX mode instead and then strips a single
    matching pair of wrapping quotes per token (non-POSIX mode leaves
    them in place, unlike POSIX mode).

    :param command: Shell-style command line to split.
    :param windows: Whether to use Windows-safe splitting.
    :returns: The split argv.
    :raises ValueError: If ``command`` has unbalanced quotes, same as
        :func:`shlex.split`.
    """
    tokens = shlex.split(command, posix=not windows)
    if not windows:
        return tokens
    return [
        token[1:-1]
        if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"')
        else token
        for token in tokens
    ]


def shell_join(parts: list[str], *, consumer: str | None = None) -> str:
    """Format argv for an explicit POSIX or PowerShell shell consumer.

    :param parts: Argument vector to serialize.
    :param consumer: Shell that interprets the resulting program. Omitted
        preserves the legacy host-based formatting for existing callers.
    :returns: Shell command string.
    :raises ValueError: If the consumer is unknown.
    """
    if consumer is None:
        if IS_WINDOWS:
            return subprocess.list2cmdline([part.replace("\\", "/") for part in parts])
        consumer = "posix"
    if consumer == "powershell":
        return "& " + " ".join("'" + part.replace("'", "''") + "'" for part in parts)
    if consumer != "posix":
        raise ValueError(f"Unknown shell consumer: {consumer}")
    return shlex.join(parts)
