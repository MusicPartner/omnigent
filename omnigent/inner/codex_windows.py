"""Windows-only Codex CLI resolution: prefer the native binary behind npm shims."""

from __future__ import annotations

from pathlib import Path

from omnigent._platform import resolve_cli_binary


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
