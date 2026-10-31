# Fork maintenance workflows

This fork keeps the native Windows changes while continuing to ingest stable releases from `omnigent-ai/omnigent`.

For release integration and historical-contract recovery, use the maintained
[`omnigent-release-integration` skill](../.claude/skills/omnigent-release-integration/SKILL.md).
The [post-v0.19 isolation plan](../docs/windows/ISOLATION-PLAN-0.19.md) prioritizes
contract tests/primitives and shared terminal preparation before further
extraction. It is a plan, not permission to refactor or publish.

## Post-v0.20 maintenance (2026-10-31)

Current validated maintenance is
`e1714c416d2608f7bfd5bf4ea93ee81b108d7311` on
`windows-parity/v0.20-isolation-p3-p5`. All six source-labelled fork/lint/
backend E2E/integration/UI/nonpublishing Docker results are indexed in the
[current closeout](../docs/windows/ISOLATION-PLAN-0.20.md).
The selected worktree and live origin branch were reverified at e1714;
the old editor checkout and release checkout are preserved.

Continuation is approved with **five remote rounds**, shared across pushes,
corrections, documentation publication and validation rerun batches; **0/5
used** at the [P0 checkpoint](../docs/windows/ISOLATION-P0-2026-10-31.md).
P0 audits precede release tooling 4–6 and neutral extractions 7, 9 and 10.
Launcher item 8 and observable portability fixes remain separate. Shared
feature/status/lifecycle policy and main's manual-only automation stay
canonical. Historical paragraphs below do not restore exhausted permissions
or supersede the current acceptance limits.

Implementation topics and the allocated first publication/validation round
are tracked in the [current package record](../docs/windows/ISOLATION-PACKAGE-2026-10-31.md).
The OSC transport/liveness R fix was separately approved at P0; it is not
hidden inside neutral extractions. Remote results remain pending.

