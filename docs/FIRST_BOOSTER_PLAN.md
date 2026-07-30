# First Evidence-Backed Booster Plan

**Status:** Approved critical-path planning baseline; Phase 66 is evidence-waiting
and processing has not begun

**Assessment date:** 2026-07-30

## 1. Executive assessment

Phase 65 is complete. PR #18 added the controlled Phase 66 raw research handoff
structure, but its manifest declares zero artifacts and its artifact directory
contains no external evidence bytes. The repository has a sound evidence archive,
claim-assessment boundary, canonical entity contracts, and dependency-safe
repository validation, but it cannot yet generate an evidence-backed Mystery
Booster 2 pack. The Rule Claim Matrix confirms only Product identity and four
partial Printing-membership examples. Pack topology, complete pools, weights,
replacement, treatments, and collation remain unsupported.

The current blocker on the approved critical path to the first evidence-backed
MB2 booster is therefore an artifact-bearing, content-complete, independently
reviewed handoff. This is not the only project-wide blocker: canonical-data and
implementation debt remain after evidence verification. Implementing a generator
now would either encode assumptions or exercise only synthetic rules. The
shortest trustworthy route is to acquire and
preserve a bounded evidence set that establishes the complete pack topology and
selection semantics, reconcile it into the claim matrix, and only then decide
whether Tier 0 can express the observed behavior.

The Codex environment is not assumed to have reliable live-web access. Phase 66
must use the controlled external handoff defined in
`EVIDENCE_ACQUISITION_PACKET_PHASE_66.md`; inaccessible sources are stop
conditions, not permission to reconstruct or infer their contents.

## 2. Current implementation maturity

| Capability | Maturity | Assessment |
| --- | --- | --- |
| Evidence repository | Implemented foundation | Content identity, manifests, provenance, and verified loading exist. |
| Rule research | Implemented assessment | Matrix/report contracts and deterministic cross-validation exist; evidence is insufficient. |
| Canonical Card/Printing repository | Implemented foundation, sparsely populated | Complete lifecycle exists; only four MB2 Printings are present. |
| Canonical Print Sheet/Slot repository | Implemented foundation, unpopulated | Contracts, loading, promotion, rollback, and dependency validation exist. |
| Canonical MB2 Product rules | Not implemented | Product is a foundation record with no Slot references. |
| Pack generator | Not implemented | No generic rule interpreter or seeded selection API exists. |
| Probability engine | Not implemented | Package placeholder only; no exact distribution calculation exists. |
| Pack validation | Not implemented | Structural repository validation exists, but generated-pack invariants and evidence fixtures do not. |
| End-to-end booster | Not available | Blocked by every rule dependency after Product identity. |

## 3. Updated repository counts

| Repository item | Count |
| --- | ---: |
| Canonical Cards | 15 |
| Canonical Printings | 15 |
| Canonical MB2 Printings | 4 |
| Canonical Products | 1 |
| Canonical Print Sheets | 0 |
| Canonical Slots | 0 |
| Game-level canonical Source Records | 7 |
| Verified evidence bundles | 3 |
| Rule Claim Matrices | 1 |
| Evidence Sufficiency Reports | 1 |
| Promotion audits | 28 |
| Automated tests | 77 |

## 4. Critical path to first booster generation

```text
Evidence
  -> Rule Claim Matrix
    -> Canonical Product Rules
      -> Print Sheets
        -> Slots
          -> Product Definition
            -> Pack Generator
              -> Probability Engine
                -> Pack Validation
                  -> First Evidence-Backed Booster
```

The arrow order is an approval and information dependency. Canonical creation
still follows entity referential order where required: Printings before Print
Sheets, Print Sheets before Slots, and Slots before the validated Product.

