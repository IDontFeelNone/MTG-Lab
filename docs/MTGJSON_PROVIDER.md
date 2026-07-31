# MTGJSON Reference Dataset Provider v1

**Status:** Phase 99 implemented; local reference evidence only
**Architecture:** v12, unchanged

## Architecture and authority

The provider in `src/providers/mtgjson` is the first concrete implementation of the
Multi-Source Evidence Acquisition Framework. It discovers, validates, parses, maps, inspects,
and plans around a caller-supplied local JSON artifact. It performs no networking, download,
review, promotion, or canonical write. MTGJSON remains a Reference Dataset; the Canonical
Repository remains the only source of truth.

The provider reports the Phase 98 registration, planning, artifact-validation, and
dataset-validation capabilities. A plan expressly reports that networking, automatic download,
and canonical writes are disabled and independent review is required.

## Supported schema and entities

Version 1 accepts MTGJSON major-version 5, AllPrintings-style documents containing `meta` and
`data` objects. `meta.version` must be semantic-version text, `meta.date` must be ISO 8601, and
each set must contain matching `code`, non-empty `name`, and a `cards` array. The provider
prepares candidate records for Cards, Printings, Sets, Languages, Rarities, Finishes, and
Identifiers.

Product, sealed-product, booster, collation, price, rulings, legality, token, deck, inventory,
and product-specific entities are unsupported. They are neither inferred nor promoted.

## Deterministic mapping

Sets map code, name, and release date. Cards map normalized name, layout, colors, and mana cost;
Printings map UUID, card reference, set code, collector number, language, rarity, finishes, and
sorted identifiers. Languages, rarities, finishes, and identifiers become explicit reference
candidates. Candidate identifiers are SHA-256 identities over canonical compact JSON natural
keys, and output is sorted by candidate identifier.

Missing optional values remain explicit `{ "status": "unknown" }` values. Every unsupported
source field and its original JSON value is retained in `unknown_fields`; unsupported input is
never silently discarded. These mappings are candidates, not canonical entity mappings.

## Validation and licensing

Validation fails closed for malformed JSON, missing top-level structures, unsupported schema
majors, malformed dates, missing set/card identity fields, malformed identifier maps, duplicate
printing UUIDs, and duplicate printing-scoped external identifiers. Oracle identifiers may
repeat across printings because they identify a shared Card. Artifact contracts require JSON
media type, lowercase SHA-256, MTGJSON provider identity, and supported licensing. Dataset
contracts require MTGJSON major version 5, at least one artifact, supported entity declarations,
and supported licensing. `validate --sha256` verifies supplied bytes against an expected digest.

Provider policy records MTGJSON attribution and CC BY 4.0 assessment while conservatively
declaring local reference use and no redistribution. Operators remain responsible for verifying
the terms applicable to the supplied artifact; incomplete or unsupported framework licensing
metadata fails closed.

## CLI and future promotion

All commands emit deterministic JSON:

```text
mtg-lab provider mtgjson validate PATH [--sha256 DIGEST] [--format json]
mtg-lab provider mtgjson inspect PATH [--format json]
mtg-lab provider mtgjson plan PATH [--format json]
```

Future promotion, if separately authorized, must register immutable artifacts and datasets,
complete validation and independent review, create a promotion candidate, and use the existing
Canonical Promotion Engine. Provider output can never promote itself.
