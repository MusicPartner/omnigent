from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from omnigent.runner import environment_filesystem
from omnigent.runner.python_probe import windows_python_argv


async def test_windows_probe_uses_argv_with_spaced_interpreter_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = 'print({"path": "Å & | ^ % ! > \\"quoted\\""})'
    python = r"C:\Program Files\Python\python.exe"
    monkeypatch.setattr(environment_filesystem.sys, "executable", python)
    monkeypatch.setattr(environment_filesystem, "IS_WINDOWS", True)
    os_env = AsyncMock()
    os_env.cwd = tmp_path
    os_env.sandbox = None
    os_env.launch_command.return_value = {"stdout": "probe", "exit_code": 0}

    result = await environment_filesystem.CallerProcessFilesystem(os_env)._run_python_probe(script)

    assert result == {"stdout": "probe", "exit_code": 0}
    os_env.launch_command.assert_awaited_once_with([python, "-c", script])
    os_env.shell.assert_not_awaited()


def test_windows_python_argv_preserves_script() -> None:
    python = r"C:\Program Files\Python\python.exe"
    script = 'print({"text": "quote \\" & | ^ ! % >"})'
    assert windows_python_argv(python, script) == [python, "-c", script]


async def test_posix_probe_keeps_sandbox_python3_shell_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = "print('filesystem probe')"
    monkeypatch.setattr(environment_filesystem, "IS_WINDOWS", False)
    os_env = AsyncMock()
    os_env.cwd = tmp_path
    os_env.sandbox = None

    await environment_filesystem.CallerProcessFilesystem(os_env)._run_python_probe(script)

    os_env.shell.assert_awaited_once_with(environment_filesystem._python_shell_command(script))
    os_env.launch_command.assert_not_awaited()


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows probe test")
async def test_windows_probe_executes_interpreter_installed_under_spaced_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json
    import venv

    from omnigent.inner.datamodel import OSEnvSandboxSpec, OSEnvSpec
    from omnigent.inner.os_env import create_os_environment

    python_dir = tmp_path / "Python With Spaces"
    venv.EnvBuilder(with_pip=False).create(python_dir)
    python = str(python_dir / "Scripts" / "python.exe")
    payload = json.dumps({"text": 'Å & | ^ ! %PATH% 2>> "quoted"'})
    script = (
        f"import os; print({payload!r}); "
        "print(os.getcwd()); print(os.getenv('OMNIGENT_PROBE_KEEP'))"
    )
    monkeypatch.setenv("OMNIGENT_PROBE_KEEP", "retained")
    os_env = create_os_environment(
        OSEnvSpec(type="caller_process", cwd=str(tmp_path), sandbox=OSEnvSandboxSpec(type="none"))
    )
    assert os_env is not None
    try:
        result = await os_env.launch_command(windows_python_argv(python, script))
    finally:
        os_env.close()

    assert result["exit_code"] == 0, result
    assert result["stdout"].splitlines() == [payload, str(tmp_path), "retained"]
