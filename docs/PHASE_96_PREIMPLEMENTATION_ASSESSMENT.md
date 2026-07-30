# Phase 96 — Mystery Booster 2 Canonical Product Repository v1

> **Status: Blocked at the pre-implementation evidence and contract gate — 2026-07-30**  
> **Architecture:** v12 unchanged

## Architecture assessment

The Phase 95 merge (`be952c1`) is the repository baseline. Phase 96 fits Architecture
v12 as a canonical-data population milestone: reviewed evidence would pass through
acquisition, normalization, review, and promotion before becoming repository truth.
Mystery Booster 2 must remain data interpreted by generic consumers; no query,
analytics, semantic, reasoning, AI-adapter, simulation, or product-specific runtime
contract needs to change.

The Canonical Repository remains the sole source of truth. Architecture v12 remains
frozen and unchanged.

## Mandatory stop finding

The checkout contains no content-complete reviewed MB2 source. Its retained evidence
supports only product identity and four bounded Card/Printing memberships. The only
checked-in structured-provider fixture is the synthetic ten-card `TST` fixture recorded
by Phase 90; it contains no MB2 records. Network acquisition is also unavailable in
this environment (the configured proxy rejects provider requests).

Consequently a production-quality import cannot truthfully establish complete Cards,
Printings, treatments, finishes, rarities, languages, packaging, or pack topology.
Collector identities, expected counts, slot pools, sheet membership, weights,
replacement behavior, and packaging composition cannot be reconstructed from memory.
Doing so would violate the constitutional rules that unknown is preferable to
incorrect and that every canonical fact must be evidence-backed.

There is also a contract-level mismatch in the requested deliverable that must be
resolved by the Project Architect before implementation:

* the frozen canonical model represents set and language as Printing attributes, not
  standalone Set and Language entities;
* the v2 PackDefinition requires at least one Slot, and every Slot requires a real,
  non-empty Print Sheet, so an explicitly unknown pack topology cannot be serialized
  as a PackDefinition without inventing a sheet and selection semantics; and
* lifecycle status is defined for Product, while the request requires lifecycle,
  validation state, confidence, dataset identity, and timestamps on every entity where
  applicable. Those fields are not a uniform requirement of the frozen entity schemas.

Silently placing substitutes in free-form metadata would not satisfy the canonical
contracts. Adding Set/Language entities or relaxing PackDefinition/Slot/Sheet contracts
would redesign frozen schemas, which Phase 96 explicitly prohibits. This is therefore
the genuine architectural-defect stop condition identified by the milestone.

## Preserved canonical inventory

No canonical record is added, rewritten, or directly populated by this assessment.
The repository continues to contain:

* one foundation Product (`mystery_booster_2`);
* four evidence-bounded MB2 Printings (collector numbers 1–4) and their four Cards;
* zero MB2 ProductVersions, PackDefinitions, PackSlots, or PrintSheets; and
* explicit unknown collation, completeness, treatment, finish, and packaging facts.

The other eleven Cards and Printings are historical non-MB2 repository records and
must not be counted as MB2 content.

## Resume criteria

Implementation may resume only when both gates are satisfied:

1. a terms-compliant, immutable, content-complete MB2 source is supplied or acquired,
   registered, independently reviewed, and assigned field-level evidence policy; and
2. the Project Architect clarifies whether “Sets” and “Languages” mean Printing
   attributes and which existing representation is authorized for an unknown pack
   topology and uniform entity governance fields, or separately authorizes a generic
   schema milestone.

After those decisions, the import must use the existing acquisition/review/promotion
pipeline, preserve source bytes and assertions, validate deterministic identifiers and
the complete relationship graph, run twice against disposable repositories, and only
then promote reviewed records. Simulation, expected value, and pack generation remain
out of scope.

