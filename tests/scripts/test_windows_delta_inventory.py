"""Contracts for the Windows owner register and review-only delta report."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "scripts" / "ci"
MAP_PATH = ROOT / "docs" / "windows" / "WINDOWS-INTEGRATION-MAP.json"
SPEC = importlib.util.spec_from_file_location("audit_windows_delta", CI / "audit-windows-delta.py")
assert SPEC is not None and SPEC.loader is not None
DELTA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DELTA)


def _register() -> dict[str, Any]:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def test_current_register_covers_all_original_and_additional_roadmap_ids() -> None:
    register = _register()
    rows = DELTA.validate_register(register)

    assert {roadmap_id for row in rows for roadmap_id in row["roadmap_ids"]} == set(range(1, 38))
    assert sum(len(row["original_ids"]) for row in rows) == 31
    assert all(
        row["windows_leaf"] is None or isinstance(row["windows_leaf"], list) for row in rows
    )


def test_all_registered_paths_exist_and_test_support_is_file_specific() -> None:
    rows = DELTA.validate_register(_register())

    for row in rows:
        for field in ("shared_caller", "windows_leaf", "test_support"):
            for relative_path in row[field] or []:
                path = ROOT.joinpath(*relative_path.split("/"))
                assert path.exists(), f"{relative_path} does not exist under {ROOT}"
        for relative_path in row["test_support"]:
            path = ROOT.joinpath(*relative_path.split("/"))
            assert path.is_file(), f"test support must name a file: {relative_path}"


def test_corrected_original_ids_maintained_seams_and_shared_owners() -> None:
    rows = DELTA.validate_register(_register())
    by_id = {roadmap_id: row for row in rows for roadmap_id in row["roadmap_ids"]}

    assert by_id[30]["original_ids"] == [30]
    for roadmap_id in (19, 20, 23, 24, 28):
        assert by_id[roadmap_id]["status"] == "maintain"
        assert by_id[roadmap_id]["disposition"] == "MAINTAIN"

    capture_bridge = "omnigent/terminals/capture_bridge.py"
    for roadmap_id in (3, 21, 29):
        assert capture_bridge in by_id[roadmap_id]["shared_caller"]
        assert capture_bridge not in (by_id[roadmap_id]["windows_leaf"] or [])

    sandbox_capabilities = "omnigent/inner/sandbox_capabilities.py"
    assert sandbox_capabilities in by_id[26]["shared_caller"]
    assert sandbox_capabilities not in (by_id[26]["windows_leaf"] or [])


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        (
            (
                b"A\0new name \xe2\x98\x83.txt\0D\0old file.txt\0"
                b"R100\0old path.txt\0new path \xe2\x98\x83.txt\0"
            ),
            [
                {"status": "A", "old_path": None, "new_path": "new name \u2603.txt"},
                {"status": "D", "old_path": "old file.txt", "new_path": None},
                {
                    "status": "R100",
                    "old_path": "old path.txt",
                    "new_path": "new path \u2603.txt",
                },
            ],
        ),
        (b"", []),
    ],
)
def test_nul_parser_handles_add_delete_rename_spaces_unicode_and_empty(
    output: bytes, expected: list[dict[str, str | None]]
) -> None:
    assert DELTA.parse_name_status(output) == expected


@pytest.mark.parametrize(
    "output",
    [
        b"M\0unterminated",
        b"R100\0old only\0",
        b"Q\0unsupported\0",
        b"M\0\0",
        b"R101\0old\0new\0",
        b"M\0one\0extra\0",
    ],
)
def test_nul_parser_rejects_malformed_records(output: bytes) -> None:
    with pytest.raises(DELTA.WindowsDeltaError):
        DELTA.parse_name_status(output)


def test_directory_ownership_matches_changed_files_and_rename_endpoints() -> None:
    assert DELTA.paths_overlap("tests/inner/test_x.py", "tests/inner")
    assert DELTA.paths_overlap("old/name.py", "old/name.py")
    assert not DELTA.paths_overlap("tests/innerx/test_x.py", "tests/inner")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        ("duplicate_id", "Duplicate roadmap ID"),
        ("traversal", "traversal segments"),
        ("bad_disposition", "disposition"),
        ("unknown_field", "missing or unknown fields"),
        ("bad_sha", "published_result_sha"),
    ],
)
def test_register_rejects_duplicate_ids_traversal_and_invalid_values(
    mutate: str, message: str
) -> None:
    register = copy.deepcopy(_register())
    if mutate == "duplicate_id":
        register["boundaries"][1]["roadmap_ids"].append(1)
        register["boundaries"][1]["original_ids"].append(1)
    elif mutate == "traversal":
        register["boundaries"][0]["shared_caller"] = ["../outside"]
    elif mutate == "bad_disposition":
        register["boundaries"][0]["disposition"] = "DROP-UPSTREAM-COVERS"
    elif mutate == "unknown_field":
        register["boundaries"][0]["future_field"] = True
    else:
        register["boundaries"][0]["published_result_sha"] = "future-sha"

    with pytest.raises(DELTA.WindowsDeltaError, match=message):
        DELTA.validate_register(register)


def test_register_rejects_missing_ids_and_wrong_schema_version() -> None:
    missing = _register()
    missing["boundaries"].pop()
    with pytest.raises(DELTA.WindowsDeltaError, match="does not cover roadmap IDs"):
        DELTA.validate_register(missing)

    wrong_version = _register()
    wrong_version["schema_version"] = 2
    with pytest.raises(DELTA.WindowsDeltaError, match="schema_version"):
        DELTA.validate_register(wrong_version)
