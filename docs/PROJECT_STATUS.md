# Project Status

> **Status: Current** — Phase 84 implementation is complete locally; GitHub Actions are pending.

## Executive status

MTG Lab remains a pre-alpha deterministic reference implementation on **Architecture v12
(unchanged)**. **Phase 83 — Institutional Memory and Project Constitution** is the latest
completed milestone on the default branch. It was documentation-only. **Phase 82 — Raw
Data Acquisition Framework** is the latest merged runtime milestone.
Phase 84 now adds a reusable, non-canonical Knowledge Acquisition Pipeline with provider
policies, dataset identity, validation, deterministic reports, and review packages. The
local baseline is **160 passing tests**. Architecture v12 remains unchanged, and merge is
not recommended until GitHub Actions are green.

The four Phase 83 Tier 0 documents remain authoritative and linked:

- [`CONSTITUTION.md`](CONSTITUTION.md) — foundational law and amendment process;
- [`ARCHITECTS_NOTEBOOK.md`](ARCHITECTS_NOTEBOOK.md) — chronological rationale;
- [`FUTURE_VISION.md`](FUTURE_VISION.md) — non-authorizing architectural intent; and
- [`QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`](QUESTIONS_MTG_LAB_SHOULD_ANSWER.md) — product and research compass.

## Capability boundary

- The Mystery Booster 2 dataset is still evidence-acquisition blocked. Canonical Print
  Sheets, Slots, complete pools, and product rules remain unpopulated.
- Simulation is not implemented.
- The Intelligence Engine is vision only and is not implemented.
- Phase 84 was explicitly authorized and is implemented on this branch. No subsequent
  milestone or canonical promotion is authorized.

## Operational guidance

There is no outstanding Phase 82 or Phase 83 merge gate. Earlier instructions to review
those pull requests or await their GitHub Actions are **superseded**. For a new session,
follow the startup order in [`SESSION_STATE.md`](SESSION_STATE.md) and treat
[`NEXT_TASK.md`](NEXT_TASK.md) as the current authorization boundary.
