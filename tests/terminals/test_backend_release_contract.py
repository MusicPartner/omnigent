"""Release terminal API contracts shared by the tmux and psmux backends."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from omnigent.inner.datamodel import OSEnvSpec, TerminalEnvSpec
from omnigent.inner.terminal import TerminalCreateResult, TerminalInstance
from omnigent.inner.terminal_lifecycle import (
    TERMINAL_INSTANCE_ID_ENV,
    TERMINAL_LAUNCH_ID_ENV,
    TERMINAL_LAUNCH_SESSION_ID_ENV,
)
from omnigent.terminals import backend, psmux
from omnigent.terminals.registry import TerminalExitedDuringLaunch, TerminalRegistry


@pytest.mark.parametrize("with_parent", [False, True])
def test_tmux_backend_delegates_exact_release_arguments(tmp_path, monkeypatch, with_parent):
    instance = TerminalInstance("shell", "s1", tmp_path / "sock", tmp_path)
    factory = Mock(return_value=TerminalCreateResult(instance, tmp_path))
    monkeypatch.setattr(backend, "create_terminal_instance", factory)
    parent_spec = OSEnvSpec(type="caller_process", cwd=str(tmp_path))
    spec = TerminalEnvSpec(command="bash")
    parent = object() if with_parent else None
    result = backend.TmuxTerminalMuxBackend().create(
        "shell",
        "s1",
        spec,
        parent_os_env=parent_spec,
        parent_environment=parent,
        cwd_override="child",
        sandbox_override="none",
        conversation_link="/c/conv",
    )
    expected = {
        "parent_os_env_spec": parent_spec,
        "cwd_override": "child",
        "sandbox_override": "none",
        "conversation_link": "/c/conv",
    }
    if with_parent:
        expected["parent_environment"] = parent
    factory.assert_called_once_with("shell", "s1", spec, **expected)
    assert result == (instance, tmp_path)


@pytest.mark.parametrize("diagnostics_fail", [False, True])
async def test_psmux_launch_replaces_parent_lifecycle_identity(
    tmp_path, monkeypatch, diagnostics_fail
):
    keys = (TERMINAL_INSTANCE_ID_ENV, TERMINAL_LAUNCH_ID_ENV, TERMINAL_LAUNCH_SESSION_ID_ENV)
    for key in keys:
        monkeypatch.setenv(key, "parent-id")
    instance = psmux.PsmuxTerminalInstance(
        "shell",
        "s1",
        tmp_path / "sock",
        tmp_path,
        command="cmd.exe",
        env=dict.fromkeys(keys, "override-id"),
    )
    instance.lifecycle_trace.transfer_session("conv_contract")
    if diagnostics_fail:
        monkeypatch.setattr(
            instance.lifecycle_trace, "launch_environment", Mock(side_effect=RuntimeError)
        )
    process = SimpleNamespace(returncode=0, communicate=AsyncMock(return_value=(b"", b"")))
    spawn = AsyncMock(return_value=process)
    monkeypatch.setattr(psmux.asyncio, "create_subprocess_exec", spawn)
    await instance.launch(cwd=tmp_path)
    env = spawn.call_args.kwargs["env"]
    if diagnostics_fail:
        assert all(key not in env for key in keys)
    else:
        assert env[TERMINAL_INSTANCE_ID_ENV] == instance.diagnostic_id
        assert env[TERMINAL_LAUNCH_ID_ENV] == instance.lifecycle_trace.launch_id
        assert env[TERMINAL_LAUNCH_SESSION_ID_ENV] == "conv_contract"
    assert instance.running


async def test_psmux_read_forwards_join_wrapped(tmp_path, monkeypatch):
    instance = psmux.PsmuxTerminalInstance(
        "shell", "s1", tmp_path / "sock", tmp_path, running=True
    )
    output = AsyncMock(side_effect=["joined", "styled joined", "1,2"])
    monkeypatch.setattr(instance, "_tmux_output", output)
    result = await instance.read(10, join_wrapped=True)
    assert result["screen"] == "styled joined"
    for call in output.call_args_list[:2]:
        assert "-J" in call.args
        assert "-10" in call.args


async def test_registry_preserves_release_early_exit_lifecycle(tmp_path):
    instance = TerminalInstance("shell", "s1", tmp_path / "sock", tmp_path)
    instance.launch = AsyncMock()
    instance.is_alive = AsyncMock(return_value=False)
    instance.close = AsyncMock()
    trace_exit = Mock(wraps=instance.lifecycle_trace.note_exit)
    instance.lifecycle_trace.note_exit = trace_exit
    seam = SimpleNamespace(create=Mock(return_value=(instance, tmp_path)))
    registry = TerminalRegistry(backend=seam)
    with pytest.raises(TerminalExitedDuringLaunch) as exc:
        await registry.launch("conv_contract", "shell", "s1", TerminalEnvSpec(command="cmd.exe"))
    assert exc.value.instance is instance
    assert instance.lifecycle_trace.session_id == "conv_contract"
    trace_exit.assert_called_once()
    instance.close.assert_awaited_once()
    assert registry.get("conv_contract", "shell", "s1") is None


def test_psmux_backend_forwards_shared_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(psmux.PsmuxTerminalMuxBackend, "validate_available", lambda self: None)
    shared = object()
    parent = SimpleNamespace(sandbox=None, cwd=tmp_path, copy_on_write_environment=shared)
    owned = SimpleNamespace(close=Mock())
    factory = Mock(return_value=owned)
    monkeypatch.setattr(psmux, "create_os_environment", factory)
    instance, cwd = psmux.PsmuxTerminalMuxBackend().create(
        "shell",
        "s1",
        TerminalEnvSpec(command="cmd.exe"),
        parent_os_env=OSEnvSpec(type="caller_process", cwd=str(tmp_path)),
        parent_environment=parent,
    )
    try:
        assert cwd == tmp_path.resolve()
        assert instance.os_env is owned
        assert factory.call_args.kwargs == {
            "sandbox_policy": None,
            "copy_on_write_environment": shared,
        }
        assert owned is not parent
    finally:
        import shutil

        shutil.rmtree(instance.private_dir)
