"""Tests for the UDS runner-transport builder used by server startup."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from omnigent.server import _runner_transport as rt


def test_build_uds_runner_returns_uds_client(tmp_path: Any) -> None:
    """The HTTP client is wired to the cosmetic ``http://runner`` base URL."""
    sock_path = str(tmp_path / "runner.sock")
    client, _factory = rt.build_uds_runner(sock_path)
    try:
        assert isinstance(client._transport, httpx.AsyncHTTPTransport)
        assert client.base_url == httpx.URL("http://runner")
    finally:
        # We never open a connection in this test; clearing the
        # transport internals avoids unclosed-client warnings without
        # needing an async fixture just for bookkeeping.
        client._transport.__dict__.clear()


def test_build_uds_runner_ws_factory_uses_unix_connect(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The WS factory invokes ``websockets.unix_connect`` with the UDS path."""
    sock_path = str(tmp_path / "runner.sock")
    captured: dict[str, Any] = {}

    def fake_unix_connect(
        path: str | None = None,
        uri: str | None = None,
        **kwargs: Any,
    ) -> Any:
        captured["path"] = path
        captured["uri"] = uri
        captured["kwargs"] = kwargs
        return "FAKE_CM"

    monkeypatch.setattr(
        "websockets.asyncio.client.unix_connect",
        fake_unix_connect,
    )

    _client, factory = rt.build_uds_runner(sock_path)
    result = factory(
        "/v1/sessions/conv_abc/resources/terminals/terminal_bash_s1/attach?read_only=false"
    )

    assert result == "FAKE_CM"
    assert captured["path"] == sock_path
    assert captured["uri"] == (
        "ws://runner/v1/sessions/conv_abc/resources/terminals/"
        "terminal_bash_s1/attach?read_only=false"
    )
    assert captured["kwargs"].get("open_timeout") == 10


def test_build_tcp_runner_returns_tcp_client() -> None:
    """The TCP client targets the configured loopback runner URL."""
    client, _factory = rt.build_tcp_runner("http://127.0.0.1:9876")
    try:
        assert client.base_url == httpx.URL("http://127.0.0.1:9876")
    finally:
        client._transport.__dict__.clear()


def test_build_tcp_runner_ws_factory_uses_websocket_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """The TCP WS factory maps http(s) base URLs to ws(s) attach URLs."""
    captured: dict[str, Any] = {}

    def fake_connect(uri: str, **kwargs: Any) -> Any:
        captured["uri"] = uri
        captured["kwargs"] = kwargs
        return "FAKE_TCP_CM"

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_connect)

    _client, factory = rt.build_tcp_runner("https://runner.example/base")
    result = factory("/v1/sessions/conv_abc/resources/terminals/t1/attach?read_only=false")

    assert result == "FAKE_TCP_CM"
    assert captured["uri"] == (
        "wss://runner.example/base/v1/sessions/conv_abc/resources/terminals/"
        "t1/attach?read_only=false"
    )
    assert captured["kwargs"].get("open_timeout") == 10


def test_build_runner_transport_prefers_tcp_over_uds(tmp_path: Any) -> None:
    """A configured TCP URL wins over UDS and works on every platform."""
    client, _factory = rt.build_runner_transport(
        uds_path=str(tmp_path / "runner.sock"),
        tcp_base_url="http://127.0.0.1:9999",
    )
    try:
        assert client.base_url == httpx.URL("http://127.0.0.1:9999")
    finally:
        client._transport.__dict__.clear()


def test_build_runner_transport_rejects_windows_uds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Native Windows gets an actionable TCP fallback hint for UDS-only config."""
    monkeypatch.setattr(rt.os, "name", "nt")

    with pytest.raises(RuntimeError, match="TCP runner base URL"):
        rt.build_runner_transport(uds_path="runner.sock")


def test_build_runner_transport_requires_a_transport() -> None:
    """Missing transport config fails loud instead of guessing."""
    with pytest.raises(RuntimeError, match="provide tcp_base_url or uds_path"):
        rt.build_runner_transport()


def test_build_runner_transport_from_env_prefers_tcp(tmp_path: Any) -> None:
    """Runtime env selection prefers cross-platform TCP over POSIX UDS."""
    client, _factory, selected = rt.build_runner_transport_from_env(
        {
            rt.RUNNER_TCP_BASE_URL_ENV: " http://127.0.0.1:7777 ",
            rt.RUNNER_UDS_PATH_ENV: str(tmp_path / "runner.sock"),
        }
    )
    try:
        assert client.base_url == httpx.URL("http://127.0.0.1:7777")
        assert selected == "tcp"
    finally:
        client._transport.__dict__.clear()


def test_runner_transport_env_configured_ignores_blank_values() -> None:
    """Blank env values are treated as missing config."""
    assert not rt.runner_transport_env_configured(
        {
            rt.RUNNER_TCP_BASE_URL_ENV: "  ",
            rt.RUNNER_UDS_PATH_ENV: "",
        }
    )


def test_build_runner_transport_from_env_rejects_blank_config() -> None:
    """Blank env values are treated as missing config and fail loud."""
    with pytest.raises(RuntimeError, match="provide tcp_base_url or uds_path"):
        rt.build_runner_transport_from_env(
            {
                rt.RUNNER_TCP_BASE_URL_ENV: "  ",
                rt.RUNNER_UDS_PATH_ENV: "",
            }
        )


def test_build_runner_transport_from_env_windows_uds_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows UDS-only env config points operators at TCP."""
    monkeypatch.setattr(rt.os, "name", "nt")

    with pytest.raises(RuntimeError, match="TCP runner base URL"):
        rt.build_runner_transport_from_env({rt.RUNNER_UDS_PATH_ENV: "runner.sock"})
