"""Windows cold resume releases stale app-server rollout handles."""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from omnigent.harnesses.codex_native import main as codex_native
from omnigent.harnesses.codex_native import process_registry as registry

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows file sharing semantics")


@pytest.mark.asyncio
async def test_stale_app_server_cleanup_unlocks_authoritative_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reaping the same home releases a real append lock before atomic refresh."""
    thread_id = "019e96aa-0be2-7343-8d3b-6f914d60936b"
    state_dir = tmp_path / "session"
    codex_home = state_dir / "codex-home"
    target = (
        codex_home
        / "sessions"
        / "2026"
        / "01"
        / "01"
        / f"rollout-2026-01-01T00-00-00-{thread_id}.jsonl"
    )
    target.parent.mkdir(parents=True)
    target.write_text("divergent local-only history\n", encoding="utf-8")
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    executable = executable_dir / "codex.exe"
    shutil.copy2(sys._base_executable, executable)
    for dll in Path(sys.base_prefix).glob("*.dll"):
        shutil.copy2(dll, executable_dir / dll.name)
    environment = {**os.environ, "PYTHONHOME": sys.base_prefix}
    ready = tmp_path / "ready"
    (executable_dir / "app-server").write_text(
        "import pathlib, sys, time\n"
        "if len(sys.argv) > 1:\n"
        "    handle = open(sys.argv[1], 'a', encoding='utf-8')\n"
        "    pathlib.Path(sys.argv[2]).write_text('locked')\n"
        "time.sleep(300)\n",
        encoding="utf-8",
    )
    victim = subprocess.Popen(
        [str(executable), "app-server", str(target), str(ready)],
        cwd=executable_dir,
        env={**environment, "CODEX_HOME": str(codex_home)},
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    bystander = None
    try:
        bystander = subprocess.Popen(
            [str(executable), "app-server"],
            cwd=executable_dir,
            env={**environment, "CODEX_HOME": str(tmp_path / "other-session" / "codex-home")},
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + 10.0
        while not ready.exists() and victim.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), f"rollout holder failed to start: {victim.poll()}"
        temporary = target.with_suffix(".tmp")
        temporary.write_text("server history\n", encoding="utf-8")
        with pytest.raises(PermissionError) as denied:
            os.replace(temporary, target)
        assert denied.value.winerror == 5
        assert target.read_text(encoding="utf-8") == "divergent local-only history\n"
        temporary.unlink()

        assert registry.reap_codex_native_processes_for_state_dir(state_dir, grace_s=2.0) == 1
        victim.wait(timeout=5.0)
        assert bystander.poll() is None

        monkeypatch.setattr(codex_native, "_replay_dead_letters_before_resume", AsyncMock())

        def history(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/sessions/conv_codex/items"
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "msg_server",
                            "type": "message",
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": "authoritative server history"}
                            ],
                        }
                    ],
                    "has_more": False,
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(history), base_url="http://test"
        ) as client:
            result = await codex_native._ensure_local_codex_resume_rollout(
                client,
                session_id="conv_codex",
                external_session_id=thread_id,
                codex_home=codex_home,
                workspace=tmp_path,
                model_provider="omnigent_databricks",
                codex_path=None,
            )
        assert result == target
        records = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
        assert "authoritative server history" in json.dumps(records)
        assert "divergent local-only history" not in json.dumps(records)
        assert not list(target.parent.glob("*.tmp"))
    finally:
        for process in (victim, bystander):
            if process is None:
                continue
            with contextlib.suppress(OSError):
                process.kill()
            process.wait(timeout=5.0)
