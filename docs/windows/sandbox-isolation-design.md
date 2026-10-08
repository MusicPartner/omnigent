# Windows sandbox and egress isolation design

## Problem

Windows Job Objects provide process-tree containment and cleanup, but they do not
provide the same security boundary as Linux `bwrap` or macOS `seatbelt`:

- no filesystem namespace for read/write allow-lists;
- no hard network namespace denial;
- no guarantee that all HTTP(S) traffic flows through Omnigent's egress proxy.

Current Windows policy should therefore fail closed for unsupported filesystem
or network restrictions. Real parity requires a Windows-specific isolation
backend.

## Goals

- Hard-fail unsupported policy instead of silently degrading.
- Preserve Job Object process cleanup for every Windows helper.
- Add a path to enforce filesystem and network policy for high-security Windows
  workloads.
- Keep low-friction local development available when users opt into
  `sandbox.type=none` or process-containment-only behavior.

## Non-goals

- Claim bwrap/seatbelt-equivalent security from Job Objects alone.
- Depend on machine-wide firewall changes for ordinary local development.
- Add a large isolation backend without maintainer design approval.

## Candidate backends

### AppContainer / restricted token

AppContainer and restricted tokens can reduce process capabilities and constrain
resource access. This is the closest Windows-native analogue for a lightweight
local sandbox.

Pros:

- Native Windows security primitive.
- Potentially works without a VM/container runtime.
- Can be paired with Job Objects for cleanup.

Cons:

- Requires careful ACL/capability setup for project directories and temp space.
- Needs investigation for developer-machine compatibility and subprocess trees.
- Network policy may still require extra capability/firewall work.

### Windows Filtering Platform / firewall-scoped rules

WFP or firewall rules could provide hard network denial or allow-listing.

Pros:

- Real network enforcement.
- Can support egress proxy-only routing if scoped correctly.

Cons:

- May require elevated privileges or persistent machine state.
- Rule cleanup must be robust across crashes.
- Risky for developer machines if rules are mis-scoped.

### Proxy-only best effort

Set proxy environment variables and trust the egress proxy to enforce L7 rules.

Pros:

- Simple and non-privileged.
- Useful for cooperative clients.

Cons:

- Not a security boundary. Tools can bypass env proxy settings.
- Must not satisfy `egress_rules` in fail-closed policy.

### VM/container isolation

Run Windows workloads inside a lightweight VM/container or remote sandbox.

Pros:

- Stronger boundary with clearer cleanup.
- Can be made closer to Linux/macOS isolation semantics.

Cons:

- Heavier operational dependency.
- May not fit the local-first Windows developer workflow.

## Recommended path

1. Keep current fail-closed `windows_jobobject` policy for network deny,
   `egress_rules`, and credential proxy.
2. Preserve Job Objects as the default process-containment backend.
3. Run an AppContainer/restricted-token spike for filesystem isolation and
   subprocess compatibility.
4. Separately spike network enforcement with WFP/firewall scoping.
5. Implement only after the backend can prove:
   - denied filesystem paths cannot be read;
   - denied network connections fail even when proxy env vars are bypassed;
   - egress allow-list traffic can be forced through the proxy;
   - cleanup survives helper crashes.

## Proposed MVP shape

Add a new backend name rather than overloading `windows_jobobject`:

```yaml
os_env:
  type: caller_process
  sandbox:
    type: windows_restricted
    read_paths: ["."]
    write_paths: ["."]
    allow_network: false
```

`windows_jobobject` remains process-containment-only. `windows_restricted`
becomes the explicit hard-enforcement backend once proven.

## Test strategy

- Unit tests for parser/validator capability checks.
- Windows-only integration tests for denied filesystem reads/writes.
- Windows-only integration tests for denied direct TCP connections.
- Egress proxy tests proving non-matching hosts fail and matching hosts pass.
- Crash cleanup tests proving no policy or process artifacts leak.

## Open questions

- Can AppContainer be used without admin rights for the target workflows?
- How should ACL grants be represented for project directories and temp space?
- Can network policy be scoped per process tree without persistent machine-wide
  side effects?
- Is a VM/container backend more maintainable for high-security workloads?
