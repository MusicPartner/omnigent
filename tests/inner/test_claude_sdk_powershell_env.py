"""Windows shell discovery reaches Claude SDK options without copying secrets."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from omnigent.inner import claude_sdk_executor, windows_powershell
from omnigent.inner.claude_sdk_executor import ClaudeSDKExecutor


@pytest.mark.parametrize("store_first", [False, True])
async def test_sdk_prefers_native_powershell_in_partial_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, store_first: bool
) -> None:
    native = tmp_path / "Program Files" / "PowerShell" / "7"
    native.mkdir(parents=True)
    (native / "pwsh.exe").touch()
    original_path = str(tmp_path / "existing-tools")
    if store_first:
        store = tmp_path / "WindowsApps"
        store.mkdir()
        (store / "pwsh.exe").touch()
        original_path = f"{store};{original_path}"
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.setenv("PATH", original_path)
    monkeypatch.setenv("OMNIGENT_TEST_AMBIENT_SECRET", "parent-only")
    sdk = ModuleType("claude_agent_sdk")
    sdk_types = ModuleType("claude_agent_sdk.types")
    sdk.ClaudeAgentOptions = SimpleNamespace
    sdk_types.StreamEvent = object
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", sdk)
    monkeypatch.setitem(sys.modules, "claude_agent_sdk.types", sdk_types)
    monkeypatch.setattr(claude_sdk_executor, "_ensure_sdk", lambda: sdk)
    executor = ClaudeSDKExecutor(model="claude-haiku-4-5")
    captured: dict[str, str] = {}

    async def capture_client(sdk, *, session_key, options, model):
        captured.update(options.env)
        raise RuntimeError("test stops before launching Claude")

    monkeypatch.setattr(executor, "_get_or_create_client", capture_client)
    try:
        _ = [
            event async for event in executor.run_turn([{"role": "user", "content": "hi"}], [], "")
        ]
    except RuntimeError as exc:
        assert str(exc) == "test stops before launching Claude"

    assert captured["PATH"] == f"{native.resolve()};{original_path}"
    assert "OMNIGENT_TEST_AMBIENT_SECRET" not in captured
    assert "ProgramFiles" not in captured
    assert os.environ["PATH"] == original_path
    await executor.close()
