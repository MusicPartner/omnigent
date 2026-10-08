# Windows native development scope

This note tracks the Windows support boundary used by contributor workflow and
incremental Windows parity work.

## Prerequisite work

- PowerShell installer and Windows setup/import fixes are tracked by the
  Windows installer workstream.
- psmux-backed terminal launch, terminal tools, and browser terminal attach are
  tracked by the Windows terminal backend workstream.

## Native Windows supported scope

Native Windows development is supported for core/server/web work that does not
require POSIX PTY behavior:

- package setup with `uv`
- core Python modules and server/API routes
- stores/spec/parser/runtime tests that avoid POSIX terminal wrappers
- SDK-harness and Job Object containment work
- psmux-backed Omnigent-managed terminals
- web lint/build/test commands under `web/`

Use this baseline command for Windows-safe Python coverage:

```powershell
uv run pytest -m "not posix_only"
```

If a broader run still discovers collection failures, mark the affected tests
`posix_only` and add a module-level Windows skip before importing POSIX-only
modules.

## POSIX-only scope

Use Linux, macOS, or WSL2 for coverage that requires:

- `pexpect` or `pyte`
- raw `pty`, `termios`, or `fcntl`
- tmux control-mode semantics
- Unix signals, fork behavior, or Unix-domain-socket-only behavior
- hard filesystem/network sandbox enforcement through bwrap or seatbelt

These tests should carry the `posix_only` marker and skip cleanly on native
Windows instead of failing during import collection.

## Pre-commit portability

Local pre-commit hooks should use `uv run ...` rather than hardcoded virtualenv
paths such as `.venv/bin/python` or `.venv\\Scripts\\python.exe`. This keeps the
same hook definitions usable from POSIX shells and native Windows PowerShell.

## Migration hazards for future main updates

- Upstream `1d0cbe7d7` already accepts drive-letter Start-session workspaces.
  **Resolved for v0.17:** upstream's `isValidWorkspace`/`isHostAbsolutePath`
  was kept and the fork's duplicate hunks were dropped; only the drive-letter
  path normalization and backslash-aware label splits were replayed on top.
- Upstream `c0df96772` deliberately disables native harness readiness on
  Windows; future psmux integration must reconcile readiness, cache keys, and
  launch support together.
  **Resolved for v0.17:** the gate is now conditional on psmux
  (`native_terminal_supported()` in `omnigent/terminals/psmux.py`), applied to
  readiness, the readiness cache key, the runner refusal payload, and the CLI
  guard together.
- Upstream changed Claude readiness, MCP ingress, process teardown, session
  lifecycle, and browser-test structure.
- Large mixed fork commits to audit by surviving hunks and merge resolutions,
  not messages: `dc48bee8d`, `de1e033f5`, `b04849152`, `d61605390`,
  `7eac00b28`, `74c37e323`.
- Future-update procedure:
  1. Choose an explicit release SHA or tag.
  2. Refresh the semantic overlap ledger.
  3. Retain upstream implementations that satisfy existing contracts.
  4. Replay only the remaining fork behavior; the leaf modules in
     `.github/FORK_MAINTENANCE.md` ("Windows isolation topic map (v0.17)") are
     the replay units.
  5. Validate platform capability and lifecycle contracts.
  6. Publish a new integration branch without rewriting the old one.

## v0.17 port deferrals

Fork changes intentionally not replayed onto v0.17.0:

- `omnigent/server/routes/hosts.py` and
  `tests/server/integration/test_hosts_worktrees.py`: the fork returns `200 []`
  for a non-git workspace; v0.17 keeps the `400` because the web client
  (`useSessionWorktrees`, `useComposerGitStatus`) relies on it to report
  `not_git`. Replay only together with a matching web-client change.
- `tests/inner/test_acp_executor.py`: two Windows `skipif` decorators
  (`test_end_to_end_against_fake_acp_agent`, `test_end_to_end_denied_permission`)
  were not replayed; both tests pass on native Windows without them.
