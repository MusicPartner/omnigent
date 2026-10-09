# Windows parity: remaining work and decisions

Research date: 2026-10-08. Branch: `windows-parity/v0.17-integration`.
Current pushed code: `28db4f72c973b15a96b00de29e11f3f93509c246`.
Previously validated baseline: `2d43e9d95c28d4cb623f98d3d49de1af959f90cc`.
This record separates the new consumer fixes and blocked decisions from the
baseline validation retained below.
Upstream direction was reviewed on 2026-10-09 in
[the evidence and merge-risk assessment](UPSTREAM-DIRECTION-2026-10-09.md).
Its recommendations below distinguish merged upstream contracts from proposals.
The accepted [implementation plan](IMPLEMENTATION-PLAN-2026-10-09.md) delegates
the work and excludes v0.14 backporting, as confirmed by the user.

## 2026-10-09 implementation outcome

The distlib executable prototype was rejected for production adoption. Native
Windows x64 tests proved literal argv, spaced/Unicode interpreter and cwd,
stdin/stdout/stderr, exit code 37 and executable deletion. A deterministic
process test also proved the blocker: Python and its target can start before
parent-side `post_spawn()` assigns the outer executable to a Job Object. Closing
that job terminates the outer executable while existing descendants survive.
The test cleans up its owned processes; its passing result records this defect,
not successful containment. This deliberately late assignment was not compared
with the existing `.cmd` launcher, so it does not establish a new regression.
Any launcher that starts descendants before assignment can have this race.

Only the test-owned prototype and evidence are retained. The production sandbox
seam and core dependencies are unchanged, so `.cmd` `%*` forwarding remains
unresolved. No clean-wheel, ARM/x86 or filesystem/network isolation claim follows
from this prototype. Existing credential rules and brokered-signer refusals
remain unchanged.

Package B adopts direct executable + args for eligible Windows command hooks,
with Python-owned stderr handling and the canonical shared hook definitions.
It also retains explicit consumer quoting, Git Bash status-line handling,
popup/bootstrap/fallback behavior and PowerShell-labelled resume hints.
Ordinary launches do not gain a PowerShell prerequisite.

Package C's tracked gated capture passed all three native Claude versions:
supported minimum **2.1.161**, CI pin **2.1.266**, and installed local **2.1.295**,
with psmux **3.3.8**. Each run preserved its start/end CLI version, exact
**9,283-byte settings** and **five literal Setup-hook arguments**, plus MCP JSON.
The isolated `--init-only` fixture uses a dummy key and loopback endpoint without
provider responses or real prompts. It compares production SessionStart settings
but does not execute canonical SessionStart or prove a full conversation.
Module/unit checks cover shared generation; branch CI completed successfully.
The shared Windows argv parser is included in required CI; real capture is an
explicit opt-in test against an existing native executable.

The original five-attempt limit and subsequent automatic-review rejection are
historical. The user revoked that limit and authorized the successful resumed
capture. Launcher containment and brokered-signer isolation remain unresolved;
no new ARM/x86 runtime support is claimed. v0.14 remains excluded.

## Current-pass validation

| Check | Result and limit |
| --- | --- |
| Isolated x64 launcher prototype | 3 passed, including the reproducible failed-containment assertion; no runtime adoption. |
| Package B focused native tests | 50 passed; 1 POSIX `fcntl` check deselected. Actual PowerShell popup and Git Bash status-line Unicode/stdin checks passed. |
| Canonical bridge/policy/framework/status integration subset | 4 passed. |
| Earlier broad Windows bridge sweep | 507 passed, 2 skipped, 5 failures from unchanged Unix-socket harness assumptions (`server.json['socket']`). This earlier sweep is not all green; it is separate from the current branch workflow below. |
| Direct-hook real-Claude capture | 2.1.161, 2.1.266 and 2.1.295 passed with psmux 3.3.8; exact 9,283-byte settings, MCP JSON and five literal Setup-hook args; start/end versions matched. Setup-only scope, not a full conversation. |
| Local production build | UI packaged 519 files including index; fresh core/client/UI SDK wheels all 0.17.0. Stamp: `0.17.0 (28db4f72, built 2026-10-09T08:42:50Z)`. |
| Clean isolated wheel install | Server app, Windows hooks/status/shell, shared observer and both SDK imports passed outside the checkout; `omni`/`omnigent --help` and `--version` passed. Editable environment preserved. |
| Applicable pre-commit hooks | Passed on the staged parity documentation files. |

