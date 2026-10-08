"""Terminal multiplexer backend abstractions.

The current implementation is tmux-backed. This module introduces a small
backend seam so alternative multiplexers can be wired without changing the
registry contract that tools and runners already use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from omnigent._platform import IS_WINDOWS
from omnigent.inner.datamodel import OSEnvSpec, TerminalEnvSpec
from omnigent.inner.terminal import TerminalInstance, create_terminal_instance
from omnigent.terminals.psmux import PsmuxTerminalInstance, PsmuxTerminalMuxBackend

# Re-exported unconditionally: tests and omnigent.terminals import the psmux
# backend from here on every OS, not just Windows.
__all__ = [
    "PsmuxTerminalInstance",
    "PsmuxTerminalMuxBackend",
    "TerminalMuxBackend",
    "TmuxTerminalMuxBackend",
    "default_terminal_mux_backend",
]


class TerminalMuxBackend(Protocol):
    """Create terminal instances for a registry-managed multiplexer backend."""

    @property
    def name(self) -> str:
        """Stable backend identifier, e.g. ``"tmux"``."""
        ...

    def create(
        self,
        terminal_name: str,
        session_key: str,
        spec: TerminalEnvSpec,
        *,
        parent_os_env: OSEnvSpec | None = None,
        cwd_override: str | None = None,
        sandbox_override: str | None = None,
        conversation_link: str | None = None,
    ) -> tuple[TerminalInstance, Path]:
        """Create an unlaunched terminal instance and its resolved cwd."""
        ...


class TmuxTerminalMuxBackend:
    """Terminal backend that delegates to the existing tmux implementation."""

    @property
    def name(self) -> str:
        return "tmux"

    def create(
        self,
        terminal_name: str,
        session_key: str,
        spec: TerminalEnvSpec,
        *,
        parent_os_env: OSEnvSpec | None = None,
        cwd_override: str | None = None,
        sandbox_override: str | None = None,
        conversation_link: str | None = None,
    ) -> tuple[TerminalInstance, Path]:
        created = create_terminal_instance(
            terminal_name,
            session_key,
            spec,
            parent_os_env_spec=parent_os_env,
            cwd_override=cwd_override,
            sandbox_override=sandbox_override,
            conversation_link=conversation_link,
        )
        return created.instance, created.cwd


def default_terminal_mux_backend() -> TerminalMuxBackend:
    """Return the platform default terminal multiplexer backend."""
    if IS_WINDOWS:
        return PsmuxTerminalMuxBackend()
    return TmuxTerminalMuxBackend()
