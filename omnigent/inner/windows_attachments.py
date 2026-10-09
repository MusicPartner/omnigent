"""Private Windows attachment files, pinned by non-reparse native handles."""

from __future__ import annotations

import contextlib
import ctypes
import ctypes.wintypes as w
import hashlib
import os
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

_INVALID_HANDLE = ctypes.c_void_p(-1).value
_REPARSE_POINT = 0x400
_DIRECTORY = 0x10
_OPEN_REPARSE_POINT = 0x00200000
_BACKUP_SEMANTICS = 0x02000000
_OBJ_DONT_REPARSE = 0x1000
_OBJ_CASE_INSENSITIVE = 0x40
_SYNCHRONOUS_IO_NONALERT = 0x20
_SYNCHRONIZE = 0x100000
_READ_ATTRIBUTES = 0x80
_LIST_DIRECTORY = 0x1
_SHARE_READ = 0x1
_READ_CONTROL = 0x20000
_WRITE_DAC = 0x40000
_MAX_BYTES = 50 * 1024 * 1024
_FULL_ACCESS = 0x1F01FF
_FILE_ACCESS = _FULL_ACCESS & ~0x20
_TRUSTED_INSTALLER = "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464"
_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.I)


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", w.DWORD), ("descriptor", w.LPVOID), ("inherit", w.BOOL)]


class _FileInfo(ctypes.Structure):
    _fields_ = [
        ("attributes", w.DWORD),
        ("creation", w.FILETIME),
        ("access", w.FILETIME),
        ("write", w.FILETIME),
        ("volume", w.DWORD),
        ("size_high", w.DWORD),
        ("size_low", w.DWORD),
        ("links", w.DWORD),
        ("index_high", w.DWORD),
        ("index_low", w.DWORD),
    ]


class _UnicodeString(ctypes.Structure):
    _fields_ = [("length", w.USHORT), ("maximum_length", w.USHORT), ("buffer", w.LPWSTR)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("length", w.ULONG),
        ("root_directory", w.HANDLE),
        ("object_name", ctypes.POINTER(_UnicodeString)),
        ("attributes", w.ULONG),
        ("security_descriptor", w.LPVOID),
        ("security_quality_of_service", w.LPVOID),
    ]


class _IoStatusBlock(ctypes.Structure):
    _fields_ = [("status", w.LPVOID), ("information", ctypes.c_size_t)]


def _relative_open(
    parent_handle, name: str, access: int, disposition: int, *, directory: bool, attributes=None
):
    """Open one lexical component beneath a held directory, refusing reparses."""
    _validate_name(name)
    loader = getattr(ctypes, "WinDLL", None)
    if loader is None:
        raise OSError("Native Windows attachment APIs are unavailable")
    native = loader("ntdll", use_last_error=True)
    native.NtCreateFile.argtypes = [
        ctypes.POINTER(w.HANDLE),
        w.DWORD,
        ctypes.POINTER(_ObjectAttributes),
        ctypes.POINTER(_IoStatusBlock),
        w.LPVOID,
        w.DWORD,
        w.DWORD,
        w.DWORD,
        w.DWORD,
        w.LPVOID,
        w.DWORD,
    ]
    native.NtCreateFile.restype = ctypes.c_long
    native.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
    native.RtlNtStatusToDosError.restype = w.ULONG
    text = ctypes.create_unicode_buffer(name)
    length = len(name.encode("utf-16-le"))
    unicode_name = _UnicodeString(length, length + 2, ctypes.cast(text, w.LPWSTR))
    objects = _ObjectAttributes(
        ctypes.sizeof(_ObjectAttributes),
        parent_handle,
        ctypes.pointer(unicode_name),
        _OBJ_CASE_INSENSITIVE | _OBJ_DONT_REPARSE,
        attributes.descriptor if attributes else None,
        None,
    )
    handle, status_block = w.HANDLE(), _IoStatusBlock()
    status = native.NtCreateFile(
        ctypes.byref(handle),
        access | _SYNCHRONIZE | _READ_ATTRIBUTES,
        ctypes.byref(objects),
        ctypes.byref(status_block),
        None,
        0x10 if directory else 0x80,
        _SHARE_READ,
        disposition,
        _OPEN_REPARSE_POINT | _SYNCHRONOUS_IO_NONALERT | (1 if directory else 0x40),
        None,
        0,
    )
    if status < 0:
        raise OSError(
            native.RtlNtStatusToDosError(status), "Windows attachment relative open failed"
        )
    return handle.value


