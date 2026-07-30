# Mystery Booster 2 MTGJSON Pilot Import

> **Phase 90 status: stopped after validation (2026-07-30).** The supplied,
> reproducible MTGJSON fixture contains no Mystery Booster 2 records. No dataset was
> registered and no entity was resolved or promoted. Architecture v12 remains frozen.

## Pre-implementation assessment

The Phase 89 adapter is merged and provides the required provider edge. The repository was
searched for supplied MTGJSON datasets; the only one is
`tests/fixtures/mtgjson/AllPrintings.json`. Its bytes were validated by the existing adapter,
and its SHA-256 is
`d31b4daf1e02e54de2ec20228930f65acf37af94ba0caad8efb0bc5dbd08074a`.

The fixture metadata identifies MTGJSON 5.2.1, generated
`2026-07-30T00:00:00Z`. Its sole data member is set code `TST`, named **Adapter Test Set**.
It contains no `MB2` set member and therefore supplies zero Mystery Booster 2 cards. The
Phase 90 stop condition applies. Live retrieval was neither attempted nor permitted, and
the synthetic TST records were not relabeled or treated as MB2 evidence.

## Architecture compatibility review

The intended lifecycle is compatible with Architecture v12 by composing the existing
MTGJSON adapter, external ingestion, immutable snapshot, normalization, candidate,
validation, human review, registration, resolution, and controlled promotion boundaries.
Canonical state remains the only authority, unknowns and conflicts remain explicit, and
provider knowledge remains at the edge. No product-specific runtime logic or architectural
change is necessary.

Failing closed at source validation is also required by that architecture. Continuing from
a non-MB2 fixture would fabricate product membership and corrupt provenance. Accordingly,
the workflow stopped at **validation**, before raw-snapshot acquisition for an MB2 import.
No later stage was bypassed; none was eligible to execute.

## Dataset source and pilot scope

| Item | Requested MB2 pilot | Supplied evidence |
| --- | --- | --- |
| Source | User-supplied dataset or checked-in reproducible fixture | Checked-in MTGJSON synthetic fixture |
| Set | Mystery Booster 2 (`MB2`) | Adapter Test Set (`TST`) |
| Cards | 25–50 representative cards | 10 synthetic cards; 0 MB2 cards |
| Multiple printings | Exercise where represented | Not assessable for MB2 |
| Rarities | Multiple | TST has 4 common, 3 uncommon, 2 rare, 1 mythic |
| Foil/non-foil | Preserve where represented | Unsupported by the adapter and not assessable for MB2 |
| Multifaced/incomplete/identifier edges | Exercise where present | Not assessable for MB2 |

The selected MB2 pilot scope is therefore **empty**. The TST fixture was used only to prove
the evidence gap and adapter readability, not as import input.

## Supported and unsupported fields

Had admissible MB2 evidence been supplied, the Phase 89 mapping would support Set identity,
name and release date; Card identity, name, layout, colors and mana cost; and Printing UUID,
collector number, Set relationship, language, rarity, and identifiers. Missing supported
values would remain explicit `{"status":"unknown"}` values.

Rules text, type line, legalities, prices, foreign data, leadership skills, purchase URLs,
booster configuration, tokens, rulings, artist data, finishes, frame treatments, and other
unmapped MTGJSON metadata remain unsupported. In particular, Phase 90 would not infer
finishes, treatments, print-sheet position, slot probability, collation, or hidden product
structure.

## Validation and deterministic evidence-gap report

Adapter validation deterministically reported 21 normalized records: one TST Set, ten
Cards, and ten Printings. It observed one explicit unknown value and the unsupported Card
fields `text` and `type`. The fixture has no MB2 member. The machine-readable result is
`data/validation/mystery_booster_2/phase_90_mtgjson_evidence_gap.json`; a regression test
recomputes the checksum, dataset identity, counts, and zero-import outcome.

## Review package and canonical import results

No MB2 raw snapshot, candidate assertions, Knowledge Review Package, dataset registration,
entity-resolution session, promotion audit, or import report was created. Creating any of
them from TST data under an MB2 identity would falsely imply supporting evidence.

| Report category | Result |
| --- | ---: |
| Imported entities | 0 |
| Rejected entities | 0 (none entered resolution) |
| Unresolved entities | 0 (none entered resolution) |
| Identifier collisions | 0 evaluated for MB2 |
| Unknown values | Not evaluated for MB2 |
| Conflicts | 0 evaluated for MB2 |
| Canonical promotions | 0 |
| Audit records | 0 |
| Requested card coverage | 0/25–50 |
| Product completeness | 0%; no completeness claim |

These zeros describe a pre-import evidence stop, not a successful empty import.

## Evidence limitations and lessons before a full import

1. A future run must receive an unmodified, reproducible MTGJSON v5 dataset whose `data`
   object actually includes `MB2`; repository-derived MB2 records cannot substitute for the
   provider bytes.
2. Source validation must precede sampling. Only after validating the MB2 member may the
   operator select 25–50 records that represent the edge cases actually present.
3. Finish data is outside the current adapter mapping. It must remain unsupported unless a
   separately governed generic mapping is approved; it must not be inferred for this pilot.
4. The complete lifecycle remains viable without MB2-specific core logic, but that claim
   cannot be empirically validated until admissible MB2 bytes are supplied.
5. Repeatability begins with the exact source checksum. A future report must retain dataset
   version, sample-selection rule, review decision, resolution outcomes, promotion audits,
   and deterministic completeness metrics.

## Reproduction

```bash
sha256sum tests/fixtures/mtgjson/AllPrintings.json
PYTHONPATH=src python -m mtglab adapter detect tests/fixtures/mtgjson/AllPrintings.json
PYTHONPATH=src python -m unittest tests.test_phase_90_mtgjson_evidence_gap
```

The first command identifies the exact supplied bytes. The second validates the MTGJSON
envelope and reports 21 records. The test proves that the only set is TST and that the
governed report records no registration, resolution, or promotion.
