"""Opt-in native containment proof; production still uses the existing launcher.

Set OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER=1 with an x64 MSVC/Windows SDK build
environment. Tests build both an immutable release stub and a checkpoint stub.
They prove private-job cleanup and immediate spawning-parent death handling.
"""

from __future__ import annotations

import asyncio
import ctypes
import ctypes.wintypes as wintypes
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from omnigent.inner.sandbox import SandboxPolicy, _launcher_inline_source, get_backend
from omnigent.inner.windows_exec_launcher import CONFIG_STREAM
from tests.inner.windows_private_job_launcher import (
    create_private_job_launcher,
    remove_private_job_launcher,
)
from tests.inner.windows_private_job_launcher import (
    private_test_directory as _test_directory,
)

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows executable")


@pytest.fixture
def tmp_path():
    yield from _test_directory.__wrapped__()


@pytest.fixture(autouse=True)
def isolate_invocation_storage(tmp_path, monkeypatch):
    from omnigent.inner import windows_exec_launcher

    monkeypatch.setattr(windows_exec_launcher, "_known_profile", lambda: tmp_path)


@pytest.fixture(scope="module")
def native_stubs(tmp_path_factory):
    if os.environ.get("OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER") != "1":
        pytest.skip("opt in with OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER=1; requires x64 MSVC/SDK")
    if platform.machine().lower() not in {"amd64", "x86_64"} or struct.calcsize("P") != 8:
        pytest.fail("opted-in private-job prototype requires native Windows x64")
    from dev.windows_launcher.build import build_launcher

    output = tmp_path_factory.mktemp("native-private-job-build")
    release = build_launcher(output / "release.exe")
    checkpoints = build_launcher(output / "checkpoints.exe", checkpoints=True)
    return release, checkpoints


def _policy(active: bool = True) -> SandboxPolicy:
    return SandboxPolicy(
        backend_type="windows_jobobject" if active else "none",
        active=active,
        read_roots=None,
        write_roots=[],
        write_files=[],
        allow_network=True,
    )


def _tree_source(ready: Path, *, release: Path | None = None, exit_code: int = 37) -> str:
    wait = (
        f"while not pathlib.Path({str(release)!r}).exists(): time.sleep(0.02)\n"
        if release
        else "time.sleep(120)\n"
    )
    return (
        "import json,os,pathlib,subprocess,sys,time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'])\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getpid(),child.pid]))\n"
        "temporary.replace(ready)\n" + wait + f"sys.exit({exit_code})\n"
    )


def _remember_tree(process: subprocess.Popen, owned: list[psutil.Process]) -> None:
    with suppress(psutil.NoSuchProcess):
        seen = {child.pid for child in owned}
        for child in psutil.Process(process.pid).children(recursive=True):
            if child.pid not in seen:
                owned.append(child)


def _diagnostics(process: subprocess.Popen, stderr: Path) -> str:
    output = stderr.read_text(encoding="utf-8", errors="replace") if stderr.exists() else ""
    return f"stub pid={process.pid}, exit={process.poll()}, stderr={output!r}"


def _wait_ready(
    ready: Path, process: subprocess.Popen, stderr: Path, owned: list[psutil.Process]
) -> list[int]:
    deadline = time.monotonic() + 20
    last_error = None
    while True:
        if ready.exists():
            try:
                pids = json.loads(ready.read_text())
            except PermissionError as error:
                if os.name != "nt":
                    raise
                last_error = error
            else:
                break
        _remember_tree(process, owned)
        assert process.poll() is None, _diagnostics(process, stderr)
        assert time.monotonic() < deadline, (
            f"startup timeout: {_diagnostics(process, stderr)}; ready read error={last_error!r}"
        )
        time.sleep(0.02)
    for pid in pids:
        with suppress(psutil.NoSuchProcess):
            if pid not in {child.pid for child in owned}:
                owned.append(psutil.Process(pid))
    _remember_tree(process, owned)
    return pids


def test_ready_publication_permission_failure_is_bounded(monkeypatch, tmp_path):
    import tests.inner.test_windows_private_job_launcher as module

    class DeniedReady:
        def exists(self):
            return True

        def read_text(self):
            raise PermissionError("publication denied")

    ticks = iter([0.0, 21.0])
    monkeypatch.setattr(
        module, "time", SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None)
    )
    monkeypatch.setattr(module, "_remember_tree", lambda *_: None)
    monkeypatch.setattr(module, "_diagnostics", lambda *_: "test process still alive")
    with pytest.raises(AssertionError, match=r"startup timeout.*publication denied"):
        _wait_ready(DeniedReady(), SimpleNamespace(poll=lambda: None), tmp_path / "stderr", [])


