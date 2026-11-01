# Windows isolation implementation roadmap

Updated 2026-11-01. This is the current master roadmap; older release and
isolation records remain dated evidence, not current execution instructions.

## Current continuation: allowance reset and correction package

Correction checkpoint **`836f308e79f4231e8f9e2efe2aea70d7eabab69b`** is now
published with normal commit/push hooks and matching live origin. **Reset
allowance: 1/5 used, four remaining.** Fork **41333606690**, Lint
**41333609058** and Integration **41333611385** were verified at that exact
SHA and completed successfully. Both preparation jobs, focused Linux, native
Windows, CLI artifact and desktop artifact jobs passed. The ANSI transport,
real startup and identity audit gates passed. Downloaded startup JUnit has
three executed cases and no skips/failures/errors; broader Windows has 4,556
actual records, 233 skips and no failures/errors. C #15's complete clean-wheel
and cache/reinstall/sentinel-refusal/uninstall roundtrip passed remotely.

Read-only inspection of the downloaded CLI bundle verified three lockstep
wheels, 13 files, three source fingerprints against 836f308e's Git blobs, and
exact LF-normalized installer/uninstaller/helper bytes. Its actual core commit
field is empty; native resource remains unsigned and `release_approved=false`.
Desktop ASAR records version `0.20.0`, `omnigentSourceCommit=836f308e...` and
`omnigentBuild=dev`. ZIP SHA-256:
`3879e2977d74ca3409483b4236f8452f760df2acd23751c3686a0f7bc8112908`
(149,172,501 bytes). This is package consistency, not GUI, signing or production
acceptance. No provenance manifest was added to these downloaded artifacts.

D #35's current local suite passed 59 tests in 5.55s after the intervening-edit
recheck. The next coordinated package contains its separate checker, shared
synthetic fixture, unit/CLI tests, candidate-only record/reverify gates and
these reconciled status records. Round 2 is allocated, not yet consumed; it
will require normal hooks, exact-SHA fork/Lint/Integration results and the
actual uploaded provenance manifest. Desktop automation and broader hooks
remain separate. The paragraphs below preserve pre-publication evidence.

Pre-commit's stash restoration converted only the two excluded Electron
files' checkout line endings from CRLF to LF under the new attributes.
Reconstructed CRLF SHA-256 values matched their pre-commit hashes exactly;
all semantic content remained excluded. The launcher test was byte-identical.
No excluded changes were staged and no broad checkout rewrite was performed.

The user reset the remote allowance to **five fresh coordinated rounds**:
**0/5 used, five available** before this correction package's publication.
The three preceding rounds remain historical evidence, not the active cap.
Pushes, corrections, docs publication and validation rerun batches share this
ledger. No main promotion, production publication, signing/native-default
change, WSL, history rewriting or real-user installation/PATH test is included.

The selected worktree, branch, full HEAD and live origin were reverified at
`3c191b8bba11f7abcb585a7c613206c10f53edc1`; the index was empty and the
three older Electron/launcher files remained excluded. The reviewed next
checkpoint contains the C #11 Windows ASCII JSON/UTF-8 fixture correction,
explicit ANSI-mode CI control, D #36 scoped LF attributes and real checkout
test, preservation assertions, and current status pointers. Shared shell
decoding, POSIX transport, test pins and workflow triggers remain unchanged.

Fresh local verification: **74 passed, one actual symlink-privilege skip in
34.40s** with `PYTHONUTF8=0`. The real Unicode workspace search and both
plain/uv Unicode tool identities each passed exactly once. D #36's owning
checkout/map/workflow suite passed **42 tests in 15.84s**. These are separate
runs, not aggregate whole-suite acceptance.

Cached pnpm 11.15.1 was recovered, but its standard formatter invocation on
the disposable LF export attempted a dependency installation preflight and
failed before Prettier ran because the subprocess could not resolve pnpm.
No dependency installation completed. The prior direct Prettier check remains
valid scoped evidence; it is not the required pnpm gate. Web edits remain
excluded, and the maintained checkout is not mass-rewritten. D #36's checkout
contract is published and its two-OS CI gate passed; broader hook/setup
reproducibility remains open. Historical round 3's skipped artifacts remain
unsuccessful evidence; the later 836f308e roundtrip does not relabel them.

