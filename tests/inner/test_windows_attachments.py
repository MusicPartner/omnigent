"""Exercise Windows attachment confinement against real filesystem aliases."""

from __future__ import annotations

import base64
import ctypes
import hashlib
import os
import struct
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from omnigent.inner import native_attachments, windows_attachments
from omnigent.inner import windows_exec_launcher as security_helpers
from tests.inner.windows_private_job_launcher import private_test_directory

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows attachment filesystem APIs")


@pytest.fixture
def tmp_path():
    yield from private_test_directory.__wrapped__()


@pytest.fixture(autouse=True)
def isolated_attachment_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(native_attachments, "data_dir", lambda: tmp_path)


def _block(content: bytes, filename: str = "report.txt") -> dict[str, object]:
    return {
        "type": "input_file",
        "filename": filename,
        "file_data": "data:text/plain;base64," + base64.b64encode(content).decode("ascii"),
    }


def _junction(path: Path, target: Path) -> None:
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(path), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.lstat().st_file_attributes & 0x400


def _symlink(path: Path, target: Path) -> None:
    try:
        path.symlink_to(target)
    except OSError as error:
        if error.winerror == 1314:
            pytest.skip("Windows symbolic-link creation privilege is unavailable")
        raise


def _assert_private(path: Path, *, expected_owner: str | None = None) -> None:
    kernel, security = security_helpers._windows()
    descriptor, owner, dacl = (ctypes.wintypes.LPVOID() for _ in range(3))
    security.GetNamedSecurityInfoW.argtypes = [
        ctypes.wintypes.LPWSTR,
        ctypes.c_int,
        ctypes.wintypes.DWORD,
        ctypes.POINTER(ctypes.wintypes.LPVOID),
        ctypes.wintypes.LPVOID,
        ctypes.POINTER(ctypes.wintypes.LPVOID),
        ctypes.wintypes.LPVOID,
        ctypes.POINTER(ctypes.wintypes.LPVOID),
    ]
    security.GetNamedSecurityInfoW.restype = ctypes.wintypes.DWORD
    assert (
        security.GetNamedSecurityInfoW(
            str(path),
            1,
            5,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        == 0
    )
    try:
        user = security_helpers._current_user_sid(kernel, security)
        assert security_helpers._sid_text(kernel, security, owner) == (expected_owner or user)
        control, revision = ctypes.wintypes.WORD(), ctypes.wintypes.DWORD()
        assert security.GetSecurityDescriptorControl(
            descriptor, ctypes.byref(control), ctypes.byref(revision)
        )
        assert control.value & 0x1000
        assert dacl.value is not None
        assert ctypes.wintypes.WORD.from_address(dacl.value + 4).value == 2
        trustees = set()
        for index in range(2):
            ace = ctypes.wintypes.LPVOID()
            assert security.GetAce(dacl, index, ctypes.byref(ace))
            assert ace.value is not None
            assert ctypes.c_ubyte.from_address(ace.value).value == 0
            assert ctypes.c_ubyte.from_address(ace.value + 1).value & 0x10 == 0
            expected = 0x1F01FF if path.is_dir() else 0x1F01DF
            assert ctypes.wintypes.DWORD.from_address(ace.value + 4).value == expected
            trustees.add(security_helpers._sid_text(kernel, security, ace.value + 8))
        assert trustees == {user, "S-1-5-18"}
    finally:
        kernel.LocalFree(descriptor)


def test_native_dispatch_writes_private_file_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    path = native_attachments.materialize_attachment(_block(b"attachment bytes"), workspace)
    assert path is not None
    assert path.read_bytes() == b"attachment bytes"
    assert path.parent == native_attachments.attachment_cache_dir(workspace)
    assert not list(workspace.iterdir())
    for protected in (path, path.parent, path.parent.parent):
        _assert_private(protected)


def test_reuse_and_collision_never_overwrite_existing_bytes(tmp_path):
    directory = tmp_path / "cache"
    first = windows_attachments.materialize_attachment(directory, "report.txt", b"first")
    assert first is not None
    assert windows_attachments.materialize_attachment(directory, "report.txt", b"first") == first
    second = windows_attachments.materialize_attachment(directory, "report.txt", b"second")
    digest = hashlib.sha256(b"second").hexdigest()[:12]
    assert second == directory / f"report_{digest}.txt"
    assert windows_attachments.materialize_attachment(directory, "report.txt", b"second") == second
    assert first.read_bytes() == b"first"
    assert second.read_bytes() == b"second"
    assert len(list(directory.iterdir())) == 2


def test_both_names_occupied_returns_none_without_overwrite(tmp_path):
    directory = tmp_path / "cache"
    desired = b"wanted"
    digest = hashlib.sha256(desired).hexdigest()[:12]
    windows_attachments.materialize_attachment(directory, "report.txt", b"first")
    windows_attachments.materialize_attachment(directory, f"report_{digest}.txt", b"other")
    assert windows_attachments.materialize_attachment(directory, "report.txt", desired) is None
    assert (directory / "report.txt").read_bytes() == b"first"
    assert (directory / f"report_{digest}.txt").read_bytes() == b"other"


@pytest.mark.parametrize("position", ["cache", "ancestor", "leaf"])
def test_junction_cannot_redirect_materialization(tmp_path, position):
    outside = tmp_path / "outside"
    outside.mkdir()
    directory = tmp_path / "cache"
    if position == "cache":
        alias = directory
    elif position == "ancestor":
        alias = tmp_path / "parent"
        directory = alias / "cache"
    else:
        directory.mkdir()
        alias = directory / "report.txt"
    _junction(alias, outside)
    try:
        with pytest.raises(OSError):
            windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
        assert list(outside.iterdir()) == []
    finally:
        alias.rmdir()


@pytest.mark.parametrize("collision", [False, True])
def test_hardlinked_leaf_cannot_be_reused_or_modified(tmp_path, collision):
    directory = tmp_path / "cache"
    directory.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"secret")
    digest = hashlib.sha256(b"secret").hexdigest()[:12]
    name = f"report_{digest}.txt" if collision else "report.txt"
    if collision:
        (directory / "report.txt").write_bytes(b"other")
    os.link(outside, directory / name)
    with pytest.raises(OSError):
        windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert outside.read_bytes() == b"secret"
    assert (directory / name).stat().st_nlink == 2