def _windows():
    loader = getattr(ctypes, "WinDLL", None)
    if loader is None:
        raise OSError("Native Windows attachment APIs are unavailable")
    kernel, security = (
        loader("kernel32", use_last_error=True),
        loader("advapi32", use_last_error=True),
    )
    signatures = {
        "CreateFileW": (
            [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE],
            w.HANDLE,
        ),
        "CloseHandle": ([w.HANDLE], w.BOOL),
        "LocalFree": ([w.LPVOID], w.LPVOID),
        "GetCurrentProcess": ([], w.HANDLE),
        "GetFileInformationByHandle": ([w.HANDLE, ctypes.POINTER(_FileInfo)], w.BOOL),
        "ReadFile": ([w.HANDLE, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID], w.BOOL),
        "WriteFile": ([w.HANDLE, w.LPCVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID], w.BOOL),
        "SetFileInformationByHandle": ([w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD], w.BOOL),
        "GetFileType": ([w.HANDLE], w.DWORD),
        "GetDriveTypeW": ([w.LPCWSTR], w.UINT),
    }
    for name, (arguments, result) in signatures.items():
        getattr(kernel, name).argtypes, getattr(kernel, name).restype = arguments, result
    signatures = {
        "OpenProcessToken": ([w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)], w.BOOL),
        "GetTokenInformation": (
            [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)],
            w.BOOL,
        ),
        "ConvertSidToStringSidW": ([w.LPVOID, ctypes.POINTER(w.LPWSTR)], w.BOOL),
        "ConvertStringSecurityDescriptorToSecurityDescriptorW": (
            [w.LPCWSTR, w.DWORD, ctypes.POINTER(w.LPVOID), w.LPVOID],
            w.BOOL,
        ),
        "GetSecurityInfo": (
            [
                w.HANDLE,
                ctypes.c_int,
                w.DWORD,
                ctypes.POINTER(w.LPVOID),
                w.LPVOID,
                ctypes.POINTER(w.LPVOID),
                w.LPVOID,
                ctypes.POINTER(w.LPVOID),
            ],
            w.DWORD,
        ),
        "GetAce": ([w.LPVOID, w.DWORD, ctypes.POINTER(w.LPVOID)], w.BOOL),
        "GetSecurityDescriptorDacl": (
            [w.LPVOID, ctypes.POINTER(w.BOOL), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.BOOL)],
            w.BOOL,
        ),
        "SetSecurityInfo": (
            [w.HANDLE, ctypes.c_int, w.DWORD, w.LPVOID, w.LPVOID, w.LPVOID, w.LPVOID],
            w.DWORD,
        ),
    }
    for name, (arguments, result) in signatures.items():
        getattr(security, name).argtypes, getattr(security, name).restype = arguments, result
    return kernel, security


def _last_error() -> int:
    return getattr(ctypes, "get_last_error", lambda: 0)()


def _check(ok, operation: str) -> None:
    if not ok:
        raise OSError(_last_error(), f"Windows attachment: {operation} failed")


def _sid_text(kernel, security, sid) -> str:
    text = w.LPWSTR()
    _check(security.ConvertSidToStringSidW(sid, ctypes.byref(text)), "read SID")
    try:
        if text.value is None:
            raise OSError("Windows attachment security SID is unavailable")
        return text.value
    finally:
        kernel.LocalFree(text)


def _current_user(kernel, security) -> str:
    token, size = w.HANDLE(), w.DWORD()
    _check(
        security.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)), "open token"
    )
    try:
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        _check(
            security.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)), "token user"
        )
        return _sid_text(kernel, security, ctypes.c_void_p.from_buffer(buffer).value)
    finally:
        kernel.CloseHandle(token)


