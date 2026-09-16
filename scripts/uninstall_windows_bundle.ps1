#Requires -Version 5.1
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\Omnigent")
)

$ErrorActionPreference = "Stop"
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

Remove-UserPathEntry $binDir

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($null -ne $uv -and (Test-Path $InstallDir)) {
    $env:UV_TOOL_DIR = $toolDir
    $env:UV_TOOL_BIN_DIR = $binDir
    & $uv.Source tool uninstall omnigent 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "uv tool uninstall returned exit code $LASTEXITCODE; removing the isolated artifact directory directly."
    }
}

if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "Removed Omnigent from $InstallDir"
} else {
    Write-Host "Omnigent install directory was not present: $InstallDir"
}
Write-Host "uv and psmux, if installed separately, were left unchanged."
