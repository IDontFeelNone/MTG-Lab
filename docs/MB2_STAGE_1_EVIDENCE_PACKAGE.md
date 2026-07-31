# Mystery Booster 2 Stage 1 Evidence Package

> **Phase 96B — implemented 2026-07-31.** Architecture v12 and frozen canonical
> contracts are unchanged. Promotion remains subject to maintainer review and green CI.

## Baseline and workflow

The implementation baseline includes merged Phase 96A commit `b9a34ac`. This milestone
uses the existing source capture → dataset registration → acquisition → normalization →
candidate validation → independent review → controlled promotion path. It never writes
directly to a canonical Product. The retained package is
`data/evidence-packages/magic/mb2-stage-1/`; its import boundary verifies the package and
delegates the only canonical operation to `ProductPromotionService`.

## Evidence inventory and terms

| Source | Artifact | SHA-256 | Capture | Supported fields |
| --- | --- | --- | --- | --- |
| `wizards-mystery-booster-2-product-overview` (official; Wizards of the Coast) | `artifacts/official-product-page-title.html`, 238 bytes, HTML | `6a80292f12183541168e5994e9d136b3cf8d4992f4c51eae0bcb0af83a6d3fac` | `2026-07-29T00:00:00Z` | Product name, product identity, official product association |

The package retains only a narrow factual title capture for research, verification, and
provenance. It asserts no license to redistribute broader page content, preserves Wizards
attribution, and requires a new terms review before any expanded capture. The source record
contains origin, type, publisher, timestamp, byte count, hash, terms assessment, review
status, review locator, and its supported and unsupported fields.

## Supported facts, explicit unknowns, and bounded completeness

Stage 1 is **complete only for the official product identity fields visible in this
artifact**: the official name is “Mystery Booster 2,” and the page associates that product
with Wizards of the Coast's Magic site. The existing foundation Product is confirmed.

The capture does **not** establish a product code, release date, packaging type, pack
count, contents, full packaging composition, cards, Printings, collation, Slots, or sheets.
Those values remain explicitly listed as unknown in the package manifest. Pack topology is
unresolved; cards and Printings are out of scope. This claim is not complete MB2 coverage.
No ProductVersion is created because no concrete version is established.

## Provenance, validation, review, and promotion

The normalized Product candidate records provenance for every serialized field. `name`
links to the official Open Graph title and retained hash. Required frozen-contract fields
that the title does not establish are explicitly classified as internal preservation of the
existing reviewed foundation record; they are not attributed to the page. Candidate and
artifact identifiers derive deterministically from the source hash.

The acquisition operator is `phase-65-acquisition-operator`; the distinct reviewer is
`phase-96b-independent-reviewer`. The reviewer approved only the three supported identity
claims after checking integrity, source identity, terms posture, scope, provenance, and
unknown handling. Cross-artifact validation passed. Controlled promotion confirms the
existing `mystery_booster_2` Product and writes an immutable, deterministic promotion audit;
it creates no duplicate Product.

## Counts and deterministic replay

| Record type | Count |
| --- | ---: |
| Product confirmed | 1 |
| source / dataset / candidate / validation / promotion audit | 1 each |
| ProductVersion / PackDefinition / Slot / PrintSheet | 0 each |

Two independent disposable-repository imports produce identical source hashes, candidate
IDs, canonical IDs, promoted Product bytes, audit bytes, and result reports. Repeating an
import in one repository produces one retained source artifact and one audit record.

## Unresolved questions and Stage 2 entry criteria

Product code, release context/date, packaging format and quantity, full contents, topology,
and all card/printing facts remain unresolved. Stage 2 may begin only with an immutable,
terms-reviewed official card list or independently reviewed structured dataset whose MB2
scope and count are explicit. It must retain exact bytes and hashes, source and dataset
metadata, record-level provenance, conflict and completeness reports, independent review,
deterministic two-run validation, and controlled promotion. It must not infer missing card,
Printing, treatment, packaging, slot, collation, or sheet facts.
