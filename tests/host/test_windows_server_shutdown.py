"""Native Windows server shutdown reaches the ASGI lifespan cleanup."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from omnigent.inner.windows_process_shutdown import stop_processes


@pytest.mark.windows_only
def test_headless_server_stop_drains_lifespan(tmp_path: Path) -> None:
    script = tmp_path / "server.py"
    ready, cleaned = tmp_path / "ready", tmp_path / "cleaned"
    script.write_text(
        "import asyncio, contextlib, sys\n"
        "from pathlib import Path\n"
        "import uvicorn\n"
        "from fastapi import FastAPI\n"
        "from omnigent.inner.windows_shutdown_cli import run_server\n"
        "ready, cleaned = map(Path, sys.argv[1:])\n"
        "@contextlib.asynccontextmanager\n"
        "async def lifespan(app):\n"
        "    try:\n"
        "        yield\n"
        "    finally:\n"
        "        await asyncio.sleep(0.05)\n"
        "        cleaned.write_text('lifespan finished')\n"
        "class Server(uvicorn.Server):\n"
        "    async def startup(self, sockets=None):\n"
        "        await super().startup(sockets)\n"
        "        ready.write_text('listening')\n"
        "config = uvicorn.Config(FastAPI(lifespan=lifespan), host='127.0.0.1', "
        "port=0, log_level='error')\n"
        "run_server(Server(config))\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    process = subprocess.Popen(
        [sys.executable, str(script), str(ready), str(cleaned)],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        deadline = time.monotonic() + 15
        while not ready.exists() and time.monotonic() < deadline:
            assert process.poll() is None, "owned server exited before startup"
            time.sleep(0.02)
        assert ready.exists(), "owned server did not become ready"
        assert stop_processes([process], grace_seconds=5)
        assert process.wait(timeout=3) == 0
        assert cleaned.read_text() == "lifespan finished"
    finally:
        stop_processes([process], grace_seconds=0, kill_seconds=3)
        process.wait(timeout=3)
