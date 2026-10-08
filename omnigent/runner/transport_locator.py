"""Runner transport locator abstractions.

The server talks to runners through an ``httpx.AsyncClient``. Today that client
uses the WebSocket tunnel registry; this seam keeps that decision in one place
so Windows-specific runner transports can be added without changing every
server route that forwards to a runner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

import httpx

from omnigent.runner.transports.ws_tunnel.transport import WSTunnelTransport
from omnigent.runtime import telemetry

if TYPE_CHECKING:
    from omnigent.runner.transports.ws_tunnel.registry import TunnelRegistry


class RunnerTransportLocator(Protocol):
    """Factory/cache for clients that can reach a runner."""

    def client_for_runner(self, runner_id: str) -> httpx.AsyncClient:
        """
        Return a client that routes requests to *runner_id*.

        :param runner_id: Runner UUID, e.g. ``"runner_0123456789abcdef"``.
        :returns: ``httpx.AsyncClient`` pointed at the selected runner transport.
        """

    async def aclose(self) -> None:
        """Close any cached transport clients."""


class LocalRunnerTransportLocator:
    """Runner transport locator backed by one configured local transport."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Create a locator that returns *client* for every pinned runner."""
        self._client = client

    def client_for_runner(self, runner_id: str) -> httpx.AsyncClient:
        """Return the configured local runner client for *runner_id*."""
        del runner_id
        return self._client

    async def aclose(self) -> None:
        """Close the configured local runner client."""
        await self._client.aclose()


class WSTunnelRunnerTransportLocator:
    """Default runner transport locator backed by the WebSocket tunnel registry."""

    def __init__(self, registry: object) -> None:
        """
        Create a WebSocket-tunnel transport locator.

        :param registry: ``TunnelRegistry`` instance used by
            :class:`WSTunnelTransport`. Typed as ``object`` to avoid importing the
            registry at runtime for this small seam.
        """
        self._registry = registry
        self._clients: dict[str, httpx.AsyncClient] = {}

    def client_for_runner(self, runner_id: str) -> httpx.AsyncClient:
        """Return a cached WebSocket-tunnel client for *runner_id*."""
        client = self._clients.get(runner_id)
        if client is None:
            client = httpx.AsyncClient(
                transport=WSTunnelTransport(cast("TunnelRegistry", self._registry), runner_id),
                base_url="http://runner",
                timeout=httpx.Timeout(5.0, read=None),
            )
            telemetry.instrument_httpx_client(client)
            self._clients[runner_id] = client
        return client

    async def aclose(self) -> None:
        """Close cached runner clients."""
        clients = list(self._clients.values())
        self._clients.clear()
        for client in clients:
            await client.aclose()
