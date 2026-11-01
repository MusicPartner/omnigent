"""Ownership receipt and path-safety contracts for the Windows bundle scripts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.scripts.test_install_windows_bundle_ps1 import run_ps

STATE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "windows_bundle_state.ps1"
PWSH = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell is not available")


def run_state(snippet: str, tmp_path: Path, **extra_env: str) -> object:
    """Dot-source the production helper with protected roots isolated from test paths."""
    env = {
        "TEST_STATE_SCRIPT": str(STATE_SCRIPT),
        "TEST_PREFIX": str(tmp_path / "bundle"),
        "TEST_LOCALAPPDATA": str(tmp_path / "user-local"),
        "TEST_PROTECTED_TEMP": r"C:\ProtectedTemp",
        "TEST_WINDOWS_ROOT": r"C:\ProtectedWindows",
        "USERPROFILE": r"C:\ProtectedUser",
        "LOCALAPPDATA": str(tmp_path / "user-local"),
        "APPDATA": r"C:\ProtectedAppData",
        "ProgramFiles": r"C:\ProtectedProgramFiles",
        "ProgramFiles(x86)": r"C:\ProtectedProgramFilesX86",
        "ProgramData": r"C:\ProtectedProgramData",
    }
    env.update(extra_env)
    result = run_ps(
        r"""
$stateSource = [System.IO.File]::ReadAllText($env:TEST_STATE_SCRIPT)
$stateSource = $stateSource.Replace(
    '[System.IO.Path]::GetTempPath()', '$env:TEST_PROTECTED_TEMP')
$stateSource = $stateSource.Replace(
    '[System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Windows)',
    '$env:TEST_WINDOWS_ROOT')
. ([scriptblock]::Create($stateSource))
"""
        + snippet,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def receipt(prefix: str, inventory: list[dict[str, str]] | None = None) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "product": "omnigent-windows-bundle",
            "prefix": prefix,
            "inventory": inventory
            if inventory is not None
            else [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/omnigent.exe", "kind": "file"},
                {"path": "bin/omni.exe", "kind": "file"},
            ],
        }
    )


def test_fresh_and_absent_prefixes_have_expected_state(tmp_path: Path) -> None:
    fresh = tmp_path / "bundle"
    fresh.mkdir()
    result = run_state(
        r"""
