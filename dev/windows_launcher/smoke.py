"""Exercise the native launcher from an installed wheel, without provider access."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-installed", action="store_true")
    parser.add_argument("--mode", choices=("native-dev", "native"), default="native-dev")
    arguments = parser.parse_args()

    from omnigent.inner import sandbox
    from omnigent.inner import windows_exec_launcher as native

    origin = Path(sandbox.__file__).resolve()
    if arguments.require_installed and not origin.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError(f"Smoke requires an installed wheel, imported {origin}")
    resource = Path(native.__file__).resolve().parents[1] / "resources/windows_launcher"
    manifest = json.loads((resource / "manifest.json").read_text(encoding="utf-8"))
    policy = sandbox.SandboxPolicy("windows_jobobject", True, None, [], [], True)
    if manifest["release_approved"] is False:
        os.environ[native.SELECTOR] = "native"
        try:
            rejected = sandbox.create_exec_launcher(sys.executable, policy)
        except OSError as error:
            if "signing/review gate" not in str(error):
                raise
        else:
            Path(rejected).unlink()
            raise RuntimeError("Unsigned candidate bypassed the production gate")
    os.environ[native.SELECTOR] = arguments.mode
    path = sandbox.create_exec_launcher(sys.executable, policy, cwd=os.getcwd())
    values = ["", "hello world", 'quote"inside', "trailing\\", "%PATH%", "a&b", "å日本語"]
    source = (
        "import json,os,sys; "
        "print(json.dumps([sys.argv[1:],sys.stdin.read(),os.getcwd()])); "
        "raise SystemExit(37)"
    )
    try:
        result = subprocess.run(
            [path, "-c", source, *values],
            input="native wheel stdin\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 37:
            raise RuntimeError(f"Native wheel smoke failed: {result.returncode}: {result.stderr}")
        expected = [values, "native wheel stdin\n", os.getcwd()]
        if json.loads(result.stdout) != expected:
            raise RuntimeError(f"Native wheel arguments/stdin/cwd mismatch: {result.stdout!r}")
    finally:
        Path(path).unlink()
    if Path(path + native.CONFIG_STREAM).exists():
        raise RuntimeError("Single-filename cleanup left the configuration stream")
    print(f"Native wheel smoke passed ({arguments.mode}); imported {origin}")


if __name__ == "__main__":
    main()
