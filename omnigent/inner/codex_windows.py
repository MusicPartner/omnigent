"""Windows-only Codex CLI resolution: prefer the native binary behind npm shims."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from omnigent._platform import IS_WINDOWS, resolve_cli_binary


def prefer_native_codex_exe(resolved: str) -> str:
    """Resolve an npm ``.cmd``/``.bat`` codex shim to the native binary, if found.

    :param resolved: Path returned by :func:`resolve_cli_binary` for ``"codex"``.
    :returns: A native ``codex.exe`` path when one can be found, else ``resolved``.
    """
    path = Path(resolved)
    if path.suffix.lower() not in {".cmd", ".bat"}:
        return resolved

    # Passing TOML/JSON-valued ``-c`` arguments through an npm batch shim lets
    # cmd.exe split their embedded spaces. The npm package ships the real Rust
    # binary below the shim; invoke it directly so argv reaches Codex unchanged.
    package_root = path.parent / "node_modules" / "@openai" / "codex"
    try:
        native_candidates = sorted(package_root.glob("**/vendor/**/codex.exe"))
    except OSError:
        native_candidates = []
    for candidate in native_candidates:
        if candidate.is_file():
            return str(candidate)

    native_on_path = resolve_cli_binary("codex.exe")
    return native_on_path or resolved


CODEX_WINDOWS_SANDBOX_ENV_VAR = "OMNIGENT_CODEX_WINDOWS_SANDBOX"


def native_codex_windows_sandbox(env: Mapping[str, str] | None = None) -> str | None:
    """Resolve the host's explicit sandbox override for native Omnigent sessions."""
    if not IS_WINDOWS:
        return None
    value = (os.environ if env is None else env).get(CODEX_WINDOWS_SANDBOX_ENV_VAR)
    if value is None:
        return None
    if value not in {"elevated", "unelevated"}:
        raise ValueError(f"{CODEX_WINDOWS_SANDBOX_ENV_VAR} must be 'elevated' or 'unelevated'")
    return value
