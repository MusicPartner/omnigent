# Release and isolation evidence index

Reviewed 2026-11-01. Local paths describe discovered evidence, not guaranteed
availability on another machine. Do not commit raw private logs or reconstruct
policy-excluded content. Use immutable code and results over stale summaries.

## Current isolation basis and implementation

Published isolation basis: `96ee061d690a26ef37f9d432a98231105fa68d9f`, branch
`windows-parity/v0.20-isolation-p3-p5`, selected `omnigent-v020-isolation` worktree.
The original extraction basis remains `e1714c416d2608f7bfd5bf4ea93ee81b108d7311`.
Use the [master roadmap](../../../../docs/windows/WINDOWS-ISOLATION-ROADMAP.md)
for the complete 1–37 inventory and implementation progress. Update its table
and chat checklist after each major step; distinguish local, published and
source-matched validation outcomes.

The [November closeout](../../../../docs/windows/ISOLATION-CLOSEOUT-2026-11-01.md)
records six successful workflows at 96ee: fork41219861480, lint41219863234,
backend41219865415, integration41219867688, UI41219869956 and Docker41219871911
(`publish=false`). These are recorded evidence, not a fresh live inspection.
The real startup trio was skipped there for absent psmux. Its post-install gate
and the auth-only DATA_DIR fix remain local; daemon/cache semantics unchanged.

Local implementation was requested on 2026-11-01. Package A preflight and focused
checks are recorded in the roadmap; no new commit/push/Actions. Counter remains
1/5 remote rounds used. The following exhausted budgets and source tables are
historical release evidence, not current authorization or isolation status.

## Historical validated v0.20 integration baseline

| Role | Full ref |
| --- | --- |
| Validated Windows v0.20 branch | `windows-parity/v0.20-integration`, `a67684ae0fc2299c8efc2e5f37824c71c8f044a6` |
| Exact upstream stable v0.20 | `bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee` |
| Prior Windows P1/P2 source | `430ea3caabec09ff894e92c0c03bfe029361418e` |
| Actual Git merge base for v0.20 | `71fb9694ecf4b54b37919fbb1acd575dfd28243f` |
| Original v0.14 isolation source | `ca0088b9c8e72a71b11b17d9b71898b703e56b4e` |

Use the validated v0.20 source, not an editor checkout that may lag at any
release. Main was not promoted to the Windows application.

