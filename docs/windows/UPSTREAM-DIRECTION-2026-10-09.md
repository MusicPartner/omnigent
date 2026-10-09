# Upstream direction and Windows integration decisions

Research date: 2026-10-09. This is a read-only upstream assessment, not an
upstream merge or an implementation of the proposed changes.

## Snapshot and method

- Latest stable release checked: [v0.17.0](https://github.com/omnigent-ai/omnigent/releases/tag/v0.17.0), published 2026-10-06.
- Upstream main snapshot: [`2e1cd1507dcde67f873d08ef3d28f4cf85bb4440`](https://github.com/omnigent-ai/omnigent/commit/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440), committed 2026-10-09 07:09 UTC.
- Fork snapshot for the overlap calculation: `6152db7e855e3c45a211d018750c4c4747f42aa9`.
- Reviewed the latest 100 commits, latest 100 updated PRs/issues, targeted topic searches, relevant file histories, PR bodies/statuses and selected discussions. Searches are bounded; absence from these results does not prove that no related proposal exists.
- Source was read at the fixed main SHA. PR merge status was checked separately: closed does not mean merged, and automated review approval does not establish maintainer acceptance.

Main is 171 commits ahead of the release's common ancestor and does not contain
the release branch's final version-bump commit. Compare reports 171 ahead / 1
behind. That release commit changes six version/lock files. Treat main as an
early warning source; keep integration based on an explicit stable release.

## Product direction supported by the evidence

Upstream continues to invest in native CLI sessions, shared model/provider
selection, managed hosts and cross-device session delivery. These are active
shared product contracts, not areas to replace with Windows-specific policy.

- [Merged #7783](https://github.com/omnigent-ai/omnigent/pull/7783) adds per-harness inference providers, curated model selection and creation-time policy snapshots. Managed sessions retain accepted routing across resume and replacement.
- [Merged #9375](https://github.com/omnigent-ai/omnigent/pull/9375) distinguishes catalog availability from the absence of a default marker. [Merged #7724](https://github.com/omnigent-ai/omnigent/pull/7724) makes model reset behavior depend on harness capabilities.
- [Merged #9587](https://github.com/omnigent-ai/omnigent/pull/9587) settles messages held by Claude prompts. [Merged #9515](https://github.com/omnigent-ai/omnigent/pull/9515) loads Codex project configuration from the session workspace. Native session correctness remains actively maintained.
- [Merged #6770](https://github.com/omnigent-ai/omnigent/pull/6770) makes brokered model authentication fail closed, with an isolated worker and a trusted signer. Compatibility fallbacks cannot expose host credentials or silently remove containment.

Windows is a different support boundary. On October 6, repository member
fanzeyi wrote: "we don't have spare bandwidth on Windows support right now."
See the [maintainer comment on #2422](https://github.com/omnigent-ai/omnigent/issues/2422#issuecomment-6006984859).
[Merged #5519](https://github.com/omnigent-ai/omnigent/pull/5519) disables native
terminal harness availability on Windows, and that gate is still present in
[the snapshot's readiness code](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/onboarding/harness_readiness.py#L234-L237).

The earlier [psmux PR #2205](https://github.com/omnigent-ai/omnigent/pull/2205)
and [Windows foundation PR #2308](https://github.com/omnigent-ai/omnigent/pull/2308)
were closed without merging. Their author explicitly paused the stack for
further work on the fork. These are historical proposals, not an accepted
upstream Windows roadmap. Our psmux integration therefore remains an explicit
fork capability. Do not assume upstream will soon absorb or maintain it.

## Decision-by-decision assessment

| Decision | Upstream evidence | Recommendation for the fork | Remaining uncertainty / cost |
| --- | --- | --- | --- |
| Sandbox launcher | Merged #4586 preserves `create_exec_launcher(...)->str`; current SDK and executors still consume a filename. | Prototype a Windows executable behind this same contract, in a Windows leaf module. Keep POSIX generation and public caller APIs unchanged. | Executable packaging, architectures, argv, lifetime and Job Object ownership still need proof. Upstream has not selected a Windows executable implementation. |
| Claude hook compatibility | Current floor is 2.1.161; hook args were introduced in 2.1.139. CI pins 2.1.266. | Reuse the upstream readiness floor and test direct hook argv on the oldest supported Windows CLI and the CI pin. Avoid a separate older-version support policy. | Version numbers establish a candidate compatibility range, not a Windows behavior proof. Preserve status-line and shell-only hook behavior until individually handled. |
| PowerShell | Current shell tooling selects Bash/sh; open #8660 explicitly selects Git Bash on Windows. | Do not impose PowerShell 7.3+ on ordinary launches. Quote for each actual consumer; isolate popup capability checks. | Popup shell requirements and fallback behavior remain local platform work. Git Bash and PowerShell are distinct consumers. |
| Exact pane exit codes | Merged #9005/#9008 preserve shutdown/failure evidence and explicit unknowns. Main still uses tmux exit status; it contains no psmux backend. | Keep Windows numeric exit status unknown; feed existing lifecycle evidence into upstream's owners. | Accurate numeric status requires dependency support or a separately justified protocol. No reason to add a parallel lifecycle system now. |
| Windows trusted signer | Merged #6770 requires active OS isolation as well as provenance validation; Windows Job Objects lack filesystem/network isolation. | Defer the full Windows brokered-signer feature, preserving refusals. Scope ordinary gateway token minting separately. | ACL/SID checks alone are insufficient. A suitable containment backend, credential separation and lifecycle proof are prerequisites. |
| v0.14 backport | Releases continue forward through v0.17; the inspected material establishes no v0.14 maintenance commitment. | Use v0.17 as the active integration base. Backport only for a known deployed v0.14 user. | Which versions you still operate is a local maintenance decision; upstream research cannot answer it. |
| Default model behavior | Merged #7783/#7724/#9375 preserve managed selection and harness-specific defaults; open #7773 preserves explicit native configuration. | Preserve upstream mode-specific behavior. Avoid a Windows-wide switch between catalog pinning and CLI defaults. | Pending fixes may alter the shared selection code; review them when merged rather than implementing a competing policy. |

### Launcher: the filename contract is deliberate

[Merged #4586](https://github.com/omnigent-ai/omnigent/pull/4586) corrected POSIX
shebang failures without changing callers. Main still returns a single filename
from [create_exec_launcher](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/inner/sandbox.py#L1235-L1278)
and the SDK consumes it as
[cli_path](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/inner/claude_sdk_executor.py#L1350-L1428).
This makes the existing executable prototype recommendation stronger. An
all-Python argv-prefix refactor would modify multiple shared callers and SDK
transport behavior with no inspected upstream proposal supporting that change.

Windows main still emits a `.py` launcher. [Closed, unmerged #5826](https://github.com/omnigent-ai/omnigent/pull/5826)
proposed avoiding it for the Claude SDK's Job Object backend, with native tools
disabled. A bot review supported the narrower fix, but a maintainer closed the
PR and the shortcut is absent from current source. It is useful evidence of
the failure and containment limits; it is not an adopted upstream solution.
Neither restoring `.py` forwarding nor copying this closed workaround is an
answer to the fork's general literal-argv requirement.

### Hooks: avoid creating a second version policy

[Current harness_install.py](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/onboarding/harness_install.py#L103-L127)
uses Claude 2.1.161 as a shared supported floor. The
[CI manifest](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/.github/actions/setup-harness-cli/manifest.json)
pins 2.1.266. [Closed, unmerged #8440](https://github.com/omnigent-ai/omnigent/pull/8440)
proposed 2.1.280 for newer model requirements; that is not the current floor.
The [Claude changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21139)
places command-hook args at 2.1.139.

Consequently, a legacy hook path solely for pre-2.1.139 clients would support
versions upstream already rejects. Prefer direct argv for eligible command
hooks once Windows tests prove the supported floor and CI version. Keep that
transport choice additive to the canonical bridge settings generator; do not
copy its lifecycle, policy, routing or hook list into a Windows implementation.
Shell pipelines/redirection and status-line commands need their own treatment.
The local proof on 2.1.294 does not validate those older supported binaries.

### Authentication: distinguish login minting from the brokered signer

[model_auth.py](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/inner/model_auth.py#L84-L101)
still uses POSIX provenance checks. More significantly,
[the worker refuses ineffective spawn containment](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/inner/codex_worker.py#L113-L183).
The [Windows backend](https://github.com/omnigent-ai/omnigent/blob/2e1cd1507dcde67f873d08ef3d28f4cf85bb4440/omnigent/inner/windows_jobobject_sandbox.py#L13-L27)
provides process-tree containment, not the filesystem/network boundaries that
the brokered signer requires. Keep the exploratory auth timeout as a real
portability defect, but do not equate a portable fixture with a supported
Windows brokered-auth feature.

[Open #8657](https://github.com/omnigent-ai/omnigent/pull/8657) instead ports
ordinary OpenAI-harness gateway token minting away from `sh`. It does not
supply brokered worker isolation. [Open #9475](https://github.com/omnigent-ai/omnigent/pull/9475)
proposes user-owned Databricks managed hosts without server-identity fallback;
that is another distinct auth surface. None of these proposals justifies
weakening the already merged signer's requirements.

### Model defaults: preserve modes rather than choose one global rule

[Open #7773](https://github.com/omnigent-ai/omnigent/pull/7773) carries an explicit
`--use-native-config` preference through daemon launch/resume. Ordinary managed
launches keep provider resolution and catalog-derived selection. It is not
merged, so it is a watch item rather than an available upstream fix.
[Open #9247](https://github.com/omnigent-ai/omnigent/pull/9247) proposes model/client
compatibility fallback while preserving explicit picks and the global floor.
Do not implement a Windows-only global-default rule that competes with these
shared semantics.

## Merge-risk assessment

GitHub's compare endpoint returned its maximum 300 files. The overlap count
therefore uses both complete recursive Git trees instead; both reported
`truncated=false`. Relative to v0.17.0, upstream main changes 949 file paths and
the fork snapshot changes 212. Their intersection contains 51 paths.
**These are overlapping changes, not proven merge conflicts.** No trial merge
or runtime test was performed for this research.

The highest-value review areas are:

| Area | Shared files to inspect | Why |
| --- | --- | --- |
| Claude terminal launch | `harnesses/claude_native/bridge.py`, `main.py`, related tests | Active prompt delivery, shutdown evidence, skill loading and model-policy changes. |
| Native orchestration | `runner/native/orchestration.py`, `resource_routes.py`, `routing.py` | Provider/config routing and terminal lifecycle must stay upstream-owned. |
| Host/readiness | `host/connect.py`, onboarding readiness/version helpers | Keep source catalog and CLI probes authoritative; retain fork platform capability gates at their seams. |
| SDK/process tools | `inner/claude_sdk_executor.py`, `codex_executor.py`, `acp_executor.py`, `os_env.py` | Preserve launcher, credentials, imports and containment contracts. |
| Web session/terminal UI | `NewChatDialog.tsx`, `TerminalsPanel.tsx`, `TerminalSession.ts`, `chatStore.ts` | Compare behavior before replaying older Windows UI fixes. |

[Merged #9540](https://github.com/omnigent-ai/omnigent/pull/9540) adds Python `-P`
to the OS helper's module launch so a broken working-tree package cannot shadow
the installed runtime. The fork also edits this helper. Preserve both the
upstream import protection and our direct Windows argv/config-file behavior
when integrating the next release; do not choose one entire version of the file.

Platform leaves reduce conflict surface, but extracted code can still drift
without a textual conflict. Compare each leaf's original upstream function with
the new release before retaining it. Keep readiness, readiness-cache identity,
runner refusal and CLI launch support synchronized around the psmux capability.

## Watch list: proposals are not product commitments

| Item | Status at research time | What to watch |
| --- | --- | --- |
| [#8660](https://github.com/omnigent-ai/omnigent/pull/8660) | Open | Git Bash selection and avoiding the WSL launcher. |
| [#9542](https://github.com/omnigent-ai/omnigent/pull/9542) | Open | Whole-process-tree cleanup for timed-out readiness probes. |
| [#9074](https://github.com/omnigent-ai/omnigent/pull/9074) | Open | Shared environment passthrough while denying runner auth tokens. Preserve those exclusions in Windows launchers. |
| [#8750](https://github.com/omnigent-ai/omnigent/pull/8750) | Open | Codex sandbox fallback, launcher policy serialization and egress changes. |
| [#7773](https://github.com/omnigent-ai/omnigent/pull/7773), [#9247](https://github.com/omnigent-ai/omnigent/pull/9247) | Open | Native-config persistence and client-aware model defaults. |
| [#8749](https://github.com/omnigent-ai/omnigent/pull/8749) | Closed, unmerged | Large package-relocation proposal. Do not rename our packages preemptively; adapt leaves if an equivalent refactor actually lands. |

## Recommended maintenance policy

1. Integrate stable release tags in isolated branches. Read main and the watch list for advance warning; do not silently promote unreleased proposals into the supported release.
2. Keep upstream launch APIs, routing/model policy, bridge lifecycle and security ownership. Add small platform calls into Windows leaves instead of replacing whole shared functions.
3. For the launcher, prototype the existing filename contract first. Prefer a Windows executable over a multi-executor/SDK transport redesign, subject to packaging and lifecycle proof.
4. For command hooks, share the upstream supported version floor and validate Windows behavior. Add shell-specific formatting only where a shell is the actual consumer.
5. Defer full brokered signer support until real isolation can satisfy upstream's requirements. Keep unknown psmux exit status and existing lifecycle evidence.
6. At each release, refresh the overlap ledger and remove fork hunks whose behavior upstream now supplies. Then run the focused Windows, Linux and branch workflow checks already defined in the parity plan.

The choices still needing local input are the executable prototype's supported
Windows architectures, whether full Windows brokered auth
is a release requirement, and whether any deployed v0.14 installation requires
maintenance. Upstream evidence narrows the implementation choices but cannot
make those deployment and support commitments for this fork.

To verify this assessment manually, open the pinned source links and the PRs
marked merged/open/closed above. Recheck state before using a pending proposal.
For a new release, recompute the complete-tree overlap and inspect changed
callers plus extracted leaf originals; this research does not certify a future
merge or change the already built application's behavior.
