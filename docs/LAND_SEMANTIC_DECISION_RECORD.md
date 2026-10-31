# Append-only land semantic decision record

The owner explicitly approved the nine existing land candidates in collection
`sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`
strictly within their bounded historical retained-text scope and documented
limitations. The owner also supplied the preceding independent Senior PM
recommendation to accept all nine. This milestone records that supplied decision;
it does not manufacture an authenticated signature, account identity, decision
timestamp or separate human-attestation event.

## Exact decision and historical base

The retained decision quotes the owner-supplied statement:

> The project owner explicitly approved all nine land interpretation candidates in collection:
>
> sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
>
> The approval applies strictly to their bounded historical retained-text interpretations and documented limitations. The Senior PM separately recommended acceptance of all nine.

The decision's provenance identifies this as an explicit owner-supplied
instruction. The PM recommendation is attributed to the owner's report of the
preceding independent recommendation, without invented authentication evidence.
The four owner authentication/event fields and PM account/time/authentication
fields remain null. A documentation date is not an owner decision timestamp.

The implementation base is canonical main
`399016f2f69d709a8a50fd16f94b94432a093524`, tree
`5db2265fae343400b17ae67dcf461a1266e83e1f`, after merged PR #220. Architecture
v13 remains ACTIVE APPROVED, Decision 017 remains ACCEPTED and repository-first
governance remains governing.

The new immutable file is
`data/review/land-semantic-decisions/owner-acceptance-v1.json`:

| Contract | Value |
|---|---|
| Schema version / identity domain | `card-rules-land-semantic-decision-v1` |
| Own identity field | `decision_id` |
| Decision identity | `sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075` |
| Canonical file bytes | 342,219 |
| Raw SHA-256 | `d842e14ba5609f21820c6a6ef9bd686d835169e2162d456911aacfe0b2ca6063` |
| Record and report byte bounds | 524,288 each |
| Report schema / identity domain | `card-rules-land-semantic-decision-report-v1` |
| Report own identity field | `report_id` |

The identity uses the existing `contract.identity` domain/content hash, omitting
only the actual own identity field. Canonical compact UTF-8 JSON includes a final
LF in serialized files; that LF is excluded from the domain/content identity
material under the established contract. Raw file hashes are distinct identities.

The record is sequence 1 with no previous decision. It has no overwrite,
amendment, arbitrary-approval or decision-authoring API. Its exact content and
identity are pinned by the finite reader. Later decisions would require a separate
explicitly scoped repository change and new immutable evidence, not mutation of
this record or a permissive flag.

## Exact nine-candidate scope

| Subject | Accepted existing candidate identity |
|---|---|
| `snow-wastes-mana` | `sha256:7ce81b50485c09cb3ed789db287142253b55541c067d275f6750f1c9a2bc02e5` |
| `port-mana` | `sha256:142af8b66263bb182396c134e4c9efb7b6f686be5097d875743d9e67c076748a` |
| `port-utility` | `sha256:8dc9ba9f08113d9ee170efeadf7e4f21022e60f3e2a5694cfd088ad3657a66da` |
| `city-mana` | `sha256:75a3a8dd76a16138dfbd8528d2680109e3f9ca542538df6b0fe6298a63e84148` |
| `city-damage-trigger` | `sha256:0a66c251fedc138c584b64ba80b36dcf1c59ba5ae34010a45c7909dfdce658e4` |
| `citadel-colorless` | `sha256:9df44dd22515ca823e3b65d3e56160b2bb6b1e756e5c691daa234cba744db013` |
| `citadel-color-choice` | `sha256:83aa0a956dd278b5362466b29664874ece949dbf6f32cf74b9777bcf47d954c1` |
| `coffers-mana` | `sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48` |
| `tower-mana` | `sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc` |

The binding includes actual owning-contract identities:

| Record | Identity |
|---|---|
| Plan | `sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5` |
| Interpretation collection | `sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e` |
| Original manifest | `sha256:243fd17c5ccedd3c0ad6bdeeb5f2769a45b55fe7a17e2003fe9b265c1cc5eed1` |
| Land CR context | `sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478` |

Complete original candidate content is retained in the decision binding, including
source identities and complete owned boundaries, criteria and assessment methods,
counterevidence, limitations, descriptive readings and unresolved questions. The
record also binds the retained Card evidence and structured CR context, plus the
original overview, assessments and four comparison identities.

Acceptance covers complete owned passages; proposed activated/triggered
classifications within the retained-text scope; applicable criterion readings and
methods; separate ability and additional-effect ownership; written costs,
conditions and output dependencies; and conditional behavior supported by the
existing evidence. It does not approve the earlier seven-subject pilot or unrelated
interpretations.

The accepted ownership keeps Port utility's complete cost and target requirement,
City's separate damage trigger, Citadel's two-sentence color-choice activation and
its separate colorless activation, Coffers' complete paid count-dependent
instruction, and Tower's commander-color-identity restriction. The unchanged
baseline's lack of an additional-effect assertion is not evidence of absence.
Citadel's separately versioned composition remains conditional; City's broad-603
procedure frontier stays unresolved.

## Historical state and current decision view

The original nine interpretation JSON bytes and identities remain unchanged:

```text
semantic_review_status=PENDING_NOT_ESTABLISHED
review.status=requires_review
human_attestation=null
canonical_admission=false
execution_authority=BLOCKED
```

Those fields truthfully describe the historical record. The new current view
reports `ACCEPTED_BOUNDED_RETAINED_TEXT`, resolved through the exact separate
`decision_id`, alongside the original historical status, historical null
attestation, original result identities, accepted scope and remaining limitations.
Neither the historical record nor its original computed conclusions are rewritten.

