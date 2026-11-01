"""Report review-only owner and path overlaps across Windows integration refs.

The audit reads Git metadata and a versioned owner register. It does not read
tracked file contents, mutate Git, check out refs, or decide reconciliation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
ROADMAP_IDS = set(range(1, 38))
REGISTER_KEYS = {"schema_version", "boundaries"}
BOUNDARY_KEYS = {
    "roadmap_ids",
    "original_ids",
    "boundary",
    "ownership",
    "shared_caller",
    "windows_leaf",
    "test_support",
    "status",
    "disposition",
    "published_result_sha",
}
STATUSES = {"local", "planned", "published", "maintain", "project"}
DISPOSITIONS = {"REVIEW", "MAINTAIN", "PROJECT"}
FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
RENAME_STATUS = re.compile(r"[RC](\d{1,3})\Z")


class WindowsDeltaError(ValueError):
    """Owner register or Git metadata could not be safely audited."""


def _validate_path(value: Any, *, context: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise WindowsDeltaError(f"{context} must be a repository-relative POSIX path.")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise WindowsDeltaError(f"{context} must not be absolute.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise WindowsDeltaError(f"{context} must not contain empty, dot, or traversal segments.")
    if PurePosixPath(value).is_absolute():
        raise WindowsDeltaError(f"{context} must not be absolute.")
    return value


def _validate_path_list(value: Any, *, context: str) -> list[str]:
    if not isinstance(value, list):
        raise WindowsDeltaError(f"{context} must be a list of paths.")
    paths = [_validate_path(path, context=context) for path in value]
    if len(paths) != len(set(paths)):
        raise WindowsDeltaError(f"{context} contains a duplicate path.")
    return paths


def validate_register(register: Any) -> list[dict[str, Any]]:
    """Validate the complete v1 register and return its boundary rows."""
    if not isinstance(register, dict) or set(register) != REGISTER_KEYS:
        raise WindowsDeltaError("Owner register must contain only schema_version and boundaries.")
    if type(register["schema_version"]) is not int or register["schema_version"] != SCHEMA_VERSION:
        raise WindowsDeltaError(f"Owner register schema_version must be {SCHEMA_VERSION}.")
    boundaries = register["boundaries"]
    if not isinstance(boundaries, list) or not boundaries:
        raise WindowsDeltaError("Owner register boundaries must be a non-empty list.")

    seen_ids: set[int] = set()
    validated: list[dict[str, Any]] = []
    for index, row in enumerate(boundaries):
        context = f"boundaries[{index}]"
        if not isinstance(row, dict):
            raise WindowsDeltaError(f"{context} must be an object.")
        keys = set(row)
        required = BOUNDARY_KEYS - {"published_result_sha"}
        if not required <= keys or keys - BOUNDARY_KEYS:
            raise WindowsDeltaError(f"{context} has missing or unknown fields.")

        ids = row["roadmap_ids"]
        if not isinstance(ids, list) or not ids or any(type(item) is not int for item in ids):
            raise WindowsDeltaError(f"{context}.roadmap_ids must be a non-empty integer list.")
        if len(ids) != len(set(ids)):
            raise WindowsDeltaError(f"{context}.roadmap_ids contains a duplicate ID.")
        for roadmap_id in ids:
            if roadmap_id not in ROADMAP_IDS:
                raise WindowsDeltaError(f"{context}.roadmap_ids contains an unknown ID.")
            if roadmap_id in seen_ids:
                raise WindowsDeltaError(f"Duplicate roadmap ID {roadmap_id}.")
            seen_ids.add(roadmap_id)

        original_ids = row["original_ids"]
        expected_original_ids = [item for item in ids if item <= 31]
        if (
            not isinstance(original_ids, list)
            or any(type(item) is not int for item in original_ids)
            or len(original_ids) != len(set(original_ids))
            or original_ids != expected_original_ids
        ):
            raise WindowsDeltaError(
                f"{context}.original_ids must list its original roadmap IDs in order."
            )

        for field in ("boundary", "ownership"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise WindowsDeltaError(f"{context}.{field} must be a non-empty string.")
        shared_paths = _validate_path_list(
            row["shared_caller"], context=f"{context}.shared_caller"
        )
        test_paths = _validate_path_list(row["test_support"], context=f"{context}.test_support")
        windows_leaf = row["windows_leaf"]
        leaf_paths = (
            []
            if windows_leaf is None
            else _validate_path_list(windows_leaf, context=f"{context}.windows_leaf")
        )
        all_paths = shared_paths + leaf_paths + test_paths
        if len(all_paths) != len(set(all_paths)):
            raise WindowsDeltaError(f"{context} declares a path more than once.")
        if not isinstance(row["status"], str) or row["status"] not in STATUSES:
            raise WindowsDeltaError(f"{context}.status is not a supported status.")
        if not isinstance(row["disposition"], str) or row["disposition"] not in DISPOSITIONS:
            raise WindowsDeltaError(f"{context}.disposition must be REVIEW, MAINTAIN, or PROJECT.")
        if "published_result_sha" in row:
            result_sha = row["published_result_sha"]
            if (
                row["status"] != "published"
                or not isinstance(result_sha, str)
                or not FULL_SHA.fullmatch(result_sha)
            ):
                raise WindowsDeltaError(
                    f"{context}.published_result_sha must be a full lowercase SHA "
                    "on a published row."
                )
        validated.append(row)

    missing_ids = sorted(ROADMAP_IDS - seen_ids)
    if missing_ids:
        raise WindowsDeltaError(f"Owner register does not cover roadmap IDs: {missing_ids}.")
    return validated


def load_register(path: Path) -> list[dict[str, Any]]:
    """Read and validate a UTF-8 JSON owner register."""
    try:
        register = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WindowsDeltaError("Cannot read owner register as UTF-8 JSON.") from error
    return validate_register(register)


def parse_name_status(output: bytes) -> list[dict[str, str | None]]:
    """Parse Git's NUL-delimited --name-status records, including renames."""
    if not output:
        return []
    if not output.endswith(b"\0"):
        raise WindowsDeltaError("Git name-status output is missing its final NUL delimiter.")
    fields = output.split(b"\0")[:-1]
    changes: list[dict[str, str | None]] = []
    cursor = 0
    while cursor < len(fields):
        try:
            status = fields[cursor].decode("ascii")
        except UnicodeDecodeError as error:
            raise WindowsDeltaError("Git returned a malformed change status.") from error
        cursor += 1
        rename_match = RENAME_STATUS.fullmatch(status)
        if rename_match is not None:
            if int(rename_match.group(1)) > 100:
                raise WindowsDeltaError("Git returned an invalid rename/copy score.")
            path_count = 2
        elif status in {"A", "D", "M", "T", "U", "X", "B"}:
            path_count = 1
        else:
            raise WindowsDeltaError("Git returned an unsupported change status.")
        if cursor + path_count > len(fields):
            raise WindowsDeltaError("Git name-status output ended before all paths were present.")
        encoded_paths = fields[cursor : cursor + path_count]
        cursor += path_count
        if any(not path for path in encoded_paths):
            raise WindowsDeltaError("Git name-status output contains an empty path.")
        paths = [os.fsdecode(path) for path in encoded_paths]
        if status == "A":
            old_path, new_path = None, paths[0]
        elif status == "D":
            old_path, new_path = paths[0], None
        elif rename_match is not None:
            old_path, new_path = paths
        else:
            old_path = new_path = paths[0]
        changes.append({"status": status, "old_path": old_path, "new_path": new_path})
    return sorted(changes, key=_change_sort_key)


