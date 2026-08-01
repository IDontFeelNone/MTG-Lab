# Phase 117A status — GitHub-native authorization workflow implemented

Main contains merged Phase 117 (`b7cee97`). The immutable scope is evidence `30663562841-review-payload-v2`, batch `mb2-batch-000001-e32022126c07`, MB2 / Mystery Booster 2, 1,000 approved candidates, request digest `4b281b3eb45b6a7e3e82a2309c271bffe1cb6c8cb939d46c5b8be059e0b6000d`, candidate digest `e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e`, and canonical pre-state `0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba`. Phase 117A adds only the manual authorization workflow and its validation/persistence support. No authorization exists, no canonical write or promotion occurred, and no MSH/Marvel data is included. Architecture v12 and canonical contracts are unchanged.

# Phase 116 status — ambiguous MB2 identifiers resolved

Merged Phase 115 (`975cc33`) reviewed exactly production evidence `30663562841-review-payload-v2`, batch `mb2-batch-000001-e32022126c07`: 979 approved, 0 excluded, and 21 additional-evidence Identifier candidates. Phase 116 matched that exact retained scope and classified the single collision group as a non-unique provider alias: `scryfallCardBackId:0aeebaf5-8c7d-4636-9e82-8c27447861f7` is shared across 820 distinct UUID-addressed physical coordinates and is never substituted for strict MTGJSON Printing identity.

The overlay totals are 1,000 approved, 0 excluded, 0 unresolved, 0 quarantined, and 0 fatal conflicts. Dependency closure is valid with no orphaned Printing. Decision `7a559f553e4b53c859efbdab542aefcb7e041170a55ace88d032c358e70cb23d` is `pending_operator_signature`; operator-signature readiness is true, promotion readiness is false. No MSH candidate or second MB2 batch was reviewed, no signature was invented, and no canonical write or promotion occurred. Architecture v12 and canonical contracts remain unchanged.

# Phase 115 status — first MB2 batch reviewed

Merged Phase 114A (`79a850d`) and evidence revision v2 / PR #90 (`16ba374`) are present. Repository
verification succeeds for `30663562841-review-payload-v2`, derived from production run
`30663562841`. Phase 115 used its retained payload bytes to review exactly batch
`mb2-batch-000001-e32022126c07`: 1,000 individual classifications comprise 979 approved, 0
excluded, and 21 requiring additional evidence for non-unique external identifiers. Dependency
closure passes. The immutable decision remains `awaiting_operator_signature`; promotion readiness
is false. No Marvel, second MB2 batch, canonical write, signature, or promotion is included.

## Phase 117 — First MB2 operator-authorization gate (2026-08-01)

Phase 115 reviewed the exact first MB2 batch and Phase 116 resolved its 21 identifier findings,
leaving 1,000 approved candidates (384 Cards, 379 Printings, 235 Identifiers, 2 Finishes) with
valid dependency closure and no MSH candidates. Phase 117 reverified that complete immutable
chain and retained a deterministic signature request, authorization contract, verification, and
promotion-readiness report under `data/reviews/phase-117/mb2-batch-000001-e32022126c07/`.
A human must supply identity, role, durable review reference, RFC 3339 review time, one allowed
decision, notes, and matching request/batch/candidate digests. No authorization exists and
promotion readiness is false. Authorization and promotion remain separate; no canonical write or
promotion occurred. Architecture v12 and canonical contracts are unchanged.
