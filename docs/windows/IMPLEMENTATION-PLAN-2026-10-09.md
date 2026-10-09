# Windows parity implementation plan

Date: 2026-10-09. Base: `9fab092f5249d037a8c60cb35a94962a5c0c49f2` on
`windows-parity/v0.17-integration`. The user accepted the upstream-aligned
recommendations and requested coding delegation to GPT-6.1 Sol / GPT-6 Luna.
Current pushed implementation: `28db4f72c973b15a96b00de29e11f3f93509c246`.
The production UI and fresh core/client/UI SDK wheels passed the local build
and isolated wheel checks; stamp `0.17.0 (28db4f72, built 2026-10-09T08:42:50Z)`.
Branch CI completed successfully; detailed evidence is in
[PARITY-NEXT-STEPS.md](PARITY-NEXT-STEPS.md#current-pass-validation).

## Outcome of this implementation pass

Package A did **not** pass the adoption gate. The test-owned distlib console
prototype preserved literal argv, Unicode/spaced interpreter and cwd, stdio,
exit code 37 and caller-owned file cleanup on native Windows x64. Its three
focused tests passed, including a test that deliberately demonstrates the
containment blocker: the stub starts Python before the parent can assign the
stub to a Job Object. Earlier descendants remain alive after that job closes.
The test terminates and waits for its owned escaped processes. Its deliberately
late assignment was not compared with the current `.cmd` launcher; it is not
evidence of an introduced regression over that baseline.

The production `create_exec_launcher(...)->str` seam, POSIX wrapper and core
dependencies are unchanged. Windows still uses `.cmd` `%*` forwarding; that
problem remains unresolved. The prototype lives only in
`tests/inner/windows_exec_launcher_prototype.py` and its focused test file.
It is not a supported runtime API or clean-wheel launcher. Native x64 evidence
does not establish ARM/x86 support or filesystem/network isolation.

The [launcher follow-up assessment](PARITY-NEXT-STEPS.md#follow-up-a-filename-compatible-native-containment-owner)
recommends a **custom native stub owning a private kill-on-close Job Object** as
the next prototype. Put Python into that job at creation, keep the handle
non-inherited, and hold it while waiting; terminating the stub can then close
the handle and kill the child tree even if parent assignment happens late.
Creation-time `PROC_THREAD_ATTRIBUTE_JOB_LIST` avoids the suspended-orphan gap
between creating a child and assigning it. This is a documented architectural
possibility, not a verified implementation. It preserves the filename API but
explicitly adds launcher-owned containment; nested jobs, SDK cancellation,
inactive policies, failure cleanup and native asset/signing builds require proof.

Any-job polling is not sufficient: this host already belongs to a job before
Omnigent assignment, and only the OS helper currently calls `post_spawn()`.
A membership gate would need intended-job identity and caller integration.
Parent-coordinated suspended spawn is the alternative when parent-only ownership
is required; it has broader caller/SDK resume and cleanup costs. Neither design
should quietly change ownership, API or credential/isolation guarantees.

No alternative is adopted in this pass. Credential policies, brokered-signer
refusals and unknown psmux exit status remain intact; v0.14 work is excluded.

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

## Scope and accepted choices

- Preserve upstream public launch APIs, canonical bridge lifecycle/settings,
  shared managed/native model selection and credential/containment rules.
- Replace sandbox batch forwarding through a Windows executable behind
  `create_exec_launcher(...)->str`; prove packaging, literal argv and lifecycle
  before adopting it. Keep the POSIX wrapper and SDK transport APIs.
- Use direct executable/argument command hooks where the supported Claude CLI
  permits them. Reuse the existing 2.1.161 minimum; do not introduce a separate
  legacy-version policy. Status lines and shell-only commands retain explicit
  consumer contracts.
- Quote shell programs for the actual consumer. Ordinary launches do not gain
  a blanket PowerShell prerequisite; popups require their specific capability.
- Automate isolated real-Claude command-line/settings evidence and connect
  meaningful coverage to the existing fork Windows checks. Use the supported
  minimum and upstream CI pin as compatibility targets, with current local CLI
  evidence; report unavailable or unproved targets honestly.
- Retain unknown psmux exit status. Full Windows brokered-signer authentication
  remains deferred because the current backend lacks required filesystem/network
  isolation. Do not weaken security checks or mask that known sweep failure.
- v0.14 backporting is excluded: the user confirmed nobody uses that version.
  Do not modify, delete or rewrite its branches/worktree.
- Native runtime validation targets this available Windows x64 machine/CI.
  Any other launcher architecture needs separate runtime evidence before being
  advertised as verified. No global CLI replacement or upstream main merge.

## Delegated work packages

| Package | Model | Owned implementation | Acceptance criteria |
| --- | --- | --- | --- |
| A: sandbox executable | GPT-6.1 Sol | Windows launcher leaf, minimal `inner/sandbox.py` seam, dependency/lock changes, launcher tests | Real executable returned through existing API; exact argv including quotes/percent/metacharacters/Unicode; spaces in interpreter/cwd; stdio and exit code; cleanup/containment behavior; clean-wheel availability; unchanged POSIX policy behavior. |
| B: hooks and shell consumers | GPT-6.1 Sol | `native/shell.py`, Claude Windows hook leaf/bridge transport seams, popup/resume consumers and their focused tests | Direct hook argv on capable supported CLI; one canonical hook/lifecycle definition; explicit POSIX/PowerShell consumers; preserved redirection/status chaining; missing-popup capability handled through existing fallback; no global PowerShell requirement or model-policy changes. |
| C: capture and integration coverage | GPT-6 Luna | New gated real-Claude capture/test helpers, focused fork CI additions, Windows pytest helper coverage | Authoritative Windows process command line plus literal hook recorder; isolated config and loopback endpoint; no credentials/provider calls; bounded waits and owned-process cleanup; meaningful assertions and pinned version reporting; integrates A/B tests after their interfaces settle. |

All agents use the shared v0.17 worktree and explicit file ownership. They do
not commit, push, dispatch workflows or edit another package's files without
coordination. The coordinator reviews combined results and delegates any fixes
back to the owner. Documentation updates, final builds and validation execution
are also delegated after the implementation interfaces settle.

## Execution order

1. Save this plan, then start A/B/C concurrently. C first studies the retained
   capture evidence and builds a repeatable helper; it coordinates with B before
   validating production hook transport.
2. A proves the executable prototype before switching the Windows seam. B
   audits actual consumers before changing quoting. If a required contract stays
   unclear, isolate the incomplete work and record the blocker rather than
   adopting an unsafe shortcut.
3. Run each package's meaningful targeted checks. Review the combined diff for
   ownership, public API, upstream replay boundaries and security semantics.
4. Delegate combined Windows checks, staged pre-commit and clean-wheel launch
   verification. Use Linux CI for POSIX coverage. Do not repeat the already
   accepted broad manual validation; exercise newly changed behavior.
5. Commit normally only after the required hooks pass. Push to the existing
   integration branch. Dispatch required branch workflows once, inspect failures
   and rerun only affected jobs when evidence supports a transient failure.
6. Delegate production web/core/SDK local builds from the final code revision,
   preserve the runnable editable environment, and update the parity/maintenance
   documents with evidence, support boundaries and exact test-run commands.

## Retry authorization and completion rules

The original five-attempt limit applied to the earlier probes recorded above.
The user has since revoked that limit and authorized continued capture work.
Record attempts and failure evidence; do not relax assertions to hide failures
or repeat green checks without a new reason. Dependency/version availability
failures must be distinguished from product failures.

Direct-hook adoption passed its native transport gate; executable-launcher
adoption remains blocked by containment. Code validation, required CI and local
build are complete. Manual Windows behavior checks remain for the user.
Unsupported auth/architectures and any unavailable CLI matrix rows remain
explicitly identified, without support claims.

For manual verification, start the local server and host from `omnigent-v017`,
open a space/Unicode workspace, start Claude and exercise Terminal/Chat,
resize/reconnect and literal `parity ; %PATH% Å` input. Verify sandbox launcher
argument/exit evidence as prototype results, not an adopted executable runtime.
