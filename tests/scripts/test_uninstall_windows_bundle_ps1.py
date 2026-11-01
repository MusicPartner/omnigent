"""Execute the uninstaller with disposable files and fake persistent PATH storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.scripts.test_install_windows_bundle_ps1 import PWSH, run_ps

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell is not available")


def run_uninstall(tmp_path: Path, outcome: str) -> dict:
    fake_uv = tmp_path / "fake-uv.ps1"
    fake_uv.write_text(
        "@{tool=$env:UV_TOOL_DIR; bin=$env:UV_TOOL_BIN_DIR; arguments=@($args)} "
        "| ConvertTo-Json -Compress | Set-Content -LiteralPath $env:TEST_UV_RECORD\n"
        "if ($env:TEST_OUTCOME -eq 'exception') { throw 'synthetic uv exception' }\n"
        "$global:LASTEXITCODE = if ($env:TEST_OUTCOME -eq 'nonzero') {31} else {0}\n",
        encoding="utf-8",
    )
    result = run_ps(
        r"""
class FakeEnvironment {
    static [string] $UserPath = 'synthetic-bin;unrelated-bin'
    static [int] $Writes = 0
    static [string] GetEnvironmentVariable([string]$Name, [string]$Target) {
        return [FakeEnvironment]::UserPath
    }
    static [void] SetEnvironmentVariable([string]$Name, [string]$Value, [string]$Target) {
        [FakeEnvironment]::UserPath = $Value
        [FakeEnvironment]::Writes++
    }
}
function Get-Command {
    param([string]$Name, $ErrorAction)
    if ($Name -eq 'uv') {
        if ($env:TEST_OUTCOME -eq 'absent') { return $null }
        return [pscustomobject]@{Source=$env:TEST_FAKE_UV}
    }
    Microsoft.PowerShell.Core\Get-Command $Name -ErrorAction $ErrorAction
}
$helperPath = Join-Path $env:TEST_ROOT 'scripts/windows_bundle_state.ps1'
$source = [IO.File]::ReadAllText((Join-Path $env:TEST_ROOT 'scripts/uninstall_windows_bundle.ps1'))
$source = $source.Replace('[Environment]', '[FakeEnvironment]')
$source = $source.Replace(
    '. (Join-Path $PSScriptRoot "windows_bundle_state.ps1")',
    '. $helperPath')
[FakeEnvironment]::UserPath = (Join-Path $env:TEST_PREFIX 'bin') + ';unrelated-bin'
$initialPath = [FakeEnvironment]::UserPath
$failure = $null
try { & ([scriptblock]::Create($source)) -InstallDir $env:TEST_PREFIX *> $null }
catch { $failure = $_.Exception.Message }
@{
    failure=$failure; writes=[FakeEnvironment]::Writes
    path=[FakeEnvironment]::UserPath; initial_path=$initialPath
    prefix_exists=[IO.Directory]::Exists($env:TEST_PREFIX)
    receipt_exists=[IO.File]::Exists((Join-Path $env:TEST_PREFIX '.omnigent-bundle-receipt.json'))
    tool=$env:UV_TOOL_DIR; tool_present=(Test-Path Env:UV_TOOL_DIR)
    bin=$env:UV_TOOL_BIN_DIR; bin_present=(Test-Path Env:UV_TOOL_BIN_DIR)
    certificates=$env:UV_SYSTEM_CERTS
    uv_called=[IO.File]::Exists($env:TEST_UV_RECORD)
} | ConvertTo-Json -Compress
""",
        env={
            "TEST_ROOT": str(ROOT),
            "TEST_PREFIX": str(tmp_path / "bundle"),
            "TEST_FAKE_UV": str(fake_uv),
            "TEST_UV_RECORD": str(tmp_path / "uv-record.json"),
            "TEST_OUTCOME": outcome,
            "UV_TOOL_DIR": r"C:\Prior\tools",
            "UV_SYSTEM_CERTS": "false",
        },
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def make_owned_prefix(tmp_path: Path) -> Path:
    prefix = tmp_path / "bundle"
    (prefix / "tools").mkdir(parents=True)
    (prefix / "bin").mkdir()
    (prefix / "tools" / "owned.txt").write_text("owned", encoding="utf-8")
    (prefix / "bin" / "omni.exe").write_bytes(b"synthetic executable")
    result = run_ps(
        ". $env:TEST_HELPER; Write-OmnigentBundleReceipt $env:TEST_PREFIX",
        env={
            "TEST_HELPER": str(ROOT / "scripts/windows_bundle_state.ps1"),
            "TEST_PREFIX": str(prefix),
        },
    )
    assert result.returncode == 0, result.stderr
    return prefix


def test_missing_uninstall_target_leaves_path_and_uv_untouched(tmp_path: Path) -> None:
    result = run_uninstall(tmp_path, "success")
    assert result["failure"] is None
    assert result["writes"] == 0 and not result["uv_called"]
    assert result["path"] == result["initial_path"]
    assert not result["prefix_exists"]


@pytest.mark.parametrize("extra", ["foreign.txt", "tools/foreign.txt", "bin/foreign.txt"])
def test_uninstall_refuses_unexpected_content_before_uv_or_path_changes(
    tmp_path: Path, extra: str
) -> None:
    prefix = make_owned_prefix(tmp_path)
    sentinel = prefix / extra
    sentinel.write_text("unrelated", encoding="utf-8")
    result = run_uninstall(tmp_path, "success")
    assert result["failure"]
    assert result["writes"] == 0 and not result["uv_called"]
    assert result["receipt_exists"] and sentinel.read_text(encoding="utf-8") == "unrelated"


def test_uninstall_refuses_receipt_free_directory_without_deletion(tmp_path: Path) -> None:
    prefix = tmp_path / "bundle"
    prefix.mkdir()
    sentinel = prefix / "unrelated.txt"
    sentinel.write_text("unrelated", encoding="utf-8")
    result = run_uninstall(tmp_path, "success")
    assert "no valid ownership receipt" in result["failure"]
    assert result["writes"] == 0 and not result["uv_called"]
    assert sentinel.read_text(encoding="utf-8") == "unrelated"


@pytest.mark.parametrize("outcome", ["absent", "success", "nonzero", "exception"])
def test_uninstall_scopes_uv_and_removes_only_validated_owned_inventory(
    tmp_path: Path, outcome: str
) -> None:
    prefix = make_owned_prefix(tmp_path)
    sibling = tmp_path / "unrelated-sibling.txt"
    sibling.write_text("preserved", encoding="utf-8")
    result = run_uninstall(tmp_path, outcome)
    assert sibling.read_text(encoding="utf-8") == "preserved"
    assert result["tool"] == r"C:\Prior\tools" and result["tool_present"]
    assert result["bin"] is None and not result["bin_present"]
    assert result["certificates"] == "false"
    assert result["uv_called"] is (outcome != "absent")
    if outcome in {"absent", "success"}:
        assert result["failure"] is None
        assert result["writes"] == 1 and result["path"] == "unrelated-bin"
        assert not result["prefix_exists"]
    else:
        assert result["failure"]
        assert result["writes"] == 0 and result["path"] == result["initial_path"]
        assert result["receipt_exists"] and (prefix / "tools/owned.txt").exists()
    if outcome != "absent":
        record = json.loads((tmp_path / "uv-record.json").read_text(encoding="utf-8-sig"))
        assert record == {
            "tool": str(prefix / "tools"),
            "bin": str(prefix / "bin"),
            "arguments": ["tool", "uninstall", "omnigent"],
        }
