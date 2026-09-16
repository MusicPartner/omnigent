#Requires -Version 5.1
<#
Install an Omnigent Windows artifact bundle produced by the fork release workflow.

The installer uses the exact wheels shipped beside this script and creates an
isolated Python 3.12 environment. The wheel's upstream-compatible console-script
metadata creates both omni.exe and omnigent.exe in the environment's Scripts
directory; that directory can be added directly to the current user's PATH.
#>

param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\Omnigent"),
    [switch]$NoPath,
    [switch]$SkipPsmux
)

$ErrorActionPreference = "Stop"
$script:PythonVersion = "3.12"
$script:BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:WheelDir = Join-Path $script:BundleRoot "wheels"

function Write-Step([string]$Message) {
    Write-Host "==> $Message"
}

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Resolve-Uv {
    $existing = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        return $existing.Source
    }

    if (-not (Test-Command "winget")) {
        throw "uv is required and was not found. Install it with 'winget install --id Astral-sh.Uv -e', then rerun this installer."
    }

    Write-Step "Installing uv with winget"
    & winget install --id Astral-sh.Uv -e --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install uv (exit code $LASTEXITCODE)."
    }

    $wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    if (Test-Path $wingetLinks) {
        $env:PATH = "$wingetLinks;$env:PATH"
    }
    $installed = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -eq $installed) {
        $candidate = Join-Path $wingetLinks "uv.exe"
        if (Test-Path $candidate) {
            return $candidate
        }
        throw "uv was installed but is not visible on PATH. Open a new PowerShell and rerun the installer."
    }
    return $installed.Source
}

function Ensure-Psmux {
    if ($SkipPsmux) {
        Write-Step "Skipping optional psmux installation"
        return
    }
    if (Test-Command "psmux") {
        Write-Step "psmux is already installed"
        return
    }
    if (-not (Test-Command "winget")) {
        Write-Warning "psmux is not installed and winget is unavailable. Omnigent will run, but native managed terminals require psmux."
        return
    }

    Write-Step "Installing psmux for native managed terminals"
    & winget install --id marlocarlo.psmux -e --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "psmux installation failed (exit code $LASTEXITCODE). The server can still run, but native managed terminals may be unavailable."
        return
    }
    $wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    if (Test-Path $wingetLinks) {
        $env:PATH = "$wingetLinks;$env:PATH"
    }
}

function Add-UserPathEntry([string]$Dir) {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @()
    if ($current) {
        $parts = @($current.Split(";") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }
    $alreadyPresent = $false
    foreach ($part in $parts) {
        if ([string]::Equals($part.TrimEnd("\"), $Dir.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) {
            $alreadyPresent = $true
            break
        }
    }
    if (-not $alreadyPresent) {
        $newPath = if ($current) { "$current;$Dir" } else { $Dir }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Step "Added $Dir to the current user's PATH"
    }
    if (-not (($env:PATH -split ";") -contains $Dir)) {
        $env:PATH = "$Dir;$env:PATH"
    }
}

if (-not (Test-Path $script:WheelDir)) {
    throw "Bundle wheel directory not found: $script:WheelDir"
}
$wheels = @(Get-ChildItem $script:WheelDir -Filter "*.whl" -File)
if ($wheels.Count -lt 3) {
    throw "Expected the core, client SDK, and UI SDK wheels in $script:WheelDir; found $($wheels.Count)."
}

$uv = Resolve-Uv
$venvDir = Join-Path $InstallDir ".venv"
$scriptsDir = Join-Path $venvDir "Scripts"
$python = Join-Path $scriptsDir "python.exe"
$omniExe = Join-Path $scriptsDir "omni.exe"
$omnigentExe = Join-Path $scriptsDir "omnigent.exe"

Write-Step "Installing Omnigent from this artifact into $InstallDir"
New-Item -ItemType Directory -Force $InstallDir | Out-Null
if (Test-Path $venvDir) {
    Remove-Item -Recurse -Force $venvDir
}

& $uv venv --python $script:PythonVersion $venvDir
if ($LASTEXITCODE -ne 0) {
    throw "Could not create the Python $script:PythonVersion environment."
}

$wheelPaths = @($wheels | ForEach-Object { $_.FullName })
& $uv pip install --python $python @wheelPaths
if ($LASTEXITCODE -ne 0) {
    throw "Could not install the artifact wheels."
}
if (-not (Test-Path $omniExe)) {
    throw "Installation completed without creating the upstream-compatible omni.exe entry point: $omniExe"
}
if (-not (Test-Path $omnigentExe)) {
    throw "Installation completed without creating the omnigent.exe entry point: $omnigentExe"
}

if (-not $NoPath) {
    Add-UserPathEntry $scriptsDir
}
Ensure-Psmux

Write-Step "Verifying the installed upstream-compatible CLI entry points"
& $omniExe --version
if ($LASTEXITCODE -ne 0) {
    throw "Installed omni.exe failed its version smoke test."
}
& $omniExe --help *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Installed omni.exe failed its help smoke test."
}
& $omnigentExe --version
if ($LASTEXITCODE -ne 0) {
    throw "Installed omnigent.exe failed its version smoke test."
}

Write-Host ""
Write-Host "Omnigent installed successfully."
Write-Host "omni.exe: $omniExe"
Write-Host "omnigent.exe: $omnigentExe"
if ($NoPath) {
    Write-Host "Run: $omniExe --version"
} else {
    Write-Host "Open a new PowerShell and run: omni --version"
}
Write-Host "Start the server with: omni server"
Write-Host "Then start a host in another PowerShell with: omni host --server http://localhost:6767"
