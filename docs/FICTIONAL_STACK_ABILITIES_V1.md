# Fictional Stack-Using Activated Abilities V1

The existing `GameplayRulesEngine`, `GameplaySession`, public loaders and CLI
support the explicit `fictional-two-player-stack-abilities-v1` profile and
`gameplay-state-v5`. This is a bounded project-authored fictional procedure, not
real Magic Card execution or complete activated-ability rules compliance.
Architecture v13, Decision 017, source permissions and real-rule execution gates
remain unchanged. No new controller, repository or persistence service is added.

## Exact supported procedure

The selected ability is an existing structured `uses_stack=true` ability with
one `adjust_life` effect whose `target=controller` means its fixed recipient,
not a target-selection procedure. No opponent recipient, add-mana stack ability,
new effect kind or arbitrary ability interpreter is supported.

The exact source-bound `stack_activation` policy is:

```json
{"timing":"priority","effect":"adjust_controller_life","source_at_resolution":"same_controlled_battlefield_object"}
```

The activating player must hold priority, control the known battlefield source,
and select its exact supported ability ID. Existing evidence/capability checks,
unknowns, restrictions, supported mana planning, explicit payment and optional tap
cost checks apply. The profile fixes ability timing to priority windows. The
existing Card `timing` field continues to govern Card casting; it is not silently
repurposed as an ability timing field. Special timing permissions and extra
ability/target fields are unsupported or schema-invalid.

A legal activation pays the supported mana and tap costs once and creates exactly
one typed ability entry. The source stays on the battlefield with its original
object identity and cost changes. The life effect does not happen at activation.
The activator retains priority. Existing player passes and supported responses
apply; two passes schedule the existing checkpoint, one top-entry resolution and
post-resolution checkpoint. The remaining entries need their own pass cycles.
No ability countering or arbitrary stack operations are implemented.

Ability resolution reads the exact bound ability semantics, changes the captured
controller's life once, removes that entry and retains the separate source object.
It does not pay the costs again. The ordinary mandatory checkpoint then evaluates
existing life/draw-failure loss conditions before active-player priority returns.
A terminal result grants no priority; no remaining stack entry auto-resolves.

## Explicit typed stack and compatibility

State V5 adds only `stack_entries` to the V4 envelope. In this explicit version,
`stack` contains entry IDs in bottom-to-top order, and `stack_entries` contains the
same ordered entries. Each closed record has:

- `entry_id`: deterministic `gameplay-stack-entry-v1` domain-separated identity.
- `kind`: exactly `spell` or `activated_ability`.
- `source_object_id`, `semantics_id`, `controller`, `ability_id` (null for spells),
  and `origin_action_id`.

A spell entry refers to its actual Card object in the stack zone. An ability entry
refers to its source and never becomes a fabricated Card object: there is no
`card_id`, owner, zone or copied Card dossier on the entry. Entry and Card-object
IDs must be disjoint. Exact entry order/membership, unique IDs/originating actions,
content identities, spell bindings and player references are validated. No one
action can claim multiple pending entries. Repeated activations, where tap/mana
costs permit them, have different state-bound actions and entry identities.

All zone/object/library/progress validation delegates to the existing state
validators using only the actual spell Cards as their historical Card-stack view.
Additional checks prevent ability-only stacks from bypassing automatic or advance
boundaries. The same native priority/resolution controller handles both kinds.

Only the new profile adds a `stack_entries` public summary and a readable typed
stack section. `stack_count` counts logical entries; stack-zone objects are actual
spell Cards only. The summary shows kind, entry ID and controller; source/ability
references are hidden when the source is not in a public zone. Full native records
remain available through `session.state.stack_entries` and explicit history. Older
public views remain byte-identical. No new CLI command is introduced.

All four earlier fictional profiles and their state schemas, snapshots, semantics,
golden identities and reports retain their meanings. Old definitions are never
migrated. Stack abilities remain unsupported in older profiles. The new profile
inherits Turn Structure V2 and Draw-Failure V1 behavior explicitly. Existing
no-stack mana abilities remain immediate. Kernel/capability/Card-semantics/action/
transition/session versions, input limits and system-transition bounds stay fixed.

## Source-state boundary and refusal

