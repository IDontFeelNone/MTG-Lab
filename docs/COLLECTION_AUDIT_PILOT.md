# Collection Audit and Organization Pilot

Canonical baseline: `15e19b84701dd47970a948485683f73a687be9d2`, the merge of GitHub PR #169. Architecture v12 remains frozen. This named milestone does not assign a new project phase number.

## Authority and ownership boundary

The audit reads the existing `collection-import-v1` and immutable `collection-snapshot-v1` contracts through `CanonicalCollectionResolver`. The snapshot remains the ownership source; the audit does not create another collection database or canonical repository. The typed Collection Engine remains unchanged, including its existing defaults and operations. The separate mixed-policy deck-allocation defect is excluded.

The source import bytes and canonical snapshot are bound to the ownership projection. Audit reconstruction verifies those bindings and reproduces the existing resolution and snapshot calculations. Exact production identities, legacy identities, ambiguous names, unsupported physical dimensions, missing fields and unresolved rows remain distinct. An exact Card identity does not establish an exact Printing or an owned copy's finish, language, condition or location.

Physical organization is supplied under an existing import row's `provenance.organization`, using the small `collection-organization-v1` annotation. Its explicit storage classification may be `sleeved`, `separated`, `bulk`, `binder`, `deck`, `other`, or unknown. `storage_location` continues to identify the physical container. Neither dimension establishes usefulness, competitive strength, value or a sorting recommendation. A stable physical lot identifier may be supplied in provenance; otherwise the immutable snapshot and source-row reference identify the record, with no inferred correspondence across snapshots.

## Quantity and work accounting

The audit separates resolved copies, ambiguous or unresolved reported copies, repeated input records, invalid quantities and conflicting physical-lot declarations. It does not reuse the older snapshot's aggregate unresolved quantity as a confirmed physical count. Positive integer quantities exclude booleans. Duplicate copies beyond the first per Printing are distinct from duplicate input rows, and neither implies unwanted surplus.

Unique Card and Printing counts use resolved identities. Storage copy counts and Card review-state counts have separate denominators. Unknown quantities and conflicting declarations prevent a complete physical census. An expected total is an explicitly supplied inventory constraint, never a reconstructed claim about the user's collection.

Read-only work lists answer which exact Cards have been reviewed, which never-reviewed Cards remain in bulk, and which prior reviews have an explicit request for another look. Previously processed Cards are not presented as new discoveries. Acquisition-candidate queries expose ownership evidence and its limitations; they do not provide reviewed buyer declarations, executable offers or purchase advice.

## Personal assessment history

Collection-owned `collection-assessment-v1` records retain source-bound personal outcomes, assessment version and timestamps, original ownership snapshot, exact Card/Printing evidence, prior assessment identity, supersession and any explicit manual reassessment trigger. They are append-only references beside existing collection snapshots, not canonical knowledge facts or another ownership store.

Replay derives the current personal review state while preserving all earlier records. Missing predecessors, conflicting successors, subject changes, tampered sources and invalid chronology fail closed. An identical record can be replayed without duplication. Recording a reassessment request does not perform reassessment or automatically approve a replacement.

Every current or historical ownership snapshot is replayed from an explicit original-import reference before it can influence review state or record admission. This bounded pilot requires its canonical query snapshot to match the current resolver. Canonical drift blocks validated audit/history projection rather than silently substituting new identity evidence; historical raw sources and assessments remain intact for explicit reconciliation. Cross-snapshot copy correspondence and automatic compatibility reconciliation are not implemented.

Real human approval requires an explicit trusted review boundary and binds the exact source claim. Synthetic review examples use fictional reviewers and non-approving mock review metadata; they do not establish human approval. Personal collection review never approves pending functional-role candidates, promotes canonical entities, or authorizes acquisition advice.

## Real inventory evidence gap

No authoritative 360-copy Mystery Booster 2 ownership list is retained at this baseline. The six partial opening reports under `data/observations/magic/mystery_booster_2/boxes/box_001/` contain 90 reported positions and are marked `in_progress` and `unverified_user_report`. They do not prove exhaustive pulls, current possession, exact Printings, physical attributes or present storage. They are preserved as evidence leads, not silently imported into ownership.

