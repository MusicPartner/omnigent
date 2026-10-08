"""Windows-only env-var adjustments for native terminal launches."""

from __future__ import annotations

import os


def psmux_claude_env_unset() -> list[str]:
    """Env vars to unset so psmux doesn't break Claude's auth lookup.

    psmux 3.3.8 turns an absent ``CLAUDE_CONFIG_DIR`` into an empty string in
    panes; Claude treats empty as an override and stops finding ``~/.claude``
    auth.
    """
    if not os.environ.get("CLAUDE_CONFIG_DIR"):
        return ["CLAUDE_CONFIG_DIR"]
    return []