The original overview still has identity
`sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd`,
689,253 canonical bytes and raw SHA-256
`0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515`.
The original integrity result still has identity
`sha256:d6725c1479882549479a76a3a30e52871d5fbedb77ac5abd105f527e9eeca4cd`,
596,487 canonical bytes and raw SHA-256
`c71633d26a13d2ad8f0bc6db1a0b561d9df824cdad5eeba9880b953bbc9f2d4a`.

The separately reproduced current summary has `report_id`
`sha256:6e4bdf2abf00bdf9aeda58df04d414586d58428851f7eeb9431fdf8626c9437b`,
192,402 canonical bytes and raw SHA-256
`ea5b76098b790694070a17a1c724ff43a33f76a83012273cc1de871aef2a176d`.
Its current integrity report has `report_id`
`sha256:300c4c691e9c2c6efa68de3e39a01886b5edb86eadc5c12f22e7be9b3501623e`,
192,404 canonical bytes and raw SHA-256
`2e2e77623b6ce2ecfbcd773f0ca9fbe212a65436ff3aaa4d5e4a68e55c6551df`.

## Admission, validation and read-only reporting

`load_land_decision` calls the actual public land evidence admission against the
independently required catalog profile, query snapshot and plan identities. It
reproduces the complete original overview and each candidate's own identity,
checks exact nine-member correspondence, then reproduces the one explicit supplied
decision against the admitted evidence. A matching hash, successful test, earlier
merge or generic approval flag cannot supply owner acceptance.

The closed validator rejects substitutions, omissions, additions, foreign
identities, changed candidate evidence, stale source bindings, changed scope or
permissions, and rehashed altered decisions/reports. Existing strict canonical
JSON contracts reject duplicate keys, nonfinite values, scalar type substitutions,
unsupported structures and oversized/noncanonical inputs. Public admission of the
real disposable writer's expanded 654-card catalog rejects incompatibility; no
historical positive catalog fixture is installed.

The consumer privately owns admitted bytes. Summary, subject and integrity reports
share that snapshot; report validation recomputes exact expected content. Decoded
views do not alias private evidence. No application report store, ingestion
pipeline, general approval service or filesystem mutation is introduced.

```python
from pathlib import Path
from card_rules_pilot.land_decision import load_land_decision, DECISION_ID

root = Path('.')
decisions = load_land_decision(
    catalog_root=root, mechanical_root=root,
    review_root=root / 'reference-reviews',
    cohort_root=root / 'data/review/land-mana-utility',
    decision_root=root / 'data/review/land-semantic-decisions',
    expected_profile_id='sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e',
    expected_query_snapshot_id='sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7',
    expected_plan_id='sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5',
    expected_decision_id=DECISION_ID)
summary = decisions.summary()
decisions.validate_report(summary.to_dict())
print(summary.to_json())
print(decisions.subject('citadel-color-choice').to_json())
print(decisions.check().to_json())
```

```bash
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
args=(--catalog-root . --mechanical-root .
  --cohort-root data/review/land-mana-utility
  --decision-root data/review/land-semantic-decisions
  --expected-profile-id sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e
  --expected-query-snapshot-id sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7
  --expected-plan-id sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
  --expected-decision-id sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075)
python -m card_rules_pilot.land_decision_cli --review-root reference-reviews summary "${args[@]}"
python -m card_rules_pilot.land_decision_cli --review-root reference-reviews summary "${args[@]}" --json
python -m card_rules_pilot.land_decision_cli --review-root reference-reviews subject "${args[@]}" citadel-color-choice --json
python -m card_rules_pilot.land_decision_cli --review-root reference-reviews check "${args[@]}" --json
```

Each command fully admits and renders before stdout. Errors return exit 2 without
a partial report. Caller-controlled stdout redirection is sufficient to retain a
demonstration outside the repository.

## Limits and delivery

Acceptance verifies no current Oracle wording, arbitrary game-state legality,
current activation eligibility, actual mana, feasible payment, trigger event or
resolution, complete stack/priority execution, executable CardGameplaySemantics,
general parser or automatic classifier. Changed text, gained abilities, copies,
external effects, Swamp count, commander context and other unresolved inputs stay
unresolved. Retained Card observations remain historical; structured retained CR
evidence is not fresh verification of the original TXT.

Real gameplay execution remains BLOCKED and canonical admission remains false.
Semantic closure remains OPEN; all ten activation responsibilities remain OPEN /
EXECUTION_BLOCKED. Source clearance remains not_granted. Private retention,
redistribution, free service, commercial service and AI export remain
NOT_ESTABLISHED. Tier A non-production restrictions are unchanged. New source
units/projections are 0/0, global coverage remains 104/16, land context remains 24,
and fresh-source/projection allowlists remain empty. No TXT attachment is needed.

The new preservation regression checks original sources, all hosted workflows,
historical input bytes and original owning-contract output parity. Exact finite
adapters strip only eight pinned documentation suffixes and enumerate only the two
new decision-consumer source files. Original assertions continue to inspect their
exact historical bytes; no broad path exemption, gate or timeout change is added.

Required validation includes focused contract, ownership, provenance, scope and
preservation tests, complete stable local discovery, and both final-head hosted
workflows with actual publication validation, real 654-card writing and matching
bare-remote readback. Exact validation receipts, filenames, inherited accounting,
base/head/tree and merge-parent evidence belong in the one draft PR. This guide
does not claim that a gate ran before its actual receipt exists. Stop for
independent PM review; no merge, auto-merge or subsequent milestone is authorized.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
