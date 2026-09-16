# Windows quickstart

## Install

1. In GitHub, open **Actions -> Fork release validation**.
2. Open the latest successful run for `windows-parity/v0.14-integration` (or `main` after the Windows branch is merged).
3. Download the `omnigent-windows-<commit-sha>` artifact and extract the ZIP.
4. Double-click `INSTALL.cmd`, or run this from PowerShell in the extracted folder:

   ```powershell
   .\install.ps1
   ```

5. Open a **new PowerShell** and verify the installed CLI:

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

## Upgrade

Download the newer successful `omnigent-windows-<commit-sha>` artifact, extract it to a new folder, and run `INSTALL.cmd` again.

The installer uses `uv tool install --force` with the exact three wheels in that bundle, so it replaces the previous Omnigent tool installation in place while keeping the same install directory and PATH entry.

Verify the upgraded version:

```powershell
omni --version
```

You do **not** need to uninstall the previous bundle first.

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
