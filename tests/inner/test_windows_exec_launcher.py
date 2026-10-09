"""Native Windows transport proof and the isolated prototype's adoption blocker."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest

from omnigent.inner.sandbox import SandboxPolicy, _launcher_inline_source, get_backend
from tests.inner.windows_exec_launcher_prototype import create_console_launcher

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows executable")


def _policy(active: bool = False) -> SandboxPolicy:
    return SandboxPolicy(
        backend_type="windows_jobobject" if active else "none",
        active=active,
        read_roots=None,
        write_roots=[],
        write_files=[],
        allow_network=True,
    )


def test_console_launcher_literal_argv_stdio_exit_and_spaced_paths(tmp_path, monkeypatch):
    interpreter_dir = tmp_path / "Python space Å"
    interpreter_dir.mkdir()
    interpreter = interpreter_dir / "python.exe"
    shutil.copy2(sys.executable, interpreter)
    shutil.copy2(Path(sys.executable).parent.parent / "pyvenv.cfg", interpreter_dir / "pyvenv.cfg")
    site_packages = interpreter_dir / "Lib" / "site-packages"
    site_packages.mkdir(parents=True)
    original_site = Path(sys.executable).parent.parent / "Lib" / "site-packages"
    monkeypatch.setattr(sys, "executable", str(interpreter))
    cwd = tmp_path / "cwd space Å"
    cwd.mkdir()
    args = [
        "",
        "space value",
        'quote"value',
        "%PATH%",
        "a&b|c>d<e^f",
        "semi;colon",
        "Å漢字",
        "end\\",
        '\\"',
    ]
    code = (
        "import json,os,sys; "
        "print(json.dumps({'argv':sys.argv[1:],'cwd':os.getcwd(),'input':sys.stdin.read()})); "
        "print('target stderr',file=sys.stderr); sys.exit(37)"
    )
    source = f"import sys; sys.path.insert(0, {str(original_site)!r}); " + _launcher_inline_source(
        str(interpreter), _policy(), cwd=str(cwd)
    )
    launcher = create_console_launcher(source, str(interpreter))
    try:
        assert Path(launcher).suffix == ".exe"
        assert Path(launcher).read_bytes().startswith(b"MZ")
        result = subprocess.run(
            [launcher, "-c", code, *args],
            input="stdin literal %PATH% Å",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            cwd=cwd,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        assert result.returncode == 37, result.stderr
        observed = json.loads(result.stdout)
        assert observed == {"argv": args, "cwd": str(cwd), "input": "stdin literal %PATH% Å"}
        assert "target stderr" in result.stderr
    finally:
        Path(launcher).unlink()
    assert not Path(launcher).exists()


def test_console_launcher_rejects_unverified_architecture(monkeypatch):
    import tests.inner.windows_exec_launcher_prototype as launcher_module

    monkeypatch.setattr(launcher_module.platform, "machine", lambda: "ARM64")
    with pytest.raises(OSError, match="native x64"):
        create_console_launcher("pass", sys.executable)


def test_console_launcher_prototype_preexisting_child_escapes_parent_job(tmp_path):
    ready = tmp_path / "ready.json"
    code = (
        "import json,os,pathlib,subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)']); "
        "ready=pathlib.Path(sys.argv[1]); temporary=ready.with_suffix('.tmp'); "
        "temporary.write_text(json.dumps([os.getpid(),child.pid])); "
        "temporary.replace(ready); time.sleep(120)"
    )
    policy = _policy(active=True)
    launcher = create_console_launcher(
        _launcher_inline_source(sys.executable, policy), sys.executable
    )
    process = subprocess.Popen(
        [launcher, "-c", code, str(ready)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    handle = None
    children = []
    try:
        deadline = time.monotonic() + 30
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), "Target did not start"
        children = [psutil.Process(pid) for pid in json.loads(ready.read_text())]
        assert all(child.is_running() for child in children)
        # Assign after startup to expose the stub/Python race deterministically.
        handle = get_backend(policy.backend_type).post_spawn(policy, process.pid)
        assert handle is not None, "Native host failed to establish Job Object containment"
        handle.close()
        process.wait(timeout=10)
        for child in children:
            with pytest.raises(psutil.TimeoutExpired):
                child.wait(timeout=0.1)
    finally:
        if not children and process.poll() is None:
            children = psutil.Process(process.pid).children(recursive=True)
        if handle is not None:
            handle.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        for child in children:
            if child.is_running():
                child.kill()
                child.wait(timeout=10)
        Path(launcher).unlink()
