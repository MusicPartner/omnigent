"""Sandbox capability metadata by platform/backend."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxCapabilities:
    """Security capabilities advertised by an OS sandbox backend.

    :param backend: Sandbox backend identifier.
    :param platform: Platform family the backend runs on.
    :param process_containment: Whether child process cleanup/containment is
        provided.
    :param filesystem_isolation: Whether read/write path policy is hard-enforced.
    :param network_isolation: Whether network deny/isolation can be hard-enforced.
    :param egress_policy: Whether L7 egress rules can be enforced by forcing all
        traffic through the Omnigent egress proxy.
    :param notes: Short human-readable support boundary.
    """

    backend: str
    platform: str
    process_containment: bool
    filesystem_isolation: bool
    network_isolation: bool
    egress_policy: bool
    notes: str


_CAPABILITIES: dict[str, SandboxCapabilities] = {
    "linux_bwrap": SandboxCapabilities(
        backend="linux_bwrap",
        platform="linux",
        process_containment=True,
        filesystem_isolation=True,
        network_isolation=True,
        egress_policy=True,
        notes="bubblewrap enforces filesystem, process, and network isolation",
    ),
    "darwin_seatbelt": SandboxCapabilities(
        backend="darwin_seatbelt",
        platform="darwin",
        process_containment=True,
        filesystem_isolation=True,
        network_isolation=True,
        egress_policy=True,
        notes="seatbelt profile enforces filesystem and network policy",
    ),
    "windows_jobobject": SandboxCapabilities(
        backend="windows_jobobject",
        platform="windows",
        process_containment=True,
        filesystem_isolation=False,
        network_isolation=False,
        egress_policy=False,
        notes=(
            "Windows Job Object support contains and cleans up process trees but "
            "does not provide filesystem isolation or network/egress policy"
        ),
    ),
    "none": SandboxCapabilities(
        backend="none",
        platform="any",
        process_containment=False,
        filesystem_isolation=False,
        network_isolation=False,
        egress_policy=False,
        notes="no OS sandbox isolation",
    ),
}


def sandbox_capabilities(backend: str | None) -> SandboxCapabilities:
    """Return capability metadata for *backend*.

    Unknown or unset backends are treated as unsupported/no-isolation so policy
    callers can fail closed instead of assuming a secure default.
    """
    name = backend or "none"
    return _CAPABILITIES.get(
        name,
        SandboxCapabilities(
            backend=name,
            platform="unknown",
            process_containment=False,
            filesystem_isolation=False,
            network_isolation=False,
            egress_policy=False,
            notes="unknown sandbox backend; no capabilities advertised",
        ),
    )


def egress_capable_backends() -> frozenset[str]:
    """Return backends that hard-enforce Omnigent egress policy."""
    return frozenset(
        backend for backend, caps in _CAPABILITIES.items() if caps.egress_policy
    )


def network_isolation_capable_backends() -> frozenset[str]:
    """Return backends that can hard-deny/isolate network access."""
    return frozenset(
        backend for backend, caps in _CAPABILITIES.items() if caps.network_isolation
    )


def sandbox_network_deny_error(backend: str | None) -> str | None:
    """Return the fail-closed error for unsupported network deny, if any."""
    caps = sandbox_capabilities(backend)
    if caps.network_isolation:
        return None
    if caps.backend == "windows_jobobject":
        return (
            "os_env.sandbox.allow_network=false is not supported with "
            "sandbox.type=windows_jobobject: Windows Job Objects contain "
            "process trees but do not hard-enforce network denial. Use a "
            "Linux/macOS hardened sandbox for network isolation or set "
            "allow_network=true on Windows."
        )
    return (
        "os_env.sandbox.allow_network=false requires a sandbox backend that "
        "hard-enforces network denial. "
        f"Got sandbox.type={caps.backend!r}."
    )


def sandbox_egress_policy_error(backend: str | None) -> str | None:
    """Return the fail-closed error for unsupported egress policy, if any."""
    caps = sandbox_capabilities(backend)
    if caps.egress_policy:
        return None
    capable = ", ".join(sorted(egress_capable_backends()))
    return (
        "os_env.sandbox.egress_rules requires sandbox.type="
        f"{capable} for hard enforcement of the network allow-list. "
        f"Got sandbox.type={caps.backend!r}; the rules would be inert "
        "decoration on the policy and the agent would have unrestricted "
        "network access despite the YAML declaring otherwise."
    )


def sandbox_credential_proxy_error(backend: str | None) -> str | None:
    """Return the fail-closed error for unsupported credential proxy, if any."""
    caps = sandbox_capabilities(backend)
    if caps.egress_policy:
        return None
    capable = ", ".join(sorted(egress_capable_backends()))
    return (
        "os_env.sandbox.credential_proxy requires sandbox.type="
        f"{capable} so credentials are bound to a hardened helper boundary. "
        f"Got sandbox.type={caps.backend!r}."
    )


def default_sandbox_backend_for_platform(platform: str | None = None) -> str:
    """Return the default sandbox backend name for a platform family."""
    name = platform or os.name
    if name == "nt":
        return "windows_jobobject"
    if name == "posix":
        if os.uname().sysname == "Darwin":
            return "darwin_seatbelt"
        return "linux_bwrap"
    return "none"


__all__ = [
    "SandboxCapabilities",
    "default_sandbox_backend_for_platform",
    "egress_capable_backends",
    "network_isolation_capable_backends",
    "sandbox_capabilities",
    "sandbox_credential_proxy_error",
    "sandbox_egress_policy_error",
    "sandbox_network_deny_error",
]
