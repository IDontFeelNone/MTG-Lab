# Typed Canonical Projection Engine v1

> **Status:** Current — Phase 103, 2026-07-31  
> **Architecture:** v12 unchanged

## Architecture assessment

The merged Phase 102 baseline is present at merge commit `8014004`. Phase 102 concluded
that the governed representative path is deterministic and fail-closed, while generic
Phase 85 assertion-path values were not the strongly typed records expected by downstream
filters and analytics. That was an implementation boundary gap, not a canonical-contract
or Tier 0 defect. Architecture v12 remains unchanged; the Canonical Repository remains the
sole source of truth; and validation, an independent review decision, and promotion remain
mandatory. Projection is a read of successful canonical promotion state, never a second
promotion path or writer to canonical assertions. No Project Architect approval was needed.

```text
Evidence -> Validation -> Independent Review -> Promotion -> Canonical Assertions
         -> Typed Projection -> Typed Canonical Repository -> Consumers
```

## Lifecycle and mapping rules

`TypedCanonicalProjectionEngine` reads the current, promoted assertion state and resolves
each evidence-reference identifier from successful immutable promotion audits. Its
versioned registry maps only approved types: Card and Printing to v3; Product and
ProductVersion to v2; and Rarity, Finish, and Treatment to their existing typed records.
Language remains a Printing field. Set remains the Query Engine's existing deterministic
virtual relationship, because Architecture v12 defines no standalone Set or Language
entity. No new domain type is introduced.

Paths lose their leading slash. Card defaults already specified by v3 are deterministic:
`game=magic`, `normalized_name=name.casefold()`, and `layout=normal`. Printing `rarity_id`
maps to the v3 `rarity` field; a reviewed null optional value becomes an explicit v3
`unknown` knowledge value. Product defaults are the existing v2 foundation lifecycle and
empty version list. Original approved assertions are embedded as promoted provenance;
derived required fields receive deterministic derived assertion records. The projection
also materializes repository Source Records needed by existing provenance validation.

## Validation

Validation rejects missing required assertions, duplicate assertion use or destinations,
unsupported entity types/combinations, inconsistent identifiers or lifecycle state,
superseded current records, empty projections, and any output that fails existing schema,
referential, lifecycle, or duplicate validation in `CanonicalRepository`. A failure occurs
before the typed repository is replaced. In particular, the engine cannot accept candidate,
rejected, conflicting, or otherwise unpromoted assertions because their identifiers cannot
be resolved through a successful promotion audit.

## Audit and deterministic guarantees

The projection identifier hashes the projection schema version, game, and canonical-state
digest. Sorted traversal, canonical JSON encoding, content-derived identifiers, atomic
repository replacement, and create-only audit storage make execution deterministic,
repeatable, and idempotent. Identical state produces byte-identical entity files and returns
the original audit even when a later invocation supplies another timestamp.

Each immutable audit records the projection identifier, original source assertion IDs,
projected entity IDs, requested timestamp, schema version, complete validation result,
canonical-state digest, and typed-repository digest. Audits live outside both canonical
assertion state and the typed repository.

## CLI

```bash
mtg-lab projection validate --format json
mtg-lab projection project --timestamp 2026-07-31T12:00:00Z --format json
mtg-lab projection inspect [projection-ID] --format json
```

All commands are local and JSON-only. `project` reads `data/canonical/state.json`, writes
the existing `data/canonical/games/<game>` typed repository through its repository-owned
atomic import boundary, and writes audits under `data/projection-audit`.

## Limitations

This version assumes the documented single-writer filesystem model; it adds no database,
cross-process lock, generation guard, networking, full-corpus performance claim, simulation,
AI provider, dataset, or product-specific runtime rule. It projects only current state;
canonical history and rollback remain owned by the Promotion Engine. Taxonomy entities are
projected when explicitly present in canonical state; values referenced only as Printing
fields do not silently create canonical taxonomy assertions.
