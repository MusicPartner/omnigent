Omnigent Windows build
======================

This bundle follows the current upstream Omnigent install model:
`uv tool install`, with both console entry points coming directly from
the core wheel:

    omni     -> omnigent.cli:main
    omnigent -> omnigent.cli:main

On Windows, installation creates real omni.exe and omnigent.exe tool
executables. No custom CLI wrapper is used.

QUICK INSTALL
-------------
1. Extract this ZIP to a normal folder.
2. Double-click INSTALL.cmd, or run from PowerShell:

     .\install.ps1

The installer uses the exact three wheels in this bundle and installs
them with uv's tool mechanism into an isolated location under:

     %LOCALAPPDATA%\Programs\Omnigent

The executable directory is prioritized at the front of your user PATH
so an older installation does not shadow this build. If uv is missing,
the installer uses winget to install it. It also attempts to install
psmux for native managed terminals.

Windows system certificates are used for uv's HTTPS requests during
installation, supporting corporate proxies and trusted internal roots.
The previous certificate setting is restored afterwards.

After installation, open a new PowerShell and run:

     omni --version
     omni --help
     omni server

Then, in another PowerShell:

     omni host --server http://localhost:6767

The installed entry points are:

     %LOCALAPPDATA%\Programs\Omnigent\bin\omni.exe
     %LOCALAPPDATA%\Programs\Omnigent\bin\omnigent.exe

`omnigent` remains an equivalent long-form alias, matching current
upstream main.

OPTIONS
-------
Install without changing PATH:

     .\install.ps1 -NoPath

Install without attempting psmux installation:

     .\install.ps1 -SkipPsmux

Use uv's bundled certificate roots instead of Windows system roots:

     .\install.ps1 -NoSystemCertificates

Install somewhere else:

     .\install.ps1 -InstallDir C:\Tools\Omnigent

UNINSTALL
---------
Double-click UNINSTALL.cmd, or run:

     .\uninstall.ps1

uv and psmux are left installed because they may be shared by other tools.
