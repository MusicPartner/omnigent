# Windows integration: upstream v0.19.0

## Scope and immutable refs

- Date: 2026-10-21.
- Fork: `https://github.com/MusicPartner/omnigent.git`.
- Windows source: `windows-parity/v0.17-integration`,
  `f50a1f1cdcbc2c01499a09c8c932c9f7348b8a42`.
- Previous upstream release: v0.17.0,
  `12b5f67d2529b43eab7366a7288fb89f7587e48b`.
- New upstream stable release: v0.19.0,
  `d43340fec4e7d2d767f319d715e84aa82f4d1bc8`, verified against the upstream tag.
- Integration branch: `windows-parity/v0.19-integration`.
- Recoverable Windows source:
  `backup/windows-v017-before-v019-20261021`.

The integration merges the exact stable release into the new branch based on
the existing Windows source. Both histories and their attribution are retained;
this is not a replacement of the Windows implementation with upstream files.
The actual Git merge base is
`b05888bab8527a10e34e7c61d19f01a442ce325e`. It differs from the previous release
tag, so the semantic Windows inventory uses v0.17.0 rather than assuming every
Git conflict represents a Windows change. Release-version conflicts are resolved
to v0.19.0 across core and sibling SDK packages.

The original v0.17 branch, the v0.14 editor checkout and its existing edits,
the installed application, and `main` must remain unchanged. The user authorized
local implementation and validation, followed by pushing this new branch and
running targeted Actions against its exact SHA. This does not authorize a
release, image publication, default-branch changes, schedule activation, or a PR
to `main`.

The user subsequently requested disabling automatic Actions on `main`.
Workflow-only commit `d8a23edf8b2e3f9531cfc70177b6a255a9415dbd` makes 58 enabled
workflow definitions manual-only. Verification found no remaining automatic
triggers among active main workflows and no running automatic main jobs.
Application code on main is unchanged; the v0.19 branch's validations remain
available. Preserve this administrative policy in any future promotion to main.

## Replay plan and ownership

The cumulative fork delta contains 307 files. The content policy permits
inspection of 306; the remaining known file is excluded from the semantic
content audit. No alternate access to restricted content is attempted.

| Topic | Reconciliation requirements |
| --- | --- |
| Terminal and runner foundation | Preserve psmux leaf modules, targeted buffer operations, copy-on-write parent environment, terminal tracing, filesystem probes and Windows path handling. |
| Process lifecycle and sandbox boundaries | Preserve identity-checked owned-process cleanup, credential refusals and the opt-in private-job launcher; a Job Object is not filesystem/network isolation. |
| Native and SDK harnesses | Retain current upstream settings, trust, readiness and message-delivery behavior while transporting literal Windows argv and capability-based readiness. |
| Frontend and Electron | Preserve workspace breadcrumbs, native-terminal input, SSE heartbeat readiness, host readdressing and desktop-owned shutdown. |
| Release infrastructure | Keep required Windows gates, isolated psmux execution, source-matched artifact checks and explicit nonpublishing Docker verification. |

Bulk conflict reconciliation and release-infrastructure work use explicitly
selected GPT-6 Luna workers with disjoint file ownership. The coordinator owns
cross-topic decisions, dependency reconciliation and final verification.
Earlier default-model attempts were interrupted before returning implementation
results; they are not reported as Luna work.

The [per-file ledger](RELEASE-INTEGRATION-0.19-ledger.csv) accounts for all 307
original fork paths, four release-version conflicts and six additional
integration-compatibility files. Raw command logs
remain in the local session evidence directory, not in the repository.
Each drop requires equivalent upstream behavior or an explicit obsolete-contract
explanation; a clean textual merge alone does not establish semantic
compatibility. `REVIEW` rows retain explicit bounded-audit or live-acceptance
limits rather than claiming complete runtime coverage.

The compatibility audit found a clean-merge omission: psmux's launch override
did not apply upstream's optional program-status wrapper. The adapter now
composes it with environment-variable removal. The existing mocked launch test
covers the four combinations of status wrapper enabled/disabled and environment
inheritance/removal; runtime execution of that extension is pending Actions.

## Dependencies

Retain upstream v0.19.0 core/client/UI/Slack versions and dependency pins.
The Windows-only `distlib` test dependency and packaged private-job-launcher
resource declarations remain from the fork. The Python lock is regenerated
for that real dependency difference, not copied from v0.17.

