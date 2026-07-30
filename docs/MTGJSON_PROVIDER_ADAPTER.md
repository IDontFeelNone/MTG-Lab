# MTGJSON Provider Adapter v1

> **Status: Current — Phase 89.** Architecture v12 remains frozen. The adapter prepares
> candidates for human review; it does not establish canonical truth or invoke promotion.

## Architecture compatibility review

The adapter is an additive provider edge built on the Phase 88 `FormatAdapter` extension
point. All MTGJSON detection, validation, metadata interpretation, and field mapping live in
`external_ingestion.mtgjson`. The generic external ingestion coordinator, immutable raw
snapshot store, Knowledge Review Package, provider trust policy, and controlled promotion
boundary are unchanged.

This placement preserves Constitution laws 1–5, 8, 10, 12, and 14: supplied bytes remain
immutable; normalization makes candidates rather than truth; unsupported values remain
visible; the generic core contains no provider branch; and successful acquisition stops at
`awaiting_human_review`. No Tier 0 entity, schema, writer, trust rule, dependency direction,
or Architecture v12 contract changes. A full MTGJSON corpus is neither included nor imported.

## Detection, versions, and metadata

v1 detects an uncompressed AllPrintings-style JSON object containing `meta` and `data`.
`meta.version` must be semantic-version shaped with major version 5; other majors fail
closed. `meta.date` must be ISO 8601. Each member of `data` must be a Set object with a
`cards` array. Future MTGJSON major versions require a separately reviewed adapter update.

A generated external dataset manifest captures:

```json
{
  "dataset_name": "AllPrintings",
  "provider": "MTGJSON",
  "version": "5.2.1",
  "publication_date": "2026-07-30",
  "source_attribution": "MTGJSON (https://mtgjson.com/)",
  "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
  "schema_version": "mtgjson-v5",
  "expected_entity_types": ["card", "printing", "set"]
}
```

The manifest additionally records a deterministic logical identity, source filename,
SHA-256 checksum, and manifest schema. `adapter detect` reports provider identity, adapter
version, MTGJSON version, dataset name, generation timestamp, licensing, attribution, and
normalized record count.

## Mapping summary

| MTGJSON source | Normalized target | Rule |
| --- | --- | --- |
| `data` key / Set `code` | Set `canonical_identifier`, `code` | Both codes must agree; lowercase stable `set-<code>` identity. |
| Set `name`, `releaseDate` | Set name, release date | Name required; absent release date is explicit unknown. |
| Card `identifiers.scryfallOracleId` | Card identity | Preferred cross-printing identity; otherwise a deterministic semantic fingerprint. |
| Card `name` | Card name / normalized name | NFC normalized and whitespace collapsed; case-folded normalized name. |
| `layout`, `colors`, `manaCost` | Card layout, colors, mana cost | Missing values are `{ "status": "unknown" }`; colors use a sorted WUBRG subset. |
| Card `uuid` | Printing identity | Required and unique; emitted as `printing-<uuid>`. |
| Card `number`, containing Set | collector number, `set_id` | Required number; stable relationship to normalized Set. |
| Card `rarity` | Printing rarity | Preserved source value or explicit unknown. |
| Card `identifiers` | Printing identifiers | Keys are sorted; values are preserved strings. |
| — | Printing language | `en`, because the supported AllPrintings card record is the English oracle record. |

One source printing produces one Printing record and references one deduplicated Card.
Each source Set produces one Set record. Canonical Card candidates shared by multiple
Printings are emitted once. Output order is Set-code and provider-card order at the adapter
edge; the generic normalizer subsequently sorts stable source identifiers.

## Supported and unsupported fields

Supported scope is Cards, Printings, Sets, identifiers, rarity, layout, colors, and mana
cost. The adapter intentionally does not map rules text, type line, legalities, prices,
foreign data, leadership skills, purchase URLs, booster configuration, tokens, rulings,
artist data, finishes, frame treatments, or other MTGJSON fields. Their source field names
are retained in `unsupported_fields`/the normalized record's unmapped source envelope; they
are not silently inferred or discarded. Unknown supported values use an explicit
`{"status":"unknown"}` value.

## Validation and deterministic normalization

The adapter fails before registration for malformed JSON, a missing metadata envelope,
unsupported major version, invalid generation timestamp, malformed Set/Card shape, missing
Set name or Card UUID/name/collector number, Set-code disagreement, malformed or duplicate
UUIDs, duplicate/conflicting identifiers, invalid colors, and conflicting facts for the same
canonical Card identifier. JSON serialization, sorted identifier/color keys, Unicode NFC,
whitespace normalization, deterministic fallback identity, checksum addressing, and generic
source-record sorting make repeated normalization byte-stable. Repeated acquisition of the
same logical version and bytes returns the existing registration; changed bytes under that
identity/version are rejected by the Phase 88 coordinator.

## CLI and examples

```bash
python -m mtglab adapter detect AllPrintings.json
python -m mtglab adapter inspect AllPrintings.json
python -m mtglab --data-root data adapter normalize AllPrintings.json \
  --timestamp 2026-07-30T18:00:00+00:00
```

A Card example is normalized to `name: "Alpha Adept"`, `normalized_name: "alpha adept"`,
`layout: "normal"`, `colors: ["U"]`, and `mana_cost: "{1}{U}"`. A corresponding Printing
references its Card and `set-tst`, retains collector number, rarity, and sorted identifiers.
A card lacking `manaCost` instead contains `mana_cost: {"status":"unknown"}`.

`normalize` generates the deterministic external manifest, stores the exact bytes in the
existing raw snapshot store, creates provider-neutral normalized source records and candidate
assertions, and prepares a Knowledge Review Package. It does not write canonical data.

## Extension strategy

Support for another MTGJSON dataset shape or major version belongs in a new/versioned adapter
or an explicit compatible expansion of this adapter with fixtures and validation. Add fields
only through provider-edge mappings into existing normalized concepts. If a desired concept
cannot be expressed by existing provider-neutral contracts, stop for architectural review;
do not add MTGJSON runtime branches to acquisition, review, promotion, or consumers.
