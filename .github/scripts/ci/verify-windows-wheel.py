"""Verify the existing Windows core-wheel resources and console entry points."""

from __future__ import annotations

import argparse
import configparser
import glob
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path


class WheelVerificationError(RuntimeError):
    """The built core wheel does not satisfy the existing release checks."""


def verify_wheel(dist_directory: Path, *, expected_version: str, source_sha: str) -> str:
    if not expected_version or any(character in expected_version for character in "\r\n"):
        raise WheelVerificationError("An explicit expected version is required.")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise WheelVerificationError("An explicit full source SHA is required.")

    wheels = sorted(glob.glob(str(dist_directory / "omnigent-*.whl")))
    if not wheels:
        raise WheelVerificationError("no core omnigent wheel found")
    wheel = wheels[-1]
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            native = "omnigent/resources/windows_launcher/"
            manifest = json.loads(archive.read(native + "manifest.json"))
            asset = archive.read(native + manifest["filename"])
            if hashlib.sha256(asset).hexdigest() != manifest["sha256"]:
                raise WheelVerificationError("native asset digest mismatch")
            if not manifest["build"]["reproducible_verified"]:
                raise WheelVerificationError("native asset lacks reproducible build evidence")
            ui = [name for name in names if "server/static/web-ui/" in name]
            has_index = any(name.endswith("server/static/web-ui/index.html") for name in ui)
            entry_files = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
            if len(entry_files) != 1:
                raise WheelVerificationError(f"expected one entry_points.txt, got {entry_files}")
            parser = configparser.ConfigParser()
            parser.read_file(io.StringIO(archive.read(entry_files[0]).decode("utf-8")))
            scripts = dict(parser["console_scripts"])
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, configparser.Error) as error:
        if isinstance(error, WheelVerificationError):
            raise
        raise WheelVerificationError(f"unable to inspect core wheel: {error}") from error

    print(f"{wheel}: {len(ui)} web UI files; index.html={has_index}")
    print(f"console scripts: {scripts}")
    if not ui or not has_index:
        raise WheelVerificationError("web UI bundle missing from core wheel")
    expected_script = "omnigent.cli:main"
    for name in ("omni", "omnigent"):
        if scripts.get(name) != expected_script:
            raise WheelVerificationError(
                f"missing/incorrect console script {name!r}: {scripts.get(name)!r}"
            )
    print(f"Verified Omnigent {expected_version} wheel for source {source_sha}.")
    return wheel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--source-sha", required=True)
    arguments = parser.parse_args(argv)
    try:
        verify_wheel(
            arguments.dist_dir,
            expected_version=arguments.expected_version,
            source_sha=arguments.source_sha,
        )
    except (OSError, WheelVerificationError) as error:
        print(f"Windows wheel verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
