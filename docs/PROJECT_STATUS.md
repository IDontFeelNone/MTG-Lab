# Project Status

> **Phase 107 reproducible MTGJSON delivery implemented — 2026-07-31.** The local command and
> manual workflow fail closed on checksum and schema, stop before promotion by default, and allow
> only one explicitly reviewed batch. Hosted Codex still receives HTTP 403, so the first real run
> awaits a GitHub runner or operator environment. Architecture v12 is unchanged.

Deterministic MTGJSON review batches, bounded independent promotion, typed projection, replay, rollback, downstream checks, and performance instrumentation are implemented. Official full-corpus execution remains pending because the approved URL returned HTTP 403 in this environment; no substitute corpus was promoted.

> **Phase 105 Official Reference Dataset Acquisition implemented — 2026-07-31.**

Approved MTGJSON AllPrintings acquisition is now automated into `data/local/`, with resume,
integrity, checksum/SHA-256, JSON/schema verification, and non-canonical evidence registration.
Acquisition remains separate from provider import, review, promotion, and typed projection.
Neither Mystery Booster 2 nor Marvel Super Heroes is marked populated.

The complete governed pipeline has now been executed with a fixed MTGJSON-derived corpus:
reviewed promotion, typed projection, all four read consumers, non-executed AI request,
replay, rollback, and restore. Architecture v12, repository authority, independent review,
and promotion governance are unchanged.

- Architecture v12: reviewed, suitable, and unchanged.
- Overall maturity: pre-alpha with a beta-ready architectural shape.
- Phase 100: merged; local MTGJSON execution stops at validated pending candidates.
- Representative validation: the governed provider-to-AI-request path passes without model execution.
- Validation baseline: 258 tests passing locally.
- Full MTGJSON canonical import: not authorized pending batching, scale/recovery, and concurrency tests.
- Canonical Promotion: Ready for bounded, controlled, single-writer workflows.
- Large imports, Collection Intelligence, and Market Intelligence: Mostly Ready.
- MB2 full population, Simulation, and AI Advisor: Not Ready.
- Current implementation assessment: `PHASE_101_ARCHITECTURE_REVIEW.md`.
- No subsequent implementation milestone is authorized by this status document.
