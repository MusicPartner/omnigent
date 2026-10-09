# Native Windows private-job launcher: candidate and release plan

Date: 2026-10-09. Base: `bfa24bfee64acbef8b150999bdfb5fee46792010` on `windows-parity/v0.17-integration`.

## Completed prototype milestone

The first milestone built an isolated x64 launcher to test the filename-only
Windows launch seam. It accepted per-launch configuration, created the Python
child in a private kill-on-close Job Object, forwarded standard streams, and
returned the child exit code. That milestone was deliberately test-only and
did not replace `create_exec_launcher` or change runtime packaging. Its results
apply to that prototype and the tested native Windows x64 environment only.

The historical prototype code and tests remain useful evidence. The current
candidate implementation and its release gates are recorded below.

## Prototype verification scope

The prototype suite covered:

- Repeatable local x64 builds, identified compiler/SDK versions, invalid configuration and process/job creation failures.
- Exact argv delivery for quotes, percent signs, shell metacharacters, Unicode, spaces in interpreter and working directory, and empty arguments.
- stdin/stdout/stderr forwarding and the child's exit code.
- Assignment to the private job at process creation, before child execution, without inheriting the private job handle.
- Normal completion, forced launcher termination, and cleanup of a child plus a deliberately spawned grandchild.
- Inactive/no-policy behavior, nested/inherited jobs, startup cleanup, SDK cancellation, and SDK version probes.
- Parent death with and without an outer kill-on-close job.

These results are prototype evidence only. A private Job Object does not
provide filesystem or network isolation.

## SDK transport audit and practical check

The installed `.venv` contains `claude_agent_sdk` 0.2.94 with bundled CLI 2.1.169. Its default subprocess transport accepts a command list, but its selected CLI path is a filename: it starts `[cli_path, ...]` with `anyio.open_process`. `close()` closes stdin, waits up to five seconds, terminates the direct process, waits another five seconds, then kills and waits; its atexit handler only sends SIGTERM to the tracked direct process. The version probe separately starts `[cli_path, "-v"]` under a two-second timeout, then terminates/waits and suppresses probe errors. These SDK paths do not establish process-tree cleanup for a filename-only launcher.

The tests instrumented both SDK call shapes: streamed launch followed by
cancellation/close, and the short `-v` probe including timeout. They recorded
launcher and child/grandchild PIDs and required bounded cleanup. Abrupt parent
exit was tested independently because an atexit signal does not cover every
termination.

## Prototype evidence on 2026-10-09

The opt-in native suite finished with **18 passed** on Windows x64 using MSVC
14.51.36231 and Windows SDK 10.0.26100.0. Its first run had 17 passed and one
failure because the parent-death assertion included a virtualenv redirector
among the host descendants it expected to survive. The test now records the
actual caller PID and its known stub subtree; the rerun passed. It also captures
the suspended child used by the resume-failure cleanup check.

