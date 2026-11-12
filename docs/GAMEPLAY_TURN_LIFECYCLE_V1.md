# Gameplay Turn Lifecycle V1 — fictional automatic untap and draw

This implements turn-start operations inside the existing `GameplayRulesEngine`
and `GameplaySession`. It is project-authored fictional gameplay, not a claim of
comprehensive Magic compliance. Architecture v13 and Decision 017 are unchanged;
real Oracle/CR semantics, source permissions, MB2 identities and production
admission remain separate and unaffected. No real rules source was acquired.

## Explicit compatible profile and state version

Existing `fictional-two-player-v1` snapshots and `gameplay-state-v1` retain their
exact behavior and identities, including immediate priority at the old turn-change
boundary. No old fixture, snapshot, semantics or session report is migrated.

The additive profile is `fictional-two-player-turn-lifecycle-v1`, under the same
`gameplay-kernel-v1` primitive interpreter contract. Its snapshot requires source-
bound `untap` and `draw` rule categories and this exact structured policy:

```json
{"turn_start":{"untap":"controlled_battlefield","draw_count":1,"library_top":"first","empty_library":"unsupported"}}
```

The three supported windows remain beginning/start, main/action, ending/end.
The beginning window has no player decision until its queued operations finish;
there is no separate upkeep or draw-step response window. These are bounded
fictional rules, with no first-player draw exception, triggers, replacement effects
or complete seven-step turn model. No text parsing selects their behavior.

This profile requires `gameplay-state-v2`. `GameState.create` and `from_dict`
dispatch only an explicitly supplied V2 schema to `OrderedGameState`, a versioned
envelope inheriting the same state implementation, core validator and immutable
codec. The ordinary public loaders, actions, transitions and replay remain usable.
A V1 state with the new profile or a V2 state with the old profile refuses.

V2 adds only two fields:

- `library_order`: an exact map from each player's exclusive library zone ID to an
  ordered array of all and only that library's object IDs. Index zero is the top.
  Both exclusive libraries and hands are required. Duplicates, omitted/foreign
  entries, shared libraries, wrong ownership and malformed arrays reject. The
  object array's order and lexical identifiers have no draw meaning. An empty
  array is a valid explicitly empty library, not an ambiguous unknown order.
- `turn_start`: `{turn_number, player_id, status}` bound to the current turn and
  active player. `pending_untap` and `pending_draw` require the exact mandatory
  queue at beginning/start with no stack, pending pass or player priority.
  `complete` cannot reschedule a turn-start operation. Historical state/replay
  identity binds the marker; it is not authenticated proof that an event occurred.

An explicitly supplied settled initial position declares its current turn-start
operations already complete. Initialization does not perform a hidden draw or
untap. Successive turn crossings perform them automatically. There is no shuffle,
opening-hand, mulligan, initial-deal or random library construction algorithm.

## Actual automatic transitions

On the existing `advance_step_or_phase` crossing ending/end into a new turn, the
kernel changes active player, clears mana and resets land allowances as before,
then sets progress to pending_untap and queues:

1. `untap_active_player`: untap battlefield objects **controlled** by the active
   player, independent of their owner or the battlefield zone's owner. Unknown tap
   state, missing/partial semantics, unimplemented restrictions and affected
   unknown/unsupported active effects fail closed. Inactive controlled objects
   and nonbattlefield objects are unchanged. Progress becomes pending_draw.
2. `draw_for_turn`: remove index zero from the active player's explicit library
   order, move that exact object to that player's exclusive hand, preserve its
   owner and assign controller to that player. Hidden unknown identity remains
   unknown; drawing never invents Card semantics. Progress becomes complete.
3. `perform_state_based_actions`: reuse the existing bounded life checkpoint.
   Only after the queue empties is the active player granted priority.

The untap changes appear in native `state_changes.objects`. Draw produces the
native exact `zone_changes` record and state changes for objects, order, progress,
revision and pending queue. Every transition has its action/state/rules identities
and relevant rule citations. The session's existing eight-system-transition bound
is unchanged (a turn-crossing submission needs five automatic transitions).

Manual selection of these system actions through `GameplaySession.submit` rejects.
The public kernel additionally requires the exact due queue and actor=None.
Replaying a stale or already-completed draw does not draw another card.

### Empty library and atomic refusal

An empty-library `draw_for_turn` returns the native `UNSUPPORTED` legality result
with `empty_library_draw_rule_not_implemented`. It does not declare a player lost
or pretend a draw succeeded. The session raises its existing `blocked_system_action`
contract error with the underlying precise reason, and atomically preserves the
entire pre-submission state **and** history, including any tentative untap/advance.
There is no partial turn commit. The same applies to blocked untap restrictions.
The kernel's native result exposes machine-readable reason codes; the CLI reports
the blocked boundary and readable reason without making a gameplay loss claim.

## Working public API and CLI

