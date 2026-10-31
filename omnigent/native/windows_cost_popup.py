"""PowerShell command encoding for the native cost popup on Windows."""

from __future__ import annotations

import base64
import json
from collections.abc import Callable


def windows_popup_command(argv: list[str], *, shell_join: Callable[..., str]) -> str:
    """Encode popup arguments for the isolated Python PowerShell consumer."""
    # Only ASCII base64 crosses PowerShell's native argument parser, including
    # older pwsh releases with legacy embedded-double-quote handling.
    payload = base64.b64encode(json.dumps(argv[4:], ensure_ascii=True).encode()).decode("ascii")
    bootstrap = (
        "import base64,json,runpy,sys;"
        "sys.argv=['omnigent.native.native_cost_popup',*json.loads(base64.b64decode(sys.argv[1]))];"
        "runpy.run_module('omnigent.native.native_cost_popup',run_name='__main__')"
    )
    return shell_join(
        [argv[0], "-I", "-X", "utf8", "-c", bootstrap, payload], consumer="powershell"
    )
