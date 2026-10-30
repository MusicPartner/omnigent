r"""E2E: a Claude-native web ``/login`` is rejected with actionable guidance.

Claude Code's ``/login`` and ``/logout`` require its terminal. The events API
rejects those web-composer messages with HTTP 400 ``invalid_input`` and directs
the user to ``omni setup`` on the host, before accepting transcript input.

The journey drives the real claude-native stack: an ordinary first turn proves
the composer → CLI → mock-LLM → transcript pipeline, then ``/login`` must leave
the draft in the composer, show the actionable error, and reach neither the
canonical transcript nor a model request.
"""

from __future__ import annotations

import json
import time

import httpx
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import get_mock_requests
from tests.e2e_ui.conftest import reset_mock_llm, set_fallback_mock_llm

_COMPOSER = "Send a message…"
_ASSISTANT = '[data-testid="message-bubble"][data-role="assistant"]'
_USER = '[data-testid="message-bubble"][data-role="user"]'
_WORKING = '[data-testid="working-indicator"]'

# Must match the model in the mock anthropic provider config written by the
# native_claude_mock_session fixture (conftest._CLAUDE_MOCK_MODEL).
_CLAUDE_MOCK_MODEL = "claude-sonnet-4-20250514"

# The dead-end answer an expired Claude Code login gives every turn. The
# mock LLM plays it as the fallback for all requests, exactly reproducing
# the reported session state.
_LOGIN_EXPIRED_LINE = "Login expired · Please run /login"

_AUTH_COMMAND_ERROR = (
    "Claude Code's /login and /logout commands require its terminal. "
    "Run omni setup on the host to sign in or out, then retry."
)

# claude-native auto-launch + first-run pre-accept + first mock turn.
_FIRST_TURN_TIMEOUT_MS = 180_000

# Bound the no-forwarding check after the server rejects /login.
_LOGIN_TURN_WATCH_S = 90.0


def _send(page: Page, text: str) -> None:
    """Type *text* into the web composer and click Send.

    :param page: The Playwright page, on the session's chat surface.
    :param text: The message body to send.
    """
    composer = page.get_by_placeholder(_COMPOSER)
    expect(composer).to_be_visible(timeout=30_000)
    composer.fill(text)
    page.get_by_role("button", name="Send", exact=True).click()


def _ensure_chat_view(page: Page) -> None:
    """Switch the terminal-first native session to its chat bubble view.

    :param page: The Playwright page, on the session's chat surface.
    """
    toggle = page.get_by_test_id("view-mode-toggle")
    expect(toggle).to_be_visible(timeout=_FIRST_TURN_TIMEOUT_MS)
    segment = page.get_by_test_id("view-mode-chat")
    expect(segment).to_be_enabled(timeout=30_000)
    segment.click()


def _user_item_texts(base_url: str, session_id: str) -> list[str]:
    """Return the canonical transcript's user-message texts, in order.

    Reads ``GET /v1/sessions/{id}/items`` — the same API both the SPA chat
    view and the TUI-parity forwarder render from — so an assertion here is
    an assertion about what the session actually recorded, not about a
    transient DOM state.

    :param base_url: Spawned server base URL.
    :param session_id: The session/conversation id.
    :returns: Each user message item's concatenated text.
    """
    resp = httpx.get(
        f"{base_url}/v1/sessions/{session_id}/items",
        params={"limit": 100, "order": "asc"},
        timeout=15.0,
    )
    resp.raise_for_status()
    texts: list[str] = []
    for item in resp.json().get("data", []):
        if item.get("type") != "message" or item.get("role") != "user":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        texts.append(
            " ".join(
                block["text"]
                for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            )
        )
    return texts


def _captured_request_user_texts(mock_url: str) -> list[str]:
    """Serialize Anthropic user-message content from captured mock requests.

    :param mock_url: Mock LLM server base URL.
    :returns: JSON-serialized content for each Anthropic user message.
    """
    return [
        json.dumps(message.get("content"))
        for request in get_mock_requests(mock_url)
        for message in request.get("messages", [])
        if isinstance(message, dict) and message.get("role") == "user"
    ]


