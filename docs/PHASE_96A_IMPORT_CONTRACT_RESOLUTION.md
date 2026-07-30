# Phase 96A — Mystery Booster 2 Import Contract Resolution

> **Status: Proposed architecture-compatible clarification — 2026-07-30**  
> **Decision:** no Architecture v12 or frozen canonical-contract change  
> **Baseline:** merged Phase 96 blocker assessment (`7880599`, containing `bc328c7`)

## Context and decision

Phase 96 correctly stopped rather than manufacturing a complete Mystery Booster 2
dataset. This review resolves the contract questions while preserving that evidence
gate. The smallest truthful resolution is:

1. keep set and language as Printing attributes;
2. retain the known foundation Product while omitting ProductVersion,
   PackDefinition, Slot, and PrintSheet records until evidence supports each record;
3. keep governance information in the existing canonical assertions/provenance,
   candidate/review/promotion records, dataset registry, and immutable acquisition
   records instead of copying every concern onto every domain entity; and
4. resume bounded population only through the existing acquisition, independent
   review, validation, and promotion boundaries.

Omission of a PackDefinition is an epistemic statement: **canonical pack composition
has not been established**. It is not a claim that the product has no packs. No empty
sheet, placeholder slot, free-form metadata flag, or MB2-specific runtime branch may
stand in for missing evidence.

This decision clarifies how existing contracts compose. It changes no Tier 0 entity,
schema, dependency direction, writer, or consumer contract and requires no data
migration. Project Architect approval is therefore not required before implementing
later evidence-backed population. Normal review and promotion approval remain
mandatory. If a future requirement demands a canonical object representing unresolved
topology, that is a separate generic frozen-contract proposal and requires explicit
Project Architect approval before implementation.

## Blocker-by-blocker resolution

### 1. Set and language — prompt-assumption error; no change

Architecture v12 defines a Card as game-level identity and a Printing as its issued
realization. Set and language characterize that realization. The v3 Printing contract
requires `set_id` and `language`, while the typed Printing exposes the same fields.
Nothing in Tier 0 requires standalone Set or Language entities.

The earlier request assumed entity boundaries the architecture does not have. Existing
Printing attributes satisfy the approved model. Adding standalone entities solely to
match that wording would add identity, referential, migration, and promotion questions
without establishing additional truth. MB2 imports must use Printing attributes and
must not introduce Set or Language entities.

### 2. Unknown pack topology — representational limitation, not a defect for import

The alternatives are resolved as follows:

| Option | Resolution | Reason |
| --- | --- | --- |
| Omit PackDefinition until evidence exists | **Selected** | A foundation Product may exist without versions or topology. It makes no false composition claim and changes no contract. |
| Add draft/incomplete PackDefinition state | Rejected for Phase 96A | It changes a frozen domain contract and risks making a structurally incomplete object appear canonical. |
| Use a separate evidence-stage candidate | Already available, when evidence exists | Parsed artifacts, normalized candidates, assertions, and v3 partial-collation records may retain provisional or unresolved claims, but are not a substitute for a canonical PackDefinition. |
| Permit unresolved canonical PackDefinition topology | Deferred | This would relax the non-empty PackDefinition/Slot/PrintSheet graph and requires a generic architecture proposal plus Project Architect approval. No current import need justifies it. |

The current contract intentionally means that a canonical PackDefinition is a real,
referentially valid composition definition. It cannot express an unresolved definition,
but the repository can truthfully express the known product without creating one.
Evidence-stage `partial-collation` records can distinguish unknown, provisional,
conflicting, and unresolved claims and fail closed for simulation. They remain
non-canonical evidence; absence of canonical topology remains visible through ordinary
relationship and query results.

### 3. Cross-cutting governance metadata — prompt-assumption error; no change

The exact implemented allocation is:

| Canonical entity contract | Provenance | Confidence | Validation state | Lifecycle state | Dataset identity | Timestamps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Product v2 | required field-level provenance | no entity field | no entity field | required (`foundation`, `draft`, `validated`, `deprecated`) | no entity field | no entity field |
| ProductVersion v2 | required field-level provenance | no entity field | no entity field | no entity field | no entity field | no entity field |
| PackDefinition v2 | required field-level provenance | no entity field | no entity field | no entity field | no entity field | no entity field |
| Slot v2 | required field-level provenance | no entity field | no entity field | no entity field | no entity field | no entity field |
| PrintSheet v2 | required field-level provenance | no entity field | no entity field | no entity field | no entity field | no entity field |
| Card v3 | required source assertions covering promoted facts | per assertion | no entity field | per assertion (`verification_status`, `lifecycle_status`) | no entity field | per assertion retrieval and optional publication timestamps |
| Printing v3 | required source assertions covering promoted facts | per assertion | no entity field | per assertion (`verification_status`, `lifecycle_status`) | no entity field | per assertion retrieval and optional publication timestamps |

