# Structured evidence continuation of draft PR #171

This supplement supersedes the acquisition limitation in `MB2_REFERENCE_COVERAGE_REVIEW.md`. The original 16-file packet remains byte-identical as historical evidence. Baseline main is `9e2a5eff32704ab2c288608bb2397858481a44b8`; the original PR head is `24719e132ad395e3bbdb762bb9a2adad2aaebf7d`. Architecture v12, canonical data and historical snapshot bindings are unchanged.

## Acquired evidence and namespaces

`reference-reviews/mb2-reference-coverage/structured-2026-10-13/source-receipts.json` records actual source URLs, retrieval timestamps, upstream and retained projection hashes, exact upstream record byte ranges and field-value projection semantics. Each retained source uses the existing immutable `RawSnapshotStore` contract. Complete upstream responses remain in private working storage; the public packet retains bounded projections, not the full PLST corpus, MB2 dataset, license-page HTML or Scryfall responses.

MTGJSON `https://mtgjson.com/api/v5/PLST.json` (generation 2026-10-12, version `5.3.0+20261012`) contains 5,694 records. Its SHA-256 is `e528b3b348a33b09bb01cc26d17ac0a5cb5b6ed8d1ab27af8f0b6dfa60fa95e8`, matching the newly downloaded `.sha256` response. The public projection preserves the exact bytes of 273 selected record objects inside a bounded wrapper, plus their original JSON pointers and byte offsets. Selection requires a catalog name correspondence and an explicit `sourceProducts` intersection with MB2 sealed products.

MTGJSON `https://mtgjson.com/api/v5/MB2.json` has SHA-256 `07c2a315ca3723f54f8a48fc25664671a75e1be4f45e99e94928ee54d59a2709`, also matching its newly downloaded `.sha256`. Its retained exact field-value projection supplies the three MB2 sealed-product identities used to verify membership links. PLST is a wider catalog containing products beyond MB2; neither a name match alone nor `set=mb2` establishes ordinary-reprint membership. The original Wizards Expansion column remains a historical lead, not an exact Printing namespace.

Four bounded read-only Scryfall `POST https://api.scryfall.com/cards/collection` requests returned 75, 75, 75 and 48 records with no `not_found` IDs. The retained factual projection cross-checks each Scryfall Printing ID, Oracle ID, set, collector number, language and full name against MTGJSON. It includes request IDs, response digests, response pointers and actual retrieval times. No images, prices or Oracle prose are mirrored. The record IDs resolve to `set=plst`, not `mb2`.

The 273 catalog labels now correspond to 273 distinct source-supported Oracle IDs and 273 provider Printing identities **within this bounded selection**. This is not a census of all MB2 content. Nezumi Graverobber and Shepherd of the Flock map explicitly to their complete two-face names; Give // Take remains a full split-card name. These catalog correspondences do not confirm any owner's unresolved spelling proposal. Gigantosaurus is explicitly Japanese PLST `M19-185j` in both providers; no English substitute or physical-copy inference is made.

The newly retrieved MTGJSON license page supplies its current MIT permission text, copyright and notice requirements; its rendered main text and original HTML checksum are retained. Adapter constants with historical CC BY labels are not used to license this acquisition. MTGJSON attribution and its notice accompany the projections. Rights in third-party card content and trademarks remain with their owners. Scryfall terms were not newly retrieved through the permitted API hostname; its factual subset and the original Wizards factual subset remain subject to independent terms/evidence review. No license for full-response/article redistribution is asserted.

## Exact pending candidate set and coverage

`candidate-preparation.json` contains the complete proposed set and field-level lineage; `review-summary.json` lists every existing mapper candidate identifier. The existing MTGJSON parser/mapper, import candidate constructor and validators are reused. No name-based identity scheme is introduced: Card IDs are Oracle IDs; Printing IDs are MTGJSON UUIDs; Scryfall identifiers retain the existing mapper's deterministic namespace IDs.

| Proposed entity | Count | Purpose |
| --- | ---: | --- |
| Card | 273 | Missing source-supported Oracle identities |
| Printing | 273 | Missing PLST UUID records, with original provider metadata |
| Identifier | 273 | Scryfall Printing alias dependencies for exact readback |
| New finish/dependency beyond identifiers | 0 | Existing canonical `nonfoil` finish reused |

All 819 candidates remain pending, with normalized validation state `requires_review` and import review status `pending`. There are zero human approvals and no admission readiness. Optional identifiers (2,348 mapper rows), two language labels, four rarity labels and the PLST set description are retained as source metadata, not proposed independent canonical entities. All provider identifiers remain preserved in the source records and mapped Printing fields. Printing/Card/finish/identifier dependency closure is verified. Unknown and unmapped provider fields are retained; mechanics are not implemented.

The original 60 canonical Card/Printing reference pairs remain source-bound to snapshot `sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`. None of the 273 proposed Cards or PLST Printings overlaps current production identities. The existing finish dependency is reused; no existing record is replaced.

| Coverage | Current production | Conditional after separate approved promotion |
| --- | ---: | ---: |
| Bounded ordinary catalog Cards | 0/273 | 273/273 |
| Bounded ordinary catalog Printings | 0/273 | 273/273 |
| Entire production Card store | 384 | 657 |
| Entire production Printing store | 913 | 1,186 |
| Entire production identifier store | 235 | 508 |
| Production finishes | 2 | 2 |

Conditional totals are arithmetic over the proposed set, not production coverage or a promotion plan. Admission would change the query snapshot and expand the live mechanical cohort; it is not authorized here. All retained mechanical artifacts and their original sources remain unchanged. Essence of Ajani remains nonordinary `layout=emblem`, `type_line=Emblem`, with no ordinary Card candidate. It does not block preparation of unrelated ordinary records.

## Review limits and owner evidence

All 273 public catalog labels have structured evidence. Remaining gates are independent source/terms review, review of the exact candidate set and dependencies, the Japanese Printing distinction, and a separately authorized compatibility review before any promotion. Provider catalog identities do not assign Printings to physical copies. A future physical identification task needs collector number/set, language and finish evidence (or legible images) where an exact Printing is required. Unconfirmed owner spelling proposals need owner confirmation; retained declarations and the Forest clarification do not need to be supplied again. There is no requirement for additional ownership evidence merely to review this public packet.

The private package and its historical replay dependencies are outside the repository. Personal inventory, quantities, declarations, position mappings, storage and prior assessment data are excluded from this PR. No private snapshot is regenerated or repinned.

## Offline verification

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/verify_mb2_reference_packet.py --check` verifies both packets, the original immutable manifest, raw snapshots, source-to-parsed correspondence, source-backed identities, the current query snapshot, cross-provider records, candidate lineage, dependency closure and exact deterministic replay. `tests/test_mb2_reference_packet.py` uses the repository's unittest infrastructure and temporary packet copies to reject altered bytes, parsed counts/rows, orphan dependencies, forged provenance, false approvals, changed identity/snapshot references and false upstream-retention claims, including tampering with recomputed outer hashes.

Actual validation results are recorded separately in `MB2_REFERENCE_STRUCTURED_VALIDATION.json` beside this document after execution. The prior 795-test checkpoint remains historical. Stop for independent Project Manager review with PR #171 in draft; no merge, promotion, reassessment or new milestone.
