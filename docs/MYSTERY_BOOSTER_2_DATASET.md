# Mystery Booster 2 Canonical Dataset v1

> **Phase 81 status: Evidence-blocked** — pre-implementation review completed
> 2026-07-30. Architecture v12 is unchanged. The complete dataset was not imported.

## Pre-implementation assessment

Phase 79, the Phase 80 v3 schemas, promotion policy, repository validation, and local
import pipeline were re-reviewed before changing canonical data. The Phase 80 work
removes the former architectural blockers: card and printing facts, assertion-level
evidence, and partial collation knowledge are now representable, and the importer can
preserve reviewed v3 assertions. No new architectural decision is required.

The required content-complete, reviewed source fixture is not present, however. The
repository contains only four bounded MB2 records. Network access to the referenced
structured providers was unavailable during this run (the environment proxy rejected
requests), and the repository's source policy prohibits reconstructing the remaining
set from memory or unverified claims. Importing a purportedly complete list would
therefore fabricate identity, completeness, and provenance. Phase 81 stops at this
data-acquisition gate.

## Current source inventory

| Source | Class | Retained scope |
| --- | --- | --- |
| Wizards MB2 product overview | Official | Product identity only |
| Wizards MB2 gallery wave 1 | Official | Membership assertions for the four bounded records |
| Scryfall MB2 wave 1 | Authoritative structured | Set, collector number, rarity, and language for the four bounded records |
| Gatherer identity wave 1 | Authoritative structured | Identity and name for the four bounded records |
| MB2 wave 1 evidence bundle | Internal reviewed bundle | Three records (collector numbers 1–3) |
| MB2 wave 2 evidence bundle | Internal reviewed bundle | One duplicate-safe continuation record (collector number 4) |

No source in the checkout claims or contains a complete MB2 card list. The archived
official HTML captures only a product-page title and cannot support card, printing,
or collation promotion.

## Canonical inventory and completeness

The canonical repository has 15 Cards and 15 Printings overall. Four Cards and four
English MB2 Printings are associated with MB2: Abzan Falconer, Academy Manufactor,
Ad Nauseam, and Adarkar Windform, collector numbers 1–4. These are historical v1
records with names and bounded printing facts; they do not contain the requested v3
rules metadata, external identifiers, assertion objects, or image references.

The machine-readable snapshot is
`data/validation/mystery_booster_2/phase_81_coverage.json`. Counts describe retained
canonical records, not a claim about the real-world complete-set size. Because no
reviewed complete source establishes the expected count, `expected_card_count` and
`expected_printing_count` remain `unknown` rather than receiving guessed values.

## Importer and reproducibility

The generic importer is local-only, validation-first, stable-JSON fingerprinted, and
supports reviewed v3 datasets. It stages a prospective graph, validates references
and collector namespaces, retains explicit assertions, reports conflicts, and applies
atomically. It was not invoked for Phase 81 because there is no complete normalized
input to validate. Consequently there is no honest byte-stability or idempotence
claim for an MB2 Phase 81 fixture.

A future import must check in a terms-compliant normalized fixture plus source records,
pin its retrieval/publication metadata, declare reviewed expected counts, run two
imports against disposable identical roots, and compare both reports and output bytes.

## Unresolved-data and collation report

All complete-set metadata beyond the four bounded v1 records remains unresolved,
including canonical identities, faces and Oracle characteristics, printing treatments,
finishes, artists, release facts, provider mappings, and licensed image references.
No assertion-class counts are reported for those legacy field-provenance records: v1
provenance is not retroactively relabeled as a v3 assertion.

Product topology, slot count and order, sheet identities, sheet completeness,
memberships, weights, replacement behavior, conditionality, correlation, and
sequencing remain unknown. There are no canonical MB2 sheets or slots. The empty
legacy `packs.json` and `slots.json` indexes are not evidence that the physical product
has empty composition. Simulation consumers must continue to fail closed; no sheets,
weights, probabilities, or replacement rules were inferred.

## Readiness

The v3 contracts are structurally ready for a future evidence-backed import. The data
is **not ready** for simulation or market analysis: simulation lacks resolved collation,
and market analysis lacks complete printing mappings. No Simulation Engine, pricing,
expected-value, trend, deck, or recommendation feature is introduced by Phase 81.

## Resume criteria

Resume only after a complete, redistributable or reproducibly normalized MB2 source
has been acquired in compliance with provider terms and independently reviewed. The
review must establish expected counts and source-to-field classifications before any
canonical promotion. GitHub Actions must be green before merge is recommended.
