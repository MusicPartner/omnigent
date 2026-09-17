from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

import pytest

from omnigent.inner.datamodel import OSEnvSandboxSpec, OSEnvSpec, TerminalEnvSpec
from omnigent.terminals import TerminalRegistry
from omnigent.terminals.backend import PsmuxTerminalMuxBackend
from omnigent.terminals.capture_bridge import bridge_capture_to_websocket
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
            if output_path.exists():
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

    monkeypatch.setattr(backend, "IS_WINDOWS", True)
    monkeypatch.setattr(backend.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="Install psmux"):
        backend.PsmuxTerminalMuxBackend().validate_available()
