#!/usr/bin/env python3
"""Check explicit Windows boundary contracts and required JUnit cases."""

from __future__ import annotations

import argparse
import ast
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


class ContractError(ValueError):
    """Invalid contract input or a contract that is not satisfied."""


_MANIFEST_KEYS = {
    "schema_version",
    "python_leaves",
    "facade_symbols",
    "frontend",
    "groups",
}
_MAX_JUNIT_BYTES = 10 * 1024 * 1024
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_MODULE_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z")
# This lightweight scan covers static imports/exports, not dynamic import().
_TS_IMPORT_RE = re.compile(
    r"(?m)^\s*(?:import|export)\b[^;]*?\bfrom\s*[\"']([^\"']+)[\"']"
    r"|^\s*import\s*[\"']([^\"']+)[\"']"
)


def _exact_keys(value: Any, keys: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ContractError(f"invalid {context} fields")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractError(f"invalid {context}")
    return value


def _repo_file(root: Path, relative: Any, context: str) -> tuple[str, Path]:
    raw = _string(relative, context)
    path = PurePosixPath(raw)
    if (
        "\x00" in raw
        or path.is_absolute()
        or "\\" in raw
        or ":" in raw
        or any(part in {"", ".", ".."} for part in raw.split("/"))
    ):
        raise ContractError(f"unsafe {context}")
    candidate = (root / Path(*path.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError(f"{context} escapes repository") from exc
    if not candidate.is_file():
        raise ContractError(f"missing {context}")
    return raw, candidate


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("cannot read contracts JSON") from exc
    manifest = _exact_keys(value, _MANIFEST_KEYS, "manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ContractError("unsupported schema_version")

    leaves = manifest["python_leaves"]
    if not isinstance(leaves, list) or not leaves:
        raise ContractError("python_leaves must be a non-empty list")
    seen_paths: set[str] = set()
    for item in leaves:
        item = _exact_keys(item, {"path", "forbidden_imports"}, "python leaf")
        file_path = _string(item["path"], "python leaf path")
        if not file_path.endswith(".py") or file_path in seen_paths:
            raise ContractError("invalid or duplicate python leaf path")
        seen_paths.add(file_path)
        _validate_string_list(item["forbidden_imports"], "forbidden_imports")
        if any(not _MODULE_RE.fullmatch(module) for module in item["forbidden_imports"]):
            raise ContractError("forbidden_imports must list exact module names")

    facades = manifest["facade_symbols"]
    if not isinstance(facades, list) or not facades:
        raise ContractError("facade_symbols must be a non-empty list")
    for item in facades:
        item = _exact_keys(item, {"path", "name"}, "facade symbol")
        _string(item["path"], "facade path")
        if not _string(item["name"], "facade symbol name").isidentifier():
            raise ContractError("invalid facade symbol name")

    frontend = _exact_keys(
        manifest["frontend"],
        {"modules", "cycle_modules", "forbidden_imports"},
        "frontend contract",
    )
    _validate_string_list(frontend["modules"], "frontend modules", nonempty=True)
    _validate_string_list(frontend["cycle_modules"], "cycle_modules", nonempty=True)
    if not set(frontend["cycle_modules"]).issubset(frontend["modules"]):
        raise ContractError("cycle_modules must be a subset of frontend modules")
    if not isinstance(frontend["forbidden_imports"], list):
        raise ContractError("frontend forbidden_imports must be a list")
    for item in frontend["forbidden_imports"]:
        item = _exact_keys(item, {"importer", "target"}, "frontend forbidden import")
        _string(item["importer"], "frontend importer")
        _string(item["target"], "frontend target")
        if (
            item["importer"] not in frontend["modules"]
            or item["target"] not in frontend["modules"]
        ):
            raise ContractError("frontend forbidden imports must reference configured modules")

    groups = manifest["groups"]
    if not isinstance(groups, dict) or not groups:
        raise ContractError("groups must be a non-empty object")
    for group_name, group in groups.items():
        if not isinstance(group_name, str) or (
            not group_name.isidentifier() and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", group_name)
        ):
            raise ContractError("invalid group name")
        group = _exact_keys(group, {"required_cases"}, "execution group")
        cases = group["required_cases"]
        if not isinstance(cases, list) or not cases:
            raise ContractError("required_cases must be a non-empty list")
        ids: set[str] = set()
        labels: set[tuple[str, str]] = set()
        for case in cases:
            case = _exact_keys(case, {"node_id", "classname", "name"}, "required case")
            node_id = _string(case["node_id"], "required node_id")
            classname = _string(case["classname"], "required classname")
            name = _string(case["name"], "required case name")
            if node_id in ids or (classname, name) in labels:
                raise ContractError("duplicate required case")
            ids.add(node_id)
            labels.add((classname, name))
    return manifest


def _validate_string_list(value: Any, context: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        raise ContractError(f"{context} must be a list")
    if any(not isinstance(item, str) or not item or item != item.strip() for item in value):
        raise ContractError(f"invalid {context} entry")
    if len(set(value)) != len(value):
        raise ContractError(f"duplicate {context} entry")


def _module_name(relative: str) -> str:
    path = PurePosixPath(relative)
    parts = list(path.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = path.stem
    return ".".join(parts)


def _python_imports(tree: ast.Module, module: str, is_package: bool) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = module.split(".") if is_package else module.split(".")[:-1]
                remove = node.level - 1
                if remove > len(base_parts):
                    continue
                base_parts = base_parts[: len(base_parts) - remove]
                base = ".".join([*base_parts, *([node.module] if node.module else [])])
            else:
                base = node.module or ""
            if base:
                imports.add(base)
            for alias in node.names:
                if alias.name != "*":
                    imports.add(f"{base}.{alias.name}" if base else alias.name)
    return imports


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                names.update(child.id for child in ast.walk(target) if isinstance(child, ast.Name))
    return names


def _ts_target(importer: str, specifier: str, module_paths: set[str]) -> str | None:
    if not specifier.startswith("."):
        return None
    normalized_text = posixpath.normpath(posixpath.join(posixpath.dirname(importer), specifier))
    if normalized_text == ".." or normalized_text.startswith(("../", "/")):
        return None
    normalized = PurePosixPath(normalized_text)
    candidates = [str(normalized)]
    if normalized.suffix == "":
        candidates.extend(str(normalized) + suffix for suffix in (".ts", ".tsx", ".js", ".jsx"))
        candidates.extend(
            str(normalized / ("index" + suffix)) for suffix in (".ts", ".tsx", ".js", ".jsx")
        )
    elif normalized.suffix in {".js", ".jsx"}:
        candidates.extend(str(normalized.with_suffix(suffix)) for suffix in (".ts", ".tsx"))
    return next((candidate for candidate in candidates if candidate in module_paths), None)


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    done: set[str] = set()
    stack: list[str] = []
    active: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            cycle = [*stack[stack.index(node) :], node]
            rotations = [
                (*cycle[index:-1], *cycle[:index], cycle[index]) for index in range(len(cycle) - 1)
            ]
            canonical = min(rotations)
            rendered = list(canonical)
            if rendered not in cycles:
                cycles.append(rendered)
            return
        if node in done:
            return
        active.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, set())):
            visit(target)
        stack.pop()
        active.remove(node)
        done.add(node)

    for start in sorted(graph):
        visit(start)
    return cycles


def audit_boundaries(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    python_checks = 0
    for leaf in manifest["python_leaves"]:
        relative, path = _repo_file(root, leaf["path"], "Python leaf")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ContractError(f"cannot parse Python leaf: {relative}") from exc
        imports = _python_imports(tree, _module_name(relative), relative.endswith("/__init__.py"))
        for forbidden in leaf["forbidden_imports"]:
            if any(
                imported == forbidden or imported.startswith(forbidden + ".")
                for imported in imports
            ):
                findings.append({"code": "forbidden-python-import", "path": relative})
        python_checks += 1

    facade_checks = 0
    for facade in manifest["facade_symbols"]:
        relative, path = _repo_file(root, facade["path"], "facade source")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ContractError(f"cannot parse facade source: {relative}") from exc
        if facade["name"] not in _top_level_names(tree):
            findings.append({"code": "missing-facade-symbol", "path": relative})
        facade_checks += 1

    frontend = manifest["frontend"]
    modules = set(frontend["modules"])
    graph: dict[str, set[str]] = {item: set() for item in frontend["cycle_modules"]}
    frontend_checks = 0
    for relative in frontend["modules"]:
        _, path = _repo_file(root, relative, "frontend module")
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ContractError(f"cannot read frontend module: {relative}") from exc
        frontend_checks += 1
        for match in _TS_IMPORT_RE.finditer(content):
            specifier = match.group(1) or match.group(2)
            target = _ts_target(relative, specifier, modules)
            if target is None:
                continue
            for rule in frontend["forbidden_imports"]:
                if relative == rule["importer"] and target == rule["target"]:
                    findings.append({"code": "forbidden-frontend-import", "path": relative})
            if relative in graph and target in graph:
                graph[relative].add(target)
    cycles = _find_cycles(graph)
    for cycle in cycles:
        findings.append({"code": "frontend-cycle", "path": cycle[0]})
    return {
        "mode": "boundaries",
        "ok": not findings,
        "checks": {
            "python_leaves": python_checks,
            "facade_symbols": facade_checks,
            "frontend_modules": frontend_checks,
        },
        "findings": findings,
    }


def _collection_ids(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ContractError("cannot read pytest collection file") from exc
    ids = [line for line in lines if line]
    if any(line != line.strip() for line in ids) or len(ids) != len(set(ids)):
        raise ContractError("invalid or duplicate pytest collection node id")
    return set(ids)


def audit_execution(
    junit_path: Path,
    group_name: str,
    manifest: dict[str, Any],
    source_sha: str,
    collection_path: Path | None = None,
) -> dict[str, Any]:
    if not _SHA_RE.fullmatch(source_sha):
        raise ContractError("source SHA must be 40 lowercase hexadecimal characters")
    groups = manifest["groups"]
    if group_name not in groups:
        raise ContractError("unknown execution group")
    required = groups[group_name]["required_cases"]
    collected = _collection_ids(collection_path) if collection_path else None
    outcomes: list[dict[str, str]] = []
    gate_findings: list[str] = []
    if collected is not None:
        gate_findings.extend(
            f"not-collected:{case['node_id']}"
            for case in required
            if case["node_id"] not in collected
        )

    try:
        raw = junit_path.read_bytes()
    except OSError as exc:
        raise ContractError("cannot read JUnit XML") from exc
    if len(raw) > _MAX_JUNIT_BYTES:
        raise ContractError("JUnit XML exceeds size limit")
    if b"\x00" in raw or re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, re.IGNORECASE):
        raise ContractError("DTD and entity declarations are not allowed")
    try:
        document = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ContractError("invalid JUnit XML") from exc
    if document.tag.rsplit("}", 1)[-1] not in {"testsuite", "testsuites"}:
        raise ContractError("invalid JUnit XML root")
    cases = [
        element for element in document.iter() if element.tag.rsplit("}", 1)[-1] == "testcase"
    ]
    labels = [(case.get("classname", ""), case.get("name", "")) for case in cases]
    duplicates = {label for label, count in Counter(labels).items() if count > 1}
    if duplicates:
        gate_findings.append("duplicate-junit-testcase")
    skipped = failures = errors = 0
    statuses: dict[tuple[str, str], str] = {}
    for case, label in zip(cases, labels, strict=True):
        children = {child.tag.rsplit("}", 1)[-1] for child in case}
        status = (
            "error"
            if "error" in children
            else "failure"
            if "failure" in children
            else "skipped"
            if "skipped" in children
            else "passed"
        )
        statuses[label] = status
        skipped += status == "skipped"
        failures += "failure" in children
        errors += "error" in children
    for required_case in required:
        label = (required_case["classname"], required_case["name"])
        status = statuses.get(label)
        if status is None:
            gate_findings.append(f"missing:{required_case['node_id']}")
            status = "missing"
        elif status != "passed":
            gate_findings.append(f"{status}:{required_case['node_id']}")
        outcomes.append({"node_id": required_case["node_id"], "status": status})
    return {
        "mode": "execution",
        "ok": not gate_findings,
        "group": group_name,
        "source_sha": {"value": source_sha, "basis": "asserted-invocation-argument"},
        "counts": {
            "total": len(cases),
            "executed": len(cases) - skipped,
            "skipped": skipped,
            "failures": failures,
            "errors": errors,
            "required": len(required),
        },
        "required_cases": outcomes,
        "findings": gate_findings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--contracts", required=True, type=Path)
    parser.add_argument("--mode", choices=("boundaries", "execution"), required=True)
    parser.add_argument("--group")
    parser.add_argument("--junit", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--collection-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = load_manifest(args.contracts)
        if args.mode == "boundaries":
            if any(
                value is not None
                for value in (args.group, args.junit, args.source_sha, args.collection_file)
            ):
                raise ContractError("execution arguments are not valid in boundaries mode")
            report = audit_boundaries(args.repository, manifest)
        else:
            if args.group is None or args.junit is None or args.source_sha is None:
                raise ContractError("execution mode requires --group, --junit, and --source-sha")
            report = audit_execution(
                args.junit,
                args.group,
                manifest,
                args.source_sha,
                args.collection_file,
            )
    except ContractError as exc:
        print(json.dumps({"mode": args.mode, "ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
