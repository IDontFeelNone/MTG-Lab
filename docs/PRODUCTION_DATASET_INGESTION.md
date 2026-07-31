# Phase 108B production gate

Production preparation reports quarantined source/candidate counts, UUIDs, namespaces, severities, and dispositions. Quarantined candidates never enter dependency-closed batches and therefore cannot be promoted. Unaffected candidates continue deterministic planning. The official rerun has not occurred, so this change must not be described as resolving the corpus: rerun must complete provider validation or expose the next fatal issue.

---

# Production Dataset Ingestion

> **Phase 108A operational correction:** the first official dry run downloaded and checksum-
> verified AllPrintings but stopped on `duplicate external identifier deckboxId:2676`. Provider
> validation now exposes non-guaranteed third-party collisions as deterministic review-required
> findings in the manifest and review packages while strict and internal identities still fail.
> No canonical write or promotion occurred, and Architecture v12 is unchanged.

> **Phase 106 — implemented 2026-07-31. Architecture v12 unchanged.**

## Architecture assessment

The Phase 105 merge (`43796c0`) is the baseline. No architectural defect was found: the
Canonical Repository remains the sole source of truth; official acquisition is complete;
MTGJSON remains reference evidence; independent decisions govern promotion; and typed projection
remains downstream of promotion. No Project Architect approval is required.

## Workflow and batching

`ProductionMTGJSONIngestion.prepare()` composes the approved local-file provider execution with
deterministic review preparation. It validates and registers artifact and dataset, generates
candidates, rejects unsupported reference entities, holds incomplete Card or Printing candidates
as unresolved, and derives stable canonical-safe identifiers. Candidates are sorted and grouped
as Card-plus-Printings dependency closures, then packed in order up to the configured batch size.
A single unusually large closure may exceed that size rather than create an invalid Printing-only
batch. Each immutable report includes entity, assertion-candidate, duplicate, rejected,
unresolved, promoted, and projection counts. Re-preparation of an identical checksum replays the
retained manifest.

## Promotion, projection, replay, and rollback

Each batch is an independent Knowledge Review Package with checksum lineage. A named independent
reviewer promotes exactly one batch through `CanonicalPromotionEngine`, the sole writer. The same
decision is idempotent. Typed projection runs only after successful promotion. Unsupported
MTGJSON Set, Identifier, Language, Rarity, and Finish candidates remain evidence rather than
entering the frozen Card/Printing contract.

Audits retain the approved package. `verify_downstream()` times replay and compares it with
`canonical/state.json`. `rollback()` creates a separately approved compensating event without
deleting evidence, versions, reviews, or audit history. Restoration requires a new decision.

## Downstream compatibility

Acceptance tests prove immediate use by Query, Analytics, Semantic Query, and Reasoning Context.
They construct an `AIModelRequest` with provider `not-invoked`; no provider or inference runs.

## Performance observations and full-corpus readiness

The manifest records wall-clock import duration, candidate throughput, batch size/count, and
approximate peak resident memory (`ru_maxrss`). Promotion reports duration; projection reports
duration, throughput, and count; verification reports replay duration. The 48-entity
production-shape acceptance run uses five dependency-closed batches of at most ten entities and
validates replay, rollback, and duplicate prevention. These are observations, not service levels.

An operator acquisition attempt on 2026-07-31 used the approved Phase 105 boundary, but this
environment returned HTTP 403 from the configured official AllPrintings URL. Therefore no
unverified substitute, fabricated full-corpus measurement, or `data/local/` artifact is committed.
The full-corpus run is **operationally ready but execution pending** in an environment permitted to
reach that URL. There, acquire and verify the official file, prepare all batches, independently
approve one bounded batch, promote and verify it, rehearse rollback, and retain the local report.
Full-corpus or automatic promotion remains unauthorized.