The completed release is `a67684ae0fc2299c8efc2e5f37824c71c8f044a6`:
[fork41088395617](https://github.com/MusicPartner/omnigent/actions/runs/41088395617)
and [lint41088396527](https://github.com/MusicPartner/omnigent/actions/runs/41088396527)
passed. CLI/desktop artifact inspection also passed; human/runtime/migration
and vendor-sandbox acceptance remain separate. The older snapshot below is
historical, not the current outcome.

The new `windows-parity/v0.20-isolation-p3-p5` worktree starts at that release.
See [current isolation record](../docs/windows/ISOLATION-PLAN-0.20.md) for the
five-iteration limit, uncommitted changes and verification gaps. Four shared CI
selection groups now have one literal argv owner; the Windows paste-load rule
uses the existing mux leaf. Shared composer/lifecycle/hooks remain canonical.
No main automation, automatic maintenance push trigger, release publication or
old release-branch edits were made. Maintenance Python/native acceptance has
not passed merely because the preceding release passed.

## Current automation policy (2026-10-30)

The v0.20 integration branch's round-5 snapshot is
`5bb6bfceda028cc4e6914493bc43470178f0bdcf`. Lint **41083128167** succeeded;
fork validation **41083128407** completed with both 37-test source/candidate
contract runs passing and focused Linux checks passing (content search: 24
passed, 1 macOS skip, 125 deselected; capture: 5 passed). Windows psmux 3.4.0
checks passed (real psmux 11, chat paste 16, parsing 1). The portable Windows
suite had 1,327 passes, 170 skips and 11 subtests; focused Windows regressions
had 21 passes. Linux portable/focused suites had 1,450/1,295 passes respectively.
Only the blocking broad Windows gate failed: JUnit
reports 4,576 suite-attributed tests but 4,552 testcase records (subtest
accounting), with 1 failure, 0 errors and 233 skips. Its fixture sets `HOME`
but not `USERPROFILE`; Windows `pathlib` therefore reads no gateway environment.
A final test-only fixture repair sets both independently and keeps the cases;
production code is unchanged. Artifacts were skipped pending this gate.

Round 6 is planned as the final authorized push (5/6 used, 1 remaining before
push; 6/6 afterward). Its SHA and result are not yet known. Do not spend a
seventh round or push another status-only update; place final exact-SHA results
in the external evidence record at
`D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-integration-20261030\FINAL-VALIDATION.md`.
Earlier UI, backend and Integration successes remain scoped to
`dfcf012803e7045cd25b29bee60f6184c9fac482`; the nonpublishing Docker success is
scoped to `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`. Runtime/artifact/human
acceptance remains pending. See the [integration record](../docs/windows/RELEASE-INTEGRATION-0.20.md),
[semantic ledger](../docs/windows/RELEASE-INTEGRATION-0.20-ledger.csv), and
[upstream direction review](../docs/windows/UPSTREAM-DIRECTION-0.20.md).
The optional upstream nonblocking Windows sweep is not a substitute for the
fork's blocking broader native Windows gate.

Preserve the workflow-only schedule removal at
`f9c0b39e004ffbe1261565d371866259716d0281` (19 paths) and the earlier
manual-only main policy below. The candidate removes all schedule declarations;
main-side automatic jobs are guarded without dropping non-main event interfaces
or changing existing dispatch inputs, reusable interfaces, or publication guards.
This does not authorize dispatch, publication, workflow reactivation, or promotion.

At the user's request, automatic triggers on `main` are disabled. The main-branch
workflow definitions are manual-only; reusable workflow-call interfaces and
existing manual inputs remain available. The workflow-only main commit is
`d8a23edf8b2e3f9531cfc70177b6a255a9415dbd`.

The v0.19 integration branch retains its own validation definitions. Its push
gate and explicitly dispatched lint, integration, E2E, UI and nonpublishing
Docker checks are separate from main automation. Do not re-enable main schedules
or push triggers when eventually promoting this branch. The flows described
below document the available maintenance design, not enabled main automation.

## Historical upstream release design (automatic main flow disabled)

1. `Sync upstream release` can be dispatched manually; its former daily schedule is disabled. It resolves the latest non-prerelease GitHub release from `omnigent-ai/omnigent`.
2. If that upstream release commit is already an ancestor of this fork's `main`, the workflow exits without changes.
3. Otherwise it creates `upstream-sync/<ref>-<run>`, merges the upstream release commit into that branch, and opens a PR to `main`.
4. The sync workflow explicitly dispatches `Fork release validation` on the sync branch. This is necessary because PRs created by the repository `GITHUB_TOKEN` do not themselves start ordinary PR-triggered workflows.
5. Review the upstream diff and merge the PR only after validation passes.
6. Automatic main validation remains disabled; a main merge is not permission to reactivate it or publish artifacts.

A merge conflict stops the sync workflow before it pushes a branch. The workflow summary lists the conflicted files so the integration can be resolved deliberately instead of silently preferring either side.

## Manual sync

Run **Actions -> Sync upstream release -> Run workflow**.

- `upstream_ref=latest-release` syncs the latest stable upstream GitHub release.
- `upstream_ref=main` syncs current upstream `main`, including unreleased commits.
- A tag such as `v0.15.0`, another branch, or a commit SHA can also be supplied.
- `target_branch` defaults to this fork's `main`.

The workflow always uses a PR; it does not push an upstream merge directly into `main`.

## Release validation

`Fork release validation` supports manual dispatch and selected integration-branch validation. Automatic main validation remains disabled. See the current v0.20 integration record and workflow for the candidate branch selection and pending acceptance gates.

On enabled integration validation events, compatibility checks run before artifact builds. The downloadable Windows artifact is deliberately built only for an allowed integration push or a manual dispatch, not every intermediate PR commit.

For v0.19, push the validated integration branch to run focused Linux checks and the required native Windows gate. A successful branch push also builds the Windows CLI bundle and Electron desktop ZIP; manual dispatch on the selected branch runs the same validation and artifact jobs. The upstream `Windows (native)` workflow remains an optional signal and does not replace the required fork Windows gate.

`Docker build` is separate and does not run on branch pushes. Dispatch it from the v0.19 branch for a server-image build and CLI smoke; `publish` defaults to `false` and must remain disabled unless image publication is explicitly authorized. See the [v0.19 integration record](../docs/windows/RELEASE-INTEGRATION-0.19.md) for pinned refs, reconciliation scope, current validation, and remaining acceptance limits.

The three stages are:

1. **Focused Linux compatibility**: Ruff plus the Windows integration surfaces and focused tests.
2. **Native Windows compatibility**: import/CLI smoke, upstream's hard Windows pair, the Windows-safe test subset, psmux installation/lifecycle tests, and the fork's required blocking broader Windows unit sweep. Only the separate upstream Windows sweep is optional and nonblocking.
3. **Windows artifact build**: production web UI build, core + lockstep SDK distributions, Twine metadata checks, bundled web UI and `omni`/`omnigent` entry-point assertions, clean wheel install, artifact-installer/uninstaller round-trip, checksums, and artifact upload.

Uploaded bundles are named `omnigent-windows-<commit-sha>` and are retained for 30 days. See `docs/windows/QUICKSTART.md` for installation, upgrades, local connection, and smoke testing.

## Housekeeping

`Fork housekeeping` has no weekly schedule and does not run automatically on main. Its manual interface describes two historical responsibilities; neither is authorized by this integration task:

- Disable upstream-only automation that is not useful in this fork, such as publishing/release, benchmark, reviewer assignment, doc-sync, merge-monitoring, and mobile bundle workflows. Core CI, Lint, E2E, E2E UI, native Windows, security/Trivy, and the fork workflows remain enabled.
- Delete same-repository branches matching `maintenance/*` or `upstream-sync/*` only after their PR has been merged and no Actions run is still active. Completed runs for those transient branches are also removed after the configured short retention window.

`main`, `windows-parity/v0.14-integration`, `windows-parity/v0.17-integration`, and `windows-parity/v0.19-integration` are explicitly protected by the housekeeping policy.

## Workflow ownership

The permanent fork-specific layer is intentionally small:

- `.github/workflows/upstream-sync.yml` — ingest upstream releases through a PR.
- `.github/workflows/fork-release-ci.yml` — focused Linux/Windows validation and the installable Windows artifact.
- `.github/workflows/fork-housekeeping.yml` — keep transient branches/runs and fork-irrelevant upstream automation under control.

Upstream's core test workflows stay available instead of being forked into custom copies. Integration logic is concentrated in these files; additive main guards in the other workflows preserve the fork's manual-only default-branch policy.

## Windows isolation topic map (v0.17)

Windows-specific mechanics live in leaf modules so shared modules keep only their `IS_WINDOWS` branch and a call to the helper. Code was extracted verbatim, so existing monkeypatch targets on the callers still work.

| Topic | Windows leaf module(s) | Caller seam (keeps the `IS_WINDOWS` branch) | Tests |
| --- | --- | --- | --- |
| psmux terminal backend | `omnigent/terminals/psmux.py` | `omnigent/terminals/backend.py` re-exports the psmux classes unconditionally | `tests/terminals/test_windows_psmux.py` |
| Web workspace breadcrumbs | `web/src/shell/hostPaths.ts`, `web/src/shell/workspaceBreadcrumbs.ts` | `web/src/shell/WorkspacePicker.tsx` re-exports them | `web/src/shell/workspaceBreadcrumbs.test.ts` (existing helper tests remain in `WorkspacePicker.test.tsx`) |
| Host listing | `omnigent/host/host_listing.py` | `omnigent/host/connect.py` (`_handle_list_dir`) | `tests/host/test_host_listing.py` |
| Runner python probe | `omnigent/runner/python_probe.py` | `omnigent/runner/environment_filesystem.py` (`_run_python_probe`) | `tests/runner/test_python_probe.py` |
| Command parsing | `omnigent/native/shell.py` (`split_command()`) | `omnigent/inner/acp_executor.py`, `omnigent/update_check.py`, `omnigent/native/_native_resume_hint.py` | `tests/test_native_shell.py` |
| Codex CLI | `omnigent/inner/codex_windows.py` | `omnigent/inner/codex_executor.py` (`_find_codex_cli`) | `tests/inner/test_codex_windows.py` |
| Claude CLI | `omnigent/inner/claude_windows.py` | `omnigent/terminals/psmux.py` (launch), `omnigent/inner/claude_sdk_executor.py` (`_find_system_claude`) | `tests/inner/test_claude_windows.py`, `tests/terminals/test_windows_psmux.py` |
| Native terminal control | `omnigent/native/mux.py` | Claude bridge, native attach/preflight, cost popups, WebSocket liveness select the platform mux | `tests/test_native_mux.py`, `tests/terminals/test_windows_psmux.py` |
| Claude hooks | `omnigent/harnesses/claude_native/windows_hooks.py` | `omnigent/harnesses/claude_native/bridge.py` (readiness/lifecycle policy stays here) | `tests/harnesses/claude_native/test_claude_native_windows_hooks.py` |
| Shutdown | `omnigent/inner/_windows_shutdown.py` | `omnigent/inner/_proc.py` (`terminate_tree`), `omnigent/runtime/harnesses/_runner.py` | `tests/inner/test_windows_shutdown.py` |
| Native env | `omnigent/runner/native/windows_env.py` | `omnigent/runner/native/orchestration.py` (`_claude_terminal_env_unset`) | `tests/runner/test_native_windows_env.py` |
| psmux readiness gate | `omnigent/terminals/psmux.py` (`native_terminal_supported()`: not Windows, or `psmux` on `PATH`) | `omnigent/onboarding/harness_readiness.py` (native harness availability and cache key), `omnigent/runner/native/orchestration.py` (start-error refusal payload), `omnigent/cli_common.py` (`reject_native_on_windows` guard) | `tests/onboarding/test_native_psmux_readiness.py`, `tests/onboarding/test_native_harnesses_windows_unavailable.py`, `tests/runner/test_native_psmux_gates.py`, `tests/runner/test_native_terminal_start_error_payload.py` |

Left in place on purpose:

- The runner transport locator and sandbox-capability seams.
- General (non-Windows) fixes: catalogs, SSE readiness, worktree error handling, and shared UI fixes.
- Upstream path helpers other than the four moved to `hostPaths.ts` stay in `WorkspacePicker.tsx`.

Rules:

- New Windows mechanics go into a leaf module, not a shared module.
- Psmux tests that monkeypatch `IS_WINDOWS` or `shutil` must patch `omnigent.terminals.psmux`.
- `workspaceBreadcrumbs.ts` and `hostPaths.ts` must not import `WorkspacePicker.tsx` (oxlint `import/no-cycle`).


## Windows launch follow-up (2026-10-08)

Claude npm shims now prefer the installed native executable in the psmux and
SDK paths. Claude bridge control, attach/preflight, cost popups, and terminal
WebSocket liveness select psmux on Windows and tmux on POSIX. Regression checks
cover both selections and a real psmux bridge round trip. The fork workflow and
stable Windows subset include the new coverage.

The latest failed [UI run](https://github.com/MusicPartner/omnigent/actions/runs/37820784465)
counted the expected undelivered-message notice as an assistant reply. Both
attempts' Claude transcripts contained exactly two replies. The corrected
assertion passed when replayed against the failed browser DOM and still rejected
a duplicated reply. The corrected reconnect journey passed on its first attempt
in the [new UI run](https://github.com/MusicPartner/omnigent/actions/runs/37828738534),
and all ten shards plus Browser Contract UI passed.
The [fork validation run](https://github.com/MusicPartner/omnigent/actions/runs/37828737400)
on revision `2d43e9d95` passed, including the Windows installer artifact.
[Docker](https://github.com/MusicPartner/omnigent/actions/runs/37829582487),
[Integration](https://github.com/MusicPartner/omnigent/actions/runs/37829587308),
and [E2E](https://github.com/MusicPartner/omnigent/actions/runs/37829592170)
also passed. E2E needed one retry of only shard 3 after a test-server port
collision; the same revision then passed all 202 tests in that shard.

Local focused validation: 587 passed, 2 skipped, and 6 Unix-only checks
were deselected. The previously failing exit-status assertion exposed a dependency
limitation: [psmux 3.3.8 hardcodes status and signal fields](https://github.com/psmux/psmux/blob/66cf613/src/format.rs#L1416)
to zero. The Windows backend and Claude bridge now leave the exit status unknown
instead of reporting successful completion. The real-psmux test confirms pane
death, exact argv, environment removal, and cwd; the standalone Python launcher
still must preserve exit status 37. The fix passed on its first attempt.

Deferred pending a clear caller contract:

- Replace sandbox `%*` batch forwarding: some callers accept only an executable
  filename, so a Python executable plus launcher arguments needs an API change.
- Select quoting by the consuming shell instead of the host OS, including popups.
- Automate the supplementary real-Claude capture across supported versions.
  Local Win32 capture on Claude 2.1.294/psmux 3.3.8 proved the settings-file
  path and full 6,822-byte inline JSON unchanged, plus exact Setup-hook argv,
  cwd and environment removal. In psmux 3.3.8, `pane_start_command` formats
  the default shell and cannot prove child argv.

The [remaining-work plan](../docs/windows/PARITY-NEXT-STEPS.md) records researched
launcher options, shell consumers, CLI compatibility choices, and the separate
Windows auth-provenance gap exposed by the non-blocking unit sweep. That sweep
timed out in a POSIX helper fixture; the required Windows checks still passed.
No ownership checks were bypassed and no blanket test skips were added.

To repeat the new Windows checks from this worktree:

```powershell
.venv\Scripts\python.exe -m pytest tests/inner/test_claude_windows.py tests/test_native_mux.py tests/terminals/test_windows_psmux.py -n 0 -p no:cacheprovider -q
```

For a manual bridge check,
start a Claude Code session on this Windows host, switch between Terminal and
Chat, send `Reply exactly: parity ; %PATH% Å`, and confirm one matching reply
and a connected terminal.
