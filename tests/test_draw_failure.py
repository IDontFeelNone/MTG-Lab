"""Actual native fictional draw-attempt/checkpoint execution, never real CR authority."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import (GameState, GameTransition, GameplayRulesSnapshot,
    CardGameplaySemantics, DRAW_FAILURE_PROFILE, rule_identity)
from gameplay_rules.session import GameplaySession, load_gameplay_session, replay_session, render_session_view
from gameplay_rules.session_cli import main
from gameplay_rules.snapshots import load_rules_snapshot, load_card_semantics, load_game_state
from test_turn_structure import action, changed, enter_b, pass_window

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/draw_failure_v1'


def contracts():
    return (load_rules_snapshot(FIX / 'rules-snapshot.json'),
            [load_card_semantics(p) for p in sorted(FIX.glob('*.semantics.json'))],
            load_game_state(FIX / 'initial-state.json'))


def session(state=None):
    rules, semantics, initial = contracts()
    return GameplaySession(rules, semantics, initial if state is None else state)


def draw_boundary():
    s = session(); enter_b(s)
    s.submit(s.action('pass_priority', 'B'))
    entry = s.submit(s.action('pass_priority', 'A'))
    return s, entry


class DrawFailureTests(unittest.TestCase):
    def test_actual_session_attempt_and_loss_with_no_card_creation(self):
        s, entry = draw_boundary()
        self.assertEqual([t['action']['kind'] for t in entry['transitions']],
                         ['pass_priority', 'perform_state_based_actions', 'advance_step_or_phase', 'draw_for_turn', 'perform_state_based_actions'])
        attempt, check = entry['transitions'][-2:]
        self.assertEqual(attempt['zone_changes'], [])
        self.assertEqual(attempt['after_state']['objects'], entry['transitions'][-3]['after_state']['objects'])
        self.assertEqual(attempt['after_state']['library_order'], entry['transitions'][-3]['after_state']['library_order'])
        self.assertEqual(attempt['after_state']['failed_draw_players'], ['B'])
        self.assertEqual(attempt['after_state']['status'], 'in_progress')
        self.assertEqual(attempt['required_system_actions'], ['perform_state_based_actions'])
        self.assertEqual(check['after_state']['failed_draw_players'], ['B'])
        self.assertEqual((s.state.status, s.state.loser_ids, s.state.winner_ids), ('ended', ('B',), ('A',)))
        self.assertEqual(s.state.pending_system_actions, ())
        for t in entry['transitions']:
            self.assertIsNone(t['after_state']['priority_player'])
        self.assertIn('draw_failure', {r['category'] for r in attempt['rule_references']})
        self.assertIn('draw_failure', {r['category'] for r in check['rule_references']})

    def test_last_card_succeeds_without_failure_or_loss(self):
        rules, sem, initial = contracts()
        b = initial.to_dict(); b.pop('state_id')
        sample = deepcopy(next(o for o in b['objects'] if o['owner'] == 'B'))
        sample.update(object_id='only-card', owner='B', controller='B', zone_id='B:library')
        b['objects'].insert(0, sample); b['library_order']['B:library'] = ['only-card']
        s = GameplaySession(rules, sem, GameState.create(b)); enter_b(s); e = pass_window(s)
        self.assertEqual(s.state.failed_draw_players, ())
        self.assertEqual((s.state.status, s.state.priority_player), ('in_progress', 'B'))
        self.assertEqual(s.state.library_order['B:library'], ())
        self.assertEqual(e['transitions'][-2]['zone_changes'], [{'object_id': 'only-card', 'from_zone': 'B:library', 'to_zone': 'B:hand'}])
        pass_window(s)
        self.assertEqual(s.state.step, 'action')
        self.assertEqual(s.state.failed_draw_players, ())

    def test_empty_library_alone_does_not_end_upkeep(self):
        s = session(); enter_b(s)
        self.assertEqual((s.state.status, s.state.step, s.state.priority_player), ('in_progress', 'upkeep', 'B'))
        self.assertEqual(s.state.failed_draw_players, ())
        self.assertEqual(s.submit(s.action('activate_ability', 'B', object_id='b-resource', ability_id='make-red'))['status'], 'LEGAL')

    def test_native_draw_is_legal_system_action_then_checkpoint(self):
        s, entry = draw_boundary(); rules, sem, _ = contracts(); engine = GameplayRulesEngine(rules, sem)
        t = entry['transitions'][-2]; before = GameState.from_dict(entry['transitions'][-3]['after_state'])
        request = action(before, 'draw_for_turn')
        self.assertEqual(engine.evaluate_action(before, request).status, 'LEGAL')
        self.assertEqual(engine.apply_action(before, request).to_dict(), t)
        after = GameState.from_dict(t['after_state'])
        self.assertNotEqual(engine.evaluate_action(after, action(after, 'pass_priority', 'B')).status, 'LEGAL')
        self.assertNotEqual(engine.evaluate_action(after, action(after, 'draw_for_turn')).status, 'LEGAL')
        self.assertEqual(engine.apply_action(after, action(after, 'perform_state_based_actions')).to_dict(), entry['transitions'][-1])

    def test_simultaneous_failed_draw_and_other_player_life_loss(self):
        _, entry = draw_boundary(); rules, sem, _ = contracts(); engine = GameplayRulesEngine(rules, sem)
        before = changed(GameState.from_dict(entry['transitions'][-2]['after_state']), lambda b: b['players'][0].update(life=0))
        t = engine.apply_action(before, action(before, 'perform_state_based_actions'))
        self.assertIsInstance(t, GameTransition)
        self.assertEqual(t.after_state['loser_ids'], ('A', 'B'))
        self.assertEqual(t.after_state['winner_ids'], ())

    def test_existing_life_loss_remains_independent_of_failed_draw(self):
        _, entry = draw_boundary(); rules, sem, _ = contracts(); engine = GameplayRulesEngine(rules, sem)
        def life(b): b.update(failed_draw_players=[]); b['players'][0]['life'] = 0
        before = changed(GameState.from_dict(entry['transitions'][-2]['after_state']), life)
        result = engine.apply_action(before, action(before, 'perform_state_based_actions'))
        self.assertEqual(result.after_state['loser_ids'], ('A',))

    def test_duplicate_checkpoint_and_post_terminal_actions_reject(self):
        s, _ = draw_boundary(); rules, sem, _ = contracts(); engine = GameplayRulesEngine(rules, sem)
        old = s.state.to_dict()
        for kind, actor in [('draw_for_turn', None), ('perform_state_based_actions', None), ('advance_step_or_phase', None), ('pass_priority', 'B')]:
            result = engine.apply_action(s.state, action(s.state, kind, actor))
            self.assertNotIsInstance(result, GameTransition)
            self.assertEqual(result.status, 'ILLEGAL')
            self.assertEqual(s.state.to_dict(), old)
        self.assertEqual(s.submit(s.action('pass_priority', 'B'))['status'], 'ILLEGAL')
        self.assertEqual(s.state.to_dict(), old)

    def test_manual_system_action_and_wrong_priority_preserve_state(self):
        s = session(); old = s.report()
        with self.assertRaises(GameplayContractError): s.submit(s.action('draw_for_turn', None))
        self.assertEqual(s.report(), old)
        self.assertEqual(s.submit(s.action('pass_priority', 'B'))['status'], 'ILLEGAL')
        self.assertEqual(s.state.to_dict(), old['initial_state'])

    def test_exact_replay_and_detached_prior_states(self):
        s = session(); initial = s.state; before = initial.to_dict(); enter_b(s); pass_window(s)
        history = s.report(); rules, sem, _ = contracts()
        replay = replay_session(rules, sem, history, expected_session_id=history['session_id'])
        self.assertEqual(replay.report(), history)
        self.assertEqual(initial.to_dict(), before)
        history['entries'][-1]['transitions'][-1]['after_state']['failed_draw_players'].clear()
        self.assertEqual(s.state.failed_draw_players, ('B',))

    def test_blocked_checkpoint_rolls_back_whole_submission(self):
        s = session(); enter_b(s); s.submit(s.action('pass_priority', 'B')); old = s.report()
        original = GameplayRulesEngine.apply_action
        def blocked(engine, state, request):
            if request.kind == 'perform_state_based_actions' and state.to_dict().get('failed_draw_players'):
                raise GameplayContractError('test_checkpoint_blocked', 'injected failure')
            return original(engine, state, request)
        with patch.object(GameplayRulesEngine, 'apply_action', blocked):
            with self.assertRaisesRegex(GameplayContractError, 'test_checkpoint_blocked'): s.submit(s.action('pass_priority', 'A'))
        self.assertEqual(s.report(), old)
        self.assertEqual(s.submit(s.action('pass_priority', 'A'))['status'], 'LEGAL')

    def test_forged_failure_progress_and_types_reject(self):
        s, entry = draw_boundary()
        pending = GameState.from_dict(entry['transitions'][-2]['after_state'])
        edits = [lambda b: b.update(failed_draw_players=None), lambda b: b.update(failed_draw_players=['B','B']),
                 lambda b: b.update(failed_draw_players=['A']), lambda b: b.update(failed_draw_players=[True]),
                 lambda b: b.update(priority_player='B', pending_system_actions=[]),
                 lambda b: b.update(pending_system_actions=['draw_for_turn','perform_state_based_actions']),
                 lambda b: b['turn_start'].update(status='pending_draw'), lambda b: b.update(step='upkeep')]
        for edit in edits:
            with self.subTest(edit=edit), self.assertRaises(GameplayContractError): changed(pending, edit)
        with self.assertRaises(GameplayContractError): changed(s.state, lambda b: b.update(loser_ids=[]))
        with self.assertRaises(GameplayContractError): changed(contracts()[2], lambda b: b.update(failed_draw_players=['B']))

    def test_unknown_life_checkpoint_remains_indeterminate(self):
        _, entry = draw_boundary(); rules, sem, _ = contracts(); engine = GameplayRulesEngine(rules, sem)
        state = changed(GameState.from_dict(entry['transitions'][-2]['after_state']), lambda b: b['players'][0].update(life=None))
        self.assertEqual(engine.evaluate_action(state, action(state, 'perform_state_based_actions')).status, 'INDETERMINATE')

    def test_unknown_draw_failure_evidence_refuses_and_rolls_back(self):
        rules, sem, initial = contracts(); b = rules.to_dict(); b.pop('rules_snapshot_id')
        for r in b['rules']:
            if r['category'] == 'draw_failure': r['status'] = 'unknown'; r['rule_hash'] = rule_identity(r)
        altered = GameplayRulesSnapshot.create(b)
        rebound = []
        mapping = {}
        for s in sem:
            d = s.to_dict(); old = d.pop('semantics_id'); d['rules_snapshot_id'] = altered.identity
            new = CardGameplaySemantics.create(d); rebound.append(new); mapping[old] = new.identity
        state = initial.to_dict(); state.pop('state_id'); state['rules_snapshot_id'] = altered.identity
        for obj in state['objects']: obj['semantics_id'] = mapping[obj['semantics_id']]
        s = GameplaySession(altered, rebound, GameState.create(state))
        self.assertEqual(s.submit(s.action('pass_priority', 'A'))['status'], 'INDETERMINATE')
        self.assertEqual(s.state.identity, GameState.create(state).identity)

    def test_new_profile_requires_explicit_policy_evidence_and_state(self):
        rules, sem, initial = contracts()
        for change in [lambda b: b['parameters']['turn_start'].update(empty_library='unsupported'),
                       lambda b: b.update(rules=[r for r in b['rules'] if r['category']!='draw_failure'])]:
            body = rules.to_dict(); body.pop('rules_snapshot_id'); change(body)
            with self.assertRaises(GameplayContractError): GameplayRulesSnapshot.create(body)
        body = initial.to_dict(); body.pop('state_id'); body.pop('failed_draw_players'); body['schema_version'] = 'gameplay-state-v3'
        with self.assertRaisesRegex(GameplayContractError, 'incompatible_state_profile'): GameplaySession(rules, sem, GameState.create(body))

    def test_unsupported_mechanics_remain_closed(self):
        s = session()
        for kind in ['draw_card', 'trigger_ability', 'attack', 'replace_draw']:
            self.assertEqual(s.submit(s.action(kind, 'A'))['status'], 'UNSUPPORTED')
        self.assertEqual(s.state.identity, contracts()[2].identity)

    def test_actual_public_loader_and_source_digest(self):
        s = load_gameplay_session(rules_path=FIX/'rules-snapshot.json', semantics_paths=sorted(FIX.glob('*.semantics.json')), state_path=FIX/'initial-state.json')
        enter_b(s); pass_window(s)
        self.assertEqual(s.state.status, 'ended')
        rules, _, _ = contracts()
        source = next(s for s in rules.sources if s['source_id']=='fictional-draw-failure-v1')
        self.assertEqual(source['content_hash'], 'sha256:'+hashlib.sha256((FIX/'fictional-rules.txt').read_bytes()).hexdigest())

    def test_golden_history_view_and_native_replay(self):
        s, _ = draw_boundary()
        history = json.loads((FIX / 'history.json').read_text())
        self.assertEqual(s.report(), history)
        self.assertEqual(s.view(), json.loads((FIX / 'final-view.json').read_text()))
        self.assertEqual(render_session_view(s.view()), (FIX / 'final-view.txt').read_text())
        self.assertEqual(sum(len(e['transitions']) for e in history['entries']), 11)
        rules, sem, _ = contracts()
        self.assertEqual(replay_session(rules, sem, history).report(), history)

    def test_coherently_rehashed_native_draw_cannot_hide_failed_attempt(self):
        _, entry = draw_boundary(); rules, sem, _ = contracts()
        engine = GameplayRulesEngine(rules, sem)
        original = entry['transitions'][-2]
        before = GameState.from_dict(entry['transitions'][-3]['after_state'])
        body = deepcopy(original); body.pop('transition_id')
        after = body['after_state']; after.pop('state_id'); after['failed_draw_players'] = []
        after = GameState.create(after); body['after_state'] = after.to_dict(); body['after_state_id'] = after.identity
        altered = GameTransition.create(body)
        with self.assertRaisesRegex(GameplayContractError, 'replay_mismatch'):
            engine.replay_transition(before, altered)

    def test_public_cli_sequence_and_replay_are_read_only(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()}
        args = ['--rules', str(FIX/'rules-snapshot.json'), '--state', str(FIX/'initial-state.json')]
        for p in sorted(FIX.glob('*.semantics.json')): args += ['--semantics', str(p)]
        for mode in ['text', 'json']:
            output = io.StringIO()
            with patch('sys.stdin', io.StringIO((FIX/'actions.jsonl').read_text())), redirect_stdout(output):
                self.assertEqual(main(args + ['--format', mode]), 0)
            self.assertIn(draw_boundary()[0].state.identity, output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ['--replay', str(FIX/'history.json')]), 0)
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()})

    def test_exact_source_successors_and_unknown_drift_rejection(self):
        import draw_failure_preservation as guard
        from pack_simulation_preservation import preceding_bytes
        for name, pin in guard.ledger()['replacements'].items():
            raw = (ROOT/name).read_bytes()
            old = guard.preceding_bytes(name, raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(), pin['old_sha256'])
            self.assertEqual(guard.preceding_bytes(name, old), old)
            self.assertIsInstance(preceding_bytes(name, raw), bytes)
            with self.assertRaises(AssertionError): guard.preceding_bytes(name, raw+b'\n# unreviewed drift\n')


if __name__ == '__main__': unittest.main()