Retain the fork's Lightning CSS 1.33.0 override: the previous release records
demonstrate it fixes valid `::highlight(...)` parsing warnings. Preserve the
new upstream PostCSS version. Regenerate the pnpm lock using the repository's
pinned pnpm 11.15.1, without upgrading unrelated dependencies.

## Validation evidence

Results below apply to the in-progress integration worktree, not an immutable
release artifact. Final commit and Actions results must be recorded separately.

| Selection | Result |
| --- | --- |
| Editable core/client/UI imports | All report 0.19.0; core imports from the new integration checkout. |
| Nine focused frontend Vitest suites | 1,669 passed. Existing React `act(...)` warnings remain diagnostic output, not test failures. |
| Electron shutdown/manager and session-visibility Node tests | 92 passed. Electron runtime download is not required for these mocked unit tests. |
| Frontend `tsc -b` | Passed. |
| Frontend oxlint | Passed with warnings denied. |
| Production frontend build | Passed; Vite reports large-chunk warnings. |
| Native shell/mux and PowerShell source-installer tests | 38 passed. |
| Bundle installer and launcher packaging fixtures | 64 passed; no real user PATH or installation changed. |
| Accessible fork Python delta | 240 files pass release-matched standalone Ruff and formatting checks. |
| Fork-added test-name preservation | All 349 named tests across 167 files remain. This textual inventory is not an AST/decorator or runtime proof. |
| Workflow syntax | Fork workflows and hook configuration parse with an independent Node YAML parser. |
| Remaining native Python regression suites | Pending; the isolated interpreter was subsequently denied by content policy. Do not access it through another command or tool. |
| Local required hooks | `pre-commit run --all-files` could not run because the command is unavailable. A separate explicit system-interpreter probe was also policy-denied; do not retry it through aliases. Ruff, frontend lint/types and formatting use independent native tools. |
| Remote lint and version lockstep | Passed at `623ef769b4a4c56ffba647d2a42696fef3c243f8`, run [39646104363](https://github.com/MusicPartner/omnigent/actions/runs/39646104363). Formatting, lint and type-check steps completed. |
| Remote harness integration | Passed at the same SHA, run [39646109887](https://github.com/MusicPartner/omnigent/actions/runs/39646109887). |
| Remote Docker verification | Passed at the same SHA with `publish=false`, run [39646101552](https://github.com/MusicPartner/omnigent/actions/runs/39646101552). |
| Initial fork release validation | Both Linux and Windows jobs failed; a passing Linux test family is not a passing job. The first Windows suite reported 15 failed, 1,276 passed, 170 skipped and 11 passing subtests. Artifacts were correctly blocked. Run [39646017315](https://github.com/MusicPartner/omnigent/actions/runs/39646017315). |
| Backend E2E at the initial SHA | Two shards passed; two failed. Three cases patched the old terminal-factory owner, and one REPL startup failure remains unclassified. Run [39646106748](https://github.com/MusicPartner/omnigent/actions/runs/39646106748). |
| UI at the initial SHA | Browser Contract and seven shards passed; three failed. Slow-ready observer and Windows path-chip test contracts require reconciliation; the render-parity recovery failure remains unclassified. Run [39646111835](https://github.com/MusicPartner/omnigent/actions/runs/39646111835). |

Local Python validation uses a separate environment, CPython 3.12.14, and
`uv sync --locked --group dev --extra tracing`. It does not reuse or modify
the old checkout's environment. No unused Databricks extra is installed.
Real psmux checks must run serially with a private `PSMUX_DATA_DIR`.
The successful local Python runs above predate the interpreter restriction;
they are not evidence for backend files reconciled afterward. Remaining
backend coverage must be established by permitted tooling or source-matched
Actions before the branch is described as validated.
The user reported a manual pre-commit launcher command, but its result and a
completed repository hook run were not supplied; it is not counted as a pass.

## Initial Windows CI repair

The first Windows failure is separated into actual support boundaries and a
new upstream portability issue:

- Preserve Windows' safe-delete `permission_denied` result when no secure
  directory-descriptor traversal is available. Tests now assert that denied
  deletion leaves the file, directory or link unchanged; POSIX deletion and
  race assertions remain.
- POSIX permission-bit assertions remain on POSIX. Windows test paths still
  verify copied credentials are separate and credential data is not leaked.
- Pi's new gateway helper used unavailable `os.killpg` on Windows. Cancellation
  now delegates to the existing identity-aware owned-process `kill_tree`
  helper on a worker thread; POSIX process-group cleanup is unchanged.

The next Windows gate starts with the exact affected cases and the psmux
program-status matrix, with retries disabled and per-test timeouts, before
repeating its larger selections. The changed repair code requires new
source-matched validation; the earlier green results are not relabeled as
validation of this later code.

Repair commit `41d03794e4aa2d4f5024c4a8c4b2b76314cd6144` passed remote lint at
run [39650266005](https://github.com/MusicPartner/omnigent/actions/runs/39650266005).
Its release validation exposed further failures rather than completing:

- Gateway-auth command construction still used POSIX quoting under Windows'
  native command shell. Commands now use the shared shell formatter; the
  credential helper uses the platform's native subprocess shell and isolated
  process-group spawn arguments.
- Helper fixtures now launch an actual Python process and record its native
  PID on both platforms. They no longer rely on POSIX `printf`, `sleep`, shell
  job syntax or MSYS process IDs. Liveness checks use the shared non-signalling
  helper instead of `os.kill(pid, 0)`.
- Codex teardown must close in a `finally` path and retain registration when
  closing fails, while respecting replacement-server/bridge-directory ownership.
- The new terminal retry E2E patches the tmux backend's actual factory owner.
  The slow-ready observer forwards upstream's `extend_for_slow_boot` keyword.
  The workspace test verifies the full path through the chip's title and still
  checks the exact session POST body.

Focused Windows failures stop at the first failure with a short traceback,
instead of allowing a later hard timeout to hide earlier assertion details.
These later repairs are not covered by the earlier green lint/E2E results.

At `e5b3b81f6c5f065f48cac521a14e7c81543c9711`, remote lint, integration and
nonpublishing Docker checks passed again. Release validation's full Linux job
passed. Windows passed the focused regression matrix, portable families,
attachment cache/consumers, Stop/ownership, desktop tests, CLI smoke, upstream
hard tests, launcher, stable subset and hook tests. Its real psmux step failed
before the broader sweep; CLI/desktop artifacts remained correctly blocked.
The UI run passed Browser Contract and nine shards, including the repaired
slow-ready and Windows-picker cases; the remaining recovery test is being
diagnosed. Do not describe these incomplete release/E2E gates as green.

The remaining test contracts were reconciled without further production
changes: psmux readiness includes its valid session-port metadata, and the
native recovery journey uses the visible queued-follow-up textbox and keyboard
submit path. The REPL failure advanced past startup and refusal before missing
the cosmetic ready-toolbar marker. Its replacement barrier sends a distinct
user turn and requires the scripted reply, retaining denied-tool output checks
before and after that round trip and recording the full PTY stream.
The earlier host-online timeout and later idle-marker timeout are different
observations, not a demonstrated shared root cause.

The psmux metadata wait did not resolve the failure in run
[39661729758](https://github.com/MusicPartner/omnigent/actions/runs/39661729758).
Source inspection of psmux 3.4.0's `socket_path.rs` established that custom `-S`
paths use `sock-<hash>__<session>` metadata namespaces. The fixture's guessed
`<session>.port` filename was therefore wrong, not merely late. It now captures
the actual `TMUX` value supplied to each child and uses the other pane's real
context for the cross-session paste test. No namespace hash is duplicated,
deadline extended, production behavior changed or assertion removed.

Round 1 reached all three real paste payload comparisons. Their only mismatch
was the canonical v0.19 focus-probe space preceding Ctrl-A/Ctrl-K, which a raw
reader records but Claude's editor clears. Round 2 updates the exact byte
expectation to that upstream prelude; payload, Unicode/multiline/20,000-character,
cross-session non-delivery and temporary-file cleanup assertions remain intact.

Round 2 stopped earlier in the Windows portable family: 1,290 tests passed and
170 skipped, but the gateway-helper test read an empty PID file between its
creation and write. Round 3 publishes the fixture PID with write-then-rename
and uses the same complete-file publication for the paste fixture's readiness
and result data. No timeout is increased and production code remains unchanged.

Round 3 passed every focused Windows gate, including real psmux, paste safety
and argv parsing. The completed broader JUnit contains 4,424 entries (including
subtests), 8 failures, 10 setup errors and 223 skips; the console log ended
after collection, so the retained JUnit rather than its tail is authoritative.
The last batch reconciles six test files:

- ACP asserts the existing quoted/repr path diagnostic on either platform.
- OpenAI gateway tests assert Windows' early missing-profile refusal and retain
  the POSIX turn-time auth diagnostic, with HTTP resources closed in either path.
- Launcher tests retain scratch-directory assertions on Windows and POSIX
  permission-bit assertions on POSIX.
- Runtime GC tests retain the real server interface and restore SIGBREAK;
  independent side clients use the manager's actual TCP/UDS route and headers.
- Git SSH parser fixtures use sandbox-POSIX paths rather than host-Windows
  paths. Portable parser and containment/refusal cases remain active. Nine real
  broker tests skip Windows because the production broker explicitly requires
  Unix sandboxing and AF_UNIX; Windows gets an explicit unsupported-platform
  assertion instead. The existing short Unix socket fixture is retained.

These changes do not enable Git SSH, brokered signing, filesystem isolation or
network isolation on unsupported Windows backends. They do not change production
code, increase deadlines or make the required broader gate non-blocking.

The final test-contract batch is code commit
`603cd8194f78211351ccdcb2778b076d58d15824`. Its handover-only descendant is sent
in the same fourth push, not a separate push/retry round. The ledger contains
317 rows and retains 46 explicit bounded-review/live-acceptance limits.
All 349 named fork-added tests remain in the textual inventory; that does not
replace runtime coverage or decorator review. Production, web and SDK source
trees remain identical to the fully linted `e5b3b81f6` application tree.

Backend E2E run [39661930031](https://github.com/MusicPartner/omnigent/actions/runs/39661930031)
passed all four shards at `008949b15688d19ab16213b606840935c4c65f6d`. UI run
[39661934560](https://github.com/MusicPartner/omnigent/actions/runs/39661934560)
passed Browser Contract, all ten shards and its aggregate gate at the same SHA.
The later changes are confined to the Windows fixture and documentation;
production code and these E2E test paths are unchanged.

## Current attempt budget

At 21:40 on 2026-10-21, the user set a shared maximum of four additional
push/retry rounds, replacing the preceding two-round cap. Already-running
checks do not count; documentation-only pushes do. The first additional round
carries the namespace-independent psmux fixture correction. The second
reconciles its raw-reader expectation with the upstream focus probe. The third
fixes complete-file publication in generated fixtures. Three rounds are used
and the fourth batches the broader-suite contract corrections and this handover
snapshot. After the fourth push/retry round, none remain. Obtain explicit
user confirmation before a fifth additional round, including across handovers.

This snapshot is committed before the final checks finish. Their durable result
is the [branch's Actions history](https://github.com/MusicPartner/omnigent/actions?query=branch%3Awindows-parity%2Fv0.19-integration);
do not infer a pass from an earlier run or from a pending snapshot. Any further
code, documentation-only push or manual retry requires renewed confirmation
once the four-round budget is exhausted.

## Acceptance limits and rollback

Historical passing v0.17 CI at `e6a14a5e9` does not validate source `f50a1f1cd`
or this merge. Setup-only Claude capture does not prove a provider conversation.
Keep live acceptance distinct from mocked/unit coverage:

Use isolated config/data and a fresh database for initial acceptance. Back up
the real v0.17 configuration and data before an in-place upgrade; do not point
v0.17 at a database already migrated by v0.19 without restoring its backup.

1. Launch the exact verified checkout or source-matched artifact explicitly.
2. Verify the executable path, version and UI URL.
3. Exercise another drive and a workspace with spaces/Unicode.
4. Use two owned native sessions to check short, multiline and large paste,
   then chat-UI resume.
5. Run `Start-Sleep -Seconds 30`, stop the session and send another message.
6. Quit the desktop while keeping an independently launched CLI session alive.
7. Verify image and ZIP reads in the actual vendor sandbox before claiming
   attachment acceptance.

Rollback is non-destructive: use the unchanged v0.17 branch or its backup ref
in its original checkout. Do not move published refs, reset other worktrees,
modify the real installation, or terminate unowned sessions.
