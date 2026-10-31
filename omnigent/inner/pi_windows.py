"""Windows-specific argv handling for the supported Pi npm shims."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable, Mapping


def windows_pi_spawn_argv(
    pi_path: str,
    env: Mapping[str, str],
    *,
    windows: bool,
    which: Callable[..., str | None],
) -> list[str]:
    """Bypass batch parsing for the two recognized Windows Pi npm packages."""
    shim = pathlib.Path(pi_path)
    if not windows or shim.suffix.lower() not in {".cmd", ".bat"} or shim.stem.lower() != "pi":
        return [pi_path]
    try:
        shim_text = shim.read_text(encoding="utf-8").replace("\\", "/")
    except (OSError, UnicodeError):
        return [pi_path]
    for package_name in ("@earendil-works/pi-coding-agent", "@mariozechner/pi-coding-agent"):
        package_root = shim.parent / "node_modules" / package_name
        try:
            metadata = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
            if not isinstance(metadata, dict) or not isinstance(metadata.get("bin"), dict):
                continue
            entry = metadata["bin"].get("pi")
            if not isinstance(entry, str):
                continue
            script = (package_root / entry).resolve()
            if not script.is_relative_to(package_root.resolve()) or not script.is_file():
                continue
            if f"/node_modules/{package_name}/{entry}" not in shim_text:
                continue
        except (OSError, ValueError, UnicodeError):
            continue
        adjacent_node = shim.parent / "node.exe"
        node = (
            str(adjacent_node)
            if adjacent_node.is_file()
            else which("node.exe", path=env.get("PATH", ""))
        )
        if node:
            # cmd.exe truncates multiline arguments and expands shell metacharacters.
            return [node, str(script)]
    return [pi_path]
