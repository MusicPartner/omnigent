from __future__ import annotations

import base64

from omnigent.runner import environment_filesystem
from omnigent.runner.python_probe import windows_python_command


def _extract_bootstrap_base64(command: str) -> str:
    marker = "b64decode('"
    start = command.index(marker) + len(marker)
    end = command.index("')", start)
    return command[start:end]


def test_windows_python_command_uses_runner_interpreter_and_embeds_script(
    monkeypatch,
) -> None:
    script = "print('filesystem probe')"

    command = windows_python_command(r"C:\Program Files\Python\python.exe", script)

    assert command.startswith('"C:\\Program Files\\Python\\python.exe" -c ')
    encoded = _extract_bootstrap_base64(command)
    assert base64.b64decode(encoded).decode("utf-8") == script


def test_python_shell_command_switches_by_platform_flag(monkeypatch) -> None:
    script = "print('filesystem probe')"
    python = r"C:\Program Files\Python\python.exe"
    monkeypatch.setattr(environment_filesystem.sys, "executable", python)

    monkeypatch.setattr(environment_filesystem, "IS_WINDOWS", True)
    assert environment_filesystem._python_shell_command(script) == windows_python_command(
        python, script
    )

    monkeypatch.setattr(environment_filesystem, "IS_WINDOWS", False)
    assert (
        environment_filesystem._python_shell_command(script)
        == "python3 -c 'print('\\''filesystem probe'\\'')'"
    )