### Historical round 3 checkpoint

Published runtime/cache correction checkpoint:
`3c191b8bba11f7abcb585a7c613206c10f53edc1`. Normal commit and push hooks
passed; live origin matched. **3/5 remote rounds used, two remaining.**
At that exact SHA, Lint and Integration passed. Fork validation passed both
terminal preparation jobs and focused Linux, but native Windows failed its
new transport gate: 58 passed, 17 failed. Artifact jobs were consequently
skipped; the cache correction has no remote bundle acceptance yet.

The failures exposed two distinct ANSI-mode gaps: UTF-8 search JSON was decoded
through the helper's default codec, corrupting Unicode paths, and two Unicode
fixtures omitted explicit file encoding. Both reproduced locally with
`PYTHONUTF8=0`. The follow-up uses ASCII-escaped JSON only on Windows and
explicit UTF-8 fixture writes; generic shell decoding and POSIX output stay
unchanged. **72 tests passed in 33.48s** in ANSI mode, then **25 passed in
4.26s** after normal hooks. The candidate CI step explicitly disables UTF-8
mode and verifies it before the transport suite. These changes are local,
not part of round 3 and not yet pushed.

D #36 now has a local scoped LF checkout rule for formatter-managed web text
extensions, retaining binary AppIcon overrides. Representative LF Git blobs
were converted to CRLF by the system `core.autocrlf=true` setting. A real
disposable checkout failed before the rule and passed all three modes
(`true`, `input`, `false`) after it: **3 passed in 12.30s** before formatting.
No global Git configuration or existing checkout mass rewrite was performed.
The standard whole-web formatter check remains pending in an external
source-matched LF export; the current checkout's older CRLF files have not
been rewritten. Broad hook reproducibility is not claimed complete.

The external Git LF export contains 1,761 tracked web paths from the exact
published index, converted only through the candidate attributes. The installed
`prettier.CMD --check .` passed with unchanged arguments/configuration. The
required `pnpm exec prettier --check .` wrapper was unavailable after the shell
reset, so this is a direct-tool result, not that gate's pass. The disposable
clone's initial full checkout hit Windows path-length errors in unrelated
snapshot paths; only its web input closure was recovered and verified, not a
clean whole-repository checkout. Owning checkout/map/workflow tests subsequently
passed **42 tests in 16.40s**; normal hooks passed with the established
`PYTHONUTF8=1` environment. A separate ANSI-mode custom-lint run failed on an
existing implicit source reader, so broad ANSI hook compatibility remains open.

The three previously excluded Electron auth/launcher test files remain local.
Items 8 and 16/25's locking/privacy contract, D #35 and E #37 remain open.

### Historical round 2 checkpoint

Published B/C maintenance and item 15:
`15f11e64929bfeb65bab3513ba43ed73c6fcadba`, on the branch below. Normal commit
and push hooks passed; live origin matched. Existing remote allowance is
**2/5 rounds used, three remaining**. No second follow-up push or rerun has
been made. The 96ee paragraphs below describe the preceding checkpoints.

All six dispatched runs were verified at that full 15f SHA. Lint, Integration,
backend E2E, UI and nonpublishing Docker completed successfully. Fork
validation's Linux, native Windows and desktop artifact jobs completed
successfully. The CLI artifact installer roundtrip failed on newly generated
Python bytecode after receipt creation. Downloaded startup JUnit passed
the maintained identity audit: three executed, no skips/failures/errors.
CLI artifact roundtrip/provenance remain pending; this is not final acceptance.

### C item 15: artifact-discovered cache correction

At 15f, CLI smoke generated a new
`tools/omnigent/Lib/site-packages/omnigent/__pycache__/install_ledger.cpython-312.pyc`
after the receipt was recorded. The subsequent preflight correctly refused the
unrecorded item, preventing the intended reinstall/uninstall roundtrip. This
invalidates the earlier assumption that the installed inventory stays static.

The local correction derives optional `__pycache__` directories and exact
CPython 3.12 cache filenames (normal, opt-1 and opt-2) only from receipt-recorded
`.py` sources under this tool's site-packages. It does not allow arbitrary
cache contents, unrecorded module names, other interpreter tags, reparse points
or type changes. Cleanup uses the fully validated live inventory, with literal
file removal and bottom-up empty-directory deletion, never recursion. Receipts
are still accidental-collision guards, not hostile-writer/security proof.

