"""psmux-backed terminal multiplexer for native Windows.

See ``designs/OMNIGENT_TERMINAL_BRIDGE.md`` for the design and the
:class:`~omnigent.inner.terminal.TerminalInstance` documentation for the
underlying tmux-compatible machinery psmux implements.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

from omnigent._platform import IS_WINDOWS
from omnigent.inner.datamodel import OSEnvSpec, TerminalEnvSpec
from omnigent.inner.os_env import OSEnvironment, create_os_environment
from omnigent.inner.sandbox import with_additional_read_roots
from omnigent.inner.terminal import TerminalInstance, build_terminal_os_env_spec
from omnigent.inner.terminal_lifecycle import (
    TERMINAL_INSTANCE_ID_ENV,
    TERMINAL_LAUNCH_ID_ENV,
    TERMINAL_LAUNCH_SESSION_ID_ENV,
)
from omnigent.runner.identity import strip_runner_auth_secrets

logger = logging.getLogger(__name__)


def native_terminal_supported() -> bool:
    """Whether the platform can run its native terminal multiplexer."""
    return not IS_WINDOWS or shutil.which("psmux") is not None


_PSMUX_CLEAN_ENV_SCRIPT = """\
$unsetCount = [int]$args[0]
for ($index = 0; $index -lt $unsetCount; $index++) {
    Remove-Item -LiteralPath "Env:$($args[$index + 1])" -ErrorAction SilentlyContinue
}
$commandIndex = $unsetCount + 1
$command = $args[$commandIndex]
$commandArgs = if ($commandIndex + 1 -lt $args.Count) {
    @($args[($commandIndex + 1)..($args.Count - 1)])
} else {
    @()
}
& $command @commandArgs
exit $LASTEXITCODE
"""


class PsmuxTerminalInstance(TerminalInstance):
    """Terminal instance launched through psmux on native Windows."""

    backend_name: str = "psmux"

    @property
    def tmux_target(self) -> str:
        safe_name = "".join(ch if ch.isalnum() else "-" for ch in self.name)
        safe_key = "".join(ch if ch.isalnum() else "-" for ch in self.session_key)
        return f"omnigent-{safe_name}-{safe_key}-{abs(hash(self.private_dir)) & 0xFFFF:x}"

    def _tmux_base_cmd(self) -> list[str]:
        return ["psmux", "-S", str(self.socket_path)]

    async def launch(self, *, cwd: Path | None = None) -> None:
        if self.running:
            return
        self._last_exit_snapshot = None
        self._last_exit_status = None
        self._last_exit_signal = None
        effective_cwd = str(cwd or self.private_dir)
        env: dict[str, str] = os.environ.copy() if self.inherit_env else {}
        env.pop("OMNIGENT_TMUX_SOCK", None)
        env.update(self.env)
        for key in self.env_unset:
            env.pop(key, None)
        for key in (
            TERMINAL_INSTANCE_ID_ENV,
            TERMINAL_LAUNCH_ID_ENV,
            TERMINAL_LAUNCH_SESSION_ID_ENV,
        ):
            env.pop(key, None)
        try:
            env.update(self.lifecycle_trace.launch_environment(self.diagnostic_id))
        except Exception as exc:
            logger.debug("Terminal lifecycle correlation unavailable (%s)", type(exc).__name__)
        env = strip_runner_auth_secrets(env)

        executable = shutil.which(self.command) or self.command
        command_args = [executable, *self.args]
        if self.env_unset:
            wrapper_path = self.private_dir / "clean-env.ps1"
            wrapper_path.write_text(_PSMUX_CLEAN_ENV_SCRIPT, encoding="utf-8")
            powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or "pwsh.exe"
            command_args = [
                powershell,
                "-NoProfile",
                "-File",
                str(wrapper_path),
                str(len(self.env_unset)),
                *self.env_unset,
                *command_args,
            ]
        launch = [
            "new-session",
            "-d",
            "-s",
            self.tmux_target,
            "-x",
            "80",
            "-y",
            "24",
            "-c",
            effective_cwd,
            "--",
            *command_args,
        ]
        base_cmd = self._tmux_base_cmd()
        if self.keep_alive_after_exit:
            # psmux does not accept tmux's multi-command ``;`` argv. Load the
            # option at server startup so even an immediately exiting CLI
            # leaves its final pane available for diagnostics.
            config_path = self.private_dir / "psmux.conf"
            config_path.write_text("set-option -gq remain-on-exit on\n", encoding="utf-8")
            base_cmd = ["psmux", "-f", str(config_path), "-S", str(self.socket_path)]
        proc = await asyncio.create_subprocess_exec(
            *base_cmd,
            *launch,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"psmux launch failed (rc={proc.returncode}): {stderr.decode().strip()}"
            )
        self.running = True
        self.launch_cwd = effective_cwd

    async def resize(self, *, cols: int, rows: int) -> None:
        """Resize the psmux pane when the browser terminal changes size."""
        if not self.running:
            raise RuntimeError("Terminal is not running")
        await self._tmux("resize-window", "-t", self.tmux_target, "-x", str(cols), "-y", str(rows))

    async def read(self, scrollback: int = 0, *, join_wrapped: bool = False) -> dict[str, object]:
        """Capture the screen together with psmux's cursor state."""
        result = await super().read(scrollback, join_wrapped=join_wrapped)
        if "screen" not in result or not self.running:
            return result
        try:
            styled_capture_args = [
                "capture-pane",
                "-t",
                self.tmux_target,
                "-p",
                "-e",
            ]
            if scrollback > 0:
                styled_capture_args.extend(["-S", f"-{scrollback}"])
            if join_wrapped:
                styled_capture_args.append("-J")
            styled_screen = await self._tmux_output(*styled_capture_args)
            result["screen"] = styled_screen
        except RuntimeError:
            # Keep the plain capture from the base implementation when an
            # older psmux does not support styled captures.
            pass
        try:
            cursor = await self._tmux_output(
                "display-message",
                "-p",
                "-t",
                self.tmux_target,
                "#{cursor_x},#{cursor_y}",
            )
            x, y = cursor.strip().split(",", maxsplit=1)
            result.update(
                cursor_x=int(x),
                cursor_y=int(y),
                # psmux currently always formats cursor_flag as "0", even
                # when its native terminal visibly renders the cursor.
                cursor_visible=True,
            )
        except (RuntimeError, ValueError):
            pass
        return result


