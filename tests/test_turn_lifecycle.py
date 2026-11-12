"""Executable, project-authored turn-start mutations; no real Magic observations."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import CardGameplaySemantics, GameAction, GameState, GameTransition, GameplayRulesSnapshot, content_identity, rule_identity
from gameplay_rules.session import GameplaySession, load_gameplay_session, replay_session
from gameplay_rules.session_cli import main
from gameplay_rules.snapshots import load_rules_snapshot, load_card_semantics, load_game_state

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/turn_lifecycle_v1'
OLD = ROOT / 'tests/fixtures/gameplay_rules'


def contracts():
    return (load_rules_snapshot(FIX/'rules-snapshot.json'),
            [load_card_semantics(p) for p in sorted(FIX.glob('*.semantics.json'))],
            load_game_state(FIX/'initial-state.json'))


def changed(state, edit):
    b = state.to_dict(); b.pop('state_id'); edit(b)
    return GameState.create(b)


def loaded(state=None, semantics=None):
    rules, definitions, initial = contracts()
    return GameplaySession(rules, definitions if semantics is None else semantics, initial if state is None else state)


def enter_b(session):
    session.submit(session.action('pass_priority', 'A'))
    return session.submit(session.action('pass_priority', 'B'))


def objects(state):
    return {o['object_id']: o for o in state.to_dict()['objects']}


class TurnLifecycleTests(unittest.TestCase):
    def demo(self):
        s = loaded()
        for line in (FIX/'actions.jsonl').read_text().splitlines():
            self.assertEqual(s.submit(GameAction.from_dict(json.loads(line)))['status'], 'LEGAL')
        return s

    def test_complete_actual_two_turn_mutations_and_exact_history(self):
        s = self.demo(); r = s.report()
        self.assertEqual(r, json.loads((FIX/'history.json').read_text()))
        self.assertEqual(s.view(), json.loads((FIX/'final-view.json').read_text()))
        self.assertEqual((s.state.turn_number,s.state.active_player,s.state.priority_player), (3,'A','A'))
        self.assertEqual(sum(len(e['transitions']) for e in r['entries']),24)
        self.assertEqual(r['execution_profile'],'fictional-two-player-turn-lifecycle-v1')
        self.assertEqual(s.state.schema_version,'gameplay-state-v2')

    def test_active_controlled_untap_and_inactive_unchanged(self):
        s=loaded(); initial=s.state; enter_b(s); result=objects(s.state)
        self.assertTrue(result['a-resource']['tapped'])
        self.assertFalse(result['b-resource']['tapped'])
        self.assertTrue(objects(initial)['b-resource']['tapped'])
        self.assertEqual(s.state.turn_start['status'],'complete')

    def test_control_not_owner_or_zone_owner_determines_untap(self):
        rules,sem,state=contracts()
        state=changed(state,lambda b:b['objects'][0].update(controller='B'))
        s=loaded(state);enter_b(s)
        self.assertFalse(objects(s.state)['a-resource']['tapped'])
        self.assertEqual(objects(s.state)['a-resource']['owner'],'A')
        self.assertEqual(objects(s.state)['a-resource']['zone_id'],'A:battlefield')

    def test_ordered_top_not_object_array_or_lexical_order(self):
        rules,sem,state=contracts()
        self.assertLess([o['object_id'] for o in state.objects].index('b-next'),[o['object_id'] for o in state.objects].index('b-top'))
        s=loaded();enter_b(s);obs=objects(s.state)
        self.assertEqual(obs['b-top']['zone_id'],'B:hand');self.assertEqual(obs['b-next']['zone_id'],'B:library')
        self.assertEqual(list(s.state.library_order['B:library']),['b-next'])
        reversed_state=changed(state,lambda b:b['library_order']['B:library'].reverse())
        s=loaded(reversed_state);enter_b(s)
        self.assertEqual(objects(s.state)['b-next']['zone_id'],'B:hand')
        self.assertEqual(objects(s.state)['b-top']['zone_id'],'B:library')

    def test_draw_owner_preserved_controller_reset_and_exact_zone_record(self):
        state=changed(contracts()[2],lambda b:next(o for o in b['objects'] if o['object_id']=='b-top').update(controller='A'))
        s=loaded(state);e=enter_b(s);obs=objects(s.state)['b-top']
        self.assertEqual((obs['owner'],obs['controller'],obs['zone_id']),('B','B','B:hand'))
        draw=next(t for t in e['transitions'] if t['action']['kind']=='draw_for_turn')
        self.assertEqual(draw['zone_changes'],[{'object_id':'b-top','from_zone':'B:library','to_zone':'B:hand'}])
        self.assertEqual({c['path'] for c in draw['state_changes']}, {'revision','objects','library_order','pending_system_actions','turn_start'})

    def test_priority_only_after_exact_automatic_sequence(self):
        s=loaded();e=enter_b(s)
        kinds=[t['action']['kind'] for t in e['transitions']]
        self.assertEqual(kinds,['pass_priority','perform_state_based_actions','advance_step_or_phase','untap_active_player','draw_for_turn','perform_state_based_actions'])
        for t in e['transitions'][:-1]:self.assertIsNone(t['after_state']['priority_player'])
        self.assertEqual(e['transitions'][-1]['after_state']['priority_player'],'B')
        untap=e['transitions'][3];self.assertEqual(untap['after_state']['turn_start']['status'],'pending_draw')
        self.assertEqual(untap['zone_changes'],[])
        self.assertIn('untap',{r['category'] for r in untap['rule_references']})
        self.assertIn('draw',{r['category'] for r in e['transitions'][4]['rule_references']})

    def test_updated_state_supports_real_activation_and_drawn_land_play(self):
        s=self.demo();r=s.report()
        self.assertEqual(r['entries'][2]['request']['object_id'],'b-resource')
        self.assertEqual(r['entries'][2]['transitions'][0]['after_state']['players'][1]['mana_pool'],{'red':2})
        self.assertEqual(objects(s.state)['b-top']['zone_id'],'B:battlefield')
        self.assertTrue(objects(s.state)['b-resource']['tapped'])

    def test_no_skipped_or_duplicate_draw_across_two_complete_turns(self):
        s=self.demo();draws=[t for e in s.report()['entries'] for t in e['transitions'] if t['action']['kind']=='draw_for_turn']
        self.assertEqual([t['zone_changes'][0]['object_id'] for t in draws],['b-top','a-next'])
        self.assertEqual(list(s.state.library_order['B:library']),['b-next'])
        self.assertFalse(objects(s.state)['a-resource']['tapped'])
        before=s.state.to_dict()
        for kind in ['untap_active_player','draw_for_turn']:
            with self.assertRaisesRegex(GameplayContractError,'player_action_required'):s.submit(s.action(kind,None))
        self.assertEqual(s.state.to_dict(),before)
        engine=GameplayRulesEngine(*contracts()[:2])
        action=GameAction.create(dict(game_id=s.state.game_id,rules_snapshot_id=s.state.rules_snapshot_id,expected_state_id=s.state.identity,kind='draw_for_turn',actor=None,object_id=None,ability_id=None,payment=None))
        self.assertEqual(engine.evaluate_action(s.state,action).status,'ILLEGAL')

    def test_empty_library_fail_closed_atomic_and_precise_kernel_reason(self):
        state=changed(contracts()[2],lambda b:(b['objects'].__setitem__(slice(None),[o for o in b['objects'] if o['zone_id']!='B:library']),b['library_order'].__setitem__('B:library',[])))
        s=loaded(state);s.submit(s.action('pass_priority','A'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'empty_library_draw_rule_not_implemented'):s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.report(),before)
        def boundary(b):
            b.update(active_player='B',phase='beginning',step='start',priority_player=None,consecutive_passes=[],pending_system_actions=['draw_for_turn','perform_state_based_actions'],turn_start={'turn_number':1,'player_id':'B','status':'pending_draw'})
        boundary_state=changed(state,boundary);engine=GameplayRulesEngine(*contracts()[:2])
        a=GameAction.create(dict(game_id=state.game_id,rules_snapshot_id=state.rules_snapshot_id,expected_state_id=boundary_state.identity,kind='draw_for_turn',actor=None,object_id=None,ability_id=None,payment=None))
        verdict=engine.apply_action(boundary_state,a)
        self.assertEqual(verdict.status,'UNSUPPORTED');self.assertIn('empty_library_draw_rule_not_implemented',verdict.to_dict()['unsupported_dimensions'])
        self.assertEqual(boundary_state.status,'in_progress')

    def test_malformed_ordering_rejects_missing_duplicate_foreign_and_wrong_types(self):
        state=contracts()[2]
        edits=[lambda b:b.pop('library_order'),lambda b:b.update(library_order=None),lambda b:b['library_order'].pop('A:library'),
               lambda b:b['library_order'].update(foreign=[]),lambda b:b['library_order'].update({'B:library':None}),
               lambda b:b['library_order'].update({'B:library':['b-top','b-top']}),lambda b:b['library_order'].update({'B:library':['b-top']}),
               lambda b:b['library_order'].update({'B:library':['b-top',2]}),lambda b:b['library_order'].update({'B:library':['b-top','a-next']}),
               lambda b:next(o for o in b['objects'] if o['object_id']=='b-top').update(owner='A'),
               lambda b:next(z for z in b['zones'] if z['zone_id']=='B:library').update(owner=None)]
        for edit in edits:
            with self.subTest(edit=edit),self.assertRaises(GameplayContractError):changed(state,edit)

    def test_progress_marker_rejects_replay_skips_and_rescheduling(self):
        state=contracts()[2]
        edits=[lambda b:b['turn_start'].update(turn_number=True),lambda b:b['turn_start'].update(turn_number=2),lambda b:b['turn_start'].update(player_id='B'),
               lambda b:b['turn_start'].update(status='pending_draw'),lambda b:b['turn_start'].update(status='approved'),
               lambda b:b.update(priority_player=None,pending_system_actions=['draw_for_turn']),lambda b:b['turn_start'].update(extra=False)]
        for edit in edits:
            with self.subTest(edit=edit),self.assertRaises(GameplayContractError):changed(state,edit)

    def test_missing_or_unknown_tap_state_cannot_be_silently_resolved(self):
        state=changed(contracts()[2],lambda b:next(o for o in b['objects'] if o['object_id']=='b-resource').update(tapped=None))
        s=loaded(state);s.submit(s.action('pass_priority','A'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'untap_state_unknown'):s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.report(),before)

    def test_unimplemented_untap_restriction_and_external_effect_block(self):
        rules,sem,state=contracts();old=next(x for x in sem if x.card_id=='pebble-resource');b=old.to_dict();b.pop('semantics_id');b['restrictions']=['does_not_untap'];restricted=CardGameplaySemantics.create(b)
        state=changed(state,lambda b:[o.update(semantics_id=restricted.identity) for o in b['objects'] if o['card_id']=='pebble-resource'])
        s=loaded(state,[restricted if x.identity==old.identity else x for x in sem]);before=s.state.to_dict()
        e=s.submit(s.action('pass_priority','A'));self.assertEqual(e['status'],'UNSUPPORTED');self.assertEqual(s.state.to_dict(),before)
        effect_state=changed(contracts()[2],lambda b:b['active_effects'].append({'effect_id':'unknown-untap','capability':'untap','affected_actions':['untap_active_player'],'knowledge':'unsupported'}))
        s=loaded(effect_state);s.submit(s.action('pass_priority','A'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'active_effect:unknown-untap'):s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.report(),before)

    def test_profile_state_pairing_fails_closed_in_kernel_and_session(self):
        rules,sem,state=contracts();old_rules=load_rules_snapshot(OLD/'rules-snapshot.json');old_sem=[load_card_semantics(p) for p in OLD.glob('*.semantics.json')]
        mismatched=changed(state,lambda b:b.update(rules_snapshot_id=old_rules.identity))
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):GameplaySession(old_rules,old_sem,mismatched)
        engine=GameplayRulesEngine(old_rules,old_sem)
        a=GameAction.create(dict(game_id=mismatched.game_id,rules_snapshot_id=old_rules.identity,expected_state_id=mismatched.identity,kind='pass_priority',actor='A',object_id=None,ability_id=None,payment=None))
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):engine.evaluate_action(mismatched,a)
        old_state=load_game_state(OLD/'game-state.json');b=old_state.to_dict();b.pop('state_id');b['rules_snapshot_id']=rules.identity
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):GameplaySession(rules,sem,GameState.create(b))

    def test_lifecycle_requires_exact_structured_snapshot_and_cited_rules(self):
        rules=contracts()[0]
        def update(edit):
            b=rules.to_dict();b.pop('rules_snapshot_id');edit(b);return GameplayRulesSnapshot.create(b)
        for edit in [lambda b:b['parameters'].pop('turn_start'),lambda b:b['parameters']['turn_start'].update(draw_count=True),lambda b:b['parameters']['turn_start'].update(empty_library='lose'),
                     lambda b:b['rules'].__setitem__(slice(None),[r for r in b['rules'] if r['category']!='draw']),lambda b:b.update(execution_profile='real-magic'),
                     lambda b:b['parameters']['turn_steps'].append({'phase':'combat','step':'attack'})]:
            with self.subTest(edit=edit),self.assertRaises(GameplayContractError):update(edit)
        b=rules.to_dict();b.pop('rules_snapshot_id')
        for r in b['rules']:
            if r['category']=='draw':r['status']='unknown';r['rule_hash']=rule_identity(r)
        unknown=GameplayRulesSnapshot.create(b);sem=[]
        for x in contracts()[1]:
            v=x.to_dict();v.pop('semantics_id');v['rules_snapshot_id']=unknown.identity;sem.append(CardGameplaySemantics.create(v))
        ids={x.card_id:x.identity for x in sem}
        state=changed(contracts()[2],lambda b:(b.update(rules_snapshot_id=unknown.identity),[o.update(semantics_id=ids[o['card_id']]) for o in b['objects']]))
        s=GameplaySession(unknown,sem,state);s.submit(s.action('pass_priority','A'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'rule_coverage'):s.submit(s.action('pass_priority','B'))
        self.assertEqual(before,s.report())

    def test_unknown_drawn_identity_remains_unknown_not_inferred(self):
        state=changed(contracts()[2],lambda b:next(o for o in b['objects'] if o['object_id']=='b-top').update(knowledge='unknown',card_id=None,semantics_id=None))
        s=loaded(state);enter_b(s);obs=objects(s.state)['b-top']
        self.assertIsNone(obs['card_id']);self.assertIsNone(obs['semantics_id']);self.assertEqual(obs['zone_id'],'B:hand')
        self.assertEqual(s.submit(s.action('play_land','B',object_id='b-top'))['status'],'INDETERMINATE')

    def test_exact_session_and_native_transition_replay_reject_rehash(self):
        rules,sem,initial=contracts();s=self.demo();r=s.report()
        self.assertEqual(replay_session(rules,sem,r,expected_session_id=r['session_id']).report(),r)
        engine=GameplayRulesEngine(rules,sem);state=initial
        for e in r['entries']:
            for t in e['transitions']:
                transition=GameTransition.from_dict(t);self.assertEqual(engine.replay_transition(state,transition).identity,transition.identity);state=GameState.from_dict(t['after_state'])
        bad=deepcopy(r);bad['entries'][1]['transitions'][4]['zone_changes'][0]['object_id']='b-next'
        bad['session_id']=content_identity('gameplay-session-v0',{k:v for k,v in bad.items() if k!='session_id'})
        with self.assertRaises(GameplayContractError):replay_session(rules,sem,bad)

    def test_inputs_prior_states_outputs_and_library_order_owned_independently(self):
        rules,sem,initial=contracts();before=initial.to_dict();s=GameplaySession(rules,sem,initial);prior=s.state;enter_b(s)
        self.assertEqual(initial.to_dict(),before);self.assertEqual(prior.to_dict(),before)
        report=s.report();report['initial_state']['library_order']['B:library'].clear();view=s.view();view['players'][1]['life']=999
        self.assertEqual(list(s.state.library_order['B:library']),['b-next']);self.assertEqual(s.view()['players'][1]['life'],10)
        hidden=[z for z in s.view()['zones'] if z['kind']=='library']
        self.assertTrue(all('objects' not in z for z in hidden));self.assertNotIn('library_order',s.view())

    def test_v0_golden_history_and_state_identities_unchanged(self):
        fixture=ROOT/'tests/fixtures/gameplay_session_v0';r=json.loads((fixture/'history.json').read_text())
        rules=load_rules_snapshot(OLD/'rules-snapshot.json');sem=[load_card_semantics(p) for p in OLD.glob('*.semantics.json')]
        s=replay_session(rules,sem,r,expected_session_id='sha256:4bc642bec3c5a95f3925b1c7ce4711dbeb1bc5140409b8cebb139fdb707be308')
        self.assertEqual(s.state.identity,'sha256:3d50568ea0ec2f7a1bfa471e9c6fca3aff3f8040096dff31d849a634809804e0')
        self.assertEqual(s.state.schema_version,'gameplay-state-v1');self.assertNotIn('library_order',s.state.to_dict())

    def test_public_load_cli_both_formats_and_replay(self):
        args=['--rules',str(FIX/'rules-snapshot.json'),'--state',str(FIX/'initial-state.json')]
        for p in sorted(FIX.glob('*.semantics.json')):args+=['--semantics',str(p)]
        expected=self.demo().state.identity
        for mode in ['json','text']:
            stream=io.StringIO()
            with patch('sys.stdin',io.StringIO((FIX/'actions.jsonl').read_text())),redirect_stdout(stream):self.assertEqual(main(args+['--format',mode]),0)
            self.assertIn(expected,stream.getvalue())
            with redirect_stdout(io.StringIO()):self.assertEqual(main(args+['--replay',str(FIX/'history.json')]),0)
        self.assertEqual(load_gameplay_session(rules_path=FIX/'rules-snapshot.json',semantics_paths=sorted(FIX.glob('*.semantics.json')),state_path=FIX/'initial-state.json').state.identity,contracts()[2].identity)

    def test_source_evidence_digest_and_exact_preservation_adapter(self):
        import hashlib
        import turn_lifecycle_preservation as guard
        rules=contracts()[0].to_dict();source=next(s for s in rules['sources'] if s['source_id']=='fictional-turn-lifecycle-v1')
        self.assertEqual(source['content_hash'],'sha256:'+hashlib.sha256((FIX/'fictional-rules.txt').read_bytes()).hexdigest())
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'\n# unrelated change\n')
        self.assertEqual(guard.preceding_bytes('src/future.py',b'new'),b'new')
