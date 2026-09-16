# Fork maintenance workflows

This fork keeps the native Windows changes while continuing to ingest stable releases from `omnigent-ai/omnigent`.

## Normal upstream release flow

1. `Sync upstream release` runs daily on the default branch. It resolves the latest non-prerelease GitHub release from `omnigent-ai/omnigent`.
2. If that upstream release commit is already an ancestor of this fork's `main`, the workflow exits without changes.
3. Otherwise it creates or refreshes `upstream-sync/<tag>`, merges the upstream release commit into that branch, and opens a PR to `main`.
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

`Fork release validation` runs for pull requests, for pushes to `main`, for the transitional `windows-parity/v0.14-integration` branch, and by manual dispatch. It has three gates:

1. **Focused Linux compatibility**: Ruff plus the Windows integration surfaces and focused tests.
2. **Native Windows compatibility**: import/CLI smoke, the Windows-safe test subset, psmux installation/lifecycle tests, and a non-blocking broader Windows unit sweep.
3. **Windows artifact build**: production web UI build, core + lockstep SDK distributions, Twine metadata checks, bundled web UI assertion, clean wheel install/import smoke, SHA-256 checksums, and artifact upload.

The build job only runs after both compatibility jobs pass. Uploaded bundles are named `omnigent-windows-<commit-sha>` and are retained for 30 days.

## Workflow ownership

The fork-specific maintenance layer is intentionally limited to:

- `.github/workflows/upstream-sync.yml`
- `.github/workflows/fork-release-ci.yml`

Upstream's existing general CI and release workflows are left unchanged. This minimizes merge conflicts when new upstream releases are integrated.
