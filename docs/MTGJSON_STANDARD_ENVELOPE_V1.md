# MTGJSON Standard export envelope compatibility V1

This bounded compatibility extension supports the official format-specific
Standard JSON envelope. It does not acquire data, grant source-use permission,
or establish Standard legality. Real-source continuation requires separate Owner
execution approval after review and merge. No real dataset is used in tests.

## Publisher evidence

At immutable publisher commit
`219405c1b5417082cf8582f82fb853b805587f45` (2026-11-23),
[FormatPrintingsFile](https://github.com/mtgjson/mtgjson/blob/219405c1b5417082cf8582f82fb853b805587f45/mtgjson5/models/files.py#L200-L238)
declares `format_name` and uses it for format-specific filtering.
The [file writer](https://github.com/mtgjson/mtgjson/blob/219405c1b5417082cf8582f82fb853b805587f45/mtgjson5/models/base.py#L412-L437)
writes `meta`, `data`, and then additional model fields. The general website file
overview does not show this additional property.

The predecessor's closed `meta`/`data` guard therefore rejects a format-specific
export after committing its set partitions. Observing that refusal does not
validate the remaining real source envelope or its `format_name` value.

## Explicit trusted-host source contract

Existing APIs gain only an optional `source_contract` keyword. Its default is
`None`: historical envelopes, errors, source-use profiles, activation plans,
outputs and checkpoint bindings keep their original behavior and identities.
The existing streaming reader, mapper, source-policy checks, worker limits and
factual publication are reused.

```python
from providers.mtgjson.reconciliation import StandardExportContract

# profile is constructed by existing reviewed trusted-host code for the exact
# release, provenance, notice and operation-specific evidence. This factory
# verifies support; it neither loads authorization from data nor creates rights.
contract = StandardExportContract.for_profile(profile)
contract_receipt = contract.receipt()  # Independently inspect/pin outside Git.

# Supply source_contract=contract to the existing import_private_release or
# activate_private_release call. Keep the existing expected plan/profile pins.
```

The versioned `mtgjson-standard-export-envelope-v1` receipt binds the complete
release declaration, exact supported factual source-use profile identity,
required section order, expected literal `standard`, and metadata byte bound.
It is a host-selected validation constraint. Do not select it from a filename,
URL substring, incoming `format_name`, or an imported authorization assertion.
Keep its receipt and the tested code identity with private execution controls,
outside the dedicated activation directory and rebuildable candidate workspace.

The selected contract requires exactly one each of `meta`, `data`, `format_name`,
in that publisher-supported order. Its format value must be a JSON string equal
to `standard`. The encoded string token is bounded to 64 UTF-8 bytes before
decoding; JSON escapes are supported. Missing metadata, other formats, invalid
types, duplicates, unknown keys, malformed JSON and trailing content refuse.
The default still refuses `format_name`. No general format registry is added.

Only factual private profiles support this extension. Oracle evidence profiles
and their separate retention/inspection authorization remain unchanged.
`format_name` is never added to the factual field allowlist, Card/Printing rows,
mechanical evidence, reviewed interpretations, canonical facts or gameplay.
All five limited-retention operations remain independently required.

## Recovery and historical compatibility

The new constraint is checked on every invocation against the exact release and
profile. It does not rewrite activation plans, receipts, SQLite binding payloads,
schemas, historical report identities or output bytes. The original artifact
hash already binds the entire envelope, including its metadata. No serialized
plan or checkpoint silently opts into the new constraint.

Synthetic tests execute the byte-exact reconstructed predecessor worker, pause
after one partition, continue until its envelope refusal after 22 committed
partitions, and then resume with the explicit new contract. Existing checks
recompute and compare every committed partition hash, row and factual assertion.
The completed report and every publication artifact must equal a clean import
byte-for-byte. Changed sources, bindings, partitions, rows or assertions refuse.
No parser-version field is invented in old checkpoints: the exact predecessor
and repaired-code equivalence tests supply compatibility evidence.

After merge and separate execution approval, a trusted host can reconstruct the
existing exact profile from its unchanged reviewed evidence, create and pin this
contract separately, and pass it to the unchanged activation-plan invocation.
Use the same original artifact, capsule, provenance, notice, profile and limits.
Do not migrate the checkpoint or suppress mismatches. If revalidation refuses,
stop and preserve the original checkpoint for review.

The actual private checkpoint and source are not resumed or parsed during this
implementation. Synthetic recovery evidence supports a later attempt; it does
not guarantee that the unvalidated remainder of the real archive will pass.

## Limits and authority

All existing resource ceilings remain unchanged. The additional scalar bound
does not raise the 8 MiB partition, 64 KiB record, 512 MiB worker, 60-second CPU
or 70-second wall limits. Synthetic performance is not release-scale assurance.

Factual limited retention still requires durable validated publication before
cleanup eligibility. No source is automatically deleted. Complete replay and
incomplete-checkpoint recovery require the exact original artifact. Retained
derivative verification remains distinct from full source replay.

This repair does not change Architecture v13, Decision 017, source-use
dispositions, canonical admission, semantic authority, gameplay execution,
Oracle retention, external AI export or production activation.
