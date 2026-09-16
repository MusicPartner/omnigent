# ADR: First-class native Windows support boundary

## Status

Proposed for the Windows enablement PR sequence.

## Context

Omnigent currently has strong POSIX assumptions in terminal management,
sandboxing, test execution, and installer/developer workflows. The Windows
parity work should make native Windows a first-class supported platform without
trying to reproduce every Linux/macOS behavior in the first milestone.

This decision captures the product and engineering boundary for a first
Windows enablement wave. It is intentionally scoped: the platform should feel
supported and reliable for agreed workflows, while unsupported security or
terminal-fidelity behaviors remain explicit rather than implied.

The current goal is to support native Windows for:

- installation and setup;
- server/host/runner/web operation;
- core spec/store/session behavior;
- Windows-safe test/developer workflows;
- Omnigent-managed terminal lifecycle through `psmux`;
- explicit sandbox capability disclosure and fail-closed validation.

The goal is not to claim complete POSIX parity where Windows behavior is not yet
equivalent.

## Windows documentation map

Detailed operational and design material lives under `docs/windows/` so this
ADR can stay readable as the top-level decision record:

- [`docs/windows/qa-matrix.md`](windows/qa-matrix.md) defines hard CI,
  non-blocking CI, manual QA, and PR evidence expectations.
- [`docs/windows/test-execution.md`](windows/test-execution.md) documents the
  native PowerShell test helper and the stable/broad Windows test split.
- [`docs/windows/e2e-evidence.md`](windows/e2e-evidence.md) describes the
  evidence package expected for end-to-end Windows validation.
- [`docs/windows/sandbox-egress.md`](windows/sandbox-egress.md) records the
  current Windows sandbox and egress capability boundary.
- [`docs/windows/sandbox-isolation-design.md`](windows/sandbox-isolation-design.md)
  compares future Windows isolation options such as AppContainer, restricted
  tokens, WFP/firewall policy, proxy enforcement, and VM/container isolation.
- [`docs/windows/upstream-related-work.md`](windows/upstream-related-work.md)
  tracks adjacent upstream workstreams that affect Windows enablement.

## Decision

Omnigent will define first-class native Windows support as a bounded support
contract:

1. Native Windows is first-class for installer, server/host/runner/web,
   core workflow execution, Windows-safe developer/test workflows, and
   Omnigent-managed terminal lifecycle through `psmux`.
2. Windows sandbox support is process-containment-only in the first phase.
   Windows Job Objects do not provide filesystem/network isolation equivalent
   to Linux `bwrap` or macOS `seatbelt`. Unsupported filesystem/network and
   egress policy combinations must fail closed.
3. Browser attach for `psmux` terminals may ship only with an explicit fidelity
   boundary. The current capture/polling attach path is useful but is not a
   POSIX PTY/control-mode equivalent.
4. The WebSocket tunnel remains the default runner transport. Explicit local
   TCP/UDS runner transport is deferred from the first Windows enablement wave
   unless maintainers request it.
5. Evidence must be capability-specific, fresh, and trustworthy. Visual evidence
   must show the real Omnigent application or terminal on an unlocked Windows
   desktop, with a live typed value such as a nonce or timestamp.

## Support statement

After this enablement wave, the intended statement is:

> Omnigent supports native Windows as a first-class platform for installation,
> server/host/runner/web usage, core workflow execution, Windows-safe developer
> and test workflows, process-containment-only sandbox boundaries with
> fail-closed unsupported policies, and Omnigent-managed terminals through
> `psmux`, with documented limitations where Windows cannot yet match POSIX
> behavior.

## Non-goals for this phase

- Full filesystem/network sandbox isolation parity with Linux/macOS.
- A new Windows isolation backend such as AppContainer, WFP/firewall rules,
  restricted tokens, proxy-only enforcement, VM/container isolation, or similar.
- POSIX-only test and terminal surfaces on native Windows, including raw PTYs,
  `termios`, `fcntl`, fork behavior, `pexpect`, and tmux-specific tests.
- A psmux streaming/control-mode browser attach bridge unless maintainers make
  that a prerequisite.
- Making local TCP/UDS runner transport part of the Windows support claim.

## Alternatives considered

### Alternative A: Full parity before calling Windows first-class

Require native Windows to match Linux/macOS across terminals, sandboxing,
network egress, CI, installer behavior, and browser terminal fidelity before
using first-class language.

Benefits:

- Strongest possible parity claim.
- Avoids support ambiguity.
- Reduces risk of users encountering lower-fidelity Windows behavior.

Costs and risks:

- Too large for a practical first milestone.
- Requires unresolved security architecture decisions for Windows sandboxing.
- Likely blocks useful Windows support behind hard problems such as filesystem
  and network isolation.
- Delays installer, developer workflow, and basic terminal support that can be
  useful now.

