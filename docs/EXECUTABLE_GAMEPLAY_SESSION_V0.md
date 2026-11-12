# Executable Gameplay Session V0 — fictional multi-action gameplay

The public `gameplay_rules.session` API makes the existing fictional two-player
kernel usable across successive explicitly selected actions. The existing
`engine.py`, state/action/transition models, costs, semantics, loaders and rules
snapshots remain unchanged. This is a session over those primitives, not a new
rules engine, real Oracle integration or complete Magic simulator.

Architecture v13 and Decision 017 remain unchanged. Real-card gameplay, canonical
admission, source permissions, MB2 data and all real-rule execution gates remain
unaffected. Only the existing project-authored `fictional-two-player-v1` profile
can initialize. No gameplay behavior is inferred from text.

## Public API

```python
from pathlib import Path
from gameplay_rules.session import load_gameplay_session, replay_session
from gameplay_rules.snapshots import load_rules_snapshot, load_card_semantics

fixture = Path('tests/fixtures/gameplay_rules')
session = load_gameplay_session(
    rules_path=fixture / 'rules-snapshot.json',
    semantics_paths=sorted(fixture.glob('*.semantics.json')),
    state_path='tests/fixtures/gameplay_session_v0/initial-state.json')

print(session.view())                 # Turn, phase/step, priority, life, public zones
request = session.action('pass_priority', 'A')  # Explicit selection, exact state binding
result = session.submit(request)      # Native legality and actual kernel transitions
print(session.state.to_dict())        # Independent native GameState
history = session.report()            # Full-information, ordered native replay evidence
```

`GameplaySession(snapshot, semantics, initial_state)` accepts existing verified
model objects. It validates the fictional profile and game/snapshot bindings,
owns independent decoded copies, and requires every known object's exact supplied
semantics. Unknown hidden objects remain unknown. Initialize at a settled player
decision boundary: initial pending-system queues or an in-progress state with no
priority holder refuse. This is a bounded initialization contract, not a new rule.

The session action builder binds the current state; `submit` also accepts a fully
bound native `GameAction`. Stale/wrong game or snapshot bindings and malformed
contracts raise `GameplayContractError` without changing state or history. Direct
caller-selected system actions refuse. Actor IDs are fictional game participants,
not authenticated human identities.

For each valid request, `GameplayRulesEngine.evaluate_action` supplies the verdict.
Only LEGAL requests reach `apply_action`. After a legal player transition, the
session drains **only** mandatory system actions returned by that kernel state,
with actor=None. It never chooses a player's response or invents a due action.
All resulting native transitions are recorded, in order. If a required system
transition blocks or a session bound fails, the entire submission rolls back;
there is no partially committed player action.

ILLEGAL, INDETERMINATE and UNSUPPORTED evaluated attempts are recorded with zero
transitions and unchanged state identity. Their attempt record changes the session
history identity, not the game state. Contract failures do not add a record.

## Priority, stack and turn behavior

One pass gives priority to the other player. Two passes cause the existing kernel
to schedule a state-based checkpoint followed by either stack-top resolution or
step advancement. Resolution schedules its existing post-resolution checkpoint,
then returns priority. Remaining stack objects do not all auto-resolve: they need
another player pass cycle. No system action can skip an available player response.

The existing fictional turn windows are beginning/start, main/action, ending/end.
Crossing the end clears mana, resets land allowances and changes active player as
specified by the kernel. **There is no automatic draw or untap implementation.**
The wrapper does not add these actions, combat, targeting, triggered/replacement/
continuous effects or multiplayer mechanics. Unsupported dimensions return the
kernel's explicit refusal, never an invented effect.

## State, display and replay integrity

`state` returns an independent native state. `view()` includes exact current
state/rules IDs, active player, turn, phase/step, priority, life/mana/land allowances,
public-zone contents, hidden-zone counts and game outcome. It never displays
hidden object identities. `render_session_view` is genuinely readable.

`report()` is deliberately **full information**, including the initial native
state, submitted native actions, legality results and every native transition.
It is for trusted local inspection/replay, not a public multiplayer display.
It may expose hidden state. The CLI only exports it with explicit `--history`.

Reports use `gameplay-session-v0` and the existing domain-separated
`content_identity` codec. They bind the initial state, exact rules snapshot,
sorted semantics identities, ordered attempts and current state. Neither a digest
nor a replay event grants permission, human review or real-game authority.

```python
again = replay_session(
    load_rules_snapshot(fixture / 'rules-snapshot.json'),
    [load_card_semantics(p) for p in sorted(fixture.glob('*.semantics.json'))],
    history, expected_session_id=history['session_id'])
assert again.report() == history
```

Replay reconstructs the initial session, reevaluates each request, recomputes each
full transition and independently invokes native `replay_transition`. Canonical
JSON byte comparisons reject boolean/integer substitutions, unknown fields and
coherently rehashed altered transition claims. An optional externally retained
`expected_session_id` binds the original complete session. Without that pin a
different valid initial scenario is a different fictional input, not an
independently authenticated historical event.

