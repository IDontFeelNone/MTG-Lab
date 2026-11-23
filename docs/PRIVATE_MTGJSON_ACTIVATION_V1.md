# Private MTGJSON Real-Source Activation V1

This local workflow prepares private input controls and invokes the existing
[private importer](PRIVATE_MTGJSON_IMPORT_V1.md). It adds no importer, permission
registry, approval-file loader, network acquisition or canonical authority.
Architecture v13, Accepted Decision 017 and historical permission records remain
unchanged. A prepared request is not source-use authorization.

## Private directory layout

Use the existing Linux Python environment and `PYTHONPATH=src`. Keep inputs,
trusted host code, evidence and results outside every Git checkout. For example:

```text
owner-private/
  inputs/AllPrintings.json.gz       # manually selected original, not copied by the workflow
  inputs/notice.txt                 # complete applicable notice, independently verified
  review/source-use-review.txt      # actual reviewed evidence, not an approval flag
  request.json                     # an untrusted request until reviewed independently
  host.py                          # Owner-controlled code; never selected by the request
  activation/                      # created owner-only by the workflow
    activation-plan.json
    provenance.json
    notice.txt
    candidates/                    # existing reconciler's bounded workspace/results
```

Make input, request and evidence files owner-only (`chmod 600`) and their private
directories owner-only (`chmod 700`). Do not move actual source files, legal
review documents or private results into public GitHub, CI or an AI conversation.
Only original project-authored data is used in public automated tests.

## 1. Prepare an untrusted, version-pinned request

Manually select one official release and its matching published checksum. The
checksum must describe the actual compressed or uncompressed artifact selected,
not a filename or a checksum for another representation. Retain acquisition
provenance, release version/date, and the complete applicable copyright/permission
notice. Establish origin independently before pinning the request. An official
URL entered into a form is not proof of acquisition or permission.

Use independently established release metadata. This command does not open the
dataset to discover its version or compute its checksum. In particular, it does
not perform an unapproved whole-file read as a prerequisite to obtaining approval.

From the repository's existing Python environment:

```sh
umask 077
PYTHONPATH=src python -B -m providers.mtgjson.private_activation plan \
  --release-id YOUR_RELEASE_ID \
  --version YOUR_EXACT_VERSION \
  --date YOUR_RELEASE_DATE \
  --source-sha256 YOUR_INDEPENDENTLY_VERIFIED_ARTIFACT_SHA256 \
  --source-url https://mtgjson.com/api/v5/AllPrintings.json.gz \
  --acquired-at YOUR_ACTUAL_UTC_ACQUISITION_TIMESTAMP \
  --notice-sha256 YOUR_INDEPENDENTLY_VERIFIED_NOTICE_SHA256 \
  --provenance-reference YOUR_ACQUISITION_REFERENCE \
  --notice-reference YOUR_NOTICE_REFERENCE \
  > /absolute/owner-private/request.json
```

Replace every placeholder; neither the example URL nor a mutable download URL
proves a historical release identity. No download occurs. The request contains
no private filesystem paths and uses the closed
`private-mtgjson-activation-plan-v1` contract. Its content identity is `plan_id`.
The authority field remains `UNREVIEWED_REQUEST_NOT_AUTHORIZATION`.

Inspect the saved request without reading a dataset:

```sh
PYTHONPATH=src python -B -m providers.mtgjson.private_activation inspect \
  /absolute/owner-private/request.json
```

Inspection validates structure and identity, not source integrity, completeness,
legal support or approval. Unknown fields such as `authorized=true`, alternative
retention profiles, omitted operations and export flags reject. There is no CLI
`approve`, `run --authorized`, or `--host-module` executable-loading mechanism.

## 2. Independently review the actual operations

The existing policy requires support for all operations the importer performs:

- `WHOLE_ARTIFACT_READ`, including checksum reads before and after processing.
- `LOCAL_PARSE` of the complete selected artifact.
- `TEMPORARY_MIXED_PROCESSING` in the bounded worker.
- `PRIVATE_SOURCE_RETENTION` by the custodian for replay.
- `PRIVATE_FACTUAL_RETENTION` of the fixed `private-factual-v1` projection.
- `PRIVATE_REPORTS` within that same projection.

The Owner's trusted local code must supply the reviewed plan identity separately
from the incoming request. Never automatically assign `expected_plan_id` from a
newly loaded request. A coherently rehashed modified request must not inherit an
old decision. A source-use reviewer must consider the actual release, fields,
operations, conditions and intended private use, including resale-related use
where relevant; private does not automatically mean noncommercial.

Use existing immutable `SourceUseBasis` records. Keep each reviewed evidence
document at a selected private path and independently pin its exact SHA-256 in
host code. A document's own approval claims are not consumed. The workflow checks
those bytes on every invocation; the host is responsible for independently
establishing issuer/authenticity, applicability, conditions and current validity.
A hash alone establishes none of those things. This is the existing trusted-host
boundary, not a new reviewer-authentication or legal-determination service.

Material scopes and grant kinds retain their existing meanings. Separate bases
may cover complete-input reads and factual-projection retention. A supported
publisher-controlled-only grant cannot clear a mixed artifact. An applicable
express restriction blocks a broader grant. Internal risk acceptance cannot
manufacture external rights, and original fixture authorship cannot authorize a
real release. `NOT_ESTABLISHED` means insufficient support for the requested
operation, not a legal finding that it is prohibited.

