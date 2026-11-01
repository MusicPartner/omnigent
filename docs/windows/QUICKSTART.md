# Windows quickstart

## Install

1. In GitHub, open **Actions -> Fork release validation** and choose the
   successful run for the exact Windows integration branch/source you intend
   to install. Verify the run's full commit SHA before downloading. An older
   branch's artifact is not evidence for the current source; `main` is not
   necessarily the Windows integration.
2. Download the `omnigent-windows-<commit-sha>` artifact and extract the ZIP.
3. Double-click `INSTALL.cmd`, or run this from PowerShell in the extracted folder:

   ```powershell
   .\install.ps1
   ```

4. Open a **new PowerShell** and verify the installed CLI:

   ```powershell
   omni --version
   omni --help
   Get-Command omni
   ```

The default install directory is:

```text
%LOCALAPPDATA%\Programs\Omnigent
```

The real wheel-generated executables are installed under:

```text
%LOCALAPPDATA%\Programs\Omnigent\bin\omni.exe
%LOCALAPPDATA%\Programs\Omnigent\bin\omnigent.exe
```

The installer also attempts to install `psmux`, which is required for native managed terminal sessions.

The published `96ee061d690a26ef37f9d432a98231105fa68d9f` artifact predates
the bundle ownership helper. Do not treat it, or any other historical bundle
without `windows_bundle_state.ps1`, as providing the safeguards below. A future
source-matched run is required to validate the helper-equipped bundle.

## Upgrade

Download the newer successful `omnigent-windows-<commit-sha>` artifact, extract it to a new folder, and run `INSTALL.cmd` again.

The installer uses `uv tool install --force` with the exact three wheels in
that bundle. With a helper-equipped bundle, in-place upgrade is supported only
for a fresh or coherently receipted prefix with no unexpected files; a
nonempty receipt-free legacy prefix is refused, not adopted automatically.
New helper-equipped bundles record the files they own. This is an
accidental-collision safeguard, not protection against a malicious concurrent
filesystem writer. Choose a fresh prefix or review a receipt-free old
installation manually. Do not infer these safeguards for historical artifacts:
the artifact from `96ee061d690a26ef37f9d432a98231105fa68d9f` predates the shared
bundle helper and does not contain it.

Verify the upgraded version:

```powershell
omni --version
```

For a valid receipted install, you do **not** need to uninstall before
upgrading. A nonempty receipt-free legacy prefix is refused; choose a fresh
prefix or review the old installation manually instead.

### Disposable installer check

Use only a future source-matched bundle that contains `windows_bundle_state.ps1`;
the historical `96ee` artifact is not that bundle. In an extracted helper-equipped
bundle, run the following in PowerShell. It uses a fresh directory beneath the
temporary folder, skips PATH changes and psmux installation, and removes only
the sentinel it creates. Run this only under a disposable Windows account or
VM: `-NoPath` prevents the installer from adding the prefix to User PATH, but
the current uninstaller still writes the filtered User PATH value when it
removes the prefix entry, even if none was present. The check below verifies
that the resulting value is unchanged; it does not prevent that environment
write.

```powershell
$ErrorActionPreference = 'Stop'
$prefix = Join-Path $env:TEMP ("omnigent-bundle-check-" + [guid]::NewGuid().ToString('N'))
$pathBefore = [Environment]::GetEnvironmentVariable('Path', 'User')
$uvNames = @('UV_TOOL_DIR', 'UV_TOOL_BIN_DIR', 'UV_SYSTEM_CERTS')
$uvBefore = @{}
foreach ($name in $uvNames) {
   $uvBefore[$name] = @{
      Present = Test-Path "Env:$name"
      Value = [Environment]::GetEnvironmentVariable($name, 'Process')
   }
}

& .\install.ps1 -InstallDir $prefix -NoPath -SkipPsmux
if (-not (Test-Path (Join-Path $prefix '.omnigent-bundle-receipt.json'))) {
   throw 'The fresh install did not write its ownership receipt.'
}
& .\install.ps1 -InstallDir $prefix -NoPath -SkipPsmux

$sentinel = Join-Path $prefix 'review-me.txt'
Set-Content -LiteralPath $sentinel -Value 'unrelated test content'
$refused = $false
try {
   & .\install.ps1 -InstallDir $prefix -NoPath -SkipPsmux
} catch {
   $refused = $_.Exception.Message -match 'Unexpected item'
}
if (-not $refused -or -not (Test-Path -LiteralPath $sentinel)) {
   throw 'Upgrade did not refuse and preserve the unexpected sentinel.'
}
Remove-Item -LiteralPath $sentinel

& .\uninstall.ps1 -InstallDir $prefix
if (Test-Path -LiteralPath $prefix) { throw 'The owned disposable prefix remains.' }
if ([Environment]::GetEnvironmentVariable('Path', 'User') -ne $pathBefore) {
   throw 'User PATH changed during the -NoPath check.'
}
foreach ($name in $uvNames) {
   $present = Test-Path "Env:$name"
   $value = [Environment]::GetEnvironmentVariable($name, 'Process')
   if ($present -ne $uvBefore[$name].Present -or $value -ne $uvBefore[$name].Value) {
      throw "$name was not restored to its prior process value."
   }
}
```

This verifies the local-user safeguards on a disposable prefix only. It is not
a hostile-writer/race-safety test or a substitute for the pending source-matched
CI bundle roundtrip.

## Connect locally

Open PowerShell window 1:

```powershell
omni server
```

Keep it running. Then open PowerShell window 2:

```powershell
omni host --server http://localhost:6767
```

This connects a local host/runner to the local Omnigent server.

## Initial smoke tests

Run these first:

```powershell
omni --version
omni --help
omni server --help
omni host --help
psmux --version
```

Then verify the local server/host path:

1. Start `omni server` in one PowerShell.
2. Start `omni host --server http://localhost:6767` in a second PowerShell.
3. Confirm neither process exits immediately with an error.
4. Exercise one normal managed terminal/session from the UI or client and confirm the terminal opens and accepts input.

For source-level Windows regression tests from a repository checkout, use:

```powershell
.\scripts\windows_safe_pytest.ps1 -StableOnly
```

For the psmux backend specifically:

```powershell
uv run pytest `
  tests/terminals/test_windows_psmux.py::test_windows_psmux_backend_launch_send_read_close `
  tests/terminals/test_windows_psmux.py::test_windows_psmux_backend_strips_runner_auth_secrets `
  -p no:cacheprovider -q
```

## Uninstall

From an extracted Windows bundle:

```powershell
.\uninstall.ps1
```

or double-click `UNINSTALL.cmd`.

`uv` and `psmux` are intentionally left installed because other tools may use them.
