# Mystery Booster 2 Stage 2 reviewed card-list intake

> **Phase 97 — intake implemented; promotion blocked, 2026-07-31.** Architecture v12
> and every canonical contract remain unchanged.

## Architecture assessment and baseline

The repository baseline is merged Phase 96B commit `0c88825`. The Stage 1 package was
successfully promoted: its official title artifact is retained and its controlled audit
confirms the foundation Product. The Canonical Repository remains the only source of truth.
Stage 2 extends the acquisition/evidence boundary; only independently reviewed evidence may
eventually establish Card and Printing membership. Unsupported values remain explicitly
unknown. No MB2-specific runtime logic, topology, sheet, slot, collation, probability,
simulation, or expected-value behavior is introduced. No architectural defect requires
Project Architect approval.

## Evidence finding and imported counts

The mandatory evidence gate stopped promotion. The repository contains **no complete,
terms-compliant, immutable MB2 card-list artifact**. Stage 1 contains only an official product
title. Historical wave evidence supports four bounded memberships and the Phase 90 fixture is
synthetic and non-MB2; neither can support a complete-list claim. No network capture or
reconstruction was attempted.

| Canonical result | Count |
| --- | ---: |
| Cards imported | 0 |
| Printings imported | 0 |
| Product/PackDefinition/PackSlot/PrintSheet records imported | 0 |
| Promotion audits written | 0 |

## Required artifact and provenance envelope

Resume requires the exact missing artifact: a content-complete official MB2 card list or an
independently reviewed structured MB2 dataset whose redistribution and use have been assessed.
Supply UTF-8 JSON with top-level `dataset_id`, `product_id: "mystery_booster_2"`, non-empty
`cards`, and non-empty `printings`. Each record contains `candidate_id`, a frozen-contract
`payload`, `field_provenance`, and `explicit_unknowns`. Printing payloads must evidence
`card_id`, `set_id`, `collector_number`, and `language`; optional rarity, finish, and treatment
fields must be omitted and named unknown unless the source supports them.

The package also requires `manifest.json`, `source.json`, `dataset.json`, and `review.json`.
Together they record the immutable artifact path and SHA-256, source and dataset identifiers,
capture actor/time, licensing and terms assessments, declared Card/Printing counts, bounded
completeness, source linkage, reviewer identity/decision, and the exact approved candidate IDs.
Every payload field must have source ID and confidence. Capture and review actors must differ.

## Validation and promotion methodology

`prepare_reviewed_card_list_package` is the ready-to-consume, local-only intake interface. It
deterministically validates the hash, identifiers, counts, dataset/product scope, duplicate
Cards and Printings, collector-number uniqueness within set/language, Printing-to-Card
integrity, field provenance, explicit unknown arrays, licensing/terms assessment, independent
review coverage, and absence of topology/runtime data. It returns a stable promotion-plan ID.
It deliberately performs no write and reports `promoted: false`; after real evidence passes,
the existing reviewed Card/Printing promotion service remains the only canonical writer and
its immutable audits remain authoritative.

## Bounded completeness and unresolved fields

* **Complete for reviewed card membership:** not yet established; no qualifying list supplied.
* **Incomplete for pack composition.**
* **Unresolved for sheet reconstruction.**
* **Unresolved for slot definitions.**
* **Unresolved for collation.**
* Rarity, finish, treatments, and any collector number not present in the future source remain
  explicitly unknown; absence never becomes a guessed value.

## Stage 3 entry criteria

Stage 3 may begin only after a real Stage 2 artifact passes this interface, independent review
approves every promoted field, two disposable runs are byte-identical, controlled promotion
audits all Card/Printing writes, repository tests and CI are green, and reviewed membership is
declared complete only for the supplied scope. Stage 3 additionally requires immutable,
terms-assessed record-level evidence for each rarity, finish, or treatment; it may not infer
those attributes from names, other printings, or pack assumptions.