## 3. Invoke from trusted host code

The following is a host integration template, not an approval or a ready-enabled
real-source profile. Supply the actual reviewed constants and documents; do not
invent the example qualified determination. The host file remains private and
is explicitly run by the Owner, never loaded from an imported plan or dataset.

```python
from pathlib import Path
from providers.mtgjson.private_activation import load_activation_plan, activate_private_release
from providers.mtgjson.private_policy import SourceUseBasis, OPERATIONS, canonical

ROOT = Path('/absolute/owner-private')
REVIEWED_PLAN_ID = 'sha256:REPLACE_WITH_INDEPENDENTLY_REVIEWED_PLAN_HASH'

# This example applies only IF a genuine independently reviewed determination
# supports every listed operation for the exact mixed artifact. Otherwise use
# the actual narrower bases and expect the existing policy to refuse gaps.
BASES = (SourceUseBasis(
    reference='YOUR_ACTUAL_REVIEW_REFERENCE',
    sha256='REPLACE_WITH_INDEPENDENTLY_PINNED_REVIEW_DOCUMENT_SHA256',
    kind='QUALIFIED_DETERMINATION', material_scope='COMPLETE_ARTIFACT',
    operations=OPERATIONS, disposition='SUPPORTED',
),)

if __name__ == '__main__':
    report = activate_private_release(
        load_activation_plan(ROOT/'request.json'),
        ROOT/'inputs/AllPrintings.json.gz', ROOT/'activation',
        expected_plan_id=REVIEWED_PLAN_ID,
        reviewed_bases=BASES,
        basis_files={'YOUR_ACTUAL_REVIEW_REFERENCE': ROOT/'review/source-use-review.txt'},
        internal_decision_reference='YOUR_INTERNAL_RISK_DECISION_REFERENCE',
        material='MIXED_MTGJSON_RELEASE', notice=ROOT/'inputs/notice.txt',
    )
    print(canonical(report))
```

Run the explicitly selected host file with the existing environment. Redirect
its returned report to an explicitly chosen private file if desired:

```sh
PYTHONPATH=/absolute/MTG-Lab/src python -B /absolute/owner-private/host.py \
  > /absolute/owner-private/latest-report.json
```

There is no real-source grant built into this template or module. If only the
existing publisher-layer evidence is available, use its actual restricted scope;
the workflow refuses before source or evidence reads/writes when the requested
operations lack support. Missing evidence is not resolved by entering `SUPPORTED`
in code: that state must describe the independently established host finding.

## What preparation and execution verify

After matching the independently reviewed plan ID, the workflow constructs the
existing `PrivateResearchProfile` and applies its operation checks. It then
verifies every selected basis document and the complete notice against independent
host pins. It rejects missing/extra evidence files, unsafe storage and symlinks.
Evidence documents are data, including any executable-looking text they contain.

It creates only three fixed private controls: the exact reviewed plan, generated
closed provenance, and byte-identical notice. Existing controls must match exactly;
they are not silently overwritten. An interrupted partial control write refuses
on replay; use a separately chosen fresh private directory or restore exact known
controls after review. No general persistence/recovery system is introduced.

The workflow then invokes `import_private_release`, which delegates source hash
verification, version/date matching, parsing, projection, identity reconciliation,
resource limits and candidate reporting to the existing bounded worker. Preparation
alone does not verify the source checksum. A checksum failure cannot produce a
new complete candidate report. The original source is never copied by activation.
Keep it and the supporting documents privately for replay.

The returned native `private-mtgjson-import-report-v1` is preserved without a new
parallel report or authority format. It binds release, provenance/notice hashes,
profile, evidence references and output artifact hashes. Its profile can be
reconstructed from the saved plan and the independent host inputs. Source coverage,
real-world catalog completeness and canonical admission remain separate.

## Replay, limits and remaining real-source prerequisite

Re-run the same host program with the same files, plan, reviewed pins and limits.
The controls are idempotent and evidence/notice hashes are rechecked. Pass existing
`limits` and `stop_after_partitions` keyword arguments when a bounded pause/resume
is appropriate; the existing checkpoint engine owns resume verification. Changed
source, evidence, plan, controls or profile cannot silently become the old result.
Old reports remain historical when a new invocation refuses.

Original-fixture tests exercise plan CLI/API parity, real profile construction,
native import parity, notices, split operation grants, conflicts, exclusions,
pause/replay and tampering. They establish software behavior only. No appropriately
supported real release is supplied or activated by this implementation.

Existing [MTGJSON MIT permission](https://mtgjson.com/license/) and
[download/local-processing guidance](https://mtgjson.com/faq/) support covered
publisher material and the intended acquisition method. The retained mixed-content
whole-read/retention questions are unchanged. No qualified determination or new
third-party permission is fabricated and no historical permission flags change.

For real execution, the concrete missing basis is a supported determination for
the complete selected artifact's reads, temporary mixed processing and necessary
private retention, alongside support for the retained factual fields/reports.
One Owner action is to supply that operation-specific reviewed source-use packet
for the selected release, so its exact plan and evidence digests can be pinned in
trusted host code. Contacting any particular publisher is not automatically
required; applicable existing rights and law may provide the necessary basis.

No canonical admission, production snapshot activation, current Oracle verification,
real-card gameplay, public redistribution, external AI export, hosted third-party
access or autonomous acquisition is authorized or implemented by this workflow.
