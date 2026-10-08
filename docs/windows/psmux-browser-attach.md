# psmux browser attach fidelity

## Decision

The first Windows terminal milestone supports browser attach as a documented
capture/send bridge, not as POSIX terminal fidelity parity.

Omnigent should not describe psmux browser attach as equivalent to the POSIX
`tmux` PTY/control attach path unless `psmux` exposes a streaming/control-mode
API that preserves terminal byte streams, cursor movement, alternate screen
redraws, ANSI attributes, and low-latency interactive updates.

## Current implementation model

The current Windows attach path uses `bridge_capture_to_websocket`:

- it polls the terminal instance with `read()` roughly every 250 ms;
- it sends changed screen snapshots to the browser;
- it forwards browser input through the instance `send()` method;
- it applies resize frames through the instance `resize()` method when
  supported;
- detach closes the browser websocket without closing the psmux session;
- ended sessions close with the terminal-not-found close code so clients stop
  reconnecting.

This model is enough for simple command input/output, lifecycle validation, and
reviewable Windows terminal evidence. It is not enough to claim parity with raw
PTY/control-mode behavior.

## Fidelity ceiling

Until a psmux streaming/control API is accepted and implemented, the browser
attach path has these known limits:

- snapshot polling can miss fast intermediate redraws;
- latency is bounded by the polling interval;
- full-screen snapshot diffs are less efficient than byte-stream forwarding;
- ANSI/cursor/alternate-screen behavior depends on what `psmux read()` exposes;
- complex TUI applications may not behave like they do through POSIX tmux attach.

## Evidence required

Terminal PR evidence should include an unlocked native Windows desktop recording
or screenshots showing:

1. Omnigent web terminal attached to a psmux-backed terminal.
2. A typed command and visible output round trip, plus a raw transcript when
   xterm/canvas rendering makes DOM text assertions unreliable, for example:

   ```powershell
   Write-Output omnigent-windows-terminal-ok
   ```

3. Detach/reconnect behavior where the terminal session remains alive.
4. Ended/dead-session behavior where the browser stops treating the terminal as
   connected.
5. ANSI/cursor/TUI behavior that demonstrates either the current limitation or a
   future parity improvement.

A gated evidence capture test lives at
`tests/e2e_ui/windows/test_psmux_terminal_evidence.py`. Run it manually with
`OMNIGENT_WINDOWS_EVIDENCE=1`; it writes screenshots and transcript artifacts
under `.pi/evidence/windows-parity/` for attach, reconnect, ANSI limitation, and
ended session states. Those files are transient review artifacts: attach them to
the PR or an issue comment, but do not commit them to the source tree.

## Path to parity

If `psmux` exposes a suitable streaming/control interface, implement a dedicated
bridge that reuses the POSIX attach architecture as closely as possible. That
future bridge should preserve raw terminal output, lower latency, resize events,
input semantics, and close-code behavior before browser attach parity is claimed.
