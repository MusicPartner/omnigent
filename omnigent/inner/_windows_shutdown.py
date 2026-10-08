"""Windows CTRL_BREAK signaling for cross-platform graceful shutdown.

Windows has no SIGTERM/process-group equivalent; a child spawned with
``CREATE_NEW_PROCESS_GROUP`` instead receives ``CTRL_BREAK_EVENT``, which
Python surfaces to it as ``SIGBREAK``.
"""

from __future__ import annotations

import os
import signal
from collections.abc import Callable
from types import FrameType

# Only exists on Windows; None elsewhere so this module still imports on POSIX.
CTRL_BREAK_EVENT = getattr(signal, "CTRL_BREAK_EVENT", None)
# Only exists on Windows; None elsewhere so this module still imports on POSIX.
SIGBREAK = getattr(signal, "SIGBREAK", None)


def send_ctrl_break(pid: int) -> bool:
    """Deliver CTRL_BREAK_EVENT to ``pid``'s process group on Windows."""
    if CTRL_BREAK_EVENT is None:
        return False
    try:
        os.kill(pid, CTRL_BREAK_EVENT)
    except Exception:  # noqa: BLE001 — pid not a console process group or already gone
        return False
    return True


def install_ctrl_break_handler(handler: Callable[[int, FrameType | None], object]) -> None:
    """Route Windows SIGBREAK (CTRL_BREAK_EVENT) to the same handler as SIGTERM.

    No-op off Windows, where ``SIGBREAK`` does not exist.
    """
    if SIGBREAK is not None:
        signal.signal(SIGBREAK, handler)
