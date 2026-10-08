# Native Windows installer

Omnigent provides a PowerShell installer for native Windows at
`scripts/install_oss.ps1`. The installer supports two explicit modes:

- **release-pinned install** from PyPI, optionally with `-Version`;
- **preview/from-source install** with `-Repo`, used for fork or pre-release
  validation.

## Prerequisites

Required for release installs:

- PowerShell 5.1 or newer;
- `uv` on `PATH`.

Required only for `-Repo` preview/from-source installs:

- `git`;
- Node.js 22 LTS or newer;
- `npm`.

Optional:

- `psmux` for native Omnigent-managed terminals on Windows.

Install common dependencies with winget:

```powershell
winget install --id Astral-sh.Uv -e
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id marlocarlo.psmux -e
```

## Check dependencies only

```powershell
.\scripts\install_oss.ps1 -CheckOnly
```

The check prints each dependency, marks it required or optional, and exits before
running `uv tool install`.

## Release-pinned install

```powershell
.\scripts\install_oss.ps1 -Version 0.1.0
```

Without `-Version`, the installer asks `uv` to install the current published
`omnigent` package from PyPI. With `-Version`, it installs exactly
`omnigent==<version>`.

## Preview/from-source install

```powershell
.\scripts\install_oss.ps1 -Repo https://github.com/smota/omnigent
```

This path is intentionally labeled preview/from-source because it installs from a
mutable repository ref instead of a published release.

## Repeat install

The installer uses `uv tool install --force`, so running the same command again
updates/replaces the tool environment. It only adds the `uv tool dir --bin` path
to the user `PATH` when that entry is missing.

## Capability boundary

The installer reflects the Windows support contract from
`../windows-first-class-support-adr.md`:

- server, web UI, and SDK-based harnesses are supported;
- `windows_jobobject` provides process containment only;
- filesystem/network sandboxing and L7 egress enforcement are not equivalent to
  Linux/macOS and unsupported policy combinations fail closed;
- `psmux` enables native Windows terminal lifecycle support when installed, with
  browser attach fidelity documented separately in `psmux-browser-attach.md`.
