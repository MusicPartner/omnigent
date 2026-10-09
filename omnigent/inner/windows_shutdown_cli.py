"""Windows desktop and CLI bridges to cooperative process shutdown."""

from __future__ import annotations

from typing import Protocol

import click
import psutil

from omnigent._platform import IS_WINDOWS


class _Server(Protocol):
    should_exit: bool

    def run(self) -> None: ...


def run_server(server: _Server) -> None:
    """Let a headless Windows server drain its existing lifespan on Stop."""
    from omnigent.inner.windows_process_shutdown import install_shutdown_listener

    listener = install_shutdown_listener(lambda: setattr(server, "should_exit", True))
    try:
        server.run()
    finally:
        listener.close()


def register_shutdown_command(group: click.Group) -> None:
    """Expose the private desktop bridge through the existing internal CLI."""

    @group.command("windows-shutdown", hidden=True)
    @click.argument("pid", type=click.IntRange(min=2))
    @click.option("--grace-seconds", type=click.FloatRange(min=0, max=60), default=30.0)
    @click.option("--created-before-ms", type=click.FloatRange(min=0), required=True)
    def windows_shutdown(pid: int, grace_seconds: float, created_before_ms: float) -> None:
        if not IS_WINDOWS:
            raise click.ClickException("Windows process shutdown is only available on Windows.")
        from omnigent.inner.windows_process_shutdown import stop_process

        try:
            created = psutil.Process(pid).create_time()
        except psutil.NoSuchProcess:
            return
        except psutil.AccessDenied as exc:
            raise click.ClickException("Cannot verify the desktop child identity.") from exc
        if created * 1000 > created_before_ms:
            raise click.ClickException("The desktop child PID has been reused.")
        if not stop_process(pid, grace_seconds=grace_seconds, expected_create_time=created):
            raise click.ClickException(f"Owned process tree for {pid} did not stop.")
