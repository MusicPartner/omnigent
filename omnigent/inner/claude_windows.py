"""Windows Claude CLI resolution that avoids npm batch argument forwarding."""

from __future__ import annotations

from pathlib import Path

from omnigent._platform import resolve_cli_binary


def prefer_native_claude_exe(resolved: str) -> str:
    """Prefer the native executable behind a Claude npm shim when available.

    :param resolved: Resolved Claude executable or npm shim path.
    :returns: A native executable when found, otherwise the original path.
    """
    path = Path(resolved)
    if path.suffix.lower() not in {".cmd", ".bat"} or path.stem.lower() != "claude":
        return resolved
    candidate = (
        path.parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    )
    try:
        # npm can leave a script placeholder at this path when installation fails.
        with candidate.open("rb") as binary:
            if binary.read(2) == b"MZ":
                return str(candidate)
    except OSError:
        pass
    return resolve_cli_binary("claude.exe") or resolved
