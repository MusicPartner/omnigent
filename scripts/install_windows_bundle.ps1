#Requires -Version 5.1
<#
Install an Omnigent Windows artifact bundle produced by the fork release workflow.

This follows current upstream's canonical wheel-install model: `uv tool install`.
The exact core/client/UI wheels shipped beside this script are installed into an
isolated uv tool environment, and the wheel's console-script metadata creates
both omni.exe and omnigent.exe in the tool bin directory.
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

$allWheels = @(Get-ChildItem $script:WheelDir -Filter "*.whl" -File)
$coreWheels = @($allWheels | Where-Object { $_.Name -match '^omnigent-[0-9].*\.whl$' })
$clientWheels = @($allWheels | Where-Object { $_.Name -match '^omnigent_client-[0-9].*\.whl$' })
$uiWheels = @($allWheels | Where-Object { $_.Name -match '^omnigent_ui_sdk-[0-9].*\.whl$' })
if ($coreWheels.Count -ne 1 -or $clientWheels.Count -ne 1 -or $uiWheels.Count -ne 1) {
    throw "Expected exactly one core, client SDK, and UI SDK wheel. Found core=$($coreWheels.Count), client=$($clientWheels.Count), ui=$($uiWheels.Count)."
}
$coreWheel = $coreWheels[0].FullName
$clientWheel = $clientWheels[0].FullName
$uiWheel = $uiWheels[0].FullName

$uv = Resolve-Uv
$toolDir = Join-Path $InstallDir "tools"
$binDir = Join-Path $InstallDir "bin"
New-Item -ItemType Directory -Force $InstallDir | Out-Null

# Keep this artifact installation isolated from any other uv-managed tools while
# still using the same `uv tool install` mechanism documented by upstream.
$env:UV_TOOL_DIR = $toolDir
$env:UV_TOOL_BIN_DIR = $binDir

Write-Step "Installing Omnigent from the bundled wheels with uv tool"
& $uv tool install --force --python $script:PythonVersion --with $clientWheel --with $uiWheel $coreWheel
if ($LASTEXITCODE -ne 0) {
    throw "uv tool install could not install the artifact wheels."
}

$omniExe = Join-Path $binDir "omni.exe"
$omnigentExe = Join-Path $binDir "omnigent.exe"
if (-not (Test-Path $omniExe)) {
    throw "Installation completed without creating the upstream-compatible omni.exe entry point: $omniExe"
}
if (-not (Test-Path $omnigentExe)) {
    throw "Installation completed without creating the omnigent.exe entry point: $omnigentExe"
}

if (-not $NoPath) {
    Add-UserPathEntry $binDir
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