@pytest.mark.parametrize("collision", [False, True])
def test_symlink_leaf_cannot_be_reused_or_modified(tmp_path, collision):
    directory = tmp_path / "cache"
    directory.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"secret")
    digest = hashlib.sha256(b"secret").hexdigest()[:12]
    name = f"report_{digest}.txt" if collision else "report.txt"
    if collision:
        (directory / "report.txt").write_bytes(b"other")
    _symlink(directory / name, outside)
    with pytest.raises(OSError):
        windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert outside.read_bytes() == b"secret"


@pytest.mark.parametrize(
    "name",
    [
        "report.txt:payload",
        "report.txt::$DATA",
        "CON",
        "con.txt",
        "NUL.txt",
        "COM1.log",
        "LPT9",
        "COM¹.txt",
        "report.txt.",
        "report.txt ",
        "..",
        "a/b.txt",
        "a\\b.txt",
        "a?b.txt",
        "a\x00b.txt",
    ],
)
def test_windows_alias_and_device_names_are_rejected(tmp_path, name):
    directory = tmp_path / "cache"
    with pytest.raises((OSError, ValueError)):
        windows_attachments.materialize_attachment(directory, name, b"secret")
    assert not directory.exists() or not list(directory.iterdir())


def test_concurrent_identical_writes_leave_one_complete_file(tmp_path):
    directory = tmp_path / "cache"
    content = b"complete attachment\n" * 4096

    def place(_):
        try:
            return windows_attachments.materialize_attachment(directory, "report.txt", content)
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        paths = list(executor.map(place, range(16)))
    assert any(path is not None for path in paths)
    assert [path.name for path in directory.iterdir()] == ["report.txt"]
    assert (directory / "report.txt").read_bytes() == content
    assert (
        windows_attachments.materialize_attachment(directory, "report.txt", content)
        == directory / "report.txt"
    )


def test_secure_alias_preserves_source_and_reuses_identical_copy(tmp_path):
    directory = tmp_path / "cache"
    source = windows_attachments.materialize_attachment(directory, "photo.png", b"image bytes")
    assert source is not None
    alias = windows_attachments.secure_alias(source, "photo_6000x4000.png")
    assert alias == directory / "photo_6000x4000.png"
    assert alias.read_bytes() == source.read_bytes()
    assert windows_attachments.secure_alias(source, alias.name) == alias
    _assert_private(alias)


