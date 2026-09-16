#Requires -Version 5.1
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\Omnigent")
)

$ErrorActionPreference = "Stop"
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
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "Removed Omnigent from $InstallDir"
} else {
    Write-Host "Omnigent install directory was not present: $InstallDir"
}
Write-Host "uv and psmux, if installed separately, were left unchanged."
