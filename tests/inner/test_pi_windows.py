"""Windows Pi npm shims preserve composed instructions without batch parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from omnigent.inner import pi_executor


def _npm_pi(tmp_path: Path, package_name: str) -> tuple[Path, Path, Path]:
    shim = tmp_path / "npm" / "pi.cmd"
    package_root = shim.parent / "node_modules" / package_name
    script = package_root / "dist" / "cli.js"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    (package_root / "package.json").write_text(
        json.dumps({"bin": {"pi": "dist/cli.js"}}), encoding="utf-8"
    )
    shim.write_text(
        f'@echo off\nnode "%dp0%/node_modules/{package_name}/dist/cli.js" %*\n',
        encoding="utf-8",
    )
    node = shim.parent / "node.exe"
    node.touch()
    return shim, node, script


@pytest.mark.parametrize(
    "package_name", ["@earendil-works/pi-coding-agent", "@mariozechner/pi-coding-agent"]
)
def test_npm_pi_uses_node_and_the_shim_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, package_name: str
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", True)
    shim, node, script = _npm_pi(tmp_path, package_name)

    assert pi_executor._pi_spawn_argv(str(shim), {}) == [str(node), str(script.resolve())]


def test_npm_pi_uses_only_the_worker_path_for_node(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", True)
    shim, node, script = _npm_pi(tmp_path, "@earendil-works/pi-coding-agent")
    node.unlink()
    lookup = Mock(return_value=str(node))
    monkeypatch.setattr(pi_executor.shutil, "which", lookup)

    assert pi_executor._pi_spawn_argv(str(shim), {"PATH": "worker-path"}) == [
        str(node),
        str(script.resolve()),
    ]
    lookup.assert_called_once_with("node.exe", path="worker-path")


@pytest.mark.parametrize("windows", [True, False])
def test_unknown_custom_launcher_keeps_its_original_argv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, windows: bool
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", windows)
    shim = tmp_path / "custom.cmd"
    shim.write_text("@echo off\ncustom %*", encoding="utf-8")

    assert pi_executor._pi_spawn_argv(str(shim), {}) == [str(shim)]


def test_non_windows_pi_shim_keeps_its_original_argv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", False)
    shim, _, _ = _npm_pi(tmp_path, "@earendil-works/pi-coding-agent")

    assert pi_executor._pi_spawn_argv(str(shim), {}) == [str(shim)]


def test_npm_pi_rejects_an_entry_outside_its_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", True)
    shim, _, script = _npm_pi(tmp_path, "@earendil-works/pi-coding-agent")
    escaped = script.parents[2] / "outside.js"
    escaped.touch()
    (script.parents[1] / "package.json").write_text(
        json.dumps({"bin": {"pi": "../outside.js"}}), encoding="utf-8"
    )

    assert pi_executor._pi_spawn_argv(str(shim), {}) == [str(shim)]


@pytest.mark.parametrize("mode", ["append", "replace"])
async def test_rpc_preserves_multiline_and_shell_metacharacters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    monkeypatch.setattr(pi_executor, "IS_WINDOWS", True)
    shim, node, script = _npm_pi(tmp_path, "@earendil-works/pi-coding-agent")
    process = Mock(returncode=0, stdin=None, wait=AsyncMock(return_value=0))
    spawn = AsyncMock(return_value=process)
    monkeypatch.setattr(pi_executor, "_create_subprocess_exec", spawn)
    monkeypatch.setattr(pi_executor._PiRpcSession, "_reader", AsyncMock())
    monkeypatch.setattr(pi_executor._PiRpcSession, "_stderr_reader", AsyncMock())
    prompt = 'Inline "quoted" & %PATH% | ^ < >\nRequest\r\nFramework \u2603'
    env = {"PATH": "worker-path"}
    session = pi_executor._PiRpcSession()
    try:
        await session.start(str(shim), env=env, system_prompt=prompt, system_prompt_mode=mode)
        args = spawn.await_args.args
        assert args[:2] == (str(node), str(script.resolve()))
        flag = "--append-system-prompt" if mode == "append" else "--system-prompt"
        assert args[args.index(flag) + 1] == prompt
        assert spawn.await_args.kwargs["env"] is env
        if mode == "replace":
            assert args[args.index("--append-system-prompt") + 1] == ""
    finally:
        await session.close()