$install = Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall
$absent = Get-OmnigentBundleState (Join-Path $env:TEST_PREFIX 'not-created')
@{
    install_present = $install.Present
    install_receipt = ($null -eq $install.Receipt)
    absent_present = $absent.Present
    absent_prefix_created = [System.IO.Directory]::Exists($absent.Prefix)
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert result == {
        "install_present": True,
        "install_receipt": True,
        "absent_present": False,
        "absent_prefix_created": False,
    }


def test_empty_prefix_without_receipt_is_install_only_state(tmp_path: Path) -> None:
    (tmp_path / "bundle").mkdir()
    result = run_state(
        r"""
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "no ownership receipt" in result["failure"]


def test_nonempty_receipt_free_prefix_is_refused(tmp_path: Path) -> None:
    prefix = tmp_path / "bundle"
    (prefix / "tools").mkdir(parents=True)
    (prefix / "tools" / "keep.txt").write_text("owned by test", encoding="utf-8")
    result = run_state(
        r"""
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $failure = $_.Exception.Message }
@{
    failure = $failure
    file_kept = Test-Path (Join-Path $env:TEST_PREFIX 'tools/keep.txt')
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "no valid ownership receipt" in result["failure"]
    assert result["file_kept"] is True


def test_write_and_read_receipt_round_trip_and_refuse_extra_root(tmp_path: Path) -> None:
    prefix = tmp_path / "bundle"
    (prefix / "tools").mkdir(parents=True)
    (prefix / "bin").mkdir()
    (prefix / "tools" / "omnigent.exe").write_bytes(b"tool")
    (prefix / "bin" / "omni.exe").write_bytes(b"cli")
    result = run_state(
        r"""
Write-OmnigentBundleReceipt $env:TEST_PREFIX
$state = Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall
$receiptPath = Get-OmnigentReceiptPath $env:TEST_PREFIX
$roundTrip = [System.IO.File]::ReadAllText($receiptPath) | ConvertFrom-Json
New-Item -ItemType Directory -Path (Join-Path $env:TEST_PREFIX 'unexpected') | Out-Null
$failure = $null
try { Write-OmnigentBundleReceipt $env:TEST_PREFIX }
catch { $failure = $_.Exception.Message }
@{
    schema = $roundTrip.schema_version
    product = $roundTrip.product
    inventory_count = $roundTrip.inventory.Count
    state_prefix = $state.Prefix
    extra_root_failure = $failure
    receipt_kept = (Test-Path $receiptPath)
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert result["schema"] == 1
    assert result["product"] == "omnigent-windows-bundle"
    assert result["inventory_count"] == 4
    assert result["state_prefix"].lower() == str(prefix).lower()
    assert "Unexpected item" in result["extra_root_failure"]
    assert result["receipt_kept"] is True


@pytest.mark.parametrize("missing_root", ["tools", "bin"])
def test_receipt_write_requires_both_bundle_roots(tmp_path: Path, missing_root: str) -> None:
    prefix = tmp_path / "bundle"
    (prefix / ("bin" if missing_root == "tools" else "tools")).mkdir(parents=True)
    result = run_state(
        r"""
$failure = $null
try { Write-OmnigentBundleReceipt $env:TEST_PREFIX }
catch { $failure = $_.Exception.Message }
@{
    failure = $failure
    receipt_exists = Test-Path (Get-OmnigentReceiptPath $env:TEST_PREFIX)
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert f"missing its expected directory: {missing_root}" in result["failure"]
    assert result["receipt_exists"] is False


def _valid_receipt(
    tmp_path: Path, entries: list[dict[str, str]] | None = None
) -> tuple[Path, str]:
    prefix = tmp_path / "bundle"
    (prefix / "tools").mkdir(parents=True)
    (prefix / "bin").mkdir()
    (prefix / "tools" / "omnigent.exe").write_bytes(b"owned")
    (prefix / "bin" / "omni.exe").write_bytes(b"owned")
    document = receipt(str(prefix), entries)
    (prefix / ".omnigent-bundle-receipt.json").write_text(document, encoding="utf-8")
    return prefix, document


@pytest.mark.parametrize(
    "document",
    [
        "{not-json",
        json.dumps({"schema_version": 1, "product": "wrong", "prefix": "x", "inventory": []}),
        json.dumps(
            {
                "schema_version": 2,
                "product": "omnigent-windows-bundle",
                "prefix": "x",
                "inventory": [],
            }
        ),
        json.dumps(
            {
                "schema_version": "1",
                "product": "omnigent-windows-bundle",
                "prefix": "x",
                "inventory": [],
            }
        ),
        json.dumps(
            {
                "schema_version": 1,
                "product": "omnigent-windows-bundle",
                "prefix": "x",
                "inventory": [],
                "extra": True,
            }
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/../escape", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools:stream", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/CON.txt", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/trailing.", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "file"},
                {"path": "bin", "kind": "directory"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/One", "kind": "file"},
                {"path": "tools/one", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/missing/child", "kind": "file"},
            ],
        ),
        receipt(
            "x",
            [
                {"path": "tools", "kind": "directory"},
                {"path": "bin", "kind": "directory"},
                {"path": "tools/file", "kind": "file", "unexpected": "property"},
            ],
        ),
    ],
    ids=[
        "malformed-json",
        "wrong-product",
        "unsupported-schema",
        "schema-type",
        "unknown-receipt-property",
        "traversal",
        "alternate-stream",
        "reserved-name",
        "trailing-dot",
        "invalid-root-kind",
        "duplicate-case-insensitive",
        "missing-parent",
        "unknown-entry-property",
    ],
)
def test_bundle_receipt_rejects_invalid_documents(tmp_path: Path, document: str) -> None:
    prefix, _ = _valid_receipt(tmp_path)
    if document != "{not-json":
        parsed_document = json.loads(document)
        parsed_document["prefix"] = str(prefix)
        document = json.dumps(parsed_document)
    (prefix / ".omnigent-bundle-receipt.json").write_text(document, encoding="utf-8")
    result = run_state(
        r"""
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert result["failure"]


def test_bundle_receipt_rejects_a_different_bound_prefix(tmp_path: Path) -> None:
    prefix, _ = _valid_receipt(tmp_path)
    (prefix / ".omnigent-bundle-receipt.json").write_text(
        receipt(str(prefix) + "-other"), encoding="utf-8"
    )
    result = run_state(
        r"""
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "different install prefix" in result["failure"]


@pytest.mark.parametrize(
    "bad_path",
    [
        r"relative\bundle",
        r"C:drive-relative",
        r"C:\safe\..\bundle",
        r"C:\safe\bundle:stream",
        r"C:\safe\wild*card",
        r"\\server\share\bundle",
        r"\\?\C:\device\bundle",
        r"C:\safe\trailing.",
        r"C:\safe\CON",
        "C:\\",
        r"-NoPath",
        r"C:\provider[bad]",
        r"HKLM:\Software\Omnigent",
    ],
    ids=[
        "relative",
        "drive-relative",
        "traversal",
        "alternate-stream",
        "wildcard",
        "unc",
        "device",
        "trailing-dot",
        "reserved-device",
        "drive-root",
        "option",
        "provider-wildcard",
        "provider-path",
    ],
)
def test_prefix_resolution_rejects_unsafe_paths(tmp_path: Path, bad_path: str) -> None:
    result = run_state(
        r"""
$failure = $null
try { Resolve-OmnigentBundlePrefix $env:TEST_BAD_PREFIX | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
        TEST_BAD_PREFIX=bad_path,
    )
    assert result["failure"]


def test_default_localappdata_programs_root_refused_and_fresh_child_allowed(
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "user-local" / "Programs"
    child = local_root / "OmnigentFresh"
    result = run_state(
        r"""
$rootFailure = $null
try { Resolve-OmnigentBundlePrefix (Join-Path $env:LOCALAPPDATA 'Programs') | Out-Null }
catch { $rootFailure = $_.Exception.Message }
$child = Resolve-OmnigentBundlePrefix $env:TEST_ALLOWED_CHILD
@{
    root_failure = $rootFailure
    child = $child
} | ConvertTo-Json -Compress
""",
        tmp_path,
        TEST_ALLOWED_CHILD=str(child),
    )
    assert "protected location" in result["root_failure"]
    assert result["child"].lower() == str(child).lower()


def test_ancestor_of_protected_environment_root_is_refused(tmp_path: Path) -> None:
    result = run_state(
        r"""
$failure = $null
try { Resolve-OmnigentBundlePrefix $env:TEST_BAD_PREFIX | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
        TEST_BAD_PREFIX=r"C:\SafeParent",
        APPDATA=r"C:\SafeParent\Roaming",
    )
    assert "protected location" in result["failure"]


def test_reparse_junction_between_synthetic_bundle_directories_is_refused(tmp_path: Path) -> None:
    prefix = tmp_path / "bundle"
    (prefix / "tools").mkdir(parents=True)
    (prefix / "bin").mkdir()
    (prefix / "tools" / "app.exe").write_bytes(b"owned")
    (prefix / "bin" / "omni.exe").write_bytes(b"owned")
    result = run_state(
        r"""
Write-OmnigentBundleReceipt $env:TEST_PREFIX
New-Item -ItemType Junction -Path (Join-Path $env:TEST_PREFIX 'tools/linked') `
    -Target (Join-Path $env:TEST_PREFIX 'bin') | Out-Null
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "reparse" in result["failure"].lower()


def test_missing_items_are_install_failure_but_uninstall_state_allows_them(tmp_path: Path) -> None:
    prefix, _ = _valid_receipt(tmp_path)
    (prefix / "tools" / "omnigent.exe").unlink()
    result = run_state(
        r"""
$installFailure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $installFailure = $_.Exception.Message }
$uninstall = Get-OmnigentBundleState $env:TEST_PREFIX
@{
    install_failure = $installFailure
    uninstall_present = $uninstall.Present
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "recorded bundle item is missing" in result["install_failure"]
    assert result["uninstall_present"] is True


def test_live_item_type_change_is_refused(tmp_path: Path) -> None:
    prefix, _ = _valid_receipt(tmp_path)
    (prefix / "tools" / "omnigent.exe").unlink()
    (prefix / "tools" / "omnigent.exe").mkdir()
    result = run_state(
        r"""
$failure = $null
try { Get-OmnigentBundleState $env:TEST_PREFIX -ForInstall | Out-Null }
catch { $failure = $_.Exception.Message }
@{ failure = $failure } | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "changed type" in result["failure"]


def test_cleanup_refuses_a_receipt_changed_after_state_capture(tmp_path: Path) -> None:
    _prefix, _ = _valid_receipt(tmp_path)
    result = run_state(
        r"""
$captured = Get-OmnigentBundleState $env:TEST_PREFIX
[System.IO.File]::WriteAllText((Join-Path $env:TEST_PREFIX 'tools/new-file'), 'owned')
Write-OmnigentBundleReceipt $env:TEST_PREFIX
$failure = $null
try { Remove-OmnigentBundleInventory $captured }
catch { $failure = $_.Exception.Message }
@{
    failure = $failure
    receipt_kept = Test-Path (Get-OmnigentReceiptPath $env:TEST_PREFIX)
    added_file_kept = Test-Path (
        Join-Path $env:TEST_PREFIX 'tools/new-file'
    )
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert "receipt changed after state was captured" in result["failure"]
    assert result["receipt_kept"] is True
    assert result["added_file_kept"] is True


def test_inventory_cleanup_contains_no_recursive_delete_command(tmp_path: Path) -> None:
    result = run_state(
        r"""
$function = (Get-Command Remove-OmnigentBundleInventory).ScriptBlock.Ast.Extent.Text
@{
    recursive_delete = $function -match '(?i)Remove-Item\s+[^\r\n]*-Recurse'
} | ConvertTo-Json -Compress
""",
        tmp_path,
    )
    assert result["recursive_delete"] is False
