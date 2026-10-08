"""Terminal control commands must select the native host's multiplexer."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import click
import pytest

from omnigent.harnesses.claude_native import bridge, main
from omnigent.native import native_cost_popup
from omnigent.native.mux import terminal_mux_command, terminal_mux_exit_status
from omnigent.terminals import ws_common


@pytest.mark.parametrize("windows,binary", [(True, "psmux"), (False, "tmux")])
def test_claude_bridge_routes_control_capture_and_liveness(
    monkeypatch: pytest.MonkeyPatch, windows: bool, binary: str
) -> None:
    run = Mock(
        side_effect=[
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "ready", ""),
            subprocess.CompletedProcess([], 0, "0", ""),
        ]
    )
    monkeypatch.setattr(bridge, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        bridge,
        "subprocess",
        SimpleNamespace(
            run=run,
            TimeoutExpired=subprocess.TimeoutExpired,
            SubprocessError=subprocess.SubprocessError,
        ),
    )
    bridge._run_tmux("private socket", "send-keys", "-t", "main", "Enter")
    assert bridge._capture_pane("private socket", "main") == "ready"
    assert bridge._claude_pane_state("private socket", "main").alive is True
    assert [call.args[0][:3] for call in run.call_args_list] == [
        [binary, "-S", "private socket"]
    ] * 3


@pytest.mark.parametrize("windows,binary", [(True, "psmux"), (False, "tmux")])
async def test_websocket_liveness_selects_host_mux(
    monkeypatch: pytest.MonkeyPatch, windows: bool, binary: str
) -> None:
    process = SimpleNamespace(returncode=0, communicate=AsyncMock(return_value=(b"0", b"")))
    spawn = AsyncMock(return_value=process)
    monkeypatch.setattr(ws_common, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        ws_common,
        "asyncio",
        SimpleNamespace(
            create_subprocess_exec=spawn, wait_for=asyncio.wait_for, subprocess=asyncio.subprocess
        ),
    )
    assert await ws_common._tmux_session_alive("private socket", "main") is True
    assert await ws_common._check_pane_dead_definitive("private socket", "main") is False
    assert [call.args[:3] for call in spawn.call_args_list] == [
        (binary, "-S", "private socket")
    ] * 2


@pytest.mark.parametrize("windows,binary", [(True, "psmux"), (False, "tmux")])
def test_popup_queries_and_launches_use_host_mux(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, windows: bool, binary: str
) -> None:
    run = Mock(
        side_effect=[
            subprocess.CompletedProcess([], 0, "client", ""),
            subprocess.CompletedProcess([], 0, "123", ""),
            subprocess.CompletedProcess([], 0, "0 124", ""),
        ]
    )
    popen = Mock()
    monkeypatch.setattr(native_cost_popup, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        native_cost_popup,
        "subprocess",
        SimpleNamespace(
            run=run,
            Popen=popen,
            DEVNULL=subprocess.DEVNULL,
            SubprocessError=subprocess.SubprocessError,
        ),
    )
    assert native_cost_popup._list_tmux_clients("sock", "main") == ["client"]
    assert native_cost_popup._tmux_window_activity_at("sock", "main") == 123
    assert native_cost_popup._tmux_last_client_input_at("sock", "main") == 124
    assert all(call.args[0][:3] == [binary, "-S", "sock"] for call in run.call_args_list)
    monkeypatch.setattr(native_cost_popup, "_list_tmux_clients", lambda *args: ["client"])
    native_cost_popup.launch_cost_popup(
        "sock",
        "main",
        tmp_path / "config.json",
        session_id="session",
        elicitation_id="approval",
        message="budget",
    )
    native_cost_popup.launch_blocked_notice("sock", "main", message="budget")
    assert all(
        call.args[0][:4] == [binary, "-S", "sock", "display-popup"]
        for call in popen.call_args_list
    )
    assert popen.call_count == 2


@pytest.mark.parametrize("windows,binary", [(True, "psmux"), (False, "tmux")])
def test_claude_preflight_requires_the_selected_mux(
    monkeypatch: pytest.MonkeyPatch, windows: bool, binary: str
) -> None:
    monkeypatch.setattr(main, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        main,
        "shutil",
        SimpleNamespace(which=lambda name: name if name in {"claude", binary} else None),
    )
    main._preflight_local_tools("claude")
    monkeypatch.setattr(
        main, "shutil", SimpleNamespace(which=lambda name: "claude" if name == "claude" else None)
    )
    with pytest.raises(click.ClickException, match=f"{binary} was not found"):
        main._preflight_local_tools("claude")


@pytest.mark.parametrize("windows,binary", [(True, "psmux"), (False, "tmux")])
def test_claude_direct_attach_selects_available_host_mux(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, windows: bool, binary: str
) -> None:
    socket = tmp_path / "sock"
    socket.touch()
    prepared = main.PreparedClaudeTerminal(
        session_id="s",
        terminal_id="t",
        bridge_dir=tmp_path,
        reattached=False,
        tmux_socket=socket,
        tmux_target="main",
    )
    monkeypatch.setattr(main, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        main, "shutil", SimpleNamespace(which=lambda name: name if name == binary else None)
    )
    assert main._can_attach_direct_tmux(prepared) is True
    monkeypatch.setattr(main, "shutil", SimpleNamespace(which=lambda name: None))
    assert main._can_attach_direct_tmux(prepared) is False
    assert terminal_mux_command(str(socket), windows=windows) == [binary, "-S", str(socket)]


@pytest.mark.parametrize("windows", [True, False])
@pytest.mark.parametrize("status", [None, "0", "37"])
def test_exit_status_is_unknown_when_the_mux_uses_placeholders(
    windows: bool, status: str | None
) -> None:
    assert terminal_mux_exit_status(status, windows=windows) == (None if windows else status)


@pytest.mark.parametrize("windows", [True, False])
def test_claude_dead_pane_status_requires_mux_support(
    monkeypatch: pytest.MonkeyPatch, windows: bool
) -> None:
    monkeypatch.setattr(bridge, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        bridge,
        "subprocess",
        SimpleNamespace(run=Mock(return_value=subprocess.CompletedProcess([], 0, "1 0", ""))),
    )
    state = bridge._claude_pane_state("sock", "main")
    assert state.alive is False
    assert state.exited is True
    assert state.exit_status == (None if windows else "0")
