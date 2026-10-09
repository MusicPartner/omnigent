"""Explicitly gated real-Claude argv and hook capture for native Windows.

Set ``OMNIGENT_REAL_CLAUDE_EXE`` to an installed native ``claude.exe`` and
install psmux to run the integration capture. It uses no provider response.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from omnigent.harnesses.claude_native.bridge import (
    augment_claude_args,
    bridge_dir_for_bridge_id,
)
from omnigent.terminals.psmux import PsmuxTerminalInstance
from tests.terminals.windows_command_line import command_line_to_argv


def _owned_claude_processes(
    *, marker: str | None = None, pid: int | None = None
) -> list[dict[str, object]]:
    if (marker is None) == (pid is None):
        raise ValueError("provide exactly one process marker or pid")
    predicate = (
        f"$_.CommandLine -like '*{marker}*'" if marker is not None else f"$_.ProcessId -eq {pid}"
    )
    query = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        "@(Get-CimInstance Win32_Process -Filter \"Name = 'claude.exe'\" "
        f"| Where-Object {{ {predicate} }} "
        "| Select-Object ProcessId,ExecutablePath,CommandLine) "
        "| ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", query],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    value = json.loads(result.stdout.lstrip("\ufeff") or "[]")
    return [value] if isinstance(value, dict) else value


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform != "win32", reason="requires native Windows")
async def test_real_claude_native_argv_and_setup_hook_capture(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """Capture production settings and literal hook argv without provider calls."""
    claude_value = os.environ.get("OMNIGENT_REAL_CLAUDE_EXE")
    if not claude_value:
        pytest.skip("set OMNIGENT_REAL_CLAUDE_EXE to opt into the real Claude capture")
    claude = Path(claude_value).resolve()
    if not claude.is_file() or claude.name.lower() != "claude.exe":
        pytest.fail(f"OMNIGENT_REAL_CLAUDE_EXE must name a native claude.exe: {claude}")
    if not shutil.which("psmux"):
        pytest.fail("psmux is required when the real Claude capture is enabled")

    started_version = subprocess.run(
        [str(claude), "--version"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    ).stdout.strip()
    marker = str(uuid.uuid4())
    root = tmp_path / f"omnigent-capture-{marker}"
    root.mkdir()
    workspace = root / "workspace space Å"
    workspace.mkdir()
    config_dir = root / "isolated-claude-config"
    config_dir.mkdir()
    bridge_dir = bridge_dir_for_bridge_id(f"real-capture-{marker}") / "bridge space Å ; % literal"
    request.addfinalizer(lambda: shutil.rmtree(bridge_dir, ignore_errors=True))
    private_dir = root / "owned-pane"
    private_dir.mkdir()
    record_path = root / "hook-record.json"
    recorder_path = root / "setup-recorder.py"
    recorder_path.write_text(
        "import json, os, pathlib, sys, time\n"
        "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
        "'argv': sys.argv[2:], 'cwd': os.getcwd(), "
        "'unset': os.getenv('OMNIGENT_CAPTURE_UNSET')}), encoding='utf-8')\n"
        "time.sleep(2)\n",
        encoding="utf-8",
    )
    expected_hook_args = [
        'quote "inside"',
        "%PATH%",
        "semi;colon",
        "space and Å",
        '2>> "log file"',
    ]

    # This is the same argument/settings path used by the production bridge.
    args = augment_claude_args(
        ("--init-only", "--session-id", marker, "--setting-sources", ""),
        bridge_dir=bridge_dir,
        python_executable=sys.executable,
    )
    settings_index = args.index("--settings") + 1
    settings_path = Path(args[settings_index])
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    production_hook = settings["hooks"]["SessionStart"][0]["hooks"][0]
    assert production_hook["type"] == "command"
    assert production_hook["command"] == sys.executable
    assert production_hook["args"] == [
        "-X",
        "utf8",
        "-I",
        "-m",
        "omnigent.harnesses.claude_native.windows_hooks",
        "--stderr",
        str(bridge_dir / "observer_hook.stderr"),
        "--",
        "omnigent.harnesses.claude_native.hook",
        "--bridge-dir",
        str(bridge_dir),
    ]
    settings.setdefault("hooks", {})["Setup"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": sys.executable,
                    "args": [
                        "-I",
                        str(recorder_path),
                        str(record_path),
                        *expected_hook_args,
                    ],
                }
            ]
        }
    ]
    settings_payload = json.dumps(settings, ensure_ascii=False, separators=(",", ":"))
    settings_path.write_text(settings_payload, encoding="utf-8")
    mcp_payload = args[args.index("--mcp-config") + 1]
    expected_mcp = json.loads(mcp_payload)

    env = {
        "CLAUDE_CONFIG_DIR": str(config_dir),
        "ANTHROPIC_API_KEY": "omnigent-capture-test-only",
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:9",
        "DISABLE_AUTOUPDATER": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "OMNIGENT_CAPTURE_UNSET": "remove-me",
    }
    instance = PsmuxTerminalInstance(
        name="real-claude-capture",
        session_key=marker,
        socket_path=private_dir / "psmux.sock",
        private_dir=private_dir,
        command=str(claude),
        args=args,
        env=env,
        env_unset=[
            "OMNIGENT_CAPTURE_UNSET",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
        ],
        inherit_env=True,
        keep_alive_after_exit=True,
    )
    captured: dict[str, object] | None = None
    try:
        await instance.launch(cwd=workspace)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            for process in await asyncio.to_thread(_owned_claude_processes, marker=marker):
                command_line = str(process.get("CommandLine") or "")
                if marker in command_line:
                    captured = process
                    break
            if captured is not None and record_path.exists():
                break
            await asyncio.sleep(0.2)

        if captured is None:
            pane = await instance.read()
            raise AssertionError(
                "Claude Win32_Process.CommandLine was not captured; pane tail: "
                + str(pane.get("screen", ""))[-1600:]
            )
        argv = command_line_to_argv(str(captured["CommandLine"]))
        assert Path(str(argv[0])).resolve() == claude
        assert argv[argv.index("--session-id") + 1] == marker
        assert argv[argv.index("--mcp-config") + 1] == mcp_payload
        assert json.loads(argv[argv.index("--mcp-config") + 1]) == expected_mcp
        captured_settings_path = Path(argv[argv.index("--settings") + 1])
        assert captured_settings_path.resolve() == settings_path.resolve()
        assert captured_settings_path.read_text(encoding="utf-8") == settings_payload
        assert json.loads(settings_payload) == settings
        assert record_path.is_file(), "Claude did not invoke the Setup recorder hook"
        recorded = json.loads(record_path.read_text(encoding="utf-8"))
        assert recorded == {
            "argv": expected_hook_args,
            "cwd": str(workspace),
            "unset": None,
        }

        ended_version = subprocess.run(
            [str(claude), "--version"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        ).stdout.strip()
        print(
            json.dumps(
                {
                    "claude_version_started": started_version,
                    "claude_version_ended": ended_version,
                    "psmux_version": subprocess.check_output(
                        ["psmux", "--version"], text=True, timeout=10
                    ).strip(),
                    "captured_pid": captured.get("ProcessId"),
                    "settings_bytes": len(settings_payload.encode("utf-8")),
                    "hook_args_verified": len(expected_hook_args),
                },
                ensure_ascii=False,
            )
        )
        assert ended_version == started_version
    finally:
        try:
            await instance.close()
        finally:
            if captured and captured.get("ProcessId"):
                pid = int(captured["ProcessId"])
                alive = True
                for _ in range(25):
                    alive = any(
                        int(process.get("ProcessId") or 0) == pid
                        for process in await asyncio.to_thread(_owned_claude_processes, pid=pid)
                    )
                    if not alive:
                        break
                    await asyncio.sleep(0.2)
                if alive:
                    subprocess.run(
                        ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                        capture_output=True,
                        timeout=10,
                    )
                    alive = any(
                        int(process.get("ProcessId") or 0) == pid
                        for process in await asyncio.to_thread(_owned_claude_processes, pid=pid)
                    )
                assert not alive, f"owned Claude process {pid} remained after cleanup"