@contextlib.contextmanager
def _private_attributes(kernel, security, user: str, *, directory: bool):
    rights = _FULL_ACCESS if directory else _FILE_ACCESS
    descriptor = w.LPVOID()
    _check(
        security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            f"O:{user}D:P(A;;0x{rights:x};;;{user})(A;;0x{rights:x};;;SY)",
            1,
            ctypes.byref(descriptor),
            None,
        ),
        "private DACL",
    )
    try:
        yield _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
    finally:
        kernel.LocalFree(descriptor)


def _validate_security(kernel, security, handle, user: str, *, cache: bool) -> None:
    owner, dacl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
    error = security.GetSecurityInfo(
        handle, 1, 5, ctypes.byref(owner), None, ctypes.byref(dacl), None, ctypes.byref(descriptor)
    )
    if error:
        raise OSError(error, "Windows attachment security lookup failed")
    try:
        trusted = {user, "S-1-5-18", "S-1-5-32-544"}
        if not cache:
            trusted.add(_TRUSTED_INSTALLER)
        if not owner or not dacl or _sid_text(kernel, security, owner) not in trusted:
            raise OSError("Windows attachment path has an untrusted owner or null DACL")
        # OWNER RIGHTS applies only to the owner validated above.
        trusted_grants = trusted | {"S-1-3-4"}
        dacl_address = dacl.value
        if dacl_address is None:
            raise OSError("Windows attachment DACL is unavailable")
        for index in range(ctypes.c_ushort.from_address(dacl_address + 4).value):
            ace = w.LPVOID()
            _check(security.GetAce(dacl, index, ctypes.byref(ace)), "read ACL")
            address = ace.value
            if not address:
                raise OSError("Windows attachment ACE is unavailable")
            kind, flags = (
                ctypes.c_ubyte.from_address(address).value,
                ctypes.c_ubyte.from_address(address + 1).value,
            )
            if kind not in (0, 1):
                raise OSError("Windows attachment path has an unsupported ACE")
            if kind == 1 or flags & 8:
                continue
            rights = ctypes.c_uint32.from_address(address + 4).value
            mutation = 0x500D0156 if cache else 0x500D0152
            if (
                rights & mutation
                and _sid_text(kernel, security, address + 8) not in trusted_grants
            ):
                raise OSError("Windows attachment path grants untrusted mutation")
    finally:
        kernel.LocalFree(descriptor)


def _tighten_security(_kernel, security, handle, attributes) -> None:
    present, defaulted, dacl = w.BOOL(), w.BOOL(), w.LPVOID()
    _check(
        security.GetSecurityDescriptorDacl(
            attributes.descriptor,
            ctypes.byref(present),
            ctypes.byref(dacl),
            ctypes.byref(defaulted),
        ),
        "private ACL",
    )
    if not present or not dacl:
        raise OSError("Windows attachment private ACL is missing")
    error = security.SetSecurityInfo(handle, 1, 0x80000004, None, None, dacl, None)
    if error:
        raise OSError(error, "Windows attachment private ACL update failed")


def _info(kernel, handle) -> _FileInfo:
    info = _FileInfo()
    _check(kernel.GetFileInformationByHandle(handle, ctypes.byref(info)), "file identity")
    if info.attributes & _REPARSE_POINT:
        raise OSError("Windows attachment path is a reparse point")
    return info


def _native_path(path: Path) -> str:
    return "\\\\?\\" + str(path)