| Dependency | Prerequisites | Required evidence | Implementation work | Validation requirements | Complexity | Blocking risks |
| --- | --- | --- | --- | --- | --- | --- |
| Evidence | Registered sources, acquisition boundary, immutable archive | Complete pack composition; pool boundaries; Printing identities; weights or defensible equal-weight claims; replacement; treatment rules; conditional/correlated/sequenced collation | Acquire exact source bytes, register Source Records, create verified manifests, and retain precise locators | Hash/size/path/media checks; source-to-claim provenance; independent review; conflicts retained rather than overwritten | Medium | Public sources may omit proprietary collation; pages may change; sources may conflict |
| Rule Claim Matrix | Verified evidence bundles | Evidence for every currently partial/unknown claim, or an explicit bounded unresolved status | Revise the matrix/report deterministically; classify source versus inference; record contradictions and architectural questions | Schema and cross-reference validation; each claim classified exactly once; no unsupported citations; reproducible output | Small | Evidence may reveal claims absent from the v1 taxonomy or behavior Tier 0 cannot express |
| Canonical Product Rules | Sufficient reviewed matrix and architectural-fit decision | Supported topology and selection semantics | Define the generic canonical rule model needed by observed evidence; approve any Tier 0/schema change before population | No MB2-specific engine behavior; provenance coverage; structural, domain, and statistical rule validation | Large if Tier 0 changes; small otherwise | Current one-sheet Slot may not express conditional, mutually exclusive, correlated, or ordered events |
| Print Sheets | Canonical MB2 Printings and approved pool model | Complete entries and positive relative weights for each pool | Populate missing Cards/Printings in bounded verified batches; create, review, and promote sheet candidates | Complete-pool assertions; unique entries; positive weights; Printing references; game scope; provenance; deterministic snapshot | Large | The full Printing corpus may be large; collector/treatment identity ambiguity; incomplete weights |
| Slots | Approved sheets and pack topology | Stable selection-event roles, draw counts, sheet mapping, and replacement | Create, review, and promote Slot candidates; extend schema only if approved rule semantics require it | Slot-to-sheet integrity; draw and replacement invariants; provenance; deterministic snapshot | Medium | A physical “slot” may not map one-to-one to the current Slot abstraction |
| Product Definition | Complete approved Slot graph | Evidence that the Slot graph describes one complete booster | Update the MB2 Product from foundation to validated and reference all required Slots | Product-to-Slot integrity; exactly complete pack topology; provenance; no dangling/unreachable rules | Small | `slot_ids` are order-independent, which may be insufficient if sequence is meaningful |
| Pack Generator | Validated canonical Product graph | No new facts; it consumes approved rules | Implement generic repository-driven traversal and weighted draws with injected seeded RNG; emit Printing IDs plus reproducibility metadata | Deterministic golden tests; invalid/unvalidated products rejected; replacement honored; no product-name branches | Medium | Canonical model may lack enough semantics; integer-weight sampling bias or unstable iteration |
| Probability Engine | Same validated graph and formally defined generator semantics | No new facts; exact results derive from rules | Compute normalized per-slot and pack-level marginal/joint distributions using exact arithmetic where feasible | Sums normalize exactly; agreement with enumerated tiny fixtures and Monte Carlo confidence checks; dependency behavior covered | Large | Combinatorial explosion; dependent events cannot be treated as independent |
| Pack Validation | Generator, probability results, and evidence-defined invariants | Observable pack constraints and, where available, empirical collation evidence | Validate generated pack size, Slot fulfillment, eligibility, multiplicity, treatments, dependencies, and reproducibility metadata | Property tests across many seeds; deterministic fixtures; impossible outcomes rejected; expected frequencies statistically checked without replacing exact proofs | Medium | Sparse empirical observations cannot prove proprietary collation; false confidence from small samples |
| First Evidence-Backed Booster | All preceding nodes complete | Traceability from every generated selection to canonical rule claims and archived evidence | Run one fixed-seed generation and retain a machine-readable result with versions, seed, inputs, and validation report | Re-run byte-identically; every Printing resolves to Card and eligible sheet; all pack invariants pass; probability result accompanies output | Small | Any upstream uncertainty makes the “evidence-backed” label invalid |

## 5. Remaining blockers

1. No preserved evidence defines the complete booster structure or Slot graph.
2. No complete, evidence-backed MB2 Printing pools or pool partitions exist.
3. No preserved evidence establishes sheet weights or justified equal weighting.
4. Replacement, treatment selection, and cross-Slot collation are unknown.
5. Tier 0 expressiveness remains indeterminate until actual collation evidence is obtained.
6. The canonical MB2 Product is a foundation record; Print Sheets and Slots are empty.
7. Generic pack generation, exact probability, and generated-pack validation are absent.

## 6. Authorized next milestone

**Phase 66 — MB2 Pack Topology and Selection-Semantics Evidence Verification and Reconciliation.**

