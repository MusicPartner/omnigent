# Windows integration: upstream v0.20.0 — candidate ledger

## Round 3 outcome and round 4 scope

Round-3 fork run [41070986497](https://github.com/MusicPartner/omnigent/actions/runs/41070986497)
at `249ac5393fe0ba71d5587e1cda5513ec317928f5` failed the strict decorator
audit on an intentional Claude tmux/psmux parameter matrix. The next batch
allows that exact matrix on its two reviewed owners, retaining all target
decorators, the exact Pi portability mapping and the four required POSIX markers.
Candidate execution and artifact jobs have not yet passed.

The original UI run [41067501570](https://github.com/MusicPartner/omnigent/actions/runs/41067501570)
completed with three failed shards. Two model-picker scenarios expected absent
Claude transcript fields (`requestedModel`, `requestRef`, `api-request`). Their
replacement evidence keeps the full pinned model/status and assistant model
checks, while correlating the real HTTP request by user marker and checking its
actual context-beta header. The mock records only that allowlisted header, with
focused regression coverage. The login journey incorrectly required a user bubble
after the server's terminal-only HTTP 400 refusal. It now checks the actionable
refusal, restored draft and absence of plain or escaped `/login` from transcript
and model user input. Neither server policy nor production UI is changed.

The user upgraded local psmux; a read-only version check confirmed **3.4.0
(`20aa1d7`, 2026-10-13)**. No running sessions were stopped or restarted. CI now
pins and verifies 3.4.0; this is not yet a runtime pass. Its status/signal/cursor
placeholders still require the existing compatibility safeguards.

Round 4 batches the fork gate, pinned lint and a UI rerun at the new source SHA.
The request-capture regression is included in focused Linux validation. Earlier
integration/backend/Docker results remain source-qualified evidence at `9ba784ca…`.
**3/6 rounds used before this push; 2 remain after round 4.** Local Python and
full hooks remain unrun under the inherited restriction; standalone Ruff,
strict YAML and whitespace checks are repeated before pushing.

## Round 2 outcome and round 3 scope

At `c0821a838732fd7ac8834342f819414369fec602`, lint run
[41070123358](https://github.com/MusicPartner/omnigent/actions/runs/41070123358)
passed every job, including the complete pinned pre-commit suite and version
lockstep. The content-search import, redundant directive, CSV EOF and YAML
repairs therefore passed that gate; focused runtime execution is still pending.

Fork run
[41070125122](https://github.com/MusicPartner/omnigent/actions/runs/41070125122)
ran on both platforms. Each source-matched baseline at `430ea3ca…` passed all
37 contract tests using its own locked environment. The new AST audit then
rejected the Pi gateway test's intentional portability parameterization before
candidate contract execution; downstream Linux/Windows/artifact jobs skipped.
It compared POSIX `printf`/`sleep` commands with native Python scripts as though
the decorator had simply disappeared. All three failure, empty-token and timeout
cases and their redaction assertions remain present.

Round 3 changes only this record and that audit. It recognizes the exact old and
new parameter matrices for this one named test; every other target decorator
must remain, and precisely the four reviewed POSIX markers must be added.
No production code, runtime assertion or gate is relaxed. Final strict YAML
checking is repeated before committing. The fork gate alone will run on push;
the passing lint result remains evidence for `c0821a838…`, not a new whole-SHA
pass. The original UI run continues untouched. **2/6 rounds used, 4 remain before
the round-3 push; 3 remain afterward.**

Date: 2026-10-30. **The integration branch is at verified HEAD
`9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`; source-matched validation and
acceptance remain in progress.** The stable merge is
`abbb5e598ad989e0268c1d577a38da5dbca758c5`, followed by the Windows terminal
fix `806c7ce308dbfe970ebc402dcac59db9c18cf652`. The previously recorded CI
snapshot `eabd86b032ad12e80131b12e2b3b91f9e099e72b` is historical, not current
HEAD. The merge has parents `430ea3caabec09ff894e92c0c03bfe029361418e` and
`bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee`. The checkout has coordinator
repair edits in progress; this record describes the verified branch HEAD and
must not be read as final validation of later edits.

Current round-1 evidence snapshot (source SHA
`9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`):

- Fork run **41067491820** completed with failure: an extra-indented AST audit
   step made the workflow invalid before any jobs ran. Strict parsing after all
   workflow repairs found zero document errors across 95 workflows. Remote AST
   execution remains pending; the earlier pre-insertion parse did not validate
   the rejected definition.
- Lint run **41067493114** completed with findings for an unused `noqa` at
   `omnigent/runner/native/interrupt.py:709`, missing CSV EOF newline,
   CheckYAML indentation, and Pyrefly's missing `_python_script_command` import
   from `environment_filesystem` in `omnigent/runner/content_search.py`. The
   coordinator repaired the content-search import/call to use the existing
   `_python_shell_command` (same POSIX
   sandbox `python3 -I -c`; Windows probe leaf unchanged) and extended
   `test_content_search_rejects_invalid_helper_output` with shell-command and
   kwargs assertions. The new focused Linux step runs
   `test_environment_filesystem -k content_search` with retries set to **0**.
- Pinned Ruff removed the unused `noqa`; that modification failed its hook and
   is included in the repair. Separate invalid-`noqa` warnings at upstream
   bridge/orchestration lines were warnings, not the blocking diagnostic.
- The 39 older BLE001 findings were not actual pinned-Ruff errors. Remote Ruff
   formatting, web Prettier/oxlint/TypeScript, native Android/iOS checks, and
   lock/version guards passed.
- Integration **41067497520** and nonpublishing Docker **41067511450** passed
   on exact SHA `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`. Backend E2E
   **41067506812** also passed. UI **41067501570** remained in progress in the
   latest Actions snapshot, with no failed jobs reported; do not stop or
   duplicate it. No runtime test was performed locally.
- Later source changes require validation at their own SHA. Evidence for an
   unchanged input closure may be reused only with its scope stated explicitly.
   Runtime, installer, artifact, and human acceptance remain pending.

Earlier implementation/evidence snapshot (historical; superseded by the
current snapshot above):

- The release workflow has a new integration-branch gate and removes 20
   scheduled declarations, preserving the no-schedule policy evidenced by the
   fork-main workflow-only commit `f9c0b39e004ffbe1261565d371866259716d0281`;
   this does not use main as the application basis.
- Native psmux now preserves unknown exit status in `_remember_exit_status`,
   with regression coverage for three paths. The launch-failure cleanup test
   now injects its backend rather than relying on a stale registry export.
- Baseline/candidate checks use independently locked environments; the
   source-matched baseline is `430ea3caabec09ff894e92c0c03bfe029361418e`.
   Preserve the earlier historical baseline-first pair unchanged.
- Frozen pnpm installation with lifecycle scripts disabled passed. Native Node
   lint passed 67 checks; focused Vitest passed 822 tests across 3 files.
- YAML parsing passed for all 95 workflow files with installed `yaml` 2.9.0.
- Standalone Ruff 0.15.16 formatting passed on 17 files and scoped psmux checks
   were clean. Its 39 target BLE001 findings are inherited from upstream and
   none are candidate-only; pinned Ruff 0.17.0 remains authoritative and pending.
- Full `prettier --check .` reported 1,474 warnings. CRLF is a possible cause,
   not a confirmed explanation; normalized-stdin checking of the changed
   fixture passed (exit 0), not a full-tree check. No mass formatting was done.
- Nineteen dependency static checks passed and were rerun by the coordinator.
   No resolver, Python, or hook run is thereby implied. A fresh PR-state snapshot
   at 2026-10-30 13:05Z recorded 17 merged and 5 open.

These are bounded observations, not full acceptance. Full hooks, remote Actions,
resolver/install validation, runtime, installer, artifact, and human checks are
still pending. The historical baseline pair remains intact. Candidate commit
references are recorded per path in the ledger; none closes a validation gate.


## Scope, immutable refs and provenance

All Git inspections in this task used absolute `git -C` paths to the selected
checkout, not the editor's older checkout.

| Role | Verified value |
| --- | --- |
| Selected checkout | `D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v020` |
| Integration branch | `windows-parity/v0.20-integration` |
| Latest Windows application source / merge first parent | `430ea3caabec09ff894e92c0c03bfe029361418e` |
| Source branch | `windows-parity/v0.19-isolation-p1-p2` in sibling `omnigent-v019-isolation` |
| Previous stable / cumulative semantic base | v0.19.0, `d43340fec4e7d2d767f319d715e84aa82f4d1bc8` |
| Exact stable target | v0.20.0, `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee` |
| Stable integration merge | `abbb5e598ad989e0268c1d577a38da5dbca758c5` (parents: source and exact stable target) |
| Follow-up terminal/test fix | `806c7ce308dbfe970ebc402dcac59db9c18cf652` |
| Earlier CI follow-up (historical snapshot; not current HEAD) | `eabd86b032ad12e80131b12e2b3b91f9e099e72b` |
| Actual Git merge base of source and target | `71fb9694ecf4b54b37919fbb1acd575dfd28243f` |
| Recoverable backup branch | `backup/windows-v019-isolation-before-v020-20261030`, resolving to `430ea3caabec09ff894e92c0c03bfe029361418e` |
| Fork remote | `https://github.com/MusicPartner/omnigent.git` |
| External private evidence root | `D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-integration-20261030` |

Strategy: **history-preserving merge from the latest isolation source into a
new integration branch**, merging only the exact stable target plus separately
scoped security hunks. Both histories are parents of the merge commit. Minimal
version and security hunks are included in that merge commit, not split into
new topic commits: release-version and lockfile conflicts were mixed
boundaries, and splitting them would break the coherent lockstep resolution.
Original security attribution is retained here by upstream PR and source SHA;
those source SHAs are not candidate commits.

The semantic base and Git merge base are deliberately different. Inventory
uses the cumulative previous-stable-to-source diff, including prior merge
resolutions and mixed commits, not just conflicts or commit subjects.

The source contains characterization commit
`a07520b5053e24ccbc399356296ad47842d6ed6d`, shared terminal preparation commit
`b5137272f026c11786b97d1c545c1e7933fd08e9`, and source validation workflow
commit `430ea3caabec09ff894e92c0c03bfe029361418e`. Preserve P1/P2 rather than
replaying old duplicated preparation. The historical baseline-first pair uses
the test-only characterization and validated baseline
`6a7c711308587a2c39dd916c0820af71debfbb67`; do not blindly repin it to the
stable target or invent a new test-only ancestry. A current-source/candidate
comparison needs its own matching dependencies, imports and scenario mapping.

The editor's v0.14 checkout is not the application basis. Fork main
`f9c0b39e004ffbe1261565d371866259716d0281` is a workflow-only administrative
change, not newer application work. Preserve its no-schedule policy without
using main's old application tree as the integration basis or modifying main.
Earlier manual-only policy at `d8a23edf8b2e3f9531cfc70177b6a255a9415dbd`
also remains relevant. Old maintenance prose describing daily/weekly automation
is design/history, not authorization to reactivate it.

## Inventory and count audit

The companion [CSV](RELEASE-INTEGRATION-0.20-ledger.csv) has the required
12 columns:

`topic,old_path,target_path,behavior,disposition,upstream_evidence,dependencies,owner,verification,result_commit,status,explanation`

| Audit against immutable refs | Result |
| --- | --- |
| Cumulative fork comparison | `d43340fec4e7d2d767f319d715e84aa82f4d1bc8` → `430ea3caabec09ff894e92c0c03bfe029361418e` |
| Rename-aware inventory | **322 entries: 111 added, 211 modified, 0 renamed, 0 deleted** |
| Unique covered inventory keys | **322 / 322** |
| Non-covered inventory entries | **0** |
| Duplicate inventory keys / unexpected inventory rows | **0 / 0** |
| Stable upstream comparison | `d43340fec4e7d2d767f319d715e84aa82f4d1bc8` → `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee` |
| Stable upstream paths / cumulative fork overlap | **1,262 / 94** |
| Predicted / actual initial conflict paths | **22 / 22** |
| Prior REVIEW entries retained / missing | **46 / 0** |
| Additional release-compatibility entries | **6**, explicitly outside the 322 |
| Total CSV rows / columns | **328 / 12** |
| Malformed column counts / evidence-label or disposition mismatches | **0 / 0** |
| Populated path-specific `result_commit` references | **19**: merge (`abbb5e598…`), terminal/test follow-up (`806c7ce3…`), and CI (`eabd86b0…`); all verification statuses remain pending |

`old_path` and `target_path` are recorded separately even though metadata shows
no renames in either immutable comparison. Future renames must retain both
names and be audited as pairs, not flattened into a misleading path total.
The 94 overlap count includes the metadata-only excluded path. Seventeen
overlaps remain REVIEW; the other 77 are RECONCILE.

| Disposition | 322 inventory | Compatibility only | All rows |
| --- | ---: | ---: | ---: |
| REPLAY | 199 | 0 | 199 |
| RECONCILE | 77 | 6 | 83 |
| DROP-UPSTREAM-COVERS | 0 | 0 | 0 |
| DROP-OBSOLETE | 0 | 0 | 0 |
| REVIEW | 46 | 0 | 46 |
| Total | 322 | 6 | 328 |

These are **retention/reconciliation decisions, not completion claims**.
REPLAY retains fork intent at a stable-unchanged or stable-absent owner and
still requires caller/contract verification. RECONCILE flags upstream-changed
owners or explicit compatibility work. REVIEW preserves an unresolved bounded
audit, live-acceptance gap or exclusion even when text has been reconciled.
No new drop is approved: no compared source blob equals its target counterpart,
and metadata alone cannot establish semantic upstream coverage or obsolescence.

The old ledger had 317 rows: 313 paths are now in this cumulative inventory;
its four version-only rows remain outside it. Nine inventory paths were absent
from that old ledger: the five maintained skill files, the isolation plan,
the two v0.19 release records, and `omnigent/inner/terminal.py`. The old ledger's
historical outcomes are not copied as candidate results.

### Six additional compatibility rows

Four release-version conflicts are not extra Windows delta paths:
`integrations/slack/pyproject.toml`, `omnigent/version.py`,
`sdks/python-client/pyproject.toml`, and `sdks/ui/pyproject.toml`.
They must retain stable **0.20.0** versions and sibling pins.

The other two are `uv.toml` and
`tests/e2e/test_lockfile_vulnerable_pins.py`, for the scoped security backports.
All six use topic `release-compatibility`; excluding that topic produces exactly
the 322 inventory rows. The newly authored v0.20 Markdown/CSV are record outputs,
not retroactively part of the immutable source inventory.

### Evidence and verification notation

Each shorthand is qualified by that row's actual target path and the full refs
above; it is not an assertion that upstream supplies Windows behavior:

- `UA`: path absent at exact stable target; fork-added owner to retain.
- `U0`: stable target path unchanged from previous stable; retain cumulative
  fork changes and audit callers separately.
- `U+`: stable changed this inventory path; reconcile both contracts.
- `UC`: target path outside the cumulative fork inventory; explicit
  release-version/security compatibility row.
- `S12041`: upstream security commit
  `7f1cf6fde9c022c92144f15f5e2167df7ae3c298`.
- `S12260`: upstream security commit
  `af1a57ffa89716e16f3a315fe89ee13fb3847c75`.
- `metadata-only`: excluded path, with no content inspection or reconstruction.

Dependencies identify review boundaries: `D0` guidance/shared intent;
`D-ci` branch/check policy; `D-deps` stable manifests/locks; `D-term` backend,
registry and shared launch preparation; `D-process` identity-aware lifecycle;
`D-shell` actual command consumer/literal argv; `D-path` host/Windows paths;
`D-route` real TCP/UDS endpoint and auth; `D-safe` fail-closed security;
`D-attach` private cache and vendor delivery; `D-launch` packaging/signer/installer;
`D-test` existing test primitives and precise platform scope; `D-web` UI/SSE
contracts. Owner labels are workstream responsibilities, not claimed model
identities or verification results.

All `pending V-*` values remain required gates; bounded observations below do
not complete those checks:
`V-doc` links/ref/count review; `V-ci` workflow selections/triggers and permitted
remote hooks; `V-deps` resolver/locked install/version/pin guards;
`V-package` clean wheel/resources/disposable install; `V-term` both backend
contracts and serial private real psmux; `V-process` interruption/Stop/Quit and
ownership; `V-shell` consumer-specific literal argv; `V-host` listing/probes;
`V-route` actual authenticated transports; `V-safe` portable refusal/security
cases; `V-attach` cache/consumer tests; `V-harness`, `V-claude`, `V-codex`,
`V-pi` affected harness suites; `V-test` portable area suites; `V-web` colocated
Vitest/Node/types/lint/build; `V-ui` browser journeys/Browser Contract;
`V-e2e` process/CLI journeys; `V-live` the separate human checks below.

Statuses remain **282 pending, 45 review-pending, 1 excluded**; all **46**
REVIEW paths remain unresolved review/live-acceptance gaps. The focused results
above are observations only; they do not close a row's full verification gate
or declare the semantic audit/runtime acceptance complete.

## Prior outcomes and acceptance gaps retained

Read before writing: selected `AGENTS.md`, maintained release skill including
its references/assets/interface, `.github/FORK_MAINTENANCE.md`, the full
v0.19 release record and CSV, and the v0.19 isolation plan. The maintained
historical index and external plan were also consulted. This is targeted
recovery, not a claim to have read every private historical transcript.

All **46** old REVIEW paths remain REVIEW. Of these, `.gitignore` is explicitly
excluded: metadata path/status only; **its contents were never read**. There is
no alternative retrieval or reconstruction. The other 45 retain their bounded
API/live gaps in their individual CSV explanations, including:

- Installed Claude hook-command API and live Git Bash status-line chaining.
- Native bridge/main/credential consumers not fully audited in the prior pass.
- Codex process cleanup reviewed only at exported API boundary, not real
  identity-aware teardown.
- Native attachment signatures previously aligned, but full implementation
  review and actual vendor-sandbox reads were not established.
- Opt-in launcher caller alignment without runtime/signing acceptance;
  approved Authenticode metadata remains a gate, not a default-support claim.
- Several shell consumers still used host-default formatting without actual
  Windows consumer execution. POSIX Git Bash, direct argv and PowerShell hints
  remain different contracts. Executable-only sandbox `%*` forwarding and
  popup consumer quoting remain deferred work, not silently fixed here.
- Native interrupt caller review, readiness/cache/guard consistency, probe and
  transport owners, and captured-grid browser attachment remain explicit gaps.

Historical passing automated checks do not erase these notes. General catalog,
SSE, shared UI and worktree fixes remain general fixes, not Windows adapter
policy. Preserve completed-output delivery without reviving the rejected custom
live-output tool. Job Objects are containment/cleanup, not filesystem/network
isolation; Windows brokered signing/Git SSH/unsupported sandbox refusals stay
fail-closed. Test portability does not add production capability.

Carry the v0.19 repair contracts forward: safe-delete refusal leaves objects
intact on Windows; credential copies stay separate without leaks; Pi uses
native shell formatting and identity-aware helper cleanup; Codex closes in
finally and preserves replacement ownership/registration on close failure;
REPL recovery uses a real post-refusal reply barrier; queued follow-ups use
keyboard submission; psmux fixtures capture actual child TMUX context, exact
focus-space prelude and atomically published PID/readiness/result files.
Real broker skips remain scoped to Unix-only support while portable parser and
Windows refusal cases remain active.

Audit test markers by their owning symbols and parameter IDs, including clean
merges; the historical 349-name textual inventory is not decorator/runtime
proof. Preserve newly added stable assertions as well as fork scenarios.

## Historical conflict and worker snapshot (before the stable merge)

The initial merge had 22 conflict paths. They were resolved and committed in
`abbb5e598ad989e0268c1d577a38da5dbca758c5`; this list is historical, not an
active unmerged-index report:

| Workstream | Paths |
| --- | --- |
| Hooks / lint mutation | `.pre-commit-config.yaml`; `dev/lint/session_list_visibility.test.mjs` |
| Version / dependencies | `integrations/slack/pyproject.toml`; `omnigent/version.py`; `pyproject.toml`; `sdks/python-client/pyproject.toml`; `sdks/ui/pyproject.toml`; `pnpm-lock.yaml`; `uv.lock` |
| CLI / update | `omnigent/cli.py`; `omnigent/update_check.py` |
| Claude | `omnigent/harnesses/claude_native/bridge.py`; `tests/harnesses/claude_native/test_claude_native_bridge.py`; `tests/harnesses/claude_native/test_claude_native_slow_ready.py`; `tests/e2e_ui/chat/test_claude_native_slow_ready_first_prompt.py` |
| Codex / Pi / lifecycle | `omnigent/harnesses/codex_native/app_server.py`; `omnigent/inner/codex_executor.py`; `omnigent/inner/pi_executor.py`; `omnigent/runner/native/interrupt.py`; `omnigent/runner/native/orchestration.py`; `tests/inner/test_pi_executor.py` |
| REPL | `tests/e2e/test_repl_approval_e2e.py` |

Eighteen are inventory paths; four version-only paths are compatibility rows.
All 22 resolutions are in the merge commit. Runtime, dependency and workflow
changes remain subject to the pending source-matched validation gates below.
Other worktrees, foreign edits, installations and live processes are preserved.
No new delegation or model-selection claim is made here.

## Scoped security backports: committed attribution and pending validation

The dependency worker's external `dependencies/REPORT.md` reports integration
of minimal target-compatible hunks from:

| Upstream PR / original SHA | Reported content |
| --- | --- |
| #12041 / `7f1cf6fde9c022c92144f15f5e2167df7ae3c298` | MLflow family 3.17.2; msgpack 1.2.3; qs 6.16.1; five expired cooldown exemptions removed; existing pin guards |
| #12260 / `af1a57ffa89716e16f3a315fe89ee13fb3847c75` | brotli 1.2.1; virtualenv 21.14.13; corresponding existing guards |

Original author for both: **Lee moon soo <moonsoo.lee@databricks.com>**;
co-author **Isaac <no-reply@databricks.com>**; original committer GitHub.
The target-compatible hunks are included in merge commit
`abbb5e598ad989e0268c1d577a38da5dbca758c5`, not separate topic commits, because
version and lockfile conflicts were mixed release boundaries. The upstream PR
and source SHAs above retain original author/co-author attribution; they are
source references, not candidate commits. Upstream advisory descriptions are
not independent exploit verification.

Reported retained boundaries: stable 0.20.0 versions and graph/markers;
Windows-only `distlib` test dependency and launcher resources; Lightning CSS
1.33.0 parser override with stable unrelated upgrades; P7D cooldown and stable
uv floor. No wholesale main lock import, unused Databricks installation,
TLS/registry workaround, new dependency-floor waiver or approval label.

The report's 19 dependency static checks passed and were rerun by the
coordinator. Frozen pnpm installation with lifecycle scripts disabled also
passed. The initial Node test attempt failed at module loading because
`typescript` was missing; this was superseded by the successful bounded Node
lint/Vitest results in the current snapshot above. None of these observations
is resolver, Python, or hook acceptance. Full lock consistency, applicable
resolver checks, broader tests and hooks remain pending. Associated CSV gates
therefore stay pending.

Larger post-tag terminal protocol, observer, lifecycle, policy-cache and picker
changes are not imported as a bundle. In particular, raw tmux query-reply
changes do not justify modifying captured psmux output; observer keyword changes
need actual target API evidence; future watchdog/Stop settlement and open PRs
are not completed stable fixes. Research snapshot
`9006942724baeafccbc54a042145b9538b5c0637` is not a merge target.

## Validation and artifact truth

| Source / selection | Evidence and limit |
| --- | --- |
| Historical exact source `430ea3caabec09ff894e92c0c03bfe029361418e` | Previously source-matched fork CI run **39752878340**: Linux/Windows contracts and release/artifact checks; historical source evidence only |
| Same historical source | Lint/version run **39752878264**; not candidate lint/version evidence |
| Earlier v0.19 baseline `6a7c711308587a2c39dd916c0820af71debfbb67` | Historical final release/lint evidence indexed by the maintained skill; not validation of source430 or this merge |
| Verified branch HEAD | `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`; round-1 results and in-progress checks are summarized above; runtime acceptance remains pending |
| Baseline/candidate comparison | Baseline source-matched to `430ea3caabec09ff894e92c0c03bfe029361418e`; baseline and candidate use independently locked environments; historical baseline-first pair is unchanged |
| Documentation scope | This record and its current-status paragraph only; coordinator code/test/workflow repairs are separate in-progress work |
| Dependency worker/coordinator | Nineteen static checks passed and were rerun; frozen pnpm install passed; resolver/Python/hooks remain unverified |

Historical CI identifiers were recovered from the source-matched handover;
they were not refreshed online in this task. No historical run is relabeled as
current-HEAD evidence. Integration and Docker passed on exact SHA
`9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`; later source changes are not
covered by those runs. Evidence for unchanged input closures may be reused
only when its scope is explicitly recorded.
No new CLI/desktop bundle, clean-wheel import, source metadata, core/client/UI
version import, signing or architecture check has been accepted. An old bundle
with a release-like filename is not a current candidate artifact.

Remaining coordinator gates and limits at verified HEAD
`9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`:

1. Review combined conflict resolutions and all clean-merge contracts, including
   factory kwargs, copy-on-write identity, correlation resets, runner-secret
   exclusion, wrapper order and failed/unregistered launch cleanup.
2. In an explicitly authorized source-matched environment, check lock consistency
   (`uv lock --check` and frozen pnpm consistency) before locked installation.
   Investigate rejection rather than silently regenerating or upgrading locks.
3. Use current dependency groups, not obsolete `--extra dev`. The dependency
   worker proposes `uv sync --locked --group dev`; verify actual target groups
   and import identity in the permitted environment. Never retry denied local
   Python through another command, tool or replacement environment.
4. Run vulnerability guards, version/resources and focused backend/Windows
   contracts with retries disabled; real psmux serially with private state.
   Audit collected nodes/markers and preserve the historical baseline pair.
5. Let the already-running backend and UI checks finish; do not stop them or
   dispatch duplicate E2E. Integration and nonpublishing Docker already passed
   on `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`. After the repair and docs are
   committed, the planned next round pushes the branch (triggering fork
   validation) and dispatches **lint only**. Record the resulting exact SHA and
   raw summaries; do not treat earlier runs as proof for changed source.
6. Only after matching gates pass, inspect SHA-matched CLI/desktop artifacts and
   perform disposable packaging/install checks and the human acceptance below.

No local Python, pre-commit, hook bypass, replacement environment, WSL,
publication, main-branch change, or installer action is authorized or attempted.
Independent bounded checks do not clear those restrictions. Raw private
evidence stays outside the tracked tree; do not commit transcripts, credentials
or demo captures.

## Shared permission and attempt ledger

The integration's shared budget is **six push/retry rounds; 1 used, 5 remain**.
It is shared across coordinator, workers and handovers. Documentation-only
pushes count; checks dispatched together for one SHA count as one round. Record
the exact candidate SHA and round before any later authorized push/dispatch.
Reserve the final round for source-matched handover; no unlimited retries or
budget reset on model/session change. Old v0.19 four-round limits are history.

| Round | SHA | Push / Actions | Outcome | Remaining |
| --- | --- | --- | --- | ---: |
| Round 1 | `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c` | Push and source-matched Actions | Fork **41067491820** failed at YAML/AST before jobs; lint **41067493114** completed with the findings listed above; integration **41067497520** and nonpublishing Docker **41067511450** passed. Backend **41067506812** and UI **41067501570** remained in progress at the latest snapshot. | 5 |
| Round 2 planned (not consumed) | Repair-and-docs commit SHA pending | Commit repairs and this documentation, push for automatic fork validation, and dispatch **lint only** | Await coordinator action; do not stop the running backend/UI checks or duplicate E2E. | 5 |

The coordinator handles the planned repair-and-docs commit, branch push,
automatic fork validation, and lint-only dispatch within this shared budget.
No publication/image push, main PR/promotion or main-branch mutation,
force/history rewrite, schedule activation, real installation mutation, global
setting change, WSL, local Python, pre-commit, replacement environment or
excluded-content read is permitted.

## Human checks and non-destructive rollback

These are future acceptance instructions, not completed checks. Do not use the
unvalidated candidate against real user state.

1. After an authorized build, select the artifact whose metadata and run head SHA
   match the candidate commit. Extract to a disposable directory and launch its
   executable by **absolute path**, not a possibly stale PATH entry. Inspect
   `Get-Command omnigent -All` to identify competing installations; confirm the
   selected version/source and use that instance's printed UI URL. No exact
   candidate artifact path or URL exists yet, so none is invented here.
2. Use fresh isolated config/data and a fresh database. Back up real config/data
   before any approved migration. Exercise a workspace on another drive with
   spaces and Unicode; check breadcrumbs, worktrees, full path title and session
   selection without normalizing away drive information.
3. Start fresh supported Claude/Codex/Copilot sessions using available economical
   models. Check trust/startup, terminal rendering, cursor, Escape and resize.
   Send `Reply exactly: parity ; %PATH% Å` and confirm one matching reply.
4. Keep two owned native panes open. Exercise short, Unicode multiline and large
   paste payloads; confirm delivery only to the intended pane, then switch
   Terminal/Chat and resume without manually waking the terminal. Real psmux
   checks use private state and serial execution, never global process cleanup.
5. In a native PowerShell session run `Start-Sleep -Seconds 30`, use **Stop
   Session**, then send another chat message. Separately test interruption and
   resume; neither substitutes for Stop or desktop Quit.
6. Keep an independently started CLI instance alive, quit the candidate desktop,
   and verify only desktop-owned descendants exit while the independent CLI
   survives. Confirm close failures remain visible and replacement bridges are
   not deleted by stale owners.
7. Verify small image and ZIP reads, reuse and Stop/resume in the **actual vendor
   sandbox**. Mock cache tests, setup-only Claude capture and Job Object cleanup
   do not establish this acceptance or enable unsupported isolation/signing.
8. For any separately authorized installer test, use disposable prefixes and
   isolated PATH state; check argument refusal, cert-setting restoration,
   idempotent install/uninstall and all resolved executable paths. Do not modify
   the real installation merely to verify this integration.

Rollback remains the unchanged source checkout
`D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v019-isolation` at
`430ea3caabec09ff894e92c0c03bfe029361418e`, recoverable through
`backup/windows-v019-isolation-before-v020-20261030`. Use an explicitly identified
previous source/artifact with its original isolated state. **Never point the
older app at a database migrated by v0.20 without restoring its matching backup.**
Do not reset/clean another worktree, move the backup, rewrite published history,
alter main or the installed application, or terminate unowned sessions. The
stable merge is already committed; do not reset or rewrite it as a rollback.
Coordinate preservation before any separately authorized rollback.

Next handover: coordinator commits the code repair and documentation, then
pushes for automatic fork validation and dispatches lint only (round 2; not yet
consumed). Let the existing backend/UI runs finish; do not duplicate E2E.
Record the resulting commit SHA and source-matched results when available. The
322-path accounting is complete; **candidate validation and runtime/live
acceptance remain pending**.