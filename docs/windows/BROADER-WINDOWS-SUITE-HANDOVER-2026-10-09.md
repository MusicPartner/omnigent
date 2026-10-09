# Handover: fix and validate the broader Windows suite

Prepared 2026-10-09; historical handover retained. The broader selection is
now repaired and passes locally and in required Windows CI. Final source:
`e6a14a5e9dad093bebdf16809b70d22e9dccd61b`. The
[current findings](BROADER-TEST-FINDINGS-2026-10-09.md) record **3,786 passed,
187 skipped, 292 deselected and 10 passing subtests** in required CI, plus
completed local runs with **3,763 passed and 210 skipped**. Linux compatibility,
the dispatched integration matrix, all four backend E2E shards, Browser Contract
and all ten UI shards passed. Matching CLI/desktop artifacts were downloaded
and verified against the exact source; disposable installer/uninstaller smoke
passed. Artifact links and remaining human acceptance checks are in the findings.

The user capped additional repair/test attempts at **five**, then requires
stopping and waiting for approval if unresolved. The test work finished in
**four attempts**; the fifth remains unused. Do not reset the count if continuing
this same task. Databricks is not used, installed or enabled. Earlier native
Python crash causes remain unconfirmed; CI retains memory diagnostics and now
requires the full broader sweep. Preserve Windows signer refusal and live
attachment sandbox acceptance limits.

## Start here

Work in **`D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v017`**, branch
**`windows-parity/v0.17-integration`**. The other checkout,
`D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent`, is the agent's default
workspace, not the integration checkout. Always set the working directory
explicitly. The integration checkout can require an approved sandbox escalation
for writes, git operations, and native tests. Do not copy changes to the wrong
checkout to bypass that boundary.

At handover, HEAD is `47df14372` (release documentation); validated application
build is **`208591ece9026fd47f62f8ee8b4c2b77e5861a77`**. Attachment implementation
is `575754760`; the subsequent build commit only corrected Windows test owner
assertions and documentation. The checkout was clean before this handover file.
Recheck branch, HEAD and dirty state before editing; preserve any newer work.

Read the repository `AGENTS.md` and `CONTRIBUTING.md`, then:

- [Broader failure findings](BROADER-TEST-FINDINGS-2026-10-09.md): historical
  99-name inventory and reproduced causes; it is not the current failure count.
- [Parity/release evidence](PARITY-NEXT-STEPS.md): supported behavior, retained
  security boundaries, matching artifact links, and manual harness checks.
- [Attachment plan](ATTACHMENT-DELIVERY-PLAN.md): completed storage work,
  malicious replacement tests, and remaining live Codex sandbox acceptance.
- `.github/workflows/fork-release-ci.yml`, `scripts/windows_safe_pytest.ps1`,
  `tests/conftest.py`, and pytest configuration in `pyproject.toml`.

## Objective and user preferences

Fix genuine Windows regressions and portable fixtures, declare legitimate
platform-only tests precisely, and obtain a **completed** broader Windows run
with a trustworthy summary and evidence. A green Actions job containing
`continue-on-error` is insufficient. Discover failures beyond the old timeout
rather than stopping after the 64 already observed names.

Persisted user preferences:

- Delegate bulk investigation/implementation to cheaper agents: **GPT-6.1 Sol**
  (`gpt-6.1-sol`) or **GPT-6 Luna** (`gpt-6-luna`). Give each a separate file
  ownership area; root reviews security changes and integration.
- Keep changes contained for upstream upgrades. Review **original upstream
  `omnigent-ai/omnigent` main** and relevant issues/fixes before implementing.
  `origin` is the fork `MusicPartner/omnigent`; its `main` is not automatically
  evidence of current original upstream. Prefer narrow patches over refactoring.
- When implementation is finished, run hooks, commit and **push directly** to
  the integration branch; **do not create a PR**. Run Actions and wait for their
  terminal results. Build and verify matching CLI/desktop artifacts when code
  changes, following the existing fork workflow.
