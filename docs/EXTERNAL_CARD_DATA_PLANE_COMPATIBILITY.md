# Current-component compatibility map

**Status: Proposed migration map; no runtime changes.** Audit baseline
`ec8fcbf97c84d24337503c81dd1c31a31e163d44`. Difficulty is relative engineering
scope, not an estimate or implementation authorization.

| Component | Current dependency / audited entry point | Proposed dependency | Difficulty | Blocker / risk |
| --- | --- | --- | --- | --- |
| Canonical repositories/loaders | `src/repository/canonical.py`, `src/repository/cards.py`: checkout-default typed game tree; roots already injectable. `canonical_compatibility.py` directly requires name | Verified attachment exposes the same declared representation roots | Low-medium | Must retain real schema-required values; no arbitrary external path accepted as authority |
| CanonicalQueryEngine | `src/query/engine.py:CanonicalQueryEngine`: typed tree + promoted state + knowledge state + audit lineage, configurable data/games roots; query digest covers result envelopes | One selected complete snapshot handle with outer authority ID and unchanged query ID | Medium | Typed/state precedence and scope must be bound; missing roots/empty catalog cannot masquerade as valid production attachment |
| CanonicalCollectionResolver | `src/collection/intelligence.py:CanonicalCollectionResolver`: query snapshot, required Card names, exact IDs/aliases then weaker name fallback; legacy production requires unambiguous game | Catalog handle plus separate private collection revision | Medium | Preserve language/finish/identity uncertainty and old audits; no name fallback upgraded to physical Printing proof; explicitly route unscoped legacy Magic state |
| TypedCanonicalProjectionEngine | `src/projection/engine.py:validate/project`: canonical tree, real admission audits, aliases and source lineage | Attachment plus exact historical/new admission evidence; generated projection keyed by input versions | High | Validation does not mean full production flat-record v3 materialization. Whole-row evidence is not field assertions; old signed/etched Finish gaps remain visible |
| MechanicalCardIntelligence | `src/card_intelligence/mechanics.py`: Scryfall `market-acquisition-evidence-v1`, a default MB2 acquisition and exact Oracle→Card binding; source constrained under data root | Catalog handle plus independently pinned compatible mechanical-source evidence component | Medium-high | Current format is not the structured reference packet. Missing coverage, unsupported format and corruption remain distinct; no fabricated source/default mechanics |
| Other Card Intelligence | `src/card_intelligence/explanation.py` and role/contextual pilots: retained source facts and named historical cohort/profile | Explicit catalog/fact/context versions, preserving each historical pilot | Medium-high | Ten-Card/Phase136 pins are historical, not universal expanded-catalog assertions; no silent repinning, automatic reassessment or strategic rankings |
| Product Intelligence | `src/product_intelligence/models.py`, `analysis.py`, `evidence_packet.py`: pure typed fixed-content contracts, offers/valuation sources and human readiness guards | Catalog for exact components + separate product/content/offer/value evidence snapshots | Low-medium | Catalog expansion does not establish guaranteed contents, fresh prices or READY. Existing incomplete CC2 production pilot remains incomplete |
| Market Intelligence | `src/market/intelligence.py`, `query.py`, `reporting.py`: temporal observations, exact mappings/dimensions, explicit as-of; reports also read canonical state/acquisitions | Catalog handle + selected temporal market evidence/mapping history | Medium | Preserve old catalog/time bindings; do not relabel historical prices as current or manufacture fresh offers. Snapshot ID alone does not grant provider/service use |
| Decision Intelligence | `src/decision_intelligence/service.py`, `reasoning.py`: immutable request/policy/domain envelopes; snapshot union; abstention on required gaps | Domain adapters bind catalog/evidence/user snapshot IDs; core remains storage-independent | Low core / medium adapters | Admission approval, evidence READY and action recommendation remain separate. LLM cannot calculate/override deterministic choice |
| AutomaticCanonicalUpdate | `src/production_evidence/automatic_updates.py`: repository-contained data root, exact binding/revalidation, real writer/consumer acceptance, Git pre-state/delta/receipt publication | Existing writer in controlled operator staging with separately approved snapshot release/activation destination | High | Passing an outside root is rejected today. Must migrate scope/host/publisher deliberately, not weaken path, privacy, authorization, backup or exact-delta checks. Old absolute-root decisions are not portable live grants |
| SQLAlchemy persistence | Decision 010 specifies hybrid SQLAlchemy 2.0/SQLite; no runtime models, imports or migrations found | Future generated persistence keyed to validated snapshot/materializer/schema/config | Future subsystem | Current MTGJSON `compact-index.sqlite3` is a transient index, not SQLAlchemy or canonical authority. Rebuild requires authorized retained snapshot, not public Git alone |
| AI reasoning context | `src/reasoning/context.py:ReasoningContextBuilder`: injected semantic responses; deterministic copies of values/provenance and bounded omissions; no live model transport | Authorized structured projection from catalog/evidence/user handles with destination-specific export policy | Low-medium attachment / separate transport work | Existing size limits are not rights/exfiltration controls. Private fields, source notes and user data can leak; provider prose is untrusted, memory is never authority |

