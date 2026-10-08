from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from omnigent.inner.datamodel import OSEnvSandboxSpec, OSEnvSpec, TerminalEnvSpec
from omnigent.terminals import TerminalRegistry
from omnigent.terminals import psmux as psmux_module
from omnigent.terminals.backend import PsmuxTerminalInstance, PsmuxTerminalMuxBackend
from omnigent.terminals.capture_bridge import _screen_snapshot_bytes, bridge_capture_to_websocket
from omnigent.terminals.ws_common import (
    WS_CLOSE_TERMINAL_DETACHED,
    WS_CLOSE_TERMINAL_NOT_FOUND,
)


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_backend_launch_send_read_close(tmp_path: Path) -> None:
    reg = TerminalRegistry(backend=PsmuxTerminalMuxBackend())
    spec = TerminalEnvSpec(
        command="powershell.exe",
        args=["-NoProfile", "-NoExit", "-Command", "Write-Output ready"],
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(tmp_path),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
    )
    instance = await reg.launch("conv_psmux", "shell", "s1", spec)
    try:
        assert instance.running is True
        read: dict[str, object] = {}
        for _ in range(75):
            await asyncio.sleep(0.2)
            read = await instance.read()
            if "ready" in str(read.get("screen", "")):
                break
        assert "ready" in str(read.get("screen", ""))
        assert isinstance(read.get("cursor_x"), int)
        assert isinstance(read.get("cursor_y"), int)
        assert isinstance(read.get("cursor_visible"), bool)
        sent = await instance.send("Write-Output hi", keys="Enter")
        assert sent == {"status": "sent"}
        for _ in range(75):
            await asyncio.sleep(0.2)
            read = await instance.read()
            if "hi" in str(read.get("screen", "")):
                break
        assert "hi" in str(read.get("screen", ""))
    finally:
        await reg.shutdown()


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_retains_dead_pane_output(tmp_path: Path) -> None:
    """A managed CLI exit keeps its final screen available for diagnosis."""
    reg = TerminalRegistry(backend=PsmuxTerminalMuxBackend())
    spec = TerminalEnvSpec(
        command="powershell.exe",
        args=["-NoProfile", "-Command", "Write-Output retained-output"],
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(tmp_path),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
        keep_alive_after_exit=True,
    )
    try:
        instance = await reg.launch("conv_psmux_retained", "shell", "s1", spec)
        read: dict[str, object] = {}
        for _ in range(50):
            await asyncio.sleep(0.1)
            read = await instance.read()
            if "retained-output" in str(read.get("screen", "")):
                break
        assert "retained-output" in str(read.get("screen", ""))
    finally:
        await reg.shutdown()


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_read_retains_ansi_styles_and_cursor(tmp_path: Path) -> None:
    reg = TerminalRegistry(backend=PsmuxTerminalMuxBackend())
    spec = TerminalEnvSpec(
        command=sys.executable,
        args=[
            "-c",
            (
                "import sys,time; "
                "sys.stdout.write('\\x1b[38;2;182;191;255mSELECTED\\x1b[0m\\n'); "
                "sys.stdout.flush(); time.sleep(30)"
            ),
        ],
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(tmp_path),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
    )
    instance = await reg.launch("conv_psmux_ansi", "shell", "s1", spec)
    try:
        read: dict[str, object] = {}
        for _ in range(75):
            await asyncio.sleep(0.1)
            read = await instance.read()
            if "SELECTED" in str(read.get("screen", "")):
                break
        screen = str(read.get("screen", ""))
        assert "SELECTED" in screen
        assert "38;2;182;191;255" in screen
        assert read["cursor_visible"] is True
    finally:
        await reg.shutdown()