```python
from pathlib import Path
from gameplay_rules.session import load_gameplay_session

f = Path('tests/fixtures/turn_lifecycle_v1')
session = load_gameplay_session(
    rules_path=f / 'rules-snapshot.json',
    semantics_paths=sorted(f.glob('*.semantics.json')),
    state_path=f / 'initial-state.json')
session.submit(session.action('pass_priority', 'A'))
result = session.submit(session.action('pass_priority', 'B'))
assert session.state.active_player == session.state.priority_player == 'B'
assert len(result['transitions']) == 6
session.submit(session.action('activate_ability', 'B',
                            object_id='b-resource', ability_id='make-red'))
```

The existing module CLI requires no new controller or command route:

```sh
PYTHONPATH=src python -B -m gameplay_rules.session_cli \
  --rules tests/fixtures/turn_lifecycle_v1/rules-snapshot.json \
  --semantics tests/fixtures/turn_lifecycle_v1/ember-scroll.semantics.json \
  --semantics tests/fixtures/turn_lifecycle_v1/moss-plot.semantics.json \
  --semantics tests/fixtures/turn_lifecycle_v1/pebble-resource.semantics.json \
  --semantics tests/fixtures/turn_lifecycle_v1/swift-lantern.semantics.json \
  --state tests/fixtures/turn_lifecycle_v1/initial-state.json \
  --format text < tests/fixtures/turn_lifecycle_v1/actions.jsonl
```

Use `--format json` for machine-readable ordered action results. Replace stdin
with `--replay tests/fixtures/turn_lifecycle_v1/history.json` to reproduce the
complete history, optionally pinning its session identity. `--history` explicitly
exports full-information history (including hidden order); ordinary public views
show only hidden-zone counts. All three successful demonstration commands exit 0.
Commands write no files, fetch no sources and infer no abilities.

## Demonstration and exact replay evidence

The new fixture is fully fictional, using rebound copies of the existing four
fictional semantics under the new snapshot; all prior fixtures remain unchanged.
`fictional-rules.txt` is new project-authored evidence with its exact digest bound
in the new snapshot. Ten explicit player requests compute 24 native transitions.

| Attempt | Actual result |
|---|---|
| 0 | A passes in turn 1 ending/end; B gets priority |
| 1 | B passes; checkpoint, turn advance to B turn 2, B resource untap, b-top draw into B hand, checkpoint, B priority. A resource stays tapped |
| 2 | B activates that resource, tapping it and adding two red mana |
| 3–4 | B/A pass to main/action |
| 5 | B plays the newly drawn b-top land from hand to battlefield |
| 6–7 | B/A pass to ending/end |
| 8–9 | B/A pass; enter A turn 3, untap A resource, draw a-next into A hand, checkpoint; A priority. B resource stays tapped |

`b-next` precedes `b-top` in the object array but **b-top** is index zero in the
explicit library order. It is the card drawn; `b-next` remains in B's library.
The new fixture contains exact initial state, action lines, complete computed
history and final JSON/readable views. Tests separately exercise reversed library
order, changed control, unknown identities, empty library and unsupported effects.

- Snapshot: `sha256:5981a209c724637b2f2712c921a983d4afa75c6086b5daca22037928f2763f91`.
- Initial state: `sha256:f804b254f501e89380971fe0e1535f2c8de03da78044aaa065447567f532b5e3`.
- Final state: `sha256:c002496918e9393ac4d42cf8a1ce41b130b3f3cb5c6084a5dbe2f47519d6c419`.
- Session: `sha256:3b3505ceffec0740a1178661402f9ca6ef0c5472be6904562b8e9e7b76c890de`.

The same session report schema `gameplay-session-v0` is retained: its already
explicit `execution_profile`, rules identity and nested state schema distinguish
the new lifecycle. Native replay recomputes all operations and full session replay
compares canonical bytes; checksums alone are insufficient. The V0 golden session
`sha256:4bc642bec3c5a95f3925b1c7ce4711dbeb1bc5140409b8cebb139fdb707be308`
and final state `sha256:3d50568ea0ec2f7a1bfa471e9c6fca3aff3f8040096dff31d849a634809804e0`
reproduce unchanged.

## Preservation and stopping boundary

The only inherited runtime successors are models, engine and session. The finite
test-only reversible adapter pins exactly those changes and two narrow historical-helper
routes, preserving prior source calculations without repinning their historical
manifests or accepting arbitrary source additions. Existing canonical data, CR
projections, semantic decisions, permissions, market/collection data, pack models,
MB2 evidence, Architecture/Decision 017 and workflows/timeouts remain unchanged.
Inherited state documents retain historical content; this focused document and the
final draft PR record the current bounded delivery and validation.

Complete final-tree local discovery and both hosted outer/nested writer and
publication/readback receipts belong in the draft PR; no gate is claimed green
before it runs. Stop for independent Senior PM review and owner approval. No merge,
auto-merge, additional rule projection or future milestone is authorized or begun.
