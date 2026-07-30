# MTG Lab Project Status

> Executive status dashboard. This document summarizes repository state; it is
> subordinate to the Tier 0 architectural constitution in `ARCHITECTURE.md`,
> `DECISIONS.md`, `DATA_MODEL.md`, `DATA_REPOSITORY.md`, and `RULES_ENGINE.md`.
> Detailed inventory, history, session state, handoff, roadmap, and authorized
> next work remain authoritative in their respective documents.

## Executive dashboard

| Status item | Current state |
| --- | --- |
| Architecture version | v12 |
| Project phase | Phase 66 evidence-waiting state; processing has not begun |
| Last completed phase | Phase 65 — MB2 Product-Rule Evidence Sufficiency Assessment |
| Last merged repository baseline | PR #18 — Phase 66 external research handoff |
| Latest completed repository capability | Product-agnostic Evidence Review Engine |
| Phase 66 status | Research handoff structure exists; verification may begin only after the entry gate is satisfied |
| Current critical-path blocker | No artifact-bearing, content-complete, independently reviewed raw handoff exists for the first evidence-backed MB2 booster |
| Canonical rule status | Population unauthorized |
| Downstream product layers | Pack generation, probability, simulation, analytics, API, and UI unauthorized |

The external-evidence blocker applies to the approved critical path to the first
evidence-backed Mystery Booster 2 booster. It is not the only project-wide
blocker and does not prevent separately approved, MB2-independent foundational
work.

## Verified repository statistics

Counts below were derived directly from the repository on 2026-07-30.

| Item | Count |
| --- | ---: |
| Tracked files | 213 |
| Markdown documents | 29 |
| Python source files under `src/` | 37 |
| Versioned JSON schemas | 16 |
| Test modules | 17 |
| Passing automated tests | 85 |
| Promotion audits | 28 |

### Canonical entities

| Entity | Count |
| --- | ---: |
| Cards | 15 |
| Printings | 15 |
| MB2 Printings | 4 |
| Products | 1 |
| Print Sheets | 0 |
| Slots | 0 |
| Game-level Source Records | 7 |

### Evidence and research artifacts

| Artifact | Count |
| --- | ---: |
| Verified Evidence Repository bundles | 3 |
| Rule Claim Matrices | 1 |
| Evidence Sufficiency Reports | 1 |
| Phase 66 raw handoff manifests | 1 |
| Phase 66 acquired external evidence artifacts | 0 |

The raw handoff contains a research summary, an empty-artifact intake manifest,
and an intentionally empty `artifacts/` directory. It is a controlled research
package and source-lead record, not an Evidence Repository bundle and not proof
of any new product-rule claim.

## Maturity and debt

### Architectural maturity

- Tier 0 data and Rules Engine architecture is approved and remains unchanged.
- Canonical repository contracts, deterministic validation, evidence archival,
  candidate review, promotion audits, and rollback foundations are implemented.
- The product-agnostic Evidence Review Engine is complete. It validates external
  handoff metadata, provenance, artifact integrity, completeness, and internal
  consistency and emits schema-validated JSON and Markdown reports before Rule
  Claim Matrix processing.
- Card and Printing lifecycle foundations are implemented but sparsely populated.
- Print Sheet and Slot lifecycle foundations are implemented but unpopulated.
- Research Log architecture is approved; implementation is deferred.
- Complete MB2 selection behavior cannot be assessed for Tier 0 fit until
  content-complete evidence is preserved and verified.

### Evidence debt

- No preserved evidence establishes complete MB2 pack topology or Slot graph.
- Complete event-specific Printing pools and exclusions are absent.
- Weights or justified frequency semantics are absent.
- Replacement, treatments, conditionality, correlation, and sequence remain unknown.
- The current raw handoff contains leads and failed-access notes but no acquired bytes.

### Canonical-data debt

- Only 15 Cards and 15 Printings are populated, including four MB2 Printings.
- The MB2 Product remains a foundation record with no Slot references.
- Canonical Print Sheets and Slots are empty.
- No canonical MB2 Product rules, complete pools, or collation data exist.

### Implementation debt

- Candidate promotion still requires manual application-workflow decisions;
  batch-level transactional orchestration is deferred.
- Generic pack generation, exact probability, simulation, and generated-pack
  validation are not implemented.
- Persistence, analytics, market intelligence, API, UI, collection, and AI
  advisor product layers remain deferred rather than partially implemented.
- Technical-debt tracking is documentation-based; no automated cross-document
  status validator currently enforces dashboard consistency.

## Critical path to the first evidence-backed MB2 booster

