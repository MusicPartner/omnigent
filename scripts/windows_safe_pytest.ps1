<#
Run the current native-Windows-safe pytest checks.

This script intentionally separates collection from execution. Collection should
stay broad (`-m "not posix_only"`) so new import-time Windows regressions are
caught early. Execution stays on the stable subset until the broader sweep is
made deterministic.
#>

[CmdletBinding()]
param(
    [switch]$CollectOnly,
    [switch]$StableOnly
)

$ErrorActionPreference = 'Stop'

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Command
    )

    Write-Host "`n==> $Name" -ForegroundColor Cyan
    Write-Host ("> " + ($Command -join ' ')) -ForegroundColor DarkGray
    & $Command[0] @($Command[1..($Command.Length - 1)])
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed with exit code ${LASTEXITCODE}: $Name"
    }
}

Invoke-Step "import smoke" @('uv', 'run', 'python', '-c', "import omnigent; print('import omnigent OK')")
Invoke-Step "CLI smoke" @('uv', 'run', 'omnigent', '--help')

if (-not $StableOnly) {
    Invoke-Step "broad Windows-safe collection" @('uv', 'run', 'pytest', '-m', 'not posix_only', '--collect-only', '-q')
}

if ($CollectOnly) {
    Write-Host "`nCollection-only mode complete." -ForegroundColor Green
    exit 0
}

Invoke-Step "stable Windows unit subset" @(
    'uv', 'run', 'pytest',
    'tests/inner/test_proc_and_platform.py',
    'tests/runtime/test_process_manager.py',
    'tests/runner/test_routing.py',
    'tests/server/test_runner_transport.py',
    'tests/inner/test_sandbox_capabilities.py',
    'tests/spec/test_parser.py::test_parse_windows_jobobject_rejects_network_deny',
    'tests/spec/test_parser.py::test_parse_windows_jobobject_rejects_egress_rules',
    'tests/spec/test_validator.py::test_os_env_windows_jobobject_rejects_network_deny',
    'tests/spec/test_validator.py::test_os_env_windows_jobobject_rejects_egress_rules',
    'tests/scripts/test_install_oss_ps1.py',
    '-p', 'no:cacheprovider', '-q'
)

Write-Host "`nWindows-safe pytest subset complete." -ForegroundColor Green
