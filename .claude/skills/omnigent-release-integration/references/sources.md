# Release and isolation evidence index

Reviewed 2026-10-22. Local paths describe the discovered archive, not guaranteed
availability on another machine. Do not commit raw private logs or reconstruct
policy-excluded content. Use immutable code and results over stale summaries.

## Current validated baseline

| Role | Full ref |
| --- | --- |
| Validated Windows v0.19 branch | `windows-parity/v0.19-integration`, `6a7c711308587a2c39dd916c0820af71debfbb67` |
| Exact upstream v0.19.0 | `d43340fec4e7d2d767f319d715e84aa82f4d1bc8` |
| Prior Windows source | `windows-parity/v0.17-integration`, `f50a1f1cdcbc2c01499a09c8c932c9f7348b8a42` |
| Previous upstream stable/semantic base | v0.17.0, `12b5f67d2529b43eab7366a7288fb89f7587e48b` |
| Actual Git merge base for that integration | `b05888bab8527a10e34e7c61d19f01a442ce325e` |
| Original v0.14 isolation source | `ca0088b9c8e72a71b11b17d9b71898b703e56b4e` |

Both source histories are ancestors of the validated branch. The original
v0.14 editor checkout and v0.17 source are not the next integration baseline.
Main was not promoted to the Windows application.

| Result | Immutable evidence |
| --- | --- |
| Final Linux/Windows, broader suite, CLI and desktop artifacts | [39674542910](https://github.com/MusicPartner/omnigent/actions/runs/39674542910), final SHA above |
| Full remote pre-commit formatting/lint/types and version lockstep | [39674541787](https://github.com/MusicPartner/omnigent/actions/runs/39674541787), final SHA |
| Four backend E2E shards | [39661930031](https://github.com/MusicPartner/omnigent/actions/runs/39661930031), `008949b15688d19ab16213b606840935c4c65f6d` |
| Ten UI shards, Browser Contract and aggregate | [39661934560](https://github.com/MusicPartner/omnigent/actions/runs/39661934560), same earlier SHA |
| Harness integration matrix | [39661935006](https://github.com/MusicPartner/omnigent/actions/runs/39661935006), same earlier SHA |
| Docker, `publish=false` | [39661930209](https://github.com/MusicPartner/omnigent/actions/runs/39661930209), same earlier SHA |
| Source-matched CLI/desktop bundles | [CLI](https://github.com/MusicPartner/omnigent/actions/runs/39674542910/artifacts/12381398475), [desktop](https://github.com/MusicPartner/omnigent/actions/runs/39674542910/artifacts/12382976790) |

The earlier E2E/integration/Docker input closure was unchanged by later Windows
unit-fixture/documentation commits; those runs are not relabeled as final-SHA
runs. Fourteen Python and four desktop modules were compared with final source.
All three wheel versions are 0.19.0; desktop metadata is dev mode with final SHA.
Artifact retention is finite; links are provenance, not permanent availability.

## Maintained records

- [v0.19 integration snapshot](../../../../docs/windows/RELEASE-INTEGRATION-0.19.md)
  and [ledger](../../../../docs/windows/RELEASE-INTEGRATION-0.19-ledger.csv):
  317 rows, 46 bounded-review/live-acceptance notes. The snapshot preceded final
  CI completion because the user's additional push allowance was exhausted.
- [Isolation plan](../../../../docs/windows/ISOLATION-PLAN-0.19.md):
  historical mapping, contract tests/primitives first, terminal preparation
  second. This is not runtime implementation authorization.
- [Maintenance map](../../../../.github/FORK_MAINTENANCE.md) and
  [Windows documentation](../../../../docs/windows/README.md).
- Local Copilot session `f0e7a504-24b0-4fe3-b2c0-d48eb50d59fa`,
  `files/v019-integration/FINAL-RESULT.md`: completed result and human steps;
  the same directory holds raw logs and module comparison evidence.

Main automation separately became manual-only in workflow-only commit
`d8a23edf8b2e3f9531cfc70177b6a255a9415dbd`: 58 enabled definitions changed, no
application promotion. Preserve this policy on any later promotion.
Four additional push/retry rounds were used. New pushes, documentation pushes
or manual retries require renewed permission; that count is not a future cap.

## Historical isolation and replay

Resolve these paths from the repository's parent directory:

| Record | Historical purpose and limit |
| --- | --- |
| `omnigent/.github/FORK_MAINTENANCE.md` at `ca0088b9` | Original v0.14 Windows leaf/caller/test boundaries |
| `_evidence/HANDOVER-windows-parity.md` | October 8 isolation commit list, original constraints and then-open acceptance |
| `_evidence/release-port/REPLAY_PROTOCOL.md` | Original semantic replay procedure and attribution |
| `_evidence/release-port/ledger.csv`, `ledger-summary.md`, `replay/final-row-status.csv` | Original **v0.17** replay; not v0.19 evidence |
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
later replay SHAs as original v0.14 or current v0.19 validation.

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
