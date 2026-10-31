# Windows isolation P0 checkpoint

## Identity, permission and classification

Implementation source: `e1714c416d2608f7bfd5bf4ea93ee81b108d7311`, branch
`windows-parity/v0.20-isolation-p3-p5`, worktree
`D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v020-isolation`.
Preflight independently verified clean status and live origin equality.
The selected interpreter is its `.venv\Scripts\python.exe`, CPython 3.12.14.
Installed psmux reports `3.4.0 (20aa1d7 2026-10-13)`; the probe started a
new private server, not an upgraded or restarted user's server.

The approved five-remote-round limit has **0/5 used**. These changes are
**A: audit/closeout**, not **E: neutral runtime extraction**, **R: portability
reconciliation** or **F: new feature**. No application code, versions,
locks, global feature defaults or workflow triggers were changed here.

## Item 1: source-labelled closeout and owners

The current isolation record and maintenance pointer now distinguish the
validated e1714 results from provisional history. The original integration
ledger is retained unchanged: 328 rows, 46 REVIEW paths; successful Actions
do not resolve semantic/live review. The companion
[P0 owner ledger](ISOLATION-P0-2026-10-31-ledger.csv) records current owners,
verification and proposed seams rather than relabelling old rows complete.

Previous e1714 runs and artifacts are recovered evidence, not new candidate
validation. Unsigned/dev artifact identity, absent dispatch interfaces,
vendor credentials, real migration, signing/update and human UX limits
remain explicit in the current closeout.

## Item 2: default Claude OSC status

### Verified source chain

`server/feature_flags.py` default-enables runner-only `CLAUDE_OSC_STATUS`.
`OMNIGENT_FEATURES=-claude_osc_status` explicitly disables it; the runner
registry retains its startup snapshot. A server's setting must not be
assumed to reconfigure a separate runner's environment or existing snapshot.
`runner/resource_registry.py::_launch_terminal_with_lifecycle` forwards
`program_status_app="claude-code"` for the Claude-native role when enabled.
The terminal registry assigns that metadata before launch. Psmux calls the
inherited `TerminalInstance._wrap_program_status`.

The generated observer runs `terminals/program_status.py::main`, whose
`relay` imports POSIX `fcntl`, `pty`, `termios` and `tty`. The bounded parser
and `harnesses/claude_native/program_status.py` status arbitration are shared
policy. The latter prefers live OSC, then the existing status-file poller;
the pane activity/exit watcher remains a distinct fallback/observer.

### Reproduced command-path failure

An external probe imported the exact selected source and used its real
feature resolver and psmux instance's inherited command wrapper. The child
was an isolated Python program writing a private marker and fixed output;
no Claude binary or vendor credentials were involved.

| Setting | Wrapper | Return | Child started | Observation |
| --- | --- | --- | --- | --- |
| Default, no override | OSC | 1 | No | `ModuleNotFoundError: No module named 'fcntl'` |
| Explicit enable | OSC | 1 | No | Same import failure |
| Explicit disable | None | 0 | Yes | Fixed child output received |

This reproduces an unsupported Windows observer-command path. It does not
prove full Claude startup/UX, fallback status delivery, remote-runner
configuration, OSC transport or a supported ConPTY alternative.

`ProgramStatusReader._read` also calls `os.kill(relay_pid, 0)`. On Windows
this must not be exercised against an unowned PID or accepted as a safe
POSIX-style liveness probe. The audit did not invoke the reader or weaken
its ownership requirements; any reconciliation must address that boundary.

### Decision required for R

A supported Windows observer/fallback contract must be selected separately.
A narrow unsupported-relay capability gate could preserve shared defaults,
parser and arbitration while avoiding a POSIX relay on native Windows;
its exact placement and reader behavior need covering contracts. A native
ConPTY OSC transport is a separate larger support project. Neither is
implemented or approved by this audit. Do not quietly globally disable
OSC or duplicate status policy inside psmux.

## Item 3: observed mux dialect

The probe launched an owned child through the real psmux backend with
`keep_alive_after_exit=True` and no OSC wrapper. The child printed a known
marker, published completion and exited with code 37.

| Operation | Result on new private psmux 3.4.0 server |
| --- | --- |
| Individual history bounds | Return 0, `0 2000` |
| Individual styled/joined history capture | Return 0, retained marker |
| Actual inherited `_exit_capture_args`, literal `;` | Return 0, bounds then retained marker |
| Dead/status/signal fields | `1 0 0`; status/signal are not the child's code |

The semicolon concern **did not reproduce** for this exact exit-capture
operation. Do not remove chaining or add a generic mux executor on the
basis of the existing launch comment. The inherited launcher and command
config modes are different operations; this result is not a universal
tmux-compatibility claim. The existing psmux unknown-status/signal overrides
remain necessary.

