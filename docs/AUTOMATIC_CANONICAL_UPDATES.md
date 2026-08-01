# Automatic Canonical Updates

> **Phase 120 · Architecture v12 compatible.** This orchestration composes existing evidence, review, promotion, query, and analytics boundaries. It changes no canonical contract or Tier 0 architecture.

## Standard lifecycle and safety

`AutomaticCanonicalUpdate` runs sixteen fixed, fail-closed stages: source acquisition verification; evidence normalization; permanent intake; exact target partitioning; bounded payload retention; complete review; policy-approved identifier/conflict resolution; dependency closure; readiness planning; deterministic preflight; atomic bounded promotion; immutable audit; post-state verification; query/analytics smoke tests; branch/PR persistence; and merge-eligibility verification. Every successful stage has a canonical-JSON digest and durable checkpoint. A failure stops later stages and retains `data/automatic_updates/<batch>/blocked-report.json`. Valid checkpoints resume; tampered checkpoints fail closed.

Promotion requires a configured trusted provider, verified hashes/inventories, exact isolation, only permitted final classifications, no unresolved/rejected/quarantined/fatal candidate, no unresolved identity conflict, valid closure and no orphan Printing, exact canonical pre-state, deterministic identities, and atomic state/audit/post-state success. Identical completed replay is idempotent; changed membership, audit, or state conflicts. Failed audit or verification restores original canonical bytes.

## Configuration and commands

Schema `automatic-canonical-update-v1` requires `game`, `target_code`, `target_name`, `trusted_provider`, `source_dataset_identity`, `source_artifact_or_workflow_run`, `evidence_identity`, `batch_identifier`, `candidate_digest`, `expected_target_isolation`, `promotion_policy`, `destination_branch`, and `base_branch`. Artifact paths, integrity expectations, trusted providers, classifications, and optional identity fields are data. A future set needs retained bounded evidence and a configuration—not engine changes.

`config/automatic_updates/mb2-first-batch.json` references completed Phase 119. Its audit makes execution an idempotent verification; it does not duplicate promotion. No second MB2 batch or MSH candidate is configured.

```bash
PYTHONPATH=src python scripts/automatic_canonical_update.py plan --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py verify --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py execute --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py status --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py replay --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py rollback-plan --config CONFIG
```

All output is JSON. Only explicit `execute` writes. `rollback-plan` never executes destructive work. Routine updates require no signature, authorization form, supplied timestamp, or hand-calculated digest.

## Automatic PR, merge, recovery, and settings

The Actions workflow executes the exact configuration, runs unittest/compile/integrity checks, verifies the changed-file allowlist, pushes a dedicated branch without force, and creates or safely reuses its exact-head/base PR. It independently verifies head, base, audit/boundary, then requests auto-merge. Required checks and branch protection remain authoritative; there is no admin bypass or force merge. Branches and always-uploaded diagnostics remain if setup fails.

Administrators must enable **Allow GitHub Actions to create and approve pull requests**, Actions `contents: write` and `pull-requests: write`, repository auto-merge, and squash merge. Protect `main`, require this repository's CI checks and current branch, and disallow force pushes/protection bypass.

Humans intervene only for genuine conflicts, ambiguous/unsupported source data, validation failure, canonical drift, architecture/contract changes, destructive work, rollback, or a blocked report. Correct source/configuration and rerun to resume verified stages. Rollback requires review of `rollback-plan`, a separately invoked audited change, the full suite, and the protected PR path. After merge, configure the next trusted dataset, dispatch the workflow, monitor checks, and let GitHub merge when green. Never reuse a completed batch identity for different content.

## Phase 121 synthetic production-readiness result

The retained fixture `tests/fixtures/phase_121_synthetic/` describes synthetic Magic set
`SYN` under the same `automatic-canonical-update-v1` contract and engine used by the MB2
reference. Its deterministic eight-candidate order is: one Set identity, two Cards, two
Printings, one Identifier, and foil/nonfoil Finishes. Every candidate has an exact synthetic
source locator; null release date and oracle text are paired with explicit unknown-state
fields. Both Printings close over retained Cards. The trusted provider, evidence and dataset
identities, source/payload hashes, exact inventory, identity fields, policy, and deterministic
branch are configuration data. Tests copy the fixture to a temporary root; synthetic bytes,
audits, checkpoints, and promoted state never enter production `data/`.

All stages returned `succeeded`, in registry order: (1) source authenticated and trusted;
(2) eight ordered candidates and payload checksum verified; (3) evidence retained; (4) exact
`SYN` partition confirmed; (5) bounded payload authenticated; (6) eight of eight reviewed and
approved; (7) deterministic identifier policy found zero unresolved conflicts; (8) zero
orphan Printings; (9) readiness true; (10) empty isolated pre-state matched; (11) eight
entities promoted atomically; (12) audit digest verified; (13) post-state digest
`47abe0658ad434f6485148592559a973a6f8f14694455a89cb0cb29b5b8e9327` verified; (14) isolated
entity counts were 2 Cards, 2 Printings, 1 Identifier, 2 Finishes, and 1 Set; (15) deterministic
branch/PR plan emitted; and (16) protected auto-merge policy emitted.

An interruption after stage eight resumed without changing completed checkpoint bytes. A
completed replay made no canonical change; altered batch/audit/state replay failed closed.
The rollback command emitted a non-executing, human-decision-required plan retaining the
audit. `plan`, `verify`, `execute`, `status`, `replay`, and `rollback-plan` all returned stable
JSON identities. Deterministic tests reject untrusted provider, contamination, missing or
duplicate inventory, unresolved/quarantined review, conflicting identity, orphan Printing,
payload checksum mismatch, pre-state drift, checkpoint/audit alteration, interrupted and
conflicting replay, mismatched PRs, non-green checks, and any force/admin path.

The engine source contains neither `MB2` nor `MSH`; no target-code/name condition was added.
The workflow takes its dedicated branch from the descriptor, reuses only an identical remote
branch/PR, validates head/base/boundary and required green checks, then requests protected
auto-merge without force or admin bypass. Diagnostics remain always retained. Before a real
future set, the remaining blockers are trusted terms-compliant evidence, full review, an
approved bounded descriptor/current pre-state, and verified GitHub repository settings. A
real update requires a later phase and normal protected review.