This asymmetry is deliberate ownership, not missing data:

* domain entities contain domain identity and facts; Product alone owns product
  completeness lifecycle;
* v1/v2 field provenance and v3 assertions identify evidence for canonical fields;
* confidence belongs to a claim/assertion, never to an entire heterogeneous entity;
* candidate `validation_state`, field provenance, and confidence belong to the
  normalized-candidate envelope before promotion;
* structural, referential, domain, and statistical validation results belong to the
  validation boundary, not to mutable flags on canonical facts;
* dataset identity and acquisition/publication timestamps belong to dataset registry,
  raw snapshot, source, session, and evidence records;
* review decisions and immutable decision timestamps belong to review packages and
  promotion audits.

Canonical files are version-controlled, so Git history and promotion audits preserve
change history without duplicating mutable `created_at`/`updated_at` fields. Free-form
`metadata` must not be used to bypass these owners. A uniform canonical envelope might
be considered only as a generic, separately approved migration; Architecture v12 does
not currently require one.

### 4. Evidence completeness — genuine external-input blocker; no contract change

The repository still supports only one MB2 foundation Product and four bounded
Card/Printing records. It does not include a reviewed, content-complete source for the
full card list, packaging, treatments, topology, collation, or sheets. This is an
evidence deficit, not a schema defect. Phase 96 population remains blocked to the
extent a requested fact lacks the package below.

## Minimum resumable evidence package

An intake may be JSON, CSV, a ZIP containing JSON/CSV accepted by the external dataset
ingestion boundary, or a repository evidence bundle containing stable local captures
plus manifests. Human-readable PDF, image, or HTML captures are acceptable evidence
artifacts only when archived by the evidence workflow with deterministic extraction;
they are not direct canonical import files.

Every package must provide:

* the exact acquired bytes in an immutable/content-addressed location; media type,
  byte length, SHA-256, acquisition timestamp, publication timestamp when known, and
  parent/version lineage;
* provider, source ID, source locator, dataset identity/version, access method, and a
  retained Source Record; redirects or mutable URLs alone are insufficient;
* recorded license or terms-of-use reference, attribution, redistribution/storage
  constraints, and confirmation that acquisition and repository retention comply;
* deterministic parsing and normalization versions, stable source-record locators,
  and field-level provenance from every candidate field to source ID, raw hash,
  parsed record, and transformation;
* an independent reviewer who did not merely perform the acquisition, a completeness
  report, conflict report, validation findings, explicit accept/reject/unresolved
  decisions, and an immutable promotion audit;
* confidence on each candidate/assertion under the reviewed provider policy, not a
  blanket confidence inferred from provider reputation.

### Evidence classes and conflicts

Claims are classified, not sources in the abstract:

1. **Official facts** are direct first-party statements or artifacts. They receive
   the `official` evidence class but still require identity, capture, provenance, and
   review.
2. **Independently corroborated facts** agree across independent authoritative or
   verified sources. Each assertion and source remains separate; agreement strengthens
   review but does not erase lineage.
3. **Community observations** are attributable direct observations. They may support
   observation or `verified_community`/`direct_observation` assertions after review,
   but do not automatically establish completeness or manufacturer intent.
4. **Statistical inference** is a derived or inferred claim with declared inputs,
   method, sample bounds, uncertainty, and reproducibility. It never masquerades as an
   official fact or silently supplies weights.
5. **Unresolved information** remains omitted from concrete canonical fields or is
   retained in an evidence-stage unknown/conflicting/unresolved knowledge value. It
   must not receive an empty collection, zero, default replacement behavior, or
   free-form placeholder.

Conflicting eligible claims are preserved and reported. Equal-priority,
equal-confidence disagreement has no automatic winner. A reviewer may reject,
supersede with explicit links, request more evidence, or leave the field unresolved;
normalization may not resolve the conflict. A package may promote a clearly bounded
subset only when it declares that subset, passes its own completeness gate, and makes
no whole-product completeness claim.

## Staged MB2 acquisition and promotion plan

Stages are cumulative, but independently evidenced bounded facts need not wait for
unknown later topology. Each canonical promotion remains atomic for its declared
scope.

