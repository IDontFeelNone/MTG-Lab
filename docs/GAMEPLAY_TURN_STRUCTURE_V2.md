# Gameplay Turn Structure V2 — fictional untap, upkeep and draw windows

The existing `GameplayRulesEngine` and `GameplaySession` now support a separately
selected fictional five-window profile. Untap and draw mutate actual native state;
upkeep and draw priority use the existing pass/stack machinery. This is not complete
Magic turn compliance. Combat, other omitted Magic steps, targeting, damage,
triggers, replacements/prevention, continuous effects/layers, first-player draw
exceptions, multiplayer/Commander and real Oracle integration are not added.

Architecture v13 and Decision 017 remain unchanged. No canonical Card/Printing,
MB2 data/admission, source permission, pack simulation or governance change occurs.
No real rules source is inspected, projected or promoted.

## Compatible explicit contracts

The new profile is `fictional-two-player-turn-structure-v2`, under the existing
`gameplay-kernel-v1` primitive interpreter. Its snapshot requires the existing
fictional evidence plus explicit untap, upkeep and draw rule categories. Its exact
structured `turn_start` policy adds `priority_windows=upkeep_and_after_draw` to the
existing controlled-battlefield untap, one draw, index-zero library top and
empty-library-unsupported policy. Exact ordered windows and main/action timing are
validated; no window behavior is inferred from Card names or prose.

| Window | Automatic boundary and player decisions |
|---|---|
| beginning/untap | Turn change queues exactly `untap_active_player`; no priority. Native untap then enters upkeep |
| beginning/upkeep | Active-player priority. Existing passes/stack resolution apply; empty stack and a complete pass cycle are required to advance |
| beginning/draw | Advancement queues `draw_for_turn`, then `perform_state_based_actions`; priority only after both finish. Another pass cycle is required to leave draw |
| main/action | Existing main-action timing, land allowance, costs and spell rules |
| ending/end | Existing simplified ending window; completed pass cycle enters the next player's untap |

Both old profiles remain unchanged: `fictional-two-player-v1` with state V1 and
`fictional-two-player-turn-lifecycle-v1` with state V2. Their rules snapshots,
semantics, fixtures, state IDs and golden session reports are not migrated.

The new profile requires **`gameplay-state-v3`**. `WindowedGameState` is only a
versioned envelope inheriting the existing ordered state/core validation and
immutable codec; it introduces no state store or separate controller. Existing
`GameState.create`/`from_dict` and public loaders dispatch only explicit versions.
The immutable `STATE_SCHEMAS_BY_PROFILE` map binds each of the three profiles to
its exact state schema in both engine and session. Cross-profile schemas reject.
Rules, semantics, actions, native transitions and session report formats stay at
their existing versions; exact profile/snapshot/nested schema already bind them.

V3 reuses `library_order` without changing its meaning: every exclusive player
library has an exact duplicate-free top-first object-ID array, whose membership
matches the zone. Object-array order, lexical IDs and random selection have no
library meaning. Library/hand scope, owners, strict types and closed fields retain
the existing validation. There is no shuffle, dealing or opening-hand algorithm.

Only the phase/queue meaning of the existing `turn_start` progress object is new
in V3. Turn number and player bind the current turn/active player:

- `pending_untap`: beginning/untap, no stack or pending pass, no priority, queue
  exactly `[untap_active_player]`.
- `upkeep`: beginning/upkeep; only existing pass/checkpoint/stack/advance queues
  are allowed. No automatic untap or draw may be rescheduled here.
- `pending_draw`: beginning/draw, no stack or pending pass, no priority, queue
  exactly `[draw_for_turn, perform_state_based_actions]`.
- `complete`: beginning/draw, main/action or ending/end. Untap/draw cannot be
  queued again. Settled in-progress windows require a priority holder. An advance
  queue cannot bypass a nonempty stack.