def _change_sort_key(change: dict[str, str | None]) -> tuple[str, str, str]:
    return (
        change["old_path"] or "",
        change["new_path"] or "",
        change["status"] or "",
    )


def paths_overlap(first: str, second: str) -> bool:
    """Return true for equal paths or when one declared path is a directory prefix."""
    first = first.rstrip("/")
    second = second.rstrip("/")
    return first == second or first.startswith(second + "/") or second.startswith(first + "/")


def _change_paths(change: dict[str, str | None]) -> list[str]:
    return [path for path in (change["old_path"], change["new_path"]) if path is not None]


def _row_paths(row: dict[str, Any]) -> list[str]:
    paths = list(row["shared_caller"]) + list(row["test_support"])
    if row["windows_leaf"] is not None:
        paths.extend(row["windows_leaf"])
    return paths


def _run_git(repository: Path, *arguments: str) -> bytes:
    inherited_keys = (
        "COMSPEC",
        "HOME",
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "WINDIR",
    )
    environment = {key: os.environ[key] for key in inherited_keys if key in os.environ}
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            env=environment,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise WindowsDeltaError("Cannot execute Git.") from error
    if completed.returncode != 0:
        raise WindowsDeltaError(f"Git metadata command failed (exit {completed.returncode}).")
    return completed.stdout


def _repository_root(repository: Path) -> Path:
    try:
        explicit_root = repository.resolve(strict=True)
    except OSError as error:
        raise WindowsDeltaError("Repository path does not exist.") from error
    if not explicit_root.is_dir():
        raise WindowsDeltaError("Repository path is not a directory.")
    git_root = os.fsdecode(_run_git(explicit_root, "rev-parse", "--show-toplevel")).strip()
    try:
        resolved_git_root = Path(git_root).resolve(strict=True)
    except OSError as error:
        raise WindowsDeltaError("Git did not resolve a repository root.") from error
    if resolved_git_root != explicit_root:
        raise WindowsDeltaError("--repository must name the Git repository root.")
    return explicit_root


