# Private MTGJSON Importer and Authorization Reform V1

This additive private pathway imports manually supplied MTGJSON-v5-shaped releases
through the existing release reconciler. It reuses its bounded streaming decoder,
validator, Card/Printing identity mapper, SQLite conflict accounting, checkpoints
and candidate reports. It introduces no canonical database or admission authority.

## Proposed internal policy successor

Status: Owner-authorized implementation and proposed internal policy revision;
pending independent PM review and Owner merge approval. Architecture v13 and
Accepted Decision 017 are unchanged. No historical permission record, accepted
semantic decision, source receipt or `NOT_ESTABLISHED` disposition is rewritten.

The changed internal authority is the new trusted-host private import profile,
not an external license. Instead of requiring the legacy reconciler's combined
full-retention disposition for every private workflow, the profile requires
separate supported bases for:

1. Reading the complete identified artifact, including checksum reads.
2. Local parsing.
3. Temporary processing of mixed source content in the bounded worker.
4. Private retention of the original input for replay by its custodian.
5. Private retention of the explicitly defined factual projection.
6. Private candidate/research reports within that same projection.

The internal decision reference records the Owner's risk posture. It cannot
satisfy a missing external basis. `NOT_ESTABLISHED` is not a legal prohibition;
it is insufficient support for the requested operation in this profile. A
supported grant for one material scope or operation does not clear another.
Upstream website terms are not automatically inherited by downstream recipients.
Whether a contract applies, whether rights are needed for particular factual
data, and whether a published grant covers particular contributions must be
resolved in the actual host disposition, not inferred by this software.

Existing source-integrity, semantic review, canonical-admission and execution
requirements remain independent. Legacy callbacks remain supported for their
existing contracts; the new profile refuses them when they imply broader
retention. In particular it cannot authorize `prepare_set_candidates` or legacy
full-retention `reconcile_release` merely because an artifact hash matches.

## Source-use evidence and remaining real-source gate

Publisher references checked on November 22, 2026:

