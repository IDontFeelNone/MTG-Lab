# Fixed-Content Product Intelligence Foundation

## Current merged status (2026-10-12)

Canonical main independently verified on 2026-10-12: `dd08c76d09e4b8d10c411ade0d8445987c8875c0`, the merge of GitHub PR #161 — Fixed-Content Evidence Admission Hardening. GitHub PR numbers and project phase numbers are independent; Phase 147 remains the highest numbered project phase. No new phase number is assigned to the later named milestones.

Implemented: shared Decision Intelligence contracts, synthetic fixed-content Product analysis and sealed-versus-singles current-cost policy, packet v1, and hardened human-attested review v2. The hardening separates eligibility from approval, freezes nested inputs, requires cost provenance and freshness, validates replay, and binds review to the exact packet/window. Production fixed-content pilot assembly, readiness review, evaluation, and recommendations have not occurred. Forecasts, premium models, simulation, API/UI, live AI-provider integration, and an operational AI Advisor remain unsupported or planned.

Architecture v12 remains frozen. Repository-first canonical truth, deterministic analytics and decisions, versioned immutable evidence, human-reviewed production admission, and product-neutral/game-neutral generic engines remain unchanged. AI/ChatGPT is the explanation and reasoning interface over validated outputs; it does not calculate or override acquisition decisions. Competitive Intelligence remains **PARKED / KNOWN GAP / NOT ON CURRENT CRITICAL PATH**. Competitive Card Intelligence and Deck Intelligence remain planned and unauthorized; existing collection/deck-completion helpers are not the planned Deck Intelligence decision domain.

The next candidate, requiring separate authorization, is one governed real fixed-content Product Intelligence pilot for **Commander Collection: Black (non-premium)**: complete independently verifiable official contents, exact canonical Printings, one available current sealed offer, complete compatible current singles observations, explicit transaction costs (including evidence for zeros), source digests/provenance, and a deterministic freshness window. Stop on any gap. Packet assembly and human readiness review do not authorize canonical promotion or acquisition evaluation. Only after separate evaluation authorization and an exact human-attested v2 `READY_FOR_EVALUATION` review may a production caller use `require_ready_evidence_review` before the existing Product analysis and Decision policy.

## Acquisition decision adapter

The first synthetic end-to-end vertical adds a thin Product Intelligence adapter without changing
the descriptive analysis contract. It projects product/game/manifest/offer/analysis identity,
current costs and deltas, coverage and unknown counts, comparability, component contributions,
anchor concentration, evidence/timestamps, assumptions, limitations, unsupported dimensions, and
input snapshots into generic Decision Intelligence requests and alternative envelopes.

Decision Intelligence—not the descriptive analyzer—interprets the explicit objective and applies
versioned current-cost policy `fixed-content-current-acquisition-cost` `1.0.0`. The only evaluated
routes are `BUY_SEALED_NOW` and `BUY_SINGLES_NOW`; singles transaction costs must be supplied.
Selected output includes the exact current cost difference and algebraic break-even thresholds.
Anchor concentration remains descriptive explanatory context and never becomes a price-collapse
forecast. Future `WAIT`, sealed-collectible, and sell/rebuy vocabulary requires new governed evidence
and policy support and currently causes abstention.

## Status and scope

