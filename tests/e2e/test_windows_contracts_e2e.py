"""Exercise the contract auditor entry point without a server or model."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "ci" / "audit-windows-contracts.py"
CONTRACTS = ROOT / ".github" / "scripts" / "ci" / "windows-contracts.json"


@pytest.fixture(autouse=True)
def _enforce_min_server_version() -> None:
    """This subprocess-only scenario has no live server version to enforce."""


def _synthetic_repository(root: Path, manifest: dict) -> None:
    for leaf in manifest["python_leaves"]:
        path = root / leaf["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")
    for facade in manifest["facade_symbols"]:
        path = root / facade["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"def {facade['name']}():\n    return None\n", encoding="utf-8")
    for module in manifest["frontend"]["modules"]:
        path = root / module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("export {};\n", encoding="utf-8")


def _invoke(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("ANTHROPIC_API_KEY", None)
    environment.pop("GEMINI_API_KEY", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )


def test_auditor_cli_checks_synthetic_boundaries_and_required_junit_cases(tmp_path: Path) -> None:
    manifest = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    synthetic_root = tmp_path / "repo"
    synthetic_root.mkdir()
    _synthetic_repository(synthetic_root, manifest)
    contracts_path = tmp_path / "contracts.json"
    contracts_path.write_text(json.dumps(manifest), encoding="utf-8")

    boundaries = _invoke(
        "--repository",
        str(synthetic_root),
        "--contracts",
        str(contracts_path),
        "--mode",
        "boundaries",
    )
    assert boundaries.returncode == 0, boundaries.stderr
    boundary_report = json.loads(boundaries.stdout)
    assert boundary_report["ok"] is True
    assert boundary_report["checks"]["python_leaves"] == 6

    junit = tmp_path / "results.xml"
    suite = ET.Element("testsuite")
    for case in manifest["groups"]["windows-status-fallback"]["required_cases"]:
        ET.SubElement(suite, "testcase", classname=case["classname"], name=case["name"])
    wrapper = ET.Element("testsuites")
    wrapper.append(suite)
    junit.write_bytes(ET.tostring(wrapper, encoding="utf-8"))
    collected = tmp_path / "collected.txt"
    collected.write_text(
        "\n".join(
            case["node_id"]
            for case in manifest["groups"]["windows-status-fallback"]["required_cases"]
        ),
        encoding="utf-8",
    )
    execution = _invoke(
        "--repository",
        str(synthetic_root),
        "--contracts",
        str(contracts_path),
        "--mode",
        "execution",
        "--group",
        "windows-status-fallback",
        "--junit",
        str(junit),
        "--source-sha",
        "f" * 40,
        "--collection-file",
        str(collected),
    )
    assert execution.returncode == 0, execution.stderr
    execution_report = json.loads(execution.stdout)
    assert execution_report["ok"] is True
    assert execution_report["counts"]["required"] == 3
    assert execution_report["source_sha"]["basis"] == "asserted-invocation-argument"
