"""Native Windows supplied-environment content-search transport regression."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from omnigent._platform import IS_WINDOWS
from omnigent.inner.datamodel import OSEnvSandboxSpec, OSEnvSpec
from omnigent.inner.os_env import CallerProcessOSEnvironment, OSEnvironment, create_os_environment
from omnigent.runner.content_search import _SEARCH_SCRIPT, search_content
from omnigent.runner.environment_filesystem import _python_shell_command
from omnigent.runner.python_probe import windows_python_argv


@pytest.mark.parametrize(("windows", "local"), [(True, True), (False, True), (True, False)])
@pytest.mark.asyncio
async def test_content_search_transport_follows_execution_environment(
    monkeypatch: pytest.MonkeyPatch, windows: bool, local: bool
) -> None:
    environment = Mock(spec=CallerProcessOSEnvironment if local else OSEnvironment)
    environment.shell = AsyncMock(return_value={"stdout": '{"matches": []}'})
    environment.launch_command = AsyncMock(return_value={"stdout": '{"matches": []}'})
    monkeypatch.setattr("omnigent.runner.content_search.IS_WINDOWS", windows)
    assert await search_content(environment, "needle") == {"matches": []}
    script = (
        "query = 'needle'\ncase_sensitive = False\n"
        "regex = False\nlimit = 500\nglob_args = []\n" + _SEARCH_SCRIPT
    )
    if windows and local:
        environment.launch_command.assert_awaited_once_with(
            [sys.executable, "-I", "-X", "utf8", "-c", script],
            timeout=20,
            max_output=4 * 1024 * 1024,
        )
        environment.shell.assert_not_awaited()
    else:
        environment.shell.assert_awaited_once_with(
            _python_shell_command(script), timeout=20, max_output=4 * 1024 * 1024
        )
        environment.launch_command.assert_not_awaited()


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows shell transport regression")
@pytest.mark.skipif(shutil.which("rg") is None, reason="ripgrep is required")
@pytest.mark.asyncio
async def test_windows_content_search_uses_supplied_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()
    nested = workspace / "répertoire"
    nested.mkdir()
    (nested / "sample.txt").write_text("😀 synthetic-marker\n", encoding="utf-8")
    environment = create_os_environment(
        OSEnvSpec(
            type="caller_process",
            cwd=str(workspace),
            sandbox=OSEnvSandboxSpec(type="none"),
        )
    )
    assert environment is not None
    try:
        probe = await environment.shell("echo synthetic-marker", timeout=5, max_output=4096)
        assert probe.get("exit_code") == 0, probe
        assert "synthetic-marker" in probe.get("stdout", ""), probe
        direct = await environment.launch_command(
            windows_python_argv(sys.executable, "print('synthetic-marker')"),
            timeout=5,
            max_output=4096,
        )
        assert direct.get("exit_code") == 0, direct
        assert "synthetic-marker" in direct.get("stdout", ""), direct
        result = await search_content(environment, "synthetic-marker")
        assert "error" not in result, result
        assert [(match["path"], match["line"]) for match in result["matches"]] == [
            ("répertoire/sample.txt", 1)
        ]
        assert result["matches"][0]["column"] == 4
    finally:
        environment.close()
