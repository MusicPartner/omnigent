# Windows release integration record

## Scope and refs

- Date, operator and request:
- Fork URL/source branch/full SHA:
- Previous upstream stable tag/full SHA:
- Actual Git merge base/full SHA and difference from previous stable:
- Target upstream tag/full SHA and provenance:
- Selected merge/replay strategy, branch basis and reason:
- Integration branch/worktree/full SHA:
- Recoverable source ref and non-destructive rollback:
- Foreign edits, worktrees and installations to preserve:
- Current permissions: plan, implement, commit, push, Actions, publishing:
- Accepted differences, exclusions and policy-blocked resources:
- Missing/partial history and evidence:
- Original v0.14 contracts, later extensions and current owner mapping:

## Topic ledger

Use a companion CSV for large inventories. Reconcile the total against all
fork-changed paths and account explicitly for excluded or deferred content.

| Topic | Old path | Target path | Behavior | Disposition | Upstream evidence | Dependencies/owner | Verification | Result commit/status | Explanation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Worker preflight and ownership

| Owned paths | Actual model | Actual cwd/branch/HEAD | Resolved input refs | Absolute evidence directory | Acceptance | Attempt limit/used | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |

A prompt's cwd is not proof of execution there. Stop on mismatch. A missing or
policy-denied report does not count as completed evidence.

## Shared permission and attempt budget

| Round | Permission/counting rule | Source SHA | Push/dispatch/run IDs | Outcome | Remaining |
| --- | --- | --- | --- | --- | --- |

Count across coordinator, workers and handovers. State whether documentation
pushes and already-running checks count. Record renewed permission explicitly;
model/session changes do not reset a budget.

## Validation evidence

| Source SHA | Platform/selection | Exact command/run URL | Passed/skipped/deselected/errors | Raw summary/JUnit | Limits |
| --- | --- | --- | --- | --- | --- |

- Input closure unchanged since earlier checks, with path/diff evidence:
- Earlier runs not relabeled as final-source results:
- Policy-blocked scope, independent permitted checks and unrun hooks:
- New skip owners/capability reasons and retained portable assertions:

## Failure classification

| Node/job | Observed failure | Pristine-target result | Classification/evidence | Fix | Attempts | Remaining decision |
| --- | --- | --- | --- | --- | --- | --- |

## Artifact and runtime identity

- Build run/source SHA and immutable download URLs:
- Core/client/UI versions and packaged-module comparisons:
- Desktop source/mode/signing/architecture:
- Clean-wheel imports and disposable install/uninstall:
- Exact executable/launch command, version and instance UI URL:
- Later changes invalidating older evidence:

## Human acceptance

- Fresh Claude/Codex/Copilot sessions and supported economical models:
- Other-drive/space/Unicode workspace, breadcrumbs and worktrees:
- Two-pane short/multiline/large paste and chat resume:
- Native shell command, Stop Session and follow-up:
- Desktop Quit, owned descendant exit and independent CLI survival:
- Image/ZIP reads and Stop/resume in the actual vendor sandbox:
- Unperformed checks and intentional support limits:

## Handover

- Final refs, topic dispositions and differences:
- Next exact step and active run IDs:
- Remaining permissions/attempts and decisions:
- Config/data backup and rollback without downgrading migrated databases:
- Demonstrated lessons added to the maintained skill:
- Superseded assumptions and evidence:
- Maintained skill and post-check result locations if no push remains:
