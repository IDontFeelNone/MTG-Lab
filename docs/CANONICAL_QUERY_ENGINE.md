# Canonical Query Engine v1

> **Status: Implemented — Phase 91. Architecture v12 is unchanged.**

## Pre-implementation assessment

Phase 90 is merged. Its governed MB2 pilot correctly stopped because the supplied MTGJSON
fixture contained no MB2 evidence; canonical state was not changed. The repository already
had validated typed aggregates, legacy schema compatibility adapters, evidence-bearing
Card/Printing documents, review packages, promotion state, and immutable audits. What it
lacked was one provider-neutral read boundary: consumers otherwise had to know storage
paths, repository generations, or promotion artifact shapes.

## Architecture compatibility review

The engine is an additive, read-only facade over the canonical repository. It does not
change Architecture v12, canonical schemas, evidence, promotion authority, or filesystem
layouts. Repository records remain the source of truth; query results are deterministic
projections. Unknown and conflicting states remain explicit. No provider or product is
special-cased. Analytics, Simulation, REST, and AI remain outside this phase.

```text
Canonical Repository
        |
        v
Canonical Query Engine
        |-- Entity and Search Queries
        |-- Relationship Queries
        |-- Provenance and Audit Queries
        |-- Dataset Queries
        `-- Validation Queries
```

Downstream code must import `CanonicalQueryEngine` and consume `QueryResult`; direct reads
from `repository.*`, canonical paths, promotion state, or audit paths are unsupported.

## Stable query contract

Every entity result has these storage-independent fields:

* `canonical_identity` and `entity_type`;
* `canonical_values` (a detached JSON-compatible value map);
* `provenance_summary`, including source IDs, acquisition lineage, dataset identity,
  review package, evidence assertions, provider policy, and promotion history;
* `confidence` and explicit `uncertainty`; and
* `supersession_state` (`current` or `superseded`).

Results are immutable values. Public collections are tuples ordered by entity type and
canonical identity. Mapping keys and audit traversal are sorted. Identical repository
bytes and identical arguments therefore return equal values in equal order. Queries do
not use clocks, networks, provider calls, randomness, fuzzy matching, or mutable caches.

## Supported queries

Entity retrieval supports canonical, provider, external, printing, and set identifiers;
entity type; exact Card name; and normalized Card name. Search supports exact, normalized,
prefix, and optional case-insensitive comparison. Normalization uses Unicode NFKC,
case-folding, whitespace collapse, and no approximate matching.

Relationship traversal supports Card-to-Printings, Printing-to-Card,
Printing-to-Set, dataset-to-promoted-entities, review-package-to-promoted-entities, and
promotion-to-audits. A Set result is a deterministic virtual relationship projection; it
does not create a new canonical Set entity.

Validation queries expose unknown, conflicting, unresolved, rejected, validation-failure,
and superseded states. Rejections and failures remain audit results rather than being
misrepresented as canonical entities.

## Examples

```python
from query import CanonicalQueryEngine

query = CanonicalQueryEngine("magic")
card = query.entity("magic.lightning-bolt")
provenance = query.provenance("magic.lightning-bolt")
printings = query.related("magic.lightning-bolt", "card_printings")
```

Equivalent command-line operations are:

```console
mtg-lab query entity magic.lightning-bolt
mtg-lab query search "light" --mode prefix --case-insensitive
mtg-lab query dataset dataset-id
mtg-lab query provenance magic.lightning-bolt
mtg-lab query validation unknown
```

## Provenance model and extension strategy

Legacy field provenance and v3 assertions are projected into one summary without rewriting
either source. Knowledge-promotion records additionally expose acquisition lineage,
dataset identity, review package and policy, assertion references, confidence,
uncertainty, supersession, and audit history. Missing historical dimensions are represented
as empty collections or `null`, never invented.

New canonical entity families should first join the repository contract, then receive a
generic result projection and stable relationship name. Future indexes or databases may
replace scan mechanics only behind this interface and must prove result equivalence and
ordering. Analytics and AI integrations must use query results, cite the included
provenance, preserve uncertainty, and keep derived conclusions outside canonical truth.
