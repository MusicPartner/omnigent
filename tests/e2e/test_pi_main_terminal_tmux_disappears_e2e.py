"""E2E regression: a Pi terminal exit must not become a tmux-unavailable failure.

The production Pi terminal is launched with ``keep_alive_after_exit=True`` so
an exiting Pi CLI leaves a dead-but-capturable pane long enough for the runner
watcher to report a deterministic pane exit. This test exercises that behavior
against the real Pi CLI and a real runner-owned tmux server.

Pi rewrites ``process.title`` to ``pi`` early during startup. On Linux that can
replace the visible ``/proc/<pid>/cmdline`` before a polling test sees the
original ``--extension`` argv. Therefore this test does not discover Pi by
racing ``/proc``. Instead it seeds a tiny test-only Pi user extension under the
daemon HOME. Pi auto-loads that extension, which atomically records its own PID
and launch argv before the title rewrite matters to the test. The recorded PID
is then revalidated with psutil using the session workspace plus either the
original bridge marker or Pi's post-rewrite bare process title.

The journey never sends an LLM turn; a local fake Pi API-key/model record is
enough to keep the interactive CLI open until the test kills it.

    .venv/bin/python -m pytest \
        tests/e2e/test_pi_main_terminal_tmux_disappears_e2e.py -v
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import tarfile
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import psutil
import pytest
import yaml

from omnigent.process_logging import PROCESS_LOG_FILE_ENV_VAR
from tests._helpers.compat import apply_runner_env, compat_runner_cwd, runner_executable
from tests.e2e._harness_probes import cli_unavailable_reason
from tests.e2e.helpers import POLL_INTERVAL_S

_WORKTREE = Path(__file__).resolve().parents[2]
_PI_MODEL_ID = "claude-sonnet-4-5"
_TMUX_UNAVAILABLE_RE = re.compile(
    r"tmux unavailable after \d+ consecutive probes for terminal pi:main"
)

# Pi changes process.title very early, which makes /proc argv polling racy.
# This test-owned user extension captures the authoritative launch identity
# from inside Pi itself. It records pid/argv/cwd only; never environment or
# credentials. Pi auto-loads ~/.pi/agent/extensions/*.js.
_OBSERVER_EXTENSION_NAME = "omnigent-e2e-pid-observer.js"
_OBSERVER_OUTPUT_FILE = "e2e-pid-observation.json"
_OBSERVER_EXTENSION_SOURCE = """\
const fs = require("fs");
const path = require("path");

module.exports = function () {
    try {
        const argv = process.argv.slice();
        const flag = argv.indexOf("--extension");
        if (flag < 0 || flag + 1 >= argv.length) return;
        const bridgeDir = path.resolve(path.dirname(argv[flag + 1]));
        const out = path.join(bridgeDir, "__OBSERVER_OUTPUT_FILE__");
        const tmp = out + ".tmp";
        fs.writeFileSync(
            tmp,
            JSON.stringify({ pid: process.pid, argv: argv, cwd: process.cwd() })
        );
        fs.renameSync(tmp, out);
    } catch (err) {
        // Observation must never affect the Pi session under test.
    }
};
""".replace("__OBSERVER_OUTPUT_FILE__", _OBSERVER_OUTPUT_FILE)

pytestmark = [
    pytest.mark.skipif(
        (_reason := cli_unavailable_reason("pi")) is not None,
        reason=f"pi-native tmux-disappear e2e needs a runnable 'pi' CLI; {_reason}.",
    ),
    pytest.mark.skipif(
        shutil.which("tmux") is None,
        reason="pi-native terminal launch needs 'tmux' on PATH.",
    ),
    pytest.mark.skipif(
        (_node := cli_unavailable_reason("node")) is not None,
        reason=f"pi-native extension needs 'node'; {_node}.",
    ),
]


def _bridge_digest(session_id: str) -> str:
    """Return the session's hashed Pi bridge directory component."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:32]


def _bridge_marker(session_id: str) -> str:
    """Return the session-specific marker present in Pi's original argv."""
    return f"pi-native/{_bridge_digest(session_id)}"


def _bridge_dir(home: Path, session_id: str) -> Path:
    """Return the Pi bridge directory for *session_id* under *home*."""
    return home / ".omnigent" / "pi-native" / _bridge_digest(session_id)


def _read_pid_observation(bridge_dir: Path) -> dict | None:
    """Read the observer extension's atomic PID/argv record, when available."""
    try:
        record = json.loads((bridge_dir / _OBSERVER_OUTPUT_FILE).read_text())
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def _live_observed_pi(
    observation: dict,
    *,
    marker: str,
    workspace: Path,
) -> tuple[int, float] | None:
    """Return ``(pid, create_time)`` when the observation is still this Pi.

    Pi may already have rewritten its process title, so a live process is
    accepted when its cwd is the session workspace and its cmdline either
    still contains the bridge marker or has become the bare ``pi`` title.
    ``create_time`` protects cleanup from PID reuse.
    """
    pid = observation.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        process = psutil.Process(pid)
        cmdline = [token for token in process.cmdline() if token]
        cwd = os.path.realpath(process.cwd())
        create_time = process.create_time()
    except (psutil.Error, OSError):
        return None
    if cwd != os.path.realpath(workspace):
        return None
    if not any(marker in token for token in cmdline) and cmdline != ["pi"]:
        return None
    return pid, create_time


