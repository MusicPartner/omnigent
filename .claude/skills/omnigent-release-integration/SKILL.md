---
name: omnigent-release-integration
description: "Use when planning, implementing or resuming an upstream Omnigent stable-release integration into the Windows fork, updating its handover, or planning Windows isolation. Covers historical contracts, merge versus replay, semantic ledgers, economical delegation and source-matched validation; not new harnesses or ordinary package publishing."
---

# Omnigent release integration

Carry the latest validated Windows behavior onto an explicit stable upstream
release with a reviewable delta. Use Plan, Implement, Validate phases only as
authorized. Plan-only stops before branch construction or runtime edits.
Historical permissions and transcripts are evidence, not new authorization.
Save planning documents only when requested or required by the current workflow.

## Establish source, target and permissions

1. Read the chosen checkout's `AGENTS.md`, scoped guidance and
   `.github/FORK_MAINTENANCE.md`. Record repository, branch, full HEAD, dirty
   paths, worktrees and remotes. Preserve foreign edits, installations and live
   sessions. An editor checkout can still be v0.14 while the source is v0.19.
2. Use [sources.md](./references/sources.md) for targeted handover recovery.
   Distinguish full transcripts, recovered prompts and summaries. Prefer latest
   user corrections, actual code and raw results. Report missing history.
3. Resolve the exact upstream stable tag and full SHA. If asked for latest,
   resolve it now. Record fork source, previous upstream release and actual Git
   merge base separately. `origin/main` is the fork; upstream main can be newer
   than the stable release. Do not accidentally integrate development main.
4. Record scope, accepted differences, retry/cost rules and separate permission
   for local implementation, commits, pushes, Actions and publishing in the
   [integration record](./assets/integration-record.md).

The v0.19 integration used a new branch, not promotion to main. Existing
boundaries: no PR to main, no WSL, local native Windows validation where
permitted and Linux coverage in Actions. Main automation became manual-only
on 2026-10-21; preserve that policy unless explicitly changed. Do not backport
to unused v0.14 or reuse one-off registry/TLS/cleanup permissions.

## Choose a strategy once

Use the latest validated Windows integration as the next source, not an older
editor checkout. Record the strategy before constructing a unique worktree:

- **History-preserving merge:** branch from the Windows source and merge the
  exact stable SHA. Prefer when ancestry is useful and obsolete policy can be
  reconciled safely. v0.17-to-v0.19 retained both source histories this way.
- **Semantic replay:** branch from the stable SHA and port behavior in attributed
  topic commits when that makes a reorganized delta more reviewable.

Both require a recoverable source ref and semantic ledger. Neither permits
rewriting published history, moving an existing backup, promoting main or
repeatedly changing branch basis without new evidence and a recorded reason.

## Inventory behavior, not only conflicts

Compare the cumulative fork diff from its previous upstream release, including
mixed commits and merge resolutions. Commit subjects and `git cherry` do not
prove semantic coverage. Check stable target code first, then upstream main,
merged fixes and relevant issues; label proposals as proposals.

Use one row per changed file:

`topic, old_path, target_path, behavior, disposition, upstream_evidence,
dependencies, owner, verification, result_commit, status, explanation`

Dispositions: `REPLAY`, `RECONCILE`, `DROP-UPSTREAM-COVERS`, `DROP-OBSOLETE`,
`REVIEW`. Every drop/deferral needs preserved behavior/tests and an explanation.
Recompute the prior ledger against the new target. Include general fixes,
test portability and release infrastructure, not only `IS_WINDOWS` files.
Keep review/live-acceptance gaps explicit even after automated checks pass.

Start with the current maintenance topic map; retarget moved callers/tests.
Keep stable release versions, lockstep SDK pins and locks unless an actual
dependency change requires regeneration. Inspect dependency groups instead
of copying obsolete `uv sync --extra dev` commands.

For new isolation, first map original v0.14 contracts to current owners, tests
and support limits. The original release-port ledger describes v0.17, not
v0.19. Do not restore obsolete code or old patch targets. Package 1 establishes
contract tests/primitives; package 2 reduces duplicated terminal preparation.
See the [staged isolation plan](../../../docs/windows/ISOLATION-PLAN-0.19.md).
Planning alone does not authorize those runtime refactors.

## Delegate bounded work economically

Use current model availability and user constraints, not historical price or
availability claims. GPT-6 Luna was explicitly used for v0.19 bulk coding;
other previously accepted choices included GPT-6.1 Sol and recent Haiku/Sonnet.
These are preferences, not a requirement to override tool defaults without a
current applicable model instruction.

