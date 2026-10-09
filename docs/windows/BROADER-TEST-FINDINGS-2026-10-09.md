# Broader Windows test findings: 2026-10-09

For the next implementation session, use the [broader-suite handover](BROADER-WINDOWS-SUITE-HANDOVER-2026-10-09.md),
including the latest 64 failure IDs, the timeout diagnosis, and validation criteria.

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

## Remaining support work

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