The following workflows target pushed code `28db4f72c973b15a96b00de29e11f3f93509c246`.
All completed successfully. The older baseline validation below does not cover
these edits.

| Branch workflow | Status |
| --- | --- |
| [Fork release validation](https://github.com/MusicPartner/omnigent/actions/runs/37906485467) | Success; native Windows compatibility, focused Linux compatibility and Windows artifact build jobs passed. Windows imports/CLI smoke, upstream hard tests, stable subset, hook/shell consumer tests, psmux backend tests and argv helper steps passed. The broad sweep step metadata says success, but its raw test summary is unavailable with current GitHub permissions. |
| [Integration](https://github.com/MusicPartner/omnigent/actions/runs/37906672686) | Success; integration and security gate jobs passed. |
| [E2E](https://github.com/MusicPartner/omnigent/actions/runs/37906676224) | Success; setup and security gate passed, and all 4/4 E2E test shards passed. |
| [E2E UI](https://github.com/MusicPartner/omnigent/actions/runs/37906679337) | Success; setup, browser contract and sidecar build passed, and all 10/10 UI test shards passed. |
| [Docker](https://github.com/MusicPartner/omnigent/actions/runs/37906708091) | Docker build and security gate passed; image publishing was skipped (`publish=false`). |

All five runs report attempt 1 and the same commit SHA; no workflow-level rerun
was made. The workflow/job metadata confirms terminal conclusions and shard/job
outcomes. GitHub's raw job-log endpoint returned HTTP 403 (admin rights
required), so the broad Windows sweep's pytest totals and any internal pytest
retry counts could not be independently read. Its step conclusion is reported
as success; no more detailed test-count or flakiness claim is made here.

### Next launcher decision

The executable remains deferred. Choose a prototype direction after explicitly
reviewing its ownership contract; neither option below has been implemented.

| Direction | Benefit | Cost and proof required |
| --- | --- | --- |
| **Recommended: native stub owns a private job** | Preserves the filename-only SDK API and avoids migrating every caller; stub termination can close its private job and kill the child tree. | Adds containment ownership and maintained native assets. Prove creation-time assignment, nested host jobs, SDK cancellation, packaging/signing and native x64 execution. |
| Parent-coordinated spawn/SDK integration | Keeps job ownership wholly with the parent and assigns the exact job before launcher execution. | Requires coordinated suspended/creation-time spawning, resume and failure cleanup across callers and the SDK; broader maintenance surface. |

The detailed [assessment](#follow-up-a-filename-compatible-native-containment-owner)
explains the suspended-orphan window and why any-job polling is insufficient.
Both options preserve credential refusals and add no filesystem/network isolation.

## Completed audit items

| Original finding | Current result |
| --- | --- |
| PowerShell clean-environment wrapper: execution policy and embedded quotes | Replaced by an isolated Python launcher in `1f40f896c`; no PowerShell script is involved in that wrapper. |
| Filesystem probe through `cmd /c`, including spaced Python paths | Probe uses direct executable/argument launch through the OS environment helper in `1f40f896c`. |
| Claude npm batch shim forwarding | Native executable lookup in psmux and Claude SDK paths, including rejection of npm script placeholders. |
| Bare tmux control calls on Windows | Bridge, attach/preflight, cost popups and WebSocket pane liveness select psmux on Windows; POSIX uses tmux. |
| psmux JSON argument handling | Real psmux/Python-child test proves exact JSON, quotes, percent, semicolons, spaces, Unicode, cwd and environment removal. Real Claude 2.1.294 Win32 capture also passed for settings-file and full inline JSON transport; CI argv parser and transport tests pass. Direct-hook captures cover Claude 2.1.161, 2.1.266 and 2.1.295. |
| Exit status verification | psmux 3.3.8 reports constant zero placeholders. Windows callers now report unknown status rather than false success; standalone Python launcher still preserves return code 37. |

The failed UI reconnect journey counted its expected undelivered-message notice
as a third assistant reply. Both failed attempts contained two Claude replies.
The assertion now excludes that specific notice while retaining duplicate-reply
checks. A separate CRLF-sensitive linter self-test mutation was corrected.
Neither failure was dismissed as flaky without investigation.

## Previously validated baseline and failure classification

| Check on implementation `2d43e9d95` | Result |
| --- | --- |
| Local affected Windows checks | 587 passed, 2 skipped; 6 Unix-only checks deselected. |
| Local custom-lint self-tests | 67 passed after the CRLF fixture correction. |
| Staged pre-commit | All applicable hooks passed. Pyrefly used the canonical Linux target; the full project has pre-existing POSIX typing assumptions on native Windows. |
| [Fork release validation](https://github.com/MusicPartner/omnigent/actions/runs/37828737400) | Passed: focused Linux, required Windows checks, wheel build and installer/uninstaller round trip. |
| [Docker](https://github.com/MusicPartner/omnigent/actions/runs/37829582487) | Passed; image publishing disabled. |
| [Integration](https://github.com/MusicPartner/omnigent/actions/runs/37829587308) | Passed; existing workflow covers the openai-agents mock harness. |
| [E2E UI](https://github.com/MusicPartner/omnigent/actions/runs/37828738534) | Passed: Browser Contract UI and 10 shards; 1,016 shard tests passed, 31 skipped, 50 deselected. |
| [E2E](https://github.com/MusicPartner/omnigent/actions/runs/37829592170) | Passed: all four shards; only shard 3 rerun once after a server-startup port collision. Retry: 202 passed, 39 skipped. |

The corrected lost-message reconnect test passed without a retry. Three other
UI tests recovered on the workflow's existing single automatic retry, without
code changes: delivered-but-unacked composer clearing (already recorded as
intermittent in the handover), Codex cached-token cost (terminal failed to
connect on the first attempt), and project rename focus (typed name was
truncated on the first attempt). These are observed intermittent failures;
passing a retry does not establish their underlying root cause. They did not
require a new workflow rerun or an assertion relaxation.

The E2E run's first attempt failed in shard 3 before the scenario began:
`test_s2_server_restart[claude-approval_pending-5s]` could not start its test
server because the selected localhost port was already in use. The fixture
releases its temporary port reservation before starting the server; both that
fixture and the scenario are unchanged from upstream v0.17.0. A single rerun
of only the failed shard on the same SHA passed all 202 tests, including that
scenario (39 skipped). This supports an intermittent startup collision for this
failure; it does not remove the fixture's port-selection race. Successful shards
were not rerun and no product code was changed to mask the failure.

The broader Windows auth timeout is a separate unresolved portability gap,
detailed below. The overall green fork run does not mean that exploratory sweep
passed. No fix/retest sequence in this work exceeded the user's five-attempt
limit: exit-status fix 1, CRLF fixture fix 1, native hook environment setup 3, E2E shard retry 1.
The supplementary real-Claude probe used exactly 5 bounded attempts: 3 setup failures, then successful settings-file and
inline-JSON captures. No further probe retry was made.

The built [Windows artifact](https://github.com/MusicPartner/omnigent/actions/runs/37828737400/artifacts/11573865543)
is named `omnigent-windows-2d43e9d95c28d4cb623f98d3d49de1af959f90cc`.

## Decisions that affect implementation

| Decision | Recommended choice | Advantage | Cost / alternative |
| --- | --- | --- | --- |
| Sandbox launcher contract | Prototype a real Windows console executable preserving the existing filename API; decide on adoption after the prototype. | Works with filename-only SDK APIs and avoids `%*` forwarding with fewer caller changes. | Adds a packaged native launcher dependency and architecture/lifecycle validation. An all-Python command-prefix API avoids that binary but needs caller migrations and SDK transport work. |
| Claude hook compatibility | Reuse upstream's 2.1.161 floor; verify direct `command` + `args` on that Windows version and the CI pin. | Avoids a second compatibility policy; the floor is already above hook args introduction in 2.1.139. | Older supported Windows binaries still need testing. Keep status-line and shell-only hooks separate; do not promise pre-floor support. |
| PowerShell requirement | Keep ordinary terminal launches compatible with existing Windows clients; gate PowerShell-dependent popups separately. | No blanket new installation requirement. | More fallback behavior. Requiring PowerShell 7.3+ simplifies native argument handling but adds an installation prerequisite and does not fix batch forwarding. |
| Exact Windows exit codes | Keep unknown status until psmux reports a real value. | Honest behavior and small maintenance surface. | Cannot distinguish success/failure from pane death alone. An Omnigent sidecar protocol could recover status but adds synchronization, crash and cleanup cases. |
| Databricks signer auth on Windows | Defer full brokered-signer support unless release-critical; preserve upstream refusals. | Aligns with the merged fail-closed credential and containment contract. | Requires real filesystem/network isolation as well as provenance and lifecycle work. Job Objects plus ACL checks are insufficient; ordinary gateway login is a separate surface. |
| v0.14 maintenance | Excluded; the user confirmed nobody uses v0.14. | No unnecessary backport work or branch validation. | Existing historical branches/worktree remain untouched. |

Upstream merged #4586 deliberately preserves the filename-only launcher API,
which strengthens the executable-prototype recommendation. Current upstream
main still disables native terminal harnesses on Windows; our psmux capability
is an explicit fork extension. See the linked assessment for sources and the
51 overlapping file changes to review at the next release.

The first decision is architectural. The recommended prototype is not a claim
that its packaging and sandbox lifecycle are already proven. The hook and
PowerShell decisions set the supported-client policy. The exit-code choice can
remain as implemented; no change is required to accept unknown status.

## 1. Replace sandbox batch forwarding

`create_exec_launcher()` in `omnigent/inner/sandbox.py` returns a single
executable filename. Windows currently emits a `.cmd` whose `%*` forwards user
arguments. Merely changing the suffix to `.py` cannot fulfill that contract.
The Windows process API needs an executable, and Python warns that batch files
can undergo shell parsing even when the caller requests no shell.
See [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)
and [Python subprocess security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations).

Owned callers include ACP, Goose, Kimi, Qwen, Pi, terminal launch and the Codex
worker. The Claude SDK also consumes the launcher filename. Installed SDK
`0.2.94` builds both the main command and the version probe from a single
`cli_path`; it has no public argv-prefix option. The SDK exposes a public custom
Transport interface, but extending its default subprocess transport couples us
to private implementation details. A new custom transport also changes session
resume/materialization behavior that must be preserved explicitly.
See the pinned SDK [subprocess transport](https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.94/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)
and [client](https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.94/src/claude_agent_sdk/client.py).

### Follow-up: a filename-compatible native containment owner

**Recommended next prototype: a native stub with its own private Job Object.**
For an active Windows Job Object policy, create a non-inherited job with
kill-on-close and no breakaway permissions, place Python in that job before it
executes, and hold the sole job handle while waiting for Python's exit. Closing
or terminating the stub then closes that handle and terminates the contained
child tree. Parent-side `post_spawn()` may still assign the stub to an outer job;
its late assignment no longer needs to retroactively enroll earlier children.
This preserves the executable filename and can avoid a new parent handshake or
migration of every SDK/caller API. It explicitly **adds launcher-owned
containment**, rather than claiming the existing parent is the only owner.
These are design inferences from
[CreateJobObjectW](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjectw)
and [process termination](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process),
not tested properties of a new implementation.

Creating Python suspended, assigning the job, then resuming prevents Python
from running before assignment. However, killing the stub between creation and
assignment can leave a suspended orphan. Prefer assigning at process creation
through `STARTUPINFOEX` / `PROC_THREAD_ATTRIBUTE_JOB_LIST`, available on Windows
10 / Server 2016 and later; prove abrupt termination across that boundary.
Keep the job handle out of the child's inherited handle list, and never clear
kill-on-close for a console event. Inactive/no-Job-Object policies should launch
without imposing this containment. On an active policy, creation/assignment or
resume failure must produce a clear nonzero exit and clean up the suspended
child, not fall back to an uncontained launch.
See [process creation attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).

Inherited jobs remain a compatibility gate. This host's Python already belongs
to a job before the Omnigent backend acts. Modern Windows permits nested jobs
when their hierarchy is valid and UI-limit constraints allow it; a host/worker
job can still make assignment fail. Do not request breakaway to evade that
supervisor. Prove inherited and nested job cases, late outer assignment, normal
exit with surviving grandchildren, forced stub termination, cancellation and
SDK version probes. Normal exit must preserve Python's status while closing
the inner job; cancellation must allow only the defined cleanup window.
See [Nested Jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)
and [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject).

**Membership polling alone is insufficient.** A native stub could wait before
starting Python without changing the public filename API, but
`IsProcessInJob(self, NULL)` detects any job, not the anonymous Omnigent job.
A read-only native query on this host returned true before backend assignment.
Matching kill-on-close/no-breakaway flags also does not prove intended ownership;
`QueryInformationJobObject(NULL, ...)` queries only the immediate job.
See [IsProcessInJob](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob)
and [QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject).
Only `inner/os_env.py` currently calls `post_spawn()`; SDK and ACP launcher
consumers do not. A required-membership wait would need a deliberate caller and
job-identity design, plus a bounded deadline and verified parent-process handle
for parent-death failure. It is not a universal fix under the current contract.

**Alternative: parent-coordinated suspended spawn, assign, then resume.** The
parent can assign its exact job before launcher code runs, avoiding inference
and launcher-owned containment. This requires spawn/resume/failure cleanup
across callers and the filename-only SDK. Merely passing `CREATE_SUSPENDED` to
generic subprocess APIs leaves a thread-resume obligation. Creation-time job
assignment should also be considered for abrupt parent-death cleanup.
See [process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).

Any native option adds maintained source, reproducible builds with a pinned
toolchain, per-architecture assets, hashes/provenance and signing/antivirus
release costs. Prove native x64 first; ARM/x86 need separate runtime evidence.
Appending a per-launch Python/config payload changes the distributed executable
and needs a signing design. An immutable signed stub plus separate configuration
would instead need its own trust and temporary-file ownership contract.

No alternative is implemented or adopted. The retained distlib prototype is
rejected-candidate evidence, not a runtime API; distlib remains available only
through development tooling. Windows `activate()` is still a no-op. A future
launcher-owned process job would not provide filesystem/network isolation or
enable brokered-signer authentication. Credential refusals remain unchanged.

## 2. Select quoting by the consumer

`omnigent/native/shell.py::shell_join()` selects quoting from the host OS. A
Windows process argument string, POSIX shell program and PowerShell program have
different rules. Forward-slash normalization does not make their quoting rules
equivalent.

Consumer map to establish before edits:

| Consumer | Required treatment |
| --- | --- |
| Owned Python subprocess | Direct argv; no shell command string. |
| Generated `#!/bin/sh` policy wrapper | POSIX quoting even when generated on Windows. |
| Claude command hooks | Prefer executable + literal args when supported; otherwise explicitly choose and quote the hook shell. |
| Claude status line | Separate shell-command contract; do not assume command-hook args apply. |
| psmux cost popup | Current psmux starts `pwsh -NoProfile -Command`; use PowerShell-specific construction. |
| Copyable resume hints | Match the user's selected terminal shell or provide clearly labelled shell variants. |

Claude's official changelog identifies `2.1.139` as the introduction of hook
`args`; the current captured local CLI is `2.1.295`. The documented exec form passes an
argument array directly and requires a real executable on Windows. This is a
transport now adopted for eligible Python command hooks. The tracked capture
proves its Setup/argv behavior on 2.1.161, 2.1.266 and 2.1.295; full lifecycle
behavior is a separate validation surface.
See [Claude hooks](https://code.claude.com/docs/en/hooks) and the
[official changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21139).
The [status-line contract](https://code.claude.com/docs/en/statusline) still
describes a shell command and does not document an `args` field.

Add explicit consumer-oriented helpers instead of switching every Windows
command to PowerShell. For PowerShell shell programs, quote literal values and
keep complex payloads out of interpolated command text. PowerShell 7.3 changed
native argument passing, while batch targets still have legacy behavior; `--%`
still expands percent-delimited environment variables. A new PowerShell version
is therefore not a general cure for the sandbox `.cmd` path.
See [PowerShell parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.5).

psmux's popup shell is fixed in the dependency's
[3.3.8 source](https://github.com/psmux/psmux/blob/66cf613/src/popup.rs).
If PowerShell is unavailable, preserve the existing approval fallback or add a
clear popup capability refusal, rather than failing an ordinary Claude launch.

## 3. Real Claude launch evidence and future coverage

The following is historical 2026-10-08 evidence, not a successful run of the new
2026-10-09 fixture. The current gated fixture passed the three-version
Setup/argv matrix after the user revoked the original retry limit; see the
current outcome above for its exact scope.

The supplementary local capture completed on Claude Code 2.1.294 and
psmux 3.3.8. A real Claude child was launched through `PsmuxTerminalInstance`
with the isolated Python environment-removal wrapper. `Win32_Process.CommandLine`
was captured and parsed with `CommandLineToArgvW`. Both the settings-file path
and a 6,822-byte inline settings JSON built from the production hook generator
arrived unchanged; Claude invoked an added local Setup hook, which recorded exact
literal quotes, `%PATH%`, semicolons, spaces, Unicode and `2>>`, the space/Unicode
cwd, and removal of the test environment variable. The endpoint was loopback
with a test-only key; no provider response or real credential was needed.

Evidence and the probe are retained locally under the ignored
`artifacts/windows-parity-2026-10-08/` directory. The working capture used normal
inherited Windows process environment plus an isolated Claude config. Three
initial probes failed during psmux session creation with a deliberately minimal
environment and/or a semicolon/percent workspace path, before Claude started.
Those changes were not isolated separately, so no specific root cause or wider
compatibility guarantee is claimed. The fifth attempt completed the probe;
there were no retries beyond the agreed limit.

Production `augment_claude_args()` already writes hooks into an invocation-local
settings file, while `--mcp-config` remains inline JSON. This capture exercises
the stronger full-settings inline case too; it does not change that production
file contract. The tracked fixture now automates the following transport
evidence. A full SessionStart/conversation journey remains separate from its
`--init-only` Setup-hook assertions:

1. Use an isolated Claude config and a uniquely named psmux server/pane. Generate
   settings through the production bridge, including hook strings with `2>>`,
   quotes, `%`, semicolons, spaces and Unicode. Include a path containing spaces.
2. Launch the installed native Claude executable through the production backend.
   Record CLI and psmux versions, generated argv, and the Claude child process's
   `Win32_Process.CommandLine`, without recording credentials or real prompts.
3. Parse the captured command line with Windows rules. Compare the production
   settings-file path and file contents, and compare inline `--mcp-config` JSON.
   Keep the stronger inline `--settings` stress case as additional coverage.
   Trigger a local hook recorder to show that Claude accepted and executed the
   settings. This can use an isolated/mock endpoint; a provider response is not
   necessary to prove argument transport.
4. Verify environment removal, cwd and cleanup using only the test-owned pane
   and processes. Add a gated native-Windows integration check once the capture
   method is repeatable, alongside the existing Python-child regression.

Do not use `pane_start_command` as the authoritative argv source. In installed
psmux 3.3.8, that field formats the configured default shell, while exit-status
fields are also placeholders. See
[format.rs](https://github.com/psmux/psmux/blob/66cf613/src/format.rs).
The [latest stable release](https://github.com/psmux/psmux/releases/tag/v3.3.8)
checked on the research date is still 3.3.8, so upgrading is not a verified fix.

### Repeat the tracked real-Claude transport check

From `omnigent-v017` on native Windows, set the full path of an **existing native
`claude.exe`** (not an npm `.cmd` shim). The test requires installed psmux, leaves
the CLI installation unchanged, and cleans up only its isolated config and
owned processes. For an executable already on PATH:

```powershell
$env:OMNIGENT_REAL_CLAUDE_EXE = (Get-Command claude.exe -ErrorAction Stop).Source
.venv\Scripts\python.exe -m pytest tests/terminals/test_real_claude_windows_capture.py -n 0 -p no:cacheprovider -q
Remove-Item Env:OMNIGENT_REAL_CLAUDE_EXE
```

For a separately installed version, assign its full filename to the same
environment variable. Expect one passing Setup/argv capture with unchanged CLI
version and exact settings/recorder arguments. This check does not exercise a
provider response or full conversation. With no opt-in variable, it skips.

## 4. Non-blocking Windows auth sweep failure

The fork validation workflow is green, including its required Windows tests and
installer round trip. Its broader exploratory Windows unit sweep still failed:
`test_cancelled_ucode_mint_terminates_helper` timed out waiting for a startup file.
Its fixture writes a `#!/bin/sh` executable and prepends POSIX directories to
PATH; that helper is not a native Windows executable. The wait also never checks
whether the mint task already failed. This is a portability defect, not evidence
of a transient CI race.

`tests/inner/test_model_auth.py` and `omnigent/inner/model_auth.py` are unchanged
from upstream v0.17.0. The production executable provenance check uses
`os.getuid()` and POSIX ownership/write bits. A real Windows implementation needs
an explicit trust policy for executable and parent-directory owners/ACLs,
reparse points and replacement races. Windows security descriptors expose owner
SIDs and DACLs, but reading them alone does not eliminate races; see Microsoft's
[GetNamedSecurityInfoW documentation](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getnamedsecurityinfow).

Options are to schedule native Windows signer support with that trust design,
or keep it explicitly outside this release's supported Windows surface until
implemented. Upstream's merged brokered-auth contract also requires real worker
filesystem/network isolation, which the Job Object backend does not provide.
ACL/SID checks and portable test helpers alone cannot enable that feature.
Ordinary gateway token minting is a separate auth surface. Do not bypass
provenance checks or add blanket skips merely to make the sweep green. A future fixture update should use a real portable helper
and a bounded startup wait that surfaces task failure, then verify cancellation
kills the helper. Existing POSIX provenance and descendant tests must remain.

## Remaining handover choices

- **Non-git workspace response:** keep v0.17's HTTP 400; the UI uses it to
  identify `not_git`. Restoring HTTP 200 with an empty list changes that contract.
- **Catalog-default model pin:** preserve upstream mode-specific behavior: managed
  sessions use shared provider/catalog policy, while an explicit native-config
  choice should use CLI configuration. Do not introduce a Windows-wide default
  override. Open upstream #7773 and #9247 address native-config persistence and
  client-aware defaults; review them if merged rather than adopting them now.
- **Two ACP Windows skips:** leave them dropped; the handover records that the
  tests passed without them. Reintroducing skips would reduce coverage.
- **Optional PR:** unnecessary for this work; keep the existing no-PR-to-main
  constraint. Existing dispatchable workflows provide branch validation.
- **v0.14 shutdown backport:** excluded; the user confirmed nobody uses that
  version. Leave historical branches and the old worktree untouched.
- **Earlier broad manual validation:** accepted as completed by the user. Only
  the new launch/bridge behavior needs the focused verification below.

## Work remaining after this pass

1. Review the native launcher-owned Job Object prototype recommended above;
   preserve the filename API and explicitly agree on containment ownership.
2. Retain the adopted direct command + args hooks and repeatable opt-in capture.
   Keep Setup/argv evidence distinct from a full SessionStart/conversation
journey; branch CI and the local production build are recorded above.
3. Run applicable pre-commit and unaffected validation when their implementation
   is ready. Record resumed capture results separately from baseline CI. Publish
   or claim final builds only after the changed behavior has the required proof.

The original five-attempt limit is historical: the user revoked it and renewed
authorization for capture. Keep failure evidence and do not suppress assertions
or claim a fix merely because a retry passed. v0.14 remains outside this work.

## Published history and future updates

The v0.14 worktree and published branches remain unchanged. The earlier process
launch changes were `1f40f896c`, followed by the validated baseline commit
`2d43e9d95`. The current hook/consumer implementation is the normal pushed
commit `28db4f72c973b15a96b00de29e11f3f93509c246`. No PR to main was opened and
published history was not rewritten. Any rollback should select the intended
change after reviewing its diff and use a normal revert followed by validation.

For subsequent upstream releases, follow
[the fork maintenance workflow](../../.github/FORK_MAINTENANCE.md): ingest a
stable release into an isolated integration branch, preserve the Windows leaf
modules/caller seams, review conflicts deliberately, and validate before an
agreed merge. Keep the launcher, shell and auth decisions recorded here with
any supported dependency versions so they can be checked during each update.

## Local application build

The production web UI and fresh core/client/UI SDK wheels were built from
`28db4f72c973b15a96b00de29e11f3f93509c246` on 2026-10-09. The core build stamp is
`0.17.0 (28db4f72, built 2026-10-09T08:42:50Z)`. The UI contains 519 packaged
files including its index. Existing Vite CSS/chunk warnings did not prevent the
successful build and are not classified as new code failures.

Wheels are in `dist/windows-parity-local/`; the production UI is in
`omnigent/server/static/web-ui/`. An isolated installation outside the checkout
passed imports for the server app, Windows hook/status/shell modules, shared
observer and both SDKs, plus `omni`/`omnigent --help` and `--version`. The existing
editable environment remains runnable with the new UI and current source.
Generated build outputs and the report at
`artifacts/windows-parity-2026-10-09/final-build-28db4f72/build-report.json` are
ignored by Git. This supersedes the older local build's `2d43e9d9` stamp; the
previous validation section remains historical evidence for that baseline.

Open two PowerShell terminals in
`D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v017`.
In the first:

```powershell
.\.venv\Scripts\omni.exe server --host 127.0.0.1
```

In the second:

```powershell
.\.venv\Scripts\omni.exe host --server http://127.0.0.1:6767
```

Open <http://127.0.0.1:6767> and select the local host/workspace. A server has
not been started for the user; these commands start the built application.

## Focused verification of the implemented fixes

From the v0.17 worktree on native Windows:

```powershell
.venv\Scripts\python.exe -m pytest tests/inner/test_claude_windows.py tests/test_native_mux.py tests/terminals/test_windows_psmux.py -n 0 -p no:cacheprovider -q
```

In Omnigent, open a workspace whose path contains a space or Unicode character,
start Claude Code, switch between Terminal and Chat, and send
`Reply exactly: parity ; %PATH% Å`. Confirm one matching reply, a connected
terminal, working resize/reconnect, and cleanup after ending the session.
Do not expect a numeric pane exit status from psmux 3.3.8.
