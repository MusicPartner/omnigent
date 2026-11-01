"""Exercise the complete Windows bundle installer with isolated side effects.

The test keeps the production installer and ownership helper intact, substituting
only uv resolution, uv execution, CLI smoke processes, and persistent user PATH.
It does not prove real uv wheel installation or the native CLI executables.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.scripts.test_install_windows_bundle_ps1 import PWSH, run_ps

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "install_windows_bundle.ps1"
STATE_SCRIPT = ROOT / "scripts" / "windows_bundle_state.ps1"
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell is not available")


def _run_installer(
    tmp_path: Path,
    *,
    existing_receipt: bool = False,
    foreign_file: bool = False,
    no_path: bool = True,
    uv_outcome: str = "success",
    smoke_failure: str = "",
    prior_uv: tuple[str | None, str | None, str | None] = (None, None, None),
) -> dict[str, object]:
    """Run the full installer body against only paths and fakes owned by tmp_path."""
    prefix = tmp_path / "bundle"
    bundle = tmp_path / "synthetic-bundle"
    wheels = bundle / "wheels"
    wheels.mkdir(parents=True)
    for wheel_name in (
        "omnigent-1.0-py3-none-any.whl",
        "omnigent_client-1.0-py3-none-any.whl",
        "omnigent_ui_sdk-1.0-py3-none-any.whl",
    ):
        (wheels / wheel_name).touch()

    uv_script = tmp_path / "fake-uv.ps1"
    uv_script.write_text(
        "@{ tool=$env:UV_TOOL_DIR; bin=$env:UV_TOOL_BIN_DIR; "
        "certificates=$env:UV_SYSTEM_CERTS; arguments=@($args) } "
        "| ConvertTo-Json -Compress "
        "| Set-Content -LiteralPath $env:TEST_UV_RECORD\n"
        "New-Item -ItemType Directory -Force -Path $env:UV_TOOL_DIR, "
        "$env:UV_TOOL_BIN_DIR | Out-Null\n"
        "[IO.File]::WriteAllText((Join-Path $env:UV_TOOL_DIR 'tool-owned.txt'), 'owned')\n"
        "[IO.File]::WriteAllText((Join-Path $env:UV_TOOL_BIN_DIR 'omni.exe'), 'owned')\n"
        "[IO.File]::WriteAllText((Join-Path $env:UV_TOOL_BIN_DIR 'omnigent.exe'), 'owned')\n"
        "if ($env:TEST_UV_OUTCOME -eq 'exception') { throw 'synthetic uv exception' }\n"
        "if ($env:TEST_UV_OUTCOME -eq 'nonzero') { $global:LASTEXITCODE = 31 } "
        "else { $global:LASTEXITCODE = 0 }\n",
        encoding="utf-8",
    )

    environment = {
        "TEST_ROOT": str(ROOT),
        "TEST_PREFIX": str(prefix),
        "TEST_BUNDLE_ROOT": str(bundle),
        "TEST_FAKE_UV": str(uv_script),
        "TEST_UV_RECORD": str(tmp_path / "uv-record.json"),
        "TEST_RESOLVE_RECORD": str(tmp_path / "resolve-record.txt"),
        "TEST_SMOKE_RECORD": str(tmp_path / "smoke-record.txt"),
        "TEST_UV_OUTCOME": uv_outcome,
        "TEST_SMOKE_FAILURE": smoke_failure,
        "TEST_USER_PATH": "prior-bin;unrelated-bin",
        "TEST_PROCESS_PATH": "process-bin;unrelated-bin",
        "TEST_EXISTING_RECEIPT": str(existing_receipt).lower(),
        "TEST_FOREIGN_FILE": str(foreign_file).lower(),
        "TEST_NO_PATH": str(no_path).lower(),
        # The state helper rejects installs under the real temp or Windows roots.
        "TEST_PROTECTED_TEMP": r"C:\ProtectedTemp",
        "TEST_WINDOWS_ROOT": r"C:\ProtectedWindows",
        "USERPROFILE": r"C:\ProtectedUser",
        "LOCALAPPDATA": r"C:\ProtectedLocalAppData",
        "APPDATA": r"C:\ProtectedAppData",
        "ProgramFiles": r"C:\ProtectedProgramFiles",
        "ProgramFiles(x86)": r"C:\ProtectedProgramFilesX86",
        "ProgramData": r"C:\ProtectedProgramData",
        "SystemRoot": r"C:\ProtectedWindows",
        "WINDIR": r"C:\ProtectedWindows",
    }
    for name, value in zip(
        ("UV_SYSTEM_CERTS", "UV_TOOL_DIR", "UV_TOOL_BIN_DIR"), prior_uv, strict=True
    ):
        environment[f"TEST_PRIOR_{name}_PRESENT"] = str(value is not None).lower()
        environment[f"TEST_PRIOR_{name}"] = value or ""

    result = run_ps(
        r"""