def _assert_stopped(owned: list[psutil.Process]) -> None:
    _, alive = psutil.wait_procs(owned, timeout=10)
    assert not alive, (
        f"owned children survived: {[(child.pid, child.status()) for child in alive]}"
    )


def _cleanup(owned: list[psutil.Process]) -> None:
    for child in owned:
        with suppress(psutil.NoSuchProcess):
            child.kill()
    _, alive = psutil.wait_procs(owned, timeout=10)
    assert not alive, f"cleanup failed for owned pids: {[child.pid for child in alive]}"


@contextmanager
def _running(
    launcher: str, tmp_path: Path, args: list[str], *, env: dict[str, str] | None = None
) -> Iterator[tuple[subprocess.Popen, Path, list[psutil.Process]]]:
    stderr = tmp_path / f"stderr-{uuid.uuid4().hex}.txt"
    owned: list[psutil.Process] = []
    try:
        with stderr.open("wb") as output:
            process = subprocess.Popen(
                [launcher, *args], stdout=subprocess.DEVNULL, stderr=output, env=env
            )
            try:
                yield process, stderr, owned
            finally:
                _remember_tree(process, owned)
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                _cleanup(owned)
    finally:
        remove_private_job_launcher(launcher)


def test_private_launcher_literal_argv_stdio_exit_and_spaced_unicode_paths(
    native_stubs, tmp_path, monkeypatch
):
    interpreter_dir = tmp_path / "Python space Å漢字"
    interpreter_dir.mkdir()
    interpreter = interpreter_dir / "python.exe"
    shutil.copy2(sys.executable, interpreter)
    original_environment = Path(sys.executable).parent.parent
    shutil.copy2(original_environment / "pyvenv.cfg", interpreter_dir / "pyvenv.cfg")
    original_site = original_environment / "Lib" / "site-packages"
    monkeypatch.setattr(sys, "executable", str(interpreter))
    cwd = tmp_path / "cwd space Å漢字"
    cwd.mkdir()
    arguments = [
        "",
        "space value",
        'quote"value',
        "%PATH%",
        "a&b|c>d<e^f",
        "semi;colon",
        "Å漢字😀",
        "end\\",
        '\\"',
    ]
    source = f"import sys; sys.path.insert(0, {str(original_site)!r}); " + _launcher_inline_source(
        str(interpreter), _policy(), cwd=str(cwd)
    )
    launcher = create_private_job_launcher(
        source, str(interpreter), native_stubs[0], active=True, directory=cwd
    )
    code = (
        "import json,os,sys; "
        "print(json.dumps({'argv':sys.argv[1:],'cwd':os.getcwd(),'input':sys.stdin.read()})); "
        "print('target stderr',file=sys.stderr); sys.exit(37)"
    )
    try:
        assert Path(launcher).read_bytes() == native_stubs[0].read_bytes()
        result = subprocess.run(
            [launcher, "-c", code, *arguments],
            input="stdin literal %PATH% Å漢字",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            cwd=cwd,
            env={
                **os.environ,
                "PYTHONUTF8": "1",
                "OMNIGENT_LAUNCHER_TEST_FAIL_JOB": "1",
                "OMNIGENT_LAUNCHER_TEST_FAIL_RESUME": "1",
                "OMNIGENT_LAUNCHER_TEST_CHECKPOINT": "invalid-release-build-checkpoint",
            },
        )
        assert result.returncode == 37, result.stderr
        assert json.loads(result.stdout) == {
            "argv": arguments,
            "cwd": str(cwd),
            "input": "stdin literal %PATH% Å漢字",
        }
        assert "target stderr" in result.stderr
    finally:
        remove_private_job_launcher(launcher)
    assert not Path(launcher).exists()
    assert not Path(launcher + CONFIG_STREAM).exists()


def test_private_launcher_rejects_unverified_architecture(monkeypatch, tmp_path):
    import omnigent.inner.windows_exec_launcher as factory

    monkeypatch.setattr(factory.platform, "machine", lambda: "ARM64")
    with pytest.raises(OSError, match="native Windows x64"):
        create_private_job_launcher("pass", sys.executable, tmp_path / "unused.exe", active=True)


