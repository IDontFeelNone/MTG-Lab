# Mystery Booster 2 Acquisition Pilot

> **Phase 87 status: stopped at the evidence gate (2026-07-30).** No dataset was
> registered, imported, or promoted. Architecture v12 remains unchanged.

## Pilot purpose and selected scope

Phase 87 proposed a deliberately bounded 25–50-card Mystery Booster 2 pilot spanning
Cards, Printings, external identifiers, finishes or treatments, multifaced cards, and
records with incomplete or conflicting evidence. Its purpose was to exercise the complete
Phase 86 governed lifecycle with real source material, not to claim product completeness,
model collation, or populate print sheets and slots.

## Pre-implementation source assessment

The repository contains source *records* for a Scryfall MB2 set page and the Wizards of
the Coast MB2 card-image gallery, plus a controlled four-record extract used by earlier
bounded waves. Those records identify URLs and access dates, but the repository does not
preserve the original page or API response bytes supporting the card-level claims. The
only retained official HTML artifact is a product-page title fragment; it cannot support
a 25–50-card acquisition pilot.

During this phase, attempts to retrieve the Scryfall search API, Scryfall API documentation,
and the Wizards/Scryfall web sources were blocked by the execution environment's outbound
network policy (HTTP tunnel 403; the search service also returned 401). Consequently, no
new immutable raw snapshot could be captured and independently reviewed.

The existing four-record controlled extract is insufficient for the requested size and
edge-case coverage. Treating its derived values as a new raw source would erase lineage,
and supplementing it from memory would fabricate evidence. The Phase 87 stop condition
therefore applies.

## Architecture compatibility review

A future pilot is compatible with frozen Architecture v12 if it composes the existing
acquisition, knowledge-review, dataset-registration, entity-resolution, and canonical-
promotion boundaries. Raw bytes must remain immutable; normalization must not establish
truth; conflicts and unknowns must remain explicit; promotion must remain fail-closed; and
no MB2-specific runtime branch may be added. No architecture or runtime change was made in
this stopped phase.

## Source inventory and provider policy assessment

| Provider | Intended stable locator | Evidence use | Licensing/attribution assessment | Phase 87 result |
| --- | --- | --- | --- | --- |
| Wizards of the Coast | `https://magic.wizards.com/en/products/mystery-booster/card-image-gallery` | Official product membership and displayed card facts | Attribution required; redistribution terms must be reviewed before retaining complete page/media bytes | Source record exists; supporting card-level raw bytes unavailable |
| Scryfall | `https://api.scryfall.com/cards/search?q=set%3Amb2&order=set&unique=prints` | Structured printing IDs, collector numbers, layouts, finishes, and related identifiers | Provider attribution and current API/data terms must be recorded with the snapshot | Retrieval blocked; no snapshot captured |
| Existing MTG Lab Wave 1/2 extract | `data/sources/magic/mb2-wave-{1,2}/` | Four bounded derived card/printing records | Repository-owned aggregate; external attribution retained, but it is not original provider material | Reviewable but too small and not an acceptable replacement for raw source bytes |

No provider policy was registered because publication/version metadata, immutable bytes,
and a legally reviewed redistribution posture could not all be established in this run.

## Acquisition, normalization, and review findings

The governed lifecycle stopped before **Raw Snapshot**. Therefore normalization,
candidate assertions, validation, Knowledge Review Package generation, dataset
registration, entity resolution, canonical promotion, and import reporting were not
executed. This is intentional fail-closed behavior, not a partial successful import.

Unknowns include the exact retrievable provider response version, publication timestamp,
complete licensing constraints for the captured representation, and whether a bounded
selection can simultaneously cover multifaced cards and finish/treatment distinctions.
No conflicting card facts were evaluated because no admissible snapshot entered review.

## Dataset registration example (not executed)

The following illustrates the intended identity only and is **not** a registered dataset:

```json
{
  "logical_dataset_identity": "mystery-booster-2-acquisition-pilot",
  "dataset_version": "unassigned",
  "provider": "Wizards of the Coast + Scryfall",
  "publication_date": "unknown",
  "schema_version": "reviewed-card-dataset-v1",
  "supported_entity_types": ["card", "printing"],
  "import_status": "not_registered_evidence_blocked",
  "canonical_import_id": null,
  "source_and_snapshot_lineage": []
}
```

## Import results, completeness, and limitations

- Candidate records: **0**
- Registered datasets: **0**
- Imported entities: **0**
- Rejected entities: **0** (nothing reached resolution)
- Unresolved entities: **0** (nothing reached resolution)
- Canonically promoted assertions: **0**
- Requested pilot coverage: **0/25–50 cards**
- Product completeness claim: **none**

No machine-readable import report exists because creating one would falsely represent an
import session that never passed acquisition. The review finding is this document and the
current-state updates recording the evidence block.

## Lessons for a complete MB2 dataset

A future attempt must first obtain explicit network access or receive a legally usable
provider export. It must capture the exact response bytes before transformation, retain
request locator and acquisition time, record provider publication/version metadata and
terms, and select a bounded sample only after inspecting the snapshot. Existing derived
extracts may corroborate results but must not be relabeled as raw provider evidence.

## Exact reproduction instructions

From the repository root:

```bash
# Confirm that only the prior bounded MB2 evidence and title fragment are retained.
find data/raw/magic/mystery_booster_2 data/sources/magic -type f | sort

# Re-run repository validation; this phase intentionally adds no runtime tests.
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'

# When outbound access and terms review are available, retrieve the provider response
# with a declared User-Agent into a temporary file, compute SHA-256, and ingest those
# exact bytes through the Phase 82 acquisition command. Do not hand-edit the response.
```

The future operator must record the actual retrieval command, response headers or provider
version metadata, SHA-256 identity, license review, and attribution in the resulting source
inventory. Until then, implementation remains stopped.
