# Windows parity: remaining work and decisions

Research date: 2026-10-08. Branch: `windows-parity/v0.17-integration`.
Validated implementation: `2d43e9d95c28d4cb623f98d3d49de1af959f90cc`.
This plan records deferred work; it does not enable the proposed changes.

## Completed audit items

| Original finding | Current result |
| --- | --- |
| PowerShell clean-environment wrapper: execution policy and embedded quotes | Replaced by an isolated Python launcher in `1f40f896c`; no PowerShell script is involved in that wrapper. |
| Filesystem probe through `cmd /c`, including spaced Python paths | Probe uses direct executable/argument launch through the OS environment helper in `1f40f896c`. |
| Claude npm batch shim forwarding | Native executable lookup in psmux and Claude SDK paths, including rejection of npm script placeholders. |
| Bare tmux control calls on Windows | Bridge, attach/preflight, cost popups and WebSocket pane liveness select psmux on Windows; POSIX uses tmux. |
| psmux JSON argument handling | Real psmux/Python-child test proves exact JSON, quotes, percent, semicolons, spaces, Unicode, cwd and environment removal. Real Claude 2.1.294 Win32 capture also passed for settings-file and full inline JSON transport; automated version-matrix coverage remains. |
| Exit status verification | psmux 3.3.8 reports constant zero placeholders. Windows callers now report unknown status rather than false success; standalone Python launcher still preserves return code 37. |

The failed UI reconnect journey counted its expected undelivered-message notice
as a third assistant reply. Both failed attempts contained two Claude replies.
The assertion now excludes that specific notice while retaining duplicate-reply
checks. A separate CRLF-sensitive linter self-test mutation was corrected.
Neither failure was dismissed as flaky without investigation.

## Validation and failure classification

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
| Claude hook compatibility | Use direct `command` + `args` hooks for verified capable versions, with an explicit-shell fallback for older versions. | Removes shell parsing where the CLI supports it and keeps older installs usable. | Two paths to maintain. Requiring a tested minimum CLI simplifies this at the cost of mandatory upgrades. |
| PowerShell requirement | Keep ordinary terminal launches compatible with existing Windows clients; gate PowerShell-dependent popups separately. | No blanket new installation requirement. | More fallback behavior. Requiring PowerShell 7.3+ simplifies native argument handling but adds an installation prerequisite and does not fix batch forwarding. |
| Exact Windows exit codes | Keep unknown status until psmux reports a real value. | Honest behavior and small maintenance surface. | Cannot distinguish success/failure from pane death alone. An Omnigent sidecar protocol could recover status but adds synchronization, crash and cleanup cases. |
| Databricks signer auth on Windows | Treat as a separate Windows support task unless it is required for this release. | Keeps the current launch fixes focused and makes the trust requirements explicit. | Enabling it needs executable/parent ACL validation and portable helper fixtures; simply removing ownership checks is unacceptable. |
| v0.14 maintenance | Backport the shutdown escalation fix only if v0.14 remains supported. | Fixes ignored CTRL_BREAK on that maintained branch. | Additional branch validation and maintenance; no benefit if v0.14 is retired. |

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

Options:

