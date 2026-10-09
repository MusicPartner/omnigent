# Broader Windows test findings: 2026-10-09

The repaired selection now passes locally and in required Windows CI.
Final source: `e6a14a5e9dad093bebdf16809b70d22e9dccd61b`.
[Required release validation](https://github.com/MusicPartner/omnigent/actions/runs/37985563937)
completed its broader Windows gate: **3,786 passed, 187 skipped,
292 deselected and 10 passing subtests**, zero failures/errors, 651.34s.
The [JUnit artifact](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643273402)
records 3,983 test/subtest entries. The step is required; `continue-on-error`
was removed. Final artifact verification is recorded below.

Local runs completed with **3,763 passed, 210 skipped, 292 deselected and
10 passing subtests**, both with normal capture and with memory diagnostics.
[UI validation](https://github.com/MusicPartner/omnigent/actions/runs/37983319919)
passed Browser Contract and all ten shards. Final Linux repaired families
passed 1,298 tests; focused integration passed 1,040. Backend E2E passed all
four shards and the dispatched integration matrix passed on the same production
repair. Subsequent commits change only tests, test dependencies and CI.

The [skip inventory](BROADER-WINDOWS-SKIPS-2026-10-09.md) records every skip and
CI/local differences. All 23 optional Databricks SDK cases stayed skipped;
Databricks was not installed or enabled. Four of the user's five permitted
additional attempts were used; the fifth was not needed.
Earlier native Python crashes remain unexplained. CI retains `PYTHONMALLOC=debug`
and `python -X dev`; passing runs do not establish the crash's root cause.
The original 99 and later 64 failure inventories remain historical.

## Historical first release sweep

Source: `489665868933fab513199060fd2349bc65d7ea01` on
`windows-parity/v0.17-integration`.
[Release validation](https://github.com/MusicPartner/omnigent/actions/runs/37962935896)
passed its required Linux/Windows checks and both artifact jobs. Its separate
non-blocking diagnostic selected 3,950 tests and recorded the 99 `FAILED` names
below before a hard timeout at approximately 61%. No complete pytest summary was
produced. Actions normalizes this step to success because of `continue-on-error`;
that conclusion does not mean the broad sweep passed.

## Fixes completed in this release

- The authentication cancellation test now launches a real Python helper on both
  operating systems, bounds startup, and checks the exact helper exits after
  cancellation. It passed in both required OS gates and in the Windows sweep.
- Both ACP fake-agent scripts explicitly use UTF-8 rather than Windows' default
  text encoding. Their mocked end-to-end tests passed in the Windows sweep.
- Lightning CSS is pinned to 1.33.0. The production web build no longer warns on
  either valid `::highlight(name)` rule; 16 local preview-search tests passed.

## Historical support work at the first sweep

These findings are a backlog, not reasons to remove security checks or silently
skip the entire suite. Local safe reproductions establish the examples below;
not every recorded failure has a verified root cause.

| Area | Evidence and next work |
| --- | --- |
| Native attachment delivery | The POSIX-only storage gap is fixed in the [Windows attachment follow-up](PARITY-NEXT-STEPS.md#windows-attachment-storage-follow-up-2026-10-09), production source `575754760` with test correction `208591ece`. Required Windows CI passed 109 cache/security and 35 consumer/resume checks. Relative native handles, private ACLs, collision/reuse, partial-write cleanup and real junction races are covered. Live Claude/Codex image/ZIP acceptance still needs the documented local check, especially Codex sandbox read access. The failure names below remain historical observations from `489665868`, not current attachment failures. |
| Brokered signer support and fixtures | The terminal timeout was `test_cancelled_close_contains_worker_and_retains_incomplete_signer_cleanup`. The mock constructs `/private/signer/...` paths that Windows does not treat as absolute. Startup error handling then awaits its deliberately blocking `close()` before any worker spawns. The real signer uses bounded process shutdown. The fixture and signer contract match local `origin/main`; this timeout does not exercise desktop Quit. Private signer homes also use POSIX mode checks that reject Windows' reported `0777`. Preserve refusals pending a proven Windows ACL/containment contract. |
| Platform-specific assertions/backends | Reproduced staging tests assume `chmod(0700)` changes POSIX permission bits; a copy-on-write test requests `linux_bwrap`, which correctly refuses Windows. Declare actual platform scope or add meaningful Windows tests; do not weaken the backend's refusal. |
| Other recorded failures | Codex SDK/hook/catalog/containment, Databricks auth, and the remaining authentication tests require case-by-case diagnosis. The four auth failures include Unix-shell and POSIX ownership fixtures. Verbose names are reliable, but this aborted run contains no final failure tracebacks. Do not attribute unverified cases to shutdown or PowerShell discovery. |

To reproduce a named case without waiting for a whole-suite timeout, use the
existing checkout environment and a bounded test invocation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/inner/<file>.py::<test> -n0 -vv --tb=short --timeout=30
```

Replace the placeholder with a recorded node ID. Tests that exercise real
provider services or credentials need their own explicit setup; the focused
local reproductions above used mocks/fake agents only. Full UI acceptance of
Claude, Codex, and Copilot remains described in
[the parity record](PARITY-NEXT-STEPS.md#automatic-native-powershell-selection-for-the-primary-windows-harnesses).

## Attachment follow-up diagnostic

On test correction source `208591ece`,
[release validation 37970056214](https://github.com/MusicPartner/omnigent/actions/runs/37970056214)
passed both required OS gates, including 144 Windows attachment checks. Its
separate non-blocking broad sweep recorded 64 `FAILED` names before the same
signer lifecycle fixture hit its 300-second hard timeout. No attachment failures
were recorded in that partial run; it still did not produce a completed suite
summary. This does not establish a clean whole-Windows-suite result or resolve
unverified causes of other historical failures. The 99-name inventory below is
retained as the earlier build's observation.

## Broader-suite repair and validation

The original upstream reviewed for this repair is `omnigent-ai/omnigent` main
`ed7c5d600684c70c226ac0b87e87df0f21fbcea0`. The earlier inventories below
remain historical observations. The completed local native rerun and required
Linux checks passed; the final required broad CI run also passed. Earlier native crash causes remain unconfirmed.

| Family | Reproduced cause and correction | Retained coverage |
| --- | --- | --- |
| Signer lifecycle / worker containment | Fake `/private` readiness paths are not absolute on Windows. Unrelated inline private-home checks prevented lifecycle tests from reaching worker startup. Extracted the staging method without changing its security checks; explicit fixtures replace that method only in transport/lifecycle tests. Bounded blocking-close fixture and cleanup handshake. | Worker refusal, credential exclusion, cancellation, escalation and failed-start cleanup remain portable. Real POSIX home permissions remain active on Linux. New Windows startup refusal proves no worker preparation/spawn. |
| Codex executor / hooks / catalog / staging | Private `0700` assertions and symlink-only fixture assumptions. Portable routing/version tests use explicit staging fixture; permission tests have precise platform scope. Hooks retain exact payload assertions when copied. | Real staging tests remain POSIX; Windows refusal and real junction skill linking remain covered. Symlink-only tests skip only actual privilege error 1314. Catalog content and credential assertions are separate from POSIX file modes. |
| Copy-on-write | Mock Linux fixtures changed shared `sys.platform` but omitted the module's OS capability check; other mocks called absent `uname`. Module-local OS/platform stand-ins keep policy tests portable. | Real unsupported-backend refusal remains. Linux keeper/xattr and namespace descriptor tests retain Linux coverage. Failure reaping and validation execute on Windows. |
| Model authentication | POSIX provenance checks and executable shell fixtures. Real Python helpers now verify child argv/environment and process spawn options. | Ownership/mode and forked descendant tests retain POSIX scope; real cancellation/reaping remains portable. No authentication policy change. |
| Optional Databricks tests | Four SDK-dependent tests lacked the adjacent tests' optional dependency guard. Added the same guard. | No SDK installed or provider enabled locally; standard CI can skip the optional dependency. User does not use Databricks. |
| Grant reach / tree copy / cwd scan / bubblewrap masks / credential refresh | Symlink fixtures fail with actual Windows privilege error 1314. | Only that exact error skips; capable Windows and Linux runners still execute security checks. |
| Pi | Real Windows npm batch wrapper truncated multiline composed instructions. Known Pi npm shims now launch their verified package entry through Node directly. Fixture retains Windows bootstrap variables and isolated user home. | All 16 real prompt variants passed locally with request/framework ordering and context assertions. Dedicated argv tests cover both npm package names, append/replace and shell metacharacters. Unknown launchers retain existing behavior. |
| Qwen | Gateway authentication hardcoded `sh`; Windows uses existing platform shell dispatch. Mock initialized agent omitted its active model and waited 30 seconds for an unanswered switch. | Real auth success/failure/empty-token tests use portable shell commands; POSIX continues using `sh`. Initialized fixture now reports the selected model. |
| Terminal / clipboard / wordmark | Real tmux, Unix sockets and shell fixtures require POSIX. ANSI test accidentally used Rich's legacy Windows output mode. | Portable terminal state/payload/ownership validation remains active. Native psmux required checks remain separate. ANSI fixture explicitly requests ANSI output. |
| Runtime process cleanup | Readiness used text-mode CRLF, and child lacked its own Windows console group. | Binary readiness, owned process-group spawn, platform graceful-signal refusal and real cancellation/force-reap assertions. |

Relevant original upstream history includes signer `5fa3bebe` (#6770), Windows
junction support `83da28cd` (#6487), copy-on-write `6b87d7b5`, Pi prompt modes
`bd607dfc` (#8349), clipboard `b9d4502b` (#7934), terminal ownership `1b1407a6`
(#7495), and cancelled runtime cleanup `8cdefbe0` (#9106). No equivalent
Windows private-home ACL contract was found. The existing signer refusal is
retained; the attachment ACL implementation is not reused as a sandbox claim.

A diagnostic tail run completed before the later repairs: 1,425 passed,
78 failed, 65 skipped and 128 deselected, with two passing subtests in 527.41s.
Its failures exposed the additional terminal, Pi, Qwen and process fixtures
above; this intermediate result is not a final acceptance result.

## Completed evidence and bounded follow-up

Production repair: `b0be8b116c14378b49d387cfd2a69ead85ea0802`.
Validated source: `62607c95cc809140eb8c0c17337759cc79461099`; the two
intervening commits only supply Linux CI prerequisites and namespace setup.
Applicable staged pre-commit hooks passed, and Pyrefly targeting Linux
reported zero errors. A read-only review found no actionable production or
security regression in the narrow Codex, Pi and Qwen changes.

| Check | Completed result |
| --- | --- |
| Local exact broader selection | 3,763 passed, 210 skipped, 292 deselected, 17 warnings and 10 passing subtests in 571.22s; exit 0. JUnit includes 3,983 test/subtest entries, zero failures/errors. |
| [Required Windows compatibility](https://github.com/MusicPartner/omnigent/actions/runs/37981197107/job/113992194375) | Repaired families: 1,188 passed, 157 skipped and two passing subtests in 188.63s. Attachment, shutdown, launcher, CLI, stable, hook/shell and psmux steps also passed. |
| [Required Linux compatibility](https://github.com/MusicPartner/omnigent/actions/runs/37981197107/job/113992194877) | Repaired families: 1,298 passed, 47 skipped and two passing subtests in 185.94s; real POSIX permission, symlink, keeper and terminal checks remain active. Focused integration: 1,040 passed, 13 skipped. |
| [Integration](https://github.com/MusicPartner/omnigent/actions/runs/37980406733) | Success on production repair source `b0be8b116`, attempt 1; dispatched OpenAI Agents matrix. |
| [Backend E2E](https://github.com/MusicPartner/omnigent/actions/runs/37980410996) | Success on `b0be8b116`, attempt 1; all four shards passed. |
| [UI E2E, original attempt](https://github.com/MusicPartner/omnigent/actions/runs/37980416638) | Browser Contract and nine UI shards passed; shard 4 failed Claude SDK terminated-CLI recovery before signaling because discovery found two launch roots. Its pytest retry also failed. |

The completed local run selected every test under `tests/inner` and
`tests/runtime/harnesses` with `-m "not posix_only"`. It did not reduce the
selection to the repaired files. Of its 210 skips, 187 require unavailable
platform/capability/host fixtures and 23 require the absent optional Databricks
SDK. Databricks is not used, installed or enabled. The inventory gives exact
reasons and test names; 292 POSIX-marked cases were deselected separately.

The broad Windows CI sweep in run `37981197107` did **not** pass. It reached
about 30%, then Python reported a native access violation during pytest's
current-test environment update; exit 1, no JUnit and no final summary. Its
`continue-on-error` normalized conclusion is success. An earlier local run
at `b0be8b116` crashed near 70% during pytest capture (exit -1073741819).
Different crash locations and a later completed local pass do not establish
the cause. Native API signatures were reviewed without finding a specific
defect. Those attempts kept the diagnostic non-blocking and required the repaired families. Source `e6a14a5e9` makes the full broader selection required, so a native crash or test failure blocks release artifacts.

Earlier intermediate runs are also retained: the diagnostic tail recorded
78 failed / 1,425 passed, and an evolving full run recorded 13 failed /
3,761 passed. The latter exposed 12 symlink fixtures and the ANSI wordmark
fixture, which were corrected before the completed local run. Release runs
`37980379230` and `37980960976` were superseded/cancelled; the former's Linux
failure identified missing bubblewrap/tmux prerequisites. They are not successes.

The UI census includes title-generation SDK clients. Original upstream fixes
`3138c7df` and `ece18f48` identify this same ownership-isolation problem, but
this integration source does not transport their agent-name environment marker.
The narrow test correction at `bbda83990` uses the existing browser preference
to disable background titles for this recovery test. Its exactly-one-root
refusal and process-exit/recovered-turn checks remain intact. No Claude runtime
behavior is changed.

The user authorized **at most five additional repair/test attempts**, then
requires stopping for approval if unresolved. Completed test attempts (four of five; fifth unused):

1. Local full selection with `PYTHONMALLOC=debug` and `python -X dev`: **passed**, 3,763 passed / 210 skipped / 292 deselected / 16 warnings / 10 passing subtests, 591.07s, exit 0. No allocator fault reported; post-exit socket/transport ResourceWarnings remain diagnostic observations.
2. [Release validation with memory diagnostics](https://github.com/MusicPartner/omnigent/actions/runs/37983318980), source `bbda83990`: broader sweep **completed with two failures**, 3,784 passed / 187 skipped / 292 deselected / 16 warnings / 10 passing subtests in 534.84s. JUnit records two failures, zero errors, and 3,983 entries. Both failures are missing `distlib` in historical Windows prototype tests. No native crash; required families and both artifact jobs passed, but the normalized workflow success is not a broader-suite pass.
3. [UI validation after title isolation](https://github.com/MusicPartner/omnigent/actions/runs/37983319919), source `bbda83990`: **success**, Browser Contract and all ten shards passed. The recovery test passed on its first execution; shard 4 reports 104 passed / one skipped / five deselected / three warnings in 715.56s, no pytest reruns.
4. [Required broader release validation](https://github.com/MusicPartner/omnigent/actions/runs/37985563937), source `e6a14a5e9`: **broader gate passed**, 3,786 passed / 187 skipped / 292 deselected / 16 warnings / 10 passing subtests in 651.34s, zero JUnit failures/errors. Final Linux families: 1,298 passed / 47 skipped / two passing subtests in 178.02s; focused integration: 1,040 passed / 13 skipped. The complete release workflow and both artifact jobs passed; downloaded source comparisons and disposable installer/uninstaller smoke also passed. Declares the already-locked distlib dependency directly in the Windows test group; removes `continue-on-error` from the full broad sweep. The offline lock refresh changed no package versions and installed nothing locally.

The completed CI run still skipped all 23 optional Databricks SDK cases. Its capable Windows runner executed symlink security fixtures that skipped locally. Its 187 skips are distinct from the local 210-skip inventory.

## Final matching artifacts

[Release validation `37985563937`](https://github.com/MusicPartner/omnigent/actions/runs/37985563937)
completed successfully on source `e6a14a5e9dad093bebdf16809b70d22e9dccd61b`.
Both downloaded bundles were inspected without installing over the user's app.
The core wheel's 14 checked Python modules match that commit, including Codex,
Pi, Qwen, attachments and shutdown. Electron's four checked host/manager modules
match; its source metadata is the exact commit, version 0.17.0, dev mode,
executable `Omnigent Dev.exe`.

The native asset remains the unsigned, opt-in candidate with
`release_approved=false`; its hash and pinned toolchain are unchanged.
The disposable-prefix installer installed the exact core/client/UI SDK wheels,
all 0.17.0. Both console entry points' version/help checks passed, and the
uninstaller removed the test prefix. Existing local dependencies and app
sessions were preserved.

- [Final CLI bundle](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643364292)
- [Final desktop ZIP](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643559052)
- [Final broader JUnit](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643273402)

### Earlier verified artifacts

Both original `62607c95c` artifacts completed and were downloaded and compared
against their commit. The core wheel contains 14 matching Python modules,
including Codex, Pi, Qwen, attachment and shutdown changes. Electron's archive
contains four matching host/manager modules and source metadata `62607c95c`,
version 0.17.0, dev mode. The native asset hash remains
`3d2564228c78a637c5c47bc350937cb2474e61ca6a855b272e0191cac6984c03`;
it is unsigned and `release_approved=false`. The disposable-prefix installer,
CLI version/help checks and uninstaller passed in CI.

- [CLI bundle](https://github.com/MusicPartner/omnigent/actions/runs/37981197107/artifacts/11641351829)
- [Desktop ZIP](https://github.com/MusicPartner/omnigent/actions/runs/37981197107/artifacts/11641279772)

To repeat the completed local selection without synchronizing dependencies:

```powershell
Set-Location D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v017
.\.venv\Scripts\python.exe -m pytest tests/inner tests/runtime/harnesses -m "not posix_only" -n0 -p no:cacheprovider -vv --tb=short --timeout=60 -ra
```

Live Claude/Codex/Copilot conversation, Stop/resume and desktop Quit acceptance
still require the manual checks in [the parity record](PARITY-NEXT-STEPS.md).
A green mocked/unit suite does not establish Codex sandbox attachment read
access or brokered signer filesystem/network isolation on Windows.

## Observed failures before the timeout

```text
tests/inner/test_antigravity_native_executor.py::test_run_turn_image_attachment_materialized
tests/inner/test_antigravity_native_executor.py::test_run_turn_attachment_only_no_longer_errors
tests/inner/test_claude_native_executor.py::test_run_turn_materializes_image_to_bridge_dir
tests/inner/test_claude_native_executor.py::test_resize_notice_uses_hidden_hook_context
tests/inner/test_claude_native_executor.py::test_run_turn_image_only_no_text_still_injects
tests/inner/test_claude_native_executor.py::test_run_turn_materializes_zip_outside_workspace
tests/inner/test_claude_native_executor.py::test_run_turn_materializes_zip_without_workspace
tests/inner/test_claude_native_executor.py::test_run_turn_dedup_same_filename
tests/inner/test_claude_native_executor.py::test_run_turn_image_without_filename_gets_generated_name
tests/inner/test_claude_native_executor.py::test_enqueue_session_message_materializes_image
tests/inner/test_claude_native_executor.py::test_run_turn_path_traversal_filename_sanitized
tests/inner/test_codex_executor.py::TestCodexExecutor::test_app_server_uses_isolated_codex_home_and_cleans_it_up
tests/inner/test_codex_executor.py::TestCodexExecutor::test_app_server_uses_workspace_cwd
tests/inner/test_codex_executor.py::test_embedded_codex_materializes_provider_auth_outside_argv[printf %s sk-sentinel-do-not-use]
tests/inner/test_codex_executor.py::test_embedded_codex_materializes_provider_auth_outside_argv[credential-helper --token sk-sentinel-do-not-use]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[omnigent/0.141.0 (macOS 15.6.1)-False]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[omnigent/0.142.0-True]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[codex_cli_rs/0.154.0-True]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[custom-client/0.154.0-alpha.1 (client/0.1)-True]
tests/inner/test_codex_executor.py::test_app_server_negotiates_direct_tools_from_server_version[unknown (client/0.154.0)-False]
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
tests/inner/test_codex_native_executor.py::test_image_block_is_sent_as_local_image_not_inline_base64
tests/inner/test_codex_native_executor.py::test_resize_notice_is_encoded_in_model_visible_image_path
tests/inner/test_codex_native_executor.py::test_resize_paths_preserve_multiple_images_and_cached_originals
tests/inner/test_codex_native_executor.py::test_input_file_binary_is_materialized_and_referenced_by_path
tests/inner/test_codex_native_executor.py::test_input_file_zip_is_materialized_outside_the_workspace
tests/inner/test_codex_native_executor.py::test_zip_submitted_as_an_image_block_still_uses_a_file_reference
tests/inner/test_codex_native_executor.py::test_input_file_zip_is_materialized_without_workspace
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
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: Unknown option --tmp-overlay-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: Unknown option --tmp-overlay-True]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: No permissions to create a new namespace-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: No permissions to create a new namespace-True]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: mounting overlay: Operation not permitted-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: mounting overlay: Operation not permitted-True]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: mounting overlay: No such device-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[bwrap: mounting overlay: No such device-True]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[OSError: [Errno 95] Operation not supported: tmpfs user xattrs-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[OSError: [Errno 95] Operation not supported: tmpfs user xattrs-True]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[-False]
tests/inner/test_copy_on_write.py::test_failed_start_reaps_process[-True]
tests/inner/test_copy_on_write.py::test_keeper_checks_tmpfs_xattrs_before_reporting_ready
tests/inner/test_copy_on_write.py::test_working_kernel_backport_is_accepted
tests/inner/test_copy_on_write.py::test_stale_namespace_closes_pinned_descriptors
tests/inner/test_cursor_native_executor.py::TestContentExtraction::test_real_image_attachment_materialized
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_prefers_user_over_gcp_service_account_first_in_file
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_env_profile_selects_sp_over_valid_user
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_selects_user_token_over_sp_token
tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_warns_when_stale_user_falls_through_to_sp
tests/inner/test_kimi_native_executor.py::TestContentExtraction::test_real_image_attachment_materialized
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