def test_secure_alias_refuses_existing_other_content(tmp_path):
    directory = tmp_path / "cache"
    source = windows_attachments.materialize_attachment(directory, "photo.png", b"image bytes")
    alias = windows_attachments.materialize_attachment(directory, "resized.png", b"other")
    assert source is not None and alias is not None
    with pytest.raises(OSError):
        windows_attachments.secure_alias(source, alias.name)
    assert alias.read_bytes() == b"other"


def test_secure_alias_refuses_hardlinked_source(tmp_path):
    directory = tmp_path / "cache"
    source = windows_attachments.materialize_attachment(directory, "photo.png", b"image bytes")
    assert source is not None
    os.link(source, tmp_path / "outside.png")
    with pytest.raises(OSError):
        windows_attachments.secure_alias(source, "resized.png")
    assert not (directory / "resized.png").exists()


def test_existing_owned_cache_migrates_to_private_non_executable_files(tmp_path):
    directory = tmp_path / "cache"
    directory.mkdir()
    path = directory / "report.txt"
    path.write_bytes(b"existing")
    directory_owner = _trusted_existing_owner(directory)
    file_owner = _trusted_existing_owner(path)
    assert windows_attachments.materialize_attachment(directory, path.name, b"existing") == path
    _assert_private(directory, expected_owner=directory_owner)
    _assert_private(path, expected_owner=file_owner)


