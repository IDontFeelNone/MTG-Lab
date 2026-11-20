# New-Set Ingestion Completeness and Candidate Preparation V1

This is a read-only, private review-candidate consumer, not a new importer,
provider, canonical database, source permission authority or snapshot activation.
It improves reproducible completeness accounting before human review.

## Supported public operation

```python
from ingestion.set_preparation import prepare_set_candidates, SetPreparationError
report = prepare_set_candidates(
    source_bytes, supplied_file_manifest, census_request,
    game="fixture-game", games_root=explicit_catalog_root,
    authorize_source=trusted_host_source_use_disposition,
)
```

No files are written. An operator may explicitly retain the returned report only
within the independently authorized private scope. No CLI permission-grant flag,
automatic persistence, default catalog, private-source discovery or public export
is provided. `SetPreparationError.as_dict()` is a structured whole-request refusal.

V1 uses the **existing supplied JSON record-list profile**, narrowed to a closed
`{"records": [...]}` envelope of canonical-shaped **v1 Card/Printing** rows.
It reuses `DatasetManifest`, `JsonAdapter`, `validate_document`,
`load_canonical_repository`, `load_card_repository`, `canonical_repository_bytes`
and `EntityResolver`. It neither calls promotion nor copies transaction logic.
The existing MTGJSON AllPrintings parser, mapper, streaming planner, quarantine
and execution queues remain unchanged. Their candidate envelopes are not silently
reinterpreted as this canonical-shaped input profile. General MTGJSON-to-canonical
conversion, multiface interpretation and automatic alias admission are not added.

## Input contracts

The supplied-file manifest is `external-dataset-manifest-v1`, using its existing
required provenance, attribution, date, license, version, data-file and checksum
fields. For this bounded profile, `schema_version` is
`supplied-canonical-records-v1`, `data_file` ends in `.json`, and
`expected_entity_types` is exactly `["card", "printing"]`. Unknown manifest fields
are refused. A license string is retained as a source assertion, not clearance.

Each source row has exactly:

* `id`: stable source-row identity.
* `entity_type`: `card` or `printing`.
* `normalized`: a record satisfying the existing v1 Card or Printing schema.
* `identifiers`: existing resolver namespaces, including a required exact
  `canonical_identifier` equal to the record's declared `id`. Other supported
  namespaces are `provider_identifier`, `external_identifiers` and
  `alternate_identifiers`, with bounded strings or lists.

Every candidate provenance source must match the manifest's logical identity.
No ID is inferred from a name. These explicit declarations support candidate
review; they do not independently prove a new Card identity. Card Oracle-ID
claims are compared for collisions with the selected catalog, not interpreted.
Aliases are scoped by Card/Printing kind before the existing resolver is called.
Unknown reference semantics are not converted into canonical identity edges.

The census request has exactly:

```json
{
  "schema_version": "set-candidate-preparation-input-v1",
  "set_code": "FJA",
  "inventory_reference": "original-authored-population-FJA",
  "expected_inventory": [
    {"entity_type": "card", "id": "shared-fixture-card"},
    {"entity_type": "printing", "id": "print-fja-0"}
  ]
}
```

The example is an abbreviated inventory structure, not a claim that those two
records constitute the complete fixture. The complete original examples are
[FJA](../tests/fixtures/set_preparation_v1/FJA.json) and
[FJB](../tests/fixtures/set_preparation_v1/FJB.json). Each contains two Cards and
two Printings: one reprint of an existing original synthetic Card and one new
original synthetic Card. The same implementation processes both codes.

`expected_inventory: null` explicitly means UNKNOWN. A supplied inventory is a
nonempty unique list of typed identities. No `complete=true` assertion is accepted.
It is a caller-declared census, not an authoritative real-world set inventory.
A source byte hash binds contents, not the truth of its claimed completeness.

V1 bounds: 2 MiB source, 16 KiB manifest, 2,000 source rows, 2,000 expected
identities, 128-character identifiers and 16 references per alias namespace.
Requests are versioned and closed; malformed JSON, duplicate JSON keys, nonfinite
numbers, altered checksums and unsupported profiles refuse without any writes.

## Three independent findings

1. **File coverage** accounts for every row by source index and exact content
   hash, including quarantine. It does not claim every row is valid.
2. **Declared completeness** compares observed typed identity multiplicities
   with the explicit expected inventory. Missing, unexpected and duplicate records
   remain visible. Absent inventories or unresolved identity/validation premises
   remain UNKNOWN; no missing records are fabricated.
3. **Canonical admission** is always NOT_PERFORMED with zero approvals. Neither
   complete file coverage nor complete declared membership changes that finding.

The deterministic `set-candidate-preparation-report-v1` binds source bytes,
manifest, request and the existing Card/Printing catalog byte identity. This is
not a full v13 release/snapshot identity. No external production snapshot is
activated and no new authority is created. Report identity covers all findings.
Source-row order remains provenance; identical bytes and inputs replay exactly.

Candidates are schema-validated, pending-review private records. The report's
`accepted_candidate_rows` means eligible for preparation only, never human
acceptance, semantic approval or canonical admission. Candidate status remains
population-review-required when inventory gaps exist, and partial/quarantined
when rows cannot safely be prepared.

Exact existing content is recognized as reuse; changed catalog content is a
conflict. Duplicate source-row or entity identities are quarantined. Ambiguous
alias claims use the owning resolver. Multifaced, absent or unsupported layouts remain
unresolved; this profile requires an explicit normal-layout declaration. A quarantined Card withholds its Printing dependencies. If a malformed
row cannot safely contribute identity claims, all candidate eligibility is withheld
rather than allowing hidden alias conflicts. Catalog drift refuses the report.
Diagnostics use bounded codes, not raw rejected source fields or private paths.

## Source-use and review gates

The default operation **refuses before source parsing**. `authorize_source` must
be trusted host code, outside untrusted requests/configuration. It receives exact
artifact, manifest and census-request bindings and the operation identity
`private-set-candidate-preparation-v1`. It must independently establish BOTH
local processing and private candidate/report retention for that exact operation.
A literal boolean in input JSON cannot install that host boundary.

This is a narrow composition hook, not an authentication service or new permission
framework. Code operators able to replace the host are inside the trust boundary.
No real-provider authorization integration or upstream permission change is supplied.
Tests use host code restricted to original synthetic bytes. That simulated test
scope cannot be retained as real provider clearance. Possession, local supply,
source attribution, existing downloads or recomputed hashes prove no rights.

Reports say HOST_AUTHORIZED_PRIVATE_OPERATION_ONLY and independently retain
licensing rights as NOT_ESTABLISHED_BY_THIS_REPORT. Publication and external AI
export are NOT_AUTHORIZED. Real operation requires a separately supported host
policy disposition; this milestone does not establish one. Human source, identity,
semantic and admission review remain independent. No source material is published
by the consumer, and all checked-in fixtures are newly authored fictional records.

## Research value and exclusions

A future authorized new-release workflow can identify omitted records, extra
records, conflicting identities and blocked prerequisites before human admission.
It can reproduce the evidence for review instead of mistaking import success for
complete set knowledge. Original synthetic demonstrations validate that workflow,
not actual ingestion of a newly released Magic set.

There is no autonomous release detection, provider acquisition, new source-use
permission, Oracle interpretation, semantic/role approval, synergy discovery,
notification, AI orchestration, pack collation, real-card execution, canonical
promotion or production snapshot activation. The Comprehensive Rules HOLD remains
unchanged. Historical ingestion behavior, source evidence and datasets are intact.