Malformed progress/window combinations, forged queues and repeated automatic
requests reject. A valid explicitly supplied settled initial position remains an
authored input, not authenticated proof that prior events happened. Session load
still requires a settled decision boundary; it does not secretly perform actions.
Replay, not a checksum alone, establishes consistency with a selected history.

## Native sequencing and failure behavior

Turn advancement changes the active player, clears mana and resets land allowances
as before. It enters untap with no priority. The existing native untap primitive
untaps eligible battlefield objects **controlled** by the active player, regardless
of owner or battlefield-zone owner. Inactive controlled objects and nonbattlefield
objects are untouched. Unknown tap state, incomplete/unsupported semantics,
unimplemented restrictions and relevant unsupported effects fail closed.

The untap transition itself changes the window to upkeep, changes progress to
upkeep and grants active-player priority. It does not draw. Two player passes with
a stack cause the existing checkpoint → top resolution → checkpoint sequence,
returning priority **in upkeep**. Another pass cycle is necessary to leave upkeep.
An instant uses existing timing/cost checks; sorceries and land plays remain
illegal outside main/action. No upkeep trigger processing is implied.

Two passes with an empty stack schedule checkpoint and advancement to draw.
Advancement grants no priority and queues the ordered draw/checkpoint. Draw moves
exactly index zero of the active player's library into that player's exclusive
hand, preserving owner and assigning controller to that player. It removes that
object from library order, records the native zone change and marks progress
complete. The checkpoint must run before priority is granted. Resolving a later
spell in draw does not redraw or advance the step automatically.

Rule references and unknown/unsupported coverage checks use the same category
selection. All new-profile actions depend on the explicit upkeep-window evidence;
unknown upkeep evidence cannot authorize window actions. No source text executes.

Player actions during a mandatory boundary fail native legality. Session callers
cannot manually submit system actions. Stale actions and unsupported behavior do
not mutate prior state. Mandatory actions are staged under the existing atomic
session submission: a blocked automatic step rolls back the **entire submission**,
including tentative advancement. Previously committed actions/history remain.
The eight-system-transition, 128-attempt and 2 MiB bounds remain unchanged.

An empty-library draw remains `UNSUPPORTED` with exact native reason
`empty_library_draw_rule_not_implemented`. The session's existing
`blocked_system_action` error carries that reason. It stays in the last committed
upkeep state; it does not fabricate a draw or declare a player lost. No draw-from-
empty-library loss rule, replacement rule or source authority is invented.

## Working API and CLI

```python
from pathlib import Path
from gameplay_rules.session import load_gameplay_session

f = Path('tests/fixtures/turn_structure_v2')
s = load_gameplay_session(
    rules_path=f / 'rules-snapshot.json',
    semantics_paths=sorted(f.glob('*.semantics.json')),
    state_path=f / 'initial-state.json')
s.submit(s.action('pass_priority', 'A'))
entry = s.submit(s.action('pass_priority', 'B'))
assert s.state.step == 'upkeep' and s.state.priority_player == 'B'
s.submit(s.action('activate_ability', 'B', object_id='b-resource', ability_id='make-red'))
```

The existing CLI accepts full state-bound native action JSON lines:

```sh
PYTHONPATH=src python -B -m gameplay_rules.session_cli \
  --rules tests/fixtures/turn_structure_v2/rules-snapshot.json \
  --semantics tests/fixtures/turn_structure_v2/blue-pebble.semantics.json \
  --semantics tests/fixtures/turn_structure_v2/ember-scroll.semantics.json \
  --semantics tests/fixtures/turn_structure_v2/moss-plot.semantics.json \
  --semantics tests/fixtures/turn_structure_v2/pebble-resource.semantics.json \
  --semantics tests/fixtures/turn_structure_v2/swift-lantern.semantics.json \
  --state tests/fixtures/turn_structure_v2/initial-state.json \
  --format text < tests/fixtures/turn_structure_v2/actions.jsonl
```

