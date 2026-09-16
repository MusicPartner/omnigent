# Native Windows test execution

This document tracks the executable Windows-safe test strategy. It complements
the broader QA matrix by separating broad collection from stable execution.

## Commands

From native Windows PowerShell:

```powershell
uv sync --locked --extra dev
.\scripts\windows_safe_pytest.ps1 -StableOnly
```

Collection-only check:

```powershell
.\scripts\windows_safe_pytest.ps1 -CollectOnly
```

Stable subset only, without broad collection:

```powershell
.\scripts\windows_safe_pytest.ps1 -StableOnly
```

## Why collection and execution are separate

`pytest -m "not posix_only" --collect-only` catches import-time Windows
regressions across the broad Windows-safe surface and remains non-blocking.
Full execution is promoted in smaller groups because many tests exercise
services, local environment state, or terminal behavior that needs separate
stabilization.

## Current stable subset

The initial stable subset includes:

- native process/platform support;
- process manager behavior;
- runner transport selection/routing;
- sandbox capability metadata;
- parser/validator fail-closed behavior for unsupported Windows network-deny and
  egress policy;
- PowerShell installer helper behavior.

## Promotion rule

A test group can move into the stable subset when:

1. It passes repeatedly on native Windows.
2. It has no dependency on real developer home-directory state.
3. POSIX-only assumptions are either fixed or marked `posix_only`.
4. Failure messages are actionable for missing optional Windows dependencies.