This is the highest-value bounded milestone because the same evidence resolves
the first critical-path node, upgrades most unknown matrix claims, determines
whether Tier 0 is usable, and prevents premature population or engine design.
It is deliberately an acquisition and assessment milestone, not another card
population wave.

Verification work may enter only after the raw handoff includes real artifacts,
complete manifest metadata and resolvable locators, and an identified independent
reviewer who has checked the bytes, hashes, scope, and claim limits. The current
PR #18 handoff fails that entry gate, so processing has not begun.

The smallest evidence target with the largest downstream unlock is one
content-complete, reviewable source set that establishes: the number and roles
of pack selection events, draw counts, pool-to-event mapping, replacement, and
any treatment or conditional/correlated behavior. Pool entry enumeration and
weights should be captured when present, but absence must be reported rather
than inferred.

## 7. Exact scope

- Identify and register a bounded set of highest-authority sources specifically
  for pack topology and selection semantics.
- Accept externally collected artifacts only through the documented raw intake
  paths and complete intake manifest; do not rely on unrestricted live retrieval.
- Archive the exact retrieved bytes in new game-scoped evidence bundles with
  hashes, sizes, media types, access context, claim provenance, and precise locators.
- Prefer first-party rules/product/checklist material; use clearly classified
  corroborating sources only where first-party material is silent.
- Extend the Phase 65 matrix/report artifacts to reconcile every acquired claim,
  contradiction, and remaining unknown without promoting canonical rules.
- Produce a binary architectural-fit decision: current Tier 0 sufficient, or a
  separately reviewable change is required, with the smallest evidenced gap.
- State whether evidence is sufficient to begin canonical pool/Print Sheet/Slot
  population and identify the exact still-blocking claims if it is not.

## 8. Explicit exclusions

- No canonical Card, Printing, Print Sheet, Slot, or Product changes.
- No inferred pool completeness, equal weights, replacement, or independence.
- No Tier 0, schema, or Rules Engine redesign.
- No pack generator, probability engine, simulation, analytics, API, UI, or persistence work.
- No broad card-population wave and no promotion decisions.
- No claim that observed openings alone prove undisclosed physical collation.

## 9. Acceptance criteria

1. Every acquired artifact is immutable, content-verified, source-registered,
   claim-scoped, and loadable exclusively through the Evidence Repository.
2. Evidence locators support independent review of pack count/roles, draw counts,
   pool mapping, replacement, treatments, and dependencies, or the report marks
   each item explicitly unresolved after the bounded search.
3. The revised matrix and sufficiency report are schema-valid, deterministic,
   mutually consistent, and cross-validated against archived bytes and Source Records.
4. Conflicting sources remain visible with classifications; no reconciliation is
   silently converted into a canonical fact.
5. Architectural fit is decided only from supported behavior and recommends no
   redesign unless a concrete evidence-backed rule cannot be represented.
6. Canonical repositories and promotion audits are byte-for-byte unchanged.
7. The complete automated suite and repository JSON validation pass, and
   repeated artifact generation is byte-identical.
8. The conclusion explicitly authorizes or blocks the next canonical-rule
   population milestone claim by claim.

## 10. Risks

- Authoritative public material may describe pack contents while withholding
  physical sheet weights or correlated collation.
- Source availability and page mutability can prevent complete archival capture.
- Community observations may be useful corroboration but insufficient proof of
  complete or independent distributions.
- New evidence may force an architectural decision before population, extending
  the critical path but preventing a misleading generator.
- “Print Sheet” may be a logical selection pool rather than a literal production
  sheet; provenance and terminology must preserve that distinction.

## 11. Assumptions

- “Evidence-backed” means every rule affecting the generated outcome is supported
  by preserved evidence or explicitly labeled, reviewed inference; the first
  booster target permits no unresolved outcome-affecting inference.
- One booster, not a display/box/case sequence, is the first end-to-end boundary.
- Market value, card images, prices, and user interfaces are unnecessary to prove
  first-booster generation.
- Exact probability calculation belongs on the critical path because the target
  includes evidence-backed selection, not merely a plausible seeded sample.
- Existing promotion and repository foundations are reusable unless evidence
  demonstrates unsupported conditional, correlated, mutually exclusive, or
  sequenced behavior.
