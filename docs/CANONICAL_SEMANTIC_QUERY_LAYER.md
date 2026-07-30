# Canonical Semantic Query Layer v1

> **Status: Current — Phase 93 implemented. Architecture v12 is unchanged.**

## Pre-implementation assessment

Architecture v12 already requires future intelligence consumers to use deterministic,
provider-neutral canonical boundaries. Phase 91 supplies the sole canonical read facade and
Phase 92 supplies content-addressed derived analytics. Phase 93 therefore fits strictly
downstream: it maps a finite structured operation and typed parameters to an existing query or
analytics call and returns their data and lineage.

This composition preserves the constitutional laws that canonical state is the single source
of truth, AI is not the repository, derived knowledge remains derived, lineage is preserved,
and failure is explicit. It introduces no repository access, writer, promotion, schema migration,
product-specific behavior, simulation, inference, fuzzy matching, natural-language parsing, or
generated answer. Canonical schemas and Architecture v12 contracts remain frozen; the semantic
request/response envelope is a new downstream consumer contract.

Unknown identifiers and datasets, invalid operations, missing or extraneous parameters,
unsupported validation states, invalid confidence bounds, and unsupported semantic schema
versions fail explicitly. Empty snapshots remain valid for list and analytics operations.
Provenance is copied from canonical results rather than reconstructed or inferred.

## Contract and CLI

`SemanticRequest` and `SemanticResponse` are immutable and use schema version
`canonical-semantic-query-v1`. Every response identifies the exact canonical snapshot, carries
deterministically ordered results and provenance references, and includes a content-addressed
analytics snapshot identifier when analytics is delegated.

Supported operations are identifier and normalized canonical-name lookup; entity listing by
type, dataset, source provenance, validation state, or inclusive confidence range; and canonical
summary, dataset, provenance, and validation analytics. `CanonicalSemanticQueryEngine` accepts
structured values only and delegates exclusively to `CanonicalQueryEngine` and
`CanonicalAnalyticsEngine`.

The JSON CLI boundary is `mtg-lab semantic find`, `semantic list`, `semantic analytics`,
`semantic dataset`, and `semantic provenance`. Output is the response envelope, not prose.

Phase 93 does not implement AI reasoning, natural-language understanding or generation,
recommendations, simulation, REST, canonical mutation, or MTG-specific runtime behavior.
