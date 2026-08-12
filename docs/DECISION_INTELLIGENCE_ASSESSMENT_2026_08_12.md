# Decision Intelligence architecture and roadmap assessment — 2026-08-12

## Scope and authoritative baseline

This is a design assessment, not implementation authorization. The checked-out baseline is merge
commit `1574f7778cc0748b14544ead631b4c906eedcd41` (GitHub PR **#155**). That merge incorporated the
roadmap reconciliation performed against its mainline parent `bf2976c0c42153f11756bd362767356f23671cfc`
(GitHub PR **#154**). The highest project milestone actually merged is **Phase 147**. A project phase
labels capability work; a GitHub PR labels an integration event. They are independent: Phase 147
arrived in PR #154, while PR #147 was an earlier Phase 143 repair. No proposed Phase 148 variant is
part of the baseline or authoritative.

Architecture v12 remains sound and unchanged. Its modular, deterministic, data-driven direction
already permits domain analytics and a downstream decision layer. This assessment refines the
planned boundaries inside that direction; it does not add a new tier, alter a frozen contract, or
modify canonical, market, knowledge, collection, retained-evidence, or production data.

Competitive Intelligence remains **parked / known gap / not on the current critical path**. Nothing
here reopens provider verification, tournament acquisition, retention, or competitive fact work.

## Current reusable capabilities

| Existing capability | Reuse in future decision verticals | Important limit |
|---|---|---|
| Canonical Product Repository | Stable Game, Product, ProductVersion, Printing, Card, pack, slot, sheet, treatment, finish, and rarity identities; validated relationships | Pack topology is not a guaranteed fixed-content manifest, an offer, or a valuation model |
| Canonical Query / Semantic Query | Provider-neutral, versioned, provenance-aware read seams | Does not compose user objectives or recommendations |
| Evidence and review frameworks | Immutable provenance, validation, explicit unknown/incomplete states, source separation, replay | No evidence class yet for a complete guaranteed manifest, product supply, sales depth, comparable-product outcomes, or deck performance |
| Market Intelligence | Immutable Printing or sealed-product observations; exact dimensions; timestamps; listing/sales-count fields; descriptive multi-snapshot movement | Production coverage is a bounded two-snapshot MB2 pilot; no presale regime, release-relative series, liquidity model, durable-value forecast, or transaction-cost policy |
| Card Intelligence | Reviewed Printing history, provider-specific demand ordinal, literal represented-deck inclusion, evidence quality, limitations, deterministic v4 explanations | Ten-Card pilot; no valuation, playability judgment, archetype inference, recommendation, or adequate tournament evidence |
| Collection Engine / Collection Intelligence | Immutable ownership snapshots, exact Printing resolution, acquisition-cost coverage, deck requirements, deterministic allocation, missing/excess/reusable copies, completion and price-free priorities | No market join, budget reservation, multi-deck opportunity cost, staple reuse graph, legal deck validation, or acquisition-plan optimizer |
| Analytics Engine | Immutable reports, fingerprints, deterministic derived measures, canonical analytics seam | Existing reports do not express product scenarios or deck alternatives |
| Decision Engine v1 | Generic, versioned, deterministic rules over bounded analytics; stable decisions and supporting facts | It is a threshold/alert evaluator, not a multi-alternative acquisition optimizer; it does not query repositories, compute domain analytics, or represent objectives, utility, uncertainty, sensitivity, abstention, and trade-offs |
| AI Reasoning Context and Model Adapter | Deterministic structured context, provenance, truncation, explicit unknowns, provider-neutral future model boundary | Current context is canonical-semantic oriented and there is no provider or ChatGPT decision request/response path; a model must explain, never originate, the recommendation |

The repository therefore has most read-only seams and governance disciplines, but not the
cross-domain decision contract or either requested domain model.

## Proposed shared Decision Intelligence architecture

Product Intelligence and Deck Intelligence should plug into one broader **Decision Intelligence**
framework rather than become isolated recommendation subsystems:

```text
immutable repository evidence and user-owned snapshots
  -> domain evidence views
  -> domain analytics (Product / Deck / Collection / Market / Card)
  -> versioned decision request (objective, alternatives, constraints, horizon, policy)
  -> thin acquisition-decision orchestrator
  -> Decision Engine policy evaluation
  -> structured recommendation, sensitivities, provenance and abstention
  -> reasoning-context projection
  -> ChatGPT explanation
```

This is a composition refinement within Architecture v12. Domain analytics remain Analytics Engine
capabilities; deterministic policy evaluation remains the Decision Engine; the reasoning context and
AI adapter remain downstream. ChatGPT must receive the repository-produced recommendation and its
evidence, not recompute value from chat history or silently fill missing inputs.

### Generic contracts to design before either domain implementation

Contracts should be game-neutral where practical and use opaque canonical entity IDs:

1. **`decision-request-v1`** — decision kind, candidate alternatives, user objective, constraints,
   budget/currency, time horizon/as-of time, acquisition objective, risk and uncertainty posture,
   transaction-cost policy, required evidence freshness, and explicit assumptions.
2. **`decision-alternative-v1`** — stable alternative ID and action code, domain-owned subject
   references, eligibility, cost/cash-flow components, benefits, risks, reversibility, and evidence
   references. The shared schema does not enumerate product contents or deck zones.
3. **`decision-policy-v1`** — stable policy/version, required metrics and evidence gates, objective
   function or ordered criteria, constraint handling, tie policy, uncertainty treatment, abstention
   thresholds, and explanation templates. Policy changes are reviewable data/configuration.
4. **`decision-analysis-v1`** — domain-metric envelopes with typed quantity/unit/currency/time basis,
   known/unknown status, uncertainty or bounded scenarios, assumptions, input fingerprints, and
   provenance. Metric namespaces prevent accidental comparison of unlike values.
5. **`recommendation-v1`** — selected action or `ABSTAIN`, ranked feasible alternatives, reasons and
   counter-reasons, rejected/ineligible alternatives, break-even and sensitivity conditions,
   confidence basis (not fabricated probability), missing decisive evidence, limitations, policy
   identity, input snapshots, and deterministic content identity.

The shared layer may standardize `WAIT` and `ABSTAIN`, but domain action vocabularies should be
registered/versioned by decision kind. It must not contain branches for Scene Boxes, Secret Lairs,
Commander decks, Yawgmoth, Eldrazi, Jund, or any named product/card/deck.

### Acquisition Decision Engine disposition

Do **not** create a second standalone engine and do not bury acquisition policy in Product or Deck
Intelligence. “Acquisition Decision Engine” should be a **thin, stateless orchestration facade over
domain analytics and the existing Decision Engine**. It validates a request, asks explicit domain
ports for comparable alternatives, passes normalized metrics and the selected versioned policy to
the Decision Engine, and assembles the recommendation envelope. It owns no provider adapter, source
data, market forecast, product formula, deck evaluator, persistence, or prose generation.

Decision Engine v1 should initially remain compatible. A later implementation milestone can add a
new multi-alternative policy/report contract beside `decision-v1`, rather than pretending its current
single-fact threshold rules already solve optimization. That is an additive extension, not an
Architecture v12 defect.

### Generic versus domain-specific responsibility

| Generic Decision/Acquisition layer | Domain-owned |
|---|---|
| objectives, budgets, horizons, constraints, alternatives, policy/version identity | guaranteed product manifest and copy-count semantics |
| eligibility, common monetary quantities, transaction-cost interface | presale/release regimes and fixed-product comparable selection |
| uncertainty states, scenarios, sensitivity, break-even envelope, abstention | intrinsic singles basket, scarcity-compression, sealed-premium and concentration analytics |
| evidence references, snapshot fingerprints, freshness, limitations | deck zones, legality, substitution, matchup/metagame and gameplay analytics |
| deterministic ranking/tie handling and explanation facts | collection allocation, shared-staple graph, bottleneck and upgrade-path analytics |
| action namespace registry and typed domain metric envelopes | domain action vocabulary and interpretation of domain metrics |

No shared score should collapse heterogeneous evidence into unexplained “value.” Missing inputs must
remain missing, not zero. Domain adapters may project into common monetary/scenario envelopes only
after retaining the original domain metrics and evidence.

## Domain boundaries and missing capabilities

### Product Intelligence

Product Intelligence owns fixed-content semantics and analysis, not recommendation policy. It should
eventually accept generic fixed-content products and produce comparable acquisition scenarios.

Missing models and evidence classes:

- a versioned guaranteed-content manifest linking ProductVersion to exact Card/Printing or an
  explicitly permitted equivalent, copy count, treatment/finish policy, content certainty, and
  effective/release dates; optional/random contents must be separate and never described as
  guaranteed;
- product offers/availability observations distinct from canonical Product identity: sealed price,
  seller/channel/region/currency, condition, timestamp, preorder/released state, quantity/depth,
  fees, shipping/tax assumptions, and provenance;
- release-relative singles observations or a safe derivation over Market observations, explicitly
  labeling presale and post-release regimes;
- supply/availability trajectory and listing/sales-depth observations with coverage and denominator;
- reviewed card-demand/playability, collector/IP, treatment/art, and reprint-risk evidence whose
  source and confidence remain separate;
- comparable-product cohort definitions and outcome windows, versioned and evidence-bound rather
  than selected after seeing an answer.

Missing analytics:

- intrinsic guaranteed-content basket value, with exact price dimensions, missing-price coverage,
  copy counts, liquidation assumptions, fees, and no double counting;
- **presale scarcity premium** and **price-compression risk** as distinct scenario quantities. A
  guaranteed-content product increases identical supply after release, so a presale singles basket
  must not be treated as durable intrinsic value. With insufficient release-relative history, the
  result must be an explicit unknown or bounded sensitivity—not an inferred forecast;
- anchor-card/value concentration (for example contribution shares and concentration measures),
  downside if one or more anchors compress, and coverage of the remaining basket;
- sealed collectible premium separate from singles value, with horizon, liquidity, storage/condition,
  supply, comparable basis, and uncertainty; it is not assumed merely because an item is sealed;
- break-even sealed price, buy-now/wait/buy-singles/keep-sealed/sell-and-rebuy scenarios, cash-flow
  timing, liquidity and transaction-cost sensitivity.

Required APIs should be read-only: resolve/validate manifest, build as-of product evidence view,
analyze contents, analyze concentration/compression/sealed premium, and project domain alternatives.
They must not select the final user action.

### Deck Intelligence

Deck Intelligence owns deck definitions and gameplay/deck-comparison metrics, not ownership truth,
market observations, or final policy.

Missing models and evidence classes:

- immutable, versioned exact decklists with canonical Card identities, main/side/other zones, format,
  effective date, source, intended ruleset, and permitted substitutions;
- format-legality evidence as-of a date, including ban/restriction and deck-construction constraints;
- archetype/version identity and similarity/equivalence rules without name-only matching;
- matchup, results, metagame-share, speed, consistency, resilience, and sideboard evidence with exact
  population, event/date/format/level, denominator, sample size, source and uncertainty;
- staple-reuse and upgrade-path definitions derived transparently from versioned deck corpora.

Missing analytics:

- exact total replacement cost and collection-aware incremental cost using comparable Printing
  policies, market dimensions, missing-price coverage and transaction costs;
- deterministic allocation across candidate decks, contested-card opportunity cost, shared-staple
  reuse, expensive bottlenecks, upgrade path, sideboard needs, and budget feasibility;
- gameplay-fit and competitiveness measures kept separate from acquisition economics, with explicit
  unsupported states where tournament evidence is absent;
- comparison and sensitivity across deck versions, metagame assumptions, price changes, substitutions,
  budget and user gameplay objective.

Required APIs should validate a deck snapshot, calculate legality as-of, calculate collection overlap
and acquisition requirements, calculate market cost, expose gameplay evidence, compare candidates,
and project domain alternatives. The engine must work when competitive dimensions are unknown; it
must abstain from competitiveness claims rather than reopening the parked evidence thread.

### Collection Intelligence role

Collection Intelligence remains the authoritative downstream user-state and allocation domain. It
should eventually provide an immutable as-of ownership view; exact and policy-based availability;
acquisition-cost basis with coverage; reserved/assigned copies; reusable, excess and contested copies;
multi-deck allocation; shared-staple and bottleneck projections; and incremental requirements. It
must not price cards, forecast markets, judge deck quality, or recommend products/decks. Market and
Deck/Product domains join through canonical IDs in a read-only composition layer.

Collection-aware decisions need explicit user-snapshot identity and privacy boundaries. Collection
data and objectives are neither canonical facts nor general evidence and must never be promoted
upstream.

### Decision, recommendation and explanation role

The deterministic recommendation layer decides only from supplied, versioned analytics and policy.
It enforces constraints, compares eligible alternatives, carries uncertainty, finds break-even or
policy-switch conditions, and abstains when a required input or discrimination margin is absent.
Explanation rendering states: what to do; why; why not the alternatives; which facts, snapshots,
assumptions and policy support it; what is unknown; and what changes would reverse it.

Natural-language generation is a downstream presentation. It may summarize and personalize the
structured result but may not invent evidence, change action/rank, hide abstention, or turn sparse
descriptive history into prediction.

## ChatGPT-facing interface concept

A future application/API endpoint should accept a structured request (or translate a user's question
into one for confirmation), never raw chat state as evidence:

```text
POST /decision-intelligence/v1/recommendations
  { decision_kind, subject_refs, collection_snapshot_id, objective,
    budget, horizon, constraints, policy_id, as_of }

-> recommendation-v1
  { action, alternatives, reasons, counterfactuals, break_evens, sensitivities,
    uncertainty, missing_evidence, limitations, evidence_refs, snapshot_refs, policy }
```

Repository-side validation and calculation produce the response. A reasoning-context projection
then supplies the exact response plus bounded supporting evidence to ChatGPT. Follow-up endpoints can
retrieve an evidence reference or rerun the same request under a changed budget/horizon; they should
not expose provider-specific details as core API contracts. The first release can be CLI/service-only
because Architecture v12's REST layer remains planned.

## Dependencies and data gaps

```text
shared decision request / alternative / analysis / recommendation contracts
  ├─ policy, uncertainty, sensitivity and abstention semantics
  ├─ Collection snapshot + allocation ports (implemented foundation; extensions needed)
  ├─ Market as-of/history query ports (implemented foundation; coverage expansion needed)
  ├─ Product path
  │    ├─ guaranteed-content manifest contract and evidence
  │    ├─ sealed offer + release-relative market evidence
  │    └─ product concentration/compression/premium analytics
  └─ Deck path
       ├─ exact deck snapshot + legality contract/evidence
       ├─ collection allocation + market costing
       └─ optional gameplay/metagame evidence
           (competitive evidence remains parked unless later critical)
        -> acquisition orchestration + Decision Engine policy
        -> recommendation reasoning context
        -> future provider/ChatGPT presentation
```

The largest near-term gaps are trustworthy complete fixed-content manifests, release dates and
release-relative market depth; broader historical prices across exact Printings; sealed offer history;
fees/shipping/tax inputs; supply and liquidity denominators; and comparable-product cohort evidence.
For decks, the gaps are governed exact decklists, current legality, substitution semantics, broad
market coverage, and credible denominator-rich gameplay data. User objectives, risk posture, horizon,
budget and transaction-cost assumptions must be supplied—not inferred from repository evidence.

## Roadmap ordering

Use a small number of capability milestones, assigning project phase numbers only when work is
actually authorized:

1. **Shared Decision Intelligence contract and policy foundation.** Specify the five envelopes above,
   domain port boundaries, units/currency/time semantics, uncertainty, abstention, sensitivity,
   provenance, and a recommendation-to-reasoning-context projection. Extend rather than replace
   Decision Engine v1. Use synthetic inputs only.
2. **First vertical: fixed-content Product Intelligence.** Add generic manifest/offer evidence and
   read-only analytics for contents, presale compression scenarios, anchor concentration, sealed
   premium, transaction costs and collection-aware sealed-versus-singles alternatives; then exercise
   the shared policy contract on one bounded representative fixture/corpus, never named-product logic.
3. **Collection-aware acquisition expansion.** Generalize deterministic allocation, contested/shared
   staples, budget and multi-alternative incremental costs where the first vertical proves necessary.
4. **Deck Intelligence vertical.** Add governed decklist/legality contracts, overlap/cost/reuse and
   upgrade-path analytics first. Add gameplay/metagame dimensions only when separately supported;
   unknown competitive evidence must not block an economics/collection comparison.
5. **Recommendation explanation and ChatGPT integration hardening.** Stabilize API/context retrieval,
   counterfactual explanations, privacy, and a separately authorized model provider only after
   deterministic verticals are proven. Explanation contract work begins in milestone 1; live model
   integration is deliberately last.

Product Intelligence is first because it is a narrower, auditable alternative comparison, directly
tests the newly important presale-compression distinction, can use current Product/Market/Collection
seams, and does not require the parked tournament evidence. Deck Intelligence has greater dependency
on deck governance, legality, multi-deck allocation, broad price coverage, and potentially unsupported
gameplay evidence. Collection Intelligence is enabling infrastructure, not a competing end-user
vertical; extend it only for requirements demonstrated by the selected vertical.

## Cross-game generalization

The shared contracts should identify a game/ruleset and use opaque entity IDs, typed quantities,
currency, time, evidence and policy rather than MTG fields. Fixed-content manifests, sealed offers,
collection allocation and alternative comparison generalize directly to other collectible-card games.
Game adapters own zone names, copy limits, legality, rotation, printing/treatment terminology and
product taxonomy. Cross-game comparison is prohibited unless units, currency, time basis and policy
are explicitly compatible. MTG-specific Commander relevance, formats and card identity never enter
the generic evaluator.

## What to design now, and what not to implement

Design now, in the next authorized milestone: the versioned decision request, alternative, analysis,
policy and recommendation schemas; metric units/dimensions; snapshot/evidence references; domain port
interfaces; action-namespace rules; uncertainty/abstention/sensitivity semantics; and reasoning-context
projection. Also draft—but do not populate—the generic guaranteed-content manifest, product-offer,
deck-snapshot and legality contracts so their identity/reference needs test the shared seams.

Do **not** yet implement Product Intelligence or Deck Intelligence runtime packages, formulas, scores,
recommendation rules, REST endpoints, ChatGPT/model providers, live integrations, provider adapters,
new acquisitions, market forecasts, tournament evidence, portfolio automation, schedulers, or writes
to canonical/market/knowledge/collection/production evidence. Do not create named-product or named-deck
branches, treat presale basket value as durable value, infer sealed premium, treat unknown as zero,
or assign a sequence of micro-phases. Do not change Architecture v12.

## Clear next milestone recommendation

The next implementation milestone should be **Decision Intelligence Contract Foundation**: an
additive, synthetic-only specification and implementation of the generic request, alternative,
domain-analysis, policy, recommendation, uncertainty/abstention and provenance contracts, plus the
thin orchestration and reasoning-context boundary—**without implementing Product or Deck analytics**.
This shared foundation prevents the first Product vertical from hard-coding an acquisition engine
that Deck Intelligence would later have to duplicate or unwind.