class FakeEnvironment {
    static [string] $UserPath
    static [int] $Writes = 0
    static [string] GetEnvironmentVariable([string]$Name, [string]$Target) {
        return [FakeEnvironment]::UserPath
    }
    static [void] SetEnvironmentVariable([string]$Name, [string]$Value, [string]$Target) {
        [FakeEnvironment]::UserPath = $Value
        [FakeEnvironment]::Writes++
    }
}
function Invoke-TestSmoke([string]$Name) {
    Add-Content -LiteralPath $env:TEST_SMOKE_RECORD -Value $Name
    if ($env:TEST_SMOKE_FAILURE -eq $Name) { $global:LASTEXITCODE = 41 }
    else { $global:LASTEXITCODE = 0 }
}

$source = [IO.File]::ReadAllText((Join-Path $env:TEST_ROOT 'scripts/install_windows_bundle.ps1'))
$tokens = $null
$parseErrors = $null
$installerAst = [System.Management.Automation.Language.Parser]::ParseInput(
    $source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
$edits = [System.Collections.Generic.List[object]]::new()
function Add-SourceEdit([int]$Start, [int]$Length, [string]$Text) {
    $edits.Add([pscustomobject]@{ Start=$Start; Length=$Length; Text=$Text })
}

$helperDotSource = '. (Join-Path $PSScriptRoot "windows_bundle_state.ps1")'
if ([regex]::Matches($source, [regex]::Escape($helperDotSource)).Count -ne 1) {
    throw 'Expected exactly one literal ownership-helper dot-source.'
}
$dotSourceOffset = $source.IndexOf($helperDotSource, [StringComparison]::Ordinal)
Add-SourceEdit $dotSourceOffset $helperDotSource.Length '. $helperPath'
$helperPath = Join-Path $env:TEST_ROOT 'scripts/windows_bundle_state.ps1'

$bundleAssignments = @($installerAst.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -eq '$script:BundleRoot'
}, $true))
$expectedBundleAssignment = '$script:BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path'
if ($bundleAssignments.Count -ne 1 -or
    $bundleAssignments[0].Extent.Text -ne $expectedBundleAssignment) {
    throw 'The BundleRoot source binding changed; review this test substitution.'
}
Add-SourceEdit $bundleAssignments[0].Extent.StartOffset $bundleAssignments[0].Extent.Text.Length `
    '$script:BundleRoot = $env:TEST_BUNDLE_ROOT'

$resolveFunctions = @($installerAst.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Resolve-Uv'
}, $true))
if ($resolveFunctions.Count -ne 1) { throw 'Expected one Resolve-Uv function.' }
Add-SourceEdit $resolveFunctions[0].Extent.StartOffset $resolveFunctions[0].Extent.Text.Length @'
function Resolve-Uv {
    Add-Content -LiteralPath $env:TEST_RESOLVE_RECORD -Value 'called'
    return $env:TEST_FAKE_UV
}
'@

foreach ($smoke in @(
    @{ Original='& $omniExe --version'; Replacement="Invoke-TestSmoke 'omni-version'" },
    @{ Original='& $omniExe --help *> $null'; Replacement="Invoke-TestSmoke 'omni-help'" },
    @{ Original='& $omnigentExe --version'; Replacement="Invoke-TestSmoke 'omnigent-version'" }
)) {
    if ([regex]::Matches($source, [regex]::Escape($smoke.Original)).Count -ne 1) {
        throw "Expected exactly one CLI smoke command: $($smoke.Original)"
    }
    $offset = $source.IndexOf($smoke.Original, [StringComparison]::Ordinal)
    Add-SourceEdit $offset $smoke.Original.Length $smoke.Replacement
}

# Apply AST/source-span edits from the end so earlier offsets remain valid.
foreach ($edit in @($edits | Sort-Object Start -Descending)) {
    $source = $source.Remove($edit.Start, $edit.Length).Insert($edit.Start, $edit.Text)
}
if ([regex]::Matches($source, '\[Environment\]::').Count -lt 2) {
    throw 'Expected installer-owned user PATH accessors before faking them.'
}
$source = $source.Replace('[Environment]', '[FakeEnvironment]')

$stateSource = [IO.File]::ReadAllText(
    (Join-Path $env:TEST_ROOT 'scripts/windows_bundle_state.ps1'))
$tempExpression = '[System.IO.Path]::GetTempPath()'
$windowsExpression = (
    '[System.Environment]::GetFolderPath(' +
    '[System.Environment+SpecialFolder]::Windows)'
)
if ([regex]::Matches($stateSource, [regex]::Escape($tempExpression)).Count -ne 1 -or
    [regex]::Matches($stateSource, [regex]::Escape($windowsExpression)).Count -lt 1) {
    throw 'Expected protected-root expressions in the real ownership helper.'
}
$stateSource = $stateSource.Replace($tempExpression, '$env:TEST_PROTECTED_TEMP')
$stateSource = $stateSource.Replace($windowsExpression, '$env:TEST_WINDOWS_ROOT')
. ([scriptblock]::Create($stateSource))

# Prevent ambient uv settings from being mistaken for values restored by the installer.
foreach ($name in @('UV_SYSTEM_CERTS', 'UV_TOOL_DIR', 'UV_TOOL_BIN_DIR')) {
    $present = [Environment]::GetEnvironmentVariable("TEST_PRIOR_${name}_PRESENT", 'Process')
    $value = [Environment]::GetEnvironmentVariable("TEST_PRIOR_$name", 'Process')
    if ($present -eq 'true') { Set-Item "Env:$name" $value }
    else { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
}
[FakeEnvironment]::UserPath = $env:TEST_USER_PATH
$env:PATH = $env:TEST_PROCESS_PATH
$initialUserPath = [FakeEnvironment]::UserPath

if ($env:TEST_EXISTING_RECEIPT -eq 'true') {
    New-Item -ItemType Directory -Force -Path (Join-Path $env:TEST_PREFIX 'tools'),
        (Join-Path $env:TEST_PREFIX 'bin') | Out-Null
    [IO.File]::WriteAllText((Join-Path $env:TEST_PREFIX 'tools/old-owned.txt'), 'old')
    [IO.File]::WriteAllText((Join-Path $env:TEST_PREFIX 'bin/old-owned.exe'), 'old')
    Write-OmnigentBundleReceipt $env:TEST_PREFIX
}
if ($env:TEST_FOREIGN_FILE -eq 'true') {
    New-Item -ItemType Directory -Force -Path $env:TEST_PREFIX | Out-Null
    [IO.File]::WriteAllText((Join-Path $env:TEST_PREFIX 'foreign.txt'), 'keep')
}

$failure = $null
try {
    & ([scriptblock]::Create($source)) -InstallDir $env:TEST_PREFIX `
        -NoPath:$($env:TEST_NO_PATH -eq 'true') -SkipPsmux *> $null
} catch { $failure = $_.Exception.Message }
$restored = @{}
foreach ($name in @('UV_SYSTEM_CERTS', 'UV_TOOL_DIR', 'UV_TOOL_BIN_DIR')) {
    $restored[$name] = @{
        present = Test-Path "Env:$name"
        value = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
}
@{
    failure = $failure
    user_path = [FakeEnvironment]::UserPath
    initial_user_path = $initialUserPath
    user_path_writes = [FakeEnvironment]::Writes
    process_path = $env:PATH
    resolve_called = [IO.File]::Exists($env:TEST_RESOLVE_RECORD)
    uv_called = [IO.File]::Exists($env:TEST_UV_RECORD)
    smoke_record_exists = [IO.File]::Exists($env:TEST_SMOKE_RECORD)
    prefix_exists = [IO.Directory]::Exists($env:TEST_PREFIX)
    receipt_exists = [IO.File]::Exists(
        (Join-Path $env:TEST_PREFIX '.omnigent-bundle-receipt.json'))
    restored = $restored
} | ConvertTo-Json -Compress -Depth 5
""",
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _assert_uv_restored(
    observed: dict[str, object], prior: tuple[str | None, str | None, str | None]
) -> None:
    restored = observed["restored"]
    assert isinstance(restored, dict)
    for name, value in zip(
        ("UV_SYSTEM_CERTS", "UV_TOOL_DIR", "UV_TOOL_BIN_DIR"), prior, strict=True
    ):
        assert restored[name]["present"] is (value is not None)
        assert restored[name]["value"] == value


def test_receipt_free_foreign_prefix_is_refused_before_uv_or_path_changes(tmp_path: Path) -> None:
    observed = _run_installer(tmp_path, foreign_file=True)

    assert "no valid ownership receipt" in observed["failure"]
    assert observed["resolve_called"] is False
    assert observed["uv_called"] is False
    assert observed["user_path_writes"] == 0
    assert observed["user_path"] == observed["initial_user_path"]
    assert (tmp_path / "bundle" / "foreign.txt").read_text(encoding="utf-8") == "keep"
    assert observed["receipt_exists"] is False


@pytest.mark.parametrize(
    "prior_uv",
    [
        (None, None, None),
        ("false", r"C:\Prior\tools", r"C:\Prior\bin"),
        ("true", None, r"C:\Prior\bin"),
    ],
    ids=["all-absent", "all-present", "mixed-presence"],
)
def test_fresh_install_writes_receipt_and_restores_uv_without_path_write(
    tmp_path: Path, prior_uv: tuple[str | None, str | None, str | None]
) -> None:
    observed = _run_installer(tmp_path, prior_uv=prior_uv, no_path=True)

    assert observed["failure"] is None
    assert observed["resolve_called"] is True and observed["uv_called"] is True
    assert observed["receipt_exists"] is True
    assert observed["user_path_writes"] == 0
    assert observed["user_path"] == observed["initial_user_path"]
    uv_call = json.loads((tmp_path / "uv-record.json").read_text(encoding="utf-8-sig"))
    assert uv_call["tool"] == str(tmp_path / "bundle" / "tools")
    assert uv_call["bin"] == str(tmp_path / "bundle" / "bin")
    assert uv_call["certificates"] == "true"
    assert uv_call["arguments"] == [
        "tool",
        "install",
        "--force",
        "--python",
        "3.12",
        "--with",
        str(tmp_path / "synthetic-bundle" / "wheels" / "omnigent_client-1.0-py3-none-any.whl"),
        "--with",
        str(tmp_path / "synthetic-bundle" / "wheels" / "omnigent_ui_sdk-1.0-py3-none-any.whl"),
        str(tmp_path / "synthetic-bundle" / "wheels" / "omnigent-1.0-py3-none-any.whl"),
    ]
    _assert_uv_restored(observed, prior_uv)
    receipt = json.loads((tmp_path / "bundle" / ".omnigent-bundle-receipt.json").read_text())
    assert receipt["product"] == "omnigent-windows-bundle"
    assert {entry["path"] for entry in receipt["inventory"]} == {
        "tools",
        "tools/tool-owned.txt",
        "bin",
        "bin/omni.exe",
        "bin/omnigent.exe",
    }
    assert not list((tmp_path / "bundle").glob(".*.tmp"))
    assert (tmp_path / "smoke-record.txt").read_text().splitlines() == [
        "omni-version",
        "omni-help",
        "omnigent-version",
    ]


def test_valid_reinstall_replaces_receipt_and_prioritizes_user_path(tmp_path: Path) -> None:
    observed = _run_installer(tmp_path, existing_receipt=True, no_path=False)

    assert observed["failure"] is None
    assert observed["receipt_exists"] is True
    assert observed["user_path_writes"] == 1
    assert observed["user_path"].startswith(str(tmp_path / "bundle" / "bin") + ";")
    receipt = json.loads((tmp_path / "bundle" / ".omnigent-bundle-receipt.json").read_text())
    assert "tools/tool-owned.txt" in {entry["path"] for entry in receipt["inventory"]}
    assert not list((tmp_path / "bundle").glob(".*.tmp"))


def test_cli_smoke_failure_does_not_write_receipt_or_user_path(tmp_path: Path) -> None:
    observed = _run_installer(tmp_path, smoke_failure="omni-help", no_path=False)

    assert "help smoke test" in observed["failure"]
    assert observed["uv_called"] is True
    assert observed["receipt_exists"] is False
    assert observed["user_path_writes"] == 0
    assert observed["user_path"] == observed["initial_user_path"]
    assert (tmp_path / "smoke-record.txt").read_text().splitlines() == [
        "omni-version",
        "omni-help",
    ]


def test_uv_failure_restores_environment_without_receipt_or_path_change(tmp_path: Path) -> None:
    prior_uv = ("false", r"C:\Prior\tools", None)
    observed = _run_installer(tmp_path, uv_outcome="nonzero", prior_uv=prior_uv)

    assert observed["failure"]
    assert observed["uv_called"] is True
    assert observed["receipt_exists"] is False
    assert observed["user_path_writes"] == 0
    assert observed["user_path"] == observed["initial_user_path"]
    _assert_uv_restored(observed, prior_uv)