| Stage | Required source quality | Expected imported entities | Allowable unknowns | Validation gate | Promotion gate |
| --- | --- | --- | --- | --- | --- |
| 1 — Official product identity and packaging evidence | Immutable first-party product page, packaging image/document, or equivalent official record; reviewed terms and hash | Product identity updates and, only if evidenced, ProductVersion/components | Card list, treatments, contents, topology, quantities not shown by evidence | Source integrity, Product schema, stable IDs, field coverage, no interpretation beyond visible claims | Independent review approves each identity/packaging field; foundation lifecycle remains unless completeness rules are met |
| 2 — Official or reviewed card-list evidence | Content-complete official list or independently reviewed structured dataset with explicit MB2 scope and count | Cards and Printings supported by the list | Optional Card/Printing fields not supplied; topology and collation | Declared-count reconciliation, duplicate/collector identity checks, Card→Printing graph, deterministic two-run report | Every promoted field has evidence; unresolved/conflicting records are rejected or retained as candidates; complete-list claim must pass completeness review |
| 3 — Printing attributes and treatments | Official gallery/checklist or independently corroborated, reviewed record-level evidence | Printing fields and referenced generic rarity/treatment/finish values already authorized by contract | Attributes absent from sources; pack membership and weights | Vocabulary mapping, set/language/collector uniqueness, treatment/finish evidence, source resolution | Field-level decisions and policy confidence pass; no Oracle-to-printing fill or provider-only guess |
| 4 — Pack-slot and collation observations | Immutable attributable opening/packaging observations with manifests, verification, and sufficient coverage for each bounded claim | Evidence-stage partial-collation/assertions; canonical ProductVersion/PackDefinition/Slot/PrintSheet only when concrete graph facts are established | Unsampled variants, weights, replacement, correlation, order, and manufacturer rules | Observation integrity, sample boundaries, contradiction report, all simulation-required unknowns visible | Promote only fully supported concrete relationships; otherwise retain non-canonical candidate/observation and omit canonical topology |
| 5 — Sheet reconstruction and statistical inference | Reviewed observations plus reproducible method, versioned inputs, sample size, uncertainty, and independent analysis | Derived/inferred assertions and candidates; concrete PrintSheets only with approved evidentiary sufficiency | Physical sheet layout, exact weights, conditionality, correlation, and sequencing not established by analysis | Deterministic reproduction, statistical review, conflict comparison, fail-closed consumer check | Human approval explicitly distinguishes inference from observation; no inferred exact value promoted as official fact |
| 6 — Validation and canonical promotion | Complete retained packages from applicable earlier stages and signed-off review package | Only reviewed Product, ProductVersion, Card, Printing, PackDefinition, Slot, and PrintSheet records supported by scope | Any fact outside declared promotion scope remains unknown/absent; simulation inputs may remain unresolved | Schema, provenance, source/hash, referential, domain, completeness, conflict, query, analytics, idempotence, and prospective-graph checks | Authorized reviewer approves immutable audit; atomic promotion succeeds twice identically in disposable repositories before the real single-writer promotion |

## Exact criteria for resuming Phase 96

Phase 96 may resume for a **declared bounded scope** only when all of the following are
true:

1. its source format is supported or a separately reviewed deterministic parser is
   available;
2. source bytes, Source Records, terms/license record, identifiers, timestamps, and
   SHA-256 identities are retained and validate;
3. the scope and completeness claim are explicit (for a whole-card-list import, the
   source must be content-complete; a bounded wave must not claim completeness);
4. parsing/normalization is deterministic and every candidate field has resolvable
   provenance, reviewed classification, and confidence;
5. an independent reviewer has dispositioned conflicts, missing data, and unsupported
   fields without defaults or placeholders;
6. the candidate/review package passes structural, referential, domain, source,
   integrity, completeness-for-scope, and prospective canonical-graph validation;
7. two clean disposable-repository runs produce identical IDs, reports, snapshots,
   queries, and analytics for the declared scope;
8. the promotion authority approves the package and the existing promotion engine can
   write it atomically with an immutable audit; and
9. PackDefinition, Slot, and PrintSheet population is omitted unless evidence supports
   a complete concrete subgraph; all consumers continue to treat missing topology as
   not established and fail closed where topology is required.

No additional Architect approval is required to use these unchanged contracts. A new
standalone Set/Language entity, entity-wide governance envelope, or unresolved
canonical PackDefinition would change frozen contracts and **does** require explicit
Project Architect approval in a future milestone.

## Migration, compatibility, and tests

There is no migration: existing bytes and the one Product/four Printing inventory are
unchanged. Legacy v1, product v2, and Card/Printing v3 readers and writers remain
compatible. Query and analytics behavior also remains unchanged: they report only the
canonical relationships that exist and must not reinterpret an empty relationship
result as proof of real-world nonexistence. Simulation remains unauthorized and must
fail closed on missing topology.

Phase 96A changes documentation only, so no new unit test is required. A later import
must use `unittest` and cover backward compatibility, absent-versus-unknown semantics,
canonical serialization, promotion validation, query and analytics behavior, and
deterministic repeated results.
