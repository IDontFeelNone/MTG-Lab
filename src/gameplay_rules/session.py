"""Multi-action sessions over the existing fictional kernel; no new game rules."""
from __future__ import annotations

import json

from .engine import GameplayRulesEngine
from .errors import GameplayContractError
from .models import (CardGameplaySemantics, GameAction, GameState, GameTransition,
                     GameplayRulesSnapshot, content_identity, STATE_SCHEMAS_BY_PROFILE)
from .snapshots import (MAX_CONTRACT_BYTES, load_card_semantics, load_game_state,
                        load_rules_snapshot)

VERSION = 'gameplay-session-v0'
MAX_ATTEMPTS = 128
MAX_SYSTEM_TRANSITIONS = 8
_SYSTEM_ACTIONS = frozenset(('perform_state_based_actions', 'resolve_top_of_stack', 'advance_step_or_phase', 'untap_active_player', 'draw_for_turn'))


def _require(condition, code, message):
    if not condition:
        raise GameplayContractError(code, message)


def _encoded(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError):
        raise GameplayContractError('invalid_session', 'Finite JSON session data is required') from None


def decode_session_json(raw):
    """Strict bounded transport for native actions and replay reports, not prose."""
    _require(type(raw) in (str, bytes), 'invalid_json', 'JSON text or bytes required')
    try:
        size = len(raw.encode('utf-8') if type(raw) is str else raw)
    except UnicodeError:
        raise GameplayContractError('invalid_json', 'Malformed session encoding') from None
    _require(size <= MAX_CONTRACT_BYTES, 'session_bound', 'Session input exceeds the existing contract byte bound')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, 'invalid_json', 'Duplicate session JSON key')
            result[key] = value
        return result

    def nonfinite(_value):
        raise GameplayContractError('invalid_json', 'Non-finite session JSON number')

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, UnicodeError, TypeError, RecursionError) as error:
        if isinstance(error, GameplayContractError):
            raise
        raise GameplayContractError('invalid_json', 'Malformed session JSON') from None