Decision: rejected. This boils the ocean and is not necessary for an honest
first-class Windows support boundary.

### Alternative B: Treat Windows as experimental until every gap is solved

Keep all Windows work labeled experimental and avoid first-class language until
sandbox, terminal browser fidelity, and CI are all fully equivalent.

Benefits:

- Low commitment.
- Avoids accidental overpromise.
- Keeps maintainers free to reject Windows-specific dependencies later.

Costs and risks:

- Undervalues already useful native Windows behavior.
- Gives contributors no stable target for supported Windows workflows.
- Encourages ad hoc fixes rather than a coherent support contract.

Decision: rejected. Windows can be first-class for a clearly bounded set of
capabilities while explicitly documenting non-goals.

### Alternative C: First-class bounded support with explicit limitations

Define the capabilities that are supported now, fail closed for unsupported
security policies, and document fidelity limits where Windows differs.

Benefits:

- Useful to Windows users immediately.
- Honest about limitations.
- Small enough for maintainers to review in focused PRs.
- Preserves POSIX behavior.
- Provides a stable roadmap for future deeper parity work.

Costs and risks:

- Requires careful wording to avoid implying full POSIX parity.
- Requires strong evidence discipline.
- Some users may expect browser terminal fidelity beyond the current psmux
  capture/polling bridge.

Decision: accepted.

## Major architecture choices

### Terminal backend dependency

Options considered:

1. Require WSL for Omnigent-managed terminals.
2. Use `psmux` as a native Windows tmux-like backend.
3. Disable Omnigent-managed terminals on native Windows.

Choice: use `psmux`, pending maintainer approval of the dependency.

Tradeoffs:

- WSL is robust for POSIX behavior but is not native Windows support.
- Disabling terminals avoids complexity but leaves a major Omnigent capability
  unavailable.
- `psmux` gives a plausible native backend with acceptable launch/read/send/close
  lifecycle behavior, but it introduces a Windows dependency and browser attach
  fidelity questions.

Implementation consequence:

- Keep POSIX `tmux` behavior unchanged.
- Add `psmux` backend selection only on native Windows.
- Make missing `psmux` diagnostics actionable.
- Add native Windows CI coverage for a real psmux lifecycle test.

### Browser attach fidelity

Options considered:

1. Build a psmux streaming/control-mode bridge before shipping terminal support.
2. Ship capture/polling attach as full parity.
3. Ship capture/polling attach as a documented reduced-fidelity limitation.
4. Exclude browser attach from the first Windows terminal support claim.

Choice: document capture/polling as reduced fidelity unless maintainers require
streaming/control-mode parity before merge.

Tradeoffs:

- A streaming/control-mode bridge would be closer to POSIX behavior, but it is
  unbounded unless psmux exposes a suitable protocol.
- Claiming full parity would be misleading because the current bridge polls
  screen snapshots, strips ANSI, and forwards input through send operations.
- Excluding browser attach entirely is conservative but may undercut a valuable
  workflow.
- Documented reduced fidelity lets the feature be useful while preserving
  honesty.

Implementation consequence:

- Do not claim browser attach parity in PRs.
- Evidence must demonstrate both simple command round-trip and the fidelity
  ceiling with colored/cursor/TUI-like output.
- Track the final fidelity decision separately before presenting browser attach
  as complete.

### Sandbox and egress

Options considered:

1. Implement AppContainer/restricted-token/WFP/firewall/proxy isolation now.
2. Treat Job Objects as equivalent to POSIX sandboxing.
3. Provide process-containment-only support and fail closed for unsupported
   stronger policies.

Choice: process-containment-only support with fail-closed unsupported policies.

Tradeoffs:

- Building a stronger backend now requires maintainer threat-model decisions and
  Windows security design work.
- Treating Job Objects as equivalent would be unsafe and misleading.
- Process containment plus fail-closed validation is useful and honest, but it
  must be documented clearly.

Implementation consequence:

- `windows_jobobject` remains process-containment-only.
- Filesystem/network isolation and egress enforcement are unsupported unless a
  future backend is approved.
- Parser, validator, docs, and tests must share one capability source of truth.

### Runner transport

Options considered:

1. Make local TCP/UDS runner transport part of the first Windows support wave.
2. Keep the WebSocket tunnel as the canonical default and defer local transport.
3. Remove local TCP/UDS transport scaffolding entirely.

Choice: keep WebSocket tunnel as the first-class default and defer local TCP/UDS
from the initial support claim.

Tradeoffs:

- Local TCP is Windows-safe and useful as an explicit operator/developer mode.
- It is not required for normal Windows support because the existing WebSocket
  tunnel is already cross-platform.
- Including it in the first wave increases review scope and config-surface
  debate.

Implementation consequence:

- Do not block Windows support on local runner transport.
- If kept, present it later as an opt-in operator/developer escape hatch.