| Consumer | Reachability / preserved owner |
| --- | --- |
| `inner/terminal.py::_exit_capture_args` | Shared inherited capture; actual psmux operation probed above |
| Base tmux launch command sequence | Psmux has its own launch override; not certified by exit-capture probe |
| `native/mux.py` command/load-buffer helpers | Existing operation-specific selection; targeted Windows load preserved |
| Claude bridge paste | Owns bytes, clear/readiness, cancel/cleanup and verified submit, not mux leaf |
| `terminals/control_bridge.py` | Raw tmux control path; not psmux grid attach |
| Server/runner terminal attach routes | Select capture bridge for psmux; retain auth/read-only/resize policy |
| `native/native_cost_popup.py` | Platform command selection, fixed pwsh popup consumer; lifecycle stays shared |
| `terminals/ws_common.py` | Existing platform liveness command selection |

Buffer load/save across sessions, popup execution, resize/reconnect and
real vendor composer acceptance were not rerun by this P0 probe. Prior
source-labelled evidence remains scoped to its original selections.

## Execution evidence and limits

Raw evidence is outside the tracked tree:
`D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-isolation-next-20261031`.
`probe-p0.py` and `p0-probe-result.json` contain the exact source/interpreter,
generated-command results and real operation argv. It used fresh HOME and
USERPROFILE/config/data/PSMUX_DATA_DIR, `PSMUX_NO_WARM=1`, unique socket and
target, and killed only the private server it started. No unowned processes
or real installation/state were altered.

The focused feature/role/parser/fallback test invocation reported **51
passed, four POSIX PTY cases deselected**, then a `KeyboardInterrupt`
before completing all 52 selected cases (exit 1). This is **incomplete**,
not a passing suite. Its JUnit reported 50 tests and cannot certify the
console's 51-pass count or completion of the adapter cases. Source inspection
found both adapter cases feed the current process PID to the reader's
`os.kill(pid, 0)`. That is an unsafe Windows liveness dependency; its
connection to the interruption is a hypothesis, not a proven root cause.
Those cases were not rerun through that dependency.

A separate safe selection containing only feature/role/parser contracts
completed: **50 passed, four POSIX PTY cases deselected**, 0.80 seconds;
`p0-safe-focused.xml` records that selection. Adapter liveness/concurrency,
real POSIX relay and full Claude fallback remain unverified in this run.
This selection does not change workflow targets, markers or test code.

## Verification and next checkpoint

1. Run the external probe with the selected source's Python and absolute
   source path; it must identify e1714 and only operate on private state.
2. Compare default/enable/disable child markers and the inherited capture
   argv/results. Command-path failure must not be labelled full Claude UX.
3. Reuse the completed safe feature/role/parser contracts. Complete adapter
   liveness/fallback contracts only through a separately approved safe
   reconciliation; retain POSIX PTY execution in its proper platform lane.
4. Decide whether to defer the reproduced OSC portability issue while doing
   the approved neutral package, or approve a separately attributed R fix.
5. Keep item 8 separate. Do not consume remote rounds before local gates,
   and do not reinterpret this checkpoint as global support acceptance.

## Separately approved R: relay capability and non-signalling liveness

At this checkpoint the user selected **"Approve a narrow portability fix
first"**. This supersedes the pending-R decision above, not the original
probe results. The reconciliation is separate from items 4–6, 7, 9 and 10.

`terminals/program_status.py::program_status_relay_supported` declares the
existing POSIX transport unavailable on native Windows. The shared terminal
wrapper consults it before creating a reader or altering a stale snapshot;
unsupported transport returns the literal prepared child argv unchanged.
Feature defaults and runner-role metadata remain unchanged. The existing
file/activity fallback path is retained; no ConPTY/OSC support is claimed.

For Windows snapshot reads only, `ProgramStatusReader` reuses
`inner/_proc.py::process_alive`, a non-signalling psutil probe. POSIX keeps
its original `os.kill(pid, 0)` behavior. This read-only probe grants no
termination authority and introduces no snapshot/ownership schema change.

Tests extend the existing literal-argv launch scenario with supported and
unsupported transport, retain preparation-failure assertions, forbid signals
in the Windows reader branch and observe a real owned child's live snapshot
without terminating it, then reject its snapshot after exit. A native Windows
runner/psmux test covers default/enable/disable role metadata and actual
credential-free child startup with isolated state and owned cleanup.

Local boundary validation passed **15 tests**; the expanded focused run passed
**70 tests**, four POSIX PTY cases deselected, 3.89 seconds, zero failures/
errors/skips in JUnit (`p0-r-focused.xml`). Both original adapter concurrency/
error-arbitration tests now completed. Ruff checks/format and editor diagnostics
passed. These are uncommitted candidate working-tree results based on e1714,
not e1714 immutable-source results or remote acceptance. Full vendor status,
POSIX relay execution, hooks and candidate Actions remain pending.
