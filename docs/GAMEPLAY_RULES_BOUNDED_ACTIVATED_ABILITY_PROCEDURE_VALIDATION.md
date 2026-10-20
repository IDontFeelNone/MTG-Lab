# Bounded Activated Ability Procedure Projection — validation checkpoint

This pre-hosted checkpoint covers the separately owner-authorized three-unit milestone. The
single draft PR carries final branch/merge checkout SHAs and hosted run evidence;
those values cannot be embedded in the commit they identify. The owner retains
final merge approval after independent PM review.

## Repository reconciliation and source

GitHub main, fetched origin/main and branch base are exactly
`2aa01764db0cfbcd89bc3a30a4433c4f24ea5893`. PR #199 is merged, reviewed head
`6cf3f4897c919b39ec82e6b9ad2e26a4ff06c183`; both trees are
`01a501b75b730fc5820a9b2eff18c8ae4872f8d0`. The original clean checkout remains
on `work` at `9e1335d53458913dec1907e2922b9e99339cc3c5`. The isolated milestone
branch is `codex/cr-bounded-activated-ability-procedure`.

The fresh first-message artifact is 977752 original bytes, effective 2026-09-25,
raw SHA-256 `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
The inherited verification identity
`sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3`
reproduces through its actual retained lineage. Only 602.2/a/b bodies and minimum
structural context are admitted. Raw anchors reproduce lines 2533/2535/2537 and
historical spans excluding final line terminators. Historical review-only
fingerprints are unchanged. No official prose, examples, TXT or actual attachment
path is retained.

Fresh source verification, offline metadata reconstruction and mocked source
comparison are separate. Only the milestone-specific external source selector
was configured locally, so inherited source-dependent tests remained explicitly
unconfigured. Hosted source verification may explicitly skip when unconfigured.
Configured missing or mismatched inputs fail closed.

## New identities and preserved authority

Projection:
`sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553`

Package:
`sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4`

| Reference | Rule identity | New anchor identity |
|---|---|---|
|602.2|`sha256:23e189bb24316153b53bd6e0e816f632d1cc9be5e0ea45991d22fc1c9af0e9cf`|`sha256:d1e9e95636b107b9549d3347c56403d60e487de4d2b166473874c8a36a6dd08c`|
|602.2a|`sha256:76b57da23eb35c46e588d8e81d4d0b888087c077b10baf6fb042f287789ecb34`|`sha256:226aa0a3f180feae52c291b08a186a9cf7b55c340c75b5cf19234ff6fd3712ae`|
|602.2b|`sha256:19943e8f5b970ac4c7065de57616c731c88cc9ec474be1716992a6d566164135`|`sha256:d21c682824feebc185e01a11101bf4e4725283bdfd0b96ef4303a5ab89e70cde`|

Exact allowlist 602.2, 602.2a, 602.2b is disjoint from the 85 inherited units.
The ten projection components have 88 distinct references and ten distinct IDs.
No outgoing target or imported body is projected. All 454 protected baseline
files remain byte-identical: 339 src and 115 gameplay evidence across 18 directories.
All seven historical document bodies are retained; current status is appended to
four and the other three remain wholly byte-identical. Historical assertions and
immutable fixtures remain intact. Only two historical test files change selectors
for eight exact new source files and eleven exact new evidence files.

Protected identities:

- Design package `sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1`.
- Stack-exception projection `sha256:7ff68d920bd2b846e3fb1616743c48d99e2935b007ccb6943057c47ce74cf87a`.
- Stack-exception package `sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1`.
- Historical acquisition `sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

The package validates 58 historical review bindings with their actual contracts,
own IDs, hash domains, canonical bytes and intended parent manifest relationships.
PR #199's seven integer-schema records use their explicit design-record-v1 domain
and `record_ids[filename]`. Valid foreign IDs and all-unique swaps fail.

## Local validation checkpoint

Commands below run in the isolated repository. `CR_SOURCE` denotes the private
runtime selector; its actual path is never recorded. Durations distinguish
unittest elapsed time from command wall time where both were measured.

| Check and actual command | Tests / skips | Duration | Exit / result |
|---|---|---|---|
| `MTGLAB_ACTIVATED_ABILITY_PROJECTION_SOURCE_ARTIFACT="$CR_SOURCE" PYTHONPATH=src python -m unittest discover -s tests -p 'test_gameplay_rules_bounded_activated_ability*.py' -v` | 54 / 0 | 7.461s unittest; 7.654s wall| 0 / PASS |
| `PYTHONPATH=src python -m gameplay_rules.activated_ability_projection validate --package reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection --source "$CR_SOURCE"` | Fresh 3 spans | 0.489s wall| 0 / PASS |
| Same `validate` command without `--source` | Offline metadata only| 0.248s wall| 0 / PASS |
| Actual fresh `build_package`, `write_package`, `load_package`, all 11 files compared byte-for-byte, `verify_preservation` | 3 fresh anchors; 454 preserved files| 0.515s operations; 0.752s wall| 0 / PASS |
| `MTGLAB_ACTIVATED_ABILITY_PROJECTION_SOURCE_ARTIFACT="$CR_SOURCE" PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v` | Running; final result in PR | Final result in PR | Pending at this checkpoint |
| `PYTHONPATH=src:tests python tests/publication_validation_regression.py` | Running; final result in PR | Final result in PR | Pending at this checkpoint |