class GameplaySession:
    """Privately owned current state, atomic submissions and exact kernel history.

    Player attempts are explicit. Only mandatory system actions scheduled by a
    legal kernel transition are drained automatically. No player choice is made.
    """

    def __init__(self, snapshot, semantics, initial_state):
        _require(isinstance(snapshot, GameplayRulesSnapshot) and isinstance(initial_state, GameState),
                 'invalid_session', 'Verified rules and initial state contracts required')
        _require(type(semantics) in (list, tuple) and len(semantics) <= 64,
                 'session_bound', 'At most 64 explicit semantics contracts required')
        _require(all(isinstance(s, CardGameplaySemantics) for s in semantics),
                 'invalid_semantics', 'Verified structured semantics required')
        self._rules = GameplayRulesSnapshot.from_dict(snapshot.to_dict())
        self._semantics = tuple(CardGameplaySemantics.from_dict(s.to_dict()) for s in semantics)
        self._initial = GameState.from_dict(initial_state.to_dict())
        _require(len(_encoded(dict(rules=self._rules.to_dict(), semantics=[s.to_dict() for s in self._semantics],
                                   state=self._initial.to_dict()))) <= MAX_CONTRACT_BYTES,
                 'session_bound', 'Combined session inputs exceed the existing contract byte bound')
        self._engine = GameplayRulesEngine(self._rules, self._semantics)
        before, rules = self._initial.to_dict(), self._rules.to_dict()
        _require(before['game_id'] == rules['game_id'] and before['rules_snapshot_id'] == self._rules.identity,
                 'session_binding', 'Initial state must bind the exact fictional game and rules')
        _require({'phase': before['phase'], 'step': before['step']} in rules['parameters']['turn_steps'],
                 'unsupported_turn_window', 'Initial turn window is not defined by the selected rules')
        _require(not before['pending_system_actions'] and
                 (before['status'] == 'ended' or before['priority_player'] is not None),
                 'initial_system_boundary', 'Initialize at a settled player decision boundary')
        _require(before['schema_version'] == STATE_SCHEMAS_BY_PROFILE[rules['execution_profile']],
                 'incompatible_state_profile', 'State schema must match the exact selected fictional profile')
        definitions = {s.identity: s.to_dict() for s in self._semantics}
        for obj in before['objects']:
            if obj['knowledge'] == 'known':
                definition = definitions.get(obj['semantics_id'])
                _require(definition is not None and definition['card_id'] == obj['card_id'],
                         'session_semantics_binding', 'Known objects require their exact supplied semantics')
        self._current = self._initial
        self._entries = []
        self.report()  # Validate the initial retained-input bound before use.

    @property
    def state(self):
        """Independent native state; prior or returned states cannot retarget a session."""
        return GameState.from_dict(self._current.to_dict())

    def action(self, kind, actor, *, object_id=None, ability_id=None, payment=None):
        """Bind an explicitly selected action to the current state. No ability inference."""
        return GameAction.create(dict(game_id=self._current.game_id,
            rules_snapshot_id=self._rules.identity, expected_state_id=self._current.identity,
            kind=kind, actor=actor, object_id=object_id, ability_id=ability_id, payment=payment))

    def submit(self, action):
        """Check/apply one native player action; rejection preserves the state.

        Contract failures and blocked system boundaries leave state AND history
        unchanged. Legal/illegal/unknown/unsupported evaluated attempts are recorded.
        """
        _require(isinstance(action, GameAction), 'invalid_request', 'A verified native GameAction is required')
        action = GameAction.from_dict(action.to_dict())
        _require(action.kind not in _SYSTEM_ACTIONS, 'player_action_required',
                 'Only the kernel may schedule session system actions')
        _require(len(self._entries) < MAX_ATTEMPTS, 'session_bound', 'Session attempt bound reached')
        before = self._current
        legality = self._engine.evaluate_action(before, action)
        next_state = before
        transitions = []
        if legality.status == 'LEGAL':
            transition = self._engine.apply_action(before, action)
            _require(isinstance(transition, GameTransition), 'kernel_transition', 'Expected a legal kernel transition')
            transitions.append(transition.to_dict())
            next_state = GameState.from_dict(transition.after_state)
            for _ in range(MAX_SYSTEM_TRANSITIONS):
                if not next_state.pending_system_actions:
                    break
                kind = next_state.pending_system_actions[0]
                _require(kind in _SYSTEM_ACTIONS, 'unsupported_system_action', 'Kernel scheduled an unsupported boundary')
                system = GameAction.create(dict(game_id=next_state.game_id,
                    rules_snapshot_id=self._rules.identity, expected_state_id=next_state.identity,
                    kind=kind, actor=None, object_id=None, ability_id=None, payment=None))
                resolved = self._engine.apply_action(next_state, system)
                _require(isinstance(resolved, GameTransition), 'blocked_system_action',
                         'A mandatory system action did not produce a legal kernel transition: ' +
                         (', '.join(resolved.to_dict()['explanation']['reason_codes']) if not isinstance(resolved, GameTransition) else ''))
                transitions.append(resolved.to_dict())
                next_state = GameState.from_dict(resolved.after_state)
            _require(not next_state.pending_system_actions, 'session_bound', 'Mandatory system-action bound exceeded')
        entry = dict(sequence=len(self._entries), request=action.to_dict(),
                     status=legality.status, legality=legality.to_dict(),
                     before_state_id=before.identity, after_state_id=next_state.identity,
                     transitions=transitions)
        entries = [*self._entries, entry]
        self._report(entries, next_state)  # Bound checks precede the atomic commit.
        self._entries = entries
        self._current = next_state
        return json.loads(_encoded(entry))

    def _report(self, entries, current):
        body = dict(schema_version=VERSION, game_id=self._initial.game_id,
                    execution_profile=self._rules.execution_profile,
                    scope='PROJECT_AUTHORED_FICTIONAL_ONLY_FULL_INFORMATION_REPLAY',
                    rules_snapshot_id=self._rules.identity,
                    semantics_ids=sorted(s.identity for s in self._semantics),
                    initial_state=self._initial.to_dict(), entries=entries,
                    current_state_id=current.identity)
        _require(len(_encoded(body)) <= MAX_CONTRACT_BYTES - 100,
                 'session_bound', 'Session history exceeds the existing contract byte bound')
        return dict(body, session_id=content_identity(VERSION, body))

    def report(self):
        """Independent full-information replay report; not the public player display."""
        return json.loads(_encoded(self._report(self._entries, self._current)))

    def view(self):
        """Show public zones and hidden-zone counts, never hidden object identities."""
        state = self._current.to_dict()
        zones = []
        for zone in state['zones']:
            objects = [o for o in state['objects'] if o['zone_id'] == zone['zone_id']]
            zones.append(dict(zone, count=len(objects), **({'objects': objects} if zone['visibility'] == 'public' else {})))
        return dict(schema_version=VERSION, scope='PROJECT_AUTHORED_FICTIONAL_ONLY_PUBLIC_VIEW',
                    state_id=state['state_id'], rules_snapshot_id=state['rules_snapshot_id'],
                    turn_number=state['turn_number'], active_player=state['active_player'],
                    phase=state['phase'], step=state['step'], priority_player=state['priority_player'],
                    status=state['status'], players=state['players'], zones=zones,
                    stack_count=len(state['stack']), winner_ids=state['winner_ids'], loser_ids=state['loser_ids'])