def test_private_launcher_cleanup_refuses_unowned_directory(tmp_path):
    unowned = tmp_path / "private-job-unowned"
    unowned.mkdir()
    marker = unowned / "launcher.exe"
    marker.write_bytes(b"owned by someone else")
    with pytest.raises(ValueError, match="not owned"):
        remove_private_job_launcher(str(marker))
    assert marker.read_bytes() == b"owned by someone else"


@pytest.mark.parametrize("active", [True, False], ids=["private-job", "inactive"])
def test_private_launcher_normal_exit_closes_only_active_job(native_stubs, tmp_path, active):
    ready, release = tmp_path / "ready.json", tmp_path / "release"
    source = _launcher_inline_source(sys.executable, _policy(active))
    launcher = create_private_job_launcher(source, sys.executable, native_stubs[0], active=active)
    with _running(launcher, tmp_path, ["-c", _tree_source(ready, release=release)]) as state:
        process, stderr, owned = state
        pids = _wait_ready(ready, process, stderr, owned)
        grandchild = next(child for child in owned if child.pid == pids[1])
        release.touch()
        assert process.wait(timeout=20) == 37, _diagnostics(process, stderr)
        if active:
            _assert_stopped(owned)
        else:
            with pytest.raises(psutil.TimeoutExpired):
                grandchild.wait(timeout=0.2)


@pytest.mark.parametrize("outer_job", [False, True], ids=["forced-stub-death", "late-outer-job"])
def test_private_launcher_death_stops_existing_descendants(native_stubs, tmp_path, outer_job):
    ready = tmp_path / "ready.json"
    policy = _policy()
    launcher = create_private_job_launcher(
        _launcher_inline_source(sys.executable, policy),
        sys.executable,
        native_stubs[0],
        active=True,
    )
    with _running(launcher, tmp_path, ["-c", _tree_source(ready)]) as state:
        process, stderr, owned = state
        _wait_ready(ready, process, stderr, owned)
        assert len(owned) >= 3, "expected wrapper, target and grandchild"
        handle = None
        try:
            if outer_job:
                handle = get_backend(policy.backend_type).post_spawn(policy, process.pid)
                assert handle is not None, _diagnostics(process, stderr)
                handle.close()
            else:
                process.kill()
            process.wait(timeout=10)
            _assert_stopped(owned)
        finally:
            if handle is not None:
                handle.close()


def test_private_launcher_inherited_nested_host_job(native_stubs, tmp_path):
    ready, host_ready = tmp_path / "ready.json", tmp_path / "host.json"
    launcher = create_private_job_launcher(
        _launcher_inline_source(sys.executable, _policy()),
        sys.executable,
        native_stubs[0],
        active=True,
    )
    repository = str(Path(__file__).resolve().parents[2])
    host_source = (
        "import ctypes,ctypes.wintypes as w,json,os,pathlib,subprocess,sys,time\n"
        f"sys.path.insert(0,{repository!r})\n"
        "from omnigent.inner.sandbox import SandboxPolicy,get_backend\n"
        "policy=SandboxPolicy('windows_jobobject',True,None,[],[],True)\n"
        "job=get_backend(policy.backend_type).post_spawn(policy,os.getpid())\n"
        "assert job is not None,'host job assignment failed'\n"
        f"stub=subprocess.Popen({[launcher, '-c', _tree_source(ready)]!r})\n"
        "k=ctypes.windll.kernel32\n"
        "k.IsProcessInJob.argtypes=[w.HANDLE,w.HANDLE,ctypes.POINTER(w.BOOL)]\n"
        "k.IsProcessInJob.restype=w.BOOL\n"
        "member=w.BOOL()\n"
        "assert k.IsProcessInJob(w.HANDLE(int(stub._handle)),w.HANDLE(job._handle),"
        "ctypes.byref(member)) and member.value,'stub did not inherit host job'\n"
        f"ready=pathlib.Path({str(host_ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getpid(),stub.pid])); temporary.replace(ready)\n"
        "time.sleep(120)\n"
    )
    stderr = tmp_path / "host-stderr.txt"
    owned: list[psutil.Process] = []
    try:
        with stderr.open("wb") as output:
            host = subprocess.Popen(
                [sys.executable, "-c", host_source],
                stdout=subprocess.DEVNULL,
                stderr=output,
            )
            try:
                host_pids = _wait_ready(host_ready, host, stderr, owned)
                _wait_ready(ready, host, stderr, owned)
                assert len(owned) >= 4, "expected inherited stub, wrapper, target and grandchild"
                next(child for child in owned if child.pid == host_pids[0]).kill()
                host.wait(timeout=10)
                _assert_stopped(owned)
            finally:
                _remember_tree(host, owned)
                if host.poll() is None:
                    host.kill()
                host.wait(timeout=10)
                _cleanup(owned)
    finally:
        remove_private_job_launcher(launcher)