| Work | Allocation |
| --- | --- |
| Inventories, log triage, mechanical tests and bounded ordinary implementation | Lower-cost recent model when available and authorized |
| Ambiguous API/ownership decisions and final reconciliation | Coordinator; escalate only the difficult slice |

Delegate only independent substantial scopes with disjoint file ownership.
Supply immutable refs, owned paths, acceptance and task-specific attempt limits.
Workers report actual cwd/repository, branch, full HEAD, resolvable input refs
and absolute evidence directory before editing. A cwd in a prompt is not proof.
Stop on mismatch; never guess ref abbreviations or write relative `sessionfiles/`
into a checkout. Bound report output; policy-denied reports are not evidence.

Verify actual diffs/tracebacks rather than trusting a worker summary or a green
exit code from an unrelated command. Review one failed approach before repeating
it. Do not replace an active worker just to alter model selection unless asked.
If explicit model selection is unavailable, disclose that; never claim it was
used or change global settings. Batch independent reads and serialize shared
terminal/index operations and resource-heavy checks.

## Reconcile with narrow platform seams

Read [Windows lessons](./references/windows-lessons.md) for touched launch,
terminal, lifecycle, attachment and installer surfaces. Keep Windows mechanics
in leaf modules with thin callers. Preserve upstream APIs, settings/lifecycle
policy, credential refusals and POSIX behavior. Windows adapters transport
canonical policy rather than duplicating it.

Audit clean merges as well as conflicts: factory arguments, status wrapping,
environment/correlation, launch-failure cleanup, hook/readiness keywords and
actual test injection owners. Prefer the existing backend injection seam to
restoring stale test-only exports. Inspect skip decorators by owning symbol
after clean applies and preserve both upstream and fork assertions.

Use topic commits and maintain the ledger while working. Follow `AGENTS.md`
hooks before committing; inspect actual hook definitions on Windows and record
permitted underlying-tool substitutions and unrun hooks honestly. Preserve
attribution. Do not commit raw transcripts, credentials or demo captures.

## Validate and count attempts honestly

- Run focused native Windows checks first; collect broader tests separately.
  Use current helper/CI selections and verify Python imports the chosen source.
  Real psmux is serial with private data/session names; isolate homes, ports
  and installer prefixes. Never terminate unowned processes.
- Diagnose failed nodes before repeating a broad sweep. Separate introduced
  defects, pristine-target failures, platform scope and optional dependencies.
  Preserve a skip inventory; do not install unused Databricks support.
- Read raw summaries/JUnit. A non-blocking green job is not a passing suite;
  timeout is incomplete. A retry pass does not prove the earlier root cause.
- Track the user's push/retry counting rule in one shared ledger before each
  round, across coordinator/workers/handovers. Count documentation-only pushes
  when included. Batch independent known fixes; avoid rerunning full E2E for
  unchanged input closures. Reserve handover capacity or record results
  externally without another push. Old four/five-attempt caps are not defaults.
- Once a resource or executable is policy-denied, do not retry via aliases,
  other tools or recreated environments. Record the blocked scope and use
  independently permitted checks. Remote checks need current authorization.
  A user's manual command fragment is not a verified hook pass.

## Publish only within current scope

For authorized pushes/Actions, use explicit repository and branch; verify each
run's `headSha`. Inspect triggers and disabled workflows before dispatch.
Do not reactivate main schedules or upstream publishing as an integration side
effect. Validate fork release, integration, backend E2E, UI/Browser Contract
and Docker as applicable. Default Docker verification to `publish=false`.
Avoid duplicate dispatches that cancel each other.

Associate every result with its source SHA and relevant input closure. Earlier
passing runs are never relabeled as final-SHA runs. Download source-matched CLI
and desktop artifacts when in scope; verify core/client/UI versions, packaged
modules, source metadata, clean-wheel imports and disposable install/uninstall.
Version labels alone do not identify a build. Distinguish dev/unsigned/opt-in
artifacts and human acceptance from production release claims.

Provide exact artifact/launch instructions, refs, topic dispositions, evidence,
intentional support limits and rollback. Follow human checks in the lessons.
Update the record and this skill with demonstrated reusable lessons only.
Keep a reviewed skill copy in the maintained lineage, not just an untracked
old checkout. Index final results and limits without raw private logs or an
extra push after the allowance is exhausted.
