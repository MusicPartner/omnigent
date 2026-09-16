"""Manual Windows evidence capture for psmux browser terminal attach.

Run with ``OMNIGENT_WINDOWS_EVIDENCE=1`` from native Windows. The test writes
screenshots under ``.pi/evidence/windows-parity`` and is intentionally gated so
ordinary browser E2E runs do not update evidence artifacts.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect
from websockets.sync.client import connect

from tests.e2e_ui.conftest import open_right_rail

pytestmark = pytest.mark.skipif(
    os.environ.get("OMNIGENT_WINDOWS_EVIDENCE") != "1",
    reason="set OMNIGENT_WINDOWS_EVIDENCE=1 to capture Windows evidence artifacts",
)

_USER_ZSH_KEY_RE = re.compile(r"^terminal:terminal_zsh_u-")


def _bash_quote(value: str) -> str:
    """Single-quote a value for the Git-bash-style evidence shell."""
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _capture_terminal_transcript(
    *,
    base_url: str,
    session_id: str,
    terminal_id: str,
    output_path: Path,
    commands: list[str],
    expected: list[str],
) -> None:
    """Drive the terminal attach API and persist raw snapshot transcript."""
    ws_base = base_url.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    url = (
        f"{ws_base}/v1/sessions/{quote(session_id, safe='')}/resources/terminals/"
        f"{quote(terminal_id, safe='')}/attach"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transcript = (
        output_path.read_text(encoding="utf-8", errors="replace")
        if output_path.exists()
        else ""
    )
    transcript += "\n--- attach command batch ---\n"
    with connect(url, max_size=20_000_000) as ws:
        for command in commands:
            ws.send(command.encode("utf-8"))
        if not expected:
            time.sleep(0.5)
        deadline = time.monotonic() + 15.0
        while expected and time.monotonic() < deadline and not all(
            item in transcript for item in expected
        ):
            try:
                message = ws.recv(timeout=0.75)
            except TimeoutError:
                continue
            if isinstance(message, bytes):
                transcript += message.decode("utf-8", errors="replace")
            else:
                transcript += message
    output_path.write_text(transcript, encoding="utf-8")
    missing = [item for item in expected if item not in transcript]
    if missing:
        raise AssertionError(f"terminal transcript missing {missing!r}; content={transcript!r}")


def _open_shell(page: Page) -> None:
    open_right_rail(page)
    rail = page.get_by_role("complementary", name="Workspace")
    rail.get_by_role("tab", name=re.compile("Shells")).click()
    rail.get_by_role("button", name="New shell").click()


def _connected_terminal(page: Page):
    main_terminal = page.get_by_test_id("main-terminal-view")
    expect(main_terminal).to_be_visible(timeout=60_000)
    expect(main_terminal).to_have_attribute("data-active-terminal", _USER_ZSH_KEY_RE)
    terminal_view = page.get_by_test_id("terminal-view").last
    expect(terminal_view).to_be_visible(timeout=60_000)
    expect(terminal_view).to_have_attribute("data-state", "connected", timeout=20_000)
    return main_terminal, terminal_view


def test_windows_psmux_browser_evidence(page: Page, terminal_session: tuple[str, str]) -> None:
    """Capture attach, input, reconnect, and ANSI limitation screenshots."""
    base_url, session_id = terminal_session
    evidence_dir = Path(".pi/evidence/windows-parity")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    nonce = os.environ.get("OMNIGENT_WINDOWS_EVIDENCE_NONCE", "omnigent-windows-terminal-ok")
    transcript_path = evidence_dir / "browser-psmux-terminal-transcript.txt"
    transcript_path.unlink(missing_ok=True)

    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(f"{base_url}/c/{session_id}")
    _open_shell(page)
    main_terminal, terminal_view = _connected_terminal(page)

    terminal_id = terminal_view.get_attribute("data-terminal-id")
    assert terminal_id is not None
    _capture_terminal_transcript(
        base_url=base_url,
        session_id=session_id,
        terminal_id=terminal_id,
        output_path=transcript_path,
        commands=[f"printf '%s\\n' {_bash_quote(nonce)}\n"],
        expected=[nonce],
    )
    expect(terminal_view).to_have_attribute("data-state", "connected")
    page.screenshot(path=str(evidence_dir / "browser-psmux-terminal-attach.png"), full_page=True)
    main_terminal.screenshot(path=str(evidence_dir / "browser-psmux-terminal-panel.png"))

    page.get_by_role("button", name="Close shell").click()
    expect(main_terminal).to_have_count(0)
    page.get_by_role("complementary", name="Workspace").get_by_role(
        "button", name=re.compile("zsh")
    ).first.click()
    main_terminal, terminal_view = _connected_terminal(page)
    page.screenshot(path=str(evidence_dir / "browser-psmux-terminal-reconnect.png"), full_page=True)

    _capture_terminal_transcript(
        base_url=base_url,
        session_id=session_id,
        terminal_id=terminal_id,
        output_path=transcript_path,
        commands=["printf '\\033[31mRED\\033[0m cursor-limit-check\\n'\n"],
        expected=["cursor-limit-check"],
    )
    page.screenshot(path=str(evidence_dir / "browser-psmux-terminal-ansi-limitation.png"), full_page=True)

    _capture_terminal_transcript(
        base_url=base_url,
        session_id=session_id,
        terminal_id=terminal_id,
        output_path=transcript_path,
        commands=["exit\n"],
        expected=[],
    )
    expect(terminal_view).to_have_attribute("data-state", "closed", timeout=10_000)
    expect(terminal_view).to_contain_text("terminal session ended", timeout=10_000)
    page.screenshot(path=str(evidence_dir / "browser-psmux-terminal-ended.png"), full_page=True)