def test_private_launcher_parent_death_without_outer_job_stops_tree(native_stubs, tmp_path):
    ready, host_ready = tmp_path / "ready.json", tmp_path / "host.json"
    launcher = create_private_job_launcher(
        _launcher_inline_source(sys.executable, _policy()),
        sys.executable,
        native_stubs[0],
        active=True,
    )
    host_source = (
        "import json,os,pathlib,subprocess,time\n"
        f"stub=subprocess.Popen({[launcher, '-c', _tree_source(ready)]!r})\n"
        f"ready=pathlib.Path({str(host_ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getpid(),stub.pid])); temporary.replace(ready)\n"
        "time.sleep(120)\n"
    )
    stderr = tmp_path / "parent-stderr.txt"
    owned: list[psutil.Process] = []
    try:
        with stderr.open("wb") as output:
            host = subprocess.Popen(
                [sys.executable, "-c", host_source], stdout=subprocess.DEVNULL, stderr=output
            )
            try:
                host_pids = _wait_ready(host_ready, host, stderr, owned)
                _wait_ready(ready, host, stderr, owned)
                assert len(owned) >= 4
                caller = next(child for child in owned if child.pid == host_pids[0])
                stub = next(child for child in owned if child.pid == host_pids[1])
                stub_tree = [stub, *stub.children(recursive=True)]
                caller.kill()
                host.wait(timeout=10)
                caller.wait(timeout=10)
                _assert_stopped(stub_tree)
                _assert_stopped(owned)
            finally:
                _remember_tree(host, owned)
                if host.poll() is None:
                    host.kill()
                host.wait(timeout=10)
                _cleanup(owned)
    finally:
        remove_private_job_launcher(launcher)


@contextmanager
def _checkpoint_events() -> Iterator[tuple[dict[str, str], object, object]]:
    kernel = ctypes.windll.kernel32
    kernel.CreateEventW.argtypes = [
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    ]
    kernel.CreateEventW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.SetEvent.argtypes = [wintypes.HANDLE]
    kernel.SetEvent.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handles = []
    env = {}
    try:
        for name in ("READY", "RELEASE"):
            event_name = f"Local\\omnigent-private-job-{name}-{uuid.uuid4().hex}"
            handle = kernel.CreateEventW(None, True, False, event_name)
            assert handle, f"CreateEventW({name}) failed"
            handles.append(handle)
            env[f"OMNIGENT_LAUNCHER_TEST_{name}_EVENT"] = event_name
        yield env, handles[0], handles[1]
    finally:
        for handle in handles:
            kernel.CloseHandle(handle)


@pytest.mark.parametrize("checkpoint", ["before_create", "after_create"])
def test_private_launcher_abrupt_startup_death(native_stubs, tmp_path, checkpoint):
    marker = tmp_path / "executed"
    source = f"import pathlib,time; pathlib.Path({str(marker)!r}).touch(); time.sleep(120)"
    launcher = create_private_job_launcher(source, sys.executable, native_stubs[1], active=True)
    with _checkpoint_events() as events:
        env = {**os.environ, **events[0], "OMNIGENT_LAUNCHER_TEST_CHECKPOINT": checkpoint}
        with _running(launcher, tmp_path, [], env=env) as state:
            process, stderr, owned = state
            deadline = time.monotonic() + 10
            while ctypes.windll.kernel32.WaitForSingleObject(events[1], 20) != 0:
                assert process.poll() is None, _diagnostics(process, stderr)
                assert time.monotonic() < deadline, _diagnostics(process, stderr)
            _remember_tree(process, owned)
            if checkpoint == "after_create":
                assert len(owned) == 1, "expected exactly one suspended Python child"
            else:
                assert not owned, "Python started before the before_create checkpoint"
            assert not marker.exists(), "suspended child executed before resume"
            process.kill()
            process.wait(timeout=10)
            _assert_stopped(owned)
            assert not marker.exists()


