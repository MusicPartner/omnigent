# Windows enablement documentation

This folder contains detailed Windows enablement material. The top-level decision
record is [`../windows-first-class-support-adr.md`](../windows-first-class-support-adr.md).

Use this folder as the product/engineering workspace for native Windows support:

- [`qa-matrix.md`](qa-matrix.md) — review gates, CI levels, manual QA, and PR evidence expectations.
- [`test-execution.md`](test-execution.md) — native PowerShell test workflow and stable/broad test split.
- [`e2e-evidence.md`](e2e-evidence.md) — expected end-to-end evidence package for Windows behavior.
- [`sandbox-egress.md`](sandbox-egress.md) — current sandbox and egress capability boundaries.
- [`sandbox-isolation-design.md`](sandbox-isolation-design.md) — future Windows isolation backend options and tradeoffs.
- [`installer.md`](installer.md) — PowerShell installer modes, prerequisites, and repeat-install behavior.
- [`psmux-browser-attach.md`](psmux-browser-attach.md) — Windows browser terminal attach fidelity boundary and evidence requirements.
- [`upstream-related-work.md`](upstream-related-work.md) — adjacent upstream workstreams and sequencing notes.

The documentation should stay honest about support boundaries. If a behavior is
not equivalent to POSIX, document the limitation and the validation evidence
needed before calling it supported.
