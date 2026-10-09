"""Isolated prototype: not safe for production sandbox containment.

The distlib stub spawns Python before parent-side Job Object assignment, so
existing descendants can escape. Do not adopt behind create_exec_launcher.

The parent owns Job Object assignment through ``post_spawn``. This executable
only transports the existing Python sandbox program; it adds no OS isolation.
"""

from __future__ import annotations

import io
import os
import platform
import struct
import tempfile
from importlib.resources import files
from zipfile import ZIP_STORED, ZipFile


def create_console_launcher(source: str, interpreter: str) -> str:
    """Return one caller-owned executable containing ``source``.

    distlib's console stub invokes the named Python with this executable as a
    zipapp, forwards the native command line, waits, and returns its exit code.
    Only Windows x64 Python has been validated for this runtime contract.
    """
    if platform.machine().lower() not in {"amd64", "x86_64"} or struct.calcsize("P") != 8:
        raise OSError("The Windows sandbox executable currently requires native x64 Python")
    if not interpreter or any(character in interpreter for character in '\r\n"'):
        raise OSError("The Windows sandbox executable requires a valid interpreter filename")

    launcher = files("distlib").joinpath("t64.exe").read_bytes()
    archive = io.BytesIO()
    with ZipFile(archive, "w", compression=ZIP_STORED) as zipped:
        zipped.writestr("__main__.py", source.encode())
    payload = launcher + f'#!"{interpreter}"\n'.encode() + archive.getvalue()
    fd, path = tempfile.mkstemp(prefix="omnigent-sandbox-", suffix=".exe")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
    except BaseException:
        os.unlink(path)
        raise
    return path