async def test_psmux_read_preserves_styles_and_keeps_cursor_visible(tmp_path: Path) -> None:
    instance = PsmuxTerminalInstance(
        name="shell",
        session_key="s1",
        socket_path=tmp_path / "psmux.sock",
        private_dir=tmp_path,
        command="cmd.exe",
    )
    instance.running = True
    calls: list[tuple[str, ...]] = []

    async def tmux_output(*args: str) -> str:
        calls.append(args)
        if args[0] == "capture-pane":
            return "\x1b[38;2;182;191;255m/status\x1b[0m" if "-e" in args else "/status"
        if args[0] == "display-message":
            return "4,1"
        raise AssertionError(f"unexpected psmux command: {args}")

    instance._tmux_output = tmux_output  # type: ignore[method-assign]

    read = await instance.read()

    assert read["screen"] == "\x1b[38;2;182;191;255m/status\x1b[0m"
    assert read["cursor_x"] == 4
    assert read["cursor_y"] == 1
    assert read["cursor_visible"] is True
    assert ("capture-pane", "-t", instance.tmux_target, "-p", "-e") in calls


def test_capture_snapshot_preserves_ansi_styles_and_shows_cursor() -> None:
    snapshot = _screen_snapshot_bytes(
        "\x1b[38;2;182;191;255m/status\x1b[0m",
        cursor_x=4,
        cursor_y=1,
        cursor_visible=True,
    )

    assert b"\x1b[38;2;182;191;255m/status\x1b[0m" in snapshot
    assert snapshot.endswith(b"\x1b[2;5H\x1b[?25h")


def test_capture_snapshot_does_not_scroll_a_full_height_pane() -> None:
    rows = "".join(f"row{row}\n" for row in range(1, 25))
    snapshot = _screen_snapshot_bytes(
        rows,
        cursor_x=5,
        cursor_y=23,
        cursor_visible=True,
    )

    assert snapshot.count(b"\r\n") == 23
    assert b"row24\r\n\x1b[24;6H" not in snapshot
    assert snapshot.endswith(b"row24\x1b[24;6H\x1b[?25h")


def test_psmux_backend_rejects_outside_cwd_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(PsmuxTerminalMuxBackend, "validate_available", lambda self: None)
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    spec = TerminalEnvSpec(
        command="python",
        allow_cwd_override=True,
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(root),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
    )
    with pytest.raises(ValueError, match="outside the allowed root"):
        PsmuxTerminalMuxBackend().create("shell", "s1", spec, cwd_override=str(outside))


