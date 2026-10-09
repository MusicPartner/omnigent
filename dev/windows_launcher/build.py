"""Build the native Windows x64 private-job launcher and its provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path


def _msvc_environment(
    *, toolset_version: str | None = None, sdk_version: str | None = None
) -> dict[str, str]:
    for version in (toolset_version, sdk_version):
        if version is not None and not re.fullmatch(r"\d+(?:\.\d+)+", version):
            raise ValueError("Toolchain versions must contain only dotted numbers")
    installer = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
    vswhere = installer / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        raise RuntimeError("MSVC discovery requires an installed Visual Studio vswhere.exe")
    discovery = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    installation = discovery.stdout.strip()
    if not installation:
        raise RuntimeError("Install the Visual Studio native x64 C++ build tools first")
    devcmd = Path(installation) / "Common7" / "Tools" / "VsDevCmd.bat"
    if not devcmd.is_file() or any(c in str(devcmd) for c in '"\r\n%'):
        raise RuntimeError("Visual Studio discovery returned an unusable VsDevCmd path")
    comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
    # cmd.exe parses its own quotes; list2cmdline would escape the batch path.
    selections = ""
    if toolset_version:
        selections += f" -vcvars_ver={toolset_version}"
    if sdk_version:
        selections += f" -winsdk={sdk_version}"
    environment = subprocess.run(
        f'"{comspec}" /d /s /c call "{devcmd}" -no_logo -arch=x64 -host_arch=x64'
        f"{selections} >nul && set",
        check=True,
        capture_output=True,
        text=True,
    )
    result = dict(
        line.split("=", 1)
        for line in environment.stdout.splitlines()
        if "=" in line and not line.startswith("=")
    )
    for key, requested in (
        ("VCToolsVersion", toolset_version),
        ("WindowsSDKVersion", sdk_version),
    ):
        actual = result.get(key, "").strip("\\/")
        if requested is not None and actual != requested:
            raise RuntimeError(f"Requested {key} {requested}; selected {actual or 'unknown'}")
    return result


def build_launcher(
    output: Path,
    *,
    checkpoints: bool = False,
    toolset_version: str | None = None,
    sdk_version: str | None = None,
    verify_reproducible: bool = False,
) -> Path:
    """Compile x64; an explicit pair of versions selects a pinned release toolchain."""
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("The launcher builds only on native Windows x64")
    if bool(toolset_version) != bool(sdk_version):
        raise ValueError("Pinned builds require both MSVC and Windows SDK versions")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name("private_job_launcher.c").resolve()
    environment = _msvc_environment(toolset_version=toolset_version, sdk_version=sdk_version)
    compiler = Path(environment["VCToolsInstallDir"]) / "bin" / "Hostx64" / "x64" / "cl.exe"
    print(
        f"MSVC tools {environment.get('VCToolsVersion', 'unknown')}; "
        f"Windows SDK {environment.get('WindowsSDKVersion', 'unknown')}",
        flush=True,
    )
    with tempfile.TemporaryDirectory(prefix="private-job-build-", dir=output.parent) as work:
        temporary = Path(work)
        executable = temporary / "launcher.exe"
        command = [
            str(compiler),
            "/nologo",
            "/std:c17",
            "/O2",
            "/MT",
            "/W4",
            "/WX",
            "/guard:cf",
            "/utf-8",
            "/Brepro",
            str(source),
            f"/Fo{temporary / 'launcher.obj'}",
            f"/Fe{executable}",
        ]
        if checkpoints:
            command.append("/DOMNIGENT_TEST_CHECKPOINTS")
        command += [
            "/link",
            "/MACHINE:X64",
            "/SUBSYSTEM:CONSOLE",
            "/INCREMENTAL:NO",
            "/DYNAMICBASE",
            "/NXCOMPAT",
            "/Brepro",
            "advapi32.lib",
        ]
        print(subprocess.list2cmdline(command), flush=True)
        subprocess.run(command, cwd=temporary, env=environment, check=True)
        executable_bytes = executable.read_bytes()
        if verify_reproducible:
            with tempfile.TemporaryDirectory(
                prefix="private-job-rebuild-", dir=output.parent
            ) as work:
                repeated = Path(work)
                repeated_command = [
                    f"/Fo{repeated / 'launcher.obj'}"
                    if argument.startswith("/Fo")
                    else f"/Fe{repeated / 'launcher.exe'}"
                    if argument.startswith("/Fe")
                    else argument
                    for argument in command
                ]
                subprocess.run(repeated_command, cwd=repeated, env=environment, check=True)
                if (repeated / "launcher.exe").read_bytes() != executable_bytes:
                    raise RuntimeError("Independent build directories produced different PE bytes")
        executable.replace(output)
    metadata = {
        "architecture": "x64",
        "configuration_stream": ":omnigent.config",
        "configuration_magic": "OJLCFG01",
        "test_checkpoints": checkpoints,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "executable_sha256": hashlib.sha256(executable_bytes).hexdigest(),
        "compiler_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
        "toolset_version": environment.get("VCToolsVersion", "").strip("\\/"),
        "windows_sdk_version": environment.get("WindowsSDKVersion", "").strip("\\/"),
        "pinned_toolchain": bool(toolset_version),
        "reproducible_verified": verify_reproducible,
        "authenticode_signed": False,
        "compiler_options": command[1 : command.index(str(source))],
        "linker_options": command[command.index("/link") + 1 :],
    }
    manifest = output.with_suffix(".build.json")
    manifest.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--test-checkpoints", action="store_true")
    parser.add_argument("--toolset-version", help="Exact MSVC tools version for a pinned build")
    parser.add_argument("--sdk-version", help="Exact Windows SDK version for a pinned build")
    parser.add_argument("--verify-reproducible", action="store_true")
    arguments = parser.parse_args()
    print(
        build_launcher(
            arguments.output,
            checkpoints=arguments.test_checkpoints,
            toolset_version=arguments.toolset_version,
            sdk_version=arguments.sdk_version,
            verify_reproducible=arguments.verify_reproducible,
        )
    )


if __name__ == "__main__":
    main()