Real `py_compile` generation after receipt creation and negative name/tag tests
pass with all owning installer suites: **107 passed in 204.59s** before final
formatting corrections. This R is local, not yet validated remotely. A new
coordinated correction/runtime checkpoint will use the next existing round,
not rerun or relabel the failed 15f artifact result.

### C items 11/12: local R corrections

Native Windows reproduced `pass_fds not supported on Windows` in the real
plain local-tool caller. The existing shared stdout protocol now covers local
Windows execution; POSIX fd 3 and srt/container command construction remain
unchanged. Real plain and uv subprocess tests pass, with uv offline, no-project,
no-sync, an existing interpreter and no dependency downloads. State, secret
stripping, cancellation, Unicode/debug output and transport selection are
covered by the owning suite. The shared stdout decoder now refuses logical
responses over 1 MiB; `communicate()` still buffers stdout/stderr in memory.
This decoder correction also applies to existing wrapper transports.

Search failed through the actual supplied Windows environment despite working
shell and direct-Python controls. The local Windows caller now reuses
`windows_python_argv` and `launch_command`, retaining isolated mode and explicit
UTF-8 for this JSON producer. A piped isolated-Python control proved cp1252
stdout/Unicode failure; console success was not valid pipe evidence. POSIX and
nonlocal environments retain the existing shell transport. Path separators are
normalized by the execution-side script only on Windows; POSIX backslash
filenames remain unchanged. Shared grants, cwd, query/glob semantics, search
limits and UTF-16 columns remain canonical.

Focused combined validation: **73 passed, one skipped in 35.22s**. The only skip
is a separate real no-follow symlink test after Windows error 1314; all 15
existing query/glob scenarios execute without that privilege requirement.
Normal scoped hooks passed. The supplied-environment fixture was subsequently
changed to close only its owned helper. Post-cleanup validation, including a
representative filesystem caller and the B register/boundary suites:
**125 passed, one skipped in 41.37s**, with no helper-reaping report. Normal
scoped hooks passed again. These are separate run counts, not an aggregate.
These runtime/test edits are local and uncommitted, not part of 15f CI.

Final combined runtime, register, boundary and workflow-preservation checks:
**147 passed, one skipped in 40.20s**; normal hooks including Pyrefly and YAML
passed. The exact-branch CI additions require real Windows search/plain/uv
identities to execute successfully and retain a separate POSIX transport gate.
No triggers, permissions, shared pins or existing test commands were changed.
This is the next local checkpoint, not a new remote result.

### C item 8: contract inventory, not runtime completion

Actual filename consumers include ACP, Goose, Qwen, Kimi and Pi subprocess
paths, Codex worker/catalog preparation and Claude's explicitly configured SDK
path. Codex's consumer calls are in `codex_executor.py` at
`prepare_codex_catalog_probe` and `prepare_codex_worker`; a delegate's claim
that no callers existed was rejected against the current absolute source.
Claude's implicit tight wrapper is Linux-only; this does not prove all explicit
SDK paths skip Windows. psmux's launch override does not call the shared base
launcher's factory. Per-consumer runtime support and cleanup remain to verify.

Default `.cmd %*` cannot preserve unrestricted percent/ampersand argv. Keep
`create_exec_launcher(...)->str`, policy and native/signing defaults unchanged.
A pure rendering extraction would preserve that defect. Selecting a restricted
filename contract, migrating consumers to an explicit launch description, or
adopting a separately approved native distribution is a contract decision,
not an implicit permission to change the API or enable unsigned native defaults.
Item 8 remains open; items 16/25 and packages D/E are not complete.

### C items 16/25: bounded auth audit

`cli_auth._write_tokens_file` writes UTF-8 but its three JSON readers have no
explicit encoding. A synthetic non-ASCII user-id roundtrip proved the current
writer's JSON is entirely ASCII (`ensure_ascii=True`), so that mismatch alone
does not prove a decoding bug. No token-format or encoding change was made.

