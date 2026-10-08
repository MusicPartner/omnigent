"""Keep native launch and CLI Windows gates consistent with psmux support."""

from unittest.mock import AsyncMock, Mock

import click
import pytest

from omnigent import cli_common
from omnigent.inner import terminal
from omnigent.inner.datamodel import OSEnvSpec, TerminalEnvSpec
from omnigent.runner.native import orchestration
from omnigent.terminals import backend, psmux
from omnigent.terminals.registry import TerminalRegistry


@pytest.mark.parametrize("supported", [False, True])
def test_windows_refusal_depends_on_psmux(supported, monkeypatch):
    monkeypatch.setattr(orchestration, "IS_WINDOWS", True)
    monkeypatch.setattr(orchestration, "native_terminal_supported", lambda: supported)
    payload = orchestration._native_terminal_start_error_payload(
        RuntimeError("private-detail"), "Claude", session_id="conv_gates"
    )
    assert payload["code"] == "native_terminal_start_failed"
    assert "private-detail" not in payload["message"]
    if supported:
        assert "not supported on Windows" not in payload["message"]
        assert "failed to start (RuntimeError)" in payload["message"]
    else:
        assert (
            "Native Claude terminal (tmux/PTY) is not supported on Windows." in payload["message"]
        )
        assert "Use an SDK-based harness" in payload["message"]


@pytest.mark.parametrize("harness", ["claude", "codex", "cursor"])
@pytest.mark.parametrize("supported", [False, True])
def test_cli_guard_depends_on_psmux(harness, supported, monkeypatch):
    monkeypatch.setattr(cli_common, "IS_WINDOWS", True)
    monkeypatch.setattr(cli_common, "native_terminal_supported", lambda: supported)
    if supported:
        cli_common.reject_native_on_windows(harness)
    else:
        with pytest.raises(click.ClickException, match="not supported on Windows"):
            cli_common.reject_native_on_windows(harness)


async def test_windows_registry_uses_psmux_without_entering_tmux_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "IS_WINDOWS", True)
    monkeypatch.setattr(psmux, "IS_WINDOWS", True)
    monkeypatch.setattr(psmux.PsmuxTerminalMuxBackend, "validate_available", lambda _: None)
    forbidden = Mock(side_effect=AssertionError("Windows must not enter the tmux factory"))
    monkeypatch.setattr(backend, "create_terminal_instance", forbidden)
    monkeypatch.setattr(psmux.PsmuxTerminalInstance, "launch", AsyncMock())
    monkeypatch.setattr(psmux.PsmuxTerminalInstance, "is_alive", AsyncMock(return_value=True))
    registry = TerminalRegistry()
    instance = await registry.launch(
        "conv_gates",
        "shell",
        "s1",
        TerminalEnvSpec(
            command="cmd.exe", os_env=OSEnvSpec(type="caller_process", cwd=str(tmp_path))
        ),
    )
    try:
        assert isinstance(instance, psmux.PsmuxTerminalInstance)
        assert instance.lifecycle_trace.session_id == "conv_gates"
        forbidden.assert_not_called()
    finally:
        await registry.shutdown()


def test_explicit_tmux_factory_keeps_release_windows_refusal(monkeypatch):
    monkeypatch.setattr(terminal, "IS_WINDOWS", True)
    with pytest.raises(RuntimeError, match="not supported on Windows"):
        terminal.create_terminal_instance("shell", "s1", TerminalEnvSpec(command="cmd.exe"))
