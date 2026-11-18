# Collection-to-Deck Analytical Integration V1

This read-only consumer combines [collection auditing](COLLECTION_INTELLIGENCE.md),
the owning exact/flexible allocator and [supplied-deck consistency](SUPPLIED_DECK_CONSISTENCY_V1.md).
It answers coverage against reported holdings and access in the **intended** deck.
Neither coverage nor a positive probability difference establishes competitive
strength, legality, castability, combo success or win rate.

## Explicit inputs

`analyze_collection_decks(request, *, snapshot, source_path, source_root, catalog_root)`
has no default private inventory or catalog. `snapshot` is an existing
`collection-snapshot-v1` document. Its original retained import source must exist
under the explicitly selected source root. No import, snapshot creation, collection
mutation, reservation or persistent analysis store is performed by this workflow.

`catalog_root` selects the existing filesystem/legacy canonical reader route, not
a new production attachment profile. The operator must already be authorized to
use that catalog and source for this operation. Private location, checksums and
caller selection do not grant source rights or canonical admission.

The closed `collection-deck-analysis-input-v1` request contains exactly:

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `collection-deck-analysis-input-v1`. |
| `catalog` | Exactly `game` and the expected `sha256:...` query `snapshot_id`. Game IDs are bounded safe path components. |
| `collection_binding` | Exactly selected `snapshot_id`, `snapshot_digest` and `source_import_digest`; digests are 64 lowercase hex characters. |
| `deck_analysis` | The existing closed supplied-deck request, with one or two complete configurations, explicit sections, identities, groups and schedules. |
| `requirements` | One object per deck: exactly `deck_id` and `requirements`. Each list has 1–512 positive rows. |

Every Printing requirement has exactly `requirement_id`, `card_id`, `section`,
integer `quantity` (1–120), `policy` (`any` or `exact`) and `printing_id` (null
for any, an exact ID for exact). Requirement IDs are unique within the deck.
IDs are printable trimmed strings of at most 128 characters. Rows sort by their
requirement IDs; configuration order retains baseline/candidate meaning.

Coverage selects the same section as the intended draw population. Requirements
must sum exactly to its positive Card quantities. Zero rows remain in probability
inputs but produce no ownership requirements. Other sections are retained in the
supplied analysis and excluded from allocation and sampling. No implicit
sideboarding, commander inclusion, name lookup or alias mapping occurs.

The packaged [input schema](../src/schemas/v1/collection-deck-analysis-input.schema.json)
and [report schema](../src/schemas/v1/collection-deck-analysis-report.schema.json)
are closed analytical contracts, checked with the existing JSON Schema dependency.
They do not register new canonical record kinds. Runtime checks additionally
enforce quantity reconciliation, source replay, exact joins and comparison rules.

## Audit and identity boundaries

The owning query and collection resolver must agree with the requested catalog
identity. `CollectionAudit.build` replays the original import bytes and canonical
resolution, reproducing the complete snapshot. A recomputed snapshot digest alone
cannot validate changed holdings. Missing sources, mismatched bindings, catalog
drift and malformed evidence withhold coverage.

Selected Card IDs and exact Printing-to-Card relationships are independently
checked through the existing exact query interface for current, known identities.
The pure probability report remains `CALLER_DECLARED`; its matching strings are
not promoted to canonical facts. Unknown or ambiguous joins withhold the affected
configuration, with null covered/uncovered quantities rather than invented zero
ownership. The consistency result can remain valid independently.

Resolved inventory joins must also be established. A source row resolved solely
through a name fallback is insufficient for this exact-identity workflow;
explicit Printing IDs or existing exact external-identifier resolution are needed.
Conflicting `owned_lot_id` assertions block coverage for both alternatives before
allocation. Audit exclusions are never bypassed by forwarding conflicting raw
holdings. Ordinary invalid, duplicate, ambiguous and unresolved rows supply no
copies; their aggregate counts remain visible.

The source and catalog boundaries are rechecked before returning confident
coverage. Detected drift clears all earlier coverage and verified bindings.
Failures report fixed reason codes, not private exception messages or paths.
No retained human assessments are discovered or required for this quantity task.

## Native Printing allocation