This fiction deliberately requires the same known battlefield source, controller
and exact semantics through resolution. Source departure, control/semantic changes,
missing source information and unsupported interactions block computation. This
is a presence-pinned fictional rule, not a claim about general Magic source
independence. No last-known-information mechanism or surrogate Card is invented.
State structure and executable semantics remain separate validation boundaries;
a structurally consistent authored pending entry is not proof it was activated.
Exact replay establishes consistency with the chosen native action history.

The unchanged session stages an entire submission and its mandatory transitions.
If a checkpoint/resolution blocks, state and history roll back together. Illegal
requests leave the game state unchanged; evaluated rejected attempts retain their
existing history semantics. Manual system actions and stale requests reject.
Unknown life, unsupported effects/restrictions/costs, triggers, replacements,
prevention, continuous effects, targeting and unknown stack operations fail closed.

## Actual fictional demonstration

`tests/fixtures/stack_abilities_v1/` contains original fictional evidence, validated
rules/semantics/initial state, exact action JSONL, computed full golden history and
final readable/JSON views. The new pulse-stone is a fictional fixture only, outside
canonical Card/Printing data. Its one `pulse` ability costs one red mana plus a tap
and adjusts its controller's life by two on resolution. Existing fixture Card
behaviors are retained under explicit new snapshot bindings.

Ten explicitly selected requests yield nineteen native transitions:

1. A activates a-pulse, pays/taps once, retains priority and life 10.
2. A passes; B activates b-pulse and casts the existing one-blue no-op instant.
3. Both pass: the instant resolves first and moves its actual Card to graveyard.
4. Another pass cycle resolves B's entry: B becomes life 12, A stays 10.
5. Another cycle resolves A's entry: A becomes life 12; stack is empty.

Both source objects remain tapped in their battlefield zones. No state is injected
between requests. Negative tests use explicitly authored fictional positions;
they are not independently observed games or real-Card semantic approvals.

```python
from pathlib import Path
from gameplay_rules.session import load_gameplay_session

f = Path('tests/fixtures/stack_abilities_v1')
s = load_gameplay_session(rules_path=f/'rules-snapshot.json',
    semantics_paths=sorted(f.glob('*.semantics.json')),
    state_path=f/'initial-state.json')
entry = s.submit(s.action('activate_ability', 'A',
    object_id='a-pulse', ability_id='pulse'))
assert s.state.players[0]['life'] == 10
assert s.state.stack_entries[0]['kind'] == 'activated_ability'
```

The existing CLI accepts these same files and `actions.jsonl` on stdin with
`--format text` or `--format json`; pass each `*.semantics.json` with `--semantics`.
Use `--replay tests/fixtures/stack_abilities_v1/history.json` to recompute the golden
session. `--history` is an explicit full-information export. API/CLI, exact replay,
read-only file behavior and prior-state ownership are exercised by functional tests.

## Real-rules evidence bridge — documentation only

Retained `602.2`, `602.2a`, `602.2b` evidence describes activation framing,
announcement/controller and the casting-stage cost analogy. See the
[activation design](GAMEPLAY_RULES_ACTIVATED_ABILITY_PROCEDURE_DESIGN.md),
[bounded projection](GAMEPLAY_RULES_BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTION.md)
and later [casting-stage family completion](GAMEPLAY_RULES_CASTING_STAGE_FAMILY_COMPLETION.md).
The later source inventory completes the numbered casting stages; historical
missing-stage statements in earlier design records retain their historical scope.
Retained `605.3b`/`405.6c` mana exceptions do not establish general stack-ability
execution. Source projection and analogy are not executable understanding.

Before real-Card execution, independently reviewed Card identity/ability semantics,
procedure/controller/priority/stack/source-state and effect closure, complete
applicable cost/legality/rollback behavior, source-use permissions and a separately
admitted real execution profile would be required. The fictional presence rule
cannot substitute for reviewed source-independence/last-known-information rules.
Real semantic closure remains OPEN and execution remains BLOCKED; no new CR unit,
projection, approval, permission or real-Card admission is introduced here.

Focused regressions cover costs, deferred effect, response opportunities, mixed
LIFO entries, source/controller separation, refusal, loss/checkpoint timing,
transaction rollback, exact native/session replay, coherent tampering, public CLI
and historical goldens. A finite exact source-delta adapter preserves old pins and
recognizes only explicitly pinned historical ancestors; unknown drift rejects.
Complete local and hosted writer/publication receipts belong in the draft PR.
Stop for independent PM review and owner-controlled merge. No future work is begun.