def load_gameplay_session(*, rules_path, semantics_paths, state_path):
    """Load explicit original fictional contracts through their owning strict readers."""
    _require(type(semantics_paths) in (list, tuple) and len(semantics_paths) <= 64,
             'session_bound', 'At most 64 explicit semantics paths required')
    return GameplaySession(load_rules_snapshot(rules_path),
                           [load_card_semantics(p) for p in semantics_paths], load_game_state(state_path))


def replay_session(snapshot, semantics, report, *, expected_session_id=None):
    """Recompute every verdict and transition; a supplied checksum alone is insufficient."""
    _require(type(report) is dict, 'invalid_session', 'A complete session report is required')
    _require(len(_encoded(report)) <= MAX_CONTRACT_BYTES, 'session_bound', 'Session report too large')
    # Strict decoded ownership also rejects non-string keys and nonfinite values.
    report = decode_session_json(_encoded(report))
    keys = {'schema_version', 'game_id', 'execution_profile', 'scope', 'rules_snapshot_id',
            'semantics_ids', 'initial_state', 'entries', 'current_state_id', 'session_id'}
    _require(set(report) == keys and report['schema_version'] == VERSION,
             'invalid_session', 'Exact session report schema/version required')
    _require(expected_session_id is None or report['session_id'] == expected_session_id,
             'session_identity_mismatch', 'Expected session identity mismatch')
    _require(type(report['entries']) is list and len(report['entries']) <= MAX_ATTEMPTS,
             'session_bound', 'Bounded ordered session attempts required')
    session = GameplaySession(snapshot, semantics, GameState.from_dict(report['initial_state']))
    for recorded in report['entries']:
        _require(type(recorded) is dict and 'request' in recorded,
                 'invalid_session', 'Complete native action history required')
        before = session.state
        observed = session.submit(GameAction.from_dict(recorded['request']))
        _require(_encoded(observed) == _encoded(recorded), 'session_replay_mismatch', 'Action verdict/transitions do not reproduce')
        # Invoke the kernel's independent transition replay as well as session replay.
        for raw in observed['transitions']:
            transition = GameTransition.from_dict(raw)
            session._engine.replay_transition(before, transition)
            before = GameState.from_dict(transition.after_state)
    _require(_encoded(session.report()) == _encoded(report), 'session_replay_mismatch', 'Complete session does not reproduce')
    return session


def render_session_view(view):
    lines = [f"Fictional turn {view['turn_number']}: active {view['active_player']}; "
             f"{view['phase']}/{view['step']}; priority {view['priority_player']}; {view['status']}"]
    for player in view['players']:
        lines.append(f"{player['player_id']}: life {player['life']}; mana " + json.dumps(player['mana_pool'], sort_keys=True))
    for zone in view['zones']:
        contents = ', '.join(o['object_id'] for o in zone.get('objects', [])) if zone['visibility'] == 'public' else 'hidden'
        lines.append(f"{zone['zone_id']} ({zone['count']}): {contents}".rstrip())
    lines += ['State: ' + view['state_id'], 'Project-authored fictional rules only; not real Magic gameplay.']
    return '\n'.join(lines) + '\n'
