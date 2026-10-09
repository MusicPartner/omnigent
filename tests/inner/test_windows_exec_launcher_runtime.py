"""Runtime selector gates and native invocation-file lifecycle."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from omnigent.inner import sandbox
from omnigent.inner import windows_exec_launcher as launcher
from tests.inner.test_windows_private_job_launcher import native_stubs as _native_fixture
from tests.inner.windows_private_job_launcher import private_test_directory as _test_directory

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows launcher")
_real_known_profile = launcher._known_profile


@pytest.fixture
def tmp_path():
    yield from _test_directory.__wrapped__()


@pytest.fixture(autouse=True)
def isolate_invocation_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "_known_profile", lambda: tmp_path)


@pytest.fixture(scope="module")
def native_stubs(tmp_path_factory):
    return _native_fixture.__wrapped__(tmp_path_factory)


def _inactive_policy():
    return sandbox.SandboxPolicy("none", False, None, [], [], True)


def _asset_manifest(tmp_path, monkeypatch, executable, **overrides):
    resource = tmp_path / "omnigent" / "resources" / "windows_launcher"
    resource.mkdir(parents=True)
    (resource / "private_job_launcher-x64.exe").write_bytes(executable.read_bytes())
    manifest = {
        "schema": 1,
        "architecture": "amd64",
        "filename": "private_job_launcher-x64.exe",
        "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "signing": {"status": "unsigned"},
        "release_approved": False,
    }
    manifest.update(overrides)
    (resource / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(launcher, "__file__", str(tmp_path / "omnigent" / "inner" / "leaf.py"))
    return resource


def test_runtime_default_preserves_legacy_filename(monkeypatch):
    monkeypatch.delenv(launcher.SELECTOR, raising=False)
    path = sandbox.create_exec_launcher(sys.executable, _inactive_policy())
    try:
        assert path.endswith(".cmd")
    finally:
        Path(path).unlink()


@pytest.mark.parametrize("architecture", [(0x8664, 0xAA64), (0x14C, 0x8664), (0, 0xAA64)])
def test_native_architecture_refuses_emulation(monkeypatch, architecture):
    monkeypatch.setattr(launcher, "_native_architecture", lambda: architecture)
    with pytest.raises(OSError, match="native x64 operating system"):
        launcher._require_x64()


@pytest.mark.parametrize("mode", ["native", "native-dev"])
def test_runtime_opted_in_errors_never_fall_back(monkeypatch, mode):
    monkeypatch.setenv(launcher.SELECTOR, mode)

    def fail(*args, **kwargs):
        raise OSError("native creation failed")

    monkeypatch.setattr(launcher, "create_native_exec_launcher", fail)
    with pytest.raises(OSError, match="native creation failed"):
        sandbox.create_exec_launcher(sys.executable, _inactive_policy())


def test_runtime_missing_asset_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(launcher.SELECTOR, "native-dev")
    monkeypatch.setattr(launcher, "__file__", str(tmp_path / "omnigent" / "inner" / "leaf.py"))
    with pytest.raises(OSError, match="manifest is unavailable"):
        sandbox.create_exec_launcher(sys.executable, _inactive_policy())


def test_runtime_native_refuses_unsigned_release(native_stubs, tmp_path, monkeypatch):
    _asset_manifest(tmp_path, monkeypatch, native_stubs[0])
    monkeypatch.setenv(launcher.SELECTOR, "native")
    with pytest.raises(OSError, match="signing/review gate"):
        sandbox.create_exec_launcher(sys.executable, _inactive_policy())


def test_runtime_dev_asset_runs_and_unlink_removes_config(native_stubs, tmp_path, monkeypatch):
    _asset_manifest(tmp_path, monkeypatch, native_stubs[0])
    monkeypatch.setenv(launcher.SELECTOR, "native-dev")
    policy = sandbox.SandboxPolicy("windows_jobobject", True, None, [], [], True)
    path = sandbox.create_exec_launcher(sys.executable, policy, cwd=str(tmp_path))
    try:
        assert path.endswith(".exe")
        assert Path(path).read_bytes() == native_stubs[0].read_bytes()
        assert Path(path + launcher.CONFIG_STREAM).read_bytes().startswith(b"OJLCFG01")
        result = subprocess.run(
            [path, "-c", "import os; print(os.getcwd())"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(tmp_path)
    finally:
        Path(path).unlink()
    assert not Path(path + launcher.CONFIG_STREAM).exists()


def test_runtime_bad_asset_hash_fails_before_copy(native_stubs, tmp_path, monkeypatch):
    _asset_manifest(tmp_path, monkeypatch, native_stubs[0], sha256="0" * 64)
    monkeypatch.setenv(launcher.SELECTOR, "native-dev")
    with pytest.raises(OSError, match="SHA-256 mismatch"):
        sandbox.create_exec_launcher(sys.executable, _inactive_policy())


def test_runtime_native_verifies_signature_after_release_gate(native_stubs, tmp_path, monkeypatch):
    _asset_manifest(
        tmp_path,
        monkeypatch,
        native_stubs[0],
        signing={"status": "authenticode", "certificate_thumbprint": "0" * 40},
        release_approved=True,
    )
    monkeypatch.setenv(launcher.SELECTOR, "native")
    with pytest.raises(OSError, match="Authenticode"):
        sandbox.create_exec_launcher(sys.executable, _inactive_policy())


def test_authenticode_verifier_binds_actual_trusted_microsoft_signer(native_stubs):
    executable = (
        Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )
    signed_file = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / (
        "PowerShell/7/pwsh.exe"
    )
    if not signed_file.is_file():
        signed_file = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / (
            "Microsoft Visual Studio/Installer/vswhere.exe"
        )
    assert signed_file.is_file(), "requires a public embedded-signed Microsoft executable"
    command = (
        "$ErrorActionPreference='Stop'; "
        "$sig=Get-AuthenticodeSignature -LiteralPath $args[0]; "
        "@{status=[string]$sig.Status;kind=[string]$sig.SignatureType;"
        "thumbprint=$sig.SignerCertificate.Thumbprint} | ConvertTo-Json -Compress"
    )
    quoted_file = "'" + str(signed_file).replace("'", "''") + "'"
    result = subprocess.run(
        [
            str(executable),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command.replace("$args[0]", quoted_file),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
        env={**os.environ, "PSModulePath": str(executable.parent / "Modules")},
    )
    signature = json.loads(result.stdout)
    assert signature["status"] == "Valid", result.stdout
    assert signature["kind"] == "Authenticode", result.stdout
    assert len(signature["thumbprint"]) == 40
    launcher._verify_signature(str(signed_file), signature["thumbprint"])
    with pytest.raises(OSError, match="thumbprint mismatch"):
        launcher._verify_signature(str(signed_file), "0" * 40)


def test_private_file_has_explicit_protected_user_system_dacl(native_stubs, tmp_path):
    path = launcher._create_invocation(
        "pass", sys.executable, native_stubs[0], active=True, directory=tmp_path
    )
    try:
        kernel, security = launcher._windows()
        user = launcher._current_user_sid(kernel, security)
        descriptor = ctypes.wintypes.LPVOID()
        owner, dacl = ctypes.wintypes.LPVOID(), ctypes.wintypes.LPVOID()
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
                path,
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
            assert launcher._sid_text(kernel, security, owner) == user
            control, revision = ctypes.wintypes.WORD(), ctypes.wintypes.DWORD()
            assert security.GetSecurityDescriptorControl(
                descriptor, ctypes.byref(control), ctypes.byref(revision)
            )
            assert control.value & 0x1000  # SE_DACL_PROTECTED
            assert dacl.value is not None
            assert ctypes.wintypes.WORD.from_address(dacl.value + 4).value == 2
            trustees = set()
            for index in range(2):
                ace = ctypes.wintypes.LPVOID()
                assert security.GetAce(dacl, index, ctypes.byref(ace))
                assert ace.value is not None
                assert ctypes.c_ubyte.from_address(ace.value).value == 0  # ACCESS_ALLOWED_ACE
                assert ctypes.c_ubyte.from_address(ace.value + 1).value == 0
                assert ctypes.wintypes.DWORD.from_address(ace.value + 4).value == 0x1F01FF
                trustees.add(launcher._sid_text(kernel, security, ace.value + 8))
            assert trustees == {user, "S-1-5-18"}
        finally:
            kernel.LocalFree(descriptor)
    finally:
        Path(path).unlink()


def test_private_creation_never_overwrites_existing_file(native_stubs, tmp_path, monkeypatch):
    monkeypatch.setattr(launcher.secrets, "token_hex", lambda _: "collision")
    path = Path(
        launcher._create_invocation(
            "pass", sys.executable, native_stubs[0], active=True, directory=tmp_path
        )
    )
    path.unlink()
    path.write_bytes(b"preserve existing file")
    with pytest.raises(OSError, match="create private executable"):
        launcher._create_invocation(
            "pass", sys.executable, native_stubs[0], active=True, directory=tmp_path
        )
    assert path.read_bytes() == b"preserve existing file"


def test_private_stream_failure_cleans_only_created_file(native_stubs, tmp_path, monkeypatch):
    real_kernel, security = launcher._windows()

    class FailStream:
        def __getattr__(self, name):
            return getattr(real_kernel, name)

        def CreateFileW(self, path, *args):
            if path.endswith(launcher.CONFIG_STREAM):
                ctypes.set_last_error(50)
                return launcher._INVALID_HANDLE
            return real_kernel.CreateFileW(path, *args)

    monkeypatch.setattr(launcher, "_windows", lambda: (FailStream(), security))
    with pytest.raises(OSError, match="NTFS required"):
        launcher._create_invocation(
            "pass", sys.executable, native_stubs[0], active=True, directory=tmp_path
        )
    assert not list(tmp_path.rglob("omnigent-sandbox-*.exe"))


def test_private_asset_rejects_reparse_point(native_stubs, tmp_path):
    import ctypes.wintypes as w

    # A junction-free hard link is allowed; a file symlink is not.
    alias = tmp_path / "asset-link.exe"
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateSymbolicLinkW.argtypes = [w.LPCWSTR, w.LPCWSTR, w.DWORD]
    kernel.CreateSymbolicLinkW.restype = w.BOOLEAN
    if not kernel.CreateSymbolicLinkW(str(alias), str(native_stubs[0]), 2):
        pytest.skip("file symlinks require Developer Mode or symbolic-link privilege")
    with pytest.raises(OSError, match="reparse point"):
        launcher._create_invocation("pass", sys.executable, alias, active=True, directory=tmp_path)


def test_private_asset_rejects_wrong_pe_architecture(tmp_path):
    bad = bytearray(100)
    bad[:2] = b"MZ"
    bad[60:64] = (64).to_bytes(4, "little")
    bad[64:68] = b"PE\0\0"
    bad[68:70] = (0xAA64).to_bytes(2, "little")
    bad[88:90] = (0x20B).to_bytes(2, "little")
    asset = tmp_path / "arm64.exe"
    asset.write_bytes(bad)
    with pytest.raises(OSError, match="x64 PE executable"):
        launcher._create_invocation("pass", sys.executable, asset, active=True, directory=tmp_path)


def test_private_storage_refuses_broad_ancestor_delete_child(tmp_path):
    kernel, security = launcher._windows()
    user = launcher._current_user_sid(kernel, security)
    descriptor = ctypes.wintypes.LPVOID()
    sddl = f"O:{user}D:P(A;;FA;;;{user})(A;;FA;;;SY)(A;;0x40;;;WD)"
    assert security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl, 1, ctypes.byref(descriptor), None
    )
    unsafe = tmp_path / "adversarial-temp"
    attributes = launcher._SecurityAttributes(
        ctypes.sizeof(launcher._SecurityAttributes), descriptor, False
    )
    try:
        assert kernel.CreateDirectoryW(str(unsafe), ctypes.byref(attributes))
    finally:
        kernel.LocalFree(descriptor)
    private = launcher._private_security(kernel, security)
    try:
        with pytest.raises(OSError, match="untrusted mutation"):
            launcher._private_directory(kernel, security, unsafe, private)
    finally:
        kernel.LocalFree(private.descriptor)
    assert not (unsafe / "Omnigent-WindowsLaunchers").exists()


def test_private_storage_ignores_environment_temp_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMP", str(tmp_path / "untrusted-temp"))
    monkeypatch.setenv("TMP", str(tmp_path / "untrusted-tmp"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "untrusted-profile"))
    profile = _real_known_profile()
    assert profile != tmp_path / "untrusted-profile"
    assert profile.is_dir()


@pytest.mark.parametrize(
    ("rights", "accepted"),
    [(0x1200A9, True), (2, False), (4, False), (0x10, False), (0x100, False), (0x40, False)],
)
def test_private_container_allows_only_additional_read_access(tmp_path, rights, accepted):
    kernel, security = launcher._windows()
    user = launcher._current_user_sid(kernel, security)
    descriptor = ctypes.wintypes.LPVOID()
    sddl = f"O:{user}D:P(A;;FA;;;{user})(A;;FA;;;SY)(A;;{rights:#x};;;WD)"
    assert security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl, 1, ctypes.byref(descriptor), None
    )
    container = tmp_path / "Omnigent-WindowsLaunchers"
    attributes = launcher._SecurityAttributes(
        ctypes.sizeof(launcher._SecurityAttributes), descriptor, False
    )
    try:
        assert kernel.CreateDirectoryW(str(container), ctypes.byref(attributes))
    finally:
        kernel.LocalFree(descriptor)
    private = launcher._private_security(kernel, security)
    try:
        if accepted:
            assert launcher._private_directory(kernel, security, tmp_path, private) == container
        else:
            with pytest.raises(OSError, match="not private"):
                launcher._private_directory(kernel, security, tmp_path, private)
    finally:
        kernel.LocalFree(private.descriptor)