Earlier separate successful checks: source/contract tests 19/1 skip in 0.105s
offline and 19/0 in 0.225s with actual source; after additional strict-type test,
20/1 in 0.130s offline. Preliminary preservation 7/0 in 0.197s and historical
preservation 75/0 in 0.906s passed. Adversarial 16/0 in 8.022s passed, followed by
corrected 17/0 in 7.546s. Consumer semantics 11/0 in 0.187s passed. All exit 0.
These are earlier results, separate from the final combined and full checks.

Two failed validation attempts are retained:

- Intermediate adversarial run: 17 tests, one error, 9.181s, exit 1. A new test
  expected the discarded `literal_outgoing_references` alias after the evidence
  corrected the current field to `outgoing_literal_references`.
- First combined focused run: 43 tests, one error, 9.595s unittest / 9.805s wall,
  exit 1, same test-field mismatch. The corrected final run passes separately.

No failed result is erased by a later pass. No publication timeout or full-suite
failure has been recorded at this point. An auxiliary broad forbidden-token scan
flagged the inherited test's own detector string; a precise scan of actual
attachment identifiers and all three selected full bodies passed. This was a scan
false positive, separate from unittest results. Initial sandboxed Git access and
one execution-transport attempt failed; network-enabled Git and the GitHub
connector supplied the required verified repository evidence. The `gh` API route
was forbidden; hosted metadata and logs use the configured connector.

## Relationships and remaining blockers

New append-only reassessment marks 605.3→602.2 DIRECT_REFERENCE_RESOLVED,
binding retained origin and new target evidence. Separately explicit 602.2b→601.2f
resolves source correspondence for the concept mapping SPELL_MANA_COST to
ABILITY_ACTIVATION_COST. 602.2→733 and 602.2a→701.20a stay unresolved.
There is one 601.2b–i range import with eight member rows: b/f/g/h projected,
c/d/e/i unprojected; 601.2a excluded. Structural children create no literal edges.

Mana distinctions remain: 605.3b activated no-stack; 605.4a independently triggered
no-stack/immediate resolution; 605.3b→405.6c resolved; 405.6c/601.2g/109.4a→605
complete-family mappings to 13 concrete units. No synthetic 605 or direct 605.4a→405.6c
or 117 citation. 405.6c priority return is limited to the same player holding
priority before activation; no finer mana/other-effect ordering is inferred.
109.4a hypothetical-stack attribution remains separate. Casting, 601.2g and
Madness improve only indirectly. 603 and delayed controller frontiers stay open.

All ten procedure responsibilities remain OPEN / EXECUTION_BLOCKED. Real
execution remains BLOCKED; the real profile is DESIGN_ONLY / NOT EXECUTABLE /
REAL_EXECUTION_PROFILE_NOT_READY. No runtime, source-permission, gameplay,
collection, catalog, MB2, admission, workflow or timeout behavior changes.
`source_policy_clearance=not_granted`; all five source-content permissions remain
NOT_ESTABLISHED.

Exactly one proposed subsequent milestone after blocker reassessment:
**Shared Casting-Stage Gap Scope Design**, review-only, zero projected units,
empty projection allowlist. Compare the shared missing-import frontier with
independent reveal, rollback, triggered and runtime frontiers before selecting
any future source boundary.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false

Full discovery and actual publication are required. Final measured local and
hosted results are appended to the same draft PR and the local completion report
after all gates finish; this checkpoint does not declare merge readiness.

## Complete changed-file inventory

- `PROJECT_INVENTORY.md`
- `docs/GAMEPLAY_RULES_BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTION.md`
- `docs/GAMEPLAY_RULES_BOUNDED_ACTIVATED_ABILITY_PROCEDURE_VALIDATION.md`
- `docs/HANDOFF.md`
- `docs/NEXT_TASK.md`
- `docs/SESSION_STATE.md`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/casting-import.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/composite-coverage.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/consumer-reassessment.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/cost-analogy.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/design-source-correspondence.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/local-scope.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/mana-relationships.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/manifest.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/overall-readiness.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/procedure-responsibilities.json`
- `reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/projection.json`
- `src/gameplay_rules/activated_ability_projection/__init__.py`
- `src/gameplay_rules/activated_ability_projection/__main__.py`
- `src/gameplay_rules/activated_ability_projection/contracts.py`
- `src/gameplay_rules/activated_ability_projection/package.py`
- `src/gameplay_rules/activated_ability_projection/pins.json`
- `src/gameplay_rules/activated_ability_projection/reviews.py`
- `src/gameplay_rules/activated_ability_projection/scope.py`
- `src/gameplay_rules/activated_ability_projection/source.py`
- `tests/activated_ability_preservation.py`
- `tests/activated_ability_projection_preservation.py`
- `tests/fixtures/bounded-activated-ability-protected-state.json`
- `tests/test_activated_ability_procedure_design.py`
- `tests/test_gameplay_rules_bounded_activated_ability_preservation.py`
- `tests/test_gameplay_rules_bounded_activated_ability_procedure_consumers.py`
- `tests/test_gameplay_rules_bounded_activated_ability_projection_validation.py`
- `tests/test_gameplay_rules_bounded_activated_ability_source.py`
