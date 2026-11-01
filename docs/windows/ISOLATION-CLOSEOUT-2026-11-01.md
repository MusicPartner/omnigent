# Isolation closeout and next checkpoint, 2026-11-01

## Current documentation checkpoint — local, source matched to working tree

The authoritative worktree was reverified at local HEAD and live origin
`96ee061d690a26ef37f9d432a98231105fa68d9f` on
`windows-parity/v0.20-isolation-p3-p5`. Existing edits were preserved. Packages
A/B are validated locally; item 15 in package C is implemented and its focused
tests and genuine three-wheel uv probe passed. Final hooks and a source-matched
CI bundle roundtrip remain pending. No new result SHA is claimed. One coordinated
B/C checkpoint push and Actions batch is authorized as existing round 2/5, but
was not performed here. The selected push plan excludes local #13 Electron files
and the #8 safe-launcher test unless explicitly added, and excludes web files
because of the pre-existing whole-web standard Prettier finding.

The item 15 helper is `scripts/windows_bundle_state.ps1`, shared by
`install_windows_bundle.ps1` and `uninstall_windows_bundle.ps1`; new assembled
bundles include it. `scripts/install_oss.ps1` is unchanged and outside this fix.
It refuses nonempty receipt-free prefixes rather than adopting old installs,
and refuses unexpected contents. A partial fresh install that fails before
receipt creation is left for manual review; use a fresh prefix rather than
automatic cleanup. UV failure preserves receipt and PATH but does not
transactionally roll back uv's internal changes. Receipts guard accidental
collisions, not hostile writers or races. Historical artifact `96ee` predates
the helper; these safeguards must not be attributed to it.

Separate local results: **82 tests** across ownership helper, installer callers
and release tooling; **9 uninstaller tests**; **7 installer-caller tests**.
These are not a single combined latest run. A genuine runner-temp three-wheel
uv probe inventoried **1,799 entries without detected reparse points**; receipt
replacement/state checks, unexpected-sentinel refusal, uv uninstall and
nonrecursive cleanup passed. Dependencies were excluded and this was not an
application smoke test. For a human check, follow the disposable
`-NoPath -SkipPsmux` install/reinstall/sentinel-refusal/known-sentinel removal/
uninstall procedure in [QUICKSTART](QUICKSTART.md), using only a future
helper-equipped source-matched bundle in a disposable Windows account or VM.
`-NoPath` prevents adding the install path, but uninstall still writes a
filtered User PATH value; the procedure checks that the value is unchanged,
not that the setter was avoided.

## Exact source and completed package

Validated candidate: `96ee061d690a26ef37f9d432a98231105fa68d9f` on
`windows-parity/v0.20-isolation-p3-p5`, in `omnigent-v020-isolation`.
Local HEAD and live origin matched; preflight working tree was clean.
The original package basis remains `e1714c416d2608f7bfd5bf4ea93ee81b108d7311`.
The release checkout, old editor checkout and backup were not changed.

| Original item | Outcome | Remaining boundary |
| --- | --- | --- |
| 1: source/owners/ledger | Closeout refreshed here and in maintenance/package indexes | Semantic REVIEW and human acceptance stay open |
| 2: Claude OSC audit | Actual Windows failure reproduced; separately approved relay/liveness R published | No ConPTY or authenticated vendor UX claim |
| 3: mux dialect audit | Private psmux 3.4.0 chained capture succeeded | Placeholder exit fields cannot certify child success |
| 4–6: release tooling | Implemented/published with independent fixtures and preserved workflow policy | Qualified duplicate AST owners are possible later hardening, not a proven missing contract |
| 7, 9, 10: paths/Pi/popup | Implemented/published with facade and injection contracts retained | No UNC or vendor behavior change |
| 8: batch launcher | Separate actual characterization completed below | Extraction/support decision remains separate |

## Source-matched remote evidence

Read-only `gh` verification confirmed every run below completed successfully
at the full candidate SHA. No workflow was rerun during closeout.

