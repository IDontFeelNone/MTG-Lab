# Card–Rules mana-ability interpretation review pilot

This capability answers one review question: for seven explicitly selected passages
on six exact retained Cards, what authored interpretation is proposed, which
retained criteria apply, what evidence supports it, and what remains unresolved?
Source correspondence, authored Card interpretation, proposed rules classification,
semantic review and canonical/execution authority remain separate dimensions.
Validation reproduces the fixed authored proposal and verifies its bindings. It
cannot establish semantic correctness.

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED. The
required canonical base is `f53ec31b2bf289e578bcffd815ab0a2f1b89f98f`, tree
`db040e92084cb3bb85e8147811b8a35f027b35a0`. GitHub PR #215 is merged, and its
reviewed head `7b1aef62638934908b1deab48a6d8d4ac3e73183` has that same tree.
The initially clean stale checkout was reconciled before implementation.

Every candidate retains `review.status=requires_review`,
`human_attestation=null`, `canonical_admission=false` and
`execution_authority=BLOCKED`. Merging this code approves no individual
interpretation, creates no knowledge fact and grants no execution authority.

## Exact selection and ownership

Names label the records; only exact canonical IDs select Cards.
An interpretation subject ID is a local review identity, never a canonical ability
identity. Passage boundaries are authored against complete retained source fields.
There is no ability parser, punctuation detector, keyword classifier or entailment
engine.

| Card | Exact canonical Card ID | Local subject / selected instruction |
|---|---|---|
| Sol Ring | `6ad8011d-3471-4369-9d68-b264cc027487` | `sol-ring-tap`: its single tap-for-mana ability |
| Basalt Monolith | `6b8cf2a0-b045-4d91-9d91-c602d40c6237` | `basalt-monolith-tap`: its tap-for-mana ability |
| Basalt Monolith | `6b8cf2a0-b045-4d91-9d91-c602d40c6237` | `basalt-monolith-untap`: its separate paid untap ability |
| Deathrite Shaman | `22f1a4a4-c423-4d1c-8775-0ed604a9fa51` | `deathrite-shaman-first`: its complete first, targeted mana-producing ability |
| Dark Ritual | `53f7c868-b03e-4fc2-8dcf-a75bbfa3272b` | `dark-ritual-spell`: its mana-producing spell instruction |
| Mana Flare | `97159138-c34b-416e-b079-5c952383a243` | `mana-flare-trigger`: its triggered ability |
| Pitiless Plunderer | `a784481f-eccb-4112-bb38-04a659319660` | `pitiless-plunderer-host-trigger`: its host Card's death-triggered token-creation ability |

Basalt's static untap restriction stays surrounding context; it is no third
subject. Its two activations cannot borrow each other's costs or effects.
Deathrite's other abilities remain complete source context and explicitly outside
the assessment. Dark Ritual binds the retained type line as well as Oracle text.
Plunderer's parenthetical token description stays source context; the quoted
activation belongs to the created Treasure. No canonical Treasure or token
semantics is constructed. Mana Flare's qualifying-trigger relationship remains an
authored pending interpretation without event detection, causality or resolution.

## Evidence and distinct time bindings

The sole Card acquisition is `scryfall-mb2-30754638264-1`. Its retained source is
`data/market/acquisitions/scryfall-mb2-30754638264-1/source-mb2.json`, exactly
2,278,127 bytes, SHA-256
`c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47`.
Provider observation is `2026-08-02T09:09:45.851000Z`; historical retrieval is
`2026-08-02T15:34:06Z`. These dates are separate from the CR release
`2026-09-25` and the explicit fixed author-preparation input
`2026-10-26T23:20:00Z`. This is historical evidence review, with no current Oracle
verification or current official ruling claimed.