def _kill_observed_pi(pid: int, create_time: float) -> None:
    """Best-effort kill of exactly the observed Pi process, never its tmux server."""
    try:
        process = psutil.Process(pid)
        if abs(process.create_time() - create_time) > 0.001:
            return
        process.kill()
    except (psutil.Error, OSError):
        pass


def _scan_home_logs_for(home: Path, pattern: re.Pattern[str]) -> str | None:
    """Return the first process-log line under *home* matching *pattern*."""
    for log_path in home.rglob("*.log"):
        try:
            text = log_path.read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if pattern.search(line):
                return line
    return None


class _PiHost:
    """Spawned host daemon backed by a test-local Pi login."""

    def __init__(
        self,
        proc: subprocess.Popen[bytes],
        host_id: str,
        home: Path,
        daemon_log: Path,
    ) -> None:
        self.proc = proc
        self.host_id = host_id
        self.home = home
        self.daemon_log = daemon_log


def _seed_pi_home(home: Path) -> str:
    """Seed a local Pi login, observer extension, and Omnigent host config."""
    omni_dir = home / ".omnigent"
    omni_dir.mkdir(parents=True, exist_ok=True)
    host_id = uuid.uuid4().hex
    host_name = f"e2e-pi-tmux-{uuid.uuid4().hex[:12]}"
    (omni_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {"host": {"host_id": host_id, "name": host_name}},
            default_flow_style=False,
            sort_keys=True,
        )
    )

    pi_agent = home / ".pi" / "agent"
    pi_agent.mkdir(parents=True, exist_ok=True)
    extensions_dir = pi_agent / "extensions"
    extensions_dir.mkdir(parents=True, exist_ok=True)
    (extensions_dir / _OBSERVER_EXTENSION_NAME).write_text(_OBSERVER_EXTENSION_SOURCE)
    (pi_agent / "auth.json").write_text(
        json.dumps({"anthropic": {"type": "api_key", "key": "test-token"}})
    )
    (pi_agent / "models-store.json").write_text(
        json.dumps(
            {
                "anthropic": {
                    "models": [
                        {
                            "id": _PI_MODEL_ID,
                            "name": "Claude Sonnet 4.5",
                            "api": "anthropic-messages",
                            "provider": "anthropic",
                            "baseUrl": "https://api.anthropic.com",
                            "input": ["text", "image"],
                        }
                    ],
                    "checkedAt": 1750000000,
                }
            }
        )
    )
    return host_id


def _wait_for_host_online(client: httpx.Client, host_id: str, timeout: float = 45.0) -> None:
    """Wait until the spawned host is registered online."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = client.get("/v1/hosts")
            if response.status_code == 200:
                for host in response.json().get("hosts", []):
                    if host["host_id"] == host_id and host["status"] == "online":
                        return
        except httpx.ConnectError:
            pass
        time.sleep(POLL_INTERVAL_S)
    raise AssertionError(f"Host {host_id!r} did not appear online within {timeout}s")


def _terminal_resource_present(client: httpx.Client, session_id: str) -> bool:
    """Return whether the runner currently exposes the session's pi:main terminal."""
    response = client.get(f"/v1/sessions/{session_id}/resources", timeout=30.0)
    if response.status_code != 200:
        return False
    for item in response.json().get("data", []):
        if item.get("type") != "terminal":
            continue
        metadata = item.get("metadata", {})
        if metadata.get("terminal_name") == "pi" and metadata.get("session_key") == "main":
            return True
    return False


