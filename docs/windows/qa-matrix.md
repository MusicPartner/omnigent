# Windows QA matrix

This matrix defines the Windows validation contract while native Windows support
is being built incrementally. It separates automated CI signals from manual QA
so contributors know which evidence belongs in each PR.

## Support levels

| Level | Signal | Required for merge? | Purpose |
| --- | --- | --- | --- |
| Hard CI | `Windows smoke + unit` import/CLI smoke, Windows-support unit tests, and the psmux terminal backend lifecycle test | Yes | Catch native Windows regressions in cross-platform primitives and the native terminal backend. |
| Non-blocking CI | Broader `-m "not posix_only"` sweep in `.github/workflows/windows.yml` | No | Surface the next Windows parity gaps without blocking unrelated work. |
| Manual QA | PowerShell transcript and screenshots/recordings where visual | Yes for Windows feature PRs | Prove native Windows behavior that CI cannot exercise reliably yet. |
| POSIX parity | Linux/macOS/WSL full test coverage | Yes through existing CI | Keep Unix terminal/sandbox behavior unchanged. |

## Windows-safe automated coverage

Run these commands from native Windows PowerShell when validating Windows-facing
changes:

```powershell
$env:OMNIGENT_SKIP_WEB_UI = "true"
$env:UV_INDEX_URL = "https://pypi.org/simple"
$env:PIP_INDEX_URL = "https://pypi.org/simple"

uv sync --locked --extra dev
.\scripts\windows_safe_pytest.ps1 -StableOnly
uv run pytest tests/terminals/test_registry.py::test_windows_psmux_backend_launch_send_read_close -p no:cacheprovider -q
.\scripts\windows_safe_pytest.ps1 -CollectOnly
```

The dedicated psmux lifecycle test is hard CI because native terminal support
requires a real Windows multiplexer signal. Broad Windows-safe collection is
non-blocking while native bridge imports and remaining terminal coverage are
being made Windows-safe. A PR that expands Windows support should include the
broad collection output and explicitly call out any remaining collection or
execution gaps.

## POSIX-only coverage

Use Linux, macOS, or WSL2 for tests that depend on:

- `tmux`, raw PTYs, `termios`, `fcntl`, or Unix signals
- `pexpect`/`pyte` terminal rendering harnesses
- bwrap or seatbelt filesystem/network sandbox enforcement
- Unix-domain-socket-only paths or fork behavior

Those tests should be marked `posix_only` and skipped on native Windows before
importing POSIX-only modules.

## Manual QA checklist by change type

### Installer / setup changes

- Fresh native Windows checkout.
- `uv sync --locked --extra dev` succeeds from PowerShell.
- `uv run omnigent --help` succeeds.
- Attach the PowerShell transcript to the PR.

### Terminal backend or attach changes

- Start a local server and host from PowerShell.
- Create a Windows-backed terminal session.
- Attach from the web UI and prove input/output round-trips.
- Include a screenshot or screen recording showing the terminal attached in the
  browser.

### Runner / transport changes

- Prove both the preferred Windows path and the fallback/error path.
- Include logs showing which transport was selected.
- Verify error messages are actionable when the transport is unavailable.

### Sandbox / containment changes

- Document exactly which capability is supported on Windows.
- Prove fail-closed behavior for unsupported policy combinations.
- Include the command output and, if UI-visible, a screenshot of the surfaced
  error.

### Docs-only Windows changes

- Validate links and commands for syntax.
- No screenshot required; use `N/A` in the PR demo section.

## PR evidence expectations

Windows PRs should include:

1. The Windows command transcript for the relevant automated/manual checks.
2. Any screenshot or recording required by the change type.
3. The exact known gaps, especially when relying on non-blocking CI.
4. Whether POSIX parity was validated by existing CI, local Linux/macOS/WSL, or
   is not affected.

## Promotion path

1. Keep the stable smoke/unit subset required through merge-ready.
2. Keep broad native Windows coverage non-blocking while known PTY/runtime gaps
   remain.
3. Move additional Windows-safe subsets into the hard `Windows smoke + unit` job
   as each feature lands.
4. Promote the broad `-m "not posix_only"` sweep to required only after it is
   deterministic on `windows-latest` and all remaining POSIX-only tests are
   correctly marked.