### Installer timing

Options considered:

1. Ship installer first.
2. Ship installer after terminal and sandbox boundaries are accepted.
3. Defer installer until every Windows capability is complete.

Choice: ship installer after capability boundaries are accepted.

Tradeoffs:

- Installer first improves onboarding, but risks promising capabilities that are
  still unsettled.
- Waiting for every capability delays basic Windows usability.
- Shipping after terminal/sandbox boundaries lets the installer be accurate and
  useful.

Implementation consequence:

- `psmux` should remain optional/detected until terminal support is accepted.
- Release-pinned and preview/from-source modes should be distinct.
- Re-runs must be idempotent and diagnostic.

## Evidence strategy

Evidence is part of the architecture. The support claim is not credible without
fresh, capability-specific validation.

Rules:

1. One evidence set per PR.
2. No copy-pasted shared transcript bundle across unrelated PRs.
3. CLI/test work uses native Windows PowerShell transcripts.
4. Browser/UI behavior requires screenshot or recording from an unlocked Windows
   desktop.
5. Visual evidence must include a live typed value such as a nonce, timestamp,
   or command unique to that run.
6. Local filesystem paths are not evidence unless artifacts are published in a
   reviewer-accessible location.
7. Known gaps must be stated in the PR body.

Terminal evidence quality bar:

- Start Omnigent server/host on native Windows.
- Create an Omnigent-managed psmux terminal.
- Attach from the web UI.
- Type a unique command.
- Show output round-trip.
- Show at least one ANSI/cursor/TUI-like example to demonstrate or disprove the
  known fidelity limitation.

## PR sequence

### PR 1: Windows QA and native developer workflow

Issues: `#6` and `#2`.

Contains:

- Windows QA/evidence matrix.
- Native Windows setup/test workflow docs.
- POSIX-only marking strategy.
- Windows-safe stable test commands.

Does not contain:

- psmux implementation.
- sandbox behavior changes.
- installer behavior changes.

Purpose:

- Establish the review and evidence contract before feature code.

### PR 2: psmux backend lifecycle and CI

Issue: `#1`.

Contains:

- psmux terminal backend selection.
- Missing binary diagnostics.
- launch/read/send/close lifecycle.
- Native Windows CI lifecycle test.
- Explicit browser attach fidelity limitation.

Does not contain:

- claim of browser attach parity.
- new psmux streaming/control bridge.

Purpose:

- Establish useful native Windows Omnigent-managed terminal support with an
  honest limitation.

### PR 3: Windows sandbox capability model and fail-closed validation

Issues: `#3` and `#17`.

Contains:

- Shared capability source of truth.
- Parser/validator use of shared capabilities.
- Fail-closed checks for unsupported Windows network/egress policy combinations.
- Tests and docs.

Does not contain:

- AppContainer/WFP/restricted-token implementation.
- Claim of filesystem/network isolation parity.

Purpose:

- Make Windows security boundaries clear and enforceable.

### PR 4: Windows installer

Issue: `#4`.

Contains:

- PowerShell installer.
- Dependency checks.
- Optional psmux detection.
- Idempotent rerun behavior.
- Release-pinned vs preview/from-source guidance.

Does not contain:

- unsupported capability promises.

### Deferred PR: local runner transport

Issue: `#5`.

Only open if maintainers approve explicit local TCP/UDS runner transport as an
upstream feature.

## Maintainer decisions required

1. Is `psmux` acceptable as a Windows dependency?
2. Is documented reduced-fidelity browser attach acceptable for first-class
   Windows terminal support, or must terminal support remain experimental until
   streaming/control parity exists?
3. Is process-containment-only sandbox support plus fail-closed unsupported
   policies an acceptable first-class Windows security boundary?
4. Should the first upstream PR be QA/developer workflow only?
5. Should local TCP/UDS runner transport be deferred from the first Windows wave?

## Consequences

Positive consequences:

- Windows support becomes useful without waiting for every parity gap.
- Maintainers can review small, coherent PRs.
- The project avoids misleading security or terminal fidelity claims.
- POSIX behavior remains the reference path and should not regress.

Negative consequences:

- Windows browser terminal attach may be lower fidelity than POSIX in the first
  phase.
- Some sandbox policies remain unsupported on Windows.
- The installer must avoid promising terminal/sandbox capabilities before those
  boundaries are accepted.
- Runner local transport work may be deferred even though some implementation
  already exists on the fork.

## Follow-up work

- Investigate whether `psmux` exposes a streaming/control protocol suitable for
  a future browser attach bridge.
- Evaluate Windows isolation backends after maintainers choose a threat model.
- Promote additional Windows-safe tests into hard CI only after they are
  deterministic.
- Revisit local runner transport if maintainers or operators need a direct
  transport mode.
