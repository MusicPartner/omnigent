# Windows isolation implementation roadmap

Updated 2026-11-01. This is the current master roadmap; older release and
isolation records remain dated evidence, not current execution instructions.

## Current execution checkpoint

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
- Published basis: `96ee061d690a26ef37f9d432a98231105fa68d9f`.
- Original extraction basis: `e1714c416d2608f7bfd5bf4ea93ee81b108d7311`.
- Validated v0.20 integration: `a67684ae0fc2299c8efc2e5f37824c71c8f044a6`.
- Exact upstream v0.20: `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee`.

Local implementation was requested on 2026-11-01. Packages A and B are
validated locally; package C's item 15 installer safeguards are implemented
locally. Final hooks and a source-matched CI/bundle roundtrip remain pending.
The published basis remains **96ee061d690a26ef37f9d432a98231105fa68d9f**;
no new result SHA is asserted. One coordinated B/C checkpoint push and
source-matched Actions batch is authorized as the next existing budget round
(round 2/5); it has not been run as part of this documentation task. This does
not renew the cap or authorize another round. The checkpoint plan excludes
local #13 Electron files and the #8 safe-launcher test unless explicitly added;
web files are excluded from the current push plan because the repository-wide
standard Prettier check has a pre-existing CRLF finding. No main promotion,
production publication, signing changes, WSL or foreign-state cleanup is
included.

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
| 11 | Content search / supplied environment | P1: reproduce native Windows execution before selecting a narrow argv seam. Preserve grants, bounds and result shape. |
| 12 | Local tools / `tools/local.py`, `_runner.py` | P1: reproduce plain/uv fd transport; reuse stdout protocol if justified, preserving secrets/state/cancellation. Audit actual buffering bounds. |
| 13 | Auth/state paths / Electron CLI | Auth-only DATA_DIR correction local; daemon/cache unchanged. P0: validate checkpoint; later migration needs its own contract. |
| 14 | Desktop CLI discovery/update/cache | P2: minimal-PATH reproduction first; isolate enumeration, not shared precedence or update policy. |
| 15 | Installer/uninstaller ownership | Implemented locally in `scripts/windows_bundle_state.ps1` and both bundle callers. Tests cover ownership receipts, preflight/refusal, inventory cleanup and environment restoration; source-matched CI roundtrip remains pending. `scripts/install_oss.ps1` is unchanged and outside this fix. |
| 16 | Structured encoding | P1/P2: audit UTF-8 producer/reader pairs; do not globally reinterpret terminal/vendor output. |
| 17 | Test reachability / skip inventory | Post-psmux three-case and desktop auth selections local. P0: actual execution; #34 extends reporting. |
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
| B | #32 → #33/#34, then package validation | Validated locally: owner map/delta audit, release-profile data and boundary/contract gates. Its 72 Python and 23 Node results are separate suites, not a combined latest-run count. Final hooks and remote validation remain pending. |
| C | #15 installer ownership safeguards | Implemented and focused tests passed locally. Genuine three-wheel uv probe and mock refusal/cleanup checks are recorded below; final hooks and source-matched CI bundle roundtrip remain pending. #8 remains a separate contract; #11/#12 reproductions and #16/#25 audits are not claimed complete. |
| D | Evidence-based #14/#18–28 refinements and #35/#36 | Not started; select only demonstrated gaps. |
| E | #37 rehearsal/scorecard and justified upstream-covered retirement | Not started; needs a selected exact target and validated basis. |
| Publication | Local commits/push/Actions limits | Separate checkpoint; no new round consumed. |

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
reparse points; the complete source-matched CI bundle roundtrip remains
pending. Stop if a future actual uv layout requires unsupported reparse
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
