# Decision Intelligence Contract Foundation

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

Future Product Intelligence will validate guaranteed-content manifests and offers, compute its own
domain analytics, and supply alternative envelopes without selecting the action. Future Deck
Intelligence will similarly own governed list, legality, collection-overlap, cost, and optional
gameplay analytics. Both use the same shared contracts and policy boundary; neither is implemented
here. The shared package contains no game, card, product, set, deck, format, booster, collectible, or
tournament semantics.

The recommended next milestone is the **Fixed-Content Product Intelligence Foundation**. It still
requires governed guaranteed-content manifests, offer/effective-time evidence, comparable exact
market dimensions, transaction-cost inputs, and explicit unknown handling. It must remain a generic
domain analytics producer and must not bypass the shared recommendation policy. Deck Intelligence
comes later and competitive evidence may remain unknown without reopening the parked work.