1. **Native console launcher:** package a small executable that invokes the
   Python sandbox bootstrap with literal argv. A mature script-launcher library
   such as [distlib](https://distlib.readthedocs.io/en/latest/tutorial.html#using-the-scripts-api)
   offers Windows console executables. Prototype before choosing it: preserve
   argv, stdin/stdout/stderr, exit code, sandbox activation, process-tree cleanup,
   cwd, environment policy and temporary-file ownership. Verify wheel installs
   and supported architectures; do not require an end-user compiler. Distlib
   is currently present through development tooling, so production availability
   must be declared or packaged explicitly, not assumed from the local venv.
2. **Structured all-Python launch:** return a descriptor containing an argv
   prefix and owned temporary paths, migrate all owned callers to direct spawn,
   and integrate the filename-only SDK through a supported transport. This avoids
   a new native asset but is a broader refactor with more SDK upgrade maintenance.
3. **Harden `.cmd` quoting:** smallest diff, but nested shell parsing and percent
   expansion remain. This does not meet the requirement for general literal argv
   and is not recommended as the final solution.

Implement neither 1 nor 2 until the contract choice is made. Preserve existing
sandbox policy and refusal/fallback behavior during the migration. Audit who
owns the Windows Job Object: `activate()` is a no-op and containment comes from
parent-side `post_spawn()`, so simply calling the bootstrap does not establish
process-tree containment. This launcher change must not claim filesystem or
network isolation, which the current Windows backend does not provide.

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
`args`; current local CLI is `2.1.294`. The documented exec form passes an
argument array directly and requires a real executable on Windows. This is a
candidate for Python hooks, not proof of older Windows versions' behavior.
Validate the selected versions on Windows before changing settings generation.
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

The supplementary local capture is now complete on Claude Code 2.1.294 and
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
file contract. Next add repeatable, gated integration coverage and test the
agreed CLI/shell versions before broadening the support claim:

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
implemented. Do not bypass provenance checks or add blanket skips merely to
make the sweep green. A future fixture update should use a real portable helper
and a bounded startup wait that surfaces task failure, then verify cancellation
kills the helper. Existing POSIX provenance and descendant tests must remain.

## Remaining handover choices

- **Non-git workspace response:** keep v0.17's HTTP 400; the UI uses it to
  identify `not_git`. Restoring HTTP 200 with an empty list changes that contract.
- **Catalog-default model pin:** keep the validated replayed behavior unless
  CLI-managed model selection is preferred. Catalog pinning gives predictable
  Omnigent selection; CLI selection honors local CLI defaults but can differ
  between hosts. This is a product preference, not a Windows launch bug.
- **Two ACP Windows skips:** leave them dropped; the handover records that the
  tests passed without them. Reintroducing skips would reduce coverage.
- **Optional PR:** unnecessary for this work; keep the existing no-PR-to-main
  constraint. Existing dispatchable workflows provide branch validation.
- **v0.14 shutdown backport:** a separate task only if that branch remains in
  use; use a normal commit, never rewrite published history.
- **Earlier broad manual validation:** accepted as completed by the user. Only
  the new launch/bridge behavior needs the focused verification below.

## Implementation sequence after the decisions

1. Turn the captured real Claude argv/settings proof into gated coverage and
   establish the agreed CLI/shell versions, including the unproven minimal-env
   and semicolon/percent cwd cases.
2. Prototype and select the sandbox launcher contract; migrate callers and add
   meaningful literal-argument, sandbox-policy and lifecycle regression checks.
3. Apply explicit consumer quoting/direct hook argv; test POSIX, Git Bash,
   PowerShell 5.1 and supported PowerShell 7 paths that remain in scope.
4. Run staged pre-commit, targeted Windows tests and the existing branch Actions.
   Keep unrelated POSIX-only Windows test failures separate from new regressions.
5. Update installer/readiness documentation for any agreed dependency floor.
   Consider the v0.14 shutdown backport independently.

For each specific issue, make at most five fix/retest attempts. Inspect the
failure evidence before retrying; rerun only an affected job for a transient
failure. At the limit, record the blocker and evidence rather than suppressing
assertions or retrying indefinitely.

## Published history and future updates

The v0.14 worktree and published v0.14 branches were not changed. The process
launch changes in `1f40f896c` were included with the user's prior approval; this
follow-up implementation is the normal commit `2d43e9d95`. No PR to main was
opened and no published history was rewritten. If the follow-up needs rollback,
use a normal `git revert 2d43e9d95c28d4cb623f98d3d49de1af959f90cc` on the intended
branch after reviewing the resulting diff, then validate and push that commit.

For subsequent upstream releases, follow
[the fork maintenance workflow](../../.github/FORK_MAINTENANCE.md): ingest a
stable release into an isolated integration branch, preserve the Windows leaf
modules/caller seams, review conflicts deliberately, and validate before an
agreed merge. Keep the launcher, shell and auth decisions recorded here with
any supported dependency versions so they can be checked during each update.

## Local build ready for test running

The production web UI, core wheel and both Python SDK wheels were built locally
from implementation `2d43e9d95` on 2026-10-08. The core build stamp reports
`0.17.0 (2d43e9d9, built 2026-10-08T19:35:18Z)`. Built wheels are retained in
`dist/windows-parity-local/`; the production web bundle is in
`omnigent/server/static/web-ui/`. These generated outputs are ignored by Git.
The existing editable virtual environment uses the built UI and current source.

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