The explicit v13 attachment seam constructs one actual attachment-backed
`MechanicalCardIntelligence` and one canonical query per invocation. Catalog,
mechanical source and review plan have independently selected roots and expected
identities. A changed live catalog rejects; no historical catalog fixture or legacy
constructor fallback is selected. The query snapshot remains
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`.
The Tier A profile ID is
`sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e`.

The existing acquisition reader verifies actual manifests, retained file lengths,
digests and report agreement. Selected dossiers from
`data/review/mechanical-card-cohort/dossiers.jsonl` are checked under their
`mechanical-card-dossier-v1` identities and against the selected canonical and
retained provider records. Bindings include actual provider row index, whole-record
identity, field pointer, complete field identity, selected complete passage,
ownership and surrounding/unselected context. Field identities preserve the
existing `mechanics.content_identity(field_object)` scheme: SHA-256 of compact
sorted-key UTF-8 JSON, without a new domain wrapper. Existing source and CR
records retain their original schema-specific own-identity schemes. Only the fixed
plan and a small output-identity manifest are newly retained; full source context
is computed through the existing dossier references, without copying provider
records or creating another Card catalog.

Existing CR packages are verified through their actual schema-specific identities,
manifests, projection identities, selected rules, anchors and artifact lineage:

- `gameplay-rules-bounded-mana-ability-projection`: all thirteen concrete 605 units.
- `gameplay-rules-bounded-mana-classification-projection`: 115.6, 606.1 and 606.2.
- `gameplay-rules-bounded-mana-stack-exception-projection`: 405.6c, separately
  qualified behavior context.

The retained release artifact SHA-256 is
`8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`;
artifact-verification identity is
`sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3`.
No source TXT is inspected and no new official rule prose or example is retained.

Later append-only dependency reviews are separately bound from historical arrays:
605.1a/b's 115.6 dependency is source-covered; broad 606 remains partially
represented because 606.1–606.2 supply no full loyalty execution. The later direct
resolution is 605.3b → 405.6c. No 605.4a → 405.6c direct citation is invented.
605.3 → 602.2 has later source coverage, still without an activation engine.
Historical unresolved arrays remain unchanged and labeled historical.

## Complete criteria and provisional readings

The complete retained 2026 activated matrix preserves ability kind, no target
requirement, potential mana on resolution, non-loyalty status, separate library
movement exclusions for costs and effects, self-replacement consideration and
disregard of other applicable replacement effects for classification. Unknown
external state/effects stay unknown. An empty annotation or missing word cannot
prove absence. Expressly authored absence readings cite the complete selected
passage, scope themselves to that evidence and remain pending semantic review.

Triggered candidates separately preserve triggered kind, no target requirement,
potential mana and the qualifying relationship to activated mana-ability
activation/resolution or mana entering a pool. A downstream relationship to mana
alone is insufficient. Actual retained exclusion records are 605.5a for targeted
abilities/nonqualifying triggers and 605.5b for mana-producing spells.

The exact classification vocabulary is `proposed_activated_mana_ability`,
`proposed_triggered_mana_ability`, `proposed_exclusion` and
`interpretation_unresolved`. Criterion states are `proposed_satisfied`,
`proposed_not_satisfied`, `unknown`, `unsupported`, `inapplicable` and
`conflicting`. Subject-kind readings in this plan are
`proposed_activated_ability`, `proposed_triggered_ability` and
`proposed_spell_instruction`. These labels describe proposals and authoring states.
The fixed plan does not manufacture an unsupported or conflicting reading where
none is authored; attempts to upgrade one by rehashing a modified record reject.
Semantic counterevidence remains visible even when the authored structure is
consistent.

| Subject | Authored proposal | Counterevidence or material unresolved reading |
|---|---|---|
| Sol Ring tap | proposed activated mana ability | Self-replacement assessment remains unknown; actual state/output unavailable. |
| Basalt tap | proposed activated mana ability | Self-replacement assessment remains unknown; its separate untap cost is not borrowed. |
| Basalt untap | proposed exclusion | Paying mana to untap is not authored as potential mana production; self-replacement assessment remains unknown. |
| Deathrite first | proposed exclusion | Target requirement is authored as counterevidence, independent of chosen-target count; self-replacement assessment remains unknown. |
| Dark Ritual spell | proposed exclusion | Type-line/spell interpretation and retained 605.5b distinguish mana-producing spell instruction from mana ability. |
| Mana Flare trigger | interpretation unresolved | The relationship to activated mana-ability activation/resolution or mana entering a pool remains unknown pending semantic review. |
| Plunderer host trigger | proposed exclusion | Death-triggered token creation is not the token's own quoted mana activation; no borrowed ownership or downstream-mana shortcut. |

The report keeps every criterion, including reasoned unknown, unsupported,
conflicting and inapplicable readings. Source validity cannot upgrade any such
reading. No fully-supported semantic summary is emitted merely because hashes and
schema validate. The fixed plan is authored data, not a population classifier.
Provider `produced_mana`, mana symbols and chosen-target count provide no automatic
classification premise.

Comparison explains strategic mana-related role versus rules category, paying
mana versus potentially producing it, target requirement versus chosen-target
count, spell versus ability, host versus created-object ownership, and
classification versus present eligibility or actual mana output. Historical
functional-role candidates remain independently pending and provide no approved
semantic premise.

Any no-stack/immediate-resolution context is conditional on the pending proposed
classification. Activated no-stack evidence is 605.3b; 405.6c separately supplies
immediate resolution and conditional prior-priority context. Triggered context uses
605.4a, without transferring activated priority-return context or asserting a live
response window.

## Closed contracts, limits and correction boundary

| Contract / identity domain | Own identity field | Scope |
|---|---|---|
| `card-rules-mana-pilot-plan-v1` | `plan_id` | Fixed authored seven-subject plan |
| `card-rules-mana-interpretation-candidate-v1` | `candidate_id` | Exact source-bound pending proposal |
| `card-rules-mana-review-report-v1` | `report_id` | Read-only seven-subject comparison |
| `card-rules-mana-pilot-manifest-v1` | `manifest_id` | Bounded reproduction identities, byte lengths and hashes |

All use explicit `schema_version`. Canonical bytes are sorted-key compact UTF-8
JSON, Unicode preserved, with one trailing LF for files. Identity is `sha256:`
plus SHA-256 of canonical `{"domain": version, "content": body}` excluding only
that object's own identity field and excluding the file LF. Absolute filesystem
paths and ambient clocks never enter identity material; relocation preserves
identities.

The fixed plan and exact reconstructed candidates form a closed contract.
Unknown fields, duplicate JSON keys/IDs, nonfinite numbers, floats, Boolean/integer
substitutions, stale identities, foreign Card/rule bindings, omitted criteria and
rehashed authority upgrades reject without coercion. Canonical byte caps are
65,536 for a plan, 131,072 for a candidate and 1,048,576 for a report. JSON depth is
at most 20, structural nodes at most 100,000, key length at most 128 and string
length at most 16,384. New plan/manifest inputs require ordinary bounded local
files; symlink inputs and ancestors, hardlinked input files and noncanonical JSON
reject. Existing Card and
CR readers preserve their respective input-validation contracts.

Models, candidates and reports own private immutable canonical bytes and return
independent decoded views. Validation and use consume that same owned content.
Caller/view/filesystem mutation cannot attach an old identity to modified material.
A new invocation performs current integrity verification; no cache hides changed
catalog, source or review bytes. Work then uses privately owned evidence rather
than rebuilding the cohort or validating the repository in each criterion loop.

Corrections require a separately authorized later plan version and new content
identities, preserving old records and explicit supersession lineage. This v1
pilot supersedes nothing and provides no mutation, approval, admission or execution
API. Structural contradiction checks establish consistency of authoring only.

## Read-only API, commands and explicit checking

The API requires independent roots and independently supplied expected identities:

```python
from pathlib import Path
from card_rules_pilot import load_pilot

