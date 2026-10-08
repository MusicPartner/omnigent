"""Windows native readiness depends on psmux as well as binary/auth probes."""

import pytest

from omnigent.harness_aliases import NATIVE_HARNESSES
from omnigent.onboarding import harness_readiness as readiness
from omnigent.terminals import psmux


@pytest.mark.parametrize(
    "windows,present,expected", [(False, False, True), (True, False, False), (True, True, True)]
)
def test_native_terminal_supported(windows, present, expected, monkeypatch):
    monkeypatch.setattr(psmux, "IS_WINDOWS", windows)
    monkeypatch.setattr(
        psmux.shutil, "which", lambda name: "psmux.exe" if present and name == "psmux" else None
    )
    assert psmux.native_terminal_supported() is expected


@pytest.mark.parametrize("harness", sorted(NATIVE_HARNESSES))
def test_psmux_present_native_harness_uses_normal_probes(harness, monkeypatch):
    import omnigent.harnesses.codex_native.main as codex

    monkeypatch.setattr(readiness, "IS_WINDOWS", True)
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: True)
    monkeypatch.setattr(readiness, "_installer_only_availability", lambda _: True)
    monkeypatch.setattr(readiness, "_binary_availability_reason", lambda _: True)
    monkeypatch.setattr(readiness, "_cli_family_availability", lambda *_: True)
    monkeypatch.setattr(readiness, "_family_provider_configured", lambda _: True)
    monkeypatch.setattr(
        readiness,
        "_FAMILY_CREDENTIAL_CHECK",
        {key: lambda: True for key in readiness._FAMILY_CREDENTIAL_CHECK},
    )
    monkeypatch.setattr(codex, "_codex_auth_unavailable_reason", lambda: None)
    canonical = readiness._canonical_harness(harness)
    assert readiness.harness_is_configured(harness) is True
    assert readiness._harness_availability(canonical) is True


@pytest.mark.parametrize("reason", ["binary-missing", "needs-auth", "version-too-low"])
def test_psmux_presence_does_not_bypass_auth_or_binary_failures(reason, monkeypatch):
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: True)
    monkeypatch.setattr(readiness, "_cli_family_availability", lambda *_: reason)
    assert readiness._harness_availability("claude-native") == reason


def test_windows_codex_cache_key_changes_with_psmux_without_sharing_plain_codex(monkeypatch):
    monkeypatch.setattr(readiness, "IS_WINDOWS", True)
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: False)
    absent = readiness._harness_readiness_cache_key("codex-native")
    plain = readiness._harness_readiness_cache_key("codex")
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: True)
    present = readiness._harness_readiness_cache_key("codex-native")
    assert absent != present
    assert absent != plain != present
    assert plain == ("codex",)


def test_posix_codex_cache_key_keeps_release_family_sharing(monkeypatch):
    monkeypatch.setattr(readiness, "IS_WINDOWS", False)
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: True)
    assert readiness._harness_readiness_cache_key("codex-native") == ("codex",)
    assert readiness._harness_readiness_cache_key("codex") == ("codex",)


def test_readiness_refresh_observes_psmux_install_without_restart(monkeypatch):
    import omnigent.harnesses.codex_native.main as codex

    monkeypatch.setattr(readiness, "IS_WINDOWS", True)
    monkeypatch.setattr(codex, "_codex_auth_unavailable_reason", lambda: None)
    supported = False
    monkeypatch.setattr(readiness, "native_terminal_supported", lambda: supported)
    original = readiness._harness_availability
    monkeypatch.setattr(
        readiness,
        "_harness_availability",
        lambda canonical: original(canonical) if canonical in ("codex", "codex-native") else True,
    )
    absent = readiness.configured_harness_map()
    supported = True
    present = readiness.configured_harness_map()
    assert absent["codex"] is present["codex"] is True
    assert absent["codex-native"] is False
    assert present["codex-native"] is True
