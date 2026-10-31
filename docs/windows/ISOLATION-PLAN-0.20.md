# Windows isolation after v0.20

Date: 2026-10-31. Status: candidate publication in progress; acceptance provisional.

## Source and authorization

Maintenance worktree `omnigent-v020-isolation`, branch
`windows-parity/v0.20-isolation-p3-p5`, starts at validated release
`a67684ae0fc2299c8efc2e5f37824c71c8f044a6`. The release checkout remains
unchanged. Exact upstream v0.20.0 is
`bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee`; prior P1/P2 source is
`430ea3caabec09ff894e92c0c03bfe029361418e`.

The initial five shared implementation/validation iterations completed, then
work stopped. The user subsequently authorized continuation, pushing when ready
and `gh` Actions dispatch/monitoring with six additional shared rounds. Round 1
is reserved for prepublication corrections, permitted checks and the initial
gated commit/push; later correction, rerun and documentation-only publication
rounds share the remaining allowance. Read-only monitoring is not a retry.
The older release allowance remains exhausted. No maintenance commit, push or
dispatch has yet occurred. The earlier claimed Python/full-hook restriction
was a misreading of read-only subagent instructions, not a global user ban.
The normal local hook gate is required before publication. No main
promotion, release/image publication or alternative interpreter is authorized.
`.gitignore` content stays excluded.

## Implemented boundaries

### One owner for shared CI selections

`.github/scripts/ci/release-test-groups.json` owns four ordered literal argv
groups: portable Codex lifecycle, attachment cache, attachment consumers and
process shutdown. The existing Linux/Windows workflow steps now select those
groups through `run-release-test-group.mjs`. Its child is `uv` with literal
arguments, inherited environment/streams, repository-root cwd and `shell: false`.
Unknown IDs, malformed manifests, spawn errors and missing status fail closed;
child failure status is propagated. No retry or passthrough command interface
was introduced.

The independent `fixtures/release-test-groups.a67684ae.json` freezes the original
argv. Offline Node tests cover literal `-k`, paths/environment, failure behavior
and both workflow lanes. Existing Node/pnpm setup moves earlier; no dependency
or lock changes are needed. The four groups retain 53 target references and
their original flags. The Windows stable helper remains a separate selection.

Existing dispatch supports the exact maintenance branch's contract guards and
uses a676 as its baseline, with ancestry/import-identity and own-lock checks.
The 37-node selection, stable AST owner audit, serial real psmux and blocking
broad Windows gate remain. No automatic maintenance push trigger is added;
workflow availability is not dispatch authorization.

A maintenance-only candidate gate executes the mux helper and existing paste
success/failure scenarios on both contract platforms, with retries disabled and
source-labelled JUnit artifacts. It supplements rather than changes the frozen
37-node baseline comparison or the four shared selections.

### Paste routing, not composer policy

`omnigent/native/mux.py::terminal_mux_load_buffer_args` owns only operation argv:
`load-buffer`, buffer name, Windows-only `-t`/target and literal file path.
`bridge._paste_and_submit` still owns bytes/temp files, clear/readiness policy,
subprocess invocation, cancellation, failure cleanup and submit verification.
`paste-buffer` stays targeted on both OSes. Existing bridge tests retain their
audited decorator matrices and add temp-file ownership/cleanup assertions;
a direct helper test covers spaces/Unicode and both platforms.

No generic mux executor, new transport class or duplicate hook policy was added.
Claude `_run_tmux`/`_capture_pane` facades and real Codex control consumers stay
unchanged. Existing P1/P2 environment/status preparation, identity-aware close,
Windows process ownership and consumer-specific shell helpers remain canonical.
Existing lifecycle coverage is reused rather than codifying known stale-event
behavior or creating another ownership framework.

## Upcoming PRs guide the boundary, not feature adoption

See the [dated direction review](UPSTREAM-DIRECTION-0.20.md). Composer parser,
repaint/clear-hold and queue-order work stays in shared upstream owners. Windows
buffer addressing is the small leaf beside that changing policy. Retired-poller
and stale-callback fences are behavioral fixes for separately attributed future
reconciliation. Interrupt acknowledgement is not Stop/idle; captured psmux grids
are not raw tmux control output. Managed config, worker launch, desktop network
policy and shared-sandbox frameworks were not changed or backported.

The measurable source change is eight duplicated workflow selection blocks
replaced by four groups, and one inline psmux load-target rule moved from the
upstream paste-policy block. This does not prove fewer future merge conflicts.
The baseline fixture duplicates expectations intentionally for preservation;
it is not another runtime selector.

## Iteration record and verification