Implemented from baseline `64410189479fc2cc1dae9decf8588c7c115f7613` (merged GitHub PR #157).
This synthetic-only foundation is deterministic, immutable, read-only, versioned, provenance-preserving,
and game-neutral. It does not change frozen Architecture v12 and does not create a production
recommendation.

## Contracts

* `fixed-content-product-manifest-v1` describes canonical game/product identity, category, dates,
  guaranteed typed collectible components, exact quantities and comparable printing/finish/language/
  treatment dimensions, evidence, completeness, explicit unknowns, assumptions, and limitations.
  Components need not be cards.
* `product-acquisition-offer-v1` keeps listed price, shipping, supplied tax, fees, discounts, exact
  effective acquisition cost, currency, time, provider, and evidence separate.
* `component-valuation-input-v1` is a thin binding to Market Intelligence's immutable
  `MarketObservation`; Product Intelligence does not own or copy market history.
* `fixed-content-product-analysis-v1` is a content-identified descriptive result. It exposes exact
  sealed cost, known and (only when complete/comparable) total component cost, both cost deltas,
  item contributions, largest/anchor concentration, top-N concentration, transaction-cost impact,
  valued component/quantity coverage, unpriced counts/quantity, and comparability issues.

Currency, provider, timestamp, price type, printing, finish, language, and treatment mismatches never
produce an exact total or cost delta. Partial evidence retains a known subtotal and explicit incomplete
state rather than treating missing prices as zero. Duplicate identities and conflicting inputs fail
closed. No repository or network writer exists.

## Ownership boundaries

* **Market Intelligence** owns observations, histories, providers, and market dimension semantics.
* **Product Intelligence** owns fixed-content manifests, sealed offers, and descriptive aggregation of
  already supplied evidence.
* **Card Intelligence** owns interpreted card-level evidence; Product Intelligence does not infer it.
* **Collection Intelligence** owns user inventory/state and is not read in this milestone.
* **Decision Intelligence** owns objectives, alternatives, policies, abstention, and recommendations.
  Product Intelligence projects generic metrics through `DomainAnalysisEnvelope` only.
* **AI/ChatGPT** may eventually explain a repository-produced structured recommendation; it does not
  calculate product economics or select an action.

Acquisition objectives—including mechanical ownership, minimum cost, art/treatment collecting,
sealed collecting, deck acquisition, and resale—therefore remain downstream request/policy concerns.

## Explicitly unsupported

Intrinsic component acquisition value is reported only as the literal sum of exact supplied component
observations. Presale scarcity premium and sealed collectible premium are distinct, unevaluated
concepts and are never folded into that sum. Post-release compression risk, supply trajectory,
availability, listing/sales depth, liquidity, playability/demand, collector/IP demand, artwork demand,
reprint risk, and historical comparable-product behavior are also `not_evaluated`. There are no
prediction, fair-value, investment, recommendation, or product-specific formulas.

## Bounded future path

The next useful boundary is one reviewed production evidence packet containing a complete manifest,
sealed offer/effective cost, complete comparable singles observations, explicit transaction costs,
and provenance/snapshot identity. A real evaluation must preserve the distinction among component
acquisition cost, presale scarcity premium, and sealed collectible premium and fail closed where the
latter concepts lack evidence. No production target, acquisition, premium model, forecast, or UI is
authorized by the synthetic vertical.

## Governed production evidence packet

`fixed-content-acquisition-evidence-v1` is the production input boundary, not an analysis or a
recommendation. It composes `FixedContentProductManifest`, `ProductAcquisitionOffer`, and a complete
partition of every guaranteed component into either `ComponentValuationInput` or an explicit
unpriced ID. `SourceSnapshot` governs provider, source record/document identity, locator when
permitted, canonical references, publication time when known, retrieval time, evidence state, and a
strict SHA-256 digest. Manifest publication/effective time, sealed offer observation/effective time,
each Market observation/recording time, retrieval times, and packet assembly time remain independent.

The sealed wrapper records availability only when actually evidenced and separately marks shipping,
tax, fees, and discounts `known`, `unknown`, `incomplete`, or `not_applicable`; the embedded offer
continues to own exact listed-price-to-effective-cost arithmetic. `SinglesTransactionCosts` records
shipping, acquisition-model marketplace fees, other explicit costs, currency, completeness,
seller/order assumptions, and provenance. Unknown singles cost amounts and their total serialize as
null; complete cost bundles require every amount. Missing values are never converted to zero: a
component without compatible price evidence must be explicitly unpriced, and an unknown required
cost remains unknown.

Canonical JSON uses sorted keys and compact separators. Packet identity is SHA-256 over the complete
logical content including retained input snapshots and timestamps. The replay repository returns the
same bytes for the same packet and rejects identity reuse with different bytes; replay validates the
digest. Construction is immutable and never writes canonical, Market, Card Intelligence, or other
production repositories. The matching JSON Schema rejects additional top-level fields and unsupported
future evidence classes.

### Admission hardening and manual review

The packet remains `fixed-content-acquisition-evidence-v1`. Sealed cost-state and future-evidence
mappings are recursively frozen copies; contained contracts and exported JSON cannot alias mutable
caller data. Existing valid numeric packet bytes and identities are preserved. Null singles cost
amounts are an additive representation of explicit unknowns, and produce a null total; they cannot
be marked complete or qualify for READY. Replay validates nested contracts, embedded identity,
content digest, and canonical byte encoding.

Critical nested manifests, offers, valuations, and observations are checked against their existing
versioned shapes. Unknown nested fields, unsupported versions, malformed timestamps, duplicate
component IDs, and a nonzero sealed cost marked `not_applicable` are rejected. The packet schema
embeds the existing Product contract definitions and the MarketObservation serialized shape for
offline validation; Market continues to own observation semantics. Timestamp validation does not
rely on jsonschema's optional date-time dependency.

`assess_evidence_packet(packet, as_of=..., acceptable_observed_after=...)` returns automated
eligibility and issues, never human approval or an acquisition action. Both times are caller-owned,
timezone-aware, deterministic inputs. The observation window is inclusive; a missing cutoff cannot
qualify, and a cutoff after `as_of` is invalid. Sealed and singles observation times are independently
checked for staleness and future dates. Material evidence publication, retrieval, recording,
effective, and assembly times cannot be in the future; inputs dated after assembly and publication
after retrieval also fail. Singles must preserve the same provider/currency/price-type/observation-
time basis. Sealed availability must be evidenced `available`; `unknown` and `unavailable` fail.

Singles transaction provenance must contain unique, present SourceSnapshot references with known
evidence state and valid digests. These sources must support the entire cost bundle, including every
zero; seller/order assumptions must explicitly document the basis for zero costs. An amount of zero
is not a substitute for unknown costs. The human reviewer verifies that the referenced evidence
actually supports the amounts and assumptions; this library does not acquire source bytes or
independently authenticate declared source claims.

`fixed-content-acquisition-evidence-review-v2` distinguishes eligibility from an affirmative human
attestation. Existing positional review arguments remain, but READY now additionally requires:

- `acceptable_observed_after` and the explicit `reviewed_at` evaluation time;
- `human_approved=True`, supplied by the trusted human-review caller;
- `reviewed_packet_id` equal to the exact packet identity; and
- a nonempty durable `review_reference` and reviewer identity.

Without these inputs, `review_evidence_packet` returns `NOT_READY_FOR_EVALUATION` with machine-readable
issues, even for an eligible packet. No caller should generate the human attestation from eligibility.
The review record retains packet identity, policy window, reviewer/time, human attestation, durable
reference, status, and issues. `EvidencePacketReview.from_dict` validates only v2 records. Historical
v1 READY records lacked the required attestation/policy and must receive a new human review; they
cannot be upgraded by relabeling the schema. There are no retained production packets or reviews to
migrate at this milestone's baseline.

`require_ready_evidence_review(packet, review, as_of=..., acceptable_observed_after=...)` verifies
exact packet binding, affirmative review, the identical approved time window, and eligibility again.
Changing a packet or the time window requires a new review. This verifies record consistency, not
human authentication or the existence of an external approval reference; those remain the trusted
review caller's responsibility. It introduces no signature service or authorization subsystem.
Neither this guard nor review invokes Product analysis or Decision policy. Any future production
entry point must use the guard before the existing analysis/evaluation functions; those functions
remain available for their existing synthetic workflows.

Reference-only placeholders for presale/post-release observations, supply/availability, listing
depth/liquidity, historical comparables, sealed collectible premium, collector/IP demand, and reprint
risk remain optional and unevaluated. They do not satisfy current-cost evidence gates.

### Existing reuse, gaps, and pilot

The packet reuses canonical Card/Printing identities, immutable `MarketObservation` semantics and
retained market history, Decision Intelligence `EvidenceReference`, existing product identity, and
established evidence/source digest conventions. It creates no parallel acquisition subsystem.
Existing production material is insufficient for a READY real packet: retained market observations
cover the bounded MB2 pilot rather than a complete fixed-content product, and no reviewed current
sealed offer/transaction-cost bundle is present.

The provisional later pilot is **Commander Collection: Black (non-premium)**. Repository-retained
MTGJSON deck evidence names an exact product record, its small guaranteed-card scope is manageable,
and it exercises exact Printing resolution without non-card valuation ambiguity. It is preferable to
a large preconstructed deck and is not the motivating named product. Selection remains conditional:
a later authorized assembly must prove complete official contents, exact canonical Printings, a
current sealed offer, complete compatible current singles observations, transaction costs, and source
integrity. No production packet was retained in this milestone.

The exact remaining dependency chain is: assemble that one governed packet from reviewed sources →
human review → separate evaluation authorization and exact READY admission guard → call existing `analyze_fixed_content` → call the existing
sealed-versus-singles Decision Intelligence policy → expose its structured recommendation to ChatGPT.
No additional infrastructure phase is presently indicated.
