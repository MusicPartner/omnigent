"""Capture/send WebSocket bridge used by native Windows psmux terminals."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import logging
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket

from omnigent.terminals.ws_common import (
    WS_CLOSE_TERMINAL_DETACHED,
    WS_CLOSE_TERMINAL_NOT_FOUND,
)

_logger = logging.getLogger(__name__)


async def bridge_capture_to_websocket(
    websocket: WebSocket,
    *,
    instance: Any,
    read_only: bool,
    on_client_interaction: Callable[[], None] | None = None,
    poll_interval_s: float = 0.25,
) -> None:
    """Bridge a capture/send terminal backend to an accepted WebSocket."""
    if on_client_interaction is not None:
        on_client_interaction()
    last_screen = ""
    close_code = WS_CLOSE_TERMINAL_DETACHED
    close_reason = "terminal detached"

    async def _instance_alive() -> bool:
        is_alive = getattr(instance, "is_alive", None)
        if callable(is_alive):
            result = is_alive()
            if inspect.isawaitable(result):
                result = await result
            return bool(result)
        return bool(getattr(instance, "running", False))

    async def _capture_loop() -> None:
        nonlocal last_screen, close_code, close_reason
        while await _instance_alive():
            read = await instance.read()
            screen = read.get("screen", "") if isinstance(read, dict) else ""
            if screen != last_screen:
                last_screen = screen
                snapshot = "\x1b[H\x1b[2J" + screen
                await websocket.send_bytes(snapshot.encode("utf-8", errors="replace"))
            await asyncio.sleep(poll_interval_s)
        close_code = WS_CLOSE_TERMINAL_NOT_FOUND
        close_reason = "terminal session ended"

    async def _input_loop() -> None:
        nonlocal close_code, close_reason
        while True:
            msg = await websocket.receive()
            if on_client_interaction is not None:
                on_client_interaction()
            if msg.get("type") == "websocket.disconnect":
                close_code = WS_CLOSE_TERMINAL_DETACHED
                close_reason = "terminal detached"
                return
            if msg.get("text") is not None:
                try:
                    ctl = json.loads(msg["text"])
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(ctl, dict) and ctl.get("type") == "resize":
                    try:
                        cols = int(ctl["cols"])
                        rows = int(ctl["rows"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    resize = getattr(instance, "resize", None)
                    if callable(resize):
                        result = resize(cols=cols, rows=rows)
                        if inspect.isawaitable(result):
                            await result
                continue
            data = msg.get("bytes")
            if data is None or read_only:
                continue
            if not await _instance_alive():
                close_code = WS_CLOSE_TERMINAL_NOT_FOUND
                close_reason = "terminal session ended"
                return
            text = data.decode("utf-8", errors="ignore")
            if not text:
                continue
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            parts = text.split("\n")
            for index, part in enumerate(parts):
                keys = "Enter" if index < len(parts) - 1 else ""
                await instance.send(part or None, keys=keys)

    capture_task = asyncio.create_task(_capture_loop(), name="terminal-capture-to-ws")
    input_task = asyncio.create_task(_input_loop(), name="terminal-ws-to-capture")
    try:
        done, pending = await asyncio.wait(
            {capture_task, input_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for task in done:
            exc = task.exception()
            if exc is not None:
                _logger.warning("capture-attach: bridge task crashed: %r", exc)
    finally:
        if on_client_interaction is not None:
            on_client_interaction()
        with contextlib.suppress(RuntimeError):
            await websocket.close(code=close_code, reason=close_reason)
