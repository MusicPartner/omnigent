# Windows sandbox and egress support boundary

Native Windows support currently uses Job Object-style process containment for
agent process trees. This is useful for cleanup and lifecycle control, but it is
not equivalent to the hardened POSIX sandboxes.

## Capability matrix

The source of truth for this matrix is `omnigent/inner/sandbox_capabilities.py`.
Parser and validator checks consume the same capability metadata so unsupported
Windows policy combinations fail closed consistently.

| Backend | Platform | Process containment | Filesystem isolation | Network isolation | Egress rules |
| --- | --- | --- | --- | --- | --- |
| `linux_bwrap` | Linux | Yes | Yes | Yes | Yes |
| `darwin_seatbelt` | macOS | Yes | Yes | Yes | Yes |
| `windows_jobobject` | Windows | Yes | No | No | No |
| `none` | Any | No | No | No | No |

## Windows policy

On Windows, Job Objects can contain and clean up process trees, but they do not
provide the filesystem namespace, network namespace, or forced proxy routing
that Omnigent relies on for hard sandbox and egress enforcement.

Therefore Windows support must stay explicit:

- process containment is supported;
- filesystem read/write policy is not hard-enforced;
- `allow_network: false` cannot be guaranteed as a hard network deny;
- `egress_rules` and `credential_proxy` are unsupported until a backend can
  force all traffic through the egress proxy;
- unsupported combinations should fail closed with actionable errors rather
  than silently degrading.

## Implementation sequence

1. Advertise capabilities through code metadata.
2. Document the support boundary for reviewers and contributors.
3. Keep parser and validator fail-closed checks wired to the shared capability
   model.
4. Only promote Windows CI once those errors are deterministic.