## Evidence/storage assumptions

- `src/repository/evidence.py` and `sources.py`: archived source identity/path/content
  verification and injected evidence/game roots already exist. Future attachment
  must route the complete authorized evidence set rather than guessing checkout paths.
- `src/acquisition/framework.py:RawSnapshotStore`: immutable hash-addressed snapshots
  already work with chosen roots. Location and successful capture do not establish
  publication permission, canonical authority or admission approval.
- `src/official_datasets/acquisition.py`: full reference datasets can be local and
  Git-ignored (`data/local/reference-datasets`). Not all provider bytes are public.
- `src/production_evidence/repository.py`: permanent evidence is bounded and rejects
  full AllPrintings/transient archives/SQLite. Do not expand its allowed public
  inventory to implement private data storage.
- `admission_publication_inventory`: currently reconstructs approved delta from
  Git `show`/`ls-tree`, then includes payload/evidence/audit/checkpoints. An external
  release needs an equally exact bound inventory; `state.json` filtering alone fails.
- Current `admission_bindings` includes absolute repository scope. Preserve legacy
  records as historical evidence; separately define portable authority scope and
  trusted staging-root capabilities for new operations without editing old grants.

## Missing documentation and maturity

`docs/API_CONTRACT.md` does not exist. Audited substitutes are
`CANONICAL_QUERY_ENGINE.md`, `CANONICAL_QUERY_LAYER.md`, `CANONICAL_CONTRACT_v2.md`,
`CANONICAL_IMPORT_PIPELINE.md`, `CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md` and
`AI_REASONING_CONTEXT_LAYER.md`. This is an inventory gap, not an implemented REST API.

README, PROJECT_INVENTORY and PROJECT_STATUS contain historical phase summaries
with old “current” headings. Source inspection establishes present maturity:
filesystem repositories, query/projection validation, mechanical evidence dossiers,
collection audits and synthetic Product/Decision paths exist. SQL persistence,
complete typed production materialization, comprehensive gameplay/rules execution,
strategic Deck/Competitive domains, production simulation and live AI Advisor
transport are not established implementations by this proposal.

## Compatibility evidence required later

Use actual writer-produced synthetic snapshots for new integration tests, including
an unrelated fictional game and variable entity counts. Validate aliases and real
Card↔Printing↔Finish relationships, acquisition lineage, evidence lookup, omissions,
consumer acceptance and idempotency. Count/dictionary smoke checks alone are not
workflow acceptance. All required consumers must validate before activation.

Keep `tests/historical_catalog.py` and historical expected query hashes/censuses
unchanged. Existing replay uses its original fixture; an expanded/private current
operation uses its explicitly selected new root. Public historical fixture use is
not a new rights grant. New private integration data never enters public fixtures,
logs or evidence snapshots merely to make CI pass.
