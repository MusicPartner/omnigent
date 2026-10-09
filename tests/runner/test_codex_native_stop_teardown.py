"""Ownership and cancellation regressions for Codex Stop teardown."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from omnigent.runner.native import orchestration


@pytest.fixture
def registered_server(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Give each test an isolated app-server registration."""
    server = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(orchestration, "_AUTO_CODEX_APP_SERVERS", {"session": server})
    return server


async def test_teardown_closes_server_after_forwarder_pops_registration(
    registered_server: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    cleanup_entered = asyncio.Event()
    cleanup_release = asyncio.Event()

    async def forwarder() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            orchestration._AUTO_CODEX_APP_SERVERS.pop("session")
            cleanup_entered.set()
            await cleanup_release.wait()

    task = asyncio.create_task(forwarder())
    await asyncio.sleep(0)

    async def cancel_forwarder(session_id: str) -> None:
        assert session_id == "session"
        task.cancel()
        await cleanup_entered.wait()
        assert not task.done()

    monkeypatch.setattr(orchestration, "_cancel_auto_forwarder_task", cancel_forwarder)
    try:
        await orchestration.teardown_codex_native_app_server("session")
        registered_server.close.assert_awaited_once_with()
        assert not task.done()
        assert "session" not in orchestration._AUTO_CODEX_APP_SERVERS
    finally:
        cleanup_release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_teardown_preserves_replacement_server(
    registered_server: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    replacement = SimpleNamespace(close=AsyncMock())

    async def cancel_forwarder(_session_id: str) -> None:
        orchestration._AUTO_CODEX_APP_SERVERS["session"] = replacement

    monkeypatch.setattr(orchestration, "_cancel_auto_forwarder_task", cancel_forwarder)
    await orchestration.teardown_codex_native_app_server("session")

    registered_server.close.assert_awaited_once_with()
    replacement.close.assert_not_awaited()
    assert orchestration._AUTO_CODEX_APP_SERVERS["session"] is replacement


async def test_teardown_propagates_close_failure_and_retains_registration(
    registered_server: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered_server.close.side_effect = RuntimeError("server still running")
    monkeypatch.setattr(orchestration, "_cancel_auto_forwarder_task", AsyncMock())

    with pytest.raises(RuntimeError, match="server still running"):
        await orchestration.teardown_codex_native_app_server("session")

    registered_server.close.assert_awaited_once_with()
    assert orchestration._AUTO_CODEX_APP_SERVERS["session"] is registered_server


async def test_teardown_closes_server_when_cancel_wait_is_cancelled(
    registered_server: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    cancellation_entered = asyncio.Event()

    async def cancel_forwarder(_session_id: str) -> None:
        cancellation_entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(orchestration, "_cancel_auto_forwarder_task", cancel_forwarder)
    task = asyncio.create_task(orchestration.teardown_codex_native_app_server("session"))
    try:
        await cancellation_entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        registered_server.close.assert_awaited_once_with()
        assert "session" not in orchestration._AUTO_CODEX_APP_SERVERS
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
