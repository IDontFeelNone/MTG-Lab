# Knowledge Acquisition Pipeline v1

> **Phase 84 / Architecture v12 compatible.** This layer prepares evidence-backed
> candidates for human review. It cannot write canonical storage or promote facts.

## Pre-implementation assessment and compatibility review

Phase 82 already supplied immutable checksum-addressed snapshots, provider adapters,
normalized source records, candidate assertions, resumable run records, and explicit CLI
stages. The missing boundary was a deterministic, complete artifact that a reviewer could
approve. Phase 84 adds that boundary rather than changing the frozen architecture.

The design preserves the Constitution: raw bytes remain immutable; unknowns and conflicts
are retained; normalization does not establish truth; validation and review are explicit;
and no dependency on a canonical repository or promotion service exists. Provider-specific
retrieval stays in adapters while trust is configured separately. No Architecture v12,
canonical schema, canonical record, MB2 population, Simulation, Intelligence Engine,
market analysis, or recommendation behavior changes.

## Staged architecture

```text
External dataset -> Raw snapshot -> Normalized records -> Candidate assertions
                 -> Validation -> Review package + reports -> [future promotion]
```

Every stage is independently serializable and retryable. A snapshot hash anchors lineage.
Normalization retains unmapped fields. Assertions remain `candidate`. Validation runs
before package construction and fails closed on structural, identity, duplication,
source-identifier, provenance, or normalized-record errors.

## Provider policies

`provider-policy-v1` is data, not adapter code. It declares provider identity, evidence
class, default confidence, licensing constraints, required attribution, allowed entity
types, and normalization rules. A representative fixture policy is:

```json
{"provider_id":"fixture","evidence_class":"authoritative_structured","confidence_default":0.8,"license_constraints":["test-only"],"attribution":"Offline reviewed fixture created for MTG Lab tests","allowed_entity_types":["card","printing"],"normalization_rules":{"faces":"preserve-order"},"schema_version":"provider-policy-v1"}
```

Policy reputation never substitutes for evidence or review.

## Dataset identity

`dataset-identity-v1` records the provider dataset ID, acquisition version, publication
date (including explicit unknown), SHA-256 snapshot hash, and a logical identity computed
from their canonical JSON representation. Identical inputs therefore yield the same
identity on repeated imports; changed bytes or version metadata yield a new identity.

## Review lifecycle and package

The deterministic `knowledge-review-package-v1` contains the acquisition run, snapshot
lineage, provider policy, schema version, sorted candidate assertions, conflicts, changed
values, unknowns, warnings, completeness metrics, evidence summary, machine-readable
reports, and a conservative recommendation. Its ID is a SHA-256 digest of the entire
unsigned package. Any missing or changed member invalidates the ID.

Example (abridged):

```json
{
  "schema_version": "knowledge-review-package-v1",
  "review_package_id": "review-<sha256>",
  "promotion_recommendation": "hold",
  "detected_conflicts": {"count": 1, "conflicts": []},
  "unknown_values": {"count": 2, "unknowns": []},
  "completeness_metrics": {"total_fields": 10, "known_fields": 9, "unknown_fields": 1, "known_ratio": 0.9}
}
```

`hold` is emitted if conflicts, unknown/unmapped values, or validation warnings exist.
`eligible_for_human_review` does not approve promotion; it only indicates that these
automated reasons to hold are absent. Canonical promotion is a future milestone and must
consume an explicit human decision through a separately approved boundary.

## Validation and reports

Validation covers schemas, identities and checksums, duplicate normalized entities,
conflicting source identifiers, provenance connections, normalized record shape, policy
entity constraints, assertion lineage, and review-package completeness/integrity.

`knowledge-pipeline-reports-v1` combines seven deterministic machine-readable sections:

```json
{"acquisition_summary":{"status":"succeeded","snapshot_count":1},"normalization_summary":{"record_count":3},"assertion_summary":{"candidate_count":12},"completeness_report":{"known_ratio":0.9166666666666666},"validation_report":{"valid":true},"conflict_report":{"count":0,"conflicts":[]},"unknown_field_report":{"count":2,"unknowns":[]}}
```

The complete artifact additionally records changed values. Reports sort unordered output
and include no wall-clock values, so identical inputs reproduce byte-for-byte output.

## CLI and resume workflow

The module entry point exposes the required stages:

```bash
python -m mtglab.acquisition acquire fixture reviewed-cards --fixture data/fixtures/knowledge/reviewed-cards.json --timestamp 2026-07-30T12:00:00Z
python -m mtglab.acquisition normalize SNAPSHOT --output normalized.json
python -m mtglab.acquisition assertions normalized.json --output assertions.json --timestamp 2026-07-30T12:00:00Z
python -m mtglab.acquisition review-package --run RUN --snapshots SNAPSHOTS --normalized NORMALIZED --assertions ASSERTIONS --policy POLICY --acquisition-version v1 --output review.json
python -m mtglab.acquisition reports --run RUN --snapshots SNAPSHOTS --normalized NORMALIZED --assertions ASSERTIONS --policy POLICY --output reports.json
```

After interruption, inspect the acquisition run's failures and immutable snapshot paths,
rerun only missing acquisition datasets, and resume normalization onward from the same
snapshot. Reusing the same snapshot and declared metadata reproduces dataset identities,
assertions, reports, and review package. Never edit an immutable artifact to resume.

## Offline fixture and raw-acquisition relationship

The small test-only collectible-card fixture contains a multifaced card, two distinguishable
printings, a null artist, unmapped review evidence, and policy evidence classes. Tests add a
contradictory candidate to exercise conflict reporting. It is not a canonical dataset and
does not attempt Mystery Booster 2 population. Phase 84 composes Phase 82 artifacts; it
does not replace or weaken the raw acquisition framework.
