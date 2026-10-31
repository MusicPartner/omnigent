"""Audit platform marker ownership against the pinned upstream test sources."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "platform-markers.bfd8.json"


class PlatformMarkerAuditError(RuntimeError):
    """The candidate changed a pinned test owner or its platform markers."""


def _test_functions(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def _decorators(tree: ast.AST) -> dict[str, list[str]]:
    return {
        name: [ast.dump(decorator) for decorator in node.decorator_list]
        for name, node in _test_functions(tree).items()
    }


def _snapshot(tree: ast.AST) -> tuple[int, str]:
    serialized = json.dumps(_decorators(tree), sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return len(_test_functions(tree)), hashlib.sha256(serialized).hexdigest()


def _expression(source: str) -> str:
    return ast.dump(ast.parse(source, mode="eval").body)


def _expected_additions(path: str, name: str, fixture: dict[str, Any]) -> set[str]:
    expected: set[str] = set()
    if name in fixture.get("expectedPosix", {}).get(path, []):
        expected.add(_expression("pytest.mark.posix_only"))
    if name in fixture.get("expectedWindowsMatrix", {}).get(path, []):
        windows_matrix = 'pytest.mark.parametrize("windows", [False, True], ids=["tmux", "psmux"])'
        expected.add(_expression(windows_matrix))
    return expected


def audit_source_pair(
    path: str,
    baseline_source: bytes | str,
    candidate_source: bytes | str,
    fixture: dict[str, Any],
) -> int:
    baseline = ast.parse(baseline_source, filename=f"{path} (pinned baseline)")
    candidate = ast.parse(candidate_source, filename=f"{path} (candidate)")
    before = _test_functions(baseline)
    after = _test_functions(candidate)
    missing = before.keys() - after.keys()
    if missing:
        raise PlatformMarkerAuditError(f"{path}: missing test symbols: {sorted(missing)}")

    gateway = fixture.get("gatewayFailure")
    target_gateway = _expression(gateway["target"]) if gateway else None
    portable_gateway = _expression(gateway["portable"]) if gateway else None
    for name in before:
        baseline_marks = {ast.dump(mark) for mark in before[name].decorator_list}
        result_marks = {ast.dump(mark) for mark in after[name].decorator_list}
        if gateway and path == gateway["path"] and name == gateway["test"]:
            if target_gateway not in baseline_marks:
                raise PlatformMarkerAuditError(
                    f"{path}:{name}: pinned gateway parameterization changed"
                )
            if portable_gateway not in result_marks:
                raise PlatformMarkerAuditError(f"{path}:{name}: portable gateway cases changed")
            baseline_marks = (baseline_marks - {target_gateway}) | {portable_gateway}
        if not baseline_marks <= result_marks:
            raise PlatformMarkerAuditError(f"{path}:{name}: lost decorator")
        expected = _expected_additions(path, name, fixture)
        if result_marks - baseline_marks != expected:
            raise PlatformMarkerAuditError(f"{path}:{name}: unexpected or misplaced decorators")
    return len(before)


def _read_fixture(fixture_path: Path) -> dict[str, Any]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(fixture, dict) or not isinstance(fixture.get("snapshots"), dict):
        raise PlatformMarkerAuditError("Platform marker fixture is malformed.")
    return fixture


def audit_repository(
    repository_root: Path,
    baseline_sha: str,
    fixture_path: Path = FIXTURE_PATH,
) -> list[str]:
    fixture = _read_fixture(fixture_path)
    if baseline_sha != fixture.get("baselineSha"):
        raise PlatformMarkerAuditError(
            "The platform marker baseline SHA does not match the pinned fixture."
        )
    results = []
    for path, expected in fixture["snapshots"].items():
        baseline_source = subprocess.check_output(
            ["git", "show", f"{baseline_sha}:{path}"], cwd=repository_root
        )
        baseline_tree = ast.parse(baseline_source, filename=f"{baseline_sha}:{path}")
        if _snapshot(baseline_tree) != (
            expected["testCount"],
            expected["testDecoratorsSha256"],
        ):
            raise PlatformMarkerAuditError(
                f"{path}: pinned baseline no longer matches the fixture."
            )
        candidate_source = (repository_root / path).read_text(encoding="utf-8")
        count = audit_source_pair(path, baseline_source, candidate_source, fixture)
        results.append(f"{path}: {count} target tests retained; marker owners audited")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    try:
        for result in audit_repository(
            arguments.repository_root.resolve(), arguments.baseline_sha
        ):
            print(result)
    except (
        OSError,
        subprocess.CalledProcessError,
        SyntaxError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Platform marker audit failed: {error}", file=sys.stderr)
        return 1
    except PlatformMarkerAuditError as error:
        print(f"Platform marker audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