New session limits: 64 explicit semantic definitions, 128 evaluated player
attempts, eight mandatory system transitions per attempt, and the existing 2 MiB
contract-byte bound for combined inputs and canonical history. Limits fail closed
before state/history commit. No inherited gate or timeout is increased. Native
contract validation and the old kernel API remain unchanged.

## Small CLI

Use the module entry point; no changes to the existing unified CLI are required:

```sh
PYTHONPATH=src python -B -m gameplay_rules.session_cli \
  --rules tests/fixtures/gameplay_rules/rules-snapshot.json \
  --semantics tests/fixtures/gameplay_rules/ember-scroll.semantics.json \
  --semantics tests/fixtures/gameplay_rules/moss-plot.semantics.json \
  --semantics tests/fixtures/gameplay_rules/pebble-resource.semantics.json \
  --semantics tests/fixtures/gameplay_rules/swift-lantern.semantics.json \
  --state tests/fixtures/gameplay_session_v0/initial-state.json \
  --format text < tests/fixtures/gameplay_session_v0/actions.jsonl
```

The CLI accepts native, explicitly bound `GameAction` JSON lines, not natural
language or an arbitrary game-state language. It shows the initial public state
and each verdict/updated public state, continuing after rejected choices. This
intentional demonstration exits2 because it includes rejected actions; all legal
later actions still execute. A fully legal stream exits0. Contract errors preserve
the prior state; an oversized line stops rather than executing its tail.

`--format json` emits one compact JSON event per line. `--history` additionally
prints the full-information replay report. `--replay FILE` verifies a saved report
against the explicitly selected initial-state, rules and semantics files;
`--expected-session-id ID` optionally pins it. Replay exits0 when the complete
history reproduces, even if that history includes correctly rejected attempts.
Commands write no files and make no provider/network calls.

## Complete actual demonstration

`tests/fixtures/gameplay_session_v0/initial-state.json` is a newly identified
beginning/start state under the **unchanged** original rules/semantics fixtures.
It starts turn1, player A active/priority, both life10, no mana. It is an authored
fictional initial position, not a shuffled opening-hand/deck/draw simulation.

`actions.jsonl` holds 15 explicit native requests. `history.json` holds their
actual computed results, not execution instructions or a prepared-answer policy.

| Attempts (zero-based) | Actual result |
|---|---|
| 0 | Land in beginning window rejected ILLEGAL; state unchanged |
| 1 | B lacks priority; rejected ILLEGAL; state unchanged |
| 2–3 | A/B pass; checkpoint and advancement enter main/action |
| 4 | Play moss-plot from A's hand to battlefield; one land allowance consumed |
| 5 | Cast without mana rejected ILLEGAL; state unchanged |
| 6 | Existing pebble-resource make-red tap ability adds two red mana |
| 7 | Cast ember-scroll; spend one red plus one generic using that pool; hand→stack |
| 8–9 | Both pass; checkpoint, real stack-top resolution, checkpoint; spell→graveyard; B life10→8 |
| 10 | declare_attackers unsupported; no combat or state change |
| 11–12 | Both pass; advance to ending/end |
| 13–14 | Both pass; advance into B's turn2, beginning/start, B priority |

The played **moss-plot has no mana ability** in the retained semantics. Mana comes
from the separate pre-existing pebble-resource, without borrowing abilities.
The life adjustment is the existing fixed opponent-life primitive, not newly
implemented targeting or a Magic damage procedure. Pebble remains tapped because
untapping is not modeled. There are **20 actual native transitions**, 11 accepted
player attempts, three ILLEGAL attempts and one UNSUPPORTED attempt.

Session identity:
`sha256:4bc642bec3c5a95f3925b1c7ce4711dbeb1bc5140409b8cebb139fdb707be308`

Final state:
`sha256:3d50568ea0ec2f7a1bfa471e9c6fca3aff3f8040096dff31d849a634809804e0`

The full final public JSON and readable view are retained beside the history.
Tests reproduce the entire session and compare exact native state, action,
legality, transition and session identities. Additional tests cover multi-object
LIFO stack behavior, game-ending checkpoints, stale/foreign bindings, illegal
land/timing/payment, unsupported effects, private ownership, malformed CLI input,
strict JSON/replay and atomic failure bounds.

## Preservation and delivery

Only the session module and its CLI are added to runtime. The native kernel,
models, loaders, costs, rule snapshots and all prior gameplay fixtures remain
byte-identical, as do canonical data, permissions, real-rule evidence, Product
simulation and historical design packages. A finite test-only source ledger pins
only these two additions and the narrow historical-guard hook; unknown neighboring
files and changed source bytes remain visible/rejected. No historical evidence
identity is repinned and no runtime admission gate is bypassed.

Final-head complete local discovery, hosted outer/nested discovery and actual
writer/publication/readback receipts belong in the draft PR. This document does
not claim those gates passed before they run. Stop for independent Senior PM
review and owner approval; no merge, auto-merge or future work is authorized.
