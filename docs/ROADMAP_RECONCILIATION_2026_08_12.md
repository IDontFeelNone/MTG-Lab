# Roadmap reconciliation — 2026-08-12

## Authoritative baseline

The baseline inspected for this reconciliation is the repository's checked-out mainline merge commit
`bf2976c0c42153f11756bd362767356f23671cfc` (`Merge pull request #154 ... initialize-phase-147-topdeck.gg-provider-probe`).
It merges project **Phase 147**, whose implementation commit is `6ecaa35`. Therefore Phase 147 is
actually merged and is the highest project phase present on the inspected mainline.

Project phase numbers describe MTG Lab milestones. GitHub pull request numbers describe integration
events. They are independent sequences: project Phase 147 arrived through GitHub PR #154; GitHub PR
#147 was an earlier repair within project Phase 143. Neither number may be used to infer the other.
This conclusion comes from the repository commit graph and files at the inspected baseline, not from
prior conversation.

## Competitive Intelligence disposition

**PARKED / KNOWN GAP / NOT ON CURRENT CRITICAL PATH.** Tournament evidence remains an explicit
unknown. No further competitive acquisition phase is currently authorized: do not begin Phase 148A,
another TopDeck acquisition phase, Phase 148B, or any follow-on competitive phase; do not add API or
GitHub Actions secrets, contact a live provider, or integrate more competitive evidence.

Sufficient fail-closed preparation already exists:

- project Phase 145 added provider-neutral `card-competitive-evidence-v1`, a schema, a local validator,
  a validation CLI, synthetic tests, explicit unknowns, and denominator/retention boundaries;
- project Phase 146 documented the provider, API, legal, licensing, retention, redistribution,
  identity, pagination, completeness, and denominator uncertainties and approved no provider;
- project Phase 147 added a transport-free, non-retaining TopDeck projector and synthetic tests with
  strict validation, literal metrics, replay checks, credential-safe diagnostics, and permanent
  exclusion of player identity; and
- there is still no live request, retained tournament snapshot, competitive fact, provider approval,
  production transport, secret, or acquisition workflow.

The exact dependency chain if this thread is ever explicitly resumed is:

1. a normal application runtime capable of ordinary external API integration must exist;
2. a human must inspect current provider-controlled API documentation and legal terms;
3. written provider clarification must verify API use, permanent bounded retention, historical
   storage, redistribution, and attribution for stored and derived data;
4. stable event/deck identities, filters, pagination, response versioning, completeness, population,
   and denominator semantics must be verified;
5. a separately authorized phase must select at most one provider and approve credentials/transport;
6. one bounded, non-retaining metadata probe with redacted diagnostics must pass;
7. a separately reviewed retention/acquisition contract and immutable evidence boundary must be
   approved before any retained snapshot; and
8. only after independent review of retained evidence may another separately authorized phase decide
   whether competitive facts or explanations are admissible.

Any failed or unknown gate stops the chain. Existing contracts and the adapter are preparation, not
authorization. Competitive work is no longer critical-path work because tournament data is only one
optional evidence class, while the product still lacks the decision layer that can turn already-held
card, product, collection, and market evidence into user actions and explanations.

## Product-vision capability assessment

The first useful ChatGPT-facing experience should answer a bounded question with an action, reasons,
alternatives, provenance, and explicit uncertainty. Infrastructure completeness or another evidence
source is not that experience.

| Capability | Current position | Gap to decision intelligence |
|---|---|---|
| Product Intelligence | Generic product repository/promotion foundations exist, but no current end-to-end fixed-content product analysis domain exists. | Define generic product contents, valuation inputs, uncertainty, scenario, and recommendation contracts. |
| Collection Intelligence | Deterministic downstream collection services exist. | Connect owned copies, goals, duplicates, missing contents, and acquisition alternatives to recommendations. |
| Sealed-product analysis | Product evidence foundations exist, but no generic sealed analytical model is authorized or implemented. | Explain contents, premiums, concentration, optionality, and uncertainty without treating unknown contents as zero. |
| Sealed versus singles | Not delivered as an end-to-end decision. | Compare like-for-like acquisition paths, ownership, transaction assumptions, time horizon, and risk. |
| Market-history reasoning | Two retained MB2 snapshots and descriptive, provenance-rich movement exist for a bounded pilot. | Generalize evidence coverage and define permissible scenario reasoning without presenting sparse history as prediction. |
| Decision/recommendation logic | A generic decision-engine foundation exists; current Card explanations intentionally stop before valuation or recommendations. | Add policy-driven actions, alternatives, break-even conditions, sensitivity, abstention, and explicit unknown handling. |
| Explanation/provenance | Strong evidence provenance, limitations, deterministic explanations, and explicit unknowns exist. | Produce recommendation-level “what, why, why not, based on what, and what could change it” output. |
| Evidence-to-decision integration | Canonical, product, collection, market, analytics, reasoning-context, and AI-adapter seams exist mostly as separate capabilities. | Compose them into one read-only, reproducible vertical slice whose conclusion never outruns its evidence. |

The principal gaps are therefore not more competitive records. They are a generic Product
Intelligence domain contract, cross-domain evidence composition, decision and abstention policy,
scenario/sensitivity analysis, collection-aware alternatives, and ChatGPT-ready explanation output.

## Reserved Product Intelligence domain

Product Intelligence is reserved as the next major domain to assess. A separate requirement must
define it before implementation; this reconciliation does not implement it. The future domain must be
generic across Scene Boxes, Secret Lairs, Commander decks, gift products, collections,
preconstructed decks, promotional bundles, and other fixed-content products. It must be able to
represent sealed-versus-singles strategy, guaranteed-content value, presale scarcity premiums,
post-release compression, anchor-card and value concentration, mechanically unique and collector-only
contents, sealed premium, optional/random contents, break-even, wait-versus-buy-now scenarios, and
sensitivity analysis. It must not embed product-specific Crack-the-Plates logic.

## Recommended next major phase

After the separate Product Intelligence requirement is supplied and explicitly authorized, the next
major phase should be **Product Intelligence decision vertical assessment and contract**, followed by
a bounded implementation phase only after review. Its target outcome is one generic, read-only,
fail-closed route from existing product, collection, and market evidence to an acquisition decision
with alternatives, break-even/sensitivity conditions, provenance, limitations, and abstention when
inputs are insufficient.

This is preferable to another acquisition phase because it moves MTG Lab from “What evidence do we
have?” to “Given the evidence, what should the user do, and why?” No project phase number or A/B
suffix is assigned here. The next requirement, not this document, determines the authorized phase
scope.

