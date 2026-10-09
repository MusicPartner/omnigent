"""Opt-in psmux integration for the native Windows launcher candidate."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import psutil
import pytest

from omnigent.inner import windows_exec_launcher
from omnigent.inner.datamodel import OSEnvSandboxSpec, OSEnvSpec, TerminalEnvSpec
from omnigent.inner.sandbox import SandboxPolicy, create_exec_launcher
from omnigent.terminals.backend import PsmuxTerminalMuxBackend
from tests.inner.test_windows_private_job_launcher import native_stubs as _native_fixture

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows psmux integration")


@pytest.fixture(scope="module")
def native_stubs(tmp_path_factory):
    if os.environ.get("OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER") != "1":
        pytest.skip("set OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER=1 to run the native integration")
    if shutil.which("psmux") is None:
        pytest.fail("psmux is required when OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER=1")
    return _native_fixture.__wrapped__(tmp_path_factory)


def _prepare_unsigned_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, executable: Path
) -> None:
    resource = tmp_path / "omnigent" / "resources" / "windows_launcher"
    resource.mkdir(parents=True)
    asset_path = resource / "private_job_launcher-x64.exe"
    shutil.copyfile(executable, asset_path)
    manifest = {
        "schema": 1,
        "architecture": "amd64",
        "filename": asset_path.name,
        "sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
        "release_approved": False,
        "signing": {"status": "unsigned"},
    }
    (resource / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(
        windows_exec_launcher,
        "__file__",
        str(tmp_path / "omnigent" / "inner" / "windows_exec_launcher.py"),
    )


def _owned_process(record: dict[str, Any], key: str) -> psutil.Process:
    process = psutil.Process(int(record[f"{key}_pid"]))
    created = float(record[f"{key}_created"])
    if abs(process.create_time() - created) > 0.05:
        raise AssertionError(f"PID {process.pid} no longer identifies the recorded {key}")
    return process


def _stop_recorded_processes(records: list[dict[str, Any]]) -> None:
    owned: list[psutil.Process] = []
    for record in records:
        for key in ("target", "grandchild", "launcher"):
            try:
                process = _owned_process(record, key)
            except (psutil.NoSuchProcess, KeyError, AssertionError):
                continue
            owned.append(process)
            if process.is_running():
                process.kill()
    if owned:
        _, alive = psutil.wait_procs(owned, timeout=5)
        for process in alive:
            if process.is_running():
                process.kill()
        _, alive = psutil.wait_procs(owned, timeout=5)
        assert not alive, f"test-owned processes did not stop: {[p.pid for p in alive]}"


@pytest.mark.asyncio
async def test_windows_psmux_close_stops_native_launcher_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, native_stubs
) -> None:
    release_executable, _ = native_stubs
    _prepare_unsigned_resource(tmp_path, monkeypatch, release_executable)
    monkeypatch.setenv(windows_exec_launcher.SELECTOR, "native-dev")

    target_report = tmp_path / "target.json"
    grandchild_report = tmp_path / "grandchild.json"
    args = ["literal space", "semi;colon", "%PATH%", "Å漢字"]
    grandchild_code = (
        "import json,os,pathlib,time; "
        f"p=pathlib.Path({str(grandchild_report)!r}); "
        "p.write_text(json.dumps({'grandchild_pid':os.getpid(),"
        "'grandchild_created':__import__('psutil').Process().create_time()})); "
        "print('native-grandchild-ready',flush=True); time.sleep(300)"
    )
    target_code = (
        "import json,os,pathlib,psutil,subprocess,sys,time; "
        f"child=subprocess.Popen([sys.executable,'-c',{grandchild_code!r}]); "
        f"p=pathlib.Path({str(target_report)!r}); "
        "p.write_text(json.dumps({'target_pid':os.getpid(),"
        "'target_created':psutil.Process().create_time(),"
        "'grandchild_pid':child.pid,'argv':sys.argv[1:]})); "
        "print('native-target-ready '+json.dumps(sys.argv[1:],ensure_ascii=True),flush=True); "
        "time.sleep(300)"
    )
    policy = SandboxPolicy(
        backend_type="windows_jobobject",
        active=True,
        read_roots=None,
        write_roots=[],
        write_files=[],
        allow_network=True,
    )
    launcher_path = create_exec_launcher(sys.executable, policy)
    instance = None
    records: list[dict[str, Any]] = []
    try:
        spec = TerminalEnvSpec(
            command=launcher_path,
            args=["-c", target_code, *args],
            os_env=OSEnvSpec(
                type="caller_process",
                cwd=str(tmp_path),
                sandbox=OSEnvSandboxSpec(type="none"),
            ),
        )
        instance, cwd = PsmuxTerminalMuxBackend().create(
            "native-launcher", "psmux-integration", spec
        )
        await instance.launch(cwd=cwd)

        deadline = time.monotonic() + 20
        screen = ""
        while time.monotonic() < deadline:
            screen = str((await instance.read()).get("screen", ""))
            if target_report.exists() and grandchild_report.exists():
                if "native-target-ready" in screen and "native-grandchild-ready" in screen:
                    break
            await asyncio.sleep(0.1)
        assert target_report.is_file(), f"native target did not report startup; screen={screen!r}"
        assert grandchild_report.is_file(), (
            f"native grandchild did not report startup; screen={screen!r}"
        )
        records.append(json.loads(target_report.read_text(encoding="utf-8")))
        records[-1].update(json.loads(grandchild_report.read_text(encoding="utf-8")))
        assert records[-1]["argv"] == args
        assert "native-target-ready" in screen
        assert "native-grandchild-ready" in screen

        target = _owned_process(records[-1], "target")
        launcher_identity = os.path.normcase(os.path.abspath(launcher_path))
        launcher = next(
            (
                parent
                for parent in target.parents()
                if os.path.normcase(os.path.abspath(parent.exe())) == launcher_identity
            ),
            None,
        )
        assert launcher is not None, "target must descend from its exact native launcher"
        records[-1].update(launcher_pid=launcher.pid, launcher_created=launcher.create_time())
        processes = [target, _owned_process(records[-1], "grandchild")]
        await instance.close()
        instance = None
        _, alive = psutil.wait_procs(processes, timeout=10)
        assert not alive, (
            "closing the psmux terminal left native launcher descendants alive: "
            f"{[process.pid for process in alive]}"
        )
        _, alive = psutil.wait_procs([launcher], timeout=10)
        assert not alive, "closing the psmux terminal left its native launcher alive"
    finally:
        if instance is not None:
            await instance.close()
        _stop_recorded_processes(records)
        Path(launcher_path).unlink(missing_ok=True)
