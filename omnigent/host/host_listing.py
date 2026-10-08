"""Helpers for host directory listing path handling and junction probing."""

from __future__ import annotations

import os


def is_untraversable_junction(path: str) -> bool:
    """True when a Windows junction exists but cannot be traversed.

    Windows can expose compatibility junctions that list but deny traversal.
    """
    if not os.path.isjunction(path):
        return False
    try:
        with os.scandir(path):
            return False
    except OSError:
        return True


def host_native_path(path: str) -> str:
    """Normalize a path to host-native separator spelling.

    DirEntry paths can mix separators when input used URL-style slashes.
    """
    return os.path.normpath(path)