| Workflow | Run | Result |
| --- | --- | --- |
| Fork release validation | [41219861480](https://github.com/MusicPartner/omnigent/actions/runs/41219861480) | Six jobs successful |
| Lint | [41219863234](https://github.com/MusicPartner/omnigent/actions/runs/41219863234) | Three jobs successful |
| Backend E2E | [41219865415](https://github.com/MusicPartner/omnigent/actions/runs/41219865415) | Eight shards: 936 passed, 187 skipped, 2 xfailed |
| Integration | [41219867688](https://github.com/MusicPartner/omnigent/actions/runs/41219867688) | 21 passed, 57.11 seconds |
| E2E UI | [41219869956](https://github.com/MusicPartner/omnigent/actions/runs/41219869956) | Shards, Browser Contract and aggregate successful |
| Docker | [41219871911](https://github.com/MusicPartner/omnigent/actions/runs/41219871911) | Build/smoke successful; publication disabled |

Downloaded JUnit, not only job conclusions, establishes:

- Both OSes: 37 baseline and 37 candidate nodes; node files identical;
  zero failures/errors/skips. Buffer-routing gates: 90 executed per OS.
- Blocking broader Windows: 4,556 actual testcase records, 4,580
  suite-attributed tests including subtests; zero failures/errors, 233 skips.
- Relay gate: 12 records per OS, nine executed and three skipped. The actual
  default/enabled/disabled startup cases said **psmux not installed** in both
  jobs. The later native job installed psmux but did not select these cases.
  Earlier green remote status therefore does not certify this real startup trio.

The closeout adds an explicit blocking native gate after the existing psmux
installation, with a source-labelled JUnit upload and a requirement for three
executed cases without skips. This is a validation-reachability correction,
not runtime behavior or workflow trigger/permission/publication policy change.
Local serial checks passed all three real startup cases. New working-tree
checks are not relabelled as remote `96ee` results.

Initial closeout owning suites: **45 passed, five POSIX/Linux-only skips**;
release-input/argv Node contracts: **12 passed**. Ruff lint/format and final
parsing of all **95 workflow definitions** passed at that checkpoint. No broad new skips,
runtime edits, dependency/version/lock changes or trigger changes were made.
Initial scoped pre-commit hooks passed after the line-ending hook normalized
two files; Pyrefly/web hooks had no applicable changed production files.

### Artifact acceptance

External inspection verified three 0.20.0 wheels, bundle checksums, embedded
native-resource digest, and packaged Pi/popup/terminal/status module content
against the selected candidate (normalizing checkout CRLF only).
The existing build job also completed clean-wheel and disposable artifact
install/uninstall checks; its log records removal of the runner-temp install.

The downloaded desktop ASAR contains version `0.20.0`, exact source `96ee`,
and build mode `dev`. Desktop ZIP SHA256:
`a9be3a36ae4c9051a1f94b67c8fb7e916abc5da65e46b7d0bb7b661ef24b88a1`.
The native resource remains `release_approved=false`. These are development
artifacts, not a signed/approved production distribution. GUI launch, vendor
credentials, real migration, signing/update and vendor-sandbox reads remain
unperformed; no real installation or user state was modified locally.

### Reachability and semantic limits

`ci.yml`, `web-tests.yml` and `windows.yml` have no dispatch interface on this
source. This maintenance branch is not eligible for fork automatic push;
its explicit dispatch remains available. Snapshot update is not a neutral
validation operation. No triggers, schedules or branch eligibility were added.
The fork Windows sweep is blocking; the separate upstream broader Windows
sweep is nonblocking and cannot replace it.

The original ledger remains 328 rows: 282 pending, 45 review-pending,
one excluded. Its 46 REVIEW paths are not automatically cleared by Actions.
This package's current ownership/result map supplements rather than rewrites
those historical dispositions. Further substantive review needs topic evidence.

## Item 8: actual batch characterization

The unchanged `create_exec_launcher(...)->str` default Windows `.cmd` was
executed via literal `subprocess.run([...])` with an owned Python argv recorder,
inactive policy and disposable HOME/USERPROFILE/config/data and launcher paths.
Two launcher directories (plain and spaces/Unicode) each exercised eight cases.

| Input | Observed result in both directories |
| --- | --- |
| Plain, spaces/empty, Unicode, bang, quotes/JSON, trailing backslash | Exact argv; child exit 37 propagated |
| `%OMNI_PROBE_VALUE%` | Expanded to seeded `expanded-value`; exit 37 but argv changed |
| `a&b` | Recorder received `a`; cmd attempted a second command `b`; wrapper exit 1 |
| Batch bytes | Literal CRLF, without doubled carriage returns |

No supplied second command was dangerous: `b` was absent in the private cwd.
This proves batch argument interpretation on the actual filename-consumer
path, not a complete vendor CLI exploit or hardened sandbox capability.
Delayed expansion inherited from other cmd consumers, interpreter-path
variants and all shell/caller variants remain outside this finite matrix.
The `%*`/executable-filename API, native/native-dev selectors, signing gates
and shared sandbox policy are unchanged. A permanent owning-layer safe-argv/
CRLF test supplements the external failure reproducer; failing inputs are not
converted into weakened expected behavior or a blanket xfail.

## Next contract decisions

1. Decide item 8 support/reconciliation before neutral extraction. Plain
   extraction would preserve the reproduced percent/ampersand defects.
   Do not silently replace the filename API or enable native-dev by default.
2. Item 13: target **authentication tokens**, not token-usage telemetry.
   The separately approved auth-only alignment is implemented locally below;
   daemon/cache/migration semantics still need a separate decision.
   An external synthetic-filesystem probe confirmed both desktop auth readers
   originally missed a token present only under DATA_DIR; Python auth and SDK path producers
   resolve that override. No real credentials/files or network were accessed.
   The pre-fix probe stubbed the unused YAML dependency before installing the
   locked Electron dependencies; it is not full desktop execution evidence.
3. Item 15: disposable characterization is complete below; decide ownership,
   root/reparse refusals and tool-environment restoration before deletion fixes.
   Never exercise recursive uninstall on a real installation or foreign prefix.
4. Items 11/12 need runtime reproductions before implementation; 14/16 follow.
   ConPTY, hardened sandboxing and production distribution remain separate.

## Limits and verification

### Approved auth-only continuation and installer characterization

The user selected **auth-only fix plus installer safety characterization**.
Both desktop auth readers now reuse existing `localDataDir()` for the token
file. `stateDir()` and daemon-registry paths remain unchanged. Five focused
scenarios cover overrides/conflicting home tokens, no legacy fallback,
home/expiry/Databricks pointers, tilde/relative paths and environment-token
refusal. Desktop CLI and server-manager suites passed **62 tests**.
The full suite first exposed two pre-existing POSIX-separator assumptions;
executing the published baseline test text reproduced both. Assertions now
use platform path joining, retaining the same discovery/order guarantees.
The existing two-OS desktop test steps also include the auth suite.

An external item 15 probe executed the real uninstaller's parsed statement
body only against its own newly created disposable prefix. Registry access
was replaced with an in-memory environment class; uv lookup returned absent.
It removed an unrelated synthetic file inside the supplied prefix without
an ownership receipt, preserved a sibling sentinel, and tolerated repeated
uninstall of the missing prefix. Real user PATH and tool environment remained
unchanged. No root, foreign prefix, reparse path or real installation was
passed to deletion. Ownership/root/reparse refusals remain a separate fix
decision; this finite probe does not establish safe general uninstall.

Existing locked desktop/web dependencies were prepared without install
scripts or manifest/lock changes. A production-only install removed local
development tool links; the subsequent frozen development install restored
them. No Electron runtime launch or dependency-version upgrade was performed.
External item 15 evidence is `uninstaller-safety-probe.ps1` and
`uninstaller-safety-result.json` in the same evidence directory.

Final local validation of this follow-up:

- Python tooling/installer/sandbox and serial real startup trio: **68 passed,
  five POSIX/Linux-only skips**, retries disabled, 30.81 seconds.
- Desktop auth/manager/shutdown and release-input/argv Node suites:
  **85 passed**, zero failures or skips, repeated after hooks.
- All **95** final workflow YAML files parsed with the installed locked
  `js-yaml`; both desktop commands retain one folded command. A transient
  extra indentation was caught by the immutable preservation test and fixed.
- Normal scoped pre-commit, Ruff, custom lint, oxlint, TypeScript and editor
  diagnostics passed. The new test's dynamic environment deletion was replaced
  with explicit static keys to satisfy the existing lint rule, not suppressed.
- Required standard whole-web Prettier check still exits **1** on 1,469
  checkout files. The CRLF-aware `--end-of-line auto` comparison exits **0**;
  changed-file formatting passes. No whole-tree rewrite or gate bypass.

The earlier final-YAML invocation used a nonexistent direct `web/yaml` import;
it did not parse anything. The successful check above resolves the existing
Electron dependency instead, with no additional dependency changes. JUnit is
`followup-final.xml`; formatter outputs are `followup-prettier-standard.txt`
and `followup-prettier-auto.txt` in the external evidence directory.

User authorized starting the recommended sequence on 2026-11-01. Closeout
and characterization do not authorize changing signing, sandbox security,
launcher API or shared lifecycle policy. Remote budget is **1/5 used, four
remaining**. No push/dispatch was performed for this checkpoint; local changes
and external evidence are not a published candidate. A subsequent coordinated
publication/validation batch consumes round 2, including documentation pushes.

Raw evidence and executable reproducer:
`D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-isolation-next-20261031`
(`closeout-probe.py`, `closeout-probe-result.json`, `closeout-focused.xml`,
`closeout-final.xml`, `auth-state-probe.cjs`).
The first probe attempt used the wrong checksum parent; its verification code
was corrected to the wheel directory, not expected artifact hashes.

To verify locally, use this checkout's interpreter and serial, retry-disabled
pytest selection for `tests/scripts/test_fork_release_tooling.py`,
`tests/scripts/test_install_windows_bundle_ps1.py`,
`tests/inner/test_sandbox.py::test_exec_launcher_windows_cmd_preserves_safe_argv_and_crlf`
and `tests/terminals/test_windows_psmux.py::test_windows_claude_role_launch_uses_supported_status_fallback`.
Run `node --test web/electron/test/omnigent_cli.test.js` from the selected root
for synthetic auth fixtures; no login, real tokens or network credentials are
required. The five auth cases verify override-only reading, no legacy fallback,
existing expiry/pointer/refusal behavior and the unchanged home daemon path.
For human acceptance, launch the identified development artifact with fresh
state; check spaces/Unicode workspaces, two-pane targeted paste and popup
dismissal. Authenticated Claude startup/status remains a separately authorized
manual check, not something the credential-free recorder establishes.