`compare_deck(..., include_allocations=False)` keeps its original signature behavior,
report schema and allocation results. Opting in returns `deck-comparison-v2` with
an additional `allocation_trace`. The existing consumption loop records, per
requirement, its stable report index/ID, Card, section, exact/flexible policy,
required/allocated/uncovered quantities and consumed Printing-ID quantities.

Exact requirements still allocate before flexible ones. Existing report ordering,
stable flexible Printing-ID order, conservation and leftover meanings are unchanged.
The integration calls this owning loop separately for each alternative; it never
reconstructs allocation or adds a second allocator.

The integrated report retains only the whitelisted trace and totals. It excludes
raw unresolved rows, source content, storage, acquisition notes, assessments and
unrelated holdings. Printing-ID matching does not claim finish, treatment,
condition or language restrictions were satisfied. Such additional constraints
are unsupported in this input version.

## Coverage, consistency and alternatives

Use “covered by reported holdings” and “uncovered in selected snapshot.” These
are source-replayed declarations, not independently verified physical ownership
or proof of the owner's complete real-world collection. `scope_complete` remains
null and physical-ownership verification false. Unresolved evidence can change
shortages. No purchase or disposition advice follows.

The complete intended configuration always goes unchanged to `assess_supplied_decks`.
Reducing inventory to zero, withholding coverage or changing allocation policy
does not reduce the intended deck or its probabilities. Existing equivalence,
exact-delta, impossible-event and abstention rules remain unchanged.

Two configurations are independent alternatives over the same immutable snapshot.
`allocation_scope` is `INDEPENDENT_ALTERNATIVES_NO_RESERVATION`. Their allocations
must not be summed into a simultaneous ownership commitment. No reservations,
joint allocation optimizer or multi-deck persistence are introduced.

The [fictional demonstration](../tests/fixtures/collection_deck_analysis_v1/)
has two reported target copies across two Printings. A three-copy intended build
uses one exact copy and one flexible copy and leaves one target copy uncovered;
a four-copy alternative leaves two uncovered. Their seven-card access remains
5397/17110 and 38962/97527 respectively, using the intended counts. The example
contains unrelated private-canary holdings/notes to verify output minimization;
it contains no real user inventory or production Card admissions.

## API, CLI and reports

```python
from collection.deck_analysis import analyze_collection_decks, parse_collection_decks

report = analyze_collection_decks(
    parse_collection_decks(raw_request), snapshot=selected_snapshot,
    source_path=original_import, source_root=authorized_source_root,
    catalog_root=authorized_existing_catalog_root,
)
```

```console
PYTHONPATH=src python -B -m mtglab deck analyze --input REQUEST.json --snapshot SNAPSHOT.json --source IMPORT.json --source-root ROOT --catalog-root CATALOG --format text
```

All five input paths are explicit; no default collection is discovered. The new
command uses `--catalog-root`, not the global legacy `--data-root`, for its catalog.
JSON is default; text shows Printing use, uncovered quantities, intended-deck
probabilities, deltas/abstentions and uncertainty. Caller-supplied deck labels are
display labels, never identity evidence. No report is automatically persisted,
published, sent to an AI provider or exported to a service.

`DeckAnalysisError` is the structured request refusal. The CLI returns 2 for
unavailable/invalid request or snapshot documents, without raw path diagnostics.
A valid analytical request with unavailable source/catalog evidence returns an
`ASSESSED` report with `WITHHELD` coverage and independent consistency; CLI exit 0
does not mean ownership was verified. Valid coverage is explicitly labeled
`REPORTED_SNAPSHOT_COVERAGE`. There is no general readiness or permission approval.

Raw/normalized requests are capped at 196,608 bytes, snapshot documents at 4 MiB,
and reports at 393,216 bytes including LF. The existing audit/catalog readers keep
their own processing contracts. No probability bounds are enlarged. Stable JSON,
SHA-256 input/report identities and detached inputs preserve reproducibility.

Architecture v13, Decision 017, permissions, admission, existing source evidence,
probability kernels, gameplay and full-corpus CR HOLD remain unchanged. Historical
source versions reconstruct through exact test-only successors with original pins.
