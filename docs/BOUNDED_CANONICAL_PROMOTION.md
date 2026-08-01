# Bounded MTGJSON Canonical Promotion v1

> **Phase 104 — complete, 2026-07-31. Architecture v12 unchanged.**

## Architecture assessment

The merged Phase 103 baseline is present at `e8bd9b8`. Typed Canonical Projection is
complete. The Canonical Repository remains authoritative and Canonical Promotion remains
the only writer: validation and an explicit decision by the independent Phase 104 reviewer
precede every successful write. This milestone composes existing contracts and introduces
no automatic promotion, network access, provider execution, canonical-contract change,
simulation, AI provider, or product-specific runtime branch. No architectural defect or
Project Architect approval requirement was found.

## Deterministic corpus

`data/reference/mtgjson/bounded-canonical-promotion-v1.json` is a frozen, local,
MTGJSON-derived reference extract, not a full import. Its two Cards and three Printings
span two sets (`set-one`, `set-two`), common and mythic rarity, English and Japanese,
foil and nonfoil finishes, and multiple printings of `card-alpha`. A reviewed null artist
is the explicit unknown. The workflow creates one conflicting rejected candidate, revises
`card-alpha` to produce a superseded record, rehearses rollback, and restores the revision
with a distinct reviewed decision. Exactly five entities finish in canonical storage;
the rejected candidate never does.

## Governed workflow and validation

The offline reference bytes pass through checksum-addressed acquisition, deterministic
normalization, assertions, validation, review-package construction, independent decision,
promotion, typed projection, Query, Analytics, Semantic Query, and Reasoning Context. The
verification command also serializes a valid `AIModelRequest` whose provider/model are
explicitly `not-invoked`; it never executes a provider.

Promotion and projection audits retain dataset identity, source assertion identifiers,
provenance, confidence, reviewed-unknown lifecycle, review identity, deterministic state
and repository hashes, and canonical identifiers. Validation checks replay equality,
typed projection, duplicate prevention, rejected-candidate isolation, and compatibility
with every downstream consumer.

## CLI, replay, and rollback

```bash
mtg-lab --data-root DATA promote corpus --format json
mtg-lab --data-root DATA promote inspect --format json
mtg-lab --data-root DATA promote verify --format json
```

`corpus` is idempotent: a completed manifest is returned only after verification. The
workflow promotes the base, promotes a reviewed correction, deterministically rolls that
correction back, verifies audit replay byte-for-value against current state, and restores
the correction under a new review decision. `inspect` exposes immutable promotion audits
and replayed state; `verify` proves the final canonical and typed projections agree.

## Limitations and full-corpus readiness

This is a five-entity, single-process filesystem rehearsal. It is not a throughput, memory,
locking, interruption, quarantine, licensing, or complete AllPrintings test. It establishes
readiness for small, bounded, explicitly reviewed MTGJSON-derived batches only. Full-corpus
promotion remains blocked on independently reviewed batching/mapping, performance and
recovery measurements, concurrency/generation controls, and operational retention policy.
Unattended or automatic promotion remains prohibited.

## Phase 118 trusted-source promotion gate

Operator signatures and authorization-only pull requests are no longer part of the active
promotion architecture. A candidate batch from an approved trusted provider may become ready after
source checksums, immutable evidence, schemas, exact candidate membership, target isolation,
dependency closure, duplicates/conflicts, explicit unknowns, quarantine state, and canonical
pre-state all validate. Normal pull-request review and green GitHub Actions provide human oversight.

Readiness never writes canonical state. Promotion remains separately and explicitly invoked, limited
to exactly one verified batch, deterministic, audited with source/membership and pre/post-state
lineage, replayable, and rollback capable. Any unresolved, quarantined, rejected, conflicting,
incomplete, non-isolated, or drifted state fails closed. The first MB2 batch satisfies the technical
readiness gates, but Phase 118 does not promote it.
