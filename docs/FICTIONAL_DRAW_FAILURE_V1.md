# Fictional Draw-Failure and State-Based Loss V1

The public native kernel and session support the explicitly selected
`fictional-two-player-draw-failure-v1` profile with `gameplay-state-v4`.
This is project-authored fictional executable policy, not an implementation claim
about arbitrary Magic Cards, CR rules or Oracle text. Architecture v13, Decision
017, source policies and all real-rule execution/admission gates are unchanged.

## Exact policy and version boundaries

The profile reuses Turn Structure V2's untap/upkeep/draw/main/end sequence,
priority, stack, ordered library, costs, existing effects and mandatory checkpoint.
It requires explicit fictional `draw_failure` rule evidence and the exact policy
`empty_library=record_attempt_then_state_based_loss` in `turn_start`.
No capability vocabulary or old profile is reinterpreted. State V4 adds only
`failed_draw_players`, a duplicate-free array initially empty. The existing
`state_based_actions` capability remains bounded to configured life loss and,
only in this profile, the recorded automatic draw failure.

- A nonempty ordered library draws exactly its first object into the active
  player's hand. Drawing the last card succeeds and leaves the failure array empty.
- An empty library alone causes no loss. A due native `draw_for_turn` on an empty
  library is a legal automatic attempt: it creates/moves no object, preserves
  library order, records the active player and marks draw progress complete.
- Both outcomes retain the mandatory `perform_state_based_actions` queue. No
  priority is granted before that checkpoint. No generic draw effect is added.
- At the checkpoint the union of recorded failed-draw players and players at/below
  the configured life threshold loses simultaneously. Remaining players win; if
  both lose, no player wins. The state ends with no priority or pending actions.
  The failure record remains for inspection and replay.
- Unknown life or unsupported effects/restrictions still block rather than
  inventing an outcome. The session's existing atomic submission rolls back if
  any mandatory transition blocks.

V4 validates that a nonempty failure array can name only the active player, in
beginning/draw with complete progress, empty library, no stack or pass residue.
An in-progress failure requires exactly the immediate checkpoint and no priority;
a terminal failure must include that player among the losers. Duplicate/foreign
flags, repeat draw queues and contradictory progress reject. Schema validation
establishes consistency, not authenticity of a supplied historical position;
exact native/session replay recomputes the actual transitions.

The V0, Turn Lifecycle V1 and Turn Structure V2 profiles, snapshots, state IDs and
full golden sessions retain their original meanings. Their empty-library draw
continues to return `empty_library_draw_rule_not_implemented` and roll back.
The new profile is never selected implicitly. Session/report/action/transition
versions, byte limits and system-transition limits are unchanged.

## Working public API

```python
from pathlib import Path
from gameplay_rules.session import load_gameplay_session

f = Path('tests/fixtures/draw_failure_v1')
s = load_gameplay_session(
    rules_path=f/'rules-snapshot.json',
    semantics_paths=sorted(f.glob('*.semantics.json')),
    state_path=f/'initial-state.json')
for player in ['A', 'B', 'B', 'A']:
    entry = s.submit(s.action('pass_priority', player))
assert s.state.status == 'ended'
assert s.state.failed_draw_players == ('B',)
assert s.state.loser_ids == ('B',) and s.state.winner_ids == ('A',)
```

The fixture starts at A's end with B's explicitly empty library. Four requests
produce eleven native transitions: turn change, B untap/upkeep, pass boundary,
empty draw attempt and state-based loss. The last request records five transitions:
pass, checkpoint, advancement, attempted draw, loss checkpoint. All five grant no
priority. The draw has no zone changes or created cards; its state delta records
`failed_draw_players=[] -> ['B']` and completed progress. Both players retain life
10; B's loss therefore comes from the attempted draw, not a fabricated life event.

The existing CLI supports the new explicit snapshot/state without new commands:

```sh
PYTHONPATH=src python -B -m gameplay_rules.session_cli \
  --rules tests/fixtures/draw_failure_v1/rules-snapshot.json \
  --semantics tests/fixtures/draw_failure_v1/blue-pebble.semantics.json \
  --semantics tests/fixtures/draw_failure_v1/ember-scroll.semantics.json \
  --semantics tests/fixtures/draw_failure_v1/moss-plot.semantics.json \
  --semantics tests/fixtures/draw_failure_v1/pebble-resource.semantics.json \
  --semantics tests/fixtures/draw_failure_v1/swift-lantern.semantics.json \
  --state tests/fixtures/draw_failure_v1/initial-state.json --format text \
  < tests/fixtures/draw_failure_v1/actions.jsonl
```

Use `--format json` for machine-readable output, `--history` for explicit
full-information native transitions, or `--replay tests/fixtures/draw_failure_v1/history.json`
to recompute the saved session. Ordinary public views retain their established
fields; failed-draw details are in the native state/history. The committed history,
final JSON/text views and exact identities are reproduced by functional tests.

## Validation, preservation and limitations

`test_draw_failure.py` covers successful last-card draw, native failed attempt,
mandatory loss/checkpoint, simultaneous life/draw loss, duplicate/manual/terminal
actions, unknown evidence/life, whole-submission rollback, exact replay and
coherently rehashed tampering, read-only public loader/CLI and immutable data.
Existing engine/session/lifecycle/turn-structure suites verify all older goldens.
A finite exact reversible test-only source ledger preserves inherited pins; it
accepts only the documented predecessor/successor bytes and rejects unknown drift.
No runtime evidence consumer is bypassed and no historical fixture is rewritten.

No triggers, replacements/prevention, combat, generic draw effects, special loss
exceptions, multiplayer, format rules or real-Card execution are implemented.
No canonical data, pack simulation, source permission, architecture or governing
decision changes occur. Final local and hosted receipts belong in the draft PR.
Stop for Project Manager review and owner-controlled merge; no future work is
begun or authorized by this delivery.
