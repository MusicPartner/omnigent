# Windows integration lessons

Reviewed 2026-10-22. These are demonstrated lessons, not permanent dependency
versions or claims of support. Recheck the target's implementation.

## Historical intent and current ownership

- Recover v0.14's leaf-module, path, argv, hook, shutdown and native-env
  contracts before new extraction. Do not restore obsolete implementations.
  Original release-port records describe v0.17, not v0.19.
- Parent-environment forwarding, lifecycle tracing, centralized psmux readiness
  and current transport owners are later extensions. Map original intent and
  later contracts to the latest owner/tests separately.
- General fixes such as SSE, catalogs and shared UI are not Windows mechanics.
  Do not hide them inside platform adapters or revive upstream-covered drops.
- Retarget moved Claude/Codex test suites. Clean three-way applies can attach
  skip decorators to the wrong neighboring test; check owning symbols/markers.
- SSE readiness changes require matching heartbeat frames in browser fakes.
  New UI areas need current feature-map registration.

## Terminal preparation and mux delivery

- Preserve current factory inputs, copy-on-write parent environments, lifecycle
  correlation, status wrapping and failure cleanup. In v0.19 a clean merge left
  psmux's launch override without upstream's optional program-status wrapper.
  Characterize both backends before sharing preparation; do not duplicate policy.
- Reuse existing preparation helpers where semantics agree. For example,
  `terminal_pane_environment` already owns inherited overrides, exclusions,
  stale correlation removal, runner-secret stripping and UTF-8 locale defaults.
  Its locale behavior must be characterized before applying it to another path.
- Keep mux-specific argv, config/control mode, native executable resolution and
  Windows environment-removal wrappers in their leaves. Do not force tmux's
  multi-command argv or POSIX signal assumptions into psmux.
- Readiness predicates, caches, CLI guards and launch refusals must agree with
  actual capability; installed psmux is not unconditional support for all modes.
- Real psmux checks are serial with private `PSMUX_DATA_DIR`, owned sessions
  and `PSMUX_NO_WARM=1` when required. Never kill machine-wide process names.
- psmux 3.3.8 buffers were session-owned: untargeted `load-buffer` could follow
  another pane while targeted paste reached Claude. Target the load on Windows,
  not POSIX tmux; exercise two sessions and short/multiline/large data.
- psmux 3.4.0 custom `-S` paths namespace metadata. A guessed session `.port`
  file was wrong, not late. Capture the child's actual `TMUX` context instead
  of duplicating private hashing or adding waits.
- v0.19 Claude sends a focus-probe Space before clear-line keys. A raw reader
  records it while the editor clears it. Expect the exact prelude; do not strip
  arbitrary data to satisfy a payload check.

## Shell consumers and hooks

- Prefer executable plus literal argv for probes and cleanup. Avoid Windows
  Store `python3` aliases and nested `cmd /c` quoting for paths with spaces.
- Select quoting for the actual consumer: subprocess, cmd, PowerShell and Git
  Bash differ. Do not switch all native commands to PowerShell or add a new
  PowerShell prerequisite. Prefer native executables over corrupting npm shims.
- Exercise spaces, Unicode, quotes/JSON, multiline/metacharacters, stderr and
  exit codes. Use Windows `.CMD` frontend-tool entrypoints, not POSIX shims.
- Canonical hook settings and lifecycle gates stay with upstream's owner.
  Windows adapters transport them. Forward current readiness/hook keyword
  contracts, including newly added options in observers/stubs.
- Gateway command helpers must use their actual shell and owned-process
  cleanup. Keep missing-profile/credential refusals explicit and redacted.

## Lifecycle and isolation boundaries

- A child may ignore CTRL_BREAK. Retain PID-identity census and bounded
  escalation rather than returning after a successful signal alone.
- Interruption, Stop Session, UI resume and desktop Quit are different paths.
  Close failures must remain observable and replacement ownership preserved.
  An independent CLI must survive another instance's shutdown.
- Preserve `create_exec_launcher(...)->str`. The rejected distlib candidate
  spawned before job assignment; demonstrating its escape was not adoption
  success. The later private-job candidate was opt-in/unsigned in v0.17
  evidence. Inspect current selector/packaging before claiming defaults,
  signing or architecture support.
- Job Objects provide containment/cleanup, not filesystem or network isolation.
  Preserve brokered signer and unsupported backend refusals. POSIX permission
  checks cannot simply become a Windows ACL-only isolation claim.
- Separate fixture portability from support: private-path, Unix socket and
  POSIX mode assumptions should not prevent portable routing/lifecycle tests.
  Narrowly scope actual Unix broker cases; keep parser and Windows-refusal cases.
  Skip symlinks only for actual missing capability/privilege.
- Attachment caches require private ACLs, safe handles/junction behavior,
  reuse and cleanup. Mock cache tests do not prove vendor sandbox reads.
- Native Claude completed-output delivery is not live output streaming. Do
  not revive the previously rejected custom output-streaming tool.

## Reliable fixtures, evidence and installers

- Use write-then-rename for generated PID/readiness/result files when existence
  means completion. File creation alone exposed empty content in CI.
- Use causal barriers: a real reply proves post-refusal input recovery better
  than a cosmetic toolbar. Streaming follow-ups use keyboard queuing; clicking
  the current Interrupt action would test a different journey.
- Independent harness clients must use actual TCP/UDS endpoints and auth,
  not assume `AF_UNIX`. Keep faults/assertions visible and reuse nearby helpers.
- Completed JUnit can be authoritative when console output truncates after
  collection. A passing family is not a passing whole job; a retry pass does
  not prove the prior root cause.
- Validate installer arguments before PATH writes. The bundle installer
  rejected option-looking install paths and scoped `UV_SYSTEM_CERTS` with
  restoration/opt-out; do not disable TLS verification.
- Check all executable resolutions: old PATH entries once masked an upgrade.
  Exercise idempotent installation/uninstall in disposable prefixes, never the
  user's real PATH or installation merely to reproduce a test.
- Verify immutable source SHA, wheel/core/client/UI versions, bundled modules
  and desktop build mode. Older runs remain older-SHA evidence; explicitly
  demonstrate unchanged input closure when reusing their results.
- Respect content-policy denials and shared push budgets. Unverified manual
  command fragments and blocked worker reports are not check passes.

## Human acceptance

Start an explicitly identified artifact/checkout with isolated state and use its
printed UI URL. Back up real config/data before an upgrade; do not downgrade
against a migrated database without restoring its backup.

1. Verify executable path, version/source, local host and relevant remote host.
2. Exercise another drive, spaces/Unicode, breadcrumbs and worktrees.
3. Start fresh Claude/Codex/Copilot sessions with supported economical models;
   check trust/startup, rendering, cursor, Escape and resize as applicable.
4. With two owned panes, exercise short, multiline and large chat delivery.
5. Run native PowerShell `Start-Sleep -Seconds 30`, Stop Session, then send
   another chat message without manually opening the terminal to wake it.
6. Keep an independent CLI alive, quit the desktop and verify only owned work
   exits. Do not infer this from a turn-interruption test.
7. Verify small image/ZIP reads, Stop/resume and reuse in the actual vendor
   sandbox. State unperformed checks instead of inferring them from mocks.
