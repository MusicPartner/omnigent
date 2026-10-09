# Broader Windows skipped-test inventory: 2026-10-09

Source: completed local Windows run at `62607c95cc809140eb8c0c17337759cc79461099`, 3,763 passed and 210 skipped. Entries use pytest node IDs reconstructed from JUnit classnames and test names. Host-specific paths were removed from skip reasons. See [the validation record](BROADER-TEST-FINDINGS-2026-10-09.md) for scope and CI limits. Databricks was not installed or enabled.

Total skipped nodes: **210**

| Category | Count |
|---|---:|
| Platform / capability / host fixture | 187 |
| Optional Databricks SDK dependency (databricks-sdk absent) | 23 |

## Platform / capability / host fixture (187)

### shadow file unavailable on this host (3)

- `tests/inner/test_cwd_scan.py::test_nested_escaping_symlink_is_marked`
- `tests/inner/test_cwd_scan.py::test_non_recursive_ignores_nested_escaping_symlink`
- `tests/inner/test_cwd_scan.py::test_symlink_pointing_outside_safe_roots_is_marked_as_file`

### expected system binary directory unavailable on this host (1)

- `tests/inner/test_cwd_scan.py::test_symlink_pointing_into_safe_root_is_not_marked`

### a POSIX symlink stands in for the junction (1)

- `tests/inner/test_codex_executor.py::TestCodexAppServerSessionHomeStaging::test_start_links_skills_through_a_junction_when_symlinks_are_refused`

### bwrap cannot create namespaces on this host (2)

- `tests/inner/sandbox/test_write_paths_missing_dir.py::test_write_into_missing_granted_dir_succeeds`
- `tests/inner/sandbox/test_write_paths_missing_dir.py::test_write_into_precreated_granted_dir_succeeds`

### bwrap not installed (2)

- `tests/inner/test_bwrap_symlink_mask_3265.py::test_bwrap_rejects_a_bind_onto_a_symlink`
- `tests/inner/test_bwrap_symlink_mask_3265.py::test_skipping_symlink_masks_does_not_leak_the_target`

### Creating symbolic links requires Windows developer mode (2)

- `tests/inner/test_windows_powershell.py::test_resolved_batch_shim_is_rejected`
- `tests/inner/test_windows_powershell.py::test_resolved_store_target_is_rejected`

### darwin_seatbelt requires macOS + sandbox-exec on PATH (26)

- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_databricks_cli_materializes_cfg_and_swaps[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_https_bearer_swaps_injected_env_token[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_swap_on_access_injects_basic_without_sandbox_secret[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_allows_matching_https_get[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_denies_unmatched_https_get[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_direct_tcp_bypass_is_blocked[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_injects_ca_env_vars_at_same_bundle[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s2_egress_allows_private_destination_when_opt_in[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s2_egress_blocks_private_destination_by_default[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s4_same_uid_external_process_cannot_use_helper_relay[darwin_seatbelt]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s4_two_sandboxes_cannot_borrow_each_others_proxy[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allow_network_false_blocks_outbound_connect[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allows_dotfile_under_read_path_when_allowlisted[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allows_home_library_when_explicit_optin[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_credential_dotfiles_under_granted_read_path[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_home_library_when_home_read_granted_without_optin[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_shell_write_outside_cwd[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_empty_write_paths_blocks_cwd_writes_but_allows_tmpdir[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_helper_does_not_inherit_unallowlisted_env_vars[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_helper_inherits_explicit_env_passthrough[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_hides_user_dotfiles_in_cwd[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_provides_writable_scratch_tmpdir[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_start_in_scratch_helper_starts_in_scratch_tmpdir[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_start_in_scratch_workspace_remains_readable[darwin_seatbelt]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_uses_private_desktop_runtime[darwin_seatbelt-helper]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_uses_private_desktop_runtime[darwin_seatbelt-launcher]`

### fork is POSIX-only (1)

- `tests/inner/test_liveness_exec.py::test_detached_reaper_fork_failure_falls_back_to_inline_teardown`

### Linux OverlayFS required (6)

- `tests/inner/test_copy_on_write_linux.py::test_file_operations_survive_helper_restart_without_host_changes`
- `tests/inner/test_copy_on_write_linux.py::test_independent_environments_and_borrowed_harness`
- `tests/inner/test_copy_on_write_linux.py::test_keeper_loss_does_not_run_against_host`
- `tests/inner/test_copy_on_write_linux.py::test_masks_readonly_paths_and_persistent_parent`
- `tests/inner/test_copy_on_write_linux.py::test_runner_tools_share_terminal_and_reopened_terminal`
- `tests/inner/test_copy_on_write_linux.py::test_session_cleanup_leaves_other_session_independent`

### linux_bwrap requires Linux + bwrap on PATH (27)

- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_databricks_cli_materializes_cfg_and_swaps[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_https_bearer_swaps_injected_env_token[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_credential_proxy_swap_on_access_injects_basic_without_sandbox_secret[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_allows_matching_https_get[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_denies_unmatched_https_get[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_direct_tcp_bypass_is_blocked[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_egress_injects_ca_env_vars_at_same_bundle[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s2_egress_allows_private_destination_when_opt_in[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s2_egress_blocks_private_destination_by_default[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s4_same_uid_external_process_cannot_use_helper_relay[linux_bwrap]`
- `tests/inner/sandbox/test_egress_e2e.py::test_s4_two_sandboxes_cannot_borrow_each_others_proxy[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allow_network_false_blocks_outbound_connect[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allows_dotfile_under_read_path_when_allowlisted[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_allows_home_library_when_explicit_optin[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_credential_dotfiles_under_granted_read_path[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_home_library_when_home_read_granted_without_optin[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_blocks_shell_write_outside_cwd[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_empty_write_paths_blocks_cwd_writes_but_allows_tmpdir[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_helper_does_not_inherit_unallowlisted_env_vars[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_helper_inherits_explicit_env_passthrough[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_hides_user_dotfiles_in_cwd[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_provides_writable_scratch_tmpdir[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_start_in_scratch_helper_starts_in_scratch_tmpdir[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_start_in_scratch_workspace_remains_readable[linux_bwrap]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_uses_private_desktop_runtime[linux_bwrap-helper]`
- `tests/inner/sandbox/test_sandbox_behavior.py::test_sandbox_uses_private_desktop_runtime[linux_bwrap-launcher]`
- `tests/inner/sandbox/test_write_paths_missing_dir.py::test_missing_write_root_survives_into_bwrap_argv`

### opt in with OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER=1; requires x64 MSVC/SDK (28)

- `tests/inner/test_windows_exec_launcher_runtime.py::test_authenticode_verifier_binds_actual_trusted_microsoft_signer`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_private_asset_rejects_reparse_point`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_private_creation_never_overwrites_existing_file`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_private_file_has_explicit_protected_user_system_dacl`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_private_stream_failure_cleans_only_created_file`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_runtime_bad_asset_hash_fails_before_copy`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_runtime_dev_asset_runs_and_unlink_removes_config`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_runtime_native_refuses_unsigned_release`
- `tests/inner/test_windows_exec_launcher_runtime.py::test_runtime_native_verifies_signature_after_release_gate`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_abrupt_startup_death[after_create]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_abrupt_startup_death[before_create]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_death_stops_existing_descendants[forced-stub-death]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_death_stops_existing_descendants[late-outer-job]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_fails_closed_before_execution[config]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_fails_closed_before_execution[interpreter]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_fails_closed_before_execution[job]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_inherited_nested_host_job`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_literal_argv_stdio_exit_and_spaced_unicode_paths`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_normal_exit_closes_only_active_job[inactive]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_normal_exit_closes_only_active_job[private-job]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_parent_death_without_outer_job_stops_tree`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_resume_failure_kills_known_suspended_child`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_sdk_client_cancellation_stops_tree`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_sdk_version_probe_and_close[version-output]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_sdk_version_probe_and_close[version-timeout]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_spawning_parent_dies_during_startup[after_create]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_spawning_parent_dies_during_startup[before_create]`
- `tests/inner/test_windows_private_job_launcher.py::test_private_launcher_spawning_parent_dies_during_startup[before_parent_capture]`

### Per-uid tmp parent is POSIX-only; Windows uses gettempdir(). (1)

- `tests/runtime/harnesses/test_process_manager.py::test_default_tmp_parent_is_per_uid_on_posix`

### POSIX directory symlinks (3)

- `tests/inner/test_codex_staging.py::test_skills_refresh_does_not_follow_child_symlinks`
- `tests/inner/test_codex_staging.py::test_skills_refresh_rejects_symlink_root`
- `tests/inner/test_codex_staging.py::test_staging_root_resolves_symlinked_temp_ancestors`

### POSIX ownership semantics (2)

- `tests/inner/test_codex_staging.py::test_staging_root_refuses_a_root_owned_by_another_user`
- `tests/inner/test_codex_staging.py::test_staging_root_refuses_a_symlink_squatting_its_name`

### POSIX permission semantics (3)

- `tests/inner/test_codex_staging.py::test_skills_refresh_rejects_nonprivate_root[455]`
- `tests/inner/test_codex_staging.py::test_skills_refresh_rejects_nonprivate_root[488]`
- `tests/inner/test_codex_staging.py::test_skills_refresh_rejects_nonprivate_root[504]`

### POSIX process groups (2)

- `tests/inner/test_acp_executor.py::test_close_reaps_the_agents_forked_children`
- `tests/inner/test_acp_executor.py::test_spawned_agent_leads_its_own_process_group`

### POSIX shebang behaviour (3)

- `tests/inner/test_sandbox.py::test_exec_launcher_runs_when_interpreter_path_has_a_space`
- `tests/inner/test_sandbox.py::test_exec_launcher_runs_when_sys_executable_is_a_shell_script`
- `tests/inner/test_sandbox.py::test_exec_launcher_shebang_is_bin_sh_not_sys_executable`

### references socket.AF_NETLINK (Linux-only) while building the probe (1)

- `tests/inner/test_seccomp.py::test_arg_filter_blocks_socket_family_only`

### requires installed Homebrew Codex (1)

- `tests/inner/test_codex_brokered_auth_e2e.py::test_real_codex_seatbelt_signer_turn_and_cleanup`

### requires Linux with bubblewrap (1)

- `tests/inner/test_codex_brokered_auth_e2e.py::test_linux_bwrap_real_signer_relay_with_deterministic_worker`

### requires Linux with bubblewrap (bwrap) installed (4)

- `tests/inner/test_os_env_active_sandbox_workspace_reach.py::test_cwd_read_grant_does_not_remount_workspace_read_only`
- `tests/inner/test_os_env_active_sandbox_workspace_reach.py::test_workspace_edit_succeeds_despite_external_read_grant`
- `tests/inner/test_os_env_active_sandbox_workspace_reach.py::test_workspace_read_succeeds_despite_external_read_grant`
- `tests/inner/test_os_env_active_sandbox_workspace_reach.py::test_write_files_grant_is_readable_and_editable`

### requires Linux, dbus-daemon, gnome-keyring-daemon, and bwrap (4)

- `tests/inner/sandbox/test_linux_keyring.py::test_runner_and_granted_goose_read_real_desktop_keyring[goose]`
- `tests/inner/sandbox/test_linux_keyring.py::test_runner_and_granted_goose_read_real_desktop_keyring[runner]`
- `tests/inner/sandbox/test_linux_keyring.py::test_sandbox_cannot_reach_known_desktop_bus_or_parent_env[helper]`
- `tests/inner/sandbox/test_linux_keyring.py::test_sandbox_cannot_reach_known_desktop_bus_or_parent_env[launcher]`

### requires macOS sandbox-exec (2)

- `tests/inner/test_credential_refresh.py::test_seatbelt_denies_sources_despite_implicit_read_grant[file]`
- `tests/inner/test_credential_refresh.py::test_seatbelt_denies_sources_despite_implicit_read_grant[unix_socket]`

### requires macOS Seatbelt (2)

- `tests/inner/test_codex_worker_containment.py::test_real_seatbelt_worker_cannot_write_outside_grants`
- `tests/inner/test_codex_worker_containment.py::test_real_seatbelt_worker_reads_only_public_signer_state_and_relay_network`

### requires POSIX abrupt process death (1)

- `tests/inner/test_model_signer_process.py::test_sigkill_signer_during_ucode_preflight_reaps_helper_tree`

### requires POSIX private signer-home permissions (2)

- `tests/inner/test_model_signer_lifecycle.py::test_signer_backed_home_is_private_and_outside_workspace`
- `tests/inner/test_model_signer_lifecycle.py::test_signer_backed_home_rejects_symlink_temp_root`

### requires POSIX process groups (1)

- `tests/inner/test_brokered_auth_abrupt_death.py::test_sigkill_runner_reaps_signer_worker_helpers_and_socket`

### Requires POSIX SIGTERM semantics (2)

- `tests/inner/test_codex_transport_closed.py::test_cancelled_native_close_kills_and_reaps_sigterm_ignoring_child[adapter]`
- `tests/inner/test_codex_transport_closed.py::test_cancelled_native_close_kills_and_reaps_sigterm_ignoring_child[cancel_close]`

### sandbox backends only resolve on Linux (bwrap) or macOS (seatbelt) (1)

- `tests/inner/test_terminal.py::test_create_terminal_instance_denies_control_socket_but_keeps_private_dir_writable`

### seccomp filter tests require Linux (prctl/seccomp_load + os.fork) (5)

- `tests/inner/test_seccomp.py::test_apply_baseline_denylist_blocks_ptrace_in_child`
- `tests/inner/test_seccomp.py::test_apply_baseline_denylist_does_not_break_subprocess_basics`
- `tests/inner/test_seccomp.py::test_masked_eq_filter_blocks_clone_with_namespace_bit`
- `tests/inner/test_seccomp.py::test_seccomp_filter_applies_to_i386_compat_abi_on_x86_64`
- `tests/inner/test_seccomp.py::test_unknown_syscall_silently_skipped`

### setsid is POSIX-only (1)

- `tests/inner/test_proc_and_platform.py::test_kill_tree_reaps_descendant_that_left_process_group`

### signer relay uses a Unix socket (2)

- `tests/inner/test_model_signer_process.py::test_real_signer_relays_only_placeholder_authorized_responses`
- `tests/inner/test_model_signer_process.py::test_ucode_auth_preflight_returns_only_non_secret_readiness`

### symlink creation requires Windows Developer Mode or privileges (1)

- `tests/inner/test_copy_on_write.py::test_resolved_alias_conflict_is_rejected`

### Symlink path is POSIX-only. (1)

- `tests/runtime/harnesses/test_process_manager.py::test_resolve_harness_tmp_parent_preserves_symlink_spelling`

### the shell fixture forks a descendant and validates POSIX process-group cleanup (1)

- `tests/inner/test_model_auth.py::test_nonzero_helper_leader_exit_does_not_leave_descendants`

### v1 signer uses config fd (5)

- `tests/inner/test_model_signer_process.py::test_cancelled_signer_start_terminates_child`
- `tests/inner/test_model_signer_process.py::test_helper_stderr_is_not_exposed_in_start_error`
- `tests/inner/test_model_signer_process.py::test_readiness_with_secret_field_is_rejected`
- `tests/inner/test_model_signer_process.py::test_signer_receives_non_secret_config_and_returns_readiness`
- `tests/inner/test_model_signer_process.py::test_ucode_auth_failure_has_stable_safe_recovery_error`

### Windows account lacks symlink privilege (WinError 1314) (11)

- `tests/inner/test_codex_executor.py::test_app_server_start_preserves_custom_home_from_inherited_private_symlink`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_auth_and_config`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_hooks_json`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_memories`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_plugins_cache`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_remote_mcp_oauth`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_keeps_skill_symlinks_as_links`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_never_materializes_linked_skills[skill_dir]`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_never_materializes_linked_skills[skills_root]`
- `tests/inner/test_codex_hooks_generation.py::test_populate_symlinks_hooks_when_none_are_injected`
- `tests/inner/test_codex_hooks_generation.py::test_write_router_hooks_file_replaces_symlink_and_merges`

### Windows symbolic-link creation privilege is unavailable (7)

- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_attachments_dir`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[False-False]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[False-True]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[True-False]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[True-True]`
- `tests/inner/test_windows_attachments.py::test_symlink_leaf_cannot_be_reused_or_modified[False]`
- `tests/inner/test_windows_attachments.py::test_symlink_leaf_cannot_be_reused_or_modified[True]`

### Windows symlink creation requires Developer Mode or privilege (10)

- `tests/inner/test_credential_refresh.py::test_refresh_rejects_changed_private_symlink_target`
- `tests/inner/test_credential_refresh.py::test_refresh_revalidates_rotation`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_readable_refresh_sources[root-alias]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_readable_refresh_sources[source-alias]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[parent-link-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[parent-link-unix_socket]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-in-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-in-unix_socket]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-out-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-out-unix_socket]`

### Windows symlink creation requires Developer Mode or symlink privilege (5)

- `tests/inner/test_os_env_fork.py::TestCopyTree::test_symlinks_are_copied_as_symlinks`
- `tests/inner/test_os_env_grant_reach.py::test_contained_realpath_admits_a_symlink_loop_but_it_reaches_nothing`
- `tests/inner/test_os_env_grant_reach.py::test_contained_realpath_decides_on_the_symlink_target`
- `tests/inner/test_os_env_grant_reach.py::test_symlink_inside_grant_cannot_escape_grant`
- `tests/inner/test_pi_settings.py::test_prepare_managed_pi_agent_dir_copies_settings_and_symlinks_npm`

### Windows symlink creation requires the SeCreateSymbolicLinkPrivilege (2)

- `tests/inner/test_bwrap_symlink_mask_3265.py::test_no_mask_targets_a_symlink`
- `tests/inner/test_cwd_scan.py::test_walker_does_not_follow_symlink_loops`

### Windows symlink privilege is required for Pi resource linking (1)

- `tests/inner/test_pi_executor.py::test_gateway_seeds_managed_settings_from_global_agent`

## Optional Databricks SDK dependency (23)

### databricks-sdk not installed (23)

- `tests/inner/test_databricks_auth_command.py::test_profile_pinning_scrubs_the_ambient_credential_env_vars`
- `tests/inner/test_databricks_auth_command.py::test_the_sdk_entrypoint_prints_the_resolved_bearer`
- `tests/inner/test_databricks_auth_command.py::test_the_sdk_path_bounds_and_restores_the_network_timeout`
- `tests/inner/test_databricks_executor.py::test_databricks_gateway_host_missing_profile_falls_back_to_ambient`
- `tests/inner/test_databricks_executor.py::test_read_databrickscfg_falls_back_when_sdk_raises`
- `tests/inner/test_databricks_executor.py::test_read_databrickscfg_missing_profile_ambient_also_fails_uses_file_fallback`
- `tests/inner/test_databricks_executor.py::test_read_databrickscfg_missing_profile_service_principal_via_ambient`
- `tests/inner/test_databricks_executor.py::test_read_databrickscfg_missing_profile_uses_ambient_credentials`
- `tests/inner/test_databricks_executor.py::test_read_databrickscfg_oauth_profile_returns_fresh_bearer`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_env_profile_selects_sp_over_valid_user`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_falls_back_to_cli_when_no_profile_matches`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_prefers_matching_profile`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_prefers_user_over_gcp_service_account_first_in_file`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_selects_user_token_over_sp_token`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_uses_profile_cli_when_sdk_is_ambiguous`
- `tests/inner/test_databricks_executor.py::test_resolve_auth_for_host_warns_when_stale_user_falls_through_to_sp`
- `tests/inner/test_databricks_executor.py::test_resolve_databricks_auth_env_profile_falls_back_to_ambient_with_warning`
- `tests/inner/test_databricks_executor.py::test_resolve_databricks_auth_explicit_profile_not_found_raises`
- `tests/inner/test_databricks_executor.py::test_resolve_databricks_auth_invalid_profile_raises_clear_error`
- `tests/inner/test_databricks_executor.py::test_resolve_databricks_auth_returns_bearer_auth_and_host`
- `tests/inner/test_openai_agents_sdk_executor.py::test_get_openai_client_invalid_profile_raises_auth_error`
- `tests/inner/test_openai_agents_sdk_executor.py::test_get_openai_client_invalid_profile_with_env_fallback_warns`
- `tests/inner/test_openai_agents_sdk_executor.py::test_get_openai_client_profile_uses_callback_auth`

## CI coverage comparison

Final required broader CI at `e6a14a5e9dad093bebdf16809b70d22e9dccd61b`
passed 3,786 tests and reported 187 skips: 171 shared with the local run and
16 requiring the real Pi CLI. Its skip set matches the earlier completed CI
run; the two missing-distlib failures are fixed and retained in the findings.
All 23 optional Databricks SDK cases remained skipped.

CI exercised the 39 local privilege-limited symlink cases listed below.
All 16 Pi process/prompt variants passed locally; CI still runs the dedicated
portable argv and instruction-transport tests.

### CI-only skips: real Pi CLI unavailable (16)

- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[absent-append-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[absent-append-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[absent-replace-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[absent-replace-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[ancestor-append-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[ancestor-append-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[ancestor-replace-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[ancestor-replace-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[singular-filename-append-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[singular-filename-append-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[singular-filename-replace-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[singular-filename-replace-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[workspace-append-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[workspace-append-enabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[workspace-replace-disabled]`
- `tests/inner/test_pi_prompt_context.py::test_real_pi_adds_workspace_context_after_inline_prompt[workspace-replace-enabled]`

### Local-only skips: symlink privilege unavailable; executed in CI (39)

- `tests/inner/test_bwrap_symlink_mask_3265.py::test_no_mask_targets_a_symlink`
- `tests/inner/test_codex_executor.py::test_app_server_start_preserves_custom_home_from_inherited_private_symlink`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_auth_and_config`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_hooks_json`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_memories`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_plugins_cache`
- `tests/inner/test_codex_executor.py::test_populate_codex_home_config_symlinks_remote_mcp_oauth`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_keeps_skill_symlinks_as_links`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_never_materializes_linked_skills[skill_dir]`
- `tests/inner/test_codex_executor.py::test_populate_codex_skills_copy_mode_never_materializes_linked_skills[skills_root]`
- `tests/inner/test_codex_hooks_generation.py::test_populate_symlinks_hooks_when_none_are_injected`
- `tests/inner/test_codex_hooks_generation.py::test_write_router_hooks_file_replaces_symlink_and_merges`
- `tests/inner/test_copy_on_write.py::test_resolved_alias_conflict_is_rejected`
- `tests/inner/test_credential_refresh.py::test_refresh_rejects_changed_private_symlink_target`
- `tests/inner/test_credential_refresh.py::test_refresh_revalidates_rotation`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_readable_refresh_sources[root-alias]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_readable_refresh_sources[source-alias]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[parent-link-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[parent-link-unix_socket]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-in-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-in-unix_socket]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-out-file]`
- `tests/inner/test_credential_refresh.py::test_rejects_sandbox_writable_refresh_sources[symlink-out-unix_socket]`
- `tests/inner/test_cwd_scan.py::test_walker_does_not_follow_symlink_loops`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_attachments_dir`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[False-False]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[False-True]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[True-False]`
- `tests/inner/test_native_attachments.py::test_materialize_cache_refuses_symlinked_destination[True-True]`
- `tests/inner/test_os_env_fork.py::TestCopyTree::test_symlinks_are_copied_as_symlinks`
- `tests/inner/test_os_env_grant_reach.py::test_contained_realpath_admits_a_symlink_loop_but_it_reaches_nothing`
- `tests/inner/test_os_env_grant_reach.py::test_contained_realpath_decides_on_the_symlink_target`
- `tests/inner/test_os_env_grant_reach.py::test_symlink_inside_grant_cannot_escape_grant`
- `tests/inner/test_pi_executor.py::test_gateway_seeds_managed_settings_from_global_agent`
- `tests/inner/test_pi_settings.py::test_prepare_managed_pi_agent_dir_copies_settings_and_symlinks_npm`
- `tests/inner/test_windows_attachments.py::test_symlink_leaf_cannot_be_reused_or_modified[False]`
- `tests/inner/test_windows_attachments.py::test_symlink_leaf_cannot_be_reused_or_modified[True]`
- `tests/inner/test_windows_powershell.py::test_resolved_batch_shim_is_rejected`
- `tests/inner/test_windows_powershell.py::test_resolved_store_target_is_rejected`