pilot = load_pilot(
    catalog_root=Path("."), mechanical_root=Path("."),
    review_root=Path("reference-reviews"),
    plan_path=Path("data/review/card-rules-mana-pilot/plan.json"),
    expected_profile_id=profile_id,
    expected_query_snapshot_id=query_snapshot_id,
    expected_plan_id=plan_id,
)
candidate = pilot.subject("basalt-monolith-untap")
report = pilot.comparison()
manifest = pilot.reproduction_manifest()
# candidate.to_dict() / report.to_dict() return independent views.
pilot.validate_candidate(candidate.to_dict())
```

`mechanical_root` selects the repository-shaped evidence root containing `data/`;
it is independent of `catalog_root`. `plan_id`, `profile_id` and
`query_snapshot_id` are explicit selected expected identities, never discoveries
accepted from untrusted changed bytes. The guide's exact current plan identity is
also retained with the fixed plan and in the milestone PR:
`sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83`.

For this retained v1 demonstration the exact values are:

```bash
PROFILE_ID=sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e
QUERY_SNAPSHOT_ID=sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7
PLAN_ID=sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83
```

Individual readable/JSON output and all-seven comparison use the same public path:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m card_rules_pilot \
  --catalog-root . --mechanical-root . --review-root reference-reviews \
  --plan data/review/card-rules-mana-pilot/plan.json \
  --expected-profile-id "$PROFILE_ID" \
  --expected-query-snapshot-id "$QUERY_SNAPSHOT_ID" \
  --expected-plan-id "$PLAN_ID" subject basalt-monolith-untap

# Use the same explicit root/identity arguments with:
# subject basalt-monolith-untap --json
# compare
# compare --json
# check
```

