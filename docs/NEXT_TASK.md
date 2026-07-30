# Next Task

## Phase 66 — Await a Complete External-Evidence Handoff

**Status:** Evidence-waiting; verification is conditionally authorized, but the
entry gate is not satisfied and processing has not begun

**Acquisition constraint:** Live-web access is not assumed. Use the controlled
external-evidence handoff in `docs/EVIDENCE_ACQUISITION_PACKET_PHASE_66.md`.

## Current Authorized Action

Maintain the controlled handoff boundary and wait for an artifact-bearing,
content-complete, independently reviewed external-evidence handoff. Once and
only once the entry gate is satisfied, verify the supplied bytes and reconcile
supported claims with the Rule Claim Matrix. Repository agents must not acquire
or fabricate the missing evidence.

## Entry Gate

- At least one real, claim-relevant external artifact exists under the raw handoff.
- The manifest declares every file, size, SHA-256, media type, acquisition context,
  product-version scope, narrow claim, and independently resolvable locator.
- An identified second human has reviewed bytes, hashes, locators, scope, and claims.
- The handoff is content-complete for the bounded submission and explicitly
  authorized for verification.

The PR #18 handoff has an empty `artifacts` array and artifact directory. It is
a valid record of unsuccessful research and source leads, but it fails this gate.

## Scope After Entry

- Archive bounded, high-authority sources for pack event count and roles, draw
  counts, pool mappings, replacement, treatment rules, and collation dependencies.
- Verify a human-supplied raw intake manifest and exact artifact bytes before
  preparing any Evidence Repository bundle.
- Reconcile the retained matrix/report with exact locators, contradictions, and
  explicit unresolved claims.
- Decide architectural fit from supported behavior without redesigning Tier 0.
- Authorize or block a later canonical-rule population milestone claim by claim.

## Exclusions

- No Product, Print Sheet, Slot, Card, or Printing record may change or be populated.
- No probability, simulation, analytics, promotion, API, UI, persistence, or AI behavior.
- No Tier 0 redesign or product-specific engine logic.
- No repository-side external acquisition and no processing of the current empty handoff.

## Acceptance Baseline

- All evidence bytes are content-verified, source-registered, and precisely located.
- The revised matrix/report are deterministic, schema-valid, and cross-validated.
- Unknown or conflicting claims remain explicit and are never inferred silently.
- Canonical repositories and promotion audits remain unchanged.
- The complete suite and repository validation pass.

The complete dependency assessment, exclusions, and acceptance criteria are in
`docs/FIRST_BOOSTER_PLAN.md`. Wait until the entry gate is demonstrably satisfied.
