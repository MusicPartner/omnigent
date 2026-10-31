# Upstream direction after v0.20.0: Windows integration

## Maintenance decision update — 2026-10-31

This section supersedes the historical candidate/state snapshots below. Final
release a676 passed fork41088395617/lint41088396527. Current maintenance is a
separate, uncommitted branch at that baseline, not a new validated release.
See [isolation record](ISOLATION-PLAN-0.20.md). The upstream review was pinned to
`8ceb87942b07f1f6135ab87fbe69af796af2bbcd`; development main is direction only.
Read-only `gh` refresh at `2026-10-31T11:12:06+01:00` confirmed the first eight
rows below (#12335 through #12414), including immutable merge pins for merged
PRs and observed heads for open PRs. The remaining rows retain the earlier
October31 review; they were not refreshed in this final batch.

| PR / reviewed state | Immutable reviewed pin | Separation decision |
| --- | --- | --- |
| #12335 merged, wide composer | `e68446c012a1b3c80b1aff140d3e8326841fcae4` | Keep pure parser shared; no competing fork parser module. |
| #12344 merged, repaint | `553d49ec1fa05c4a303f56a48d2be65a94409a5e` | POSIX discovery returns zero on Windows; do not invent supported repaint. |
| #12394 open, clear-hold/repaint/order | `a310587b71e22df1d65863b53af4b924c8b9d548` | Isolate only psmux load-buffer addressing; clear/submit/cancellation stay shared. |
| #12330 merged, retire fence | `c26c74cc35df508267d334610b27a77af59fe606` | New post-read behavior, not a sem-neutral extraction. Defer adoption. |
| #12331 merged, stale callbacks | `b2c7acb7f5672722b6b72a5a313c8ea795dbbc23` | Keep instance identity at publication; reconcile behavior separately. |
| #12259 open, confirmed interrupt | `8075349df826e28d89f3144ddfa475e56bd50baa` | Escape injection is not confirmed idle or Stop. |
| #5554 open, stalled output queues | `22d35b88c3875ff7e2cfa0af13be2ba9df80d5d1` | Updated head; raw queue policy is not captured-grid transport. |
| #12414 open, attach retry | `fa9181530558a8874a976f2c7de9e85728543aa8` | Keep attachment lifecycle separate from mux command execution. |
| #12080 merged, managed MCP | `57fcefe0cbd575c5bea536a840df103d6528b9a8` | Keep canonical managed config and tool-availability consequences. |
| #12355 merged, SDK worker catalog | `1504b908851a64c54c90ab693b4c4ad8c3132c51` | Shared child launch/catalog owner; no Windows worker framework. |
| #12406 open, managed Codex provider | `2d6753bac0d2cb4a318cbfe3b6e6a92465b9daf5` | No speculative provider policy extraction. |
| #12385 merged, Pi turn budget | `d6c6822a63e001bde2eddf26fe9ec7cdbd227b5f` | Future timeout keywords must retain actual shell and owned cleanup. |
| #12339 closed, not merged | `26552c496c7436447bbc71e901295d600fbea19c` | Synthetic merge SHA is not merge proof; no accepted timeout fix. |

Desktop #12305/#12306/#12307 form an identity/network-policy dependency chain;
do not take an isolated localhost relaxation. #12411 long tools and
#12418/#12417/#12403 session/sandbox direction do not justify a new global
Windows lifecycle or sandbox abstraction. No listed PR behavior was backported
by this maintenance task. Recheck state, ancestry and owning code before the
next stable release integration. Shared hooks and `_run_tmux`/`_capture_pane`
facades retain existing cancellation/error/test-injection contracts.

## Historical October30 review

Recorded **2026-10-30**. This is a bounded compatibility assessment and
next-release watchlist. The v0.20 integration is committed, but candidate
validation and runtime acceptance remain pending; this is not permission to
merge main.
See the [integration record](RELEASE-INTEGRATION-0.20.md) and
[per-file ledger](RELEASE-INTEGRATION-0.20-ledger.csv) for reconciliation status.

## Decision: exact stable plus narrow security backports

The authorized integration is a history-preserving merge of exact upstream
**v0.20.0** onto the latest validated Windows application source. The user
authorized autonomous integration decisions, not wholesale adoption of unreleased
features. This documentation update does not implement any of the future
changes described below.

| Role | Immutable reference |
| --- | --- |
| Latest validated fork source | `430ea3caabec09ff894e92c0c03bfe029361418e`, `windows-parity/v0.19-isolation-p1-p2` |
| Exact stable target | `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee`, upstream `v0.20.0` |
| Stable integration merge | `abbb5e598ad989e0268c1d577a38da5dbca758c5` (parents are source and target) |
| Terminal/test follow-up | `806c7ce308dbfe970ebc402dcac59db9c18cf652` |
| CI follow-up / current candidate HEAD | `eabd86b032ad12e80131b12e2b3b91f9e099e72b` |
| Previous stable / semantic comparison base | `d43340fec4e7d2d767f319d715e84aa82f4d1bc8`, upstream `v0.19.0` |
| Actual source/target Git merge base | `71fb9694ecf4b54b37919fbb1acd575dfd28243f` |
| Upstream main research snapshot only | `9006942724baeafccbc54a042145b9538b5c0637` |
| Selected worktree / branch | `D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v020`, `windows-parity/v0.20-integration` |

The merge is committed, followed by the terminal/test and CI commits above;
there is no current `MERGE_HEAD` or unmerged index state. The recovered release
lookup identifies v0.20.0 as non-draft/non-prerelease, published
`2026-10-28T05:48:51Z`; that release lookup was not refreshed here.

The research inventory from stable target to the pinned main snapshot contains
**291 PR-tagged commits, 1,330 changed paths and 85 cumulative-fork path
overlaps**. These are recorded ancestry/inventory counts, not 291 independently
reviewed changes. Selected diffs and overlapping contracts received targeted
semantic review; this document does not claim exhaustive main coverage.
Release-publication timestamps alone do not define that ancestry range.

Taking all main would enlarge the tested baseline with terminal protocols,
policy caching, question UI, lifecycle and launch APIs that are not in the
chosen stable release. Instead:

- Retain the source P1/P2 characterization and shared launch preparation.
- Reconcile against stable owners first; do not restore obsolete fork policy.
- Include only the two separately attributed dependency-security backports
  below. Other changes remain watchlist/deferred unless a stable-target defect
  is demonstrated and a narrow reconciliation is justified.
- Preserve the fork's manual-only/no-schedule administrative policy. A newer
  workflow-only main commit is not a newer Windows application basis.

Historical source [fork gate 39752878340](https://github.com/MusicPartner/omnigent/actions/runs/39752878340)
and [lint/version gate 39752878264](https://github.com/MusicPartner/omnigent/actions/runs/39752878264)
were recorded successful for **430ea3ca**, including source Linux/Windows
contracts and CLI/desktop artifacts. They were not refreshed in this task and
**do not validate the v0.20 candidate**, its security hunks or future work.

## PR state evidence

All 22 selected PRs below were rechecked through read-only GitHub REST API
calls to `repos/omnigent-ai/omnigent/pulls/{number}` during
**2026-10-30T13:05:18Z–13:05:35Z**. The returned fields were number, title,
state, merged, head SHA, merge SHA, merged time and updated time. There were
no failed lookups in that batch. These are **dated lookup snapshots**, not a
promise that an open PR remains open when this document is read later.

For merged PRs the immutable pin below is the API merge commit, not a mutable
branch. For open PRs it is the observed head commit; an API synthetic
`merge_commit_sha` is not evidence that the PR landed. Recheck state and
ancestry before any later adoption, even if a proposal subsequently merges.

### Merged at lookup: security, compatibility and feature dependencies

Every row returned `state=closed`, `merged=true`. Times are UTC.

| PR | Topic | Immutable merge SHA | Merged at |
| --- | --- | --- | --- |
| [#12041](https://github.com/omnigent-ai/omnigent/pull/12041) | MLflow, msgpack, qs security pins | `7f1cf6fde9c022c92144f15f5e2167df7ae3c298` | 2026-10-28T20:13:32Z |
| [#12260](https://github.com/omnigent-ai/omnigent/pull/12260) | brotli, virtualenv security pins | `af1a57ffa89716e16f3a315fe89ee13fb3847c75` | 2026-10-30T03:49:01Z |
| [#11495](https://github.com/omnigent-ai/omnigent/pull/11495) | Terminal query double-answer prevention | `916887faecc1426af2f556697e88d430f352cbaf` | 2026-10-29T12:10:29Z |
| [#12115](https://github.com/omnigent-ai/omnigent/pull/12115) | Raw control-bridge command echo | `3800f0a6ecd7d5a47de77b6d1c2eeb7686dee5e0` | 2026-10-29T08:50:36Z |
| [#12092](https://github.com/omnigent-ai/omnigent/pull/12092) | Shell no-policy ALLOW cache | `3102870ce6ca022a577eaf0beadb851e3c995b31` | 2026-10-29T09:29:33Z |
| [#12103](https://github.com/omnigent-ai/omnigent/pull/12103) | curl observer transport / `wrap_python` | `a45a3442b5b700f118a68b51f85b66919507b7e9` | 2026-10-29T09:54:59Z |
| [#12290](https://github.com/omnigent-ai/omnigent/pull/12290) | Claude Bash-tool tmux isolation | `416e082889c6f879b4995cfc69aef4ff0658313a` | 2026-10-30T07:02:36Z |
| [#11995](https://github.com/omnigent-ai/omnigent/pull/11995) | Codex forwarder cleanup after failures | `6305bf5120bdbeebbb22263ae41198ffe4d4f8b6` | 2026-10-28T20:39:55Z |
| [#12146](https://github.com/omnigent-ai/omnigent/pull/12146) | Codex app-server thread-lock retry | `f22428f77c7c6e8959549a0a429a48fce79b01f5` | 2026-10-29T21:21:59Z |
| [#12200](https://github.com/omnigent-ai/omnigent/pull/12200) | Native idle-pane reaper | `cdb863459c3eab56a5ddeb1508300378137cfc1b` | 2026-10-29T21:03:31Z |
| [#12150](https://github.com/omnigent-ai/omnigent/pull/12150) | Stop settles Claude turn as cancelled | `34960c7ade68b3323a060778de195fb07b09180e` | 2026-10-29T22:47:46Z |
| [#12153](https://github.com/omnigent-ai/omnigent/pull/12153) | Active-work idle-watchdog hold | `f7d67db5b5ad67beb6a74b3a391fee131e97338d` | 2026-10-29T21:20:58Z |
| [#12077](https://github.com/omnigent-ai/omnigent/pull/12077) | Client-surface launch forwarding | `4996cc7278b3991b227f212f5eea82dea4cb8c54` | 2026-10-29T07:01:30Z |
| [#11992](https://github.com/omnigent-ai/omnigent/pull/11992) | Isolated sandbox launcher imports | `94d3f3b0fc690f665d03b1b6cfd82a0618bfddb9` | 2026-10-28T18:14:56Z |
| [#11369](https://github.com/omnigent-ai/omnigent/pull/11369) | Workspace picker / Electron chooser | `21dbacd031c261deb6f55baeb388ed0de82515f7` | 2026-10-28T13:25:51Z |
| [#12138](https://github.com/omnigent-ai/omnigent/pull/12138) | AskUserQuestion hook-failure denial | `e945cb9796e6e8aad41cfcd4c81b15999fb17e1b` | 2026-10-29T09:16:38Z |
| [#7403](https://github.com/omnigent-ai/omnigent/pull/7403) | AskUserQuestion clickable-options feature | `1d239a2e3a732a4b734a7f43963e459ca910babf` | 2026-10-29T07:58:47Z |

### Open at lookup: proposals, not accepted fixes

Every row returned `state=open`, `merged=false`, with no merged time. All
observed heads still matched the earlier research snapshot. Updated times are
API metadata, not test or acceptance evidence.

| PR | Proposal | Immutable observed head SHA | Updated at (UTC) | Disposition |
| --- | --- | --- | --- | --- |
| [#12259](https://github.com/omnigent-ai/omnigent/pull/12259) | Confirm interrupt completion / report busy delivery | `8075349df826e28d89f3144ddfa475e56bd50baa` | 2026-10-30T12:10:25Z | Research only; interrupt acknowledgement must not imply Stop completion |
| [#12339](https://github.com/omnigent-ai/omnigent/pull/12339) | Preserve working pane after follow-up timeout | `26552c496c7436447bbc71e901295d600fbea19c` | 2026-10-30T12:32:30Z | Research only; test timeout without destroying active work |
| [#12344](https://github.com/omnigent-ai/omnigent/pull/12344) | Repaint launcher-hosted Claude outside pane | `bf8bc36cf3c8b2c671eea7ad79141467eebea7dd` | 2026-10-30T11:04:13Z | Research only; distinguish launcher ownership from captured-grid fidelity |
| [#5554](https://github.com/omnigent-ai/omnigent/pull/5554) | Bound stalled terminal output queues | `a1b47ea4c365284e1a3509e782e31fe8c6a83989` | 2026-10-30T09:21:02Z | Research only; prove bounded memory, ordering and cancellation per backend |
| [#12355](https://github.com/omnigent-ai/omnigent/pull/12355) | SDK worker catalogs / child launch routing | `ee5f60505fd114e52cb31c8babf5fda32a56fff3` | 2026-10-30T11:56:44Z | Research only; preserve actual selected harness/model and child launch inputs |

## Security backports: minimal hunks in the stable merge; validation pending

The dependency worker's external `dependencies/REPORT.md` and the integration
record identify the following target-compatible hunks in merge commit
`abbb5e598ad989e0268c1d577a38da5dbca758c5`. They are committed candidate
changes, not validated security results. The live PR lookup above confirms
upstream merge state, not the correctness of the local backport.

| Original PR / SHA | Stable pins → committed candidate pins | Other scoped changes |
| --- | --- | --- |
| #12041 / `7f1cf6fde9c022c92144f15f5e2167df7ae3c298` | MLflow / mlflow-skinny / mlflow-tracing 3.16.0 → 3.17.2; msgpack 1.2.1 → 1.2.3; qs 6.16.0 → 6.16.1 | Remove five expired uv cooldown exemptions; update existing vulnerable-pin guards |
| #12260 / `af1a57ffa89716e16f3a315fe89ee13fb3847c75` | brotli 1.2.0 → 1.2.1; virtualenv 21.14.7 → 21.14.13 | Extend the same guard file; preserve target dependency edges/markers |

Owner paths are `pyproject.toml`, `uv.toml`, `uv.lock`,
`pnpm-workspace.yaml`, `pnpm-lock.yaml` and the existing
`tests/e2e/test_lockfile_vulnerable_pins.py`. Retain stable 0.20.0 core/SDK
versions, Windows-only distlib test dependency and launcher resources, the fork
Lightning CSS 1.33.0 override, P7D cooldown and the stable uv floor. Do not copy
main's locks wholesale, install unused Databricks support, weaken TLS/registry
policy or invent a dependency-floor approval.

Both upstream commits attribute Lee moon soo, with Isaac as co-author. Their
original PRs and immutable source SHAs are recorded above and in the integration
record; the candidate hunks live inside the merge commit, not separate topic
commits. This preserves their source attribution without implying separate
candidate commits. Nineteen dependency static checks passed and were rerun by
the coordinator. Frozen pnpm installation with lifecycle scripts disabled
passed; native Node lint passed 67 checks and focused Vitest passed 822 tests
across 3 files. YAML parsing passed for all 95 workflow files with `yaml` 2.9.0.
These checks do not establish resolver, full-hook, Actions, runtime or security
acceptance.

**Still pending:** full manifest parsing, uv lock consistency, frozen pnpm
consistency, locked installation, vulnerable-pin tests, package-resource/version
checks and required hooks in an authorized source-matched environment. Upstream
reports security advisories, including critical findings for #12041; advisory
applicability, exploitability and remediation have **not been independently
verified here**. A version guard alone does not establish a security clean bill.

## Compatibility decisions and next-release acceptance

Paths below identify concrete workstream owners, not individual assignees.
Upstream-only files/tests are **future landing points**, not claims that exact
stable already contains them. Selected commit path metadata was checked here;
the semantic decisions come from the targeted release research, not a new
exhaustive code audit. Reuse existing scenarios/primitives and retain both
stable and fork assertions when these topics actually land.

### 1. Terminal replies: raw tmux is not a psmux captured grid

**#11495, #12115 — defer broader protocol adoption.** Raw tmux control output
uses `control_bridge.py`, with #11495 adding `query_replies.py` and browser
`TerminalQueryReplies`. It announces `tmux-replies` before output, probes real
tmux through sh/stty and discovers supported reply capabilities instead of
guessing by version. #12115 fixes command echo in that same raw stream.

Windows uses `omnigent/terminals/capture_bridge.py` and captured screen grids,
not tmux's raw control stream. Preserve no-announcement/default browser replies
for this path. **Do not suppress psmux browser replies because tmux can answer
queries**, blindly replace the capture bridge or claim raw PTY parity. The
[capture fidelity boundary](psmux-browser-attach.md) remains in force.

- Owners: `omnigent/terminals/{control_bridge,capture_bridge,psmux}.py`, future
  `query_replies.py`, `web/src/components/blocks/TerminalSession.ts` and future
  `TerminalQueryReplies.ts`.
- Tests: `tests/terminals/test_control_bridge.py`, future
  `test_query_replies.py`, existing `test_windows_psmux.py`, colocated
  `TerminalSession.test.ts` / future `TerminalQueryReplies.test.ts`, and
  `tests/e2e_ui/windows/test_psmux_terminal_evidence.py`.
- Acceptance: prove announcement-before-output and single replies on raw tmux;
  prove absent-announcement/default replies on captured psmux; verify command
  input is not echoed/corrupted, plus resize, detach/reconnect, dead panes and
  two-pane Unicode/multiline/large paste. Run real psmux serially with private
  state; do not reinterpret a captured grid as protocol bytes.

### 2. Canonical hooks, future keywords and tool-only environment

**#12103 — future adapter transport, not duplicated hook policy.** Keep
canonical hook composition in `omnigent/native/tool_observer_hook.py` and
Claude lifecycle/readiness/settings in
`omnigent/harnesses/claude_native/bridge.py`. Windows transport belongs in
`windows_hooks.py`. The new `wrap_python` keyword and POSIX shell/curl/here-doc
fallback must not be executed as cmd or PowerShell source. Transport the
canonical command through a supported consumer or an explicit supported
fallback, retaining loopback no-proxy behavior and keeping tokens out of
argv/logs. Update observer/test-double kwargs only when the target API requires
them; do not add a speculative production API now.

**#12290 — audit before any small backport; otherwise defer.** Its packaged
`omnigent/resources/scripts/claude_tool_env.sh`, wired by
`omnigent/harnesses/claude_native/main.py`, uses `CLAUDE_ENV_FILE` to unset
`TMUX`/`TMUX_PANE` **for Bash tools only**, preserving a user-supplied env-file
value. It is not whole-pane environment sanitization. Do not strip TMUX from
the entire Claude/Codex pane; native behavior needs that context. Windows Bash
consumer invocation remains an adoption gate.

- Tests: `tests/native/test_tool_observer_hook.py`,
  `tests/harnesses/claude_native/test_claude_native_windows_hooks.py`,
  `test_claude_native_bridge.py`, `test_claude_native_slow_ready.py`,
  `test_claude_native.py` and `tests/runner/test_app_claude_native_launch_args.py`.
- Acceptance: spaces/Unicode/quotes/JSON and literal argv across actual shell
  consumers; required kwargs reach observers; unsupported consumers fail
  explicitly; secrets stay redacted. Assert Bash-tool TMUX removal while pane
  context and user `CLAUDE_ENV_FILE` survive, including native Codex behavior.

### 3. Policy cache and sandbox imports stay fail-closed

**#12092 — defer the cache feature, retain canonical policy ownership.** A
shell fast-path ALLOW is safe only with correct session generation,
invalidation and `sys_add_policy` mutation guarding. Windows must not maintain
an independent permissive implementation or bypass refusal after policy changes.

**#11992 — compatible import direction, not extra Windows isolation.** Its
`omnigent/sandbox/copy_on_write.py` launcher import work must preserve isolated
startup without site packages while unsupported Windows isolation remains
refused. Job Objects are containment/cleanup, not filesystem/network isolation;
brokered signer/Git SSH/unsupported sandbox boundaries stay fail-closed.

- Owners/tests: future `omnigent/native/policy_allow_cache.py` and
  `tests/native/test_policy_allow_cache.py`; canonical
  `omnigent/runtime/policies/builder.py`,
  `tests/runtime/policies/test_builder_session_policies.py` and future
  `tests/e2e/test_native_policy_allow_cache_e2e.py`; sandbox owner above with
  `tests/inner/test_copy_on_write.py`, `test_sandbox.py`,
  `test_sandbox_capabilities.py` and `tests/runner/test_enforce_sandbox_gate.py`.
- Acceptance: no-policy fast path, policy installation/mutation, generation
  changes and stale/malformed cache all exercise canonical evaluation/refusal.
  Test isolated imports separately from portable Windows refusal/security
  cases; do not skip those cases with Unix-only broker tests.

### 4. Codex cleanup and retry preserve replacement ownership

**#11995, #12146 — backport only for a demonstrated stable defect, not as a
bundle.** Owners are `omnigent/harnesses/codex_native/{forwarder,app_server}.py`,
`omnigent/inner/codex_executor.py` and
`omnigent/runner/native/orchestration.py`. Preserve deterministic close in
finally, owned-process identity, replacement bridge-directory ownership and
registration on close failure. A thread-lock retry must not delete or kill
the replacement server or an independent CLI.

- Tests: `tests/harnesses/codex_native/session/test_subscription.py`,
  `tests/harnesses/codex_native/test_codex_native.py`,
  `test_codex_native_process_registry.py`, `test_codex_native_windows_resume_lock.py`,
  `tests/inner/test_codex_executor.py` and
  `tests/runner/test_app_sessions_native_workflow_init.py`.
- Acceptance: failed forwarder tasks still clean up; launch-lock retry is
  bounded; close errors remain visible; an old owner cannot remove a new
  bridge or terminate a PID-reused/unowned process. Exercise real Stop/resume
  independently of mock subscription cleanup.

### 5. Idle, Stop and watchdog remain separate deferred runner work

**#12200, #12150, #12153 — defer broad lifecycle adoption until a release or
specific reproduction requires it.** Future owners are
`omnigent/terminals/pane_reaper.py`, `omnigent/runner/_entry.py` and
`omnigent/runner/app.py`; current Windows seams include
`omnigent/runner/native/interrupt.py` and native orchestration. Characterize
current Stop, interrupt/resume and desktop Quit separately. Do not treat a
successful interrupt signal as turn settlement or all-process teardown.

- Tests: future `tests/terminals/test_pane_reaper.py`, existing
  `tests/runner/test_runner_idle_active_work.py`,
  `test_app_sessions_native_events_lifecycle.py`, `test_native_interrupt_runner.py`,
  `test_codex_native_stop_teardown.py` and `tests/inner/test_windows_shutdown.py`.
- Acceptance: idle panes reap only when eligible; live work holds the watchdog;
  Stop settles cancellation and permits a later message; follow-up timeout
  preserves active work; desktop Quit kills only desktop-owned descendants.
  Keep an independently started CLI alive during the Quit check.
- Open #12259/#12339/#12344 and #5554 remain hypotheses for interruption,
  timeout, repaint and queue handling. Recheck their pinned proposals and test
  those exact boundaries before adopting any part; none is an accepted fix here.

### 6. Client-surface kwargs must follow the actual launch contract

**#12077 — future forwarding seam, not a speculative current API.** Owners
are `omnigent/telemetry/surface.py`, `omnigent/runner/resource_registry.py`,
`omnigent/runner/native/orchestration.py` and server session orchestration.
When adopting it, forward new surface kwargs through factories, observers and
injected test backends without dropping existing parent env, cwd, lifecycle,
correlation or program-status inputs. Keep shared preparation canonical in
`omnigent/inner/terminal.py` and registry launch; apply status wrapping once.

- Tests: `tests/terminals/test_backend_release_contract.py`, `test_registry.py`,
  `test_launch_failure_cleanup.py`, `tests/inner/test_terminal.py`,
  `tests/runner/test_resource_registry.py`, `test_app_sessions_native_terminals_runtime.py`
  and `tests/server/integration/test_session_host_launch.py`.
- Acceptance: Windows/POSIX factories and test doubles receive the same required
  inputs; parent environments remain copy-on-write; stale correlation and
  runner secrets are excluded; failed unregistered launches clean up; unknown
  psmux exit status stays unknown. Preserve the historical characterization
  pair; use separately source-matched dependencies/imports for a new comparison.
- Open #12355 stays research-only: verify catalog provenance, selected model
  and child routing without importing an unreviewed catalog/launch feature.

### 7. Picker/Electron changes preserve leaf dependency direction

**#11369 — defer the larger picker feature; retain Windows path contracts.**
`web/src/shell/hostPaths.ts` and `workspaceBreadcrumbs.ts` are leaf helpers.
They must not import `WorkspacePicker.tsx`; shared picker code imports leaves,
not the reverse. Future chooser changes belong in
`web/electron/src/folderChooser.js`, `main.js`, `preload.js` and
`web/src/lib/nativeBridge.ts`, not duplicated OS/path policy in the component.

- Tests: `web/src/shell/workspaceBreadcrumbs.test.ts`,
  `WorkspacePicker.test.tsx`, future `web/electron/test/folderChooser.test.js`,
  `tests/browser_ui/chat/test_workspace_missing_recovery.py` and
  `tests/e2e_ui/files/test_files_panel_header.py`.
- Acceptance: another drive, UNC/drive roots, spaces and Unicode survive
  selection, breadcrumbs, worktrees and native chooser round trips. Check the
  import cycle rule plus colocated tests; a future user-facing UI change needs
  its browser journey and noncommitted visual evidence as well.

### 8. AskUserQuestion denial is not a standalone stable backport

**#12138 depends on #7403**, the new clickable question/hook feature absent
from exact stable and the selected fork. Its merged state does not make the
fix independently applicable. Defer both; do not import the feature merely
to obtain its hook-failure fix.

- Future owners: `omnigent/inner/claude_sdk_executor.py`,
  `omnigent/server/ask_user_question.py` and
  `omnigent/runtime/harnesses/_executor_adapter.py`.
- Future tests: `tests/inner/test_claude_sdk_executor.py`,
  `tests/server/test_ask_user_question.py` and
  `tests/runtime/harnesses/test_executor_adapter.py`, plus a real question UI
  happy path when the feature is adopted.
- Acceptance: a failed/missing question hook denies rather than allowing by
  default, cancellation propagates, and actual answers route to the correct
  session. The security behavior and UI feature must be evaluated together.

## Unresolved gates and human verification

No Python, pre-commit, resolver, artifact, installer or live vendor checks ran
for this documentation assignment. Read-only PR states and owner metadata do
not establish those results. Existing denied local resources remain denied; no
replacement environment or alternative retrieval of excluded content is
authorized. `.gitignore` content was not read.

The candidate is `eabd86b032ad12e80131b12e2b3b91f9e099e72b`. It still needs
source-matched focused/full Windows and Linux contracts, locks/guards, hooks,
remote Actions, relevant integration/E2E/UI checks and artifact inspection.
Preserve the required blocking Windows gate, serial private psmux tests,
unknown-status semantics, canonical cleanup and precise platform skips. A
nonblocking green job, timeout or old-source pass is not candidate success.

After a separately authorized validated build, a human should select its
absolute executable path and SHA-matched artifact, use fresh isolated
config/data and its printed UI URL, then:

1. Select a workspace on another drive with spaces/Unicode; verify picker,
   breadcrumbs and worktree paths.
2. With two owned native panes, send `Reply exactly: parity ; %PATH% Å`, then
   multiline and large paste inputs. Confirm one reply in the intended pane,
   Terminal/Chat switching, reconnect and resume without manually waking it.
3. Run native PowerShell `Start-Sleep -Seconds 30`, use **Stop Session**, and
   send a follow-up. Check interruption/resume separately, then desktop Quit
   while an independent CLI remains alive.
4. Verify small image/ZIP reads, cache reuse and Stop/resume in the actual
   vendor sandbox. Mocks, setup-only Claude capture and Job Object cleanup do
   not close attachment, shell-consumer or isolation acceptance gaps.

Signing/architecture acceptance, actual hook consumers, vendor attachment reads,
captured-grid fidelity and identity-aware teardown remain explicit support
limits until demonstrated. Do not use the unvalidated tree against real user
state; back up before any approved migration and never downgrade onto a migrated
database without restoring its matching backup. Source
`430ea3caabec09ff894e92c0c03bfe029361418e` remains historical rollback evidence,
not a candidate result.

**Scope and budget:** this assignment edits only the three v0.20 integration
documents. No staging, commit, push, dispatch, publication, main promotion,
schedule change or installation mutation occurred. Round 1 is planned for the
documentation commit; its exact SHA remains unknown until the coordinator
commits. The shared budget remains **0/6 used, 6 remaining** until an actual
push; local documentation does not spend or reset it.