| Result | Immutable evidence |
| --- | --- |
| Final fork validation, six jobs SUCCESS, exact SHA above | [41088395617](https://github.com/MusicPartner/omnigent/actions/runs/41088395617) |
| Final lint, three jobs SUCCESS, exact SHA above | [41088396527](https://github.com/MusicPartner/omnigent/actions/runs/41088396527) |
| Both-OS baseline candidate | 37 nodes; zero errors, failures or skips; identical nodes |
| Broader Windows suite | 4,552 actual / 4,576 suite-attributed including subtests; 0 failures, 0 errors, 233 skips |
| Source-matched CLI / desktop artifacts | [CLI 12993698944](https://github.com/MusicPartner/omnigent/actions/runs/41088395617/artifacts/12993698944), [desktop 12995030094](https://github.com/MusicPartner/omnigent/actions/runs/41088395617/artifacts/12995030094); same fork run, dev/unsigned, `release_approved=false` |
| UI, backend E2E, integration matrix | [41078697033](https://github.com/MusicPartner/omnigent/actions/runs/41078697033), [41078798047](https://github.com/MusicPartner/omnigent/actions/runs/41078798047), [41078793722](https://github.com/MusicPartner/omnigent/actions/runs/41078793722); all PASS at `dfcf012803e7045cd25b29bee60f6184c9fac482`, unchanged input closure only—not final-SHA runs |
| Docker, `publish=false` | [41067511450](https://github.com/MusicPartner/omnigent/actions/runs/41067511450), at `9ba784ca2fd4eb44a8033cc3be07ffb12a5a869c`; unchanged runtime closure, not final-SHA evidence |

These are source-matched results only as labeled; earlier workflow runs are
not relabeled as final-SHA runs. Artifact retention is finite; links are
provenance, not permanent availability.

The v0.20 six-round push/retry allowance is exhausted. This is not a generic
future cap; any additional integration push or retry needs renewed permission.
Human acceptance, vendor-sandbox checks, migration acceptance and signing
remain outstanding. The release artifacts are dev/unsigned and not approved.

The v0.20 ledger has 328 rows: 282 pending, 45 review-pending and one excluded.
Its 46 `REVIEW` paths remain unresolved; automated success does not clear them.
The maintained isolation plan is `docs/windows/ISOLATION-PLAN-0.20.md`; use it for the
staged work and authorization boundary; this evidence index is not
implementation authorization.

## Maintained records

- [v0.20 isolation plan](../../../../docs/windows/ISOLATION-PLAN-0.20.md)
  (staged work and authorization boundary).
- [v0.20 integration snapshot](../../../../docs/windows/RELEASE-INTEGRATION-0.20.md)
  and [ledger](../../../../docs/windows/RELEASE-INTEGRATION-0.20-ledger.csv).
- Local final evidence: `D:\Develop\Source\OpenSource\_AI\Omnigent\_evidence\v020-integration-20261030\FINAL-VALIDATION.md`.
- [Maintenance map](../../../../.github/FORK_MAINTENANCE.md) and
  [Windows documentation](../../../../docs/windows/README.md).

## Historical v0.19 integration

The v0.19 record is preserved as historical evidence, not as the current
baseline:

| Historical role | Full ref / evidence |
| --- | --- |
| Validated v0.19 integration | `6a7c711308587a2c39dd916c0820af71debfbb67`, branch `windows-parity/v0.19-integration` |
| Exact upstream v0.19.0 | `d43340fec4e7d2d767f319d715e84aa82f4d1bc8` |
| Prior Windows v0.17 source | `f50a1f1cdcbc2c01499a09c8c932c9f7348b8a42` |
| Actual v0.19 merge base | `b05888bab8527a10e34e7c61d19f01a442ce325e` |
| Final fork / lint at v0.19 SHA | [39674542910](https://github.com/MusicPartner/omnigent/actions/runs/39674542910) / [39674541787](https://github.com/MusicPartner/omnigent/actions/runs/39674541787) |

- [v0.19 integration snapshot](../../../../docs/windows/RELEASE-INTEGRATION-0.19.md)
  and [ledger](../../../../docs/windows/RELEASE-INTEGRATION-0.19-ledger.csv):
  317 rows, 46 bounded-review/live-acceptance notes. The snapshot preceded final
  CI completion because the user's additional push allowance was exhausted.
- [Isolation plan](../../../../docs/windows/ISOLATION-PLAN-0.19.md):
  historical mapping, contract tests/primitives first, terminal preparation
  second. This is not runtime implementation authorization.
- Local Copilot session `f0e7a504-24b0-4fe3-b2c0-d48eb50d59fa`,
  `files/v019-integration/FINAL-RESULT.md`: completed result and human steps;
  the same directory holds raw logs and module comparison evidence.

Main automation separately became manual-only in workflow-only commit
`d8a23edf8b2e3f9531cfc70177b6a255a9415dbd`: 58 enabled definitions changed, no
application promotion. Preserve this policy on any later promotion.
The v0.19 allowance was four additional push/retry rounds. That historical
count is not a future cap; see the current v0.20 allowance above.

## Historical isolation and replay

Resolve these paths from the repository's parent directory:

| Record | Historical purpose and limit |
| --- | --- |
| `omnigent/.github/FORK_MAINTENANCE.md` at `ca0088b9` | Original v0.14 Windows leaf/caller/test boundaries |
| `_evidence/HANDOVER-windows-parity.md` | October 8 isolation commit list, original constraints and then-open acceptance |
| `_evidence/release-port/REPLAY_PROTOCOL.md` | Original semantic replay procedure and attribution |
| `_evidence/release-port/ledger.csv`, `ledger-summary.md`, `replay/final-row-status.csv` | Original **v0.17** replay; not v0.19 or v0.20 evidence |
| `omnigent-v017/docs/windows/BROADER-WINDOWS-SUITE-HANDOVER-2026-10-09.md` | Task-specific broad-suite continuation |
| `omnigent-v017/docs/windows/BROADER-TEST-FINDINGS-2026-10-09.md`, `BROADER-WINDOWS-SKIPS-2026-10-09.md` | Historical failures, final counts, platform versus fixture distinctions |
| `omnigent-v017/docs/windows/PARITY-NEXT-STEPS.md` | Later launch/hook/shutdown/attachment outcomes; reconcile against newer code |
| `omnigent-v017/docs/windows/UPSTREAM-DIRECTION-2026-10-09.md` | Dated merged contracts versus proposals |

The original ledger's 201 files and 189-completed/nine-dropped/three-deferred
counts are dated v0.17 history, not the next release's expected disposition.
Earlier Windows CI at `e6a14a5e9dad093bebdf16809b70d22e9dccd61b` passed its
required broader gate; it did not validate later source `f50a1f1cd`. Passing
runs do not establish the root cause of earlier native Python crashes.

Original v0.14 extraction history includes psmux leaf `d28450b89`,
paths/breadcrumbs `3c460fb34`, host listing/probe `83bb2d870`, splitting
`e8b442a7a`, Codex resolution `5a09bf943`, Claude hooks `6057704ce` and
shutdown/native-env `a68442657`, indexed in the handover. Parent-environment,
tracing and readiness/transport extensions are later contracts. Do not present
later replay SHAs as original v0.14 or current-release validation.

## Deeper history only when needed

Codex: `%USERPROFILE%\.codex\session_index.jsonl` and matching
`sessions\YYYY\MM\DD\rollout-*.jsonl`. Distinguish root/worker cwd and inspect
only relevant user turns and results. Early recovered prompts in
`%LOCALAPPDATA%\Temp\session-history-investigation-2026-10-08` are partial.
Relevant root IDs include `01a11b2a-e159-7e22-9f35-3951429d18da`,
`01a11c8e-4ebc-73b2-bfc2-9111410b8d8a`,
`01a11cb5-b555-7823-9053-a720537ae293`,
`01a1200d-82bd-7c20-bbec-7286a7cf9f9a` and
`01a1220a-66bf-7ca0-b29f-c954cd4a6a4d`.

Copilot: discover the relevant `%APPDATA%\Code\User\workspaceStorage`
workspace/profile and its chat logs read-only. Observed source workspace key
`ee4d992436f7ec12c60b4f31f2321b55`; relevant session IDs include
`2d5db604-1b85-48bf-a373-e0ca4e495cb6`,
`1afb1610-b9f3-4ef8-971c-fc8399a74126` and
`8f0e80bc-d383-4559-a050-800e30e83acb`.
The Code globalStorage Copilot session store contained related turns; the
separate user-level CLI store did not provide equivalent history when inspected.

These indexes are targeted, not exhaustive access claims. Memory notes and
recovered summaries may be stale. Do not modify logs/databases, read unrelated
conversations, retry denied resources or reuse historical one-time permissions.