@pytest.mark.parametrize("terminal_os_env", [None, "inherit"])
def test_psmux_backend_resolves_inherited_parent_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_os_env: str | None,
) -> None:
    monkeypatch.setattr(PsmuxTerminalMuxBackend, "validate_available", lambda self: None)
    parent_cwd = tmp_path / "parent-workspace"
    parent_cwd.mkdir()
    spec = TerminalEnvSpec(command="python", os_env=terminal_os_env)
    instance, cwd = PsmuxTerminalMuxBackend().create(
        "shell",
        "s1",
        spec,
        parent_os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(parent_cwd),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
    )
    assert cwd == parent_cwd.resolve()
    shutil.rmtree(instance.private_dir, ignore_errors=True)


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_backend_strips_runner_auth_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from omnigent.runner.identity import RUNNER_AUTH_SECRET_ENV_VARS

    output_path = tmp_path / "runner-auth-env.txt"
    secret_env = {name: f"leaked-{name}" for name in RUNNER_AUTH_SECRET_ENV_VARS}
    for name, value in secret_env.items():
        monkeypatch.setenv(name, value)
    quoted_names = ",".join(f"'{name}'" for name in sorted(RUNNER_AUTH_SECRET_ENV_VARS))
    quoted_output = str(output_path).replace("'", "''")
    command = (
        f"foreach ($name in @({quoted_names})) {{ "
        "$value = [Environment]::GetEnvironmentVariable($name); "
        "if ($null -eq $value) { $value = '' }; "
        f"Add-Content -LiteralPath '{quoted_output}' -Value \"$name=$value\" "
        "}; Write-Output ready; Start-Sleep -Seconds 30"
    )
    reg = TerminalRegistry(backend=PsmuxTerminalMuxBackend())
    spec = TerminalEnvSpec(
        command="powershell.exe",
        args=["-NoProfile", "-Command", command],
        env=dict(secret_env),
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(tmp_path),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
    )
    try:
        await reg.launch("conv_psmux_secret", "shell", "s1", spec)
        for _ in range(50):
            if output_path.exists() and len(output_path.read_text().splitlines()) == len(
                RUNNER_AUTH_SECRET_ENV_VARS
            ):
                break
            await asyncio.sleep(0.1)
        assert output_path.exists()
        assert output_path.read_text().splitlines() == [
            f"{name}=" for name in sorted(RUNNER_AUTH_SECRET_ENV_VARS)
        ]
    finally:
        await reg.shutdown()


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_honors_env_unset_after_pane_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pane startup cannot reintroduce an explicitly excluded variable."""
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    output_path = tmp_path / "unset-result.txt"
    quoted_output = str(output_path).replace("'", "''")
    command = (
        "if (-not (Test-Path -LiteralPath Env:CLAUDE_CONFIG_DIR)) { "
        f"Set-Content -LiteralPath '{quoted_output}' -Value unset }} "
        f"else {{ Set-Content -LiteralPath '{quoted_output}' -Value set }}"
    )
    reg = TerminalRegistry(backend=PsmuxTerminalMuxBackend())
    spec = TerminalEnvSpec(
        command="powershell.exe",
        args=["-NoProfile", "-Command", command],
        env_unset=["CLAUDE_CONFIG_DIR"],
        os_env=OSEnvSpec(
            type="caller_process",
            cwd=str(tmp_path),
            sandbox=OSEnvSandboxSpec(type="none"),
        ),
        keep_alive_after_exit=True,
    )
    try:
        await reg.launch("conv_psmux_unset", "shell", "s1", spec)
        for _ in range(50):
            if output_path.exists():
                break
            await asyncio.sleep(0.1)
        assert output_path.read_text().strip() == "unset"
    finally:
        await reg.shutdown()


async def test_capture_bridge_streams_read_and_forwards_input() -> None:
    class FakeInstance:
        running = True

        def __init__(self) -> None:
            self.sent: list[tuple[str | None, str]] = []
            self.resizes: list[tuple[int, int]] = []

        async def read(self) -> dict[str, object]:
            return {
                "screen": "first\nsecond",
                "cursor_x": 4,
                "cursor_y": 1,
                "cursor_visible": False,
            }

        async def send(self, text: str | None = None, *, keys: str = "Enter") -> dict[str, str]:
            self.sent.append((text, keys))
            return {"status": "sent"}

        async def resize(self, *, cols: int, rows: int) -> None:
            self.resizes.append((cols, rows))

    class FakeWebSocket:
        def __init__(self) -> None:
            self.sent_bytes: list[bytes] = []
            self.close_code = 0
            self.closed = False
            self.frames: list[dict[str, object]] = [
                {"type": "websocket.receive", "text": '{"type":"resize","cols":100,"rows":40}'},
                {"type": "websocket.receive", "bytes": b"echo hi\r"},
                {"type": "websocket.disconnect"},
            ]

        async def send_bytes(self, data: bytes) -> None:
            self.sent_bytes.append(data)

        async def receive(self) -> dict[str, object]:
            await asyncio.sleep(0)
            return self.frames.pop(0)

        async def close(self, code: int = 1000, reason: str = "") -> None:
            del reason
            self.close_code = code
            self.closed = True

    instance = FakeInstance()
    ws = FakeWebSocket()
    await bridge_capture_to_websocket(
        ws,
        instance=instance,  # type: ignore[arg-type]
        read_only=False,
        poll_interval_s=0,
    )
    assert ws.sent_bytes[0].startswith(b"\x1b[H\x1b[2J")
    assert ws.sent_bytes[0] == b"\x1b[H\x1b[2Jfirst\r\nsecond\x1b[2;5H\x1b[?25l"
    assert ("echo hi", "Enter") in instance.sent
    assert (100, 40) in instance.resizes
    assert ws.closed is True
    assert ws.close_code == WS_CLOSE_TERMINAL_DETACHED


async def test_capture_bridge_closes_not_found_when_backend_dies() -> None:
    class DeadInstance:
        running = False

        async def is_alive(self) -> bool:
            return False

        async def read(self) -> dict[str, object]:
            raise AssertionError("dead backend must not be read")

    class WaitingWebSocket:
        def __init__(self) -> None:
            self.close_code = 0
            self.close_reason = ""

        async def send_bytes(self, data: bytes) -> None:
            del data

        async def receive(self) -> dict[str, object]:
            await asyncio.sleep(10)
            return {"type": "websocket.disconnect"}

        async def close(self, code: int = 1000, reason: str = "") -> None:
            self.close_code = code
            self.close_reason = reason

    ws = WaitingWebSocket()
    await bridge_capture_to_websocket(
        ws,
        instance=DeadInstance(),  # type: ignore[arg-type]
        read_only=False,
        poll_interval_s=0,
    )
    assert ws.close_code == WS_CLOSE_TERMINAL_NOT_FOUND
    assert ws.close_reason == "terminal session ended"


def test_psmux_backend_missing_binary_error_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    import omnigent.terminals.backend as backend
    import omnigent.terminals.psmux as psmux

    monkeypatch.setattr(psmux, "IS_WINDOWS", True)
    monkeypatch.setattr(psmux.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="Install psmux"):
        backend.PsmuxTerminalMuxBackend().validate_available()


def test_psmux_backend_reexport_preserves_identity() -> None:
    import omnigent.terminals as terminals_pkg
    import omnigent.terminals.backend as backend
    import omnigent.terminals.psmux as psmux

    assert backend.PsmuxTerminalMuxBackend is psmux.PsmuxTerminalMuxBackend
    assert backend.PsmuxTerminalInstance is psmux.PsmuxTerminalInstance
    assert terminals_pkg.PsmuxTerminalMuxBackend is psmux.PsmuxTerminalMuxBackend


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows launcher test")
def test_psmux_python_launcher_preserves_argv_environment_and_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launch_path = tmp_path / "launch.py"
    launch_path.write_text(psmux_module._PSMUX_CLEAN_ENV_SCRIPT, encoding="utf-8")
    output_path = tmp_path / "result.json"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "inherited-from-server")
    monkeypatch.setenv("OMNIGENT_PROBE_KEEP", "retained")
    # Isolated startup must ignore modules placed beside the launcher.
    (tmp_path / "subprocess.py").write_text("raise RuntimeError('shadowed')", encoding="utf-8")
    child_script = (
        "import json,os,pathlib,sys; "
        "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
        "'argv':sys.argv[2:], 'unset':os.getenv('CLAUDE_CONFIG_DIR'), "
        "'kept':os.getenv('OMNIGENT_PROBE_KEEP')}), encoding='utf-8'); sys.exit(37)"
    )
    payload = [
        json.dumps({"permissionMode": "default", "command": 'echo hi 2>> "log file"'}),
        '& | ^ ! %PATH% > 2>> "quoted" Å',
        "",
        "space and trailing slash\\\\",
    ]
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(launch_path),
            "1",
            "CLAUDE_CONFIG_DIR",
            sys.executable,
            "-I",
            "-c",
            child_script,
            str(output_path),
            *payload,
        ],
        cwd=tmp_path,
        check=False,
    )

    assert completed.returncode == 37
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result == {"argv": payload, "unset": None, "kept": "retained"}
    assert os.environ["CLAUDE_CONFIG_DIR"] == "inherited-from-server"


async def test_psmux_launch_uses_isolated_absolute_python_wrapper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "inherited")
    instance = PsmuxTerminalInstance(
        name="shell",
        session_key="s1",
        socket_path=tmp_path / "psmux.sock",
        private_dir=tmp_path,
        command=sys.executable,
        args=['{"command":"echo Å & | ^ ! %PATH% 2>> \\\\"log file\\\\""}', ""],
        env_unset=["CLAUDE_CONFIG_DIR"],
    )
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate.return_value = (b"", b"")
    spawn = AsyncMock(return_value=proc)
    monkeypatch.setattr(
        psmux_module,
        "asyncio",
        SimpleNamespace(create_subprocess_exec=spawn, subprocess=asyncio.subprocess),
    )
    await instance.launch(cwd=tmp_path)

    call = spawn.call_args
    argv = call.args
    wrapper = argv[argv.index("--") + 1 :]
    assert wrapper == (
        sys.executable,
        "-I",
        str((tmp_path / "launch.py").resolve()),
        "1",
        "CLAUDE_CONFIG_DIR",
        shutil.which(sys.executable) or sys.executable,
        *instance.args,
    )
    assert "CLAUDE_CONFIG_DIR" not in call.kwargs["env"]
    assert (tmp_path / "launch.py").read_text(
        encoding="utf-8"
    ) == psmux_module._PSMUX_CLEAN_ENV_SCRIPT


@pytest.mark.skipif(sys.platform != "win32", reason="native Windows psmux test")
@pytest.mark.skipif(shutil.which("psmux") is None, reason="psmux not installed")
async def test_windows_psmux_preserves_json_argv_and_clears_existing_server_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("OMNIGENT_PROBE_UNSET", raising=False)
    output_path = tmp_path / "result.json"
    seed_path = tmp_path / "seed.json"
    seed = PsmuxTerminalInstance(
        name="seed",
        session_key="s1",
        socket_path=tmp_path / "psmux.sock",
        private_dir=tmp_path,
        command=sys.executable,
        args=[
            "-I",
            "-c",
            (
                "import json,os,pathlib,sys,time; "
                "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
                "'config':os.getenv('CLAUDE_CONFIG_DIR'), "
                "'unset':os.getenv('OMNIGENT_PROBE_UNSET')})); time.sleep(60)"
            ),
            str(seed_path),
        ],
        env={"CLAUDE_CONFIG_DIR": "server-config", "OMNIGENT_PROBE_UNSET": "server-unset"},
    )
    payload = [
        json.dumps({"command": 'echo Å 2>> "log file"', "permissionMode": "default"}),
        '& | ^ ! %PATH% > 2>> "quoted"',
        "",
        "space and trailing slash\\",
    ]
    instance = PsmuxTerminalInstance(
        name="probe",
        session_key="s1",
        socket_path=seed.socket_path,
        private_dir=tmp_path,
        command=sys.executable,
        args=[
            "-I",
            "-c",
            (
                "import json,os,pathlib,sys; "
                "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
                "'argv':sys.argv[2:], 'config':os.getenv('CLAUDE_CONFIG_DIR'), "
                "'unset':os.getenv('OMNIGENT_PROBE_UNSET'), 'cwd':os.getcwd()}), "
                "encoding='utf-8'); sys.exit(37)"
            ),
            str(output_path),
            *payload,
        ],
        env_unset=["CLAUDE_CONFIG_DIR", "OMNIGENT_PROBE_UNSET"],
        keep_alive_after_exit=True,
    )
    try:
        await seed.launch(cwd=tmp_path)
        for _ in range(100):
            if seed_path.exists():
                break
            await asyncio.sleep(0.1)
        assert json.loads(seed_path.read_text()) == {
            "config": "server-config",
            "unset": "server-unset",
        }
        await instance._tmux("set-option", "-gq", "remain-on-exit", "on")
        await instance.launch(cwd=tmp_path)
        for _ in range(100):
            if output_path.exists():
                break
            await asyncio.sleep(0.1)
        assert json.loads(output_path.read_text(encoding="utf-8")) == {
            "argv": payload,
            "config": None,
            "unset": None,
            "cwd": str(tmp_path),
        }
        for _ in range(100):
            await instance._refresh_exit_status()
            if instance.last_exit_status() is not None:
                break
            await asyncio.sleep(0.1)
        assert instance.last_exit_status() == 37
    finally:
        await instance.close()
        await seed.close()