The related launcher/sandbox regression command finished with **27 passed, 3
POSIX skips**. The full scoped pre-commit run and final docs-only rerun passed with
`PYTHONUTF8=1` and Git Bash/Node v24.21.0 available to hooks. The native
suite command is recorded in [PARITY-NEXT-STEPS.md](PARITY-NEXT-STEPS.md#next-launcher-decision).
No remote CI workflow was dispatched for this prototype.
These results do not establish production readiness.

## Production candidate implemented; release remains gated

The candidate preserves the legacy launcher as the default and adds a lazy
selector at the shared `create_exec_launcher` seam. `native` requires a
release-approved signed artifact; `native-dev` explicitly opts into the
unsigned development/test artifact. Both modes use the same asset hash,
architecture, config-security, and process-lifecycle checks. Existing
caller-specific argument construction and POSIX launch behavior remain
unchanged. No signed release artifact or approved signing identity has been
provided, so `native` currently fails closed.

The config transport stores the existing `OJLCFG01` payload in the
launcher copy's `:omnigent.config` NTFS alternate data stream (ADS). Each
invocation already receives its own executable copy, so the stream can carry
that invocation's config while the PE image bytes remain identical. Removing
the executable also removes the stream. Invocation files use a persistent
per-user Windows profile container. The runtime validates the container and
its ancestors for reparse points and cross-user mutation rights, rejecting
unsafe paths that could let another account replace the container. The
container may allow additional read/traverse access; the executable and ADS
retain a protected DACL limited to the current user and SYSTEM. The native
side keeps both file handles open with sharing that prevents replacement,
checks that the ADS belongs to the same file, and rejects unsupported file
types. It fails closed when ADS or those checks are unavailable. This does not
claim isolation from malicious code running as the same user or an
administrator.

ADS is a practical config transport, not a portable filesystem feature.
The candidate requires local NTFS and tests that copying and cleanup preserve
the intended behavior. Some archive, synchronization, and non-NTFS paths may
drop streams. It does not silently fall back to a sibling config file or
launch without policy.

For active policies, the launcher watches its immediate parent process and
creates the Python child suspended with the private job assigned atomically
before resuming it. It rechecks parent liveness around child creation and
resume, then closes the private job on parent death or launcher shutdown.
Nested host jobs and SDK cancellation/version-probe behavior are covered by
opt-in tests. This remains process-lifecycle containment only; it does not
provide filesystem or network isolation or brokered-signer support.

Packaging keeps `setup.py` unchanged. `dev/windows_launcher/package.py`
prepares the asset before wheel or sdist creation; a resource package and one
`pyproject.toml` package-data entry include the prepared executable and
manifest in both. `MANIFEST.in` adds only the native source/build helpers to
the sdist. A universal wheel carries the optional Windows x64 data asset while
POSIX runtime behavior stays unchanged. Generated executables and manifests
remain ignored. A clean sdist-to-wheel build and isolated install/import smoke
completed successfully, including the native candidate resource and its exact
SHA-256.

The pinned candidate build used MSVC 14.44.35207 and Windows SDK 10.0.26100.0.
Independent output comparison passed. Its unsigned executable SHA-256 is
`3d2564228c78a637c5c47bc350937cb2474e61ca6a855b272e0191cac6984c03`.
The separate prototype suite used MSVC 14.51.36231 and the same SDK version.
Code signing and the approved signer identity, antivirus/SmartScreen behavior
on a clean machine, remote CI evidence, and the release-default decision remain
open. Current credential refusals and POSIX behavior remain unchanged.

### Candidate validation recorded so far

The opt-in native prototype suite passed **18 tests**. The candidate's native
process suite passed **21 tests**. A separate rerun exposed a readiness-file
read race in the test helper; the transient `PermissionError` was not a native
launch or containment assertion. A bounded read retry fixed the test helper,
and the nested-job plus permanent-read-failure cases passed together in three
separate runs. No production code changed for that fix. The runtime suite
passed **24 tests with 1 symlink-rejection skip** without Windows Developer
Mode or symbolic-link privilege; it includes the positive signer check.
**41 packaging checks passed** after adding embedded-signature validation. The
shared launcher/capability regression subset passed **17 tests with 3 POSIX
skips**, and the actual psmux/native-launcher lifecycle test passed (**1
passed**). The installed-wheel smoke ran with `python -I` and
`--require-installed`;
it exercised an active native-dev launch, exact arguments, stdin/stdout,
working directory, exit code 37, executable/ADS cleanup, and refusal of the
unsigned asset by strict `native` mode. The installed wheel also passed CLI
version and server import checks. The signer test accepted an installed
Microsoft embedded Authenticode signature with the matching thumbprint,
rejected a wrong thumbprint, and refused a catalog-only signature. That test
proves the verification path; it does not establish the organization's
production signing identity.

The unchanged scoped pre-commit run passed its other 14 applicable hooks;
Windows Pyrefly still reports 156 existing errors outside the launcher leaf.
The launcher adds no Windows typing errors, and the full canonical Linux
type-check reports zero errors. Final docs/test-only hooks passed.

No remote CI workflow has been dispatched for the candidate. These results
establish local Windows x64 behavior and packaging only; they do not establish
a signed release, clean-machine SmartScreen/reputation behavior, ARM64 or x86
support, or filesystem/network isolation.

### Upgrade and verification touchpoints

The candidate touches the shared launcher selector and runtime helper
(`omnigent/inner/sandbox.py`, `omnigent/inner/windows_exec_launcher.py`), native
source/build/package/smoke tooling (`dev/windows_launcher/build.py`,
`package.py`, `smoke.py`, `private_job_launcher.c`), the optional resource
package and packaging declarations (`omnigent/resources/windows_launcher/`,
`pyproject.toml`, `MANIFEST.in`, `.gitignore`), launcher and packaging checks
(`tests/inner/test_sandbox.py`,
`tests/inner/test_windows_exec_launcher_runtime.py`,
`tests/inner/test_windows_private_job_launcher.py`,
`tests/inner/windows_private_job_launcher.py`,
`tests/scripts/test_windows_launcher_packaging.py`,
`tests/terminals/test_windows_native_launcher_psmux.py`), and
`.github/workflows/fork-release-ci.yml`. POSIX launch code and callers keep
their current contracts.

On native Windows x64 with Visual Studio C++ tools, Windows SDK, and psmux
installed, run the opt-in lifecycle checks from PowerShell:

```powershell
$env:OMNIGENT_TEST_PRIVATE_JOB_LAUNCHER = "1"
uv run pytest tests/inner/test_windows_private_job_launcher.py tests/inner/test_windows_exec_launcher_runtime.py tests/terminals/test_windows_native_launcher_psmux.py -q -n 0 -p no:cacheprovider
```

For the installed-wheel check, build the wheel with the pinned native toolchain
and install it into a fresh environment. From the checkout, invoke the smoke
script with that environment's interpreter:
`<fresh-venv>\Scripts\python.exe -I dev/windows_launcher/smoke.py --require-installed`.
The script verifies that Omnigent imports from the installed environment.
Keep the `native-dev` selector explicit for unsigned artifacts. Do not enable
or distribute `native` until maintainers provide the approved signing identity,
the signed artifact is verified, and clean-machine reputation checks plus
remote CI have passed.

## Remaining release gates

The local candidate is integrated, but release adoption remains gated on:

1. Confirm the release signing policy and approved signer identity, then produce and verify a signed artifact. The current unsigned manifest must continue to fail closed in strict `native` mode.
2. Run the release workflow against the candidate and retain its Windows results.
3. Verify AV/SmartScreen reputation on a clean supported Windows machine and document the release-default/rollback plan.
4. Keep x64 support explicit; add separate architecture runtime evidence before claiming x86 or ARM64 support.
5. Preserve current credential refusals and sandbox boundaries. A Job Object provides process lifecycle containment, not filesystem/network isolation or brokered-signer support.

Until these gates pass, do not claim a signed production asset or production
adoption. Update the parity decision/outcome only with observed results and
limitations; do not convert design intent into a production guarantee.