@pytest.mark.parametrize("checkpoint", ["before_parent_capture", "before_create", "after_create"])
def test_private_launcher_spawning_parent_dies_during_startup(native_stubs, tmp_path, checkpoint):
    marker, host_ready = tmp_path / "executed", tmp_path / "parent.json"
    launcher = create_private_job_launcher(
        f"import pathlib,time; pathlib.Path({str(marker)!r}).touch(); time.sleep(120)",
        sys.executable,
        native_stubs[1],
        active=True,
    )
    source = (
        "import json,os,pathlib,subprocess,time\n"
        f"stub=subprocess.Popen({[launcher]!r})\n"
        f"ready=pathlib.Path({str(host_ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getpid(),stub.pid])); temporary.replace(ready)\n"
        "time.sleep(120)\n"
    )
    stderr = tmp_path / "parent-startup-stderr.txt"
    owned = []
    with _checkpoint_events() as events:
        env = {**os.environ, **events[0], "OMNIGENT_LAUNCHER_TEST_CHECKPOINT": checkpoint}
        try:
            with stderr.open("wb") as output:
                host = subprocess.Popen(
                    [sys.executable, "-c", source],
                    stdout=subprocess.DEVNULL,
                    stderr=output,
                    env=env,
                )
                try:
                    pids = _wait_ready(host_ready, host, stderr, owned)
                    deadline = time.monotonic() + 10
                    while ctypes.windll.kernel32.WaitForSingleObject(events[1], 20) != 0:
                        assert host.poll() is None, _diagnostics(host, stderr)
                        assert time.monotonic() < deadline, _diagnostics(host, stderr)
                    _remember_tree(host, owned)
                    caller = next(child for child in owned if child.pid == pids[0])
                    stub = next(child for child in owned if child.pid == pids[1])
                    child_tree = stub.children(recursive=True)
                    assert len(child_tree) == (1 if checkpoint == "after_create" else 0)
                    assert not marker.exists()
                    caller.kill()
                    host.wait(timeout=10)
                    assert ctypes.windll.kernel32.SetEvent(events[2])
                    _assert_stopped([stub, *child_tree])
                    assert not marker.exists(), "Python ran after its spawning parent died"
                finally:
                    if host.poll() is None:
                        host.kill()
                    host.wait(timeout=10)
                    _cleanup(owned)
        finally:
            remove_private_job_launcher(launcher)


@pytest.mark.parametrize("failure", ["interpreter", "config", "job"])
def test_private_launcher_fails_closed_before_execution(native_stubs, tmp_path, failure):
    marker = tmp_path / "executed"
    interpreter = (
        str(tmp_path / "missing-python.exe") if failure == "interpreter" else sys.executable
    )
    launcher = create_private_job_launcher(
        f"import pathlib; pathlib.Path({str(marker)!r}).touch()",
        interpreter,
        native_stubs[1],
        active=True,
    )
    if failure == "config":
        Path(launcher + CONFIG_STREAM).write_bytes(b"OJLCFG01\x01")
    env = dict(os.environ)
    if failure == "job":
        env["OMNIGENT_LAUNCHER_TEST_FAIL_JOB"] = "1"
    with _running(launcher, tmp_path, [], env=env) as state:
        process, stderr, owned = state
        assert process.wait(timeout=10) != 0
        assert stderr.read_bytes(), _diagnostics(process, stderr)
        assert not marker.exists(), _diagnostics(process, stderr)
        _assert_stopped(owned)


def test_private_launcher_resume_failure_kills_known_suspended_child(native_stubs, tmp_path):
    marker = tmp_path / "executed"
    launcher = create_private_job_launcher(
        f"import pathlib; pathlib.Path({str(marker)!r}).touch()",
        sys.executable,
        native_stubs[1],
        active=True,
    )
    with _checkpoint_events() as events:
        env = {
            **os.environ,
            **events[0],
            "OMNIGENT_LAUNCHER_TEST_CHECKPOINT": "after_create",
            "OMNIGENT_LAUNCHER_TEST_FAIL_RESUME": "1",
        }
        with _running(launcher, tmp_path, [], env=env) as state:
            process, stderr, owned = state
            deadline = time.monotonic() + 10
            while ctypes.windll.kernel32.WaitForSingleObject(events[1], 20) != 0:
                assert process.poll() is None, _diagnostics(process, stderr)
                assert time.monotonic() < deadline, _diagnostics(process, stderr)
            _remember_tree(process, owned)
            assert len(owned) == 1, "expected a known suspended Python child"
            assert ctypes.windll.kernel32.SetEvent(events[2]), "release checkpoint failed"
            assert process.wait(timeout=10) != 0
            assert stderr.read_bytes(), _diagnostics(process, stderr)
            assert not marker.exists(), _diagnostics(process, stderr)
            _assert_stopped(owned)


