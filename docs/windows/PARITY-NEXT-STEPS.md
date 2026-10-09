# Windows parity: remaining work and decisions

Research date: 2026-10-08. Branch: `windows-parity/v0.17-integration`.
Latest validated build/artifacts: `e6a14a5e9dad093bebdf16809b70d22e9dccd61b`.
The full broader Windows gate is required and passed. Earlier native Python
crash causes remain unconfirmed; CI retains memory diagnostics.
The final release evidence and remaining Windows test gaps are recorded below.
Previously validated baseline: `2d43e9d95c28d4cb623f98d3d49de1af959f90cc`.
This record separates the new consumer fixes and blocked decisions from the
baseline validation retained below.
Upstream direction was reviewed on 2026-10-09 in
[the evidence and merge-risk assessment](UPSTREAM-DIRECTION-2026-10-09.md).
Its recommendations below distinguish merged upstream contracts from proposals.
The accepted [implementation plan](IMPLEMENTATION-PLAN-2026-10-09.md) delegates
the work and excludes v0.14 backporting, as confirmed by the user.

## Broader Windows suite follow-up: 2026-10-09

The repair at `b0be8b116` keeps the Codex private-home security refusal and
makes lifecycle fixtures portable. It fixes Windows Pi npm-shim truncation of
multiline instructions and dispatches Qwen authentication through the platform
shell. Remaining test corrections declare genuine POSIX scope or handle only
actual Windows symlink privilege errors. Databricks remains unused and absent;
four tests received the same optional dependency guard as adjacent tests.

The exact broader selection completed locally at source `62607c95c`:
**3,763 passed, 210 skipped, 292 deselected and 10 passing subtests**.
Final required broader CI at `e6a14a5e9` passed **3,786 tests**, with 187 skipped,
292 deselected and 10 passing subtests; zero JUnit failures/errors. Required
Linux repaired families passed 1,298 tests and focused integration passed 1,040.
Backend E2E passed all four shards and the dispatched integration matrix passed.
UI validation at `bbda83990` passed Browser Contract and all ten shards.
Subsequent commits change only test dependencies and CI. Four of the user's
five additional attempts were used; the fifth was unnecessary.
Earlier broad CI failures/native crashes remain historical evidence. CI retains
memory diagnostics and makes the full sweep required. The native crash's root
cause remains unconfirmed; the successful runs do not prove it fixed.
The [findings](BROADER-TEST-FINDINGS-2026-10-09.md) contain raw-result distinctions,
all historical failures, the [full skip inventory](BROADER-WINDOWS-SKIPS-2026-10-09.md),
and bounded diagnostic attempts. UI recovery initially found two launch roots,
consistent with overlap from a background title client; `bbda83990` isolates
the test using the existing title preference without weakening ownership checks.

