# Windows isolation after v0.19

Date: 2026-10-22. Status: packages 1 and 2 authorized; implementation in progress.

## Scope and baseline

The user authorized continuing Phase 0, package 1 and package 2 in a separate
maintenance worktree. The validated release branch and its documentation edits
remain intact. Branch `windows-parity/v0.19-isolation-p1-p2` starts at the exact
baseline below; existing skill/plan documents were copied into it.

The previous release integration's four-round allowance remains exhausted.
The user separately authorized one maintenance-branch push and validation round,
with confirmation required before any retry. That permission does not include
main or validated-release-branch changes.

Local Python executables remain policy-restricted. Package 1 is preserved as a
test-only commit. In the single authorized CI round, Windows and Linux first
run those contracts against the unchanged baseline implementation, then run
them against the package 2 candidate. Package 2 is not accepted as validated
unless both stages and the applicable release checks pass.

Use validated Windows source `6a7c711308587a2c39dd916c0820af71debfbb67`, not
the editor's v0.14 checkout, for any later authorized maintenance branch.
Its upstream base is exact v0.19.0
`d43340fec4e7d2d767f319d715e84aa82f4d1bc8`; original Windows source was
`f50a1f1cdcbc2c01499a09c8c932c9f7348b8a42`.

The [release record](RELEASE-INTEGRATION-0.19.md) and
[317-row ledger](RELEASE-INTEGRATION-0.19-ledger.csv) retain scope and limits.
[Final release validation](https://github.com/MusicPartner/omnigent/actions/runs/39674542910)
and [lint](https://github.com/MusicPartner/omnigent/actions/runs/39674541787)
passed at the exact final SHA. Backend E2E, UI/Browser Contract, integration
and Docker passed at `008949b15`; their relevant inputs were unchanged later.
The 46 review/live-acceptance notes are not erased by automated success.

Goal: reduce duplicated semantics and upstream-owned conflict surface, not
simply create more Windows files. Preserve the working release as the baseline.

## Phase 0: recover original contracts before extraction

**Yes, v0.14 history is relevant.** Review original intent once, then map it
to current owners. Do not replay/backport it or relabel historical gaps as
current failures. Original isolation source:
`ca0088b9c8e72a71b11b17d9b71898b703e56b4e`.

The targeted review used the original maintenance map and the sibling archive
`_evidence/HANDOVER-windows-parity.md`. Its extraction commit list gives:

| Original contract and history | Current owner | Package acceptance |
| --- | --- | --- |
| psmux leaf/backend, `d28450b89` | [backend](../../omnigent/terminals/backend.py), [psmux](../../omnigent/terminals/psmux.py), [registry](../../omnigent/terminals/registry.py) | P1 keeps interface/re-export identity and backend injection; P2 shares preparation, not mux command protocols |
| Paths/breadcrumbs, `3c460fb34`; host/probe, `83bb2d870` | [host paths](../../web/src/shell/hostPaths.ts), [breadcrumbs](../../web/src/shell/workspaceBreadcrumbs.ts), [listing](../../omnigent/host/host_listing.py), [probe](../../omnigent/runner/python_probe.py) | Preserve space/Unicode/drive/argv cases; no new extraction unless the launch change touches them |
| Platform command splitting, `e8b442a7a` | [shell helpers](../../omnigent/native/shell.py) | P1 preserves literal arguments and consumer-specific quoting; P2 does not globally replace shells |
| Native Codex resolution, `5a09bf943` | [Codex Windows leaf](../../omnigent/inner/codex_windows.py) | Preserve native executable resolution; do not fold it into a generic platform-policy module |
| Claude Windows hooks, `6057704ce` | [Windows hooks](../../omnigent/harnesses/claude_native/windows_hooks.py), [canonical bridge](../../omnigent/harnesses/claude_native/bridge.py) | Preserve current settings/keyword transport; no duplicate readiness or lifecycle policy |
| Shutdown/native environment, `a68442657` | [process helpers](../../omnigent/inner/_proc.py), [Windows shutdown](../../omnigent/inner/_windows_shutdown.py), [native environment](../../omnigent/runner/native/windows_env.py) | Preserve environment exclusion and owned-process identity/cleanup; P2 must not alter interruption/Stop/Quit semantics |
| Process containment is not isolation | [capabilities](../../omnigent/inner/sandbox_capabilities.py), [sandbox design](sandbox-isolation-design.md) | Both packages preserve unsupported credential, Git SSH, filesystem and network isolation refusals |

The original `_evidence/release-port` ledger and replay SHAs describe v0.17,
not v0.19. Parent-environment forwarding, lifecycle tracing, centralized
capability predicates, current resource routes and program-status wrapping
are later extensions that must also survive. General fixes such as SSE,
catalogs and shared UI are separate from Windows mechanics.

All seven extraction refs above resolve with their recorded topic subjects.
The v0.14 isolation HEAD is not an ancestor of the v0.17 Windows source; its
intent was carried through semantic replay, not direct ancestry. Treat the
mapping as behavior/provenance evidence, not a reason to merge that old branch.

Do not reopen v0.14's completed patches or deferred general work. Historical
design options are not approval for a new sandbox or experimental launcher.

## Package 1: contract tests and reusable primitives

**Dependency:** phase-0 owner/contract mapping. Production behavior remains
unchanged. Read [test placement](../../tests/README.md) and
[primitive catalog](../../tests/_helpers/README.md) before adding setup.

### 1A. Characterize the terminal/backend boundary

Extend the nearest scenarios in
[registry tests](../../tests/terminals/test_registry.py),
[psmux tests](../../tests/terminals/test_windows_psmux.py) and
[terminal tests](../../tests/inner/test_terminal.py):

- Parameterize the existing backend protocol/factory injection, not a new
  plugin system or removed `registry.create_terminal_instance` monkeypatch.
- Verify parent environment, cwd/sandbox overrides and conversation link
  forwarding. Preserve copy-on-write identity, not only equal values.
- Verify status application assignment, lifecycle transfer/identity reset,
  liveness validation and cleanup of unregistered/failed launches.
- Preserve exact errors, closed-state/idempotence and replacement ownership.
- Retain the current four-case status-wrapper/environment-removal matrix.

Keep backend identity/re-export compatibility. A genuinely superseded private
test patch point is not a reason to recreate a production re-export.

### 1B. Reuse mechanics, leave assertions with the test

- Reuse [polling primitives](../../tests/_helpers/polling.py) for observed
  conditions rather than increasing sleeps. Generated PID/readiness/result
  fixtures publish complete files atomically; factor only if multiple actual
  consumers benefit.
- Keep the existing runtime side-client helper in
  [scaffold tests](../../tests/runtime/harnesses/test_scaffold.py) local unless
  another real consumer needs it. Preserve live TCP/UDS endpoint, auth headers,
  independent transport and client cleanup. Document existing internal-entry
  coupling instead of adding a product API just for a test.
- Capture actual child TMUX context, not psmux metadata filenames. Keep
  short/Unicode-multiline/large cross-session payload and cleanup assertions.
- Preserve queued-composer keyboard submission, actual post-refusal reply
  barriers and transcript capture; do not create a UI helper that hides state
  or turns Interrupt into Send.
- Preserve POSIX parser namespace semantics, native-host path diagnostics,
  early auth refusals and narrowly scoped capability skips.

### Acceptance

Collect normalized test names, parameter IDs, markers and fixtures before/after.
The existing 349 fork-added named-test inventory is a preservation aid, not
runtime proof. No unexplained lost scenario, marker move, weaker assertion or
new Windows skip is allowed. Include negative cases with deliberately incomplete
test doubles so missing contract inputs, status wrappers, auth headers,
exclusions or cleanup calls cannot produce a success-shaped result.

Run the focused suites with retries disabled, then affected fixture consumers.
Real psmux remains serial with private state. Cross-platform matrices stay at
the lowest reliable layer; retain existing E2E for process/browser boundaries.

## Package 2: share terminal launch preparation

**Dependency:** package 1 passes on Windows and POSIX. Keep the existing
`TerminalInstance.launch(cwd=...)`, factory results and backend tuple contracts.
Do not introduce a configurable launch-plan framework.

### 2A. Reuse environment preparation

[TerminalInstance](../../omnigent/inner/terminal.py) already calls
`terminal_pane_environment`; the psmux override duplicates much of its work.
Prefer reusing that helper over adding another module with the same policy.
Characterize first:

1. Inheritance, explicit overrides and exclusions in the existing order.
2. Removal of inherited control-socket and lifecycle identities.
3. Runner-secret removal after overrides.
4. Current launch correlation and failure behavior.
5. UTF-8 locale defaults: the existing helper already skips normalization on
   Windows. Package 1 freezes explicit non-UTF-8 Windows values for both launch
   paths, and retains the separate POSIX locale tests. Reuse does not add a new
   locale option or change the Windows guard.

If semantics differ intentionally, make that small platform leaf adjustment
explicit with a test; otherwise gate the behavior change or stop for a design
decision. Never silently ignore unsupported settings.

### 2B. Share optional program-status wrapping

Both launch paths currently build the same `ProgramStatusReader`/wrapper argv.
Extract a small preparation method/helper near its existing owning code and
call it from both paths. Prefer an existing owner extension to a new package.
Its exact name is an implementation decision after characterization.

Preserve stale status-file removal, reader assignment, exact argv and error
propagation. Keep wrapper order: command/native resolution and existing
sandbox wrapping where supported, shared status wrapper, then psmux's
environment-removal shim. Do not pass POSIX sandbox launch behavior into psmux
or enable unsupported Windows containment/isolation modes.

### 2C. Keep transport-specific launch separate

Do not collapse the whole tmux/psmux launch functions just to remove lines.
Keep psmux native argv, config-file remain-on-exit, resize/capture behavior
and native CLI resolution separate from tmux command sequencing, control
mode, attach gates, sandbox brokers and clipboard behavior.

Audit current failure cleanup and no-op repeated launch behavior explicitly.
If shared reset/preparation is justified, add only the smallest hook that
eliminates a demonstrated duplicate. Registry keeps session ownership,
liveness validation and cleanup authority.

### Acceptance and validation

- Exactly one canonical status-wrapper construction and one shared environment
  policy where semantics agree; no second lifecycle/settings implementation.
- Preserve literal JSON/metacharacter argv, stdout/stderr/exit behavior,
  inherit/override/unset order and runner-secret exclusion.
- Existing status/env matrix plus failure/relaunch cases passes on both
  platforms, along with current registry/factory and lifecycle tests.
- Unsupported sandbox/signer/Git SSH behavior remains fail-closed.
- Record upstream-owned modified paths, changed lines and duplicate preparation
  blocks before/after. Added Windows files alone are not an improvement.
- A source-only comparison with the v0.19 delta should show reduced semantic
  duplication; no future-release conflict reduction is promised without an
  actual comparison to that release.

Proposed focused command from the implementation checkout:

```powershell
uv run --no-sync pytest tests\terminals\test_registry.py tests\terminals\test_windows_psmux.py tests\inner\test_terminal.py tests\runtime\harnesses\test_runner.py tests\runtime\harnesses\test_scaffold.py -n 0 --reruns 0 -p no:cacheprovider -q -ra
```

This is a proposed command, not a claim that it ran. Use permitted environment
tooling only; previously denied Python executables must not be retried through
aliases or replacement environments. Record blocked checks and seek permission
for source-matched Actions. Preserve the existing Linux/Windows gates, required
broader sweep, E2E, Browser Contract and artifact identity checks.

## Later packages, only after 1 and 2

3. Hook/mux transport: narrow encoding/control adapters, upstream canonical
   readiness/settings/delivery policy. No broad bridge rewrite.
4. Lifecycle/shell callers: reuse current consumer-specific quoting and
   identity-aware helpers; no experimental launcher default change.
5. Validation selections: reuse the current Windows helper and one selection
   owner for local/CI phases instead of copied lists. Keep the broad gate
   required and real mux checks serial; preserve main manual-only policy.

Upstream genuinely portable improvements separately when authorized, reducing
the maintained fork delta instead of merely moving it.

## Execution gate and handover

Before any runtime work: approve the maintenance branch/worktree and package
scope, verify baseline/import identity, establish permitted validation tools
and a new shared attempt/push budget. No implied budget reset. Commit/push/
Actions permissions are separate; do not rewrite the validated branch or
reactivate automatic main workflows.

Use small disjoint work units; follow current model constraints. Workers must
prove actual checkout/full refs and absolute evidence locations. The coordinator
owns factory/lifecycle/cleanup contracts and reviews the combined change.
No giant platform abstraction, unrelated UI/general fix, dependency upgrade
or v0.14 backport belongs in these packages.

Human acceptance after an authorized build: verify exact source/version,
space/Unicode/other-drive workspaces, two-session paste, Stop/resume after
`Start-Sleep -Seconds 30`, owned desktop shutdown with an independent CLI
surviving, and actual image/ZIP sandbox reads. Passing mocks do not replace it.
Back up real config/data; do not downgrade against a migrated database.

## Execution record: packages 1 and 2

| Phase | Implementation/evidence | Status before the authorized push |
| --- | --- | --- |
| Phase 0 | Seven original extraction refs verified; current owner and security/support mapping above retained. Original v0.14 intent is not mistaken for later parent-environment/status/tracing contracts. | Complete; no old code replayed |
| Package 1 | Test-only commit `a07520b5053e24ccbc399356296ad47842d6ed6d`, directly on the validated baseline. Existing lifecycle/error tests are parameterized across tmux and psmux. New scenarios cover Windows environment ordering, literal status-wrapper argv, preparation failure before spawn, and exact registry context/ownership. Existing release-backend and cleanup tests remain sufficient and unchanged. | Ruff/format passed; runtime characterization must pass on unchanged production in CI |
| Package 1 primitives | Existing injected backend, local fake subprocesses, release contract tests and runtime side-client/polling primitives are reused. No new global fixture, helper framework, removed test patch point or capability skip. | No test moves, old test names or decorators removed |
| Package 2 | Commit `b5137272f026c11786b97d1c545c1e7933fd08e9` changes only `omnigent/inner/terminal.py` and `omnigent/terminals/psmux.py`. Both use one inherited `_wrap_program_status` implementation; psmux reuses `terminal_pane_environment`. | Candidate prepared; acceptance conditional on baseline-first and candidate contract checks |
| Validation | A Windows/Linux matrix checks the immutable package 1 parent and source identity, runs baseline contracts, switches to the candidate, verifies identical collected nodes, then repeats the same tests with retries disabled. Full existing release checks wait for that matrix. | One push/validation round authorized; no retry without confirmation |

The production candidate has 34 added and 53 removed lines across those two
owners (19 fewer overall): status-wrapper construction goes from two copies
to one, and the psmux-specific environment-policy copy is removed. No module,
public constructor, launch signature, dependency pin, shell selection,
sandbox behavior, broker cleanup or mux protocol is replaced.

Local Python and full pre-commit execution remain blocked/unavailable; local
Ruff/format and workflow/static checks are not reported as runtime passes.
The authorized round includes the existing remote lint/type/version checks.
Record exact run SHAs and completed results after the round without another
push if no allowance remains.