A disposable two-process check held `cli_auth._token_file_lock` in the parent;
the child announced readiness and entered its own lock before the parent
released it. Native Windows serialization is therefore absent in this tested
fallback. No real credentials, user state or network exchange was accessed.
This proves lock non-exclusion, not a duplicate-refresh result or lost update.
The existing synthetic token roundtrip passed separately.

Before a locking R package, define lock acquisition/failure/release semantics,
test simultaneous synthetic refresh exchanges and ordinary writers, and audit
Windows ACL privacy separately from POSIX mode bits. Shared token formats,
refresh recheck, refusal and credential provenance must remain canonical.
No lock/ACL implementation or security guarantee is claimed here.

## Goal and source

Reduce Windows-specific mechanics in frequently changing upstream owners and
reduce the work required to integrate the next exact stable release. Preserve
shared application policy; more leaf files alone do not demonstrate success.

- Worktree: `D:\Develop\Source\OpenSource\_AI\Omnigent\omnigent-v020-isolation`.
- Branch: `windows-parity/v0.20-isolation-p3-p5`.
- Latest published basis: `836f308e79f4231e8f9e2efe2aea70d7eabab69b`.
- Original extraction basis: `e1714c416d2608f7bfd5bf4ea93ee81b108d7311`.
- Validated v0.20 integration: `a67684ae0fc2299c8efc2e5f37824c71c8f044a6`.
- Exact upstream v0.20: `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee`.

Implementation was requested on 2026-11-01. Packages A/B and C #11/#12/#15
are published; Windows/cache acceptance passed at 836f308e after the distinct
round 3 failure. The C #11 ANSI follow-up and D #36 checkout contract are
published and remotely validated. D #35 is the next local package. Local #13 Electron files
and the #8 safe-launcher test remain excluded; they are not implicitly
authorized for this publication. Older dated paragraphs describe their
original checkpoints, not the current source or renewed allowance.

## Boundary rules

Shared upstream owners retain composer/parser/readiness, queue and lifecycle,
status arbitration, auth/grants, sandbox policy, configuration and tool
protocols. Windows leaves contain argv, encoding, Win32 process/filesystem
mechanics, mux dialect and discovery. Caller facades and injection owners stay
stable; independently installable SDKs must not acquire core dependencies.

Classify work explicitly: **A** audit/verification, **E** neutral extraction,
**R** observable reconciliation, **F** new capability. Reproduce defects before
R; do not conceal behavior changes inside E. Captured grids are not raw control
streams; Job Objects do not establish filesystem/network isolation.

## Original integration points

P0 closes the trusted checkpoint; P1 offers the best maintenance or safety
payback; P2 maintains/selectively refines seams; P3 is separate support work.

