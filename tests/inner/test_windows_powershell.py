"""Native PowerShell selection without depending on the host installation."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from omnigent.inner import windows_powershell


@pytest.fixture(autouse=True)
def windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", True)


def _exe(directory: Path, name: str = "pwsh.exe") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    executable = directory / name
    executable.touch()
    return executable


def test_store_first_path_prefers_standard_install(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = _exe(tmp_path / "WindowsApps")
    native = _exe(tmp_path / "Program Files" / "PowerShell" / "7")
    tools = tmp_path / "tools"
    env = {"Path": f"{store.parent};{tools}", "ProgramFiles": str(tmp_path / "Program Files")}
    original = dict(env)

    with caplog.at_level(logging.INFO):
        result = windows_powershell.prepare_native_powershell_env(env)

    assert result["Path"] == f"{native.parent};{store.parent};{tools}"
    assert env == original
    assert str(native) in caplog.text


@pytest.mark.parametrize("key", ["ProgramFiles", "ProgramW6432", "PROGRAMFILES"])
def test_standard_install_with_empty_path(tmp_path: Path, key: str) -> None:
    native = _exe(tmp_path / "programs" / "PowerShell" / "7")
    result = windows_powershell.prepare_native_powershell_env({key: str(tmp_path / "programs")})
    assert result["PATH"] == str(native.parent)


def test_programw6432_precedes_programfiles(tmp_path: Path) -> None:
    native = _exe(tmp_path / "native" / "PowerShell" / "7")
    other = _exe(tmp_path / "other" / "PowerShell" / "7")
    result = windows_powershell.prepare_native_powershell_env(
        {"ProgramW6432": str(native.parents[2]), "ProgramFiles": str(other.parents[2])}
    )
    assert result["PATH"] == str(native.parent)


def test_portable_install_preserves_tools_and_is_idempotent(tmp_path: Path) -> None:
    native = _exe(tmp_path / "portable")
    tools = tmp_path / "tools"
    env = {"pAtH": f'{tools};"{native.parent}";{str(native.parent).upper()}', "TOKEN": "private"}
    result = windows_powershell.prepare_native_powershell_env(env)
    assert result == {"pAtH": f"{native.parent};{tools}", "TOKEN": "private"}
    assert windows_powershell.prepare_native_powershell_env(result) == result


def test_duplicate_path_keys_keep_first_spelling(tmp_path: Path) -> None:
    native = _exe(tmp_path / "portable")
    result = windows_powershell.prepare_native_powershell_env(
        {"Path": str(native.parent), "PATH": "ignored"}
    )
    assert result == {"Path": str(native.parent)}


def test_store_only_warns_and_preserves_vendor_fallback(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = _exe(tmp_path / "wInDoWsApPs")
    env = {"PATH": str(store.parent)}
    assert windows_powershell.prepare_native_powershell_env(env) == env
    assert "MSI installer" in caplog.text
    assert "vendor shell fallback" in caplog.text


def test_portable_after_store_alias(tmp_path: Path) -> None:
    store = _exe(tmp_path / "WindowsApps")
    native = _exe(tmp_path / "portable")
    result = windows_powershell.prepare_native_powershell_env(
        {"PATH": f"{store.parent};{native.parent}"}
    )
    assert result["PATH"] == f"{native.parent};{store.parent}"


@pytest.mark.parametrize("name", ["pwsh.cmd", "pwsh.bat", "powershell.exe"])
def test_no_native_executable_preserves_fallback(tmp_path: Path, name: str) -> None:
    shim = _exe(tmp_path / "tools", name)
    env = {"PATH": str(shim.parent), "OTHER": "value"}
    assert windows_powershell.prepare_native_powershell_env(env) == env


def test_empty_environment_preserves_fallback() -> None:
    assert windows_powershell.prepare_native_powershell_env({}) == {}


def test_non_windows_returns_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(windows_powershell, "IS_WINDOWS", False)
    env = {"Path": "some/path", "PATH": "another/path"}
    result = windows_powershell.prepare_native_powershell_env(env)
    assert result == env
    assert result is not env


def test_resolved_store_target_is_rejected(tmp_path: Path) -> None:
    store = _exe(tmp_path / "WindowsApps")
    portable = tmp_path / "portable"
    portable.mkdir()
    try:
        (portable / "pwsh.exe").symlink_to(store)
    except OSError:
        pytest.skip("Creating symbolic links requires Windows developer mode")
    env = {"PATH": str(portable)}
    assert windows_powershell.prepare_native_powershell_env(env) == env


def test_resolved_batch_shim_is_rejected(tmp_path: Path) -> None:
    shim = _exe(tmp_path / "shims", "pwsh.cmd")
    portable = tmp_path / "portable"
    portable.mkdir()
    try:
        (portable / "pwsh.exe").symlink_to(shim)
    except OSError:
        pytest.skip("Creating symbolic links requires Windows developer mode")
    env = {"PATH": str(portable)}
    assert windows_powershell.prepare_native_powershell_env(env) == env


def test_installation_roots_do_not_forward_host_environment(tmp_path: Path) -> None:
    native = _exe(tmp_path / "programs" / "PowerShell" / "7")
    env = {"Path": str(tmp_path / "tools"), "KEEP": "value"}
    host = {"programfiles": str(tmp_path / "programs"), "SECRET": "private"}
    result = windows_powershell.prepare_native_powershell_env(env, installation_env=host)
    assert result == {"Path": f"{native.parent};{env['Path']}", "KEEP": "value"}
    assert "SECRET" not in result
    assert "programfiles" not in result


def test_child_installation_root_precedes_host_root(tmp_path: Path) -> None:
    native = _exe(tmp_path / "child" / "PowerShell" / "7")
    other = _exe(tmp_path / "host" / "PowerShell" / "7")
    result = windows_powershell.prepare_native_powershell_env(
        {"ProgramFiles": str(native.parents[2])},
        installation_env={"PROGRAMFILES": str(other.parents[2])},
    )
    assert result["PATH"] == str(native.parent)


def test_partial_environment_uses_host_path_and_preserves_tools(tmp_path: Path) -> None:
    store = _exe(tmp_path / "WindowsApps")
    native = _exe(tmp_path / "programs" / "PowerShell" / "7")
    tools = tmp_path / "tools"
    host = {
        "pAtH": f"{store.parent};{tools}",
        "PROGRAMFILES": str(tmp_path / "programs"),
        "SECRET": "private",
    }
    env = {"KEEP": "value"}
    result = windows_powershell.prepare_native_powershell_env(env, installation_env=host)
    assert result == {"KEEP": "value", "PATH": f"{native.parent};{store.parent};{tools}"}
    assert env == {"KEEP": "value"}


def test_partial_environment_can_discover_host_portable_install(tmp_path: Path) -> None:
    native = _exe(tmp_path / "portable")
    result = windows_powershell.prepare_native_powershell_env(
        {"KEEP": "value"}, installation_env={"Path": str(native.parent), "SECRET": "private"}
    )
    assert result == {"KEEP": "value", "PATH": str(native.parent)}


@pytest.mark.parametrize("store_present", [False, True])
def test_partial_environment_without_native_install_does_not_forward_host_path(
    tmp_path: Path, store_present: bool
) -> None:
    directory = tmp_path / "WindowsApps"
    if store_present:
        _exe(directory)
    env = {"KEEP": "value"}
    result = windows_powershell.prepare_native_powershell_env(
        env, installation_env={"PATH": str(directory), "SECRET": "private"}
    )
    assert result == env


def test_explicit_empty_child_path_prevents_host_path_discovery(tmp_path: Path) -> None:
    native = _exe(tmp_path / "portable")
    env = {"pAtH": "", "KEEP": "value"}
    result = windows_powershell.prepare_native_powershell_env(
        env, installation_env={"Path": str(native.parent)}
    )
    assert result == env
