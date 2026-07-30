# Canonical Dataset Import Framework

**Status:** Phase 86 pilot complete (2026-07-30)  
**Architecture:** v12 unchanged

## Pre-implementation assessment and compatibility review

Phase 84 already preserved immutable provider bytes and produced normalized candidates and assertions. Phase 85 already enforced review-package, policy, integrity, conflict, uncertainty, decision, and audit gates before promotion. The missing capability was orchestration: datasets were not first-class, identifiers were not resolved before acquisition, and no durable session joined the stages. Phase 86 composes those systems rather than replacing or bypassing them.

This is compatible with frozen Architecture v12. Canonical state remains the sole authority; raw bytes remain immutable; uncertainty and rejection remain explicit; reviewed promotion remains the only writer; and behavior remains data-driven. No Tier 0 or canonical Card/Printing contract changes were made.

## Lifecycle

1. **Registration** validates logical identity, version, provider, publication date, source schema, and supported types. A stable canonical import ID is derived from identity, version, and provider. A changed registration cannot overwrite an existing version.
2. **Resolution** prefers a canonical identifier, then deterministically derives one from a provider identifier. Canonical, provider, external, and alternate identifiers participate in collision detection. Duplicates, collisions, conflicts, and missing identities are reported rather than guessed.
3. **Acquisition** passes eligible reviewed records through the existing provider, acquisition run, checksum-addressed raw snapshot, normalization, and candidate assertion stages.
4. **Review** builds and validates the existing knowledge review package. Unknown optional values remain visible and require an explicit decision.
5. **Promotion** invokes `CanonicalPromotionEngine`; the importer never writes canonical knowledge directly.
6. **Reporting** writes deterministic session and report artifacts containing every outcome and cross-stage identifier. Identical inputs, actor, and timestamp return the same result.

## Registration example

```json
{"logical_dataset_identity":"mtg-lab-pilot-cards","dataset_version":"1.0.0","provider":"MTG Lab reviewed pilot","publication_date":"2026-07-30","schema_version":"pilot-card-dataset-v1","supported_entity_types":["card","printing"]}
```

```bash
PYTHONPATH=src python -m mtglab dataset register data/fixtures/canonical_import/pilot-manifest.json
PYTHONPATH=src python -m mtglab dataset list
```

## Import sessions and CLI

```bash
PYTHONPATH=src python -m mtglab import mtg-lab-pilot-cards --version 1.0.0 --source data/fixtures/canonical_import/pilot-reviewed-cards.json --actor reviewer --timestamp 2026-07-30T16:00:00Z
PYTHONPATH=src python -m mtglab import status IMPORT-SESSION-ID
PYTHONPATH=src python -m mtglab import report IMPORT-SESSION-ID
```

A session records the dataset, acquisition run, review package, promotion ID, imported/rejected/unresolved entities, validation, status, timing, and input digest. `--require-complete` fails before acquisition when any record is ineligible; otherwise eligible records form an explicit partial import.

## Report example, pilot, and auditability

`canonical-import-report-v1` contains dataset/import summaries, all three outcome lists, validation, promotion and audit summaries, collision details, and completeness metrics. The pilot has 39 records: 25 cards and 10 printings import; two colliding aliases and one conflicting identity reject; one identity remains unresolved. It includes multiple printings, foil/non-foil pairs, transform faces, alternate identifiers, missing optional metadata, conflicts, and unknown values. It contains no Mystery Booster 2 data.

The session links the registry to raw snapshot, normalized artifact, assertions, review package, immutable promotion audit, and canonical versions. Large product imports can scale provider adapters and inputs while retaining these generic gates; they must not introduce product-specific shortcuts.