- [MTGJSON license](https://mtgjson.com/license/): MIT grant for covered material,
  with the complete copyright and permission notice preserved in covered copies.
- [MTGJSON FAQ](https://mtgjson.com/faq/): recommends AllPrintings, compressed
  downloads, local processing and checksum verification; identifies multiple
  upstream sources. This supports the publisher-side workflow, not a complete
  independent finding about underlying third-party rights.
- Existing operation/field evidence remains in
  [the retained permission contract](V13_LEGACY_PUBLIC_PERMISSION_CLOSURE.md).

No real AllPrintings source-use profile ships enabled. A publisher-controlled-only
MIT basis cannot cover complete mixed-input reads. An internal risk-policy basis
cannot substitute for permission or an applicable legal determination. Original
fixture authorship cannot authorize real provider content. A real-source host
must establish the actual scope from applicable permissions or a qualified
determination and independently review and pin the supporting evidence. There
is no dataset `approved` field, permission file loader or CLI override.

The demonstrated positive basis is original project authorship for the exact
project-authored fixture bytes. Tests are neither real catalog import evidence
nor legal clearance. No new external dataset is acquired by this milestone.

## Public Python API

Use the existing Python environment with `PYTHONPATH=src`. Call from an importable
main module on Linux, as required by the existing resource-limited spawn worker.

```python
from providers.mtgjson.private_import import import_private_release
from providers.mtgjson.private_policy import PrivateResearchProfile, SourceUseBasis

# reviewed_host_profile is constructed in trusted host code after independent
# review. Never deserialize a profile or its approval from the dataset itself.
if __name__ == '__main__':
    report = import_private_release(
        manually_selected_source, dedicated_private_workspace,
        profile=reviewed_host_profile,
        provenance=retained_acquisition_receipt, notice=retained_complete_notice,
    )
```

Construct a profile with `PrivateResearchProfile.for_release(release, ...)`.
`release` uses the existing closed provider/release/version/date/source-hash/
provenance-reference/notice-reference binding. Independently pin provenance and
notice SHA-256 values. Provide a tuple of immutable `SourceUseBasis` records:
reference, evidence digest, kind, material scope, operation tuple and disposition.
The profile identity binds these records and the exact retained-field inventory.

Kinds distinguish project authorship, publisher permission, qualified
determination and internal policy. Scopes distinguish complete artifact, factual
projection and publisher-controlled-only material. These are host findings,
not data-derived truths. Evidence hashes bind documents; they neither authenticate
issuers nor prove that their claims or legal conclusions are correct. This is a
small host integration contract, not a general reviewer-authentication framework.

The provenance control is bounded to 64 KiB and has exactly these fields:
`provider`, `release_id`, `version`, `date`, `artifact_sha256`, `source_url`,
`acquired_at` (UTC), and `acquisition_method` (`MANUALLY_SUPPLIED`). Release fields
must agree with the independently pinned host profile. Real-source URLs must use
the official HTTPS MTGJSON hosts; fixture URLs use `urn:mtglab:original:`. A URL
claim alone does not authenticate acquisition. The host must establish that origin
before pinning the receipt. The source hash is independently checked by the worker.

Source, provenance and notices must be owner-only ordinary files outside Git, with
no symlink ancestors. Workspaces remain owner-only, dedicated and outside Git.
No network access, automatic source copy, acquisition or export is implemented.
Retain the original source and applicable complete notices privately for replay.
The API cannot control independent copies made by the input custodian.

## Retention and report contract

The named projection `private-factual-v1` retains declared identity, name, printing
coordinates, layout/face relationships, colors, mana labels, type labels, numeric
characteristics, language, rarity and finish fields. Only `scryfallOracleId`,
`oracleId` and `scryfallId` identifier namespaces enter this projection. The exact
field lists appear in the profile receipt and owning policy module.

This is a field-scoped candidate projection, not a finding that every value is
true or that every field is legally unrestricted. Unknown values and unresolved
identity joins remain explicit. No characteristic is inferred from a name.

Rules text, printed/flavor text, rulings, foreign prose, market/EDHREC metadata,
purchase URLs, other provider identifiers and arbitrary unknown fields do not
reach SQLite or output artifacts. Filtering happens before the existing mapper;
its residual `unknown_fields` are removed before persistence. Full input partitions
can exist temporarily in memory under the separate temporary-processing grant
and the inherited memory/partition limits. No extra raw-source copy is made.

Original artifact, partition and row hashes bind the unfiltered evidence without
retaining its excluded values or arbitrary excluded field names. Omitted row-field
counts report limited coverage. Private duplicate detection compares original
row hashes: differing excluded text still withholds a duplicate Printing rather
than silently selecting a winner. A source variation is not a claim that a
particular retained factual field conflicts. Cross-set Card conflicts compare
only the retained assertion fields. Excluded mechanics remain unassessed.

The new output uses `private-mtgjson-import-report-v1` and deterministic canonical
JSON, retaining the owning reconciler's artifact inventory, candidate/conflict
counts and limits. `source_release.private_scope` binds the profile receipt and
retention version. Its authority is explicitly `HOST_DISPOSITION_NOT_EXTERNAL_LICENSE`.
The legacy API's default report bytes and retention semantics remain unchanged.

Source coverage, real-world catalog coverage and canonical admission remain
separate. Every output remains a private review candidate. Real-card execution
is `BLOCKED`; production activation and canonical admission are `NOT_PERFORMED`.

## Replay, refusals and validation

Re-run with the same source, controls, profile and limits. Existing interrupted
processing/checkpoint validation is reused; changing the authorization profile
cannot resume an old workspace. A new workspace yields the same deterministic
report. Measurements remain in the existing separate `last-run.json` receipt.
Source hash/version changes, checkpoint tampering, unsafe storage and exceeded
budgets retain the owning reconciler's structured refusals. Policy/control errors
raise `SourcePolicyError` with code `SOURCE_POLICY_REFUSAL`, without private paths
or source content in error messages. No interrupted calculation is a complete result.

Focused tests exercise the full original-fixture path, omissions across every
persisted artifact, conflicts and identity uncertainty, resume/replay, immutable
profiles, control tampering, operation-specific denials, retention escalation,
export/admission refusals and the unchanged legacy consumers. Historical evidence
and predecessor hashes remain protected by exact reversible compatibility tests.

No real-source import, legal clearance, canonical admission, semantic approval,
gameplay execution, hosted access, AI export or public dataset redistribution is
claimed. A subsequent real-source execution requires its own supported host
disposition; the software implementation alone does not authorize it.
