# Canonical Promotion Engine v1

> **Status: Current — Phase 85.** Architecture v12 remains frozen.

## Pre-implementation assessment and architecture compatibility

Phase 84 ends at an immutable, identity-verified Knowledge Review Package; the existing
entity promotion service is tied to older candidate artifacts. Phase 85 adds a package-level
boundary rather than weakening either system. It implements Constitution laws 1–5, 8,
12–14: canonical knowledge has one writer, unknowns are explicit, every value retains
lineage, validation fails closed, history is immutable, and a named actor remains
accountable. It changes no Tier 0 contract, canonical v1/v2/v3 schema, provider adapter,
MB2 data, Simulation, Intelligence, or market behavior.

## Promotion lifecycle

```text
Knowledge Review Package -> Validation -> Decision -> Canonical versions
                         -> Immutable audit -> Supersession history
```

`CanonicalPromotionEngine` is the only writer for `data/canonical/knowledge`. It validates
the review-package schema and content identity, the exact independently supplied provider
policy, snapshot/dataset identities, checksums, assertion identity/lineage, duplicates,
conflicts, unknown handling, completeness arithmetic, and reproducibility. A validation
failure writes an immutable rejected-attempt audit but writes no canonical value. Package
promotion is atomic from the consumer perspective: immutable versions and audit are written
before the current-state projection is replaced.

Unknowns require `allow_unknowns` in the accountable decision and produce the
`unknowns_reviewed` uncertainty state. Conflicting assertions always fail closed. No
confidence, recommendation, or provider reputation silently resolves a conflict.

## Canonical write guarantees and supersession

Each immutable version records its canonical identifier, entity type, promotion timestamp
and ID, review-package ID, dataset identities, acquisition lineage, evidence assertion IDs,
minimum assertion confidence, uncertainty state, superseded status, replacement link, and
values. A new value creates a version linked to the previous promotion. History remains
queryable with `history`; `current` reads the deterministic state projection. Nothing in a
version or audit is deleted or overwritten.

Repeated identical promotion decisions return the existing audit. Changed values create a
new version. Replacement links support historical reconstruction and deterministic replay;
a historical record's effective superseded state is established by later replacement
events without mutating the old record.

## Audit trail

Audit files are create-only and contain the actor, timestamp, deterministic ID, complete
inputs and embedded review package, named validation results, promoted/rejected entities,
warnings, conflicts, action, and resulting state digest. Example (abridged):

```json
{"promotion_id":"promotion-<sha256>","action":"promote","actor":"release-bot",
 "inputs":{"review_package_id":"review-<sha256>"},"validation_results":{"valid":true},
 "promoted_entities":["card-001"],"rejected_entities":[],"warnings":[],"conflicts":[]}
```

## Rollback

Rollback is a compensating promotion, never a deletion or edit. Given an approved decision,
it verifies that affected entities still point at the target event, writes new versions of
prior values (or removes newly introduced values only from the current projection), writes
a linked audit, and leaves all source versions and audits intact.

```text
promotion-B (value 4) -> rollback-C (restores value 3 from promotion-A)
```

## Replay

`replay` orders successful immutable events by timestamp and deterministic promotion ID,
applies their preserved versions, applies compensating rollbacks, and verifies the state
digest after every event. The same acquisition snapshot lineage, review package, provider
policy, and decisions therefore reproduce identical canonical state. Failed attempts are
retained for audit but do not participate in state replay.

## CLI

```bash
python -m mtglab.acquisition promote --package review.json --policy policy.json --actor maintainer --timestamp 2026-07-30T12:00:00Z --allow-unknowns
python -m mtglab.acquisition rollback promotion-ID --actor maintainer --timestamp 2026-07-30T13:00:00Z
python -m mtglab.acquisition replay
python -m mtglab.acquisition audit [promotion-ID]
```

The Phase 84 pipeline prepares packages; it cannot canonize them. Phase 85 consumes those
packages only after an explicit decision and never reaches backward to mutate acquisition.