| ID | Point / owner | Current status and next action |
| --- | --- | --- |
| 1 | Source, owner map, semantic closeout | P0 checkpoint validated locally; current pointers and roadmap reconciled. Historical REVIEW and human acceptance remain open. |
| 2 | Claude OSC/status capability | Audit and separately approved relay/liveness R published. P0: validate the real startup gate, not a full ConPTY claim. |
| 3 | Mux dialect / `native/mux.py`, psmux | Audit and targeted buffer routing complete. P2: maintain actual-version operations and unknown exit-status contract. |
| 4 | Release inputs / CI reader | Published. Extend with #33; preserve historical refs and fixtures. |
| 5 | AST test/decorator ownership | Published. Extend with #34; qualified-owner hardening only if a real collision warrants it. |
| 6 | Wheel verification and bundle assembly | Published. Extend provenance with #35; preserve layout, digests and CRLF contracts. |
| 7 | Workspace paths / `hostPaths.ts` | Published; preserve facades, drive/POSIX/tilde behavior. UNC changes remain separate. |
| 8 | Batch launcher / `inner/sandbox.py` | Safe subset test local; actual percent expansion and ampersand splitting reproduced. P1: decide filename-consumer contract before R/E. |
| 9 | Pi Windows argv / `pi_windows.py` | Published; preserve package allowlist, containment, worker PATH and fallback. |
| 10 | Popup / `native/windows_cost_popup.py` | Published; encoding mechanics only, shared approval/dismissal lifecycle retained. |
| 11 | Content search / supplied environment | Published and remotely validated, including explicit ANSI control at 836f308e. Supplied-environment argv seam preserves shared grants, bounds and result shape. |
| 12 | Local tools / `tools/local.py`, `_runner.py` | Published and remotely validated; Windows reuses stdout, POSIX fd 3 remains. Secrets/state/cancellation retained; logical response cap is not bounded `communicate()` memory. |
| 13 | Auth/state paths / Electron CLI | Auth-only DATA_DIR correction local; daemon/cache unchanged. P0: validate checkpoint; later migration needs its own contract. |
| 14 | Desktop CLI discovery/update/cache | P2: minimal-PATH reproduction first; isolate enumeration, not shared precedence or update policy. |
| 15 | Installer/uninstaller ownership | Published helper/callers/cache correction; source-matched clean-wheel/cache/reinstall/refusal/uninstall and UV restoration roundtrip passed at 836f308e. Receipt limits remain; `scripts/install_oss.ps1` is unchanged and outside this fix. |
| 16 | Structured encoding | P1/P2: audit UTF-8 producer/reader pairs; do not globally reinterpret terminal/vendor output. |
| 17 | Test reachability / skip inventory | Three real post-psmux cases executed and audited at 836f308e, no skips. Desktop auth edits remain local; broader reachability is not automatically complete. |
| 18 | Terminal backend/registry/launch preparation | Existing seam sufficient. P2: protect caller arguments, environment and failure cleanup; no second launch framework. |
| 19 | Shell/vendor CLI/native environment/hooks | P2: actual-shell/version fixtures and kwargs; keep shared hooks/readiness policy. |
| 20 | Owned shutdown/process replacement | P1/P2: ownership, creation-time and grace contracts; distinguish Stop, Interrupt and Quit. |
| 21 | Capture/control/WebSocket/attach | P2: capability, resize, reconnect and read-only agreement; raw support belongs to #29. |
| 22 | Runner transport locator/endpoints | Existing seam sufficient. P2: verify cache/aclose coverage before adding focused tests. |
| 23 | Host listing/worktrees/filesystem/probes | P2: drive/UNC/reparse/containment matrices; keep traversal and grants shared. |
| 24 | Attachment handles/DACL/aliases/collisions | P1 safety/P2 maintenance: verify fixed-volume/UNC refusal coverage, retain private alias tests; vendor reads separate. |
| 25 | Credential privacy/locking/provenance/TLS | P1 audit: disposable concurrency and Windows privacy facts before R; preserve formats and trust domains. |
| 26 | Sandbox capabilities/parser/Job Objects | P2: explicit refusal and best-effort inventory; #8, #30 and #31 stay distinct. |
| 27 | Packaging/dependencies/toolchains/hooks | P1/P2: canonical groups, lockstep SDKs and reproducible setup; #36 extends ergonomics. |
| 28 | Electron identity/ZIP/updater/origin/CORS | P2: shared security dependencies and source/build identity; dev ZIP is not production acceptance. |
| 29 | ConPTY OSC/raw/repaint parity | P3: separate capability specification and real acceptance. |
| 30 | Hardened sandbox/trust/handle-safe deletion | P3: separate threat model and adversarial verification; receipts are insufficient. |
| 31 | Signed/native-default/ARM64/service/self-contained distribution | P3: split into separately selected product projects; not isolation prerequisites. |

## Additional maintenance deliverables

| ID | Priority / effort | Deliverable and next-release benefit |
| --- | --- | --- |
| 32 | P1 / medium | One current owner register and rename-aware cumulative fork/target delta report. Cover general fixes too; suggest review, never automatically DROP or close REVIEW. |
| 33 | P1 / medium | Versioned exact-release execution profile extending #4. Stage before baseline checkout; obtain candidate SHA from the actual run. Workflow still owns eligibility/permissions/publishing. |
| 34 | P1 / medium | Focused boundary/facade and collected-versus-executed contract checks extending #5/#17. Required skipped or deselected cases must fail meaningfully. |
| 35 | P2 / small–medium | Bundle provenance checked against actual wheel/resource/package data. Not signing, trust or installer ownership. |
| 36 | P1/P2 / small–medium | Scoped native checkout/hook reproducibility. Inspect normalization separately; no whole-tree rewrite or formatter bypass. |
| 37 | P1 / medium | Same-target integration rehearsal and scorecard: shared Windows hunks, reconciliation paths, repeated pins, contract drift and upstream-covered delta retirement. |

