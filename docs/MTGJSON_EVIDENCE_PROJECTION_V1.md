# MTGJSON Evidence Projection and Card Intelligence Handoff V1

This optional private projection supplies literal, unadmitted evidence to the
existing `MechanicalCardIntelligence` consumer. The importer extracts evidence;
it does not interpret abilities, classify roles, decide legality or run gameplay.
Architecture v13, Accepted Decision 017, canonical admission and historical
source-use dispositions remain unchanged. No real dataset is acquired or cleared.

## Supported interfaces and authority

The existing mechanical dossier interface requires an admitted production Card
cohort and a verified Scryfall-shaped acquisition, including its full source
closure. It cannot safely represent a private MTGJSON candidate as an admitted
dossier. Manufacturing that acquisition or feeding candidates to `dossier()` would
misrepresent provenance and authority.

The smallest additive remedy is the separate
`MechanicalCardIntelligence.inspect_mtgjson_candidate(...)` method. It uses an
existing verified `CanonicalQueryEngine` attachment and the owning MTGJSON evidence
reader. It never initializes the Scryfall reader, populates admitted dossiers,
changes the catalog, or admits mechanical knowledge. The method requires exact
current canonical Card/Printing identities and their existing relationship; new
import candidates cannot create those identities themselves. No name fallback,
Printing substitution, or production attachment capability is added.

## Private importer selection

Continue using `import_private_release` with the existing trusted-host
`PrivateResearchProfile` and `SourceUseBasis` contracts. The default
`private-factual-v1`, its schema, receipt serialization and results are unchanged.
The existing activation-plan CLI remains factual-only and cannot grant text scope.

To request text, explicitly construct the profile with
`retention_profile='private-oracle-evidence-v1'` and a `retention_mode` described
below. Supply independently reviewed, release-bound bases for the actual complete
reads, local parsing, temporary mixed processing, retained factual fields and
private reports. Text requires the additional
`PRIVATE_ORACLE_EVIDENCE_RETENTION` operation, covered by `COMPLETE_ARTIFACT` or
`ORACLE_PROJECTION`; a factual-only scope cannot grant it. Private inspection also
requires `PRIVATE_ORACLE_EVIDENCE_INSPECTION`. Oracle-bearing reports require an
Oracle-capable scope for `PRIVATE_REPORTS`. Publisher-controlled-only grants,
internal risk acceptance, source integrity and arbitrary approval flags cannot
satisfy missing rights. Real releases reject project-fixture authorship as a basis.

No positive real-source profile is shipped. Real-source execution remains gated
by the existing independent source-use determination. The public tests use only
original authored data; they establish behavior, not real MTGJSON permission.

## Evidence and integrity contract

The existing bounded parser, validator, mapper, disk-backed assertion comparison,
checkpoint engine and output writer produce the native
`private-mtgjson-oracle-import-report-v1`. Its independently retained `report_id`
binds artifact hashes, release/version/date, exact original artifact hash,
provenance, notice, scoped host profile and resource limits.

`oracle-evidence.jsonl` contains `mtgjson-candidate-oracle-evidence-v1` source
occurrences with:

- Exact provider Card reference and Printing UUID, without identity-by-name.
- Exact supplied `text` value, its field name and JSON pointer.
- Whole-card or explicit face boundaries; no inherited text from another face.
- Release, partition and row integrity references, provenance and notice hashes.
- Source-use profile identity, missing/unsupported states and withheld conditions.
- Explicit unadmitted status, unestablished semantics and blocked execution.

Only `text` is supported. `oracle_text`, printed/flavor text, rulings, foreign
prose and arbitrary extra fields are not alternative text inputs and are not
retained. Empty supplied text differs from missing/null text. Invalid text types
remain unsupported without retaining the invalid value. Multiface rows need
explicit side, face name and related Printing identifiers; exceptional records
remain review-required. Missing or incompatible face relationships stay unresolved.
No text is interpreted, normalized into instructions, or certified as current Oracle.

Every occurrence is preserved. Cross-set text assertions are compared through the
existing assertion engine. Contradictory Card assertions, duplicate/conflicting
Printings, conflicting external identifiers and exceptional records are withheld;
the reader never selects a supposed authoritative winner. Inspection can display
these source assertions with their conditions, not as accepted mechanics.

The reader requires an independently pinned report identity and the matching host
profile. Do not obtain those pins from newly received untrusted output. It verifies
the report and streamed evidence artifact before returning any text, rechecks the
catalog attachment, and does not read the original dataset. Hashes establish
integrity bindings, not issuer authenticity or external rights.

## API example (private, explicit invocation)

```python
from providers.mtgjson.private_import import import_private_release
from card_intelligence import MechanicalCardIntelligence

if __name__ == '__main__':
    # reviewed_profile is independently supported for the requested Oracle scope.
    # verified_query comes from an existing verified immutable catalog attachment.
    report = import_private_release(source, workspace, profile=reviewed_profile,
                                    provenance=provenance, notice=notice)
    inspection = MechanicalCardIntelligence.inspect_mtgjson_candidate(
        verified_query, expected_query_snapshot_id=independently_pinned_snapshot,
        card_id=exact_existing_card_id, printing_id=exact_existing_printing_id,
        evidence_directory=workspace / 'output', profile=reviewed_profile,
        expected_report_id=report['report_id'])
```

Store the successful import receipt privately before later reopen/inspection. The
result is `mechanical-candidate-inspection-v1`, content identified and explicitly
non-authoritative. It is not a dossier, semantic approval or export permission.
Nothing sends source-bearing content to an AI provider or external service.

## Retention, replay and recovery

- `retained-source`: requires `PRIVATE_SOURCE_RETENTION`. The custodian preserves
  the authorized exact original and reviewed host dependencies for source replay.
- `limited-retention`: does not require permanent original retention after a
  completed import. It retains only the selected authorized evidence, factual
  projection, notices, provenance and integrity references. It never deletes or
  copies the source automatically. The custodian controls its separate lifecycle.

Both modes explicitly state that complete source replay is unavailable without
the exact original artifact. Derived evidence inspection can continue without it;
that is artifact verification, not source replay. Interrupted imports and checkpoint
recovery still need the original, same profile and limits. Do not discard it before
completion. Changed profiles cannot inherit old checkpoints, and old reports remain
historical when a new invocation refuses. No alternate persistence system is added.

## Resource envelope and limitations

Existing hard ceilings are unchanged: Linux; 2 GiB source, 8 GiB decoded,
8 MiB per partition, 64 KiB source row, one million rows, 10,000 partitions,
2 GiB workspace, 512 MiB output, 512 MiB worker memory, 60 CPU/70 wall seconds.
Oracle evidence adds text to selected row payloads, assertion comparisons and a
streamed output artifact, so it consumes more of those same budgets. The evidence
reader limits reports to 4 MiB, lines to 256 KiB and selected occurrences to 128.
Limits refuse rather than approximate or silently enlarge. Full official-release
capacity is unmeasured; authorization alone does not establish that it will fit.

The end-to-end demonstration imports original EQA/EQB fixtures and retrieves the
actual supplied paper-dial instruction through the existing mechanical consumer.
It proves provenance and inspection, not real-card semantics, strategic usefulness,
gameplay, catalog completeness, canonical admission or production activation.