| Iteration | Work and observed result |
| --- | --- |
| 1 | CI selection owner and tests. Six Node tests passed, two failed on LF-only assertions. |
| 2 | Normalize CRLF and tighten no-auto-trigger assertion. Seven passed, one caught an unintended maintenance push trigger. |
| 3 | Remove that trigger; extend existing paste cleanup assertions. Shared terminal returned stale interruption text, no usable validation output. |
| 4 | Small argv extraction, direct unit test, skill corrections and handover. Node eight passed; static verifier passed 95 workflows, skill links, exact Git argv parity and unchanged gates. Ruff caught one new overlong test line. |
| 5 | Split that test line. Final Node 8/8, 95-workflow YAML/skill links/exact Git argv parity/whitespace and scoped Ruff lint/format all passed. Stopped at the initial allowance. |
| Additional 1/6 | Add a candidate-only two-OS buffer gate/JUnit and exact-once group assertions. Node 9/9 and static verification of 95 workflows, original argv/triggers/contracts and whitespace passed. Publication paused because read-only worker restrictions were incorrectly treated as global. |
| Additional 2/6 | Correct the restriction scope. Install locked lint/test dependencies with Python 3.12.14 and pre-commit 4.6.0; locks unchanged. Native Windows candidate tests: 36 passed. Linux-target Pyrefly: zero errors; default Windows target reports inherited POSIX API diagnostics. Hooks also repaired missing newlines/mixed endings. |
| Additional 3/6 | Explicit Linux type-check target passes normal Pyrefly. Custom lint exposed default Windows cp1252 decoding; hooks normalized configuration endings. |
| Additional 4/6 | UTF-8 hook execution fixes decoding; full source scan exposes Windows command-line length limit. No files skipped or rule suppressed. |
| Additional 5/6 | Move the complete TypeScript path list to UTF-8 JSON stdin; retain argv CLI. Extend existing Python/Node tests for 2,000 Unicode paths and both CLI modes. Python 90 passed; Node 77 passed. Semantic hooks all pass; formatter/line-ending hooks made repairs. |
| Additional 6/6 | Final hook repairs, ordinary signed-off commit/push and initial source-matched `gh` dispatch/monitoring reserved. No further correction push/rerun authorized; record final results externally without an extra documentation push. |

`gh` confirmed fork-release and lint workflows active (IDs 359819091 and
359819105). The maintenance branch does not yet exist remotely; recent main
runs are unrelated to this candidate. Shared Git hooks were absent, and the
current repository guidance still requires the pre-commit gate. The coordinator
subsequently verified that the supposed local restriction belonged only to
read-only research prompts. No unchecked commit or remote-write workaround was
performed. Proceed through normal hooks and source-matched `gh` validation.
The Linux type target matches the existing canonical CI type-check lane; Windows
runtime coverage remains independent. The visibility lint change preserves the
full source scan but avoids Windows' process command-line limit using JSON stdin.
No application behavior, dependency lock or lint rule was loosened.

Editor diagnostics reported no errors in changed Python, workflow and Node test
files. Diagnostics and source review are not Python execution or native mux
acceptance. Local candidate mux/paste/visibility tests passed (90 total) and
Node contracts passed (77 total). Applicable semantic hooks passed; final
formatted-source gate and remote baseline/candidate contracts, full suites,
live psmux and candidate artifacts still await publication results.
Earlier release checks/artifacts validate a676, not these uncommitted edits.
Local evidence is outside the tracked tree at
`D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-isolation-20261031`.

Final read-only `gh` refresh at `2026-10-31T11:12:06+01:00` confirmed the eight
core composer/lifecycle/queue/attach PR pins and states in the direction record.
The release checkout remained clean at a676. All maintenance edits are still
uncommitted; no source-matched candidate Actions or artifacts exist.

## How to verify

1. Open the maintenance checkout, not the old editor or release checkout.
   Run `node --test .github/scripts/ci/release-test-groups.test.mjs`.
2. In a subsequently permitted environment, run `tests/test_native_mux.py`,
   the existing Claude paste/failed-buffer scenarios and Codex control tests
   with retries disabled; compare baseline/candidate contract nodes and actual
   results. Preserve the workflow's full blocking Windows and serial psmux lanes.
3. For later authorized runtime acceptance, identify the absolute executable,
   version/source and printed UI URL with fresh config/data. Use two owned panes
   for short, Unicode/multiline and 20 KB chat messages; only the target receives
   them. An unreadable composer must not be certified clear; a buffer failure
   must not send Enter.
4. Separately exercise Stop/follow-up after native PowerShell
   `Start-Sleep -Seconds 30`, interrupt/resume and desktop Quit while an
   independent CLI survives. No real installation, state migration or vendor
   credentials were exercised by this task.

Rollback sources remain the unchanged a676 release checkout and prior430 backup
`backup/windows-v019-isolation-before-v020-20261030`. Never downgrade against a
newer database without restoring its matching backup.
