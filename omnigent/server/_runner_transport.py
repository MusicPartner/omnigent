"""Server-side helpers for connecting to local runner transports."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx

# Type alias: callable returning an async context manager around a
# connected websockets client. Kept ``Any`` because the actual return
# type lives in :mod:`websockets.asyncio.client` and varies between
# library versions.
RunnerWSFactory = Callable[[str], Any]

RUNNER_TCP_BASE_URL_ENV = "OMNIGENT_RUNNER_TCP_BASE_URL"
RUNNER_UDS_PATH_ENV = "OMNIGENT_RUNNER_UDS_PATH"


def runner_transport_env_configured(environ: dict[str, str] | None = None) -> bool:
    """Return whether local runner transport env configuration is present."""
    env = os.environ if environ is None else environ
    return bool(
        _non_empty_env(env, RUNNER_TCP_BASE_URL_ENV) or _non_empty_env(env, RUNNER_UDS_PATH_ENV)
    )


def build_runner_transport_from_env(
    environ: dict[str, str] | None = None,
) -> tuple[httpx.AsyncClient, RunnerWSFactory, str]:
    """Build a local runner transport from environment configuration.

    ``OMNIGENT_RUNNER_TCP_BASE_URL`` is cross-platform and preferred. The UDS
    env var remains available for POSIX deployments. On native Windows, UDS-only
    configuration fails with the same actionable TCP guidance as
    :func:`build_runner_transport`.
    """
    env = os.environ if environ is None else environ
    tcp_base_url = _non_empty_env(env, RUNNER_TCP_BASE_URL_ENV)
    uds_path = _non_empty_env(env, RUNNER_UDS_PATH_ENV)
    client, ws_factory = build_runner_transport(
        tcp_base_url=tcp_base_url,
        uds_path=uds_path,
    )
    selected = "tcp" if tcp_base_url else "uds"
    return client, ws_factory, selected


def _non_empty_env(env: dict[str, str], name: str) -> str | None:
    """Return a stripped env value or ``None`` when unset/blank."""
    value = env.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def build_runner_transport(
    *,
    uds_path: str | None = None,
    tcp_base_url: str | None = None,
) -> tuple[httpx.AsyncClient, RunnerWSFactory]:
    """Build the best local runner transport for this platform.

    TCP is cross-platform and wins when configured. UDS remains the POSIX
    default. Native Windows has no Unix-domain-socket client support in the
    websockets path, so it fails with an actionable error unless a TCP base URL
    is provided.

    :param uds_path: Optional Unix-domain-socket path.
    :param tcp_base_url: Optional TCP runner URL, e.g. ``"http://127.0.0.1:9876"``.
    :returns: ``(client, ws_factory)`` for the selected runner transport.
    :raises RuntimeError: If no supported transport is configured.
    """
    if tcp_base_url:
        return build_tcp_runner(tcp_base_url)
    if uds_path and os.name != "nt":
        return build_uds_runner(uds_path)
    if uds_path and os.name == "nt":
        raise RuntimeError(
            "runner UDS transport is not supported on native Windows; "
            "configure a TCP runner base URL instead"
        )
    raise RuntimeError("no runner transport configured; provide tcp_base_url or uds_path")


def build_tcp_runner(base_url: str) -> tuple[httpx.AsyncClient, RunnerWSFactory]:
    """Build the HTTP client + WS factory for a TCP-attached runner.

    :param base_url: HTTP(S) runner base URL, e.g. ``"http://127.0.0.1:9876"``.
    :returns: ``(client, ws_factory)``. The WebSocket factory maps HTTP(S) to
        WS(S) while preserving host, path prefix, and per-call attach path.
    """
    normalized = base_url.rstrip("/")
    client = httpx.AsyncClient(base_url=normalized, timeout=httpx.Timeout(5.0, read=None))

    def ws_factory(path: str) -> Any:
        from websockets.asyncio.client import connect as _ws_connect

        return _ws_connect(
            _http_to_ws_url(_join_base_path(normalized, path)),
            open_timeout=10,
        )

    return client, ws_factory


def _join_base_path(base_url: str, path: str) -> str:
    """Join a base URL and absolute API path without dropping base prefixes."""
    base = base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _http_to_ws_url(url: str) -> str:
    """Convert an HTTP(S) URL to WS(S)."""
    parsed = urlparse(url)
    if parsed.scheme == "http":
        scheme = "ws"
    elif parsed.scheme == "https":
        scheme = "wss"
    else:
        raise ValueError(f"runner TCP base URL must be http(s), got {parsed.scheme!r}")
    return urlunparse(parsed._replace(scheme=scheme))


def build_uds_runner(uds_path: str) -> tuple[httpx.AsyncClient, RunnerWSFactory]:
    """Build the HTTP client + WS factory for a UDS-attached runner.

    :param uds_path: Filesystem path to the runner's Unix socket.
    :returns: ``(client, ws_factory)``. The client uses httpx's UDS
        transport; the WS factory uses ``websockets.unix_connect``
        against the same path. Both target ``http://runner`` /
        ``ws://runner`` as cosmetic base hosts because the UDS
        transport ignores the host portion.
    """
    client = httpx.AsyncClient(
        transport=httpx.AsyncHTTPTransport(uds=uds_path),
        base_url="http://runner",
        timeout=httpx.Timeout(5.0, read=None),
    )

    # Imported lazily so ``import omnigent.server`` doesn't pay the
    # websockets-library cost when the runner attach feature isn't used.
    from websockets.asyncio.client import unix_connect as _ws_unix_connect

    def ws_factory(path: str) -> Any:
        return _ws_unix_connect(
            path=uds_path,
            uri=f"ws://runner{path}",
            open_timeout=10,
        )

    return client, ws_factory
