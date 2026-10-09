from __future__ import annotations

import sys

import pytest

from tests.terminals.windows_command_line import command_line_to_argv


@pytest.mark.skipif(sys.platform != "win32", reason="requires native Windows")
def test_command_line_parser_uses_windows_rules() -> None:
    parsed = command_line_to_argv(
        'claude.exe --settings "path with spaces Å" --mcp-config "{\\"x\\":1}"'
    )
    assert parsed == [
        "claude.exe",
        "--settings",
        "path with spaces Å",
        "--mcp-config",
        '{"x":1}',
    ]
