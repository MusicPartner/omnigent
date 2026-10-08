# Fork maintenance workflows

This fork keeps the native Windows changes while continuing to ingest stable releases from `omnigent-ai/omnigent`.

## Normal upstream release flow

1. `Sync upstream release` runs daily on the default branch. It resolves the latest non-prerelease GitHub release from `omnigent-ai/omnigent`.
2. If that upstream release commit is already an ancestor of this fork's `main`, the workflow exits without changes.
3. Otherwise it creates `upstream-sync/<ref>-<run>`, merges the upstream release commit into that branch, and opens a PR to `main`.
4. The sync workflow explicitly dispatches `Fork release validation` on the sync branch. This is necessary because PRs created by the repository `GITHUB_TOKEN` do not themselves start ordinary PR-triggered workflows.
5. Review the upstream diff and merge the PR only after validation passes.
6. The push to `main` runs `Fork release validation` again and produces a fresh Windows artifact from the merged commit.

A merge conflict stops the sync workflow before it pushes a branch. The workflow summary lists the conflicted files so the integration can be resolved deliberately instead of silently preferring either side.

## Manual sync

Run **Actions -> Sync upstream release -> Run workflow**.

- `upstream_ref=latest-release` syncs the latest stable upstream GitHub release.
- `upstream_ref=main` syncs current upstream `main`, including unreleased commits.
- A tag such as `v0.15.0`, another branch, or a commit SHA can also be supplied.
- `target_branch` defaults to this fork's `main`.

The workflow always uses a PR; it does not push an upstream merge directly into `main`.

## Release validation

`Fork release validation` runs for non-documentation pull requests, for non-documentation pushes to `main` and the transitional `windows-parity/v0.14-integration` branch, and by manual dispatch.

Compatibility validation always runs for a normal code PR. The downloadable Windows artifact is deliberately built only for a push/merge or a manual dispatch. This prevents every intermediate PR commit from consuming another Windows build runner while still validating the code before merge.

The three stages are:

1. **Focused Linux compatibility**: Ruff plus the Windows integration surfaces and focused tests.
2. **Native Windows compatibility**: import/CLI smoke, upstream's hard Windows pair, the Windows-safe test subset, psmux installation/lifecycle tests, and a non-blocking broader Windows unit sweep.
3. **Windows artifact build**: production web UI build, core + lockstep SDK distributions, Twine metadata checks, bundled web UI and `omni`/`omnigent` entry-point assertions, clean wheel install, artifact-installer/uninstaller round-trip, checksums, and artifact upload.

Uploaded bundles are named `omnigent-windows-<commit-sha>` and are retained for 30 days. See `docs/windows/QUICKSTART.md` for installation, upgrades, local connection, and smoke testing.

## Housekeeping

`Fork housekeeping` lives on the default branch and runs weekly or manually. It has two responsibilities:

- Disable upstream-only automation that is not useful in this fork, such as publishing/release, benchmark, reviewer assignment, doc-sync, merge-monitoring, and mobile bundle workflows. Core CI, Lint, E2E, E2E UI, native Windows, security/Trivy, and the fork workflows remain enabled.
- Delete same-repository branches matching `maintenance/*` or `upstream-sync/*` only after their PR has been merged and no Actions run is still active. Completed runs for those transient branches are also removed after the configured short retention window.

`main` and `windows-parity/v0.14-integration` are explicitly protected by the housekeeping policy.

## Workflow ownership

The permanent fork-specific layer is intentionally small:

- `.github/workflows/upstream-sync.yml` — ingest upstream releases through a PR.
- `.github/workflows/fork-release-ci.yml` — focused Linux/Windows validation and the installable Windows artifact.
- `.github/workflows/fork-housekeeping.yml` — keep transient branches/runs and fork-irrelevant upstream automation under control.

Upstream's core test workflows stay available instead of being forked into custom copies. Fork-only policy is concentrated in these files to minimize merge conflicts during future upstream releases.

## Windows isolation topic map (v0.14)

Windows-specific mechanics live in leaf modules so shared modules keep only their `IS_WINDOWS` branch and a call to the helper. Code was extracted verbatim, so existing monkeypatch targets on the callers still work.

| Topic | Windows leaf module(s) | Caller seam (keeps the `IS_WINDOWS` branch) | Tests |
| --- | --- | --- | --- |
| psmux terminal backend | `omnigent/terminals/psmux.py` | `omnigent/terminals/backend.py` re-exports the psmux classes unconditionally | `tests/terminals/test_windows_psmux.py` |
| Web workspace breadcrumbs | `web/src/shell/hostPaths.ts`, `web/src/shell/workspaceBreadcrumbs.ts` | `web/src/shell/WorkspacePicker.tsx` re-exports them | `web/src/shell/workspaceBreadcrumbs.test.ts` (existing helper tests remain in `WorkspacePicker.test.tsx`) |
| Host listing | `omnigent/host/host_listing.py` | `omnigent/host/connect.py` (`_handle_list_dir`) | `tests/host/test_host_listing.py` |
| Runner python probe | `omnigent/runner/python_probe.py` | `omnigent/runner/environment_filesystem.py` (`_python_shell_command`) | `tests/runner/test_python_probe.py` |
| Command parsing | `omnigent/native/shell.py` (`split_command()`) | `omnigent/inner/acp_executor.py`, `omnigent/update_check.py`, `omnigent/native/_native_resume_hint.py` | `tests/test_native_shell.py` |
| Codex CLI | `omnigent/inner/codex_windows.py` | `omnigent/inner/codex_executor.py` (`_find_codex_cli`) | `tests/inner/test_codex_windows.py` |
| Claude hooks | `omnigent/harnesses/claude_native/windows_hooks.py` | `omnigent/harnesses/claude_native/bridge.py` (readiness/lifecycle policy stays here) | `tests/test_claude_native_windows_hooks.py` |
| Shutdown | `omnigent/inner/_windows_shutdown.py` | `omnigent/inner/_proc.py` (`terminate_tree`), `omnigent/runtime/harnesses/_runner.py` | `tests/inner/test_windows_shutdown.py` |
| Native env | `omnigent/runner/native/windows_env.py` | `omnigent/runner/native/orchestration.py` (`_claude_terminal_env_unset`) | `tests/runner/test_native_windows_env.py` |

Left in place on purpose:

- The runner transport locator and sandbox-capability seams.
- General (non-Windows) fixes: catalogs, SSE readiness, worktree error handling, and shared UI fixes.
- Upstream path helpers other than the four moved to `hostPaths.ts` stay in `WorkspacePicker.tsx`.

Rules:

- New Windows mechanics go into a leaf module, not a shared module.
- Psmux tests that monkeypatch `IS_WINDOWS` or `shutil` must patch `omnigent.terminals.psmux`.
- `workspaceBreadcrumbs.ts` and `hostPaths.ts` must not import `WorkspacePicker.tsx` (oxlint `import/no-cycle`).
