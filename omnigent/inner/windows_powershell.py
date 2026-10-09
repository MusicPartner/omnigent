"""Select a native PowerShell installation for Windows agent child processes."""

from __future__ import annotations

import logging
import ntpath
from collections.abc import Mapping
from pathlib import Path

from omnigent._platform import IS_WINDOWS

logger = logging.getLogger(__name__)


def _is_store_path(path: Path) -> bool:
    return any(part.casefold() == "windowsapps" for part in path.parts)


def _path_identity(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value.strip('"')))


def prepare_native_powershell_env(
    env: Mapping[str, str], *, installation_env: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Return a child environment preferring a non-Store ``pwsh.exe``.

    Standard PowerShell 7 installs take precedence over portable installs on
    PATH. Optional installation_env supplies discovery roots and inherited PATH
    for partial child environments, without forwarding other variables. Without
    compatible PowerShell 7, existing vendor shell fallback is preserved.
    """
    result = dict(env)
    if not IS_WINDOWS:
        return result

    path_keys = [key for key in result if key.casefold() == "path"]
    path_key = path_keys[0] if path_keys else "PATH"
    host_env = {key.casefold(): value for key, value in (installation_env or {}).items()}
    path_value = result[path_key] if path_keys else host_env.get("path", "")
    for key in path_keys[1:]:
        del result[key]
    entries = path_value.split(";") if path_value else []
    folded_env = dict(host_env)
    folded_env.update({key.casefold(): value for key, value in result.items()})
    candidates = [
        Path(root) / "PowerShell" / "7" / "pwsh.exe"
        for key in ("programw6432", "programfiles")
        if (root := folded_env.get(key))
    ]
    candidates.extend(Path(entry.strip('"')) / "pwsh.exe" for entry in entries if entry)

    store_found = False
    for candidate in candidates:
        try:
            candidate.lstat()
            if _is_store_path(candidate):
                store_found = True
                continue
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if _is_store_path(resolved):
                store_found = True
                continue
            if resolved.suffix.casefold() != ".exe":
                continue
        except (OSError, RuntimeError):
            continue
        preferred = str(resolved.parent)
        remaining = [
            entry for entry in entries if _path_identity(entry) != _path_identity(preferred)
        ]
        result[path_key] = ";".join([preferred, *remaining])
        logger.info("Selected native PowerShell for agent: %s", resolved)
        return result

    if store_found:
        logger.warning(
            "Only Microsoft Store PowerShell was found; retaining the vendor shell fallback. "
            "Install PowerShell 7 using the MSI installer in Program Files, or add a "
            "portable PowerShell directory containing pwsh.exe to PATH."
        )
    return result