@contextlib.contextmanager
def _locked_directory(directory: Path) -> Iterator[tuple]:
    directory = Path(os.path.abspath(directory))
    if not re.fullmatch(r"[A-Za-z]:\\", directory.anchor):
        raise OSError("Windows attachment cache requires a local drive")
    kernel, security = _windows()
    if kernel.GetDriveTypeW(directory.anchor) != 3:
        raise OSError("Windows attachment cache requires a fixed local drive")
    user = _current_user(kernel, security)
    handles = []
    try:
        with _private_attributes(kernel, security, user, directory=True) as attributes:
            # List access makes read-only sharing effective against data mutation.
            for path in (*reversed(directory.parents), directory):
                final = path == directory
                access = _LIST_DIRECTORY | _READ_CONTROL | (_WRITE_DAC if final else 0)
                if handles:
                    handle = _relative_open(
                        handles[-1],
                        path.name,
                        access,
                        3,
                        directory=True,
                        attributes=attributes,
                    )
                else:
                    handle = kernel.CreateFileW(
                        _native_path(path),
                        access,
                        _SHARE_READ,
                        None,
                        3,
                        _OPEN_REPARSE_POINT | _BACKUP_SEMANTICS,
                        None,
                    )
                    _check(handle != _INVALID_HANDLE, "lock drive root")
                handles.append(handle)
                if not _info(kernel, handle).attributes & _DIRECTORY:
                    raise OSError("Windows attachment ancestor is not a directory")
                _validate_security(kernel, security, handle, user, cache=final)
                if final:
                    _tighten_security(kernel, security, handle, attributes)
            try:
                yield kernel, security, user, directory, handles[-1]
            finally:
                for handle in handles:
                    _info(kernel, handle)
    finally:
        for handle in reversed(handles):
            kernel.CloseHandle(handle)


def _validate_name(name: str) -> None:
    if (
        not name
        or name in (".", "..")
        or name.endswith((".", " "))
        or any(character in '<>:"/\\|?*' or ord(character) < 32 for character in name)
        or _RESERVED.match(name.split(".", 1)[0].rstrip(" ") + ".")
        or name.split(".", 1)[0].rstrip(" ").upper() in {"CLOCK$", "CONIN$", "CONOUT$"}
    ):
        raise ValueError("Unsafe Windows attachment filename")
    try:
        if len(name.encode("utf-16-le")) > 510:
            raise ValueError("Windows attachment filename exceeds the component limit")
    except UnicodeError as exc:
        raise ValueError("Invalid Unicode attachment filename") from exc


def _open_existing(parent_handle, name: str):
    for attempt in range(50):
        try:
            return _relative_open(
                parent_handle,
                name,
                0x80000000 | _READ_CONTROL | _WRITE_DAC,
                1,
                directory=False,
            )
        except OSError as exc:
            if exc.errno not in (32, 33) or attempt == 49:
                raise
            time.sleep(0.02)
    raise AssertionError("Windows attachment retry loop exhausted")


def _read_handle(kernel, handle, size: int) -> bytes:
    if size > _MAX_BYTES:
        raise OSError("Windows attachment exceeds the bounded read limit")
    chunks = []
    while size:
        buffer, read = ctypes.create_string_buffer(min(size, 1024 * 1024)), w.DWORD()
        _check(
            kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(read), None),
            "read attachment",
        )
        if not read.value:
            break
        chunks.append(buffer.raw[: read.value])
        size -= read.value
    return b"".join(chunks)