For the second scenario use `stack-initial-state.json` and `stack-actions.jsonl`.
Use `--format json` for machine-readable action results. Use `--replay history.json`
or `--replay stack-history.json` with the corresponding initial state to recompute
saved history; `--expected-session-id` optionally pins its exact identity. These
successful scenarios/replays exit 0. No command writes files or fetches sources.

Public views expose hidden-zone counts, not hidden identities or library order.
Explicit `--history` is a full-information inspection/replay export and includes
hidden state; it is not a public multiplayer view. `replay_session` recomputes
verdicts/transitions and independently invokes native replay, comparing complete
canonical results. Coherently rehashed changed history cannot bypass replay.

## Two actual executable scenarios

The primary fixture begins at A turn 1 ending/end with tapped A/B resources and an
explicit B library `[b-top, b-next]`. The object array places b-next earlier than
b-top; it still draws b-top. No state is injected between the following requests:

| Attempts | Real execution |
|---|---|
| 0–1 | A/B pass; checkpoint, advance into B turn 2 untap with no priority, native untap, upkeep with B priority |
| 2 | B activates the untapped resource, tapping it and adding two red mana |
| 3–4 | B/A pass; checkpoint, enter draw, draw b-top to B hand, checkpoint, B priority |
| 5–6 | B/A pass; checkpoint and advance to main/action |
| 7 | B plays drawn b-top from hand to battlefield |
| 8–9 | B/A pass to ending/end |
| 10–11 | B/A pass; next turn enters A untap, untaps A resource, reaches A upkeep with priority; B resource remains tapped |

This is **12 player requests and 26 actual native transitions**. A's library has
not drawn yet at its new upkeep. Inactive A resource stays tapped throughout B's
turn. Native state changes capture the turn/window/priority/tap/progress/order
changes; draw has the exact `B:library → B:hand` zone change, and land play has
`B:hand → B:battlefield`. The existing phase-advance mana clearing remains intact.

The second scenario uses the existing swift-lantern one-blue instant/no-op spell.
A separately authored fictional blue-pebble merely supplies an explicit blue amount
through the **already implemented** tap/add_mana primitive; no cost/timing rule is
loosened and no new effect interpreter is added. After B reaches upkeep, it taps
that resource, casts and pays for swift-lantern, and both players pass. Resolution
moves the spell to B's graveyard and returns priority in upkeep, with b-top still
in the library. Another pass cycle reaches draw; another reaches main; B plays the
drawn land. This is **11 player requests and 23 actual native transitions**.

Exact snapshot, initial/final state and session identities for both scenarios,
plus final-tree local/hosted receipts, are recorded in the draft PR. The fixture
retains complete computed histories and final JSON/readable views, independently
reproduced by tests. `fictional-rules.txt` is original project-authored evidence
with its exact digest bound in the new snapshot. All old fixtures remain unchanged.

## Preservation, tests and stop

Only models, engine and session have runtime successors. A finite test-only exact
reversible source ledger and one narrow existing helper hook preserve original
source calculations without repinning old manifests or ignoring unknown changes.
There is no new runtime controller, authentication service or governance layer.
Existing V0 and lifecycle V1 full golden sessions, native state identities, pack
V0/V0.1/V0.2 outcomes, historical evidence and source/permission gates remain.
Global historical state documents retain their source-pinned content; this focused
document and draft PR describe the current bounded delivery.

Functional/adversarial tests cover both actual sequences, upkeep mana and stack,
ordered draw/checkpoint priority, timing/priority refusal, manual/repeated system
actions, malformed progress/order/profile, unknown rule evidence, empty library,
unsupported restrictions/effects, immutable inputs/history, exact native/session
replay, both earlier golden histories, public CLI and source preservation.
Complete local discovery and both unchanged hosted outer/nested writer/publication
checks are required before delivery; results belong in the draft PR.

Stop for independent Senior PM review and owner approval. No merge, auto-merge,
future milestone, new source permission or real-card gameplay is authorized.