def test_foreign_writable_cache_is_refused_without_acl_upgrade(tmp_path):
    directory = tmp_path / "cache"
    directory.mkdir()
    result = subprocess.run(
        ["icacls.exe", str(directory), "/grant", "*S-1-1-0:(OI)(CI)(F)"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with pytest.raises(OSError):
        windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert not list(directory.iterdir())


def test_partial_write_failure_deletes_only_owned_new_leaf(tmp_path, monkeypatch):
    directory = tmp_path / "cache"
    original = windows_attachments.materialize_attachment(directory, "keep.txt", b"keep")
    assert original is not None
    write = windows_attachments._write_handle

    def fail(kernel, handle, content):
        write(kernel, handle, content[:7])
        raise OSError("simulated full disk after partial write")

    monkeypatch.setattr(windows_attachments, "_write_handle", fail)
    with pytest.raises(OSError, match="partial write"):
        windows_attachments.materialize_attachment(directory, "report.txt", b"complete content")
    assert list(directory.iterdir()) == [original]
    assert original.read_bytes() == b"keep"
    monkeypatch.setattr(windows_attachments, "_write_handle", write)
    assert windows_attachments.materialize_attachment(directory, "report.txt", b"complete content")


@pytest.mark.parametrize("which", ["directory", "ancestor"])
def test_held_ancestor_handles_block_rename_during_creation(tmp_path, monkeypatch, which):
    ancestor = tmp_path / "parent"
    directory = ancestor / "cache"
    write = windows_attachments._write_handle
    attempted = []

    def write_after_attack(kernel, handle, content):
        target = directory if which == "directory" else ancestor
        with pytest.raises(OSError) as error:
            target.rename(target.with_name(target.name + "-moved"))
        assert error.value.winerror in {5, 32, 33}
        attempted.append(target)
        write(kernel, handle, content)

    monkeypatch.setattr(windows_attachments, "_write_handle", write_after_attack)
    path = windows_attachments.materialize_attachment(directory, "report.txt", b"complete")
    assert attempted
    assert path == directory / "report.txt"
    assert path.read_bytes() == b"complete"
    assert not ancestor.with_name("parent-moved").exists()
    assert not directory.with_name("cache-moved").exists()


def test_resize_dispatch_uses_private_alias_and_keeps_metadata(tmp_path):
    directory = tmp_path / "cache"
    source = windows_attachments.materialize_attachment(directory, "photo.png", b"image bytes")
    assert source is not None
    alias = native_attachments.codex_resize_metadata_path(source, {"width": 6000, "height": 4000})
    assert alias != source
    assert "__omnigent-downscaled-from-6000x4000-request-crop-for-fine-detail" in alias.name
    assert alias.read_bytes() == source.read_bytes()
    assert (
        native_attachments.codex_resize_metadata_path(source, {"width": 6000, "height": 4000})
        == alias
    )
    _assert_private(alias)


def test_resize_dispatch_refuses_source_junction(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    source = windows_attachments.materialize_attachment(outside, "photo.png", b"image bytes")
    assert source is not None
    alias = tmp_path / "redirect"
    _junction(alias, outside)
    redirected = alias / source.name
    try:
        assert (
            native_attachments.codex_resize_metadata_path(
                redirected, {"width": 6000, "height": 4000}
            )
            == redirected
        )
        assert [path.name for path in outside.iterdir()] == [source.name]
    finally:
        alias.rmdir()


def test_secure_alias_refuses_linked_destination(tmp_path):
    directory = tmp_path / "cache"
    source = windows_attachments.materialize_attachment(directory, "photo.png", b"image bytes")
    assert source is not None
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"image bytes")
    os.link(outside, directory / "resized.png")
    with pytest.raises(OSError):
        windows_attachments.secure_alias(source, "resized.png")
    assert outside.read_bytes() == b"image bytes"


def test_post_create_validation_failure_removes_owned_leaf(tmp_path, monkeypatch):
    directory = tmp_path / "cache"

    def fail(*args):
        raise OSError("simulated file identity lookup failure")

    monkeypatch.setattr(windows_attachments, "_regular_file", fail)
    with pytest.raises(OSError, match="identity lookup"):
        windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert not list(directory.iterdir())


def test_file_handle_blocks_leaf_replacement_during_write(tmp_path, monkeypatch):
    directory = tmp_path / "cache"
    write = windows_attachments._write_handle

    def write_after_attack(kernel, handle, content):
        leaf = directory / "report.txt"
        with pytest.raises(OSError) as error:
            leaf.rename(directory / "redirected.txt")
        assert error.value.winerror in {5, 32, 33}
        write(kernel, handle, content)

    monkeypatch.setattr(windows_attachments, "_write_handle", write_after_attack)
    path = windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert path is not None
    assert path.read_bytes() == b"secret"
    assert not (directory / "redirected.txt").exists()


@pytest.mark.parametrize("filename", ["payload.exe", "payload.cmd"])
def test_uploaded_file_denies_native_execute_access(tmp_path, filename):
    path = windows_attachments.materialize_attachment(tmp_path / "cache", filename, b"attachment")
    assert path is not None
    kernel, _security = security_helpers._windows()
    handle = kernel.CreateFileW(str(path), 0x20, 7, None, 3, 0x00200000, None)
    try:
        assert handle == ctypes.c_void_p(-1).value
        assert ctypes.get_last_error() == 5
    finally:
        if handle != ctypes.c_void_p(-1).value:
            kernel.CloseHandle(handle)
    assert path.read_bytes() == b"attachment"


def test_resize_source_read_is_bounded(tmp_path, monkeypatch):
    source = windows_attachments.materialize_attachment(tmp_path / "cache", "photo.png", b"12345")
    assert source is not None
    monkeypatch.setattr(windows_attachments, "_MAX_BYTES", 4)
    with pytest.raises(OSError, match="bounded read"):
        windows_attachments.secure_alias(source, "resized.png")
    assert [path.name for path in source.parent.iterdir()] == [source.name]


@pytest.mark.parametrize("stem", ["a" * 251, "😀" * 125 + "a"])
def test_maximum_component_collision_remains_bounded_and_preserves_extension(tmp_path, stem):
    directory = tmp_path / "cache"
    name = stem + ".txt"
    assert len(name.encode("utf-16-le")) == 510
    first = windows_attachments.materialize_attachment(directory, name, b"first")
    second = windows_attachments.materialize_attachment(directory, name, b"second")
    assert first is not None and second is not None and first != second
    assert first.read_bytes() == b"first"
    assert second.read_bytes() == b"second"
    assert second.suffix == ".txt"
    assert hashlib.sha256(b"second").hexdigest()[:12] in second.name
    assert len(second.name.encode("utf-16-le")) <= 510
    assert windows_attachments.materialize_attachment(directory, name, b"second") == second
    assert len(list(directory.iterdir())) == 2


@pytest.mark.parametrize("name", ["CONIN$", "CONOUT$.txt", "CLOCK$", "CON .txt", "LPT1 .txt"])
def test_reserved_device_aliases_cannot_be_disguised(tmp_path, name):
    with pytest.raises(ValueError):
        windows_attachments.materialize_attachment(tmp_path / "cache", name, b"secret")


@pytest.mark.parametrize("rights", ["WA", "WEA", "WD"])
def test_foreign_reparse_mutation_rights_on_ancestor_are_refused(tmp_path, rights):
    ancestor = tmp_path / "parent"
    ancestor.mkdir()
    result = subprocess.run(
        ["icacls.exe", str(ancestor), "/grant", f"*S-1-1-0:({rights})"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with pytest.raises(OSError, match="untrusted mutation"):
        windows_attachments.materialize_attachment(ancestor / "cache", "report.txt", b"secret")
    assert not (ancestor / "cache").exists()


def _set_junction_by_handle(path: Path, target: Path, access: int = 0x40000000) -> None:
    kernel, _security = security_helpers._windows()
    kernel.DeviceIoControl.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.LPVOID,
        ctypes.wintypes.DWORD,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.wintypes.LPVOID,
    ]
    kernel.DeviceIoControl.restype = ctypes.wintypes.BOOL
    handle = kernel.CreateFileW(str(path), access, 7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        substitute = ("\\??\\" + str(target)).encode("utf-16-le")
        printable = str(target).encode("utf-16-le")
        names = substitute + b"\0\0" + printable + b"\0\0"
        payload = (
            struct.pack(
                "<IHHHHHH",
                0xA0000003,
                8 + len(names),
                0,
                0,
                len(substitute),
                len(substitute) + 2,
                len(printable),
            )
            + names
        )
        buffer = ctypes.create_string_buffer(payload)
        returned = ctypes.wintypes.DWORD()
        if not kernel.DeviceIoControl(
            handle,
            0x000900A4,
            buffer,
            len(payload),
            None,
            0,
            ctypes.byref(returned),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)


@pytest.mark.parametrize("access", [0x40000000, 0x2, 0x100])
def test_same_owner_can_set_junction_without_renaming_unlocked_directory(tmp_path, access):
    directory = tmp_path / "cache"
    directory.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        _set_junction_by_handle(directory, outside, access)
        assert directory.lstat().st_file_attributes & 0x400
        assert directory.resolve() == outside.resolve()
    finally:
        directory.rmdir()


@pytest.mark.parametrize("which", ["directory", "ancestor"])
@pytest.mark.parametrize("access", [0x40000000, 0x2])
def test_held_directory_handles_block_in_place_reparse_mutation(tmp_path, which, access):
    ancestor = tmp_path / "parent"
    directory = ancestor / "cache"
    outside = tmp_path / "outside"
    outside.mkdir()
    with windows_attachments._locked_directory(directory):
        target = directory if which == "directory" else ancestor
        with pytest.raises(OSError) as error:
            _set_junction_by_handle(target, outside, access)
        assert error.value.winerror in {32, 33}
        assert not target.lstat().st_file_attributes & 0x400
    path = windows_attachments.materialize_attachment(directory, "report.txt", b"secret")
    assert path is not None and path.read_bytes() == b"secret"
    assert not list(outside.iterdir())


def test_foreign_add_subdirectory_right_does_not_allow_reparse_mutation(tmp_path):
    ancestor = tmp_path / "parent"
    ancestor.mkdir()
    result = subprocess.run(
        ["icacls.exe", str(ancestor), "/grant", "*S-1-1-0:(AD)"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    path = windows_attachments.materialize_attachment(ancestor / "cache", "report.txt", b"secret")
    assert path is not None and path.read_bytes() == b"secret"
    _assert_private(path)


def test_attribute_only_reparse_mutation_is_detected_when_directory_context_exits(tmp_path):
    directory = tmp_path / "cache"
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        with pytest.raises(OSError, match="reparse"):
            with windows_attachments._locked_directory(directory):
                _set_junction_by_handle(directory, outside, 0x100)
                assert directory.lstat().st_file_attributes & 0x400
        assert not list(outside.iterdir())
    finally:
        if directory.exists():
            directory.rmdir()


@pytest.mark.parametrize("which", ["directory", "ancestor"])
def test_attribute_only_mutation_before_relative_create_cannot_redirect_bytes(
    tmp_path, monkeypatch, which
):
    ancestor = tmp_path / "parent"
    cache = ancestor / "cache"
    outside = tmp_path / "outside"
    outside.mkdir()
    opening = windows_attachments._relative_open
    attacked = []
    target = cache if which == "directory" else ancestor
    attack_name = "report.txt" if which == "directory" else "cache"

    def race(parent_handle, name, access, disposition, *, directory: bool, attributes=None):
        if name == attack_name and directory == (which == "ancestor"):
            _set_junction_by_handle(target, outside, 0x100)
            attacked.append(name)
        return opening(
            parent_handle,
            name,
            access,
            disposition,
            directory=directory,
            attributes=attributes,
        )

    monkeypatch.setattr(windows_attachments, "_relative_open", race)
    try:
        with pytest.raises(OSError):
            windows_attachments.materialize_attachment(cache, "report.txt", b"private payload")
        assert attacked == [attack_name]
        assert not list(outside.iterdir())
    finally:
        if target.exists():
            target.rmdir()


def _trusted_existing_owner(path: Path) -> str:
    kernel, security = security_helpers._windows()
    handle = kernel.CreateFileW(str(path), 0x20000, 7, None, 3, 0x02200000, None)
    assert handle != ctypes.c_void_p(-1).value
    descriptor, owner = ctypes.wintypes.LPVOID(), ctypes.wintypes.LPVOID()
    try:
        assert (
            security.GetSecurityInfo(
                handle,
                1,
                1,
                ctypes.byref(owner),
                None,
                None,
                None,
                ctypes.byref(descriptor),
            )
            == 0
        )
        try:
            actual = security_helpers._sid_text(kernel, security, owner)
            user = security_helpers._current_user_sid(kernel, security)
            assert actual in {user, "S-1-5-18", "S-1-5-32-544"}
            return actual
        finally:
            kernel.LocalFree(descriptor)
    finally:
        kernel.CloseHandle(handle)


def _acl_trustees(path: Path) -> set[str]:
    kernel, security = security_helpers._windows()
    handle = kernel.CreateFileW(str(path), 0x20000, 7, None, 3, 0x02200000, None)
    assert handle != ctypes.c_void_p(-1).value
    descriptor, owner, dacl = (ctypes.wintypes.LPVOID() for _ in range(3))
    try:
        assert (
            security.GetSecurityInfo(
                handle,
                1,
                5,
                ctypes.byref(owner),
                None,
                ctypes.byref(dacl),
                None,
                ctypes.byref(descriptor),
            )
            == 0
        )
        try:
            assert dacl.value is not None
            trustees = set()
            for index in range(ctypes.wintypes.WORD.from_address(dacl.value + 4).value):
                ace = ctypes.wintypes.LPVOID()
                assert security.GetAce(dacl, index, ctypes.byref(ace))
                assert ace.value is not None
                trustees.add(security_helpers._sid_text(kernel, security, ace.value + 8))
            return trustees
        finally:
            kernel.LocalFree(descriptor)
    finally:
        kernel.CloseHandle(handle)


def test_python_private_directory_owner_rights_is_upgraded_to_actual_user_acl(tmp_path):
    directory = Path(tempfile.mkdtemp(dir=tmp_path))
    owner = _trusted_existing_owner(directory)
    assert "S-1-3-4" in _acl_trustees(directory)
    path = windows_attachments.materialize_attachment(directory, "report.txt", b"private payload")
    assert path is not None and path.read_bytes() == b"private payload"
    _assert_private(directory, expected_owner=owner)
    _assert_private(path)
    assert "S-1-3-4" not in _acl_trustees(directory)


@pytest.mark.parametrize("operation", ["materialize", "resize"])
def test_windows_refusal_logs_no_payload_or_exception_locals(tmp_path, caplog, operation):
    payload = b"private-attachment-bytes-never-log-this"
    encoded = base64.b64encode(payload).decode("ascii")
    if operation == "materialize":
        assert (
            native_attachments.materialize_attachment(_block(payload, "NUL.txt"), tmp_path) is None
        )
    else:
        source = windows_attachments.materialize_attachment(
            tmp_path / "cache", "photo.png", payload
        )
        assert source is not None
        os.link(source, tmp_path / "linked-photo.png")
        assert (
            native_attachments.codex_resize_metadata_path(source, {"width": 6000, "height": 4000})
            == source
        )
    records = [
        record for record in caplog.records if record.name == "omnigent.inner.native_attachments"
    ]
    assert records
    assert all(record.exc_info is None for record in records)
    assert payload.decode("ascii") not in caplog.text
    assert encoded not in caplog.text
