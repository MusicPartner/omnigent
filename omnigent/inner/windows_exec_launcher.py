"""Opt-in Windows x64 launcher with private invocation files.

The native job contains process lifetime only; it adds no filesystem or network
isolation. The executable bytes stay immutable; unlinking it removes its config
stream too. Native execution remains gated while release signing is unresolved.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as w
import hashlib
import json
import os
import platform
import secrets
import struct
from pathlib import Path

CONFIG_STREAM = ":omnigent.config"
SELECTOR = "OMNIGENT_WINDOWS_EXEC_LAUNCHER"
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_READ = 0x80000000
_WRITE = 0x40000000
_READ_CONTROL = 0x00020000
_SHARE_READ = 1
_OPEN_EXISTING = 3
_OPEN_REPARSE_POINT = 0x00200000
_ATTRIBUTE_REPARSE_POINT = 0x400
_MAX_UNITS = 32768


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [
        ("length", w.DWORD),
        ("descriptor", w.LPVOID),
        ("inherit", w.BOOL),
    ]


class _TokenUser(ctypes.Structure):
    _fields_ = [("sid", w.LPVOID), ("attributes", w.DWORD)]


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


def _win_dll(name: str):
    loader = getattr(ctypes, "WinDLL", None)
    if loader is None:
        raise OSError("Windows launcher: native library loading is unavailable")
    return loader(name, use_last_error=True)


def _last_error() -> int:
    query = getattr(ctypes, "get_last_error", None)
    if query is None:
        raise OSError("Windows launcher: native error reporting is unavailable")
    return query()


def _windows():
    kernel = _win_dll("kernel32")
    security = _win_dll("advapi32")
    kernel.CreateFileW.argtypes = [
        w.LPCWSTR,
        w.DWORD,
        w.DWORD,
        ctypes.POINTER(_SecurityAttributes),
        w.DWORD,
        w.DWORD,
        w.HANDLE,
    ]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.LocalFree.argtypes = [w.LPVOID]
    kernel.LocalFree.restype = w.LPVOID
    kernel.WriteFile.argtypes = [w.HANDLE, w.LPCVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID]
    kernel.WriteFile.restype = w.BOOL
    kernel.ReadFile.argtypes = [w.HANDLE, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID]
    kernel.ReadFile.restype = w.BOOL
    kernel.GetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.POINTER(_FileInfo)]
    kernel.GetFileInformationByHandle.restype = w.BOOL
    kernel.CreateDirectoryW.argtypes = [w.LPCWSTR, ctypes.POINTER(_SecurityAttributes)]
    kernel.CreateDirectoryW.restype = w.BOOL
    security.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    security.OpenProcessToken.restype = w.BOOL
    security.GetTokenInformation.argtypes = [
        w.HANDLE,
        ctypes.c_int,
        w.LPVOID,
        w.DWORD,
        ctypes.POINTER(w.DWORD),
    ]
    security.GetTokenInformation.restype = w.BOOL
    security.ConvertSidToStringSidW.argtypes = [w.LPVOID, ctypes.POINTER(w.LPWSTR)]
    security.ConvertSidToStringSidW.restype = w.BOOL
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        w.LPCWSTR,
        w.DWORD,
        ctypes.POINTER(w.LPVOID),
        ctypes.POINTER(w.DWORD),
    ]
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = w.BOOL
    security.GetSecurityInfo.argtypes = [
        w.HANDLE,
        ctypes.c_int,
        w.DWORD,
        ctypes.POINTER(w.LPVOID),
        w.LPVOID,
        ctypes.POINTER(w.LPVOID),
        w.LPVOID,
        ctypes.POINTER(w.LPVOID),
    ]
    security.GetSecurityInfo.restype = w.DWORD
    security.GetAce.argtypes = [w.LPVOID, w.DWORD, ctypes.POINTER(w.LPVOID)]
    security.GetAce.restype = w.BOOL
    security.GetSecurityDescriptorControl.argtypes = [
        w.LPVOID,
        ctypes.POINTER(w.WORD),
        ctypes.POINTER(w.DWORD),
    ]
    security.GetSecurityDescriptorControl.restype = w.BOOL
    return kernel, security


def _check(ok, operation: str) -> None:
    if not ok:
        raise OSError(_last_error(), f"Windows launcher: {operation} failed")


def _current_user_sid(kernel, security) -> str:
    token, length, text = w.HANDLE(), w.DWORD(), w.LPWSTR()
    _check(security.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)), "token")
    try:
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        buffer = ctypes.create_string_buffer(length.value)
        _check(
            security.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)),
            "token user",
        )
        sid = ctypes.cast(buffer, ctypes.POINTER(_TokenUser)).contents.sid
        _check(security.ConvertSidToStringSidW(sid, ctypes.byref(text)), "user SID")
        try:
            value = text.value
            if value is None:
                raise OSError("Windows launcher: token user SID is unavailable")
            return value
        finally:
            kernel.LocalFree(text)
    finally:
        kernel.CloseHandle(token)


def _private_security(kernel, security):
    user = _current_user_sid(kernel, security)
    descriptor = w.LPVOID()
    # Protected DACL: do not inherit broad permissions from the temp directory.
    sddl = f"O:{user}D:P(A;;FA;;;{user})(A;;FA;;;SY)"
    _check(
        security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None
        ),
        "private DACL",
    )
    return _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)


def _write_handle(kernel, handle, content: bytes) -> None:
    written = w.DWORD()
    _check(kernel.WriteFile(handle, content, len(content), ctypes.byref(written), None), "write")
    if written.value != len(content):
        raise OSError("Windows launcher: incomplete file write")


def _sid_text(kernel, security, sid) -> str:
    text = w.LPWSTR()
    _check(security.ConvertSidToStringSidW(sid, ctypes.byref(text)), "security SID")
    try:
        value = text.value
        if value is None:
            raise OSError("Windows launcher: security SID is unavailable")
        return value
    finally:
        kernel.LocalFree(text)


def _validate_directory(kernel, security, path: Path, user: str, *, private: bool) -> None:
    trusted = {
        user,
        "S-1-5-18",
        "S-1-5-32-544",
        "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464",
    }
    handle = kernel.CreateFileW(
        str(path),
        _READ_CONTROL,
        _SHARE_READ,
        None,
        _OPEN_EXISTING,
        _OPEN_REPARSE_POINT | 0x02000000,
        None,
    )
    _check(handle != _INVALID_HANDLE, "open invocation directory")
    try:
        info = _FileInfo()
        _check(kernel.GetFileInformationByHandle(handle, ctypes.byref(info)), "directory identity")
        if info.attributes & _ATTRIBUTE_REPARSE_POINT or not info.attributes & 0x10:
            raise OSError(
                "Windows launcher: invocation ancestor is a reparse point or not a directory"
            )
        owner, dacl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
        result = security.GetSecurityInfo(
            handle,
            1,
            5,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result:
            raise OSError(result, "Windows launcher: directory security lookup failed")
        try:
            if (
                _sid_text(kernel, security, owner) not in ({user} if private else trusted)
                or not dacl
            ):
                raise OSError("Windows launcher: invocation directory has untrusted owner/DACL")
            control, revision = w.WORD(), w.DWORD()
            _check(
                security.GetSecurityDescriptorControl(
                    descriptor, ctypes.byref(control), ctypes.byref(revision)
                ),
                "directory security control",
            )
            if private and not control.value & 0x1000:
                raise OSError("Windows launcher: invocation directory DACL is not protected")
            dacl_address = dacl.value
            if dacl_address is None:
                raise OSError("Windows launcher: invocation directory DACL is unavailable")
            ace_count = ctypes.c_ushort.from_address(dacl_address + 4).value
            permitted = set()
            for index in range(ace_count):
                ace = w.LPVOID()
                _check(security.GetAce(dacl, index, ctypes.byref(ace)), "directory ACE")
                address = ace.value
                if address is None:
                    raise OSError("Windows launcher: invocation directory ACE is unavailable")
                kind = ctypes.c_ubyte.from_address(address).value
                flags = ctypes.c_ubyte.from_address(address + 1).value
                if kind not in {0, 1}:
                    raise OSError("Windows launcher: unsupported invocation-directory ACE")
                if private and (kind != 0 or flags & 0x18):
                    raise OSError("Windows launcher: invocation directory is not private")
                if flags & 8:
                    continue
                if kind == 1:  # Denied rights cannot grant directory replacement.
                    continue
                rights = ctypes.c_uint32.from_address(address + 4).value
                sid = _sid_text(kernel, security, address + 8)
                if private:
                    if sid in {user, "S-1-5-18"}:
                        if rights != 0x1F01FF:
                            raise OSError(
                                "Windows launcher: invocation directory lacks private grants"
                            )
                        permitted.add(sid)
                    elif rights & 0x500D0156:
                        raise OSError("Windows launcher: invocation directory is not private")
                elif rights & 0x500D0040 and sid not in trusted:
                    raise OSError(
                        "Windows launcher: invocation ancestor grants untrusted mutation"
                    )
            if private and permitted != {user, "S-1-5-18"}:
                raise OSError("Windows launcher: invocation directory lacks private grants")
        finally:
            kernel.LocalFree(descriptor)
    finally:
        kernel.CloseHandle(handle)


def _known_profile() -> Path:
    class Guid(ctypes.Structure):
        _fields_ = [("one", w.DWORD), ("two", w.WORD), ("three", w.WORD), ("four", w.BYTE * 8)]

    folder = Guid(
        0x5E6C858F, 0x0E22, 0x4760, (w.BYTE * 8)(0x9A, 0xFE, 0xEA, 0x33, 0x17, 0xB6, 0x71, 0x73)
    )
    text = w.LPWSTR()
    shell = _win_dll("shell32")
    shell.SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(Guid),
        w.DWORD,
        w.HANDLE,
        ctypes.POINTER(w.LPWSTR),
    ]
    shell.SHGetKnownFolderPath.restype = w.LONG
    result = shell.SHGetKnownFolderPath(ctypes.byref(folder), 0, None, ctypes.byref(text))
    if result:
        raise OSError(f"Windows launcher: per-user application data lookup failed ({result:#x})")
    ole = _win_dll("ole32")
    ole.CoTaskMemFree.argtypes = [w.LPVOID]
    try:
        value = text.value
        if value is None:
            raise OSError("Windows launcher: per-user profile path is unavailable")
        return Path(value)
    finally:
        ole.CoTaskMemFree(text)


def _private_directory(kernel, security, parent: Path, attributes) -> Path:
    parent = parent.absolute()
    kernel.GetDriveTypeW.argtypes = [w.LPCWSTR]
    kernel.GetDriveTypeW.restype = w.UINT
    kernel.GetVolumeInformationW.argtypes = [
        w.LPCWSTR,
        w.LPWSTR,
        w.DWORD,
        w.LPVOID,
        w.LPVOID,
        w.LPVOID,
        w.LPWSTR,
        w.DWORD,
    ]
    kernel.GetVolumeInformationW.restype = w.BOOL
    filesystem = ctypes.create_unicode_buffer(32)
    if kernel.GetDriveTypeW(parent.anchor) != 3:
        raise OSError("Windows launcher: invocation storage requires a local NTFS volume")
    _check(
        kernel.GetVolumeInformationW(
            parent.anchor, None, 0, None, None, None, filesystem, len(filesystem)
        ),
        "invocation volume",
    )
    if filesystem.value != "NTFS":
        raise OSError("Windows launcher: invocation storage requires a local NTFS volume")
    user = _current_user_sid(kernel, security)
    for ancestor in reversed((parent, *parent.parents)):
        _validate_directory(kernel, security, ancestor, user, private=False)
    path = parent / "Omnigent-WindowsLaunchers"
    if not kernel.CreateDirectoryW(str(path), ctypes.byref(attributes)):
        if _last_error() != 183:
            _check(False, "create private invocation directory")
    _validate_directory(kernel, security, path, user, private=True)
    return path


def _read_asset(kernel, executable: Path) -> bytes:
    handle = kernel.CreateFileW(
        str(executable), _READ, _SHARE_READ, None, _OPEN_EXISTING, _OPEN_REPARSE_POINT, None
    )
    _check(handle != _INVALID_HANDLE, "open native asset")
    try:
        info = _FileInfo()
        _check(kernel.GetFileInformationByHandle(handle, ctypes.byref(info)), "asset identity")
        size = (info.size_high << 32) | info.size_low
        if info.attributes & _ATTRIBUTE_REPARSE_POINT or not 0 < size <= 16 * 1024 * 1024:
            raise OSError("Windows launcher: invalid native asset or reparse point")
        content, read = ctypes.create_string_buffer(size), w.DWORD()
        _check(
            kernel.ReadFile(handle, content, size, ctypes.byref(read), None), "read native asset"
        )
        if read.value != size:
            raise OSError("Windows launcher: incomplete native asset read")
        return content.raw
    finally:
        kernel.CloseHandle(handle)


def _require_x64() -> None:
    if (
        os.name != "nt"
        or platform.machine().lower() not in {"amd64", "x86_64"}
        or struct.calcsize("P") != 8
    ):
        raise OSError("The native Windows launcher requires native Windows x64 Python")
    if _native_architecture() != (0, 0x8664):
        raise OSError("The native Windows launcher requires a native x64 operating system")


def _native_architecture() -> tuple[int, int]:
    kernel = _win_dll("kernel32")
    try:
        query = kernel.IsWow64Process2
    except AttributeError as error:
        raise OSError(
            "Windows launcher: native architecture verification is unavailable"
        ) from error
    kernel.GetCurrentProcess.restype = w.HANDLE
    query.argtypes = [w.HANDLE, ctypes.POINTER(w.WORD), ctypes.POINTER(w.WORD)]
    query.restype = w.BOOL
    process, native = w.WORD(), w.WORD()
    _check(
        query(kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(native)),
        "native architecture",
    )
    return process.value, native.value


def _configuration(source: str, interpreter: str, active: bool) -> bytes:
    if (
        not interpreter
        or not os.path.isabs(interpreter)
        or any(character in interpreter for character in '\0\r\n"')
    ):
        raise OSError("The native Windows launcher requires an absolute interpreter filename")
    if not source or "\0" in source:
        raise OSError("The native Windows launcher requires nonempty source without NUL")
    try:
        encoded_interpreter = interpreter.encode("utf-16-le")
        encoded_source = source.encode("utf-16-le")
    except UnicodeError as error:
        raise OSError("The native Windows launcher requires valid Unicode") from error
    units = len(encoded_interpreter) // 2, len(encoded_source) // 2
    if max(units) >= _MAX_UNITS:
        raise OSError("The native Windows launcher configuration exceeds its size limit")
    return (
        b"OJLCFG01"
        + struct.pack("<III", int(active), *units)
        + encoded_interpreter
        + encoded_source
    )


def _validate_pe_x64(asset: bytes) -> None:
    if len(asset) < 64 or asset[:2] != b"MZ":
        raise OSError("Windows launcher: native asset is not an x64 PE executable")
    offset = struct.unpack_from("<I", asset, 60)[0]
    if (
        offset + 26 > len(asset)
        or asset[offset : offset + 4] != b"PE\0\0"
        or struct.unpack_from("<H", asset, offset + 4)[0] != 0x8664
        or struct.unpack_from("<H", asset, offset + 24)[0] != 0x20B
    ):
        raise OSError("Windows launcher: native asset is not an x64 PE executable")


def _create_invocation(
    source: str,
    interpreter: str,
    executable: Path,
    *,
    active: bool,
    directory: Path | None = None,
    expected_sha256: str | None = None,
) -> str:
    """Create a private immutable copy; used directly only by native test fixtures."""
    _require_x64()
    config = _configuration(source, interpreter, active)
    kernel, security = _windows()
    asset = _read_asset(kernel, executable)
    _validate_pe_x64(asset)
    if expected_sha256 is not None and hashlib.sha256(asset).hexdigest() != expected_sha256:
        raise OSError("Windows launcher: native asset SHA-256 mismatch")
    attributes = _private_security(kernel, security)
    path = None
    handle = stream = _INVALID_HANDLE
    created = False
    try:
        container = _private_directory(kernel, security, directory or _known_profile(), attributes)
        path = container / f"omnigent-sandbox-{secrets.token_hex(24)}.exe"
        handle = kernel.CreateFileW(
            str(path),
            _WRITE | _READ_CONTROL,
            _SHARE_READ,
            ctypes.byref(attributes),
            1,
            _OPEN_REPARSE_POINT,
            None,
        )
        _check(handle != _INVALID_HANDLE, "create private executable")
        created = True
        _write_handle(kernel, handle, asset)
        stream = kernel.CreateFileW(
            str(path) + CONFIG_STREAM,
            _WRITE,
            _SHARE_READ,
            ctypes.byref(attributes),
            1,
            _OPEN_REPARSE_POINT,
            None,
        )
        _check(stream != _INVALID_HANDLE, "create private config stream (NTFS required)")
        _write_handle(kernel, stream, config)
    except BaseException:
        for opened in (stream, handle):
            if opened != _INVALID_HANDLE:
                kernel.CloseHandle(opened)
        stream = handle = _INVALID_HANDLE
        if created and path is not None:
            path.unlink()
        raise
    finally:
        for opened in (stream, handle):
            if opened != _INVALID_HANDLE:
                kernel.CloseHandle(opened)
        kernel.LocalFree(attributes.descriptor)
    return str(path)


def _verify_signature(path: str, expected_thumbprint: str) -> None:
    class Guid(ctypes.Structure):
        _fields_ = [("one", w.DWORD), ("two", w.WORD), ("three", w.WORD), ("four", w.BYTE * 8)]

    class File(ctypes.Structure):
        _fields_ = [
            ("size", w.DWORD),
            ("path", w.LPCWSTR),
            ("file", w.HANDLE),
            ("subject", w.LPVOID),
        ]

    class Trust(ctypes.Structure):
        _fields_ = [
            ("size", w.DWORD),
            ("policy", w.LPVOID),
            ("sip", w.LPVOID),
            ("ui", w.DWORD),
            ("revocation", w.DWORD),
            ("choice", w.DWORD),
            ("file", ctypes.POINTER(File)),
            ("action", w.DWORD),
            ("state", w.HANDLE),
            ("url", w.LPCWSTR),
            ("flags", w.DWORD),
            ("context", w.DWORD),
            ("signature", w.LPVOID),
        ]

    class ProviderCertificate(ctypes.Structure):
        _fields_ = [("size", w.DWORD), ("certificate", w.LPVOID)]

    class ProviderSigner(ctypes.Structure):
        _fields_ = [
            ("size", w.DWORD),
            ("verified_at", w.FILETIME),
            ("count", w.DWORD),
            ("certificates", ctypes.POINTER(ProviderCertificate)),
        ]

    class Certificate(ctypes.Structure):
        _fields_ = [("encoding", w.DWORD), ("encoded", w.LPVOID), ("length", w.DWORD)]

    action = Guid(
        0x00AAC56B, 0xCD44, 0x11D0, (w.BYTE * 8)(0x8C, 0xC2, 0, 0xC0, 0x4F, 0xC2, 0x95, 0xEE)
    )
    file = File(ctypes.sizeof(File), path, None, None)
    trust = Trust()
    trust.size = ctypes.sizeof(Trust)
    trust.ui, trust.choice, trust.action = 2, 1, 1
    trust.file = ctypes.pointer(file)
    trust.flags = 0x1000  # Use cached certificate retrieval for predictable offline startup.
    library = _win_dll("wintrust")
    verifier = library.WinVerifyTrust
    verifier.argtypes = [w.HWND, ctypes.POINTER(Guid), ctypes.POINTER(Trust)]
    verifier.restype = w.LONG
    try:
        status = verifier(None, ctypes.byref(action), ctypes.byref(trust))
        if status:
            raise OSError(
                f"Windows launcher: Authenticode trust verification failed ({status:#x})"
            )
        provider = library.WTHelperProvDataFromStateData
        provider.argtypes, provider.restype = [w.HANDLE], w.LPVOID
        signer = library.WTHelperGetProvSignerFromChain
        signer.argtypes = [w.LPVOID, w.DWORD, w.BOOL, w.DWORD]
        signer.restype = ctypes.POINTER(ProviderSigner)
        data = provider(trust.state)
        verified = signer(data, 0, False, 0) if data else None
        if not verified or not verified.contents.count or not verified.contents.certificates:
            raise OSError("Windows launcher: verified signing certificate is unavailable")
        context = verified.contents.certificates[0].certificate
        if not context:
            raise OSError("Windows launcher: verified signing certificate is unavailable")
        certificate = ctypes.cast(context, ctypes.POINTER(Certificate)).contents
        fingerprint = (
            hashlib.sha1(
                ctypes.string_at(certificate.encoded, certificate.length), usedforsecurity=False
            )
            .hexdigest()
            .upper()
        )
        if fingerprint != expected_thumbprint:
            raise OSError("Windows launcher: verified signing certificate thumbprint mismatch")
    finally:
        trust.action = 2
        verifier(None, ctypes.byref(action), ctypes.byref(trust))


def create_native_exec_launcher(source: str, interpreter: str, *, active: bool) -> str:
    """Resolve a reviewed packaged asset, then create one invocation."""
    _require_x64()
    directory = Path(__file__).resolve().parents[1] / "resources" / "windows_launcher"
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OSError("Windows launcher: reviewed native asset manifest is unavailable") from error
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != 1
        or manifest.get("architecture") != "amd64"
        or manifest.get("filename") != "private_job_launcher-x64.exe"
        or not isinstance(manifest.get("sha256"), str)
        or len(manifest["sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in manifest["sha256"])
    ):
        raise OSError("Windows launcher: unsupported native asset manifest")
    signing = manifest.get("signing")
    if not isinstance(signing, dict) or signing.get("status") not in {"unsigned", "authenticode"}:
        raise OSError("Windows launcher: native asset signing metadata is unavailable")
    development = os.environ.get(SELECTOR) == "native-dev"
    if not development and (
        manifest.get("release_approved") is not True or signing["status"] != "authenticode"
    ):
        raise OSError("Windows launcher: native asset release signing/review gate is unresolved")
    thumbprint = signing.get("certificate_thumbprint")
    if not development and (
        not isinstance(thumbprint, str)
        or len(thumbprint) != 40
        or any(character not in "0123456789ABCDEF" for character in thumbprint)
    ):
        raise OSError("Windows launcher: approved signing certificate thumbprint is unavailable")
    path = _create_invocation(
        source,
        interpreter,
        directory / manifest["filename"],
        active=active,
        expected_sha256=manifest["sha256"],
    )
    try:
        if not development:
            if not isinstance(thumbprint, str):
                raise OSError(
                    "Windows launcher: approved signing certificate thumbprint is unavailable"
                )
            _verify_signature(path, thumbprint)
    except BaseException:
        Path(path).unlink()
        raise
    return path