Matching [CLI](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643364292)
and [desktop](https://github.com/MusicPartner/omnigent/actions/runs/37985563937/artifacts/11643559052)
artifacts at `e6a14a5e9` were downloaded and compared with their commit:
14 Python modules and four Electron host/manager modules matched. Electron
metadata identifies source `e6a14a5e9`, version 0.17.0 and dev mode; the wheel
retains the unsigned, opt-in native launcher candidate. CI's installer,
version/help and uninstaller smoke passed in a disposable prefix.

Human acceptance still needs a fresh session for each of Claude, Codex and
Copilot using the verified development desktop build. Keep a separate CLI
session running. Ask the agent to execute `Start-Sleep -Seconds 30` in native
PowerShell, press Stop while it runs, then send another message and confirm it
responds. Quit Omnigent and confirm its owned work exits while the independent
CLI session survives. Repeat image and ZIP attachment checks from the existing
attachment follow-up; Codex sandbox read access remains unproven by mocked tests.

## 2026-10-09 implementation outcome

The earlier distlib executable prototype was rejected for production adoption.
Its native Windows x64 test showed that Python and its target could start before
parent-side `post_spawn()` assigned the outer executable to a Job Object; closing
that job left the existing descendants alive. This result applies to distlib's
late-assignment design and was not compared with the existing `.cmd` launcher.
It does not establish a regression in the legacy launcher.

The separate native candidate is now integrated behind the Windows
`create_exec_launcher` selector, with legacy `.cmd` behavior still the default.
Clean-wheel packaging and local x64 lifecycle evidence are recorded below.
Remote x64 CI and matching fork artifacts passed as recorded below. There is
no signed native release artifact, ARM/x86 runtime claim, or filesystem/network
isolation. Existing credential refusals and
brokered-signer boundaries remain unchanged.

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
capture. The original test-only launcher’s no-outer-job parent-death result is
historical prototype evidence; the current candidate watches its immediate
parent. Brokered-signer isolation remains unsupported, and no filesystem/network
isolation or ARM/x86 runtime support is claimed. v0.14 remains excluded.

## Earlier consumer validation

| Check | Result and limit |
| --- | --- |
| Earlier distlib x64 launcher prototype | 3 passed, including the reproducible failed-containment assertion; no runtime adoption. |
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

The current implementation is an **opt-in Windows x64 candidate** integrated
at `create_exec_launcher`. Legacy behavior remains the default. `native` fails
closed unless the packaged manifest marks an Authenticode artifact as
release-approved and its signer thumbprint matches; `native-dev` explicitly
selects the unsigned development artifact. Both modes check the asset hash,
architecture and invocation config.

The launcher stores per-invocation `OJLCFG01` data in its copy's
`:omnigent.config` NTFS alternate data stream (ADS). Copies live in a protected
per-user profile container whose ancestors are checked for reparse points and
cross-user mutation rights. The native process keeps executable and ADS handles
locked, assigns its Python child to a private kill-on-close job at process
creation, and watches the immediate parent so caller death closes the job.
This provides process lifecycle containment only; filesystem/network isolation
and brokered-signer support remain unavailable.

Packaging includes the prepared executable and manifest in both the universal
wheel and sdist; `MANIFEST.in` adds only native source/build helpers. Generated
executables and manifests remain untracked. The pinned MSVC 14.44.35207 /
Windows SDK 10.0.26100.0 build
passed its independent-output reproducibility check. The unsigned candidate
SHA-256 is
`3d2564228c78a637c5c47bc350937cb2474e61ca6a855b272e0191cac6984c03`.

The candidate native process suite passed **21 tests**. A separate rerun
exposed a readiness-file read race in the test helper; the transient
`PermissionError` was not a native launch or containment assertion. A bounded
read retry fixed the test helper, and the nested-job plus permanent-read-failure
cases passed in three separate runs, each with **2 passed**. No production code
changed for the test fix. The runtime suite passed **24 tests with 1
symlink-rejection skip** without Windows Developer Mode or symbolic-link
privilege, including the positive signer check. **41 packaging checks passed**
after adding embedded-signature validation.
**17 shared launcher and capability regressions passed with 3 POSIX skips**,
and the actual psmux/native-launcher lifecycle test passed. A clean
sdist-to-wheel build and isolated installed-wheel smoke passed with
`python -I`; it exercised active native-dev launch, literal argv/stdin/cwd/exit
code, ADS cleanup, and strict refusal of the unsigned artifact by `native`
mode. The final wheel was rebuilt, reinstalled and smoke-checked. CLI version
and server imports passed in the isolated install. No candidate remote CI run
has completed.

Release adoption remains gated on the approved signing policy and signed
artifact, remote CI evidence, clean-machine AV/SmartScreen behavior, and an
explicit decision about enabling `native` by default. Keep unsigned
development use behind `native-dev` until those gates pass. See the
[candidate plan](PRIVATE-JOB-LAUNCHER-PLAN.md) for the scope and exact local
verification commands.

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

The broader Windows auth timeout was a separate portability gap in this
earlier build, detailed below. It is repaired in the broader-suite follow-up
above. This earlier green fork run did not mean its exploratory sweep passed. No fix/retest sequence in this work exceeded the user's five-attempt
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

### Historical prototype assessment: a filename-compatible containment owner

**Prototype result: a test-only native stub owns a private Job Object.** For an
active policy, the x64 stub creates a non-inheritable kill-on-close job, assigns
Python to it at process creation, and holds the job handle while waiting for the
Python exit code. The 18-test run confirmed that normal exit and forced stub
termination stop the child tree; assigning the stub to an outer job after its
children start also stopped the tree through the private job. The filename-only
API shape is preserved by the experiment, but the production seam and SDK APIs
remain unchanged. This explicitly **adds launcher-owned containment** for the
prototype rather than claiming the existing parent is the only owner.
The isolated prototype now implements this ownership shape. Its passing
termination tests establish behavior for the tested native x64 build and SDK
call patterns only; they do not establish production packaging or caller-death
cleanup without an outer job.

The release-like prototype assigns the child at creation through
`STARTUPINFOEX` / `PROC_THREAD_ATTRIBUTE_JOB_LIST`, before the child executes;
only its test build suspends the child at controlled checkpoints. The tests
confirm that terminating the stub at the post-create checkpoint does not leave
a running or suspended Python child. The job handle is excluded from the child's
explicit inherited-handle list. Active-policy failures return nonzero and clean
up the child instead of falling back to an uncontained launch. The private job
is not created for inactive/no-Job-Object policies.
See [process creation attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).

Inherited jobs remain a compatibility gate. This host's Python already belongs
to a job before the Omnigent backend acts. Modern Windows permits nested jobs
when their hierarchy is valid and UI-limit constraints allow it; a host/worker
job can still make assignment fail. Do not request breakaway to evade that supervisor.
The opt-in suiteexercised
nested host jobs, late outer assignment, normal exit with a surviving
grandchild, forced stub termination, SDK cancellation and SDK version-probe
output/timeout; all 18 tests passed. Normal exit preserved Python's status while
closing the private job. Separately, killing a caller without an outer job left
the stub and its private-job tree alive until the test explicitly killed the
stub. This is an observed limitation, not successful parent-death cleanup.
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

The first custom native launcher in `dev/windows_launcher/` was an isolated
prototype; its 18-test run passed with MSVC 14.51.36231 and Windows SDK
10.0.26100.0. Its no-outer-job caller-death result describes that prototype
only. The current candidate is integrated behind the explicit runtime
selector and has separate lifecycle and packaging evidence recorded above.
Run the historical prototype suite from the v0.17 worktree with an x64
MSVC/Windows SDK environment:

```powershell
$env:OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER = "1"
.venv\Scripts\python.exe -m pytest tests/inner/test_windows_private_job_launcher.py -n 0 -p no:cacheprovider -q
Remove-Item Env:OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER
```

The suite covers literal argv and Unicode/spaced paths, stdio and exit code 37,
active and inactive policies, creation-time assignment, nested jobs, failure
cleanup, direct stub termination, SDK close/cancellation, and version-probe
output/timeout. The original distlib prototype remains rejected-candidate
evidence, not a runtime API. Windows `activate()` remains a no-op. Neither that
prototype nor the current candidate adds filesystem/network isolation or
brokered-signer support; credential refusals remain unchanged.

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

1. Keep release adoption gated until the approved signer and signed artifact,
   remote CI, clean-machine AV/SmartScreen handling, and release-default
   decision are documented.
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

## Local workflow follow-ups (2026-10-09)

### Claude native PowerShell live output

Observed: the Chat tool card waits while PowerShell runs, then displays the
complete output. The Claude-native forwarder currently mirrors completed
transcript tool results; unlike Codex-native, it has no producer for
`external_tool_output_delta`. The shared server event and web live-output
handler each passed a focused regression check, so adding a frontend timer or
changing the Windows launcher would not supply the missing output.

An isolated Claude Code 2.1.295 process, using a local mock provider and fresh
configuration, executed a PowerShell command with two output markers separated
by a 20-second wait. Its print-mode transcript and JSON stream exposed no
incremental PowerShell output. Source inspection found internal PowerShell
progress snapshots, but no supported command hook that exports their output;
`MessageDisplay` forwards assistant text. This evidence does not establish
that every Claude version or integration mode has the same limitation.

A subsequent isolated interactive test with psmux 3.3.8 succeeded when run
outside the test execution sandbox. The PowerShell command emitted its first
marker, waited 20 seconds, and recorded both markers in the completed tool
result. Its 28 observed transcript records contained no progress records.
This verifies the native terminal/transcript behavior, not an end-to-end
browser journey. The owned terminal and local mock server were stopped.

Decision: retain Claude's native tools only. The user withdrew approval for
an additional Omnigent streaming PowerShell tool; its partial integration
edits were reverted. Do not add a replacement tool, command wrapper, or
speculative output-file matching to work around this limitation.

Follow-up: find a supported, call-correlated source of live tool output, then
forward it through the existing transient event path. Verify output before
command completion, cancellation, concurrent tool calls, reconnect, and final
result reconciliation without duplicate lines. Keep this change within the
Claude-native integration and retest after Claude upgrades. No runtime
streaming change has been made as part of this investigation.

Manual reproduction: start a Claude-native session and request
`1..10 | ForEach-Object { Write-Output "Tick $_"; Start-Sleep -Seconds 1 }`.
Observe Chat while it runs and after completion. The current limitation is
confirmed when all ten lines appear only after the command finishes.

### Codex repeated administrator setup prompts — resolved

On 2026-10-09, the user confirmed that incomplete Codex sandbox setup caused
the repeated administrator prompts. Completing setup resolved the issue.
This supersedes the earlier suspected repeated-provisioning defect; that
upstream issue was not established as the cause on this machine.

The temporary `windows.sandbox = "unelevated"` workaround is no longer needed
for this issue. No Omnigent launcher change is required, and no personal Codex
configuration was changed or audited as part of this documentation update.

Regression check: start two fresh Codex sessions and run `Get-Date` in each;
commands should complete without repeating the sandbox setup prompt.

### Codex restart from Chat after Stop fails with EACCES — implemented; UI acceptance pending

User-reported on 2026-10-09: after stopping native Codex, another command from
Chat failed before terminal startup; Console resume worked. The reported runner
log identifies `os.replace(tmp, target)` in `_ensure_local_codex_resume_rollout`
as the failing operation (`PermissionError`, errno 13, WinError 5). The target
rollout was not read-only and had normal owner permissions. Read-only process
inspection found an older same-session `codex.exe app-server` whose parent had
exited, alongside the later server created by successful Console resume. No
user processes were terminated during diagnosis.

Upstream was checked before implementation at main
`b419d1f59f7eb730bc9f34613d85820c944af466`. Its
[rollout refresh](https://github.com/omnigent-ai/omnigent/blob/b419d1f59f7eb730bc9f34613d85820c944af466/omnigent/harnesses/codex_native/main.py)
still replaces the existing file, and its
[same-session cleanup](https://github.com/omnigent-ai/omnigent/blob/b419d1f59f7eb730bc9f34613d85820c944af466/omnigent/harnesses/codex_native/process_registry.py)
still skips non-POSIX systems. No matching fix was found in the inspected
issues/PRs. Related [#9161](https://github.com/omnigent-ai/omnigent/pull/9161)
handles stopped backends behind surviving terminals;
[#9461](https://github.com/omnigent-ai/omnigent/pull/9461) handles EACCES during
CLI discovery. Neither fixes this rollout replacement. No upstream merge was
needed for the local correction.

The contained fix adds `codex_native/windows_process_cleanup.py`, selected by a
small Windows branch in the existing pre-resume cleanup function. It matches
Codex app-servers to the exact session-private `CODEX_HOME`, protects the caller
and its ancestors, checks process birth identity, and waits for owned writers
to exit before the existing atomic history refresh. Other session homes are
excluded. The successful server transcript remains authoritative, including
empty or shorter history; the fix does not suppress errors or reuse divergent
local history. POSIX cleanup and the native Codex launch path are retained.

Verification: 14 new focused tests passed, including a native Windows test
using owned processes that reproduces WinError 5 with an open append handle,
reaps the matching writer, preserves a second session's process, and refreshes
the same rollout from authoritative history. The helper tests cover unrelated
homes, non-server commands, caller/ancestor exclusions, PID reuse, changed
ancestry, inaccessible metadata, and termination failure. Another 27 existing
runner lifecycle tests passed. Existing rollout/terminal-preparation tests
produced 48 passes and one pre-existing Windows ZIP-attachment failure:
`native_attachments.materialize_attachment` uses unavailable `os.O_DIRECTORY`.
That attachment issue is outside this correction. Linux-target Pyrefly reports
zero errors; native Windows reports the same 156 existing POSIX-API errors.
Formatting and other applicable repository hooks passed. No full browser
Stop/Chat/Console acceptance run was performed; follow the manual check below.

Focused automated reproduction from this checkout:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/harnesses/codex_native/test_windows_process_cleanup.py tests/harnesses/codex_native/test_codex_native_windows_resume_lock.py -q -n 0 -p no:cacheprovider
```

Manual acceptance after restarting the Omnigent host with the updated checkout:

1. Start native Codex from Chat. Send: `Remember the marker blue-lantern, then
   run Write-Output "before-stop" in PowerShell.`
2. Use **Stop session**, then send `What marker did I ask you to remember? Run
   Write-Output "after-resume" in PowerShell.` directly from Chat.
3. Verify it resumes without EACCES or a Console detour, remembers the marker,
   and shows `after-resume`. Repeat Stop then Chat send twice.
4. Keep a second Codex session open during this check; verify it still responds.
5. In a separate stopped session, verify **Console → Resume session** still
   works and retains history.

Original diagnostic reference:

```text
Native Codex terminal failed to start (ClickException errno 13 EACCES)
Error ID: err_d0d8196fd12a47f49b0928074382ae0d
Runner log: ~/.omnigent\logs\runner\runner-ae876cf7f60945969835a6ab8269db3b-20261009-145314-078926.log
```

### Claude Stop raises invalid WebSocket status code — implemented; UI acceptance pending

The supplied 2026-10-09 traceback shows a runner tunnel abort represented by
internal code `1006`, followed by the terminal proxy trying to send that code
to the browser. WebSocket close frames cannot carry `1006`; the attempted close
raised `ProtocolError: invalid status code`. Upstream main retains the bug and
[issue #8929](https://github.com/omnigent-ai/omnigent/issues/8929) reports the
same traceback.

`server/routes/terminal_attach.py` now forwards only wire-valid standard or
application codes. Internal/invalid codes map to retryable `1011`; valid codes
and the reason are preserved. All 24 terminal route tests passed, including 13
close-code regression cases that exercise the real serializer. Restart the
server, open Claude's Console, start a response and use Stop. Confirm the
terminal disconnects without the ASGI `invalid status code` traceback, then
resume and send another message. This addresses proxy error handling, not
Claude tool-output streaming.

### Codex sandbox secrets deletion after successful setup — upstream; temporary session fallback

Codex 0.162.0 failed before command execution while deleting the affected
session's `.sandbox-secrets/sandbox_users.json`. Metadata-only inspection found
ordinary directories/files, not junctions or read-only files. Native setup owns
the secrets as Administrators and grants the normal user read/write/execute but
not Delete. Omnigent does not copy or link this directory. Secret contents were
not read, and ACLs/accounts were not modified.

The installed-version source explains both parts:

- [Fixed machine-wide account names](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/setup.rs#L48-L50)
  are combined with per-`CODEX_HOME` credentials. Provisioning another private
  home resets the accounts' passwords; the affected credential file predated
  the latest password reset. This supports stale credentials as the trigger.
- [Credential recovery](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/identity.rs#L150-L160)
  attempts to delete the stale record, while
  [setup ACLs](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/setup_provisioning.rs#L801-L829)
  deliberately withhold Delete from the normal user.
- [Upstream #40627](https://github.com/openai/codex/issues/40627) tracks the
  multi-home provisioning conflict. No applicable released fix was identified.

Following the user's previously authorized fallback, only the reported private
home `9346488ae2608d749c35528ccb05247e/codex-home/config.toml` was changed from
`[windows] sandbox = "elevated"` to `"unelevated"`. Its rollback copy is
`config.before-unelevated-20261009.toml` beside that config. The global Codex
config, other sessions, and new-session defaults are unchanged. Existing
private configs survive Omnigent startup, so the change persists for this
session. Restart its runner/app-server before testing. This is a temporary
workaround with weaker network isolation, not an upstream sandbox repair; see
[OpenAI's Windows sandbox documentation](https://learn.chatgpt.com/docs/windows/windows-sandbox).

A native CLI probe using a disposable home and explicit unelevated selection
successfully printed `1`, `2`, `3` through PowerShell (exit 0). The affected UI
session still needs manual acceptance: after restart, ask Codex to run
`Get-Date` using its native shell tool, then the 60-second loop. Ask it to report
native-tool failure rather than switch to `sys_os_shell`. That fallback uses
`cmd.exe` on Windows; raw PowerShell `$i` syntax or incorrect nested quoting
explains the subsequent fallback errors and does not validate native execution.

Revisit this workaround when upstream fixes per-home credential reconciliation.
Restore the original elevated setting only after verifying two different
Omnigent Codex sessions can both execute native commands without invalidating
each other's sandbox setup. Do not share secrets directories or broaden their
ACLs as a workaround.

### Subsequent sessions: invocation-only native sandbox opt-in and Store PowerShell failure

The next report used a different private home,
`772f079e9e84ef36b0b8ddad30cc74a1`, so the earlier single-session config repair
did not cover it. The opt-in `OMNIGENT_CODEX_WINDOWS_SANDBOX` now selects native
Codex's Windows sandbox for every app-server started by that Omnigent host,
including new and resumed private homes. Accepted values are exactly `elevated`
or `unelevated`; invalid values fail before launch. Unset leaves existing
behavior unchanged, and non-Windows hosts ignore it. The override is passed as
`-c windows.sandbox="unelevated"` (or `"elevated"`) to the native app-server and
remote TUI. The sandbox override does not write `config.toml` or modify
secret-file ACLs; normal Omnigent config preparation still runs as before.

The separate `CreateProcessAsUserW` error `-1073283067` is `0xC0070005`
(access denied). Isolated Codex 0.162.0 probes reproduced it for the reported
Microsoft Store PowerShell executable; both
`C:\Program Files\PowerShell\7\pwsh.exe` and System32 Windows PowerShell
succeeded. Codex's
[Store-shell substitution](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/exec-server/src/process_sandbox.rs#L244)
excludes unelevated mode. Its
[shell discovery](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/shell-command/src/shell_detect.rs)
uses the first `pwsh` on PATH. This version has no `powershell_exe` config key.
Related report: [Codex #35958](https://github.com/openai/codex/issues/35958).

Stop the existing Omnigent host and start it from this checkout in a fresh
PowerShell window, keeping the existing server running at the usual local URL:

```powershell
Set-Location D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v017
$env:OMNIGENT_CODEX_WINDOWS_SANDBOX = "unelevated"
.\.venv\Scripts\omni.exe host --server http://127.0.0.1:6767
```

PowerShell selection is now automatic for Claude, Codex, and Copilot child
processes; the manual PATH prefix is no longer needed. The sandbox environment
variable above still applies to this host process and its descendants. Removing
it and restarting the host/affected sessions restores their existing
saved/default sandbox selection.
It does not undo earlier manual or formerly persisted settings: the previously
edited `9346488ae2608d749c35528ccb05247e` session still has its saved unelevated
setting and rollback copy described above. This change makes no further edits
to personal session configs. A still-running app-server retains its launch
configuration until restarted.

Acceptance: create two fresh Codex sessions, and in each ask for `Get-Date`
using the native tool with no fallback. Then run a short counter before retrying
the 60-second counter. Confirm tool launch uses non-Store PowerShell and neither
session reports sandbox-secret deletion. Also Stop and resume an existing
session to check the override reaches resumed homes. The error text shown under
"Claude" mentions Codex's unified executor; verify the active harness/tool when
retesting rather than assuming it came from Claude's native PowerShell tool.
No replacement streaming tool was added.

Validation of the invocation-only revision: 22 startup tests passed; six
symlink cases skipped because this Windows environment cannot create symlinks.
The tests check saved settings, native server and fresh/resumed TUI arguments,
and removal of the generated override on a reused server. Linux-target Pyrefly
reported zero errors, and the applicable repository hooks passed after
normalizing line endings. Native A/B probes above used disposable homes; the
full two-session UI acceptance check remains pending.


Invocation-only verification: the installed Codex 0.162.0 app-server was
started with an isolated home whose saved setting was `elevated`. With the
CLI override, `config/read` returned `unelevated` and the config bytes remained
unchanged. A second launch without the override returned `elevated`, again
without changing the file. Both probe processes were stopped; no user sessions
or credentials were used. Omnigent uses native app-server/remote-TUI arguments
here, so no TypeScript SDK integration is involved.

### Codex Stop leaves its app-server running — implemented; user verified

Stop previously used the same `turn/interrupt` handler as Interrupt, so an idle
Codex session returned success without ending its app-server. The local original
checkout has the same dispatch. Codex now has a dedicated Stop handler using
existing session-owned app-server and terminal teardown. Ordinary Interrupt
continues to interrupt the turn. Shutdown exceptions are surfaced as Stop
failures, and a successful Stop clears pending interrupt timers and settles
sub-agent cancellation.

Teardown retains the original server handle across forwarder cancellation so a
forwarder that removes its registration early cannot strand that server. A
replacement registration is preserved. The server's Stop request now allows
30 seconds for native cancellation and process shutdown. Changes are confined
to native interrupt/orchestration and the Stop forwarding budget; no process-name
sweep is added.

Verification: 47 focused Codex tests passed, including runner HTTP/unit
regressions, cleanup ownership and cancellation cases, and a Windows test with
two owned writer processes. Another 18 existing cancellation/capability checks
passed; `sys_cancel_task` retains its existing best-effort Codex behavior because
externally CLI-owned lifetimes cannot be confirmed by runner cleanup. Linux-target
Pyrefly reports zero errors. The
selected process exits, its file handle is released, and the other session
remains running. A separate smoke test with the installed Codex 0.162.0 launches
two isolated native app-servers: Stop returns 204, the selected `codex.exe` exits,
the second app-server stays alive, and a repeated Stop succeeds. Both owned test
processes were closed afterward. No existing user processes were stopped.
This proves registered runner-owned app-server teardown; a full browser journey
and CLI-owned lifecycle are not covered by this smoke test.

Manual acceptance after restarting both the server and host from this checkout:

1. Open two native Codex sessions. Record their app-server PIDs in Task Manager
   using the Details tab and Command line column.
2. Ask one session to run a 60-second foreground counter, then use **Stop session**.
   Confirm its app-server PID exits and the other session still responds.
3. Send another message from Chat in the stopped session. Confirm it resumes
   without EACCES and retains the conversation.
4. Stop again while the session is idle; confirm its new app-server PID exits.
5. Check **Console → Resume session**, then repeat Stop once more. Other Codex
   sessions and editor processes can legitimately remain in Task Manager.


### Whole-app Windows shutdown — implemented; desktop acceptance pending

Windows desktop quit and local host/server stop now request graceful lifecycle
cleanup before terminating surviving owned processes. Closing a browser tab
still leaves sessions running. Desktop quit stops hosts and the local server
that the desktop started; previously running or adopted hosts/servers remain
under their existing ownership. Conversation history remains available for
resume after restarting Omnigent.

The Windows-specific implementation lives in
`omnigent/inner/windows_process_shutdown.py`,
`omnigent/inner/windows_shutdown_cli.py`, and
`web/electron/src/windows_host_shutdown.js`. Existing host, runner, server, and
desktop lifecycle code contains only integration hooks. POSIX signal-based
shutdown remains in place. There are no new dependencies, public shutdown
endpoints, process-name sweeps, or harness streaming tools.

A process registers a named Windows event scoped to its PID and kernel creation
time. A stop request captures owned process identities and descendants before
signalling registered listeners, including listeners behind Python/CLI wrappers.
Requests retry during startup. Hosts stop tracked runners together; runners use
existing lifespan cleanup to close harnesses and terminals. The headless server
sets uvicorn's existing `should_exit` flag. After the grace period, captured
survivors are terminated leaves first, with creation time rechecked before each
operation. Captured descendants remain tracked even if their parent exits.
Runner parent-death fallback also captures children started during the grace.

Windows default grace is 30 seconds for owned process trees and 35 seconds for
recorded host-daemon stops. Desktop gives helpers longer timeouts and permits
up to 130 seconds for quit cleanup; healthy shutdown normally finishes sooner.
Missing helpers, unreadable ownership, or surviving processes report failure
instead of claiming success. Server pidfiles are checked against the actual
server command and file timestamp before granting tree ownership. Force-killing
the entire desktop/backend, power loss, and external detached process ownership
are outside the normal graceful-quit guarantee.

Validation: 44 focused Python tests and 180 desktop tests passed; Linux-target
Pyrefly reported zero errors. Coverage includes real headless event delivery and
FastAPI/uvicorn lifespan cleanup; late registration; retained descendants after root exit; forced cleanup;
PID reuse and stale pidfile refusal; console stop; and desktop ownership/errors.
An installed Codex app-server smoke test uses disposable homes and actual host
runner-stop, runner-listener, and native app-server close code: the selected
Codex exits, cleanup completes, and another owned native Codex remains running.
It makes no model requests and does not cover the complete browser session or
full runner app lifespan. The native smoke test is opt-in through
`OMNIGENT_TEST_CODEX_EXE`. The Electron main tests use mocked Electron APIs;
actual desktop quit with both harnesses still needs human verification.

Manual acceptance from a freshly restarted desktop built from this checkout:

1. Start one Claude and one Codex session. Ask each to run a 60-second foreground
   counter; record their process PIDs in Task Manager's Details tab.
2. Use the desktop's **Quit/Exit** action. Confirm the owned host, runner,
   harness, and command PIDs exit. Allow the grace period if a process is stuck.
   Closing the web browser or hiding/minimizing the desktop is not this test.
3. Reopen Omnigent and resume both conversations. Confirm history remains and
   a new native command runs without a rollout-file EACCES error.
4. Separately start a foreground host from this checkout. Repeat with both
   harnesses and stop that host with Ctrl+C. Confirm its session PIDs exit.
5. Keep a separately started host/session running while quitting the desktop.
   Confirm that independently owned session remains usable. Repeat desktop
   quit once with idle sessions and once during new-session startup.

To run the maintained native smoke test without using existing sessions:

```powershell
$env:OMNIGENT_TEST_CODEX_EXE = "C:\Users\keivan.kechmiri\AppData\Local\AI-Harness-Runtimes\codex\bin\codex.exe"
.\.venv\Scripts\python.exe -m pytest tests/runner/test_windows_runner_shutdown.py -k owned_native_codex -n0 -q
Remove-Item Env:OMNIGENT_TEST_CODEX_EXE
```


### Automatic native PowerShell selection for the primary Windows harnesses

`omnigent/inner/windows_powershell.py` owns shell discovery for Claude, Codex,
and Copilot. It checks the PowerShell 7 installation under `ProgramW6432` and
`ProgramFiles`, then compatible portable installations already on PATH. Store
execution aliases and resolved Store targets are excluded from preferred
selection. The selected executable directory is placed first in each child
process's copied PATH, preserving other tool directories. Repeated preparation
avoids duplicate prefixes and handles Windows environment key casing.

Claude native terminal startup and Claude SDK options, Codex SDK/native
app-server/remote-terminal environments, and Copilot SDK client startup all use
the shared helper. Copilot's GitHub host setting now belongs to that copied
child environment too. No personal config file, global PATH, or sandbox mode
is changed. Installation-root discovery reads only the needed host environment
values and does not add host credentials to filtered or partial launch envs.
A machine without a compatible PowerShell 7 retains its existing vendor shell
fallback; Store-only discovery logs installation guidance rather than claiming
the Store sandbox problem is repaired. This change does not install PowerShell.

The local native smoke started from a Store-first child PATH with the ordinary
PowerShell install removed from PATH. The resulting command ran
`C:\Program Files\PowerShell\7\pwsh.exe`, and the parent PATH remained unchanged.
Resolver tests and harness integration tests cover fresh startup, the Codex
remote terminal used for resume, credential-filter preservation, SDK child env,
and fallback behavior. Existing runner/host shutdown hooks apply to all three
primary harnesses; Copilot close tests check session/client cleanup and repeated
close. Actual Copilot UI execution remains a human acceptance check.

Combined focused shell/shutdown validation: 295 tests and three subtests passed;
two symlink cases skipped because this Windows account lacks symlink privilege.
An additional Codex launch/environment selection passed 121 tests with eight
symlink skips. Linux-target Pyrefly reported zero errors. The broader Claude
native suite retains 19 existing Windows failures, reproduced with the new
shell helper disabled, so these focused results do not claim a clean full
Windows suite. Copilot child `env` support was confirmed in the installed sibling
checkout SDK 1.0.16; this checkout has no installed Copilot SDK for a live UI
probe. No optional dependencies were installed for these checks.

After restarting the updated host/desktop, remove the manual PowerShell PATH
prefix from your startup instructions. Create one session with each of Claude,
Codex, and Copilot and ask its native shell tool to run:

```powershell
$PSHOME
(Get-Process -Id $PID).Path
```

With the ordinary PowerShell 7 install on this machine, expect
`C:\Program Files\PowerShell\7` and its `pwsh.exe`. Repeat after **Stop session**
and sending a message to resume. Run a foreground counter in all three, quit
the desktop or stop the owning host with Ctrl+C, and confirm their recorded
process PIDs exit. Independently owned sessions should remain usable, and
conversation history should still be available after restart.


### Installing this fork's Windows release artifacts

Fork release validation now requires the shutdown and primary-harness shell
environment regressions on both Linux and Windows, plus the desktop host-helper
and server-manager tests. Its successful build produces two artifacts for the
same source commit:

- `omnigent-windows-<commit>`: the core and lockstep SDK wheels, bundled web UI,
  and `INSTALL.cmd` / `install.ps1` installation helpers.
- `omnigent-windows-desktop-<commit>`: a portable x64 Electron ZIP containing the
  updated desktop shutdown integration. Extract it to a new directory and run
  `Omnigent Dev.exe`, using the CLI installed from the matching core bundle.

The desktop uses the existing development app identity and fork source/version
metadata. Automatic upstream desktop updates are disabled, and the workflow
never publishes to the upstream update endpoint. These are unsigned fork build
artifacts. The native containment candidate is packaged for explicit development
verification; production `native` selection still requires its signed approval
manifest. Legacy launcher selection remains the default.

Download both artifacts from the same successful Fork release validation run.
Quit the existing desktop, stop its owning host/server, install the core bundle,
and start the extracted desktop before repeating the three-harness PowerShell,
Stop/resume, and desktop Quit checks above. Merely updating the Python wheels
cannot update an already packaged Electron desktop.

### 2026-10-09 shutdown and PowerShell release validation

Feature code was pushed directly in `6e7aab88002d166e98893982e3b3621c855c2dda`.
The matching release source is `489665868933fab513199060fd2349bc65d7ea01`.
Subsequent commits repaired CI invocation and native test assertions/cleanup;
the final update ports two Unix-dependent test fixtures and pins Lightning CSS
1.33.0. The shutdown and shell-discovery feature code is unchanged. No PR,
main merge, public package release, or Docker image publication was performed.

| Workflow | Source and result |
| --- | --- |
| [Fork release validation](https://github.com/MusicPartner/omnigent/actions/runs/37962935896) | Success on `489665868`; both OS gates and matching CLI/desktop builds passed. |
| [Integration](https://github.com/MusicPartner/omnigent/actions/runs/37954666470) | Success on feature commit `6e7aab880`; all harness matrix legs passed. |
| [E2E](https://github.com/MusicPartner/omnigent/actions/runs/37954670494) | Success on `6e7aab880`; all four shards passed. |
| [E2E UI](https://github.com/MusicPartner/omnigent/actions/runs/37962959935) | Success on `489665868`; Browser Contract UI and all ten shards passed. |
| [Docker build](https://github.com/MusicPartner/omnigent/actions/runs/37954680499) | Success on `6e7aab880`; build-only, publishing skipped. |

Integration, E2E, and Docker were not rerun after the CI/test corrections and
CSS parser update; their Python feature source is unchanged. E2E UI was rerun
for the parser update; its earlier run `37954675337` also passed all ten shards
and Browser Contract UI on the feature commit. Conclusions include each workflow's
existing
test retry policy and are not a claim that every test passed its first attempt.
The failed release runs were diagnosed and corrected on new commits:

- `37954644151`: Node 22 rejected `--test-isolation=none`; use ordinary `--test`.
- `37954994893`: Windows rendered administrator SDDL as `LA`; compare actual
  SID identities and exact protected ACL entries instead of presentation text.
- `37955892125`: the psmux test deleted its executable before awaiting the
  native supervisor. It now records and awaits that exact owned launcher too.
- `37957267551`: the CLI bundle and all required checks passed, but PowerShell
  split unquoted dotted builder options. All desktop config options are quoted.

The exploratory Windows sweep remains separate from required checks. In
`37957267551`, its 3,950-item selection stopped on pytest-timeout in
`tests/inner/test_model_auth.py::test_cancelled_ucode_mint_terminates_helper`.
Its Actions conclusion was normalized to success by `continue-on-error`; the
underlying sweep did not pass. This is the previously recorded Windows helper
cancellation portability gap, not a clean whole-Windows-suite result.

The first complete matching CLI/desktop run
[37959695922](https://github.com/MusicPartner/omnigent/actions/runs/37959695922)
passed on `cf8f9a333`. Both downloaded artifacts were independently inspected:
ten Python modules and four Electron modules matched that source commit, the
native binary matched its manifest digest, and desktop version/build/source
metadata matched. The manifest records reproducible x64 builds with MSVC
14.44.35207 and Windows SDK 10.0.26100.0, without signing/release approval.

The final downloaded artifacts from `37962935896` passed the same independent
source/metadata checks on `489665868` (ten Python and four Electron modules):

- [CLI bundle, artifact 11633160483](https://github.com/MusicPartner/omnigent/actions/runs/37962935896/artifacts/11633160483).
- [Desktop ZIP, artifact 11632913523](https://github.com/MusicPartner/omnigent/actions/runs/37962935896/artifacts/11632913523).

Required Linux results: 130 regression tests passed with 21 platform skips,
1,040 focused integration tests passed with 13 skips, and 23 desktop tests
passed. Required Windows results: 150 new regression tests passed with one
skip, 23 desktop tests passed, 50 upstream hard tests passed with ten skips,
88 native lifecycle tests passed, 250 stable tests passed with 23 skips and
two deselections, 34 hook/shell tests passed with one deselection, eight real
psmux tests passed, and the argv-helper test passed. Applicable staged hooks
passed; Linux-target Pyrefly reported zero errors. The local Windows hook
launcher cannot execute its Unix shebang, so that check used the installed
Windows executable with the same project configuration.

CI web build also emitted no highlight/Lightning CSS warnings. The packaged
desktop is `Omnigent Dev` 0.17.0 with upstream updates disabled and its exact
source commit embedded. The native candidate hash remains
`3d2564228c78a637c5c47bc350937cb2474e61ca6a855b272e0191cac6984c03`.

### Broader Windows findings and follow-ups

The final follow-up replaces the cancellation test's Unix shell script with a
real Python subprocess and a bounded readiness handshake. It verifies the exact
helper exits after cancellation on Windows and is included in both required OS
gates. ACP fake-agent source files now explicitly use UTF-8; both local mocked
conversation regressions passed. Neither fix changes production authentication.

Lightning CSS 1.32.0 warned on the standard `::highlight(name)` syntax even while
preserving it in generated CSS. The pinned 1.33.0 parser fixes both warnings:
local Vite production build passed with both search selectors preserved and no
highlight warnings, and 16 preview-search tests passed. No CSS/runtime workaround
was added. The unrelated large-chunk build advisory remains.

The diagnostic sweep is not a Windows production acceptance gate. Local focused
reproduction found existing native attachment failures at `os.O_DIRECTORY` /
`os.O_NOFOLLOW` and descriptor-relative operations. Windows attachment delivery
needs a native-handle implementation preserving reparse-point, directory, and
file-identity checks; replacing those flags with ordinary path writes is unsafe.
At that build, attachment-dependent Claude/Codex workflows remained unsupported.
The Windows storage follow-up below replaces those POSIX-only operations.
Other reproduced gaps include POSIX chmod assertions, Linux-only bubblewrap
tests, and signer-home refusals in mocked Codex SDK tests. Retain credential
refusals and isolate those platform support tasks from shutdown/shell selection.
The earlier quiet run's progress markers do not identify every failure; current
diagnostic output prints names, and complete sweep status is recorded below.

In the final run, the auth cancellation and both ACP regressions passed. The
broader 3,950-test selection recorded 99 `FAILED` cases before a hard timeout
at approximately 61% in
`test_cancelled_close_contains_worker_and_retains_incomplete_signer_cleanup`.
The mock's Unix paths fail readiness validation on Windows; startup then awaits
its intentionally blocking cleanup before any worker starts. This is separate
from the real signer's bounded shutdown. There is no complete suite summary.
[The maintained failure inventory](BROADER-TEST-FINDINGS-2026-10-09.md) records
confirmed node IDs and separates reproduced support gaps from unverified causes.

Install the matching CLI bundle and extracted Electron ZIP, then perform the
Claude/Codex/Copilot PowerShell, Stop/resume, desktop Quit, and independently
owned-session checks above. Live desktop acceptance with all three harnesses
remains a human check. The native private-job candidate remains unsigned,
explicitly opt-in, and refused by production `native` mode pending signing and
release approval.


## Windows attachment storage follow-up (2026-10-09)

Feature source: `57575476067af12a311004860418e71c120e679c`; validated test
correction: `208591ece9026fd47f62f8ee8b4c2b77e5861a77`. The latter changes tests
and documentation only; production source is identical. No PR was created.
The separate [attachment plan](ATTACHMENT-DELIVERY-PLAN.md) records the storage
contract, upstream review, consumer coverage, and manual acceptance steps.

`windows_attachments.py` owns the Windows filesystem implementation; two narrow
dispatches select it from the shared attachment helper. Decoding, HTTP reads,
capability declarations, executor transports, and resume resolution remain in
their existing modules. POSIX file operations remain unchanged. Images and
filesystem attachments are delivered through the existing Claude/Codex native
interfaces; the existing Cursor/Kimi/Antigravity image consumers are covered.
This does not register Copilot attachment support or add a streaming shell tool.

Directory and file operations use validated handles and relative `NtCreateFile`
opens. Tests reproduce attribute-only directory-to-junction mutations and prove
refusal without redirected writes. The helper refuses reparses, hard-linked
leaves, unsafe names, and untrusted mutation permissions. It preserves equal-byte
reuse and deterministic collisions without overwriting different content,
cleans up its exact partial file handle, and retains resize metadata aliases.
New leaves receive protected current-user/SYSTEM ACLs without execute access.
Safe existing owners are retained during ACL migration. The storage must be on a
fixed local drive supporting Windows ACLs; this is not filesystem/network sandbox
isolation. Refusal logs omit exception locals and attachment payloads.

Required attachment results in
[release validation 37970056214](https://github.com/MusicPartner/omnigent/actions/runs/37970056214):

| Platform | Cache/security | Consumer and resume delivery |
| --- | --- | --- |
| Linux | 43 passed; 66 Windows-only skips | 35 passed; 82 unrelated tests deselected |
| Windows x64 | 109 passed; no skips | 35 passed; 82 unrelated tests deselected |

Local Windows security checks passed 64 cases with two actual symbolic-link
privilege skips; the shared suite passed 38 with five such skips. Real junction,
hard-link, concurrent writer, ACL, non-execute, and attribute-only race checks
ran locally. The CI account could run all symbolic-link cases. Staged hooks
passed, and the Linux-target Pyrefly check reported zero errors.

The first release attempt, `37969495382`, passed Linux and failed two Windows
migration assertions: its pre-existing directories/files used the trusted
Administrators owner rather than the test's assumed current-user owner. The
correction snapshots and validates that existing owner, requires it unchanged,
and still asserts exact protected user/SYSTEM ACLs and non-execute file access.
Production ownership validation was not weakened.

Live Windows native-vendor acceptance remains separate. In Codex 0.162.0,
`localImage` is read by the same-user app-server, while a ZIP path in text does
not grant sandbox filesystem access. Test the ZIP read under the actual sandbox
policy; do not implicitly loosen the cache ACL or switch to full access. See the
plan's exact vendor source links and image/ZIP/Stop/resume steps. Linux mocked UI
checks cannot establish this Windows sandbox acceptance.


Both required compatibility jobs and both Windows artifact jobs passed in
`37970056214`. The CLI bundle installer/uninstaller checks passed. Downloaded
artifacts were independently inspected: twelve Python modules, including the
Windows attachment helper and shared dispatch, match `208591ece`; four Electron
modules and desktop source/version/dev metadata match the same build. The
packaged native candidate still matches its unchanged manifest SHA-256 and
remains unsigned without production native-mode approval.

- [CLI bundle, artifact 11635294449](https://github.com/MusicPartner/omnigent/actions/runs/37970056214/artifacts/11635294449).
- [Desktop ZIP, artifact 11637425061](https://github.com/MusicPartner/omnigent/actions/runs/37970056214/artifacts/11637425061).

[Integration 37969521491](https://github.com/MusicPartner/omnigent/actions/runs/37969521491)
and [E2E UI 37969530034](https://github.com/MusicPartner/omnigent/actions/runs/37969530034)
passed on feature source `575754760`. UI includes Browser Contract UI and all ten
shards using mocks. These were not rerun after the Windows migration assertion
correction; application source is unchanged between the two commits.

The separate non-blocking Windows diagnostic recorded 64 failures before its
known signer lifecycle fixture hit the 300-second hard timeout. No attachment
failures were recorded, but there is no completed whole-suite result. Keep the
remaining platform/signer backlog in the maintained failure inventory.


[Backend E2E 37969525794](https://github.com/MusicPartner/omnigent/actions/runs/37969525794)
on feature source `575754760` passed three shards on its first attempt. Shard 3
failed its Cursor forwarder FD-exhaustion test's initial session-items HTTP probe
with `httpx.ConnectError`, before changing the descriptor limit or filling
ballast. The test, its fixture, and forwarder are unchanged from the earlier
successful `489665868` build. This fixture's server log was not included in the
uploaded artifact, so server-exit versus transient connection failure was not
established. Only the failed shard was retried; the original passing shards were
preserved.

Attempt 2 completed successfully: shard 3 passed, and the original passing
shards 0, 1, and 2 remained preserved. The workflow is green after that targeted
retry; the first-attempt baseline connection failure remains recorded above.
