"""Unit coverage for the bounded Windows contract auditor."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "ci" / "audit-windows-contracts.py"
CONTRACTS = ROOT / ".github" / "scripts" / "ci" / "windows-contracts.json"
_SPEC = importlib.util.spec_from_file_location("audit_windows_contracts", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
AUDITOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(AUDITOR)


def _manifest() -> dict:
    return copy.deepcopy(AUDITOR.load_manifest(CONTRACTS))


def _write_contracts(path: Path, manifest: dict) -> Path:
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


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


def _junit(path: Path, records: list[tuple[str, str, str]]) -> Path:
    suite = ET.Element("testsuite")
    for classname, name, status in records:
        case = ET.SubElement(suite, "testcase", classname=classname, name=name)
        if status != "passed":
            ET.SubElement(case, status, message=f"synthetic {status}")
    wrapper = ET.Element("testsuites")
    wrapper.append(suite)
    path.write_bytes(ET.tostring(wrapper, encoding="utf-8"))
    return path


def _required_records(status: str = "passed") -> list[tuple[str, str, str]]:
    required = _manifest()["groups"]["windows-status-fallback"]["required_cases"]
    return [(case["classname"], case["name"], status) for case in required]


def test_manifest_is_versioned_and_uses_exact_leaf_import_rules() -> None:
    manifest = _manifest()

    assert manifest["schema_version"] == 1
    assert {leaf["path"] for leaf in manifest["python_leaves"]} == {
        "omnigent/inner/pi_windows.py",
        "omnigent/native/windows_cost_popup.py",
        "omnigent/inner/_windows_shutdown.py",
        "omnigent/harnesses/claude_native/windows_hooks.py",
        "omnigent/runner/native/windows_env.py",
        "omnigent/inner/windows_attachments.py",
    }
    assert "omnigent.inner.pi_executor" in manifest["python_leaves"][0]["forbidden_imports"]


def test_boundaries_pass_on_synthetic_leaf_and_facade_sources(tmp_path: Path) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert report["ok"]
    assert report["checks"] == {"python_leaves": 6, "facade_symbols": 2, "frontend_modules": 3}
    assert report["findings"] == []


def test_python_leaf_cannot_import_its_caller(tmp_path: Path) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    path = tmp_path / manifest["python_leaves"][0]["path"]
    path.write_text("from omnigent.inner import pi_executor\n", encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert {finding["code"] for finding in report["findings"]} == {"forbidden-python-import"}


@pytest.mark.parametrize(
    ("source", "is_forbidden"),
    [
        ("import omnigent.inner.pi_executor.helpers\n", True),
        ("from omnigent.inner.pi_executor.helpers import helper\n", True),
        ("from .pi_executor.helpers import helper\n", True),
        ("import omnigent.inner.pi_executor_extra\n", False),
    ],
)
def test_python_leaf_forbidden_import_matches_module_prefix_only(
    tmp_path: Path, source: str, is_forbidden: bool
) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    path = tmp_path / manifest["python_leaves"][0]["path"]
    path.write_text(source, encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    codes = {item["code"] for item in report["findings"]}
    assert ("forbidden-python-import" in codes) is is_forbidden


def test_python_leaf_may_import_shared_modules_and_platform_primitives(tmp_path: Path) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    path = tmp_path / manifest["python_leaves"][0]["path"]
    path.write_text("import os\nimport omnigent.inner.shared_helper\n", encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert report["ok"]


def test_missing_public_facade_symbol_is_reported(tmp_path: Path) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    facade = manifest["facade_symbols"][0]
    (tmp_path / facade["path"]).write_text("def another_name():\n    pass\n", encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert {finding["code"] for finding in report["findings"]} == {"missing-facade-symbol"}


def test_frontend_picker_dependency_and_cycle_are_reported(tmp_path: Path) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    host_paths, breadcrumbs, picker = manifest["frontend"]["modules"]
    (tmp_path / host_paths).write_text('import "./workspaceBreadcrumbs";\n', encoding="utf-8")
    (tmp_path / breadcrumbs).write_text(
        'import "./hostPaths";\nimport "./WorkspacePicker";\n', encoding="utf-8"
    )
    (tmp_path / picker).write_text("export {};\n", encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert {finding["code"] for finding in report["findings"]} == {
        "frontend-cycle",
        "forbidden-frontend-import",
    }


@pytest.mark.parametrize(
    "source",
    [
        'export { WorkspacePicker } from "./nested/../WorkspacePicker";\n',
        'import "./nested/../WorkspacePicker";\n',
    ],
)
def test_frontend_static_reexport_and_side_effect_import_paths_are_normalized(
    tmp_path: Path, source: str
) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    host_paths = manifest["frontend"]["modules"][0]
    (tmp_path / host_paths).write_text(source, encoding="utf-8")

    report = AUDITOR.audit_boundaries(tmp_path, manifest)

    assert {item["code"] for item in report["findings"]} == {"forbidden-frontend-import"}


def test_frontend_relative_import_target_cannot_escape_repository() -> None:
    target = AUDITOR._ts_target(
        "web/src/shell/hostPaths.ts",
        "../../../../outside",
        {"../outside.ts"},
    )

    assert target is None


@pytest.mark.parametrize(
    ("graph", "expected"),
    [
        ({"a": set(), "b": {"c"}, "c": {"b"}}, [["b", "c", "b"]]),
        ({"a": {"a"}}, [["a", "a"]]),
        ({"b": {"a"}, "a": {"b"}, "c": {"a", "b"}}, [["a", "b", "a"]]),
        (
            {"d": {"c"}, "c": {"d"}, "b": {"a"}, "a": {"b"}},
            [["a", "b", "a"], ["c", "d", "c"]],
        ),
    ],
)
def test_frontend_cycles_are_canonical_and_cover_disconnected_graphs(
    graph: dict[str, set[str]], expected: list[list[str]]
) -> None:
    assert AUDITOR._find_cycles(graph) == expected
    assert AUDITOR._find_cycles(dict(reversed(list(graph.items())))) == expected


def test_execution_passes_required_cases_inside_nested_junit_suites(tmp_path: Path) -> None:
    junit = _junit(tmp_path / "results.xml", _required_records())
    sha = "a" * 40

    report = AUDITOR.audit_execution(junit, "windows-status-fallback", _manifest(), sha)

    assert report["ok"]
    assert report["counts"] == {
        "total": 3,
        "executed": 3,
        "skipped": 0,
        "failures": 0,
        "errors": 0,
        "required": 3,
    }
    assert report["source_sha"] == {"value": sha, "basis": "asserted-invocation-argument"}


def test_unrelated_junit_outcomes_are_counted_but_do_not_expand_required_gate(
    tmp_path: Path,
) -> None:
    records = [
        *_required_records(),
        ("unrelated.module", "unrelated_failure", "failure"),
        ("unrelated.module", "unrelated_skip", "skipped"),
    ]

    report = AUDITOR.audit_execution(
        _junit(tmp_path / "results.xml", records),
        "windows-status-fallback",
        _manifest(),
        "a" * 40,
    )

    assert report["ok"]
    assert report["counts"]["total"] == 5
    assert report["counts"]["executed"] == 4
    assert report["counts"]["skipped"] == 1
    assert report["counts"]["failures"] == 1


@pytest.mark.parametrize("status", ["skipped", "failure", "error"])
def test_execution_rejects_nonpassing_required_case(tmp_path: Path, status: str) -> None:
    records = _required_records()
    records[0] = (*records[0][:2], status)
    report = AUDITOR.audit_execution(
        _junit(tmp_path / "results.xml", records),
        "windows-status-fallback",
        _manifest(),
        "b" * 40,
    )

    assert not report["ok"]
    assert report["required_cases"][0]["status"] == status


def test_execution_rejects_missing_or_duplicate_required_cases(tmp_path: Path) -> None:
    records = _required_records()
    missing = AUDITOR.audit_execution(
        _junit(tmp_path / "missing.xml", records[:-1]),
        "windows-status-fallback",
        _manifest(),
        "c" * 40,
    )
    duplicate = AUDITOR.audit_execution(
        _junit(tmp_path / "duplicate.xml", [*records, records[0]]),
        "windows-status-fallback",
        _manifest(),
        "c" * 40,
    )

    assert any(item.startswith("missing:") for item in missing["findings"])
    assert "duplicate-junit-testcase" in duplicate["findings"]


def test_execution_rejects_deselected_required_case(tmp_path: Path) -> None:
    required = _manifest()["groups"]["windows-status-fallback"]["required_cases"]
    collection = tmp_path / "collected.txt"
    collection.write_text("\n".join(case["node_id"] for case in required[:-1]), encoding="utf-8")

    report = AUDITOR.audit_execution(
        _junit(tmp_path / "results.xml", _required_records()),
        "windows-status-fallback",
        _manifest(),
        "d" * 40,
        collection,
    )

    assert not report["ok"]
    assert any(item.startswith("not-collected:") for item in report["findings"])


@pytest.mark.parametrize(
    ("sha", "xml", "message"),
    [
        ("not-a-sha", b"<testsuites/>", "source SHA"),
        ("e" * 40, b"<testsuites>", "invalid JUnit"),
        ("e" * 40, b"<!DOCTYPE x [<!ENTITY e 'x'>]><testsuites/>", "DTD"),
        ("e" * 40, "<?xml version='1.0' encoding='utf-16'?><testsuites/>".encode("utf-16"), "DTD"),
    ],
)
def test_execution_rejects_invalid_sha_or_unsafe_xml(
    tmp_path: Path, sha: str, xml: bytes, message: str
) -> None:
    junit = tmp_path / "invalid.xml"
    junit.write_bytes(xml)

    with pytest.raises(AUDITOR.ContractError, match=message):
        AUDITOR.audit_execution(junit, "windows-status-fallback", _manifest(), sha)


def test_manifest_rejects_unknown_fields_and_unsafe_paths(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["unexpected"] = True
    with pytest.raises(AUDITOR.ContractError, match="manifest fields"):
        AUDITOR.load_manifest(_write_contracts(tmp_path / "extra.json", manifest))

    manifest = _manifest()
    manifest["python_leaves"][0]["path"] = "../outside.py"
    _synthetic_repository(tmp_path, _manifest())
    with pytest.raises(AUDITOR.ContractError, match="unsafe Python leaf"):
        AUDITOR.audit_boundaries(tmp_path, manifest)


@pytest.mark.parametrize(
    "path",
    [
        "omnigent/inner/./pi_windows.py",
        "omnigent//inner/pi_windows.py",
        "omnigent/inner/\x00pi_windows.py",
    ],
)
def test_manifest_rejects_unsafe_raw_paths_that_alias_valid_paths(
    tmp_path: Path, path: str
) -> None:
    manifest = _manifest()
    _synthetic_repository(tmp_path, manifest)
    manifest["python_leaves"][0]["path"] = path

    with pytest.raises(AUDITOR.ContractError, match="unsafe Python leaf"):
        AUDITOR.audit_boundaries(tmp_path, manifest)


def test_manifest_rejects_wildcard_import_patterns(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["python_leaves"][0]["forbidden_imports"] = ["omnigent.inner.*"]

    with pytest.raises(AUDITOR.ContractError, match="exact module names"):
        AUDITOR.load_manifest(_write_contracts(tmp_path / "wildcard.json", manifest))
