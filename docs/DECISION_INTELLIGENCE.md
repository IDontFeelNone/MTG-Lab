# Decision Intelligence Contract Foundation

## First domain vertical

The synthetic fixed-content acquisition adapter is the first end-to-end use of these contracts. It
builds a request from a `FixedContentProductAnalysis`, caller-supplied constraints/preferences, and
explicit alternatives. Supported objectives are
`minimize_acquisition_cost_for_guaranteed_contents` and `acquire_guaranteed_contents_now`; both mean
that the guaranteed contents are the acquisition subject and only supported present routes are being
compared. Supported actions are `BUY_SEALED_NOW` and `BUY_SINGLES_NOW`. `WAIT`, sealed collecting,
and sell/rebuy actions are reserved but analytically unsupported.

Policy `fixed-content-current-acquisition-cost` version `1.0.0` minimizes current comparable cost.
Sealed cost is Product Intelligence's effective offer cost; singles cost is the complete guaranteed-
component acquisition total plus an explicitly supplied singles transaction cost. Decimal values are
normalized to a shared exact integer scale for the generic numeric policy comparison. A tie abstains.
The recommendation records exact display costs/difference, objective, factors, descriptive anchor
concentration, evidence-quality state, gaps, and algebraic change thresholds. No confidence
probability was added: existing completeness, uncertainty, and decision-support states carry the
appropriate semantics.

Domain preflight also abstains for incomplete manifests, unknown values/costs, incompatible currency
or market dimensions, contradictory economics, provenance conflict, missing singles transaction
cost, unsupported objective, or unsupported alternative. Potential presale scarcity premium,
post-release compression, sealed collectible premium, future supply, liquidity/listing depth,
collector/IP demand, reprint risk, and historical comparables remain explicit `not_evaluated`
limitations. ChatGPT receives the completed recommendation through the existing reasoning context
and may explain, but neither recalculate nor override, it.

## Status and boundary

The additive Decision Intelligence foundation approved by the 2026-08-12 assessment is implemented
over the authoritative `19b69c2` baseline (GitHub PR #156). The highest merged **project phase** at
that baseline is Phase 147, delivered earlier by PR #154; phase and PR numbers are independent.
Architecture v12 remains frozen and unchanged.

This milestone is synthetic-only. It adds no external acquisition, provider, secret, workflow,
production recommendation, canonical mutation, retained market observation, or Card Intelligence
fact. Competitive Intelligence remains **PARKED / KNOWN GAP / NOT ON CURRENT CRITICAL PATH**.

## Contracts and orchestration

The game-neutral `decision_intelligence` package supplies immutable `decision-request-v1`,
`decision-alternative-v1`, `decision-analysis-v1`, `decision-policy-v1`, and `recommendation-v1`
models plus matching JSON Schemas. Requests bind explicit objectives, alternatives, caller-owned
constraints and preferences, opaque domain inputs, evidence, policy identity, uncertainty, and input
snapshots. Domain analysis envelopes preserve domain/version identity, alternative identity, opaque
metrics, known/unknown/incomplete/unsupported states, provenance, assumptions, limitations,
uncertainty, sensitivity inputs, and snapshots.

The thin, stateless acquisition-decision orchestrator performs only:

```text
validated request + supplied domain analyses + exact policy
  -> ordered deterministic policy evaluation
  -> structured selected outcome or ABSTAIN
```

Policy criteria name opaque numeric metrics and explicitly choose maximize or minimize ordering.
There are no hidden weights, inferred utility, domain formulas, provider access, persistence, prose,
or LLM calculation. Action and metric vocabularies remain domain-owned. Canonical JSON, sorted input
normalization, SHA-256 request/recommendation identities, duplicate-metric contradiction detection,
and conflicting evidence-reference rejection make replay reproducible.

## Fail-closed behavior

Abstention is a first-class outcome. The orchestrator abstains for a policy identity mismatch,
unknown alternatives, missing required metrics, unknown/incomplete/unsupported required evidence,
non-numeric policy inputs, contradictory metrics, conflicting provenance references, or a policy
tie. An abstention has no selected alternative and retains machine-readable reasons, uncertainty,
assumptions, limitations, provenance, and snapshots.

Selected recommendations contain ordered structural rationale, supporting factors, counterarguments,
evidence references, uncertainty, assumptions, limitations, and conditions under which the ordered
comparison could change. Confidence is not fabricated.

## Reasoning-context / ChatGPT boundary

`recommendation_reasoning_context` projects the complete repository-produced recommendation into a
versioned AI-facing envelope. Its instruction permits explanation but forbids changing the outcome,
recalculating it, or inventing evidence. ChatGPT is therefore a downstream conversational renderer;
it is not required or permitted to reconstruct the calculation from raw evidence.

## Future domain integration and prerequisites

Product Intelligence now validates guaranteed-content manifests and offers, computes its own
domain analytics, and supplies alternative envelopes without selecting the action. Future Deck
Intelligence will similarly own governed list, legality, collection-overlap, cost, and optional
gameplay analytics. Both use the same shared contracts and policy boundary; neither is implemented
here. The shared package contains no game, card, product, set, deck, format, booster, collectible, or
tournament semantics.

Before a real product can be evaluated, one governed packet must supply a complete guaranteed-content
manifest, timestamped sealed effective-cost evidence, complete compatible singles observations,
explicit transaction costs, and provenance/snapshot identity. Deck Intelligence remains later and
competitive evidence may remain unknown without reopening the parked work.
