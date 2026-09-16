"""Tests for sandbox capability metadata."""

from __future__ import annotations

from omnigent.inner.sandbox_capabilities import (
    default_sandbox_backend_for_platform,
    egress_capable_backends,
    sandbox_capabilities,
    sandbox_credential_proxy_error,
    sandbox_egress_policy_error,
    sandbox_network_deny_error,
)


def test_windows_jobobject_capabilities_are_process_only() -> None:
    """Windows metadata is explicit about containment but no egress isolation."""
    caps = sandbox_capabilities("windows_jobobject")

    assert caps.platform == "windows"
    assert caps.process_containment is True
    assert caps.filesystem_isolation is False
    assert caps.network_isolation is False
    assert caps.egress_policy is False
    assert "Job Object" in caps.notes


def test_egress_capable_backends_are_marked() -> None:
    """Linux/macOS hardened backends advertise egress-policy support."""
    assert sandbox_capabilities("linux_bwrap").egress_policy is True
    assert sandbox_capabilities("darwin_seatbelt").egress_policy is True


def test_unknown_backend_fails_closed() -> None:
    """Unknown backend metadata must not imply any isolation capability."""
    caps = sandbox_capabilities("future_backend")

    assert caps.backend == "future_backend"
    assert caps.process_containment is False
    assert caps.filesystem_isolation is False
    assert caps.network_isolation is False
    assert caps.egress_policy is False


def test_default_windows_backend() -> None:
    """Native Windows defaults to process containment metadata."""
    assert default_sandbox_backend_for_platform("nt") == "windows_jobobject"


def test_egress_capable_backends_derive_from_capability_table() -> None:
    """Policy helpers expose the capability table, not duplicated literals."""
    assert egress_capable_backends() == {"darwin_seatbelt", "linux_bwrap"}


def test_windows_network_deny_error_comes_from_capability_table() -> None:
    """Windows fail-closed network denial text is shared by parser/validator."""
    message = sandbox_network_deny_error("windows_jobobject")

    assert message is not None
    assert "windows_jobobject" in message
    assert "allow_network=true" in message
    assert sandbox_network_deny_error("linux_bwrap") is None


def test_windows_egress_and_credential_proxy_errors_fail_closed() -> None:
    """Windows Job Objects do not satisfy egress or credential proxy policy."""
    egress_message = sandbox_egress_policy_error("windows_jobobject")
    credential_message = sandbox_credential_proxy_error("windows_jobobject")

    assert egress_message is not None
    assert "windows_jobobject" in egress_message
    assert credential_message is not None
    assert "windows_jobobject" in credential_message
