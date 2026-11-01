"""Assemble the workflow's existing Windows wheel bundle from pinned templates."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

TEMPLATE_DIRECTORY = Path(__file__).with_name("templates") / "windows"
BUNDLE_FILES = {
    "scripts/install_windows_bundle.ps1": "install.ps1",
    "scripts/uninstall_windows_bundle.ps1": "uninstall.ps1",
    "scripts/windows_bundle_state.ps1": "windows_bundle_state.ps1",
    "scripts/windows_safe_pytest.ps1": "windows_safe_pytest.ps1",
    "docs/windows/README.md": "WINDOWS-README.md",
    "docs/windows/test-execution.md": "TESTING.md",
}


class BundleAssemblyError(RuntimeError):
    """The Windows release bundle could not be assembled faithfully."""


def _windows_text(path: Path, *, encoding: str) -> bytes:
    text = path.read_text(encoding=encoding)
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode(encoding)


def assemble_bundle(
    repository_root: Path,
    wheels_directory: Path,
    output_directory: Path,
    *,
    expected_version: str,
    source_sha: str,
    template_directory: Path = TEMPLATE_DIRECTORY,
) -> Path:
    if not expected_version or any(character in expected_version for character in "\r\n"):
        raise BundleAssemblyError("An explicit expected version is required.")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise BundleAssemblyError("An explicit full source SHA is required.")

    repository_root = repository_root.resolve()
    wheels_directory = (
        wheels_directory if wheels_directory.is_absolute() else repository_root / wheels_directory
    )
    output_directory = (
        output_directory if output_directory.is_absolute() else repository_root / output_directory
    )
    wheel_sources = sorted(wheels_directory.glob("*.whl"), key=lambda path: path.name)
    if not wheel_sources:
        raise BundleAssemblyError(f"No wheel artifacts found in {wheels_directory}")

    bundle_wheels = output_directory / "wheels"
    bundle_wheels.mkdir(parents=True, exist_ok=True)
    for wheel in wheel_sources:
        shutil.copy2(wheel, bundle_wheels / wheel.name)
    for source_name, destination_name in BUNDLE_FILES.items():
        shutil.copy2(repository_root / source_name, output_directory / destination_name)

    (output_directory / "INSTALL.cmd").write_bytes(
        _windows_text(template_directory / "INSTALL.cmd", encoding="ascii")
    )
    (output_directory / "UNINSTALL.cmd").write_bytes(
        _windows_text(template_directory / "UNINSTALL.cmd", encoding="ascii")
    )
    readme = _windows_text(template_directory / "README.txt", encoding="utf-8")
    readme = readme.replace(
        b"\r\n     .\\install.ps1 -NoSystemCertificates\r\n",
        b"\r\n  .\\install.ps1 -NoSystemCertificates\r\n",
    )
    (output_directory / "README.txt").write_bytes(readme)

    checksum_lines = [
        f"{hashlib.sha256(wheel.read_bytes()).hexdigest()}  {wheel.name}"
        for wheel in sorted(bundle_wheels.glob("*.whl"), key=lambda path: path.name)
    ]
    checksums = "\r\n".join(checksum_lines)
    if checksum_lines:
        checksums += "\r\n"
    (output_directory / "SHA256SUMS.txt").write_bytes(checksums.encode("ascii"))
    print(f"Assembled Omnigent {expected_version} Windows bundle for source {source_sha}.")
    return output_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--wheels-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--source-sha", required=True)
    arguments = parser.parse_args(argv)
    try:
        assemble_bundle(
            arguments.repository_root,
            arguments.wheels_dir,
            arguments.output_dir,
            expected_version=arguments.expected_version,
            source_sha=arguments.source_sha,
        )
    except (OSError, BundleAssemblyError) as error:
        print(f"Windows bundle assembly failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