@pytest.mark.parametrize(
    "version_output", [True, False], ids=["version-output", "version-timeout"]
)
async def test_private_launcher_sdk_version_probe_and_close(
    native_stubs, tmp_path, monkeypatch, version_output
):
    from claude_agent_sdk import ClaudeAgentOptions
    from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

    version_ready, ready = tmp_path / "version.json", tmp_path / "sdk.json"
    source = (
        "import json,os,pathlib,subprocess,sys,time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'])\n"
        "version='-v' in sys.argv[1:]\n"
        f"ready=pathlib.Path({str(version_ready)!r} if version else {str(ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getppid(),os.getpid(),child.pid]))\n"
        "temporary.replace(ready)\n"
        f"if version and {version_output!r}: print('2.1.266 (local mock)',flush=True)\n"
        "time.sleep(120)\n"
    )
    launcher = create_private_job_launcher(source, sys.executable, native_stubs[0], active=True)
    monkeypatch.delenv("CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK", raising=False)
    transport = SubprocessCLITransport(
        prompt="local mock only",
        options=ClaudeAgentOptions(cli_path=launcher, cwd=tmp_path, env={"ANTHROPIC_API_KEY": ""}),
    )
    owned: list[psutil.Process] = []
    try:
        await asyncio.wait_for(transport.connect(), timeout=15)
        assert version_ready.exists(), "actual SDK did not execute its version probe"
        # The version probe may already be dead; any survivor is captured for cleanup.
        for pid in json.loads(version_ready.read_text()):
            with suppress(psutil.NoSuchProcess):
                owned.append(psutil.Process(pid))
        _assert_stopped(owned)
        deadline = time.monotonic() + 15
        while not ready.exists():
            assert transport._process is not None
            assert transport._process.returncode is None, "SDK mock exited before startup"
            assert time.monotonic() < deadline, "SDK mock did not report its child tree"
            await asyncio.sleep(0.02)
        for pid in json.loads(ready.read_text()):
            owned.append(psutil.Process(pid))
        assert transport._process is not None
        owned.extend(psutil.Process(transport._process.pid).children(recursive=True))
        await asyncio.wait_for(transport.close(), timeout=15)
        _assert_stopped(owned)
    finally:
        if transport._process is not None:
            with suppress(psutil.NoSuchProcess):
                owned.extend(psutil.Process(transport._process.pid).children(recursive=True))
        await asyncio.wait_for(transport.close(), timeout=15)
        _cleanup(owned)
        remove_private_job_launcher(launcher)


async def test_private_launcher_sdk_client_cancellation_stops_tree(
    native_stubs, tmp_path, monkeypatch
):
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    ready = tmp_path / "cancel.json"
    source = (
        "import json,os,pathlib,subprocess,sys,time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'])\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        "temporary=ready.with_suffix('.tmp')\n"
        "temporary.write_text(json.dumps([os.getppid(),os.getpid(),child.pid]))\n"
        "temporary.replace(ready)\n"
        "for line in sys.stdin:\n"
        " request=json.loads(line)\n"
        " if request.get('type')=='control_request':\n"
        "  print(json.dumps({'type':'control_response','response':{'subtype':'success',"
        "'request_id':request['request_id'],'response':{}}}),flush=True)\n"
        "time.sleep(120)\n"
    )
    launcher = create_private_job_launcher(source, sys.executable, native_stubs[0], active=True)
    monkeypatch.setenv("CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK", "1")
    options = ClaudeAgentOptions(cli_path=launcher, cwd=tmp_path, env={"ANTHROPIC_API_KEY": ""})
    entered = asyncio.Event()
    owned: list[psutil.Process] = []

    async def client_session() -> None:
        async with ClaudeSDKClient(options=options):
            entered.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(client_session())
    try:
        deadline = time.monotonic() + 15
        while not entered.is_set():
            if task.done():
                task.result()
                pytest.fail("SDK client exited before connection")
            assert time.monotonic() < deadline, "SDK mock control initialization timed out"
            await asyncio.sleep(0.02)
        assert ready.exists(), "SDK client connected without mock child-tree evidence"
        owned = [psutil.Process(pid) for pid in json.loads(ready.read_text())]
        started = time.monotonic()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=12)
        _assert_stopped(owned)
        assert time.monotonic() - started < 12, "SDK cancellation exceeded its cleanup window"
    finally:
        if ready.exists():
            for pid in json.loads(ready.read_text()):
                with suppress(psutil.NoSuchProcess):
                    owned.append(psutil.Process(pid))
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=12)
        _cleanup(owned)
        remove_private_job_launcher(launcher)