@pytest.mark.nightly
@pytest.mark.timeout(600)
def test_login_slash_is_not_silently_spent_on_the_model(
    page: Page,
    native_claude_mock_session: tuple[str, str],
    mock_llm_server_url: str,
) -> None:
    """The web composer retains a rejected ``/login`` with terminal guidance.

    The first mock-backed turn proves the native chat pipeline is live. The
    next composer submission must receive the server's 400 rejection, preserve
    its draft, display the actionable reason, and never reach transcript/model
    user input.

    :param page: Playwright page (fresh context per test).
    :param native_claude_mock_session: ``(base_url, session_id)`` on the
        real claude-native wrapper, backed by the mock LLM.
    :param mock_llm_server_url: The mock LLM server base URL.
    """
    base_url, session_id = native_claude_mock_session

    # Every model call answers with the expired-login line — the exact
    # session state the report describes. Fallbacks survive /mock/reset,
    # so Claude's background requests can't drain them.
    set_fallback_mock_llm(mock_llm_server_url, "default", _LOGIN_EXPIRED_LINE)
    set_fallback_mock_llm(mock_llm_server_url, _CLAUDE_MOCK_MODEL, _LOGIN_EXPIRED_LINE)

    page.goto(f"{base_url}/c/{session_id}")
    _ensure_chat_view(page)

    # Turn 1 — any ordinary message comes back as the dead-end line. This
    # both reproduces the reported state and proves the composer → bridge →
    # CLI → mock-LLM → transcript pipeline is live before /login is judged.
    _send(page, "hello, are you there?")
    expect(page.locator(_ASSISTANT, has_text=_LOGIN_EXPIRED_LINE).first).to_be_visible(
        timeout=_FIRST_TURN_TIMEOUT_MS
    )
    expect(page.locator(_WORKING)).to_have_count(0, timeout=60_000)

    # Clear the capture log so the /login verdict below scans only traffic
    # from the /login turn onward (set_fallback survives this reset).
    reset_mock_llm(mock_llm_server_url)

    # Let Claude Code finish turn 1 entirely before checking the rejected send.
    time.sleep(15.0)

    # Turn 2 — the server rejects this web-only auth command before acceptance.
    with page.expect_response(
        lambda response: (
            response.url.endswith(f"/v1/sessions/{session_id}/events")
            and response.request.method == "POST"
        ),
        timeout=60_000,
    ) as login_response_info:
        _send(page, "/login")
    login_response = login_response_info.value
    assert login_response.status == 400
    response_error = login_response.json()["error"]
    assert response_error["code"] == "invalid_input"
    assert response_error["message"] == _AUTH_COMMAND_ERROR

    # The existing failed-send flow restores the unsent draft and surfaces the
    # server's actionable message in the error pill.
    composer = page.get_by_placeholder(_COMPOSER)
    expect(composer).to_have_value("/login", timeout=15_000)
    expect(page.locator(_USER, has_text="/login")).to_have_count(0)
    error_pill = page.get_by_test_id("error-pill")
    expect(error_pill).to_be_visible(timeout=15_000)
    error_pill.locator('button[aria-expanded="false"]').click()
    expect(error_pill.get_by_test_id("error-message-content")).to_contain_text(_AUTH_COMMAND_ERROR)

    # Rejection must remain a no-forward guarantee: neither canonical nor
    # escaped command text may appear in user transcript/model content.
    deadline = time.monotonic() + _LOGIN_TURN_WATCH_S
    while time.monotonic() < deadline:
        transcript_login = [
            text for text in _user_item_texts(base_url, session_id) if "/login" in text
        ]
        model_login = [
            text for text in _captured_request_user_texts(mock_llm_server_url) if "/login" in text
        ]
        if transcript_login or model_login:
            pytest.fail(
                "the server-rejected /login reached user input: "
                f"transcript={transcript_login!r}, model={model_login!r}"
            )
        time.sleep(2.0)