class PsmuxTerminalMuxBackend:
    """Windows terminal backend using psmux as a tmux-compatible multiplexer."""

    @property
    def name(self) -> str:
        return "psmux"

    def validate_available(self) -> None:
        """Fail loudly when the psmux backend cannot run on this machine."""
        if not IS_WINDOWS:
            raise RuntimeError("psmux terminal backend is only supported on Windows")
        if shutil.which("psmux") is None:
            raise RuntimeError(
                "psmux is required for Omnigent-managed terminals on native Windows "
                "but was not found on PATH. Install psmux and restart the Omnigent "
                "host, or use WSL/Linux/macOS for the tmux terminal backend."
            )

    def create(
        self,
        terminal_name: str,
        session_key: str,
        spec: TerminalEnvSpec,
        *,
        parent_os_env: OSEnvSpec | None = None,
        parent_environment: OSEnvironment | None = None,
        cwd_override: str | None = None,
        sandbox_override: str | None = None,
        conversation_link: str | None = None,
    ) -> tuple[TerminalInstance, Path]:
        self.validate_available()
        effective_os_env = build_terminal_os_env_spec(
            spec,
            parent_os_env_spec=parent_os_env,
            cwd_override=cwd_override,
            sandbox_override=sandbox_override,
        )
        private_dir = Path(tempfile.mkdtemp(prefix="omnigent-terminal-"))
        cwd = Path(effective_os_env.cwd or os.getcwd()).resolve()
        os_env = None
        if parent_environment is not None:
            inherited_policy = None
            if spec.os_env is None or spec.os_env == "inherit":
                inherited_policy = getattr(parent_environment, "sandbox", None)
                parent_cwd = getattr(parent_environment, "cwd", None)
                if inherited_policy is not None and parent_cwd is not None:
                    inherited_policy = with_additional_read_roots(inherited_policy, [parent_cwd])
            os_env = create_os_environment(
                effective_os_env,
                sandbox_policy=inherited_policy,
                copy_on_write_environment=parent_environment.copy_on_write_environment,
            )
        command = (
            spec.command
            or shutil.which("pwsh")
            or shutil.which("powershell.exe")
            or os.environ.get("COMSPEC")
            or "cmd.exe"
        )
        instance = PsmuxTerminalInstance(
            name=terminal_name,
            session_key=session_key,
            socket_path=private_dir / "psmux.sock",
            private_dir=private_dir,
            os_env=os_env,
            command=command,
            args=list(spec.args),
            env=dict(spec.env),
            env_unset=list(spec.env_unset),
            inherit_env=spec.inherit_env,
            conversation_link=conversation_link,
            scrollback=spec.scrollback,
            tmux_allow_passthrough=spec.tmux_allow_passthrough,
            tmux_start_on_attach=spec.tmux_start_on_attach,
            keep_alive_after_exit=spec.keep_alive_after_exit,
        )
        return instance, cwd