def _validate_commit(repository: Path, sha: str) -> None:
    if not isinstance(sha, str) or not FULL_SHA.fullmatch(sha):
        raise WindowsDeltaError("Commit arguments must be full lowercase 40-character SHAs.")
    resolved = os.fsdecode(
        _run_git(repository, "rev-parse", "--verify", f"{sha}^{{commit}}")
    ).strip()
    if resolved != sha:
        raise WindowsDeltaError("A supplied SHA does not resolve to that exact commit.")


def _diff(repository: Path, before: str, after: str, source: str) -> list[dict[str, Any]]:
    raw = _run_git(
        repository,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--name-status",
        "-z",
        "-M",
        before,
        after,
        "--",
    )
    return [{"source": source, **change} for change in parse_name_status(raw)]


def build_report(
    repository: Path,
    base_sha: str,
    fork_sha: str,
    target_sha: str,
    boundaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare cumulative fork and target changes without deciding their disposition."""
    validated = validate_register({"schema_version": SCHEMA_VERSION, "boundaries": boundaries})
    root = _repository_root(repository)
    for sha in (base_sha, fork_sha, target_sha):
        _validate_commit(root, sha)

    fork_changes = _diff(root, base_sha, fork_sha, "fork_cumulative_base_to_fork")
    target_changes = _diff(root, base_sha, target_sha, "upstream_target_base_to_target")
    fork_records: list[dict[str, Any]] = []
    for change in fork_changes:
        paths = _change_paths(change)
        owners = [
            row
            for row in validated
            if any(
                paths_overlap(changed, declared)
                for changed in paths
                for declared in _row_paths(row)
            )
        ]
        overlaps = [
            target
            for target in target_changes
            if any(
                paths_overlap(fork_path, target_path)
                for fork_path in paths
                for target_path in _change_paths(target)
            )
        ]
        fork_records.append(
            {
                **change,
                "owner_roadmap_ids": sorted(
                    roadmap_id for row in owners for roadmap_id in row["roadmap_ids"]
                ),
                "owner_boundaries": sorted(row["boundary"] for row in owners),
                "mapping": "MAPPED" if owners else "UNMAPPED_REVIEW",
                "overlap_review": [
                    {
                        "source": target["source"],
                        "status": target["status"],
                        "old_path": target["old_path"],
                        "new_path": target["new_path"],
                    }
                    for target in overlaps
                ],
            }
        )

    return {
        "schema_version": 1,
        "refs": {"base_sha": base_sha, "fork_sha": fork_sha, "target_sha": target_sha},
        "counts": {
            "fork_cumulative": len(fork_records),
            "upstream_target": len(target_changes),
            "mapped_fork": sum(record["mapping"] == "MAPPED" for record in fork_records),
            "unmapped_review": sum(
                record["mapping"] == "UNMAPPED_REVIEW" for record in fork_records
            ),
            "path_overlap_reviews": sum(bool(record["overlap_review"]) for record in fork_records),
        },
        "policy": {
            "unmapped_fork_change": "REVIEW",
            "path_overlap": "review signal only; not a conflict or reconciliation verdict",
            "owner_disposition": "no automatic DROP or RECONCILE decisions",
        },
        "fork_cumulative": fork_records,
        "upstream_target": target_changes,
    }


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository", type=Path, required=True, help="explicit Git repository root"
    )
    parser.add_argument("--base-sha", required=True, help="full lowercase base commit SHA")
    parser.add_argument("--fork-sha", required=True, help="full lowercase fork commit SHA")
    parser.add_argument("--target-sha", required=True, help="full lowercase target commit SHA")
    parser.add_argument(
        "--map", dest="map_path", type=Path, required=True, help="v1 owner register JSON"
    )
    parser.add_argument("--output", type=Path, help="write JSON here; stdout is the default")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the read-only delta report CLI."""
    arguments = _arguments(argv)
    try:
        report = build_report(
            arguments.repository,
            arguments.base_sha,
            arguments.fork_sha,
            arguments.target_sha,
            load_register(arguments.map_path),
        )
        rendered = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        if arguments.output is None:
            sys.stdout.write(rendered)
        else:
            try:
                with arguments.output.open("w", encoding="utf-8", newline="\n") as output_file:
                    output_file.write(rendered)
            except OSError as error:
                raise WindowsDeltaError("Cannot write the explicit output path.") from error
    except WindowsDeltaError as error:
        print(f"Windows delta audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
