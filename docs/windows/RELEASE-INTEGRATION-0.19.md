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
original fork paths plus four release-version conflicts. Raw command logs
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
| Initial fork release validation | Linux passed; first Windows suite reported 15 failed, 1,276 passed, 170 skipped and 11 passing subtests. Artifacts were correctly blocked. Run [39646017315](https://github.com/MusicPartner/omnigent/actions/runs/39646017315). |
| Backend E2E and UI | Dispatched against the same SHA; final results pending. |

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

## Acceptance limits and rollback

Historical passing v0.17 CI at `e6a14a5e9` does not validate source `f50a1f1cd`
or this merge. Setup-only Claude capture does not prove a provider conversation.
Keep live acceptance distinct from mocked/unit coverage:

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
