#Requires -Version 5.1
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\Omnigent")
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "windows_bundle_state.ps1")
$bundleState = Get-OmnigentBundleState $InstallDir
$InstallDir = $bundleState.Prefix
$toolDir = Join-Path $InstallDir "tools"
$binDir = Join-Path $InstallDir "bin"

function Remove-UserPathEntry([string]$Dir) {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $current) { return }
    $kept = @(
        $current.Split(";") |
            Where-Object {
                -not [string]::IsNullOrWhiteSpace($_) -and
                -not [string]::Equals($_.TrimEnd("\"), $Dir.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)
            }
    )
    [Environment]::SetEnvironmentVariable("Path", ($kept -join ";"), "User")
}

if (-not $bundleState.Present) {
    Write-Host "Omnigent install directory was not present: $InstallDir"
    return
}
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($null -ne $uv) {
    $previousUvToolDir = $env:UV_TOOL_DIR
    $previousUvToolBinDir = $env:UV_TOOL_BIN_DIR
    try {
        $env:UV_TOOL_DIR = $toolDir
        $env:UV_TOOL_BIN_DIR = $binDir
        & $uv.Source tool uninstall omnigent
        if ($LASTEXITCODE -ne 0) {
            throw "uv tool uninstall failed (exit code $LASTEXITCODE); preserving the receipt and PATH for recovery."
        }
    } finally {
        if ($null -eq $previousUvToolDir) {
            Remove-Item Env:\UV_TOOL_DIR -ErrorAction SilentlyContinue
        } else {
            $env:UV_TOOL_DIR = $previousUvToolDir
        }
        if ($null -eq $previousUvToolBinDir) {
            Remove-Item Env:\UV_TOOL_BIN_DIR -ErrorAction SilentlyContinue
        } else {
            $env:UV_TOOL_BIN_DIR = $previousUvToolBinDir
        }
    }
}

Remove-OmnigentBundleInventory $bundleState
Remove-UserPathEntry $binDir
Write-Host "Removed Omnigent from $InstallDir"
Write-Host "uv and psmux, if installed separately, were left unchanged."
