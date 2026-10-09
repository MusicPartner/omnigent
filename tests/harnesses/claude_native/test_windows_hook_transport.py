"""Literal Windows Claude hook transport and shell consumer regression checks."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from omnigent.harnesses.claude_native import bridge, windows_hooks
from omnigent.native import native_cost_popup
from omnigent.native.shell import shell_join


def test_posix_shell_roundtrip_preserves_shell_metacharacters() -> None:
    import shlex

    parts = [r"C:\space path\python.exe", 'quote"', "$(bad)", "%PATH%", "\u00c5", ""]
    assert shlex.split(shell_join(parts, consumer="posix")) == parts
    with pytest.raises(ValueError, match="Unknown shell"):
        shell_join(parts, consumer="cmd")


def test_missing_pwsh_keeps_popup_approval_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(native_cost_popup, "IS_WINDOWS", True)
    monkeypatch.setattr(native_cost_popup.shutil, "which", lambda _: None)
    monkeypatch.setattr(native_cost_popup, "_list_tmux_clients", lambda *_: ["client"])
    monkeypatch.setattr(
        native_cost_popup.subprocess, "Popen", lambda *_a, **_k: pytest.fail("spawned")
    )
    native_cost_popup.launch_cost_popup(
        "socket",
        "pane",
        tmp_path / "config.json",
        session_id="session",
        elicitation_id="elicitation",
        message="approve?",
    )
    native_cost_popup.launch_blocked_notice("socket", "pane", message="denied")


@pytest.mark.skipif(os.name != "nt", reason="actual Windows PowerShell native argv")
def test_popup_pwsh_roundtrip_literal_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("psmux popup capability pwsh unavailable")
    monkeypatch.setattr(native_cost_popup, "IS_WINDOWS", True)
    message = 'literal "quotes" ; $env:PATH $(exit 41) %PATH% \u00c5 apostrophe\' end'
    command = native_cost_popup._popup_command(
        [
            sys.executable,
            "-I",
            "-m",
            "omnigent.native.native_cost_popup",
            "--notice",
            "--message",
            message,
        ]
    )
    result = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        input="\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert message in result.stdout


def test_status_chain_uses_claude_configured_git_bash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bash = tmp_path / "Git space" / "bash.exe"
    bash.parent.mkdir()
    bash.touch()
    monkeypatch.setenv("CLAUDE_CODE_GIT_BASH_PATH", str(bash))
    command = 'cat | tr a-z A-Z; printf "\u00c5"'
    assert windows_hooks.status_shell_command(command) == [str(bash), "-c", command]


@pytest.mark.skipif(os.name != "nt", reason="actual Claude Git Bash status consumer")
def test_status_line_git_bash_captures_context_and_chains_stdin(tmp_path: Path) -> None:
    try:
        bash = windows_hooks.status_shell_command("ignored")[0]
    except FileNotFoundError:
        pytest.skip("Claude Git Bash capability unavailable")
    directory = tmp_path / "bridge space \u00c5"
    directory.mkdir()
    raw = json.dumps(
        {
            "context_window": {"context_window_size": 200000},
            "marker": '\u00c5 \u65e5 "literal" ; %PATH%',
        },
        ensure_ascii=False,
    )
    command = windows_hooks.status_line_command(sys.executable, directory, "cat")
    result = subprocess.run(
        [bash, "-c", command],
        input=raw,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == raw
    assert json.loads((directory / "context.json").read_text(encoding="utf-8")) == {
        "context_window_size": 200000,
    }


def test_windows_generated_hooks_keep_literal_args_and_canonical_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bridge, "IS_WINDOWS", True)
    monkeypatch.setattr(bridge, "_BRIDGE_ROOT", tmp_path)
    monkeypatch.setattr(bridge, "_TRUSTED_PARENT", tmp_path)
    directory = tmp_path / "space ; %PATH% \u00c5"
    directory.mkdir()
    python = r"C:\Program Files\Python\python.exe"
    settings = bridge.build_hook_settings(
        directory,
        python_executable=python,
        ap_server_url="http://127.0.0.1:1",
        subagent_router_dir=directory,
        turn_routing=True,
    )
    hooks = [
        hook
        for entries in settings["hooks"].values()
        for entry in entries
        for hook in entry["hooks"]
    ]
    assert all(hook["command"] == python for hook in hooks)
    assert all(str(directory) in hook["args"] for hook in hooks)
    assert settings["hooks"]["PermissionRequest"][0]["hooks"][0]["timeout"] == 86400
    assert len(settings["hooks"]["UserPromptSubmit"]) == 3
    message = settings["hooks"]["MessageDisplay"][0]["hooks"][0]
    assert message["args"][:5] == [
        "-X",
        "utf8",
        "-I",
        "-m",
        "omnigent.harnesses.claude_native.message_display_hook",
    ]
    assert "args" not in settings["statusLine"]


def test_stderr_transport_appends_without_changing_stdio_or_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_file = tmp_path / "observer stderr.log"
    error_file.write_text("previous\n", encoding="utf-8")
    stdin = io.StringIO("literal stdin")
    stdout = io.StringIO()
    original_stderr = sys.stderr
    monkeypatch.setattr(sys, "argv", list(sys.argv))
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    literal = ['quote"', "%PATH%", ";", "\u00c5", ""]

    def run_module(module: str, **kwargs: object) -> None:
        assert module == "owned.module"
        assert sys.argv == ["owned.module", *literal]
        assert sys.stdin.read() == "literal stdin"
        print("visible stdout")
        print("new error", file=sys.stderr, flush=True)
        os.write(2, b"descriptor error\n")
        subprocess.run(
            [sys.executable, "-c", "import os; os.write(2, b'child error\\n')"], check=True
        )
        raise SystemExit(37)

    monkeypatch.setattr(windows_hooks.runpy, "run_module", run_module)
    with pytest.raises(SystemExit) as exc:
        windows_hooks.main(["--stderr", str(error_file), "--", "owned.module", *literal])
    assert exc.value.code == 37
    assert sys.stderr is original_stderr
    assert stdout.getvalue() == "visible stdout\n"
    assert (
        error_file.read_text(encoding="utf-8")
        == "previous\nnew error\ndescriptor error\nchild error\n"
    )


def test_direct_message_hook_keeps_utf8_stdin(tmp_path: Path) -> None:
    parts = [
        sys.executable,
        "-I",
        "-m",
        "omnigent.harnesses.claude_native.message_display_hook",
        "--bridge-dir",
        str(tmp_path),
    ]
    settings = windows_hooks.command_hook(parts)
    delta = 'literal \u00c5 \u65e5 "quoted" ; %PATH%'
    payload = json.dumps({"message_id": "message", "delta": delta}, ensure_ascii=False)
    result = subprocess.run(
        [settings["command"], *settings["args"]],
        input=payload.encode("utf-8"),
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads((tmp_path / "message_deltas.jsonl").read_text(encoding="utf-8"))
    assert record["delta"] == delta


def test_shared_tool_observer_keeps_owned_argv_and_timeout(tmp_path: Path) -> None:
    from omnigent.native.tool_observer_hook import hook_settings

    calls = []

    def format_command(parts: list[str]) -> dict[str, object]:
        calls.append(parts)
        return {"type": "command", "command": parts[0], "args": parts[1:]}

    result = hook_settings(
        tmp_path, "python.exe", "owned.module", command_formatter=format_command
    )
    assert calls == [
        ["python.exe", "-I", "-m", "owned.module", "observe-tool", "--bridge-dir", str(tmp_path)]
    ]
    assert result["args"] == calls[0][1:]
    assert result["timeout"] == 3
