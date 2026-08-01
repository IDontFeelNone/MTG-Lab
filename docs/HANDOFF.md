# Phase 117A handoff

After this implementation PR merges green, the human project owner should dispatch **MB2 operator authorization** with `dry_run: true`, supply genuine identity, role, durable namespaced reference, RFC 3339 timestamp, decision, and notes, and retain the immutable defaults. Inspect the uploaded verification reports. If valid, rerun byte-identical values with `dry_run: false`; review and merge the resulting authorization-only PR into `main`. Repository Settings > Actions > General may need permission for Actions to create PRs; if unavailable, use the reported pushed branch and commit to open it manually. Stop after the authorization PR: do not run canonical promotion.

# Phase 116 handoff

The exact 21 Phase 115 ambiguous Identifiers are resolved from retained evidence as shared `scryfallCardBackId` aliases, bringing the first MB2 batch to 1,000 approved evidence classifications with valid dependency closure and no exclusions, unresolved candidates, quarantines, fatal conflicts, or orphaned Printings. The seven Phase 116 overlay artifacts are immutable and Phase 115 remains byte-for-byte unchanged.

The next separately authorized gate is genuine operator signature metadata for decision `7a559f553e4b53c859efbdab542aefcb7e041170a55ace88d032c358e70cb23d`. Do not infer reviewer identity/reference/time, promote, write canonical state, review another MB2 batch, or review Marvel. Phase 116 itself performed none of those actions.

# Phase 115 handoff

The first retained MB2 batch has a complete candidate ledger: 979 approved, 0 excluded, and 21
requiring additional evidence for ambiguous external Identifier mappings. The exact retained v2
payload and dependency closure verified; no Marvel or second MB2 batch was inspected. Begin next
with the collision entries in `data/reviews/phase-115/mb2-batch-000001-e32022126c07/` and preserve
the immutable ledger/decision. Stop before operator signature and promotion unless separately
authorized. Canonical state is unchanged.

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

### Manual authorization command

Create a private/input JSON object containing all nine required human-entered fields, then run:

```bash
PYTHONPATH=src python scripts/authorize_mb2_batch.py /path/to/operator-input.json --data-root data
```

The command rereads the immutable request, replays the Phase 115/116 chain, verifies the current
canonical pre-state, validates the human fields, and writes
`operator-authorization.json` only if all checks pass. It never promotes or writes canonical data.