Prefer extending existing ledgers/helpers over duplicate hand-maintained
registries or generic platform frameworks. Historical fixtures stay immutable.

## Implementation packages and progress

Update this table and the chat checklist after each major step, naming the
original IDs, evidence, publication state and next work.

| Package | Scope | State |
| --- | --- | --- |
| A | Preflight; #1/#13/#17 closeout and existing #8 safe regression | Validated locally; current source/owner records reconciled and local test reachability corrections recorded. The prior 96ee results and follow-up work remain distinct. |
| B | #32 → #33/#34, then package validation | Published at 15f11e with normal hooks and integrated CI; maintenance and executed-startup gates passed again at 836f308e. Historical local suite counts remain separate; broader contracts remain review work. |
| C | #15 ownership and #11/#12 transports; #8 separate | Published at 3c191, ANSI correction at 836f308e; transport and actual cache/reinstall/refusal/uninstall acceptance passed at 836f308e. #8 API and #16/#25 locking/privacy changes are not implemented. |
| D | Evidence-based #14/#18–28 refinements and #35/#36 | #36 scoped checkout contract published at 836f308e; standard pnpm wrapper/broad hooks remain open. #35's separate local identity/inventory checker and synthetic CLI e2e are implemented, not published or remotely accepted. Other gaps remain selective. |
| E | #37 rehearsal/scorecard and justified upstream-covered retirement | Not started; needs a selected exact target and validated basis. |
| Publication | Local commits/push/Actions limits | Reset round 1 published 836f308e; all three source-matched workflows passed. Four rounds remain; D35 round 2 allocated, no next push/rerun yet. |

Dependency order: A first, then B. #33 and #34 can proceed independently once
#32 defines the map. C can progress independently after A; separate topics and
behavior decisions. D is selective. E measures the relevant completed work.
One owner edits workflow policy; shared index, terminal and native tests are
serialized. Disjoint analysis and file scopes may be delegated economically.

### Installer contract (#15)

The helper preflights absolute local paths, protected roots and detected
reparse points before uv/winget, PATH or filesystem side effects. Install accepts
fresh/empty or coherently receipted prefixes; it refuses nonempty receipt-free
prefixes without implicit adoption. Uninstall removes only validated inventoried
ordinary files and empty directories, never the entire supplied prefix
recursively. Unexpected content stops. Missing uninstall targets are no-ops.
UV tool variables and installer TLS state are restored after uv calls.

