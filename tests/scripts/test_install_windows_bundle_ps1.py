"""Bundle installer regressions without touching installed tools or user PATH."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

INSTALLER = Path(__file__).resolve().parents[2] / "scripts" / "install_windows_bundle.ps1"
PWSH = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell is not available")


def run_ps(snippet: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Parse the real installer, then execute only the selected code in a child."""
    assert PWSH is not None
    base = os.environ.copy()
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DATABRICKS_TOKEN", "UV_SYSTEM_CERTS"):
        base.pop(name, None)
    base.update(env or {})
    installer = str(INSTALLER).replace("'", "''")
    program = f"""
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    '{installer}', [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) {{ throw ($parseErrors | Out-String) }}
{snippet}
"""
    return subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-Command", program],
        env=base,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


@pytest.mark.parametrize("option", ["--system-certs", "  --unexpected"])
def test_bundle_installer_rejects_options_as_install_paths(option: str) -> None:
    assert PWSH is not None
    result = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(INSTALLER), "-InstallDir", option],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert result.returncode != 0
    assert "InstallDir must be a filesystem path" in result.stderr
    assert "-NoSystemCertificates" in result.stderr


@pytest.mark.parametrize(
    ("user_path", "process_path", "expected_user", "expected_process"),
    [
        ("", "", r"C:\New\bin", r"C:\New\bin"),
        (
            r"C:\Old\bin;C:\New\bin;C:\Other;c:\new\bin\;;",
            r"C:\Other;c:\NEW\bin\;C:\Old\bin",
            r"C:\New\bin;C:\Old\bin;C:\Other",
            r"C:\New\bin;C:\Other;C:\Old\bin",
        ),
        (r"C:\New\bin;C:\Old", r"C:\New\bin;C:\Old", r"C:\New\bin;C:\Old", r"C:\New\bin;C:\Old"),
    ],
    ids=["empty", "duplicates-and-old-first", "already-first"],
)
def test_bundle_installer_prioritizes_path_without_duplicate_entries(
    user_path: str, process_path: str, expected_user: str, expected_process: str
) -> None:
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
function Write-Step([string]$Message) {}
$function = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Add-UserPathEntry'
}, $true)
Invoke-Expression ($function.Extent.Text.Replace('[Environment]', '[FakeEnvironment]'))
[FakeEnvironment]::UserPath = $env:TEST_USER_PATH
$env:PATH = $env:TEST_PROCESS_PATH
Add-UserPathEntry 'C:\New\bin'
$writes = [FakeEnvironment]::Writes
Add-UserPathEntry 'C:\New\bin'
@{ user = [FakeEnvironment]::UserPath; process = $env:PATH;
   idempotent = ([FakeEnvironment]::Writes -eq $writes) } | ConvertTo-Json -Compress
""",
        env={"TEST_USER_PATH": user_path, "TEST_PROCESS_PATH": process_path},
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "user": expected_user,
        "process": expected_process,
        "idempotent": True,
    }


@pytest.mark.parametrize("previous", [None, "true", "false"])
@pytest.mark.parametrize("opt_out", [False, True], ids=["system-roots", "bundled-roots"])
@pytest.mark.parametrize("outcome", ["success", "nonzero", "exception"])
def test_bundle_installer_scopes_system_certificates_and_restores_environment(
    tmp_path: Path, previous: str | None, opt_out: bool, outcome: str
) -> None:
    fake_uv = tmp_path / "fake-uv.ps1"
    observed = tmp_path / "observed.txt"
    fake_uv.write_text(
        "$env:UV_SYSTEM_CERTS | Set-Content -LiteralPath $env:TEST_CERT_OUTPUT\n"
        "if ($env:TEST_UV_OUTCOME -eq 'exception') { throw 'simulated uv failure' }\n"
        "$global:LASTEXITCODE = if ($env:TEST_UV_OUTCOME -eq 'nonzero') { 31 } else { 0 }\n",
        encoding="utf-8",
    )
    env = {
        "TEST_FAKE_UV": str(fake_uv),
        "TEST_CERT_OUTPUT": str(observed),
        "TEST_UV_OUTCOME": outcome,
        "TEST_CERT_OPT_OUT": str(opt_out).lower(),
    }
    if previous is not None:
        env["UV_SYSTEM_CERTS"] = previous
    result = run_ps(
        """
$uv = $env:TEST_FAKE_UV
$script:PythonVersion = '3.12'
$coreWheel = 'core.whl'
$clientWheel = 'client.whl'
$uiWheel = 'ui.whl'
$NoSystemCertificates = $env:TEST_CERT_OPT_OUT -eq 'true'
$assignment = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -eq '$previousUvSystemCerts'
}, $true)
$install = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.TryStatementAst]
}, $true)
$check = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.IfStatementAst] -and
    $node.Extent.Text.StartsWith('if ($uvInstallExitCode -ne 0)')
}, $true)
$failure = $null
try {
    Invoke-Expression ($assignment.Extent.Text + "`n" + $install.Extent.Text +
        "`n" + $check.Extent.Text)
} catch { $failure = $_.Exception.Message }
@{ restored = $env:UV_SYSTEM_CERTS; present = (Test-Path Env:UV_SYSTEM_CERTS);
   failure = $failure } | ConvertTo-Json -Compress
""",
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert observed.read_text(encoding="utf-8-sig").strip() == ("false" if opt_out else "true")
    details = json.loads(result.stdout)
    assert details["present"] is (previous is not None)
    assert details["restored"] == previous
    if outcome == "success":
        assert details["failure"] is None
    else:
        assert details["failure"] is not None
        expected = "could not install" if outcome == "nonzero" else "simulated uv failure"
        assert expected in details["failure"]
