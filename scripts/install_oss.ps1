#Requires -Version 5.1
<#
Omnigent Windows installer.

Installs the published `omnigent` wheel from PyPI with uv, wires PATH for the
current user, and prints Windows capability notes. The default package includes
the prebuilt web UI, so Node.js/npm are checked for harness support but are not
required for the base install.
#>

param(
    [switch]$NonInteractive,
    [switch]$VerboseOutput,
    [switch]$CheckOnly,
    [string]$Version = "",
    [string]$Repo = "",
    [string[]]$Extra = @()
)

$script:PackageName = "omnigent"
$script:PythonVersion = "3.12"
$script:InstallUrl = ""

function Write-Step([string]$Message) {
    Write-Host "==> $Message"
}

function Write-Warn([string]$Message) {
    Write-Warning $Message
}

function Fail([string]$Message) {
    throw $Message
}

function Test-Command([string]$Name) {
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-CommandVersionLine([string]$Command, [string[]]$VersionArgs = @("--version")) {
    if (-not (Test-Command $Command)) { return $null }
    try {
        $output = & $Command @VersionArgs 2>&1 | Select-Object -First 1
        if ($null -eq $output) { return "found" }
        return [string]$output
    } catch {
        return "found (version check failed: $($_.Exception.Message))"
    }
}

function Join-Extras([string[]]$Values) {
    $parts = @()
    foreach ($value in $Values) {
        if ([string]::IsNullOrWhiteSpace($value)) { continue }
        $parts += $value.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    }
    return ($parts -join ",")
}

function Normalize-RepoUrl([string]$RepoUrl, [string]$VersionValue) {
    if ($RepoUrl -and $VersionValue) {
        Fail "--version installs a PyPI release and cannot be combined with --repo."
    }
    if (-not $RepoUrl) { return "" }
    if ($RepoUrl -match "^git\+(ssh|https?|file)://") { return $RepoUrl }
    if ($RepoUrl -match "^(ssh|https?|file)://") { return "git+$RepoUrl" }
    if ($RepoUrl -match "^[^@\s]+@[^:\s]+:.+") {
        $idx = $RepoUrl.IndexOf(":")
        return "git+ssh://$($RepoUrl.Substring(0, $idx))/$($RepoUrl.Substring($idx + 1))"
    }
    Fail "Unsupported --repo URL: $RepoUrl. Use https://..., ssh://..., or git@host:org/repo.git."
}

function Test-NodeSupported {
    if (-not (Test-Command "node")) { return $false }
    try {
        & node -e "process.exit(typeof require('node:worker_threads').markAsUncloneable === 'function' ? 0 : 1)" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-ToolStatus {
    $rows = @()
    $rows += [pscustomobject]@{ Name = "uv"; Required = $true; Found = Test-Command "uv"; Detail = Get-CommandVersionLine "uv" }
    $rows += [pscustomobject]@{ Name = "git"; Required = [bool]$Repo; Found = Test-Command "git"; Detail = Get-CommandVersionLine "git" }
    $rows += [pscustomobject]@{ Name = "node"; Required = [bool]$Repo; Found = Test-Command "node"; Detail = Get-CommandVersionLine "node" @("--version") }
    $rows += [pscustomobject]@{ Name = "npm"; Required = [bool]$Repo; Found = Test-Command "npm"; Detail = Get-CommandVersionLine "npm" @("--version") }
    $rows += [pscustomobject]@{ Name = "psmux"; Required = $false; Found = Test-Command "psmux"; Detail = Get-CommandVersionLine "psmux" }
    return $rows
}

function Show-DependencySummary {
    Write-Step "Checking Windows prerequisites"
    foreach ($row in Get-ToolStatus) {
        $kind = if ($row.Required) { "required" } else { "optional" }
        if ($row.Found) {
            Write-Host "  - $($row.Name): found ($kind) $($row.Detail)"
        } else {
            Write-Host "  - $($row.Name): missing ($kind)"
        }
    }

    if (-not (Test-Command "uv")) {
        Fail "uv is required. Install it with: winget install --id Astral-sh.Uv -e"
    }
    if ($Repo -and -not (Test-Command "git")) {
        Fail "git is required when --repo is used. Install it with: winget install --id Git.Git -e"
    }
    if ($Repo -and -not (Test-NodeSupported)) {
        Fail "Node.js 22 LTS or newer is required when --repo builds from source. Install it from https://nodejs.org/ or with winget."
    }
    if ($Repo -and -not (Test-Command "npm")) {
        Fail "npm is required when --repo builds from source. Install Node.js 22 LTS or newer."
    }
}

function Get-UvInstallTarget([string]$InstallUrlValue, [string]$VersionValue, [string]$ExtrasValue) {
    if ($InstallUrlValue) { return $InstallUrlValue }
    $name = $script:PackageName
    if ($ExtrasValue) { $name = "$name[$ExtrasValue]" }
    if ($VersionValue) { return "$name==$VersionValue" }
    return $name
}

function Get-UvToolBinDir {
    $out = & uv tool dir --bin 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($out)) {
        Fail "Could not determine uv tool bin directory."
    }
    return ([string]$out).Trim()
}

function Add-UserPathEntry([string]$Dir) {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @()
    if ($current) { $parts = $current.Split(";") | Where-Object { $_ } }
    if ($parts -contains $Dir) {
        Write-Step "PATH is already configured for $Dir"
        return
    }
    $newPath = if ($current) { "$current;$Dir" } else { $Dir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Step "Added $Dir to the user PATH"
}

function Show-CapabilitySummary {
    Write-Step "Windows capability summary"
    Write-Host "  - Supported: omnigent server, the web UI, and SDK-based harnesses."
    Write-Host "  - Process containment: Windows Job Object backend."
    Write-Host "  - Not yet equivalent to Linux/macOS: filesystem/network sandboxing and L7 egress proxy."
    if (Test-Command "psmux") {
        Write-Host "  - psmux detected; native Omnigent-managed terminal lifecycle is enabled."
    } else {
        Write-Host "  - psmux not found; native Omnigent-managed terminals require psmux on PATH."
    }
}

function Install-Omnigent([string]$Target) {
    Write-Step "Installing Omnigent with uv"
    & uv tool install --force -q --python $script:PythonVersion $Target
    if ($LASTEXITCODE -ne 0) { Fail "uv tool install failed." }
}

function Invoke-OmnigentInstaller {
    $script:InstallUrl = Normalize-RepoUrl $Repo $Version
    $extrasValue = Join-Extras $Extra
    Show-DependencySummary
    Show-CapabilitySummary
    if ($CheckOnly) {
        Write-Step "Check-only mode complete; no installation commands were executed."
        return
    }
    $target = Get-UvInstallTarget $script:InstallUrl $Version $extrasValue
    Install-Omnigent $target
    $binDir = Get-UvToolBinDir
    Add-UserPathEntry $binDir
    Write-Step "Installed Omnigent. Open a new PowerShell and run: omnigent"
}

if ($env:OMNIGENT_INSTALL_OSS_PS1_LIB_ONLY -ne "1") {
    Invoke-OmnigentInstaller
}
