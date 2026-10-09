"""Windows stop-session teardown with real processes owned by this test."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from omnigent.harnesses.codex_native.app_server import CodexNativeAppServer
from omnigent.inner import _proc
from omnigent.runner.native import orchestration
from tests.runner.test_native_interrupt_runner import _make_runner


async def _spawn_owned_server(home: Path) -> CodexNativeAppServer:
    """Hold a session file like a native writer without loading credentials."""
    home.mkdir()
    held_file = home / "writer.lock"
    script = (
        "import pathlib, sys, time\n"
        "with pathlib.Path(sys.argv[1]).open('w') as writer:\n"
        "    writer.write('ready')\n"
        "    writer.flush()\n"
        "    time.sleep(120)\n"
    )
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        script,
        str(held_file),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        **_proc.spawn_kwargs(),
    )
    server = CodexNativeAppServer(
        codex_path=sys.executable,
        socket_path=home / "unused.sock",
        codex_home=home,
        env={},
        config_overrides=[],
        cwd=home,
        bridge_dir=home,
        proc=proc,
    )
    try:
        async with asyncio.timeout(5):
            while not held_file.exists() or held_file.stat().st_size == 0:
                assert proc.returncode is None, "owned writer exited before readiness"
                await asyncio.sleep(0.02)
    except BaseException:
        await server.close()
        raise
    return server


@pytest.mark.windows_only
@pytest.mark.asyncio
async def test_stop_reaps_owned_codex_server_and_preserves_other_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stop releases one actual Windows writer while its neighbor remains alive."""
    target = await _spawn_owned_server(tmp_path / "target")
    neighbor: CodexNativeAppServer | None = None
    assert target.proc is not None
    target_proc = target.proc
    try:
        neighbor = await _spawn_owned_server(tmp_path / "neighbor")
        assert neighbor.proc is not None
        neighbor_proc = neighbor.proc
        servers = {"conv_target": target, "conv_neighbor": neighbor}
        monkeypatch.setattr(orchestration, "_AUTO_CODEX_APP_SERVERS", servers)
        monkeypatch.setattr(orchestration, "_AUTO_FORWARDER_TASKS", {})
        terminals = SimpleNamespace(
            list_for_conversation=lambda conv: [
                SimpleNamespace(terminal_name="codex", session_key="main")
            ]
        )
        resources = SimpleNamespace(
            terminal_registry=terminals,
            close_terminal=AsyncMock(return_value=True),
        )
        runner, _captured = _make_runner(resource_registry=resources)

        response = await asyncio.wait_for(runner.stop("codex-native", "conv_target"), 10)

        assert response is not None and response.status_code == 204
        assert target_proc.returncode is not None
        assert neighbor_proc.returncode is None
        assert "conv_target" not in servers
        assert servers["conv_neighbor"] is neighbor
        resources.close_terminal.assert_awaited_once_with("conv_target", "terminal_codex_main")
        # Windows refuses unlink while the writer still owns this open handle.
        (target.codex_home / "writer.lock").unlink()
        assert (neighbor.codex_home / "writer.lock").exists()
    finally:
        # These handles were created here; never enumerate or reap host processes.
        await target.close()
        if neighbor is not None:
            await neighbor.close()