A genuine local three-wheel probe inventoried 1,799 uv entries without detected
reparse points; the complete source-matched CI bundle roundtrip passed at
836f308e. Stop if a future actual uv layout requires unsupported reparse
traversal. Receipts guard accidental collisions, not malicious concurrent
writers or proof of race-free deletion (#30). If a fresh install fails before
receipt creation, any partial prefix is left for manual review; use a fresh
prefix rather than automatic cleanup. During uninstall, uv failure preserves
the receipt and PATH but cannot roll back changes uv may already have made to
its tool environment. `scripts/install_oss.ps1` is unchanged and outside item
15.

### Launcher contract (#8)

Inventory real executable-filename consumers before changing `.cmd` forwarding.
Exact argv may require a support/API decision. Preserve existing native/signing
defaults until explicitly reviewed; pure rendering extraction alone would keep
the reproduced percent/ampersand defects.

### Artifact consistency (#35), local implementation

`verify-windows-bundle-provenance.py` is a separate stdlib checker, not an
assembler rewrite. It inspects one of each lockstep package's actual METADATA,
checks filename/version agreement, inspects the core's literal embedded
`COMMIT_SHA` without importing artifact code, and matches native resource
bytes to the existing manifest digest. It records sizes and SHA-256 values
for all bundle files except its own `BUNDLE-PROVENANCE.json`, retaining unsigned
and `release_approved=false` status without approving it. Additional nonlockstep
wheels remain permitted if their metadata and filename agree.

The candidate-only workflow records after assembly and independently compares
the live bundle after the installer roundtrip, before upload. The existing
assembler/template/checksum bytes and upstream eligibility remain unchanged.
Synthetic unit and CLI e2e tests cover identity mismatch, missing SDKs, stale
checksums, altered/extra files, malformed/duplicate metadata and size refusals.
The checker refuses detected links and bounds inventory count/member reads;
ZIP parsing and filesystem enumeration are not hostile-input or race-proof
security. The embedded source field remains builder-authored consistency
metadata, not signed attestation of source contents. A real historical 96ee
wheel contained an empty `COMMIT_SHA`, consistent with the documented no-Git
build fallback. Empty fields require three selected maintained modules to
match actual Git blobs at the requested full SHA, normalizing only CRLF to
LF; the manifest records the empty field and each fingerprint explicitly.
A nonempty wrong SHA still refuses. These selected fingerprints are not a
whole-source binding. Desktop ASAR consistency remains follow-up scope.

Final fingerprint/unit/CLI/register/preservation validation passed **59 tests
in 5.85s** after normal hooks. Read-only inspection of the actual historical
96ee three-wheel bundle passed against its own Git SHA: 12 files and three
module fingerprints, with its empty embedded commit recorded in the result.
No historical manifest was written and no evidence was relabelled as current.
The continuation recheck passed 59 tests in 5.55s. The same read-only checker
also inspected the actual 836f308e bundle against its Git SHA: three wheels,
13 files and three fingerprints. These local inspections do not prove that
the checker ran remotely or that a provenance record was uploaded.

Do not attribute this uncommitted checker or manifest to the completed 836f308e
Actions or historical bundles. Its remote validation will need a later reviewed
checkpoint, now allocated as reset round 2, not an automatic rerun.

## Verification and acceptance

1. Reverify selected root, full SHA, dirty paths, live origin, interpreter and
   import root before execution. Preserve foreign worktrees/state.
2. E: compare independent fixture bytes, argv, exports, injection owners, test
   nodes and shared POSIX behavior. Test the caller as well as the leaf.
3. R: disposable before/after execution for argv, supplied environments, auth,
   installer refusal/environment restoration and concurrent credential writes.
4. Native psmux is private and serial, with retries disabled. Inspect JUnit;
   startup requires exactly three executed cases, no skips/failures/errors.
5. Run owning unit tests, normal hooks/type checks and final YAML parsing.
   New tooling features need a happy-path e2e entrypoint test with synthetic
   repositories/artifacts; no server, credentials or real installs are needed.
6. Remote validation is a separate approved batch at the exact candidate SHA.
   Inspect raw tests and packaged source identity; old success stays old-SHA
   evidence. Trigger/permission changes are not validation workarounds.
7. Human checks: spaces/Unicode/other-drive paths; two-pane multiline paste and
   failed buffer without Enter; Stop then follow-up; Quit preserving another
   CLI; disposable upgrade/uninstall preserving unrelated sentinels.

Package A preflight on 2026-11-01 confirmed local HEAD and live origin at full
96ee, with the expected follow-up paths and no unexpected edits. Its focused
Python and Node evidence is retained in the dated closeout; these counts are
not combined with later package runs and are not new remote or production
acceptance.

### Package B checkpoint and verification

Local implementation of #32–34 completed on 2026-11-01 against the selected
checkout; local HEAD and live origin remain full `96ee061d`. Focused tests after
code/formatting corrections: **72 Python passed in 7.31s** and **23 Node
passed**, no skips. These are separate suites. Normal scoped hooks, including
TypeScript, passed at that Package B checkpoint; final hooks for the current
documentation/installer state are pending. `package-b-post-hooks.xml` is in the
external evidence directory. No commit, push or Actions dispatch was performed.

- #32: [current owner register](WINDOWS-INTEGRATION-MAP.json) covers IDs 1–37;
   `audit-windows-delta.py` reports rename-aware cumulative fork/target overlap.
   The v0.19 → 96ee / v0.20 report includes imported upstream changes because
   96ee already integrates v0.20. Its 1,565 cumulative paths and 1,438 unmapped
   review records are not Windows-only defect counts or semantic drop verdicts.
- #33: `release-profiles.json` and `release-profiles.mjs` select the existing
   three exact branch baselines before checkout; the reader's legacy two-file
   stage remains compatible. Workflow eligibility and permissions remain shared.
   Toolchain/test pins remain in canonical `release-inputs.json`; this extension
   does not automatically create future per-release test/toolchain matrices.
- #34: `windows-contracts.json` / `audit-windows-contracts.py` check six Python
   leaves, two facade symbols and three frontend modules. Static import rules
   and facade existence are bounded checks, not dynamic-import or full consumer
   signature verification. The actual Package A JUnit's three required startup
   identities passed; five unrelated POSIX/Linux skips do not weaken that gate.
   The supplied source SHA is labelled asserted invocation metadata, not proof
   of a clean committed artifact's provenance. Remote startup acceptance remains
   pending at a future published candidate.

To verify Packages A/B from the selected worktree without credentials or a live
server, run `.venv\Scripts\python.exe -m pytest tests/scripts/test_windows_delta_inventory.py tests/scripts/test_windows_contracts.py tests/e2e/test_windows_delta_inventory_e2e.py tests/e2e/test_windows_contracts_e2e.py -q -n 0 --reruns 0 --timeout 30`,
then `node --test .github/scripts/ci/release-inputs.test.mjs .github/scripts/ci/release-profiles.test.mjs .github/scripts/ci/release-test-groups.test.mjs`.
Inspect rename endpoints and owner IDs; `UNMAPPED_REVIEW` entries are review,
not automatic retirement. #8 remains a separate contract decision.

### Local item 15 evidence and remaining acceptance

Focused local suites passed separately: **82 tests** across the ownership
helper, installer callers and release tooling; **9 uninstaller tests**; and
**7 installer-caller tests**. These are separate observed suite results, not
one aggregated run. A genuine runner-temp three-wheel `uv` probe inventoried
1,799 entries without detected reparse points. Receipt replacement, state
validation, unexpected-sentinel refusal, uv uninstall and nonrecursive cleanup
also passed. Dependency installation was excluded and this was not an
application smoke test. The complete source-matched bundle roundtrip on CI is
planned and remains pending, as do final hooks for this documentation
checkpoint.

Preflight occurs before uv/PATH changes. Nonempty receipt-free prefixes are
refused by install and uninstall; a missing uninstall prefix is a no-op.
Unexpected content stops cleanup. If a fresh install fails before a receipt is
written, its partial prefix is intentionally left for manual review; do not
clean it automatically. An uninstall uv failure preserves receipt and PATH,
but uv's internal partial changes are not transactionally rolled back. These
are best-effort accidental-collision guards, not hostile-writer or race-proof
filesystem security.

Follow the disposable `-NoPath -SkipPsmux`
install/reinstall/sentinel-refusal/known-sentinel removal/uninstall procedure
in [QUICKSTART](QUICKSTART.md) against a future helper-equipped artifact, in a
disposable Windows account or VM. `-NoPath` prevents adding the install path,
but uninstall still writes the filtered User PATH value; the procedure checks
that it stays unchanged, not that no environment write occurs.
Historical artifact `96ee061d690a26ef37f9d432a98231105fa68d9f` predates the
helper and has no such safety claim. The separate `scripts/install_oss.ps1`
installer is unchanged. #13 Electron authentication changes and the #8
safe-launcher test remain local/unpublished and are not part of this
documentation checkpoint.

### B/C publication checkpoint

Normal scoped hooks and final fork YAML parsing passed. The combined
pre-format suite passed **152 tests** and release Node contracts passed **23**.
After formatting, 145 cases passed and seven installer-caller cases exposed
a PowerShell test-string continuation error; that exact error was corrected
and all seven passed in 20.73s. These are separate source-labelled results,
not a claim that the failed post-format run passed as a whole.
The next source-matched Actions batch checks the committed candidate, including
the complete wheel installer/reinstaller/sentinel-refusal/uninstaller roundtrip.
The B/C checkpoint excludes the local Electron auth and safe-launcher edits;
the desktop auth selector is deferred with its fix. Existing triggers,
permissions, main policy, canonical pins and historical fixtures are unchanged.

Completion means each active boundary has an owner, protected contract and
support limit; new stable integration needs targeted reconciliation rather
than copied Windows policy; and #37 demonstrates reduced maintenance effort.
The [November closeout](ISOLATION-CLOSEOUT-2026-11-01.md) retains exact remote
results, development-artifact limits and outstanding semantic/human review.