def _write_handle(kernel, handle, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        chunk, written = content[offset : offset + 1024 * 1024], w.DWORD()
        _check(
            kernel.WriteFile(handle, chunk, len(chunk), ctypes.byref(written), None),
            "write attachment",
        )
        if not written.value:
            raise OSError("Windows attachment write made no progress")
        offset += written.value


def _regular_file(kernel, security, handle, user: str) -> _FileInfo:
    info = _info(kernel, handle)
    if kernel.GetFileType(handle) != 1 or info.attributes & _DIRECTORY or info.links != 1:
        raise OSError("Windows attachment leaf is not a single-link regular file")
    _validate_security(kernel, security, handle, user, cache=True)
    return info


def _place(
    kernel, security, user: str, parent_handle, path: Path, content: bytes
) -> Literal["placed", "taken"]:
    with _private_attributes(kernel, security, user, directory=False) as attributes:
        try:
            handle = _relative_open(
                parent_handle,
                path.name,
                0xC0030000 | _WRITE_DAC,
                2,
                directory=False,
                attributes=attributes,
            )
        except OSError as exc:
            if exc.errno not in (80, 183):
                raise
            handle = _open_existing(parent_handle, path.name)
            try:
                info = _regular_file(kernel, security, handle, user)
                size = (info.size_high << 32) | info.size_low
                if size != len(content) or _read_handle(kernel, handle, size) != content:
                    return "taken"
                _tighten_security(kernel, security, handle, attributes)
                _regular_file(kernel, security, handle, user)
                return "placed"
            finally:
                kernel.CloseHandle(handle)
        try:
            try:
                _regular_file(kernel, security, handle, user)
                _write_handle(kernel, handle, content)
                _regular_file(kernel, security, handle, user)
            except BaseException:
                delete = w.BOOL(True)
                _check(
                    kernel.SetFileInformationByHandle(
                        handle, 4, ctypes.byref(delete), ctypes.sizeof(delete)
                    ),
                    "delete partial attachment",
                )
                raise
            return "placed"
        finally:
            kernel.CloseHandle(handle)


def materialize_attachment(directory: Path, filename: str, raw_bytes: bytes) -> Path | None:
    """Create or reuse identical private bytes without overwriting any leaf."""
    _validate_name(filename)
    if len(raw_bytes) > _MAX_BYTES:
        raise ValueError("Windows attachment exceeds the upload limit")
    stem, suffix = os.path.splitext(filename)
    digest = hashlib.sha256(raw_bytes).hexdigest()[:12]
    if len(suffix.encode("utf-16-le")) > 484:
        stem, suffix = filename, ""
    available = 484 - len(suffix.encode("utf-16-le"))
    while len(stem.encode("utf-16-le")) > available:
        stem = stem[:-1]
    collision = f"{stem}_{digest}{suffix}"
    with _locked_directory(directory) as (kernel, security, user, directory, parent_handle):
        for name in (filename, collision):
            _validate_name(name)
            if (
                _place(kernel, security, user, parent_handle, directory / name, raw_bytes)
                == "placed"
            ):
                return directory / name
    return None


def _read_source(kernel, security, user: str, parent_handle, path: Path) -> bytes:
    _validate_name(path.name)
    handle = _open_existing(parent_handle, path.name)
    try:
        info = _regular_file(kernel, security, handle, user)
        with _private_attributes(kernel, security, user, directory=False) as attributes:
            _tighten_security(kernel, security, handle, attributes)
        size = (info.size_high << 32) | info.size_low
        content = _read_handle(kernel, handle, size)
        if len(content) != size:
            raise OSError("Windows attachment source changed during read")
        _regular_file(kernel, security, handle, user)
        return content
    finally:
        kernel.CloseHandle(handle)


def secure_alias(path: Path, alias_name: str) -> Path:
    """Copy validated source bytes into an exclusive private sibling alias."""
    _validate_name(alias_name)
    with _locked_directory(path.parent) as (kernel, security, user, directory, parent_handle):
        content = _read_source(kernel, security, user, parent_handle, directory / path.name)
        alias = directory / alias_name
        if _place(kernel, security, user, parent_handle, alias, content) != "placed":
            raise OSError("Windows attachment alias contains different bytes")
        return alias


def resize_metadata_path(path: Path, *, width: int, height: int) -> Path:
    """Encode Codex resize metadata using the same private file-handle rules."""
    with _locked_directory(path.parent) as (kernel, security, user, directory, parent_handle):
        content = _read_source(kernel, security, user, parent_handle, directory / path.name)
        name = (
            f"{path.stem[:80]}_{hashlib.sha256(content).hexdigest()[:12]}"
            f"__omnigent-downscaled-from-{width}x{height}"
            f"-request-crop-for-fine-detail{path.suffix}"
        )
        _validate_name(name)
        alias = directory / name
        if _place(kernel, security, user, parent_handle, alias, content) != "placed":
            raise OSError("Windows attachment resize alias contains different bytes")
        return alias