@pytest.fixture(scope="module")
def pi_host(
    live_server: str,
    http_client: httpx.Client,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[_PiHost]:
    """Spawn a host daemon with the test-local Pi login."""
    home = tmp_path_factory.mktemp("pi-tmux-home")
    host_id = _seed_pi_home(home)
    daemon_log = home / "host-daemon.log"
    env = {
        **os.environ,
        "HOME": str(home),
        "OMNIGENT_CONFIG_HOME": str(home / ".omnigent"),
        "OMNIGENT_DATA_DIR": str(home / ".omnigent"),
        PROCESS_LOG_FILE_ENV_VAR: str(daemon_log),
    }
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(_WORKTREE),
            str(_WORKTREE / "sdks" / "python-client"),
            str(_WORKTREE / "sdks" / "ui"),
        ]
        + ([existing_pythonpath] if existing_pythonpath else [])
    )
    with open(daemon_log, "w") as log_fh:
        proc = subprocess.Popen(
            [runner_executable(), "-m", "omnigent.host._daemon_entry", "--server", live_server],
            env=apply_runner_env(env),
            cwd=compat_runner_cwd(),
            stdout=subprocess.DEVNULL,
            stderr=log_fh,
        )
    try:
        _wait_for_host_online(http_client, host_id, timeout=45.0)
        yield _PiHost(proc=proc, host_id=host_id, home=home, daemon_log=daemon_log)
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def test_pi_main_terminal_survives_pi_exit_without_tmux_unavailable(
    pi_host: _PiHost,
    http_client: httpx.Client,
) -> None:
    """Killing the real Pi CLI must produce pane-dead handling, not tmux loss."""
    host = pi_host
    spec_yaml = "\n".join(
        [
            "name: pi-native-ui",
            "prompt: |",
            "  Pi is running in the session terminal.",
            "executor:",
            "  harness: pi-native",
            "spawn: true",
            "os_env:",
            "  type: caller_process",
            "  cwd: .",
            "  sandbox:",
            "    type: none",
            "",
        ]
    )
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = spec_yaml.encode()
        info = tarfile.TarInfo("pi-native-ui.yaml")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

    workspace = host.home / "ws"
    workspace.mkdir(exist_ok=True)
    create = http_client.post(
        "/v1/sessions",
        data={
            "metadata": json.dumps(
                {
                    "host_id": host.host_id,
                    "workspace": str(workspace),
                    "labels": {
                        "omnigent.ui": "terminal",
                        "omnigent.wrapper": "pi-native-ui",
                    },
                }
            )
        },
        files={"bundle": ("pi-native-ui.tar.gz", buf.getvalue(), "application/gzip")},
        timeout=60.0,
    )
    assert create.status_code in (200, 201), f"session create failed: {create.text}"
    session_id = str(create.json()["session_id"])
    marker = _bridge_marker(session_id)
    bridge_dir = _bridge_dir(host.home, session_id)

    observed_identity: tuple[int, float] | None = None
    try:
        # The resource is the authoritative signal that the runner created
        # pi:main. Do not race Pi's mutable Linux process title for readiness.
        terminal_deadline = time.monotonic() + 45.0
        while time.monotonic() < terminal_deadline:
            if _terminal_resource_present(http_client, session_id):
                break
            if host.proc.poll() is not None:
                raise AssertionError(
                    f"host daemon exited (rc={host.proc.returncode}) before pi:main appeared; "
                    f"log tail:\n{host.daemon_log.read_text()[-2000:]}"
                )
            time.sleep(POLL_INTERVAL_S)
        assert _terminal_resource_present(http_client, session_id), (
            "pi:main terminal resource never appeared for session "
            f"{session_id!r}; the runner did not register the terminal."
        )

        # The Pi user extension records the real PID before process.title can
        # erase --extension from /proc/<pid>/cmdline. Revalidate the observed
        # PID against cwd and Pi's accepted pre/post-title cmdline shapes.
        observation: dict | None = None
        pid_deadline = time.monotonic() + 30.0
        while time.monotonic() < pid_deadline:
            observation = _read_pid_observation(bridge_dir)
            if observation is not None:
                observed_identity = _live_observed_pi(
                    observation,
                    marker=marker,
                    workspace=workspace,
                )
                if observed_identity is not None:
                    break
            time.sleep(0.25)
        assert observed_identity is not None, (
            "Pi observer did not yield a live process for session "
            f"{session_id!r}; observation={observation!r}; "
            f"daemon log tail:\n{host.daemon_log.read_text()[-2000:]}"
        )

        # Let the idle watcher arm, then kill exactly Pi -- never the tmux
        # server/launcher merely because it contains the bridge marker.
        time.sleep(2.5)
        pi_pid, pi_create_time = observed_identity
        _kill_observed_pi(pi_pid, pi_create_time)

        # Keep scanning after the terminal resource disappears: the buggy
        # watcher emits its generic tmux-unavailable signature a few probe
        # intervals later, so exiting the loop early would create a false pass.
        signature_line: str | None = None
        terminal_gone = False
        scan_deadline = time.monotonic() + 25.0
        while time.monotonic() < scan_deadline:
            hit = _scan_home_logs_for(host.home, _TMUX_UNAVAILABLE_RE)
            if hit is not None:
                signature_line = hit
                break
            if not _terminal_resource_present(http_client, session_id):
                terminal_gone = True
            time.sleep(0.5)

        if signature_line is None and not terminal_gone:
            terminal_gone = not _terminal_resource_present(http_client, session_id)
        assert terminal_gone or signature_line is not None, (
            "pi:main terminal never exited after the Pi CLI was killed -- the "
            "exit path was not exercised, so the reproduction is inconclusive."
        )
        assert signature_line is None, (
            "Bug reproduced: killing Pi made the pi:main tmux server disappear "
            "and the idle watcher emitted the generic tmux-unavailable failure "
            f"instead of a pane-dead exit:\n    {signature_line}"
        )
    finally:
        if observed_identity is not None:
            _kill_observed_pi(*observed_identity)