`subject` and `compare` create no files, mutate no candidate, admit no facts and
never automatically retain reports. The only new retained review artifacts are
`data/review/card-rules-mana-pilot/plan.json` (46,332 bytes) and `manifest.json`
(1,920 bytes). The manifest contains candidate/report IDs plus generated canonical
output byte lengths and SHA-256 hashes; it contains no redundant Card/provider/CR
copy. `pilot.reproduction_manifest()` reproduces this small record. `check`
compares its fresh reconstruction with the exact retained manifest and writes
nothing. Complete candidates and comparison remain computed API/CLI output.

The bounded demonstration invokes the actual public API and real CLI for all seven
subjects, verifies deterministic replay and selected evidence non-mutation, and
prints its summary:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python tools/card_rules_pilot_demo.py \
  --catalog-root . --mechanical-root . --review-root reference-reviews \
  --plan data/review/card-rules-mana-pilot/plan.json \
  --expected-profile-id "$PROFILE_ID" \
  --expected-query-snapshot-id "$QUERY_SNAPSHOT_ID" \
  --expected-plan-id "$PLAN_ID"
```

Optional `--output-directory /tmp/existing-empty-directory` explicitly retains
only demonstration transcripts in an existing empty directory outside all evidence
and repository roots. No general artifact writer is introduced. Actual outputs,
identities and final validation evidence appear in the single draft PR description.
Final hosted evidence stays there to avoid a report-only source commit.

## Preservation and limits

No fresh Scryfall/Oracle acquisition, source discovery, CR projection, external
service, model call, embedding or AI export occurs. Real candidates never enter
fictional packets or v1/v2 evaluators. Existing fictional success establishes no
real semantic premise. No `CardGameplaySemantics`, real rules snapshot, execution
profile, legality, targeting, payment, mana output, trigger, token, stack, priority
or replacement-effect engine is constructed. Unsupported semantics remain visible.
No combo, ranking, deck, market or acquisition conclusion is supplied.

Existing provider/Card/dossier, role/comparison, CR/review/anchor and all eight
original PR #209 JSON artifacts remain preserved. Historical document bodies are
unchanged; finite exact suffix adapters preserve historical assertions and compare
reconstructions with canonical Git blobs. There is no new registry, approval
service, persistence framework or repository-wide freeze inventory. Existing
workflows, timeouts, gates, writer/admission, catalog/profile controls and personal
collection boundaries remain unchanged. Historical acquisition identity stays
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

Coverage remains 100 real CR source units / 15 projections; existing stage/range
coverage remains unchanged. Semantic closure remains OPEN, all ten activated
responsibilities remain OPEN / EXECUTION_BLOCKED, and real execution remains
BLOCKED. `source_policy_clearance=not_granted`; private retention,
redistribution, free/commercial service and AI export remain NOT_ESTABLISHED.
Tier A retains `production_eligible=false`, `approval_state=not_granted` and
`data_processing_permission_established=false`, alongside all existing
operation-specific permission states.

Stop for independent PM review of this single draft PR. The owner retains final
merge approval. No follow-on milestone or source projection is authorized.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
