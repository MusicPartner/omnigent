from __future__ import annotations

import os

from omnigent.host import host_listing


def test_is_untraversable_junction_false_when_not_junction(monkeypatch) -> None:
    called = {"scandir": 0}

    monkeypatch.setattr(host_listing.os.path, "isjunction", lambda _path: False)

    def _scandir(_path: str):
        called["scandir"] += 1
        raise AssertionError("scandir should not be called for non-junction paths")

    monkeypatch.setattr(host_listing.os, "scandir", _scandir)

    assert host_listing.is_untraversable_junction("C:/repo") is False
    assert called["scandir"] == 0


def test_is_untraversable_junction_false_when_traversable(monkeypatch) -> None:
    monkeypatch.setattr(host_listing.os.path, "isjunction", lambda _path: True)

    class _Ctx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(host_listing.os, "scandir", lambda _path: _Ctx())

    assert host_listing.is_untraversable_junction("C:/repo") is False


def test_is_untraversable_junction_true_on_permission_error(monkeypatch) -> None:
    monkeypatch.setattr(host_listing.os.path, "isjunction", lambda _path: True)

    def _scandir(_path: str):
        raise PermissionError("denied")

    monkeypatch.setattr(host_listing.os, "scandir", _scandir)

    assert host_listing.is_untraversable_junction("C:/repo") is True


def test_host_native_path_matches_normpath() -> None:
    path = "C:/Users/alice\\repo/subdir"
    assert host_listing.host_native_path(path) == os.path.normpath(path)
