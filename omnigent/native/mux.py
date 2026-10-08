"""Platform selection for commands targeting local native terminal panes."""

from __future__ import annotations


def terminal_mux_command(socket_path: str, *, windows: bool) -> list[str]:
    """Build the command prefix for the host's terminal multiplexer.

    :param socket_path: Private multiplexer socket identifying the terminal.
    :param windows: Whether the terminal runs on native Windows.
    :returns: Multiplexer executable and socket arguments.
    """
    return ["psmux" if windows else "tmux", "-S", socket_path]


def terminal_mux_exit_status(raw_status: str | None, *, windows: bool) -> str | None:
    """Return only an exit status actually reported by the multiplexer.

    psmux's status field is a constant placeholder rather than the child's code.
    """
    return None if windows else raw_status
