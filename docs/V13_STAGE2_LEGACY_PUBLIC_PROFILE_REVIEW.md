# V13 Stage 2 — Legacy/Public Snapshot Profile Review

Status: owner-authorized **review/design/inventory complete, pending PM review**.
Baseline: `83e832e3105ddb1c65252b5946387651c49685e4` (merged PR #176).
Architecture v13 is active; Decision 017 is Accepted. No runtime profile,
production snapshot, source-policy decision or admission is created here.

## Recommendation and stopping boundary

**Stage 3 — Legacy/Public Catalog Snapshot Profile: NOT READY.** A faithful
read-only compatibility contract is technically describable without new identities,
query-hash redefinition, rewriting state or writer changes. It cannot yet be
presented as a permission-certified, dependency-complete production release.

Recommend the narrower prerequisite **Legacy/Public Profile Permission and Closure
Contract**, **NOT AUTHORIZED**. It must decide exact operation/field/component
permission and evidence/CI placement, plus whether the target is entity queries,
full audit APIs or historical admission validation. It must explicitly preserve
legacy incompleteness. This is not a request to implement a profile or contact
providers now. Decision 017 needs no correction based on this review.

## Reproducible package, without another corpus

[`reference-reviews/v13-stage2-legacy-public-profile/`](../reference-reviews/v13-stage2-legacy-public-profile/)
contains census, path/hash inventory, layer classifications, consumer dependencies,
semantic dependency sets and preservation bindings. Its relative-path manifest
binds exact review bytes. These are **review metadata, not a snapshot manifest,
release receipt, admission decision or permission grant**.

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/review_legacy_catalog.py --root . --baseline-revision 83e832e3105ddb1c65252b5946387651c49685e4`

The inspector reads only tracked selected inputs and prints metadata to stdout;
it does not write files, attach anything, acquire data or invoke a writer. It
rejects untracked/symlinked canonical inputs before reading their contents. Its
baseline argument is the review/code anchor, not an assertion that arbitrary
current bytes equal that commit: actual file hashes and canonical-tree digest
identify the inspected state. Never silently refresh this retained baseline after
an admission. A changed catalog needs a separately identified observation.

The inventory binds **1,778 files** across reviewed public data, existing MB2
reference/policy metadata and historical fixtures. It contains no copied source
values or raw provider corpus. Individual collection files, their hashes and
contents are excluded; only the family boundary is classified. Existing private
files are neither discovered nor included. Hash/path references do not themselves
clear future redistribution of the bytes referenced.

Tests verify the retained historical canonical census against the existing frozen
historical fixture. They separately check the actual current inspector/query
output dynamically. Thus a future writer-produced expansion can legitimately
change current counts without rewriting the Stage 2 baseline or hiding a failure
behind old data. The existing full hosted expanded-writer gate remains intact.

## Exact census: representations are not interchangeable

| Kind | Typed per-game entities | Promoted state | Explicit both-root query |
| --- | ---: | ---: | ---: |
| Card | 15 | 384 | **399** |
| Printing | 15 | 913 | **928** |
| Identifier | 0 | 235 | **235** |
| Finish | 0 | 2 | **2** |
| Game | 1 | 0 | **1** |
| Product | 1 | 0 | **1** |
| ProductVersion | 0 | 0 | 0 |
| PackDefinition | 0 | 0 | 0 |
| Slot | 0 | 0 | 0 |
| PrintSheet | 0 | 0 | 0 |
| Treatment | 0 | 0 | 0 |
| Rarity | 0 | 0 | 0 |
| SourceRecord | 8 | 0 | Not a query entity |

There are **1,534 promoted records**, **1,566 query entities**, and **52 canonical
files (46 JSON plus six .gitkeep markers)**. SourceRecords comprise seven global
and one Product-local record. The Product subtree's seven JSON files are one
Product, three metadata/reference sidecars, one SourceRecord and two acquisition
manifests; they are not seven Products. The foundation Product has zero slots.
No pack distribution, sheet weights, collation or complete-set coverage follows.

Typed Cards/Printings/Product and SourceRecords use v1 contracts. Game and
promotion-state rows lack record-level schema_version; the latter are interpreted
through their original promotion-specific contracts/audits, not relabeled v3.
Schema versions for every inventoried family are in layer-inventory.json.

### Typed tree versus promoted state

Neither is a superset. Exact typed/state ID overlap is **zero Cards and zero
Printings**; there is one shared name, which is not an approved identity mapping.
Do not merge it, select one identity by name, or assign physical ownership.

`CanonicalRepository` reads the typed tree. `CanonicalQueryEngine` emits typed
entities first, then `canonical/state.json`, then optional
`canonical/knowledge/state.json`, skipping state entries that collide with typed
(entity_type, ID). The skip set does not also deduplicate the two state files.
The optional knowledge state is currently **absent**; future presence/conflicts
must be explicitly bound or rejected. `data/knowledge/facts/` is a different store.

State is an authoritative retained admission representation and a promotion
projection at the same time. Its legacy format is technical debt, not permission
to treat its records as pending or discardable. Preserve both representations
and their precedence, bytes, identities and original evidence. Materializing state
as typed files would introduce different schema/lineage semantics; it is not a
location-only Stage 3 step and is excluded.

### Identity and completeness limitations

- No promoted Printing→Card or Identifier→Printing orphans were found.
- Two admitted Finishes are foil/nonfoil. Thirty historical Phase 136 Printings
  reference additional labels: signed=21 and etched=9. These remain documented
  historical gaps, not newly manufactured Finish entities.
- Typed Printings contain no finish field; four carry Product membership metadata.
- State languages retain English=896, French=4, Japanese=4, Spanish=3 and Quenya=6;
  typed language is en=15. Preserve source labels and established equivalence only.
- The 235 aliases span 15 namespaces. A shared card-back identifier across 21
  Printings is legitimate nonunique namespace behavior, not a merge instruction.
- `TypedCanonicalProjectionEngine.validate()` can verify original flat admissions
  while reporting `typed_materialization_ready=false`; `project()` does not turn
  whole-row evidence into v3 field assertions. No taxonomy repair is authorized.

## Three different identities and an explicit-root caveat

Canonical pre-state remains:
`881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077`.
It hashes every file under `data/canonical` with relative path and SHA-256,
including unused SourceRecords, sidecars and empty markers. It is not merely the
hash of state.json.

Explicit BOTH-root query identity:
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`.
It hashes result envelopes including provenance and audit-byte references. The
outer v13 release/content/source/validation identities remain separate again.

The bare QueryEngine constructor currently infers data_root from
`games_root.parents[2]`, which resolves to the repository rather than its data
folder for this layout. It consequently sees only 32 typed entities and yields
`sha256:e580c987f4e7cae0c0a69e22dc025e468ceacef078a4ff907935c1d54998fa6e`.
This is a measured entry-point difference, not two interchangeable catalog
snapshots. Stage 1 factories already pass **both explicit roots**. Future parity
must name that target; fixing the legacy constructor default is a separate
compatibility decision and is not done here.

## Required closure: distinguish entities from readable dependencies

`semantic-dependencies.json` binds the exact relative paths/hashes for these
statically derived sets. No real-data bundle or isolated provider copy was made.

| Required behavior | Bound files | Meaning |
| --- | ---: | --- |
| Current entity snapshot/provenance output | 40 | 32 typed entities + five referenced global SourceRecords + state + two entity-referenced audits |
| Full query API read surface | 68 | Same typed/source/state inputs + all 30 audit JSON files |
| Full query API plus unchanged canonical pre-state | 82 | All 52 canonical bytes + all 30 audits |
| Additional original-admission validation dependencies | 17 | Twelve Phase115/116 review receipts, original candidate payload and source lineage, three Phase135 evidence files |

The first set describes output dependencies, **not** the literal reader scan:
current query construction scans all audit JSON. Only two audits contribute to
entity provenance (1,000 Phase119 entities and 534 Phase136 entities). The other
28 remain observable through lazy promotion history and global rejection/failure
queries. Omitting them may preserve today's entity snapshot, but cannot claim full
API parity. A future profile must either bind the independently classified audit
context or declare a narrower capability. Do not silently put every historical
audit into canonical entity content.

Admission validation also requires original receipts/source projections; basic
query/collection does not read the underlying raw provider archives. Provenance
references and physical evidence verification are distinct. A technical read-set
is not proof that the complete evidentiary or permission chain is closed.

## Architectural layer classification

| Family | Primary role | Scope and exclusions |
| --- | --- | --- |
| Typed domain entities + promoted state | CANONICAL SNAPSHOT CONTENT | Exact mixed representations, no rematerialization or name merging |
| Game metadata, sidecars, placeholders, profile/schema bindings | CANONICAL SNAPSHOT CONTROL/METADATA | Some participate in old pre-state hashing despite not being query entities |
| SourceRecords, sources/raw/evidence/evidence-packages/production evidence, reference packets | SOURCE EVIDENCE PLANE | Independently permissioned dependencies; no blanket raw-corpus inclusion |
| data/audit; retained reviews and execution histories | AUDIT / PROVENANCE HISTORY | Historical approval is not reusable execution authority; pending proposals stay pending |
| production run summaries, processed indexes, local compact SQLite | GENERATED PERSISTENCE / INDEX | Rebuildable only from exact permitted retained inputs; no authoritative SQL runtime exists |
| market observations/imports/mappings | TEMPORAL MARKET EVIDENCE | 956 observation files, two import reports; mapping roots supported but no separate tracked mapping files here |
| market acquisition source/receipts | SOURCE EVIDENCE PLANE | Six files; dual use for market extraction and current mechanical evidence, without becoming catalog entities |
| knowledge/facts, dossiers, roles, comparisons, Product/Decision outputs | DERIVED CARD / PRODUCT / DECISION INTELLIGENCE | 140 reviewed append-only knowledge assertions are not all inferred facts or disposable cache. Source-backed assertion evidence remains independently governed; none enter basic catalog query today |
| collections/imports/assessments/storage/holdings | PERSONAL / USER DATA | Never part of shared catalog or retained per-file Stage2 inventory; fictional demonstrations stay separate |
| review pilots, validation fixtures, explicit historical fixtures | HISTORICAL TEST / REPLAY FIXTURE | Preserve original scope, bytes and expected identities; no production eligibility inferred |
| intermediate/pending proposals and unsupported future domains | UNSUPPORTED / UNRESOLVED | No promotion by directory location or architecture approval |

The classifications are semantic: e.g. SourceRecords are physically inside the
canonical tree, market source bytes also support MCI, and knowledge assertions
have their own reviewed fact authority. These justified cross-domain relationships
are retained without turning every file in data/ into a catalog component.

`src/repository/rules.py` is a PrintSheet/Slot/structured-product repository.
Currently it loads zero sheets/slots. It is not comprehensive gameplay rules,
Oracle reasoning, timing or interaction execution. Any future rules corpus needs
its own versioned, permissioned module; no current gameplay-rule entities were found.

## Consumer migration contract

The machine-readable consumer map records roots, flags, identities, existing
source paths, explicit-root seams, difficulty and blockers for each consumer.

| Consumer | Actual dependence / future boundary |
| --- | --- |
| CanonicalRepository / Card loaders | Typed game tree, referenced SourceRecords; separate archived-evidence API. Cannot alone represent the promoted population |
| CanonicalQueryEngine | Both explicit roots; typed + promoted/optional knowledge state + audit provenance; unchanged query identity |
| Semantic query / analytics | Existing CanonicalQueryService and analytics consume QuerySnapshot envelopes; optional market repository remains explicit |
| Collection resolver | Query entities/aliases/relationships plus separate user input; records query identity. No ownership or physical Printing upgrade |
| Typed projection | State + exact original admission audits/receipts; validation differs from materialization. Do not migrate writer or synthesize field assertions |
| Mechanical Card Intelligence | Query + independently selected Scryfall market-acquisition-evidence-v1 source; missing, unsupported and corrupt evidence remain distinct |
| Other Card Intelligence | Append-only KnowledgeRepository, reviews/dossiers and explicit catalog/market/as-of scopes; derived contexts are not catalog facts |
| Product Intelligence | Explicit product/content/offer/valuation contracts; foundation Product is catalog content, CC2 evidence/readiness is separate and incomplete |
| Market Intelligence | Temporal observations/history + provider mappings/as-of + catalog references; no prices or histories folded into core |
| Decision Intelligence | Storage-independent domain/request/policy envelopes; deterministic decisions do not admit facts |
| Reasoning Context | Injected validated semantic/decision envelopes, provenance and omissions; no conversation memory or AI transport authority |
| Rules repository | Typed sheets/slots/product graph only; gameplay semantics unsupported |
| AutomaticCanonicalUpdate | Analysis only: repository-scoped state/pre-state, evidence/receipts, review/readiness, trusted owner boundary, writer delta/checkpoints/publication. All unchanged |

## Conditional minimum profile and permissions

A future faithful profile would pin original mixed canonical bytes, explicit game
scope, exact both-root mapping, typed-first precedence, alias namespaces and
language/finish semantics, plus separately classified SourceRecord/audit and
admission-validation references. Absent optional state is a pinned fact. It must
support original IDs and query hash without flattening schemas or changing old
expected outputs. Existing legacy/public handles only check directories; they do
not already provide immutable file/dependency certification.

The Product foundation and relationships must remain if full current query/API
parity is promised. A separate Product Intelligence module may add independently
reviewed content/offer evidence later; it cannot retroactively turn zero slots
into complete product contents. This review authorizes no module composition.

Exclude temporal prices/history, personal files, pending candidates (including
MB2 810 and nine holds), reviewed/derived intelligence, AI contexts, credentials,
caches/backups, unrelated raw provider archives and unselected audit histories.
Full audit APIs need an explicitly bound audit context; it is not canonical
entity content. Full provenance verification needs its exact permitted evidence
plane. Do not hide those dependencies in unclassified metadata blobs.

Existing source-policy evidence is reused, not researched anew:

- [PR174 readiness analysis](MB2_810_PRODUCTION_READINESS.md) and
  [permission follow-up](MB2_810_SOURCE_PERMISSION_FOLLOW_UP.md).
- [Retained policy review](../reference-reviews/mb2-810-source-policy/2026-10-14/policy-review.json).
- [Accepted security/permission boundaries](EXTERNAL_CARD_DATA_PLANE_SECURITY.md).

| Component/status | Evidence classification for a new operation |
| --- | --- |
| Newly authored inspection code, review metadata, fictional fixtures | public-safe / project-authored; no provider corpus copied |
| Original legacy entities, identifiers, source-derived names/mechanical labels | previously public historical material; complete future-use permission NOT established |
| Source/audit/receipt dependencies containing original provider values | source-policy NOT established for repackaging/private-service/public-service scopes merely from historical publication |
| MTGJSON-controlled layer | narrower MIT grant/notices retained; does not clear Wizards, Scryfall, marketplace or other upstream content |
| Personal collection files | not applicable to catalog; excluded, separately governed |
| Future rules/AI export/production activation | requires separate review; not implemented or authorized |

The retained MB2 evidence is not a new field-by-field ruling on every old catalog
source. It establishes that no blanket permission can be inherited. An exact
legacy-operation permission ledger is still missing. API access, a repository
merge, private storage, hashes or old license labels are neither permission nor
prohibition. An HTTP403 is no rights decision. No clearance registry is changed.

## Feasibility proof and next acceptance boundary

New fictional tests use the existing Stage1 attachment and legacy/public seam to
exercise typed+state precedence, stable aliases/relationships, relocation,
independently observable audit context and query-hash changes. They prove that
knowledge/facts, market and personal planes need not become catalog facts. A
mixed legacy fixture correctly fails the fictional immutable snapshot profile.
No real catalog was attached as a v13 snapshot or copied into a new release.

The narrower prerequisite must deliver: operation/field/component evidence and
notices; exact approved catalog/audit/evidence closure and allowed placements;
capability semantics for historical Finish gaps and optional knowledge state;
explicit-root parity target; and a source-safe public/private CI plan preserving
old replay hashes. If those cannot be established, later implementation must
remain fictional-only or blocked. No new identity model, writer change, state
rewrite or Tier0 architecture correction is currently justified.

Only after separate owner authorization may a later implementation introduce a
generic legacy representation contract, immutable manifest verification and
read-only attachment. Acceptance would require full entity/value/provenance/query
and collection parity, distinct outer/query/pre-state identities, path and drift
failures, no fallback/network/writer, historical replay preservation and explicit
incomplete capabilities. None of that implementation is begun by Stage2.