1. Receive an artifact-bearing, content-complete, independently reviewed handoff.
2. Verify raw bytes, paths, sizes, hashes, metadata, version scope, claims, and locators.
3. Register supported sources and construct content-verified Evidence Repository bundles.
4. Reconcile the Rule Claim Matrix and Evidence Sufficiency Report.
5. Decide Tier 0 fit from supported behavior; stop for separate approval if it does not fit.
6. Separately approve and populate canonical Cards/Printings, Print Sheets, Slots,
   and the Product graph in referential order.
7. Separately approve and implement a generic deterministic pack generator.
8. Separately approve and implement exact probability and pack validation.
9. Produce and byte-reproduce one fixed-seed, fully traceable booster result.

## Phase 66 gates

### Entry criteria

Phase 66 evidence verification is authorized only when all of the following hold:

- the raw handoff contains at least one real external artifact needed for a
  Phase 66 claim;
- the manifest is content-complete and lists each exact artifact path, byte size,
  SHA-256, media type, acquisition context, product-version scope, narrow claim,
  and independently resolvable locator;
- every listed artifact exists and no unlisted artifact is presented as evidence;
- an independent human reviewer is identified and has checked bytes, hashes,
  locators, scope, and claim boundaries; and
- explicit authorization is limited to verification and research reconciliation,
  not canonical population or downstream implementation.

The current PR #18 handoff fails this gate because its `artifacts` array and
artifact directory are empty. Phase 66 processing has therefore not begun.

### Exit criteria

- Every accepted artifact is immutable, content-verified, source-registered,
  precisely located, and loadable through the Evidence Repository.
- The deterministic Rule Claim Matrix and sufficiency report reconcile all
  acquired claims, conflicts, and remaining unknowns.
- Pack topology, pool mappings, weights/frequency semantics, replacement,
  treatments, and dependencies are either supported or explicitly unresolved.
- Tier 0 fit is decided only from supported behavior.
- The conclusion authorizes or blocks a later canonical-rule population
  milestone claim by claim.
- Canonical repositories, promotion audits, runtime code, schemas, and tests
  remain unchanged during Phase 66.

### Mandatory stop conditions

Stop at the affected claim boundary if evidence is missing or inaccessible; an
artifact fails path, size, or hash verification; a locator is not independently
resolvable; version scope is ambiguous; sources conflict without resolution;
membership is shown without eligibility or collation; exact weights cannot be
supported; or evidenced behavior cannot be expressed by current Tier 0.

Stopping never authorizes equal-weight, independence, replacement, completeness,
cross-version, or other outcome-affecting inference.

## Outstanding risks

- Public first-party material may omit proprietary weights or collation.
- Mutable or inaccessible sources may prevent content-complete preservation.
- Product versions, channels, languages, regions, or production runs may differ.
- Community observations may corroborate outcomes without proving complete rules.
- Evidence may reveal behavior outside the current one-sheet Slot relationship,
  requiring a separate architectural decision.
- Sparse canonical population may make later complete-pool work large even after
  rule evidence is sufficient.

## Bounded completion estimates

These are planning estimates, not commitments, and begin only after their stated
dependencies and approvals are satisfied.

| Bounded activity | Estimate | Dependency |
| --- | --- | --- |
| Validate a complete raw handoff and report entry-gate failures | 0.5–1 working day | Artifact-bearing reviewed handoff |
| Register a small accepted source set and reconcile Phase 65 research artifacts | 1–3 working days | Successful byte/locator verification |
| Decide and document Tier 0 fit | 0.5–2 working days | Supported selection behavior; longer work requires separate approval |
| Prepare one bounded canonical rule-population milestone | 2–5 working days | Sufficient evidence and separate approval |
| Implement and validate a minimal generic generator | 3–7 working days | Complete validated canonical Product graph and separate approval |
| Implement exact probability plus first-booster validation | 5–10 working days | Stable generator semantics and separate approval |

No estimate is provided for acquiring missing external evidence because source
availability, legal access, completeness, and independent review are outside the
repository's control.

## Documentation authority

1. Tier 0 constitution: `ARCHITECTURE.md`, `DECISIONS.md`, `DATA_MODEL.md`,
   `DATA_REPOSITORY.md`, `RULES_ENGINE.md`, and approved engineering standards.
2. `../PROJECT_INVENTORY.md`: implemented modules and canonical inventory.
3. `ROADMAP.md`: milestone history, sequencing, and debt categories.
4. `SESSION_STATE.md`: durable current-session baseline.
5. `NEXT_TASK.md`: the single authorized next action and its gates.
6. `HANDOFF.md`: concise, replaceable transition note.
7. This dashboard: executive synthesis only; lower-authority text never
   overrides a higher-authority architectural or approval boundary.
