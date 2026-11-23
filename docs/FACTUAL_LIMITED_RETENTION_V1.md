# Factual Limited-Retention Compatibility V1

The existing private importer now supports an explicitly selected factual
limited-retention lifecycle. This changes custody requirements, not source rights,
canonical admission, semantic authority or gameplay permissions. Real MTGJSON
processing remains on HOLD; all public demonstrations use original authored data.

## Select the lifecycle

Default calls remain `retention_profile='private-factual-v1'` and
`retention_mode='retained-source'`. Their existing V1 receipts, activation plans,
reports and deterministic identities are unchanged. No old plan is reinterpreted.

In independently reviewed trusted-host Python code, construct the existing
`PrivateResearchProfile.for_release(..., retention_mode='limited-retention')`.
Keep the factual retention profile. Invoke `import_private_release` as before.
Alternatively, prepare the existing activation request with
`plan_private_activation(..., retention_mode='limited-retention')`, independently
review/pin its plan identity, then use `activate_private_release` as before.
The planning CLI accepts `--retention-mode limited-retention`; it grants no rights
and does not execute an import. Existing acquisition and control requirements apply.

Limited factual receipts use `private-mtgjson-source-profile-v2`; limited activation
plans use `private-mtgjson-activation-plan-v2`. These closed additive contracts bind
the explicit mode and five requested operations. Limited import reports use
`private-mtgjson-factual-limited-report-v1`, with explicit replay limitations.
Historical retained-source V1 schemas are unchanged.

## Required operation-specific support

Each actual operation still needs independently supported evidence:

- `WHOLE_ARTIFACT_READ`
- `LOCAL_PARSE`
- `TEMPORARY_MIXED_PROCESSING`
- `PRIVATE_FACTUAL_RETENTION`
- `PRIVATE_REPORTS`

`PRIVATE_SOURCE_RETENTION` remains mandatory for retained-source mode; it is not
requested in limited mode. Selecting limited mode is not authorization. Publisher
permissions cover only their supported material scope; internal risk acceptance,
fixture authorship relabeled as real data, missing evidence and approval flags
cannot supply external rights. Applicable express restrictions still refuse.

The existing factual allowlist, source SHA-256/version checks, manual acquisition
URL/time, exact notice/provenance pins, identity resolution, conflict withholding,
streaming worker, checkpoint bindings and resource ceilings are retained. Oracle
text, rulings, artwork, flavor text, marketplace metadata and arbitrary unsupported
fields are not retained by this projection. Both Oracle projection lifecycles
remain independently gated and unchanged.

Keep the selected provenance and notice inputs outside the rebuildable candidate
workspace until import/publication completes. A limited import refuses controls
inside that workspace without replacing them. The existing activation workflow
already keeps its pinned controls outside `candidates/`.

## Completion, publication and cleanup

These are separate states:

1. **Source validation:** the worker checks the selected original artifact's exact
   hash before processing and again before completion, plus source version/date.
2. **Import completion:** every partition is accounted for, outputs are generated
   under the existing budgets and the deterministic report is produced.
3. **Safe publication:** under the same workspace lock, the importer verifies
   the independently pinned report and every artifact's hash/byte/row counts,
   retains the exact pinned provenance and complete notice in `output/`, syncs
   files and the directory ancestry, and publishes `output/publication.json` last.
4. **Custodian cleanup:** the publication receipt declares cleanup eligibility,
   not deletion authority or completion. The authorized custodian may remove its
   original only under a separately explicit custody/cleanup decision.

There is no automatic deletion API, source copy, path-based cleanup request or
new ownership framework. The caller-owned original always remains untouched.
Publication failure raises without reporting successful import publication to the
caller. Completed factual output may remain recoverable; keep the original and
retry with the same controls/profile/limits. Partial controls and temporary marker
files are recognized only within the limited factual workspace and are rebuilt
on retry. No failed or paused import receives a cleanup-eligible return value.

If custodian deletion fails, the published factual results remain valid and the
original remains available. A cleanup failure must not be interpreted as a failed
calculation or silently change a published result.

## Verify retained evidence and replay accurately

Independently retain the successful import's `report_id` and trusted host profile.
Do not take a report ID from newly received untrusted output as its own trust pin.

```python
from providers.mtgjson.factual_retention import verify_factual_publication

receipt = verify_factual_publication(
    workspace, profile=reviewed_profile,
    expected_report_id=independently_retained_report_id,
)
```

Verification needs no source reads. It rechecks the closed report, profile/release,
all derivative artifact hashes/counts, retained provenance/notice and publication
receipt, enforces budgets/private paths, and re-establishes durability barriers.
The receipt is deterministic and contains no private storage paths. Hashes bind
evidence; they are neither a permission determination nor canonical admission.

After authorized cleanup, derived verification remains possible from these pins.
Complete source replay is **unavailable without the exact original artifact**.
Incomplete checkpoint recovery also requires that original. Re-running an import
without it refuses; retained hashes cannot recreate excluded content. With the
original restored, unchanged checkpoints and host bindings can resume normally.
Changing lifecycle/profile cannot reuse an old checkpoint's authority.

Factual derivatives remain review candidates. Catalog completeness is not
established, canonical admission/production activation are not performed,
semantic authority is not established and real-card execution remains blocked.
No AI export, source-use expansion or new acquisition is authorized.
