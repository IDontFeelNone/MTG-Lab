# AI Reasoning Context Layer v1

> **Status: Current — Phase 94 implemented; review and green CI pending.**

## Architectural role and boundary

The AI Reasoning Context Layer is a deterministic evidence-preparation consumer below the
Canonical Semantic Query Layer. `ReasoningContextBuilder` accepts only public `SemanticRequest`
operations and receives `SemanticResponse` values from `CanonicalSemanticQueryEngine`. It never
loads repository storage, database tables, files, Query Engine objects, or Analytics Engine
internals. Analytics inclusion is requested through a semantic analytics operation.

This layer performs no reasoning. It has no model-provider integration, API key, natural-language
prompt contract, generated advice, embeddings, ranking, simulation, or canonical write path.
Architecture v12 and all frozen upstream contracts remain unchanged.

## Versioned request contract

`canonical-reasoning-context-v1` requests contain one structured semantic request plus optional
entity-type, dataset, provenance-source, validation-state, and inclusive confidence filters.
They also declare whether analytics is included, three non-negative size limits, and the sole v1
truncation policy, `canonical-order-prefix`. Natural-language prompts are not accepted.

Malformed and unsupported requests raise typed `ReasoningContextError` subclasses. Invalid schema
versions, semantic operations, confidence ranges, limits, analytics operations, and truncation
policies never fall back silently.

## Result, evidence, and provenance contract

Every immutable result identifies its context, canonical snapshot, semantic schema, and optional
analytics snapshot. It contains the normalized request, selected entities and mechanically
projected `*_id` relationships, analytics results, provenance and evidence maps, validation and
confidence maps, omitted counts, truncation metadata, warnings, and ordering declaration.
Nested lists become tuples and mappings become read-only mapping proxies.

Evidence entries retain canonical identity and type, source dataset records, copied provenance,
validation state, confidence (including explicit `null`), canonical snapshot, and lifecycle state.
No provenance is fabricated: when assertions are absent, only existing source identifiers may form
references; when neither exists, the evidence map remains empty. Unknown, incomplete, superseded,
and absent/null values stay distinct.

## Determinism and truncation

Entities sort by `(entity_type, canonical_identity)`, relationships by `(relationship_type,
source, target)`, and evidence by evidence identifier. Limits retain the prefix of those orders.
All omitted counts and each applied limit are reported. The context identifier is SHA-256 over the
normalized request, exact snapshots, selected content, lineage, omissions, truncation, and warnings.
Stable JSON uses sorted keys and compact separators. Identical requests and snapshots therefore
produce identical bytes and identifiers.

## CLI

```bash
PYTHONPATH=src python -m mtglab reasoning context --type card --format json
PYTHONPATH=src python -m mtglab reasoning entity magic.lightning-bolt --format json
PYTHONPATH=src python -m mtglab reasoning dataset foundation-magic --format json
PYTHONPATH=src python -m mtglab reasoning analytics --type card --format json
PYTHONPATH=src python -m mtglab reasoning provenance source-id --format json
```

Success output is the structured context envelope. Runtime contract failures return status 2 and a
JSON error containing a stable code and message. CLI parsing failures retain standard argparse
behavior. Output never contains advisory or conversational prose.
