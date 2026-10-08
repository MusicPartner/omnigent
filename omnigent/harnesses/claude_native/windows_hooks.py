"""Windows-only Claude Code hook command builders for the native bridge.

Native Windows has no portable equivalent of the POSIX hook pipelines, so
these commands invoke the stdlib hook scripts directly instead.
"""

from __future__ import annotations

import base64
from pathlib import Path

from omnigent.native.shell import shell_join


def message_display_command(python: str, bridge_dir: Path) -> str:
    """Build the Windows ``MessageDisplay`` hook command.

    :param python: Python executable to run the hook module with.
    :param bridge_dir: Bridge directory passed to the hook as ``--bridge-dir``.
    :returns: Shell-joined command string.
    """
    return shell_join(
        [
            python,
            "-I",
            "-m",
            "omnigent.harnesses.claude_native.message_display_hook",
            "--bridge-dir",
            str(bridge_dir),
        ]
    )


def status_line_command(python: str, bridge_dir: Path, chain_command: str | None) -> str:
    """Build the Windows ``statusLine`` hook command.

    :param python: Python executable to run the hook module with.
    :param bridge_dir: Bridge directory passed to the hook as ``--bridge-dir``.
    :param chain_command: User's globally-configured statusLine command, if
        any. Base64-encoded into ``--chain-b64`` so the hook module can chain
        to it after capturing Claude's stdin.
    :returns: Shell-joined command string.
    """
    status_parts = [
        python,
        "-I",
        "-m",
        "omnigent.harnesses.claude_native.status",
        "--bridge-dir",
        str(bridge_dir),
    ]
    if chain_command is not None:
        chain_b64 = base64.b64encode(chain_command.encode("utf-8")).decode("ascii")
        status_parts.extend(["--chain-b64", chain_b64])
    return shell_join(status_parts)
