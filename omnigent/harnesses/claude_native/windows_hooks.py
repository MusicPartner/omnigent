"""Windows-only Claude Code hook command builders for the native bridge.

Native Windows has no portable equivalent of the POSIX hook pipelines, so
these commands invoke the stdlib hook scripts directly instead.
"""

from __future__ import annotations

import base64
import contextlib
import os
import runpy
import sys
import traceback
from pathlib import Path

from omnigent.native.shell import shell_join


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
        python.replace("\\", "/"),
        "-I",
        "-X",
        "utf8",
        "-m",
        "omnigent.harnesses.claude_native.status",
        "--bridge-dir",
        str(bridge_dir).replace("\\", "/"),
    ]
    if chain_command is not None:
        chain_b64 = base64.b64encode(chain_command.encode("utf-8")).decode("ascii")
        status_parts.extend(["--chain-b64", chain_b64])
    return shell_join(status_parts, consumer="posix")


def status_shell_command(command: str) -> list[str]:
    """Use Claude's Git Bash consumer when chaining a Windows status line."""
    configured = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    candidates = [configured] if configured else []
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(variable)
        if root:
            candidates.extend(
                [
                    str(Path(root) / "Git" / "bin" / "bash.exe"),
                    str(Path(root) / "Programs" / "Git" / "bin" / "bash.exe"),
                ]
            )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return [candidate, "-c", command]
    raise FileNotFoundError("Claude status-line chaining requires Git Bash")


def command_hook(parts: list[str], *, stderr_file: Path | None = None) -> dict[str, object]:
    """Transport a generated command through Claude's literal argument array."""
    if stderr_file is None:
        return {"type": "command", "command": parts[0], "args": ["-X", "utf8", *parts[1:]]}
    # The canonical caller supplies Python -I -m MODULE and its arguments.
    return {
        "type": "command",
        "command": parts[0],
        "args": [
            "-X",
            "utf8",
            "-I",
            "-m",
            __name__,
            "--stderr",
            str(stderr_file),
            "--",
            *parts[3:],
        ],
    }


def main(argv: list[str] | None = None) -> None:
    """Append stderr while retaining the target module's stdio and exit status."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 4 or args[0] != "--stderr" or args[2] != "--":
        raise SystemExit("Expected --stderr FILE -- MODULE [ARGS]")
    module = args[3]
    sys.argv = [module, *args[4:]]
    with open(args[1], "a", encoding="utf-8") as stderr:
        previous_fd = os.dup(2)
        try:
            os.dup2(stderr.fileno(), 2)
            with contextlib.redirect_stderr(stderr):
                try:
                    runpy.run_module(module, run_name="__main__", alter_sys=True)
                except Exception:  # noqa: BLE001 - retain interpreter traceback in stderr log
                    traceback.print_exc()
                    raise SystemExit(1) from None
                except SystemExit as exc:
                    if exc.code is not None and not isinstance(exc.code, int):
                        print(exc.code, file=sys.stderr)
                        raise SystemExit(1) from None
                    raise
        finally:
            stderr.flush()
            os.dup2(previous_fd, 2)
            os.close(previous_fd)


if __name__ == "__main__":
    main()