- Preserve the current local environment. Use the existing `.venv`; do not run
  local `uv sync` or dependency-installing `uv run` without a concrete need and
  authorization. CI already creates clean locked environments.
- Use native harness tools. Do not add a custom Claude streaming PowerShell tool.
  The Codex repeated administrator prompt was an incomplete setup and is solved;
  do not downgrade the sandbox or edit the user's global config as a workaround.
- Stop only test-owned processes and clean up only checked disposable paths.
  Do not stop the user's running Omnigent, harnesses, or sessions by process name.

## Evidence and present limits

[Release validation 37970056214](https://github.com/MusicPartner/omnigent/actions/runs/37970056214)
on `208591ece` passed both required OS gates and both Windows artifact jobs.
Required attachment results: Windows **109 cache/security + 35 consumer/resume
passed**, no skips; Linux **43 cache + 35 consumer/resume passed**, with 66
Windows-only skips. The attachment gap is already fixed; don't redo or weaken it.

The same run's **non-blocking broader sweep** recorded **64 FAILED node IDs**
before a **300-second hard timeout** in
`tests/inner/test_model_signer_lifecycle.py::test_cancelled_close_contains_worker_and_retains_incomplete_signer_cleanup`.
There was **no completed summary**. The timeout test is separate from the 64
recorded failures, and tests after it remain unverified. No attachment failures
were recorded in this partial sweep. Absence from its FAILED list alone does
not prove another test passed.

The exact CI invocation is:

```powershell
uv run pytest tests/inner tests/runtime/harnesses -m "not posix_only" -p no:cacheprovider -vv --tb=short
```

The existing script's stable subset is a different selection. Passing stable
checks or broad collection does not prove this broader execution passed.

Local preserved evidence (ignored, not committed; only available on this machine):

```text
D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent\.tmp\windows-attachment-release\
  run-37970056214-windows-job-113954086537.log
  run-37970056214-windows-job-113954086537.log.failed-nodes.txt
```

Completed job logs can be fetched if necessary:

```powershell
gh api repos/MusicPartner/omnigent/actions/jobs/113954086537/logs --allow-escape-sequences
```

An in-progress job's log endpoint can return 404. Keep logs outside tracked
source and avoid publishing credentials, payloads or private machine paths.
The exact latest partial failure inventory is included below so this handover
works without the local ignored files.

Other validation on production-equivalent feature source `575754760`:

- [Integration 37969521491](https://github.com/MusicPartner/omnigent/actions/runs/37969521491): passed.
- [E2E UI 37969530034](https://github.com/MusicPartner/omnigent/actions/runs/37969530034): Browser Contract UI and all ten shards passed.
- [E2E 37969525794](https://github.com/MusicPartner/omnigent/actions/runs/37969525794): passed after retrying only shard 3. Initial failure was a local-server HTTP baseline probe before FD exhaustion; fixture/forwarder code was unchanged. Retain this retry history.

These mock Linux journeys do not establish live Windows vendor/GUI acceptance.
The matching artifacts were inspected against source (12 Python/4 Electron
modules): CLI artifact **11635294449**, desktop artifact **11637425061** in the
release run above. Packaged native launcher candidate is still unsigned,
development opt-in; production `native` mode still refuses it pending signing.

## Recommended work order

1. **Unblock the signer lifecycle test before another full sweep.** Reproduce
   it alone with a short timeout. Its fixture advertises `/private/signer/...`,
   which Windows does not consider absolute. Readiness refusal then awaits its
   deliberately blocking mock `close()` (`asyncio.sleep(3600)`) before any worker
   starts. This does not exercise desktop Quit or the real signer's bounded
   process shutdown. Make the test reach its intended scenario using portable,
   isolated fixtures where the contract permits it. Examine failure cleanup as
   its own contract; do not merely remove readiness validation or hide the hang.
2. **Separate security refusal from platform fixture assumptions.** Codex
   private/signer home staging uses POSIX ownership/mode checks; Windows reports
   `0777` for directories. Preserve refusal unless a reviewed ACL/containment
   contract proves equivalent protection. The attachment ACL helper is not
   automatically a valid brokered-signer implementation or sandbox.
3. **Classify the other families using individual tracebacks.** Copy-on-write
   tests requesting `linux_bwrap` correctly encounter an unsupported backend.
   Staging/auth fixtures include POSIX chmod, ownership, Unix shell, symlink and
   process-group assumptions. Some policy/validation tests can remain portable;
   others genuinely require POSIX. The four Databricks cases have no confirmed
   root cause yet. Don't assume all failures share a cause or blame shutdown /
   PowerShell discovery without evidence.
4. **Delegate disjoint families.** Suggested first split: signer lifecycle /
   worker containment; Codex staging / executor / hooks / catalog; copy-on-write
   / authentication fixtures. Root manages shared test setup, security review
   and CI. Avoid simultaneous edits to `tests/conftest.py` or shared production
   helpers. Assign Databricks investigation once an agent slot is free.
5. **Keep a classification ledger.** For each failing node record reproduction,
   cause, upstream evidence, product fix versus fixture fix versus true platform
   scope, retained security assertion, Windows/Linux result, and open questions.
   Update the maintained findings document, preserving historical inventories.
6. **Run the full selection to completion.** Once the early blocker is resolved,
   inspect tests previously never reached. Use smaller independent runs to
   diagnose other hard timeouts; don't treat removal of the original blocker as
   complete-suite acceptance. Do not permanently deselect the timeout merely to
   obtain a green badge.

## Local reproduction and checks

Run commands from the integration checkout in PowerShell. No real credentials
are needed for the mocked reproductions. Native or real-provider acceptance
requires separate setup and must not borrow ambient credentials accidentally.
Use a fresh report directory per run:

```powershell
Set-Location 'D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v017'
git status --short
git branch --show-current
git rev-parse HEAD
$reportRoot = Join-Path $env:TEMP ('omnigent-windows-suite-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $reportRoot | Out-Null
$env:PYTHONUTF8 = '1'

# First blocker; a hard timeout may terminate pytest, so run it in its own invocation.
.\.venv\Scripts\python.exe -m pytest tests/inner/test_model_signer_lifecycle.py::test_cancelled_close_contains_worker_and_retains_incomplete_signer_cleanup -n0 -p no:cacheprovider -vv --tb=long --timeout=30 --junitxml "$reportRoot\signer-blocker.xml"

# Replace this example with the exact observed node under investigation.
.\.venv\Scripts\python.exe -m pytest tests/inner/test_codex_staging.py::test_staging_root_tightens_a_loose_preexisting_mode -n0 -p no:cacheprovider -vv --tb=long --timeout=30

# After focused fixes, broad collection catches import-time regressions.
.\.venv\Scripts\python.exe -m pytest tests/inner tests/runtime/harnesses -m "not posix_only" --collect-only -q -p no:cacheprovider

# Complete broad execution; capture the true exit code and summary.
.\.venv\Scripts\python.exe -m pytest tests/inner tests/runtime/harnesses -m "not posix_only" -n0 -p no:cacheprovider -vv --tb=short --timeout=60 --junitxml "$reportRoot\broader-windows.xml" *> "$reportRoot\broader-windows.log"
$suiteExit = $LASTEXITCODE
Get-Content "$reportRoot\broader-windows.log" -Tail 80
Write-Host "pytest exit code: $suiteExit; reports: $reportRoot"
```

A 60-second diagnostic timeout is not a reason to lower legitimate test runtime
requirements. A hard timeout can prevent JUnit output; preserve the log and
report incomplete execution honestly. CI currently uses the default 300 seconds.

`tests/conftest.py` isolates `OMNIGENT_DATA_DIR` before application imports; on
Windows it uses a unique profile-root directory to provide trusted ancestors.
Keep that isolation. For attachment/security test storage reuse reviewed private
fixtures rather than ordinary directories under a shared writable workspace.
Symbolic-link creation may skip only for actual Windows privilege error 1314;
GitHub's runner can execute those cases. Junction races and hard-link refusals
must still be exercised.

Before committing, run staged hooks after agents stop editing. Existing Windows
hook workaround (do not change project hook configuration just for the host):

```powershell
$env:PATH = 'C:\Program Files\Git\bin;C:\Program Files\nodejs;' + $env:PATH
$env:UV_NO_SYNC = '1'
$env:PYTHONUTF8 = '1'
$env:SKIP = 'pyrefly'
.\.venv\Scripts\pre-commit.exe run
.\.venv\Scripts\pyrefly.exe check --python-platform linux
```

The Pyrefly hook points at a Unix executable path; run the installed Windows
executable manually, using the existing project configuration. Re-stage and
rerun if hooks fix formatting/line endings. Prior session manually ran all hooks
and used `git -c core.hooksPath=NUL commit ...` only after they passed. Do not
skip verification just to commit. Clear the shell's `SKIP` when done.

## Validation and release completion criteria

- The exact broader Windows selection reaches a final summary and has no
  unexplained failures or hangs. Inventory collected/run/passed/failed/skipped/
  deselected counts and each intentional skip. A real unsupported backend must
  retain explicit refusal tests; markers require accurate reasons, not blanket
  family exclusion. Linux coverage for POSIX tests must remain active.
- Every changed family has focused native Windows and relevant Linux proof.
  Add meaningful tests for changed behavior, including failure/cancellation
  cleanup. Keep credentials out of argv/logs and require no worker spawn on
  failed containment/readiness. Do not loosen security assertions to pass mocks.
- Keep shutdown, native PowerShell, Stop/resume, attachment, private-job launcher,
  and terminal required checks passing. Do not add unproven brokered-signer
  Windows support, filesystem/network isolation, Copilot attachment capability,
  or unsigned production native-mode approval as incidental work.
- Add stable repaired cases to required CI where appropriate. Keep broad CI
  non-blocking during diagnosis; after complete native results and Linux parity,
  assess making that selection required. Do not use its normalized Actions
  conclusion as evidence or claim green while it still fails internally.
- Push directly, run fork release validation and any impacted Integration/E2E/UI
  checks, and wait for terminal results. Use failed-job retries only after
  diagnosis; record original failure and final attempt. Example dispatch:

  ```powershell
  git push origin windows-parity/v0.17-integration
  # Push triggers fork-release-ci.yml; dispatch only if a fresh run is needed.
  gh workflow run fork-release-ci.yml --repo MusicPartner/omnigent --ref windows-parity/v0.17-integration
  gh workflow run integration.yml --repo MusicPartner/omnigent --ref windows-parity/v0.17-integration
  gh workflow run e2e.yml --repo MusicPartner/omnigent --ref windows-parity/v0.17-integration
  gh workflow run e2e-ui.yml --repo MusicPartner/omnigent --ref windows-parity/v0.17-integration
  ```

  Avoid redundant release dispatches: branch concurrency cancels older runs.
  Documentation-only pushes do not trigger the fork release workflow.
- Download matching CLI/desktop artifacts from the successful source build,
  verify module/source metadata and installer smoke, and record links. Existing
  local verifier is under the other checkout's ignored
  `.tmp/windows-release-verification/verify.py`; inspect/update its module list
  for the actual changed files. Do not overwrite old evidence directories.
- Update this handover/findings with the final completed summary and remaining
  limits. Provide human verification steps: fresh Claude/Codex/Copilot session,
  timed PowerShell command, Stop Session and UI resume, desktop Quit, and an
  independently owned session that should remain alive. If attachments change,
  add image/ZIP/Stop/resume checks from the attachment plan; Codex sandbox ZIP
  read access remains live acceptance, not implied by cache unit checks.

## Latest observed failure families

Counts below cover only the 64 FAILED names emitted before the timeout.
They are observations, not a complete present-suite result or verified diagnosis.

| Test module | Recorded failures |
| --- | ---: |
| `tests/inner/test_codex_executor.py` | 11 |
| `tests/inner/test_codex_hooks_generation.py` | 8 |
| `tests/inner/test_codex_model_catalog.py` | 1 |
| `tests/inner/test_codex_staging.py` | 1 |
| `tests/inner/test_codex_worker_containment.py` | 5 |
| `tests/inner/test_copy_on_write.py` | 18 |
| `tests/inner/test_databricks_executor.py` | 4 |
| `tests/inner/test_model_auth.py` | 4 |
| `tests/inner/test_model_signer_lifecycle.py` | 12 |

## Exact latest partial failure IDs

```text
tests/inner/test_codex_executor.py::TestCodexExecutor::test_app_server_uses_isolated_codex_home_and_cleans_it_up
tests/inner/test_codex_executor.py::TestCodexExecutor::test_app_server_uses_workspace_cwd
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[omnigent/0.142.0-True]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[codex_cli_rs/0.154.0-True]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[None-False]
tests/inner/test_codex_executor.py::test_app_server_start_uses_real_home_for_private_inherited_codex_home
tests/inner/test_codex_executor.py::test_app_server_start_preserves_custom_home_from_inherited_private_symlink
tests/inner/test_codex_executor.py::TestCodexAppServerSessionHomeStaging::test_start_copies_skills_into_the_home_when_no_link_is_possible
tests/inner/test_codex_executor.py::TestCodexAppServerSessionHomeStaging::test_start_falls_back_to_tempdir_when_staging_root_uncreatable
tests/inner/test_codex_executor.py::TestCodexAppServerSessionHomeStaging::test_start_stages_empty_skills_before_worker_spawn_when_disabled
tests/inner/test_codex_executor.py::TestCodexAppServerSessionHomeStaging::test_start_stages_home_under_the_staging_root_not_cwd
tests/inner/test_codex_hooks_generation.py::test_app_server_argv_carries_no_hook_trust_flag
tests/inner/test_codex_hooks_generation.py::test_app_server_keeps_symlinked_hooks_when_routing_off
tests/inner/test_codex_hooks_generation.py::test_a_plain_codex_session_gets_no_probe_and_keeps_its_hooks_symlink
tests/inner/test_codex_hooks_generation.py::test_a_pinned_smart_routing_codex_session_gets_the_catalog_only
tests/inner/test_codex_hooks_generation.py::test_an_auto_harness_codex_session_gets_the_catalog_and_the_spawn_gate
tests/inner/test_codex_hooks_generation.py::test_an_old_codex_cli_registers_no_spawn_gate
tests/inner/test_codex_hooks_generation.py::test_a_new_enough_codex_cli_registers_the_spawn_gate
tests/inner/test_codex_hooks_generation.py::test_an_old_codex_cli_keeps_the_sdk_harness_hooks_symlinked
tests/inner/test_codex_model_catalog.py::test_required_brokered_catalog_is_bundled_private_and_credential_free
tests/inner/test_codex_staging.py::test_staging_root_tightens_a_loose_preexisting_mode
tests/inner/test_codex_worker_containment.py::test_signer_readiness_rejects_ordinary_egress_rules
tests/inner/test_codex_worker_containment.py::test_signer_readiness_rejects_unwrapped_worker
tests/inner/test_codex_worker_containment.py::test_session_containment_failure_prevents_worker_spawn
tests/inner/test_codex_worker_containment.py::test_session_spawns_owned_launcher_and_releases_it
tests/inner/test_codex_worker_containment.py::test_spawn_failure_releases_launcher_and_private_home
tests/inner/test_copy_on_write.py::test_persistent_parent_with_disposable_child
tests/inner/test_copy_on_write.py::test_ambiguous_or_invalid_roots_rejected[grants0]
tests/inner/test_copy_on_write.py::test_ambiguous_or_invalid_roots_rejected[grants1]
tests/inner/test_copy_on_write.py::test_ambiguous_or_invalid_roots_rejected[grants2]
tests/inner/test_copy_on_write.py::test_ambiguous_or_invalid_roots_rejected[grants3]
tests/inner/test_copy_on_write.py::test_ambiguous_or_invalid_roots_rejected[grants4]
tests/inner/test_copy_on_write.py::test_file_grant_cannot_persist_inside_cow
tests/inner/test_copy_on_write.py::test_resolved_alias_conflict_is_rejected
tests/inner/test_copy_on_write.py::test_missing_bubblewrap_is_actionable
tests/inner/test_copy_on_write.py::test_missing_bubblewrap_requirements_depend_on_grant[True]
tests/inner/test_copy_on_write.py::test_persistent_grants_never_initialize_or_probe_cow[grants0]
tests/inner/test_copy_on_write.py::test_persistent_grants_never_initialize_or_probe_cow[grants1]
tests/inner/test_copy_on_write.py::test_unlaunchable_bubblewrap_reports_requirements
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[-True]
tests/inner/test_copy_on_write.py::test_keeper_checks_tmpfs_xattrs_before_reporting_ready
tests/inner/test_copy_on_write.py::test_working_kernel_backport_is_accepted
tests/inner/test_copy_on_write.py::test_stale_namespace_closes_pinned_descriptors
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_prefers_user_over_gcp_service_account_first_in_file
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_env_profile_selects_sp_over_valid_user
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_selects_user_token_over_sp_token
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_warns_when_stale_user_falls_through_to_sp
tests/inner/test_model_auth.py::test_ucode_resolution_rejects_writable_parent
tests/inner/test_model_auth.py::test_ucode_resolution_rejects_unsafe_symlink_chain
tests/inner/test_model_auth.py::test_ucode_adapter_uses_hermetic_environment_and_fixed_argv
tests/inner/test_model_auth.py::test_ucode_helper_gets_an_owned_process_group
tests/inner/test_model_signer_lifecycle.py::test_signer_preflights_before_codex_state_and_worker_spawn
tests/inner/test_model_signer_lifecycle.py::test_required_catalog_failure_stops_before_worker_preparation
tests/inner/test_model_signer_lifecycle.py::test_signer_exit_before_worker_spawn_fails_startup
tests/inner/test_model_signer_lifecycle.py::test_signer_exit_during_worker_spawn_tears_worker_down
tests/inner/test_model_signer_lifecycle.py::test_signer_backed_home_excludes_host_credential_files
tests/inner/test_model_signer_lifecycle.py::test_signer_backed_home_is_private_and_outside_workspace
tests/inner/test_model_signer_lifecycle.py::test_signer_backed_home_rejects_symlink_temp_root
tests/inner/test_model_signer_lifecycle.py::test_failure_after_signer_readiness_closes_signer_and_state
tests/inner/test_model_signer_lifecycle.py::test_retry_uses_a_fresh_signer_after_failed_preflight
tests/inner/test_model_signer_lifecycle.py::test_signer_exit_terminates_worker
tests/inner/test_model_signer_lifecycle.py::test_signer_exit_escalates_to_kill_for_term_ignoring_worker
tests/inner/test_model_signer_lifecycle.py::test_runner_close_terminates_worker_without_waiting_for_signer
```

## Prompt to paste into the new session

> Continue the broader Windows suite work using
> `docs/windows/BROADER-WINDOWS-SUITE-HANDOVER-2026-10-09.md` in the
> `omnigent-v017` integration checkout. Read AGENTS.md and the handover first,
> verify current branch/state, then fix and validate the suite to completion.
> Use GPT-6.1 Sol or GPT-6 Luna subagents for bulk work with disjoint file
> ownership. Check original upstream main/issues for existing fixes first.
> Resolve the signer-fixture hard timeout before rerunning the whole sweep;
> retain containment/credential/security refusals and classify legitimate
> platform-only tests precisely. Keep changes contained for upstream upgrades,
> preserve my existing environment, and don't create a PR. When ready, run
> hooks, push directly, run Actions, verify matching artifacts, and report the
> actual completed Windows summary plus any remaining acceptance limits.