The demonstration therefore uses a clearly labeled compressed synthetic quantity fixture. Its declared 360 copies test reconciliation and duplicate handling; they are not the user's pulls or an inferred real inventory. The existing 384-Card mechanical cohort and 379 admitted MB2 Printings are bounded canonical coverage, not complete MB2 set membership.

For real import, supply an exhaustive dated inventory with a stable collection identity and scope; positive copy quantities totaling 360 after repeated records are excluded; stable lot/copy or pack-position references; exact Printing IDs or identifying source evidence; observed physical attributes with unknowns explicit; current possession/disposition information; storage classifications and containers; and retained prior review decisions with exact subjects, reviewer, date, assessment version, outcome and evidence references. Clarify whether the 90 partial reports belong to that inventory and remain owned. Missing identities and unverifiable reviews stay pending.

## Delivery and stop boundary

The derived audit dossier and manual ChatGPT handoff retain exact source, snapshot and assessment identities, explicit unknowns and omission accounting. Complete compact UTF-8 structured delivery must fit 65,536 bytes including its single trailing LF; oversize output fails closed. A bounded handoff references complete retained evidence rather than silently dropping records or claiming live ChatGPT integration.

The complete retained audit is 82,314 bytes. Its delivery projection is 54,650 bytes and the manual handoff is 57,928 bytes, each including LF. The six resolved Cards are Ponder, Faithless Looting, Greater Good, Sol Ring, Counterspell and Veil of Summer. Resolved copies total 330; ambiguous and unresolved declarations total 15 each. Repeated input quantity 80 and the invalid zero row are excluded. Copies beyond the first per Printing total 324. Storage counts are binder 210, bulk 90, sleeved 5, separated 5 and unknown 50. These are fictional source declarations, not sorting decisions. Six source-bound mock assessment records yield three reviewed, two pending and one reassessment-needed Card; no actual human approval is recorded.

The new commands reuse the unified CLI. Relative `--source` paths are resolved below `--source-root`; `--data-root` selects the existing collection storage. Use `collection audit --snapshot ID --source IMPORT --source-root ROOT --assessment-root RECORDS --expected-total 360 --reasoning-context` for bounded delivery. `--card-id`, `--printing-id` and `--card-name` select an exact-ID or explicit-ambiguity query. `--candidate-printing-id` can identify an acquisition comparison's candidates without authorizing acquisition.

`collection assess --snapshot ID --source REVIEW_SOURCE --source-root ROOT --assessment-root RECORDS` records an explicitly supplied personal review claim; it validates source and canonical identity, history and output size before append. `--record-human-review` is an explicit trusted-caller boundary for a real human approval. `--trust-retained-human-reviews` permits reading already admitted source-bound human approvals during audit; it does not create an approval. The synthetic pilot uses neither flag. Receipts preserve synthetic and approval markers. Oversized error diagnostics are explicitly omitted in a bounded failure response; successful output is never truncated.

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/build_collection_audit_pilot.py --check
```

The complete audit and compact delivery materials are retained under `data/review/collection-audit-pilot/`; original imports, snapshots and assessments remain under `data/collections/`. The generator verifies complete source/result replay and companion artifact digests before rendering explanations or handoffs, refuses conflicting existing evidence, and performs no mutations in `--check` mode.

Canonical records, historical market observations, knowledge facts, previous demonstrations, approved decisions and Architecture v12 remain protected. No automatic value ranking, bulk-versus-sleeve recommendation, role approval, synergy discovery, competitive classification, deck optimization, provider acquisition, purchase execution or automatic reassessment occurs.

The earlier Card acquisition generator's protection calculation excludes the newly added collection-owned files and this audit's review artifacts, which were absent from its original baseline. Its historical manifest and all eleven retained artifacts remain unchanged; every original protected file still contributes its hash. A regression verifies both original-baseline replay and detection of canonical edits. This compatibility change does not alter acquisition policy, input validation or recommendation behavior.

Stop after this single milestone's PR handoff. The next action is Project Manager review; real inventory import and any follow-on work require their applicable authorization and evidence.
