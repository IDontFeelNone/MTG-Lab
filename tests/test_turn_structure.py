"""Executable fictional turn windows over the existing native gameplay kernel."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import (GameAction, GameState, GameTransition, CardGameplaySemantics,
    GameplayRulesSnapshot, STATE_SCHEMAS_BY_PROFILE, TURN_STRUCTURE_PROFILE, content_identity, rule_identity)
from gameplay_rules.session import GameplaySession, load_gameplay_session, replay_session
from gameplay_rules.session_cli import main
from gameplay_rules.snapshots import load_rules_snapshot, load_card_semantics, load_game_state

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/turn_structure_v2'


def contracts(prefix=''):
    return (load_rules_snapshot(FIX/'rules-snapshot.json'),
            [load_card_semantics(p) for p in sorted(FIX.glob('*.semantics.json'))],
            load_game_state(FIX/(prefix+'initial-state.json')))


def changed(state, edit):
    b=state.to_dict();b.pop('state_id');edit(b);return GameState.create(b)


def loaded(prefix='', state=None, sem=None):
    r,definitions,initial=contracts(prefix)
    return GameplaySession(r,definitions if sem is None else sem,initial if state is None else state)


def enter_b(s):
    s.submit(s.action('pass_priority','A'))
    return s.submit(s.action('pass_priority','B'))


def pass_window(s):
    s.submit(s.action('pass_priority','B'))
    return s.submit(s.action('pass_priority','A'))


def objs(s):return {o['object_id']:o for o in s.to_dict()['objects']}


def action(state,kind,actor=None,**fields):
    b=dict(game_id=state.game_id,rules_snapshot_id=state.rules_snapshot_id,expected_state_id=state.identity,kind=kind,actor=actor,object_id=None,ability_id=None,payment=None);b.update(fields);return GameAction.create(b)


class TurnStructureTests(unittest.TestCase):
    def demo(self,prefix=''):
        s=loaded(prefix)
        for line in (FIX/(prefix+'actions.jsonl')).read_text().splitlines():
            self.assertEqual(s.submit(GameAction.from_dict(json.loads(line)))['status'],'LEGAL')
        return s

    def test_complete_primary_actual_history_and_next_player_upkeep(self):
        s=self.demo();self.assertEqual(s.report(),json.loads((FIX/'history.json').read_text()))
        self.assertEqual(s.view(),json.loads((FIX/'final-view.json').read_text()))
        self.assertEqual((s.state.turn_number,s.state.active_player,s.state.phase,s.state.step,s.state.priority_player),(3,'A','beginning','upkeep','A'))
        self.assertEqual(sum(len(e['transitions']) for e in s.report()['entries']),26)
        self.assertEqual(objs(s.state)['b-top']['zone_id'],'B:battlefield')
        self.assertTrue(objs(s.state)['b-resource']['tapped'])

    def test_second_actual_stack_scenario_golden(self):
        s=self.demo('stack-');self.assertEqual(s.report(),json.loads((FIX/'stack-history.json').read_text()))
        self.assertEqual(sum(len(e['transitions']) for e in s.report()['entries']),23)
        self.assertEqual((s.state.phase,s.state.step),('main','action'))
        self.assertEqual(objs(s.state)['upkeep-spell']['zone_id'],'B:graveyard')
        self.assertEqual(s.state.stack,())

    def test_turn_crossing_native_untap_no_priority_then_upkeep(self):
        s=loaded();e=enter_b(s)
        self.assertEqual([t['action']['kind'] for t in e['transitions']],['pass_priority','perform_state_based_actions','advance_step_or_phase','untap_active_player'])
        advance,untap=e['transitions'][-2:]
        self.assertEqual((advance['after_state']['phase'],advance['after_state']['step']),('beginning','untap'))
        self.assertIsNone(advance['after_state']['priority_player']);self.assertEqual(advance['required_system_actions'],['untap_active_player'])
        self.assertEqual((untap['after_state']['step'],untap['after_state']['priority_player']),('upkeep','B'))
        self.assertEqual(untap['after_state']['turn_start']['status'],'upkeep')
        self.assertFalse(objs(s.state)['b-resource']['tapped']);self.assertTrue(objs(s.state)['a-resource']['tapped'])
        self.assertEqual(objs(s.state)['b-top']['zone_id'],'B:library')

    def test_untap_control_not_owner_and_nonbattlefield_unchanged(self):
        initial=changed(contracts()[2],lambda b:(b['objects'][0].update(controller='B'),next(o for o in b['objects'] if o['object_id']=='b-top').update(tapped=True)))
        s=loaded(state=initial);enter_b(s)
        self.assertFalse(objs(s.state)['a-resource']['tapped']);self.assertEqual(objs(s.state)['a-resource']['owner'],'A')
        self.assertTrue(objs(s.state)['b-top']['tapped'])

    def test_existing_mana_ability_legal_in_upkeep(self):
        s=loaded();enter_b(s);e=s.submit(s.action('activate_ability','B',object_id='b-resource',ability_id='make-red'))
        self.assertEqual(e['status'],'LEGAL');self.assertEqual(s.state.step,'upkeep')
        self.assertEqual(s.state.to_dict()['players'][1]['mana_pool'],{'red':2});self.assertTrue(objs(s.state)['b-resource']['tapped'])

    def test_both_passes_required_for_draw_and_checkpoint_before_priority(self):
        s=loaded();enter_b(s);first=s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.state.step,'upkeep');self.assertEqual(s.state.priority_player,'A');self.assertEqual(len(first['transitions']),1)
        e=s.submit(s.action('pass_priority','A'))
        self.assertEqual([t['action']['kind'] for t in e['transitions']],['pass_priority','perform_state_based_actions','advance_step_or_phase','draw_for_turn','perform_state_based_actions'])
        for t in e['transitions'][:-1]:self.assertIsNone(t['after_state']['priority_player'])
        self.assertEqual((s.state.step,s.state.priority_player),('draw','B'))
        draw=e['transitions'][-2];self.assertEqual(draw['zone_changes'],[{'object_id':'b-top','from_zone':'B:library','to_zone':'B:hand'}])
        self.assertEqual(draw['required_system_actions'],['perform_state_based_actions'])
        self.assertIn('draw',{r['category'] for r in draw['rule_references']})
        self.assertIn('upkeep',{r['category'] for r in e['transitions'][2]['rule_references']})

    def test_upkeep_stack_resolves_and_remains_until_another_pass_cycle(self):
        s=loaded('stack-');enter_b(s);s.submit(s.action('activate_ability','B',object_id='b-resource',ability_id='make-blue'))
        cast=s.submit(s.action('cast_spell','B',object_id='upkeep-spell'));self.assertEqual(cast['status'],'LEGAL')
        self.assertEqual(s.state.stack,('upkeep-spell',));self.assertEqual(s.state.to_dict()['players'][1]['mana_pool'],{'blue':0})
        e=pass_window(s);kinds=[t['action']['kind'] for t in e['transitions']]
        self.assertEqual(kinds,['pass_priority','perform_state_based_actions','resolve_top_of_stack','perform_state_based_actions'])
        self.assertNotIn('advance_step_or_phase',kinds);self.assertEqual((s.state.step,s.state.priority_player),('upkeep','B'))
        self.assertEqual(objs(s.state)['b-top']['zone_id'],'B:library')
        pass_window(s);self.assertEqual(s.state.step,'draw');self.assertEqual(objs(s.state)['b-top']['zone_id'],'B:hand')

    def test_draw_uses_explicit_order_not_object_array_and_only_once(self):
        s=loaded();enter_b(s);pass_window(s);self.assertEqual(list(s.state.library_order['B:library']),['b-next'])
        self.assertEqual(objs(s.state)['b-next']['zone_id'],'B:library')
        pass_window(s);self.assertEqual(s.state.step,'action')
        draws=[t for e in s.report()['entries'] for t in e['transitions'] if t['action']['kind']=='draw_for_turn'];self.assertEqual(len(draws),1)
        initial=changed(contracts()[2],lambda b:b['library_order']['B:library'].reverse());s=loaded(state=initial);enter_b(s);pass_window(s)
        self.assertEqual(objs(s.state)['b-next']['zone_id'],'B:hand');self.assertEqual(objs(s.state)['b-top']['zone_id'],'B:library')

    def test_draw_owner_controller_and_exact_destination(self):
        initial=changed(contracts()[2],lambda b:next(o for o in b['objects'] if o['object_id']=='b-top').update(controller='A'))
        s=loaded(state=initial);enter_b(s);pass_window(s);o=objs(s.state)['b-top']
        self.assertEqual((o['owner'],o['controller'],o['zone_id']),('B','B','B:hand'))

    def test_sorcery_and_land_timing_stay_illegal_until_main(self):
        rules,sem,initial=contracts();ids={d.card_id:d.identity for d in sem}
        initial=changed(initial,lambda b:b['objects'].append(dict(object_id='sorcery',card_id='ember-scroll',semantics_id=ids['ember-scroll'],owner='B',controller='B',zone_id='B:hand',tapped=False,knowledge='known')))
        s=loaded(state=initial);enter_b(s);s.submit(s.action('activate_ability','B',object_id='b-resource',ability_id='make-red'));before=s.state.to_dict()
        e=s.submit(s.action('cast_spell','B',object_id='sorcery'));self.assertEqual(e['status'],'ILLEGAL');self.assertIn('not_main_action_window',e['legality']['failed_requirements']);self.assertEqual(s.state.to_dict(),before)
        pass_window(s);before=s.state.to_dict();e=s.submit(s.action('play_land','B',object_id='b-top'));self.assertEqual(e['status'],'ILLEGAL');self.assertEqual(s.state.to_dict(),before)
        pass_window(s);self.assertEqual(s.submit(s.action('play_land','B',object_id='b-top'))['status'],'LEGAL')

    def test_incorrect_priority_and_manual_system_actions_preserve_state(self):
        s=loaded();enter_b(s);before=s.state.to_dict();e=s.submit(s.action('pass_priority','A'))
        self.assertEqual(e['status'],'ILLEGAL');self.assertEqual(s.state.to_dict(),before)
        before=s.report()
        for kind in ['untap_active_player','draw_for_turn','advance_step_or_phase']:
            with self.assertRaisesRegex(GameplayContractError,'player_action_required'):s.submit(s.action(kind,None))
        self.assertEqual(s.report(),before)

    def test_native_player_actions_block_during_untap_and_due_actor_required(self):
        s=loaded();e=enter_b(s);pending=GameState.from_dict(e['transitions'][-2]['after_state']);engine=GameplayRulesEngine(*contracts()[:2])
        a=action(pending,'pass_priority','B');r=engine.apply_action(pending,a)
        self.assertEqual(r.status,'ILLEGAL');self.assertIn('required_system_action_pending',r.to_dict()['failed_requirements'])
        self.assertEqual(engine.evaluate_action(pending,action(pending,'untap_active_player','B')).status,'ILLEGAL')
        t=engine.apply_action(pending,action(pending,'untap_active_player'));settled=GameState.from_dict(t.after_state)
        self.assertEqual(settled.step,'upkeep');self.assertEqual(engine.evaluate_action(settled,action(settled,'untap_active_player')).status,'ILLEGAL')
        self.assertEqual(engine.evaluate_action(settled,action(settled,'draw_for_turn')).status,'ILLEGAL')

    def test_progress_rejects_skipped_windows_repeated_queue_and_forged_flags(self):
        state=contracts()[2]
        edits=[lambda b:b['turn_start'].update(status='upkeep'),lambda b:b.update(phase='beginning',step='untap'),
               lambda b:b.update(phase='beginning',step='upkeep'),lambda b:b['turn_start'].update(turn_number=True),lambda b:b['turn_start'].update(player_id='B'),
               lambda b:b.update(priority_player=None,pending_system_actions=['untap_active_player']),lambda b:b['turn_start'].update(status='pending_draw'),
               lambda b:b['turn_start'].update(status='complete',extra=True),lambda b:b.update(phase='combat',step='attack')]
        for edit in edits:
            with self.subTest(edit=edit),self.assertRaises(GameplayContractError):changed(state,edit)
        s=loaded();e=enter_b(s);untap=GameState.from_dict(e['transitions'][-2]['after_state'])
        for edit in [lambda b:b.update(priority_player='B'),lambda b:b.update(pending_system_actions=['draw_for_turn']),lambda b:b.update(step='draw')]:
            with self.assertRaises(GameplayContractError):changed(untap,edit)
        upkeep=s.state
        with self.assertRaises(GameplayContractError):changed(upkeep,lambda b:b.update(priority_player=None,pending_system_actions=['draw_for_turn','perform_state_based_actions']))

    def test_empty_library_draw_rolls_back_final_upkeep_pass_only(self):
        def empty(b):b['objects'][:]=[o for o in b['objects'] if o['zone_id']!='B:library'];b['library_order']['B:library']=[]
        s=loaded(state=changed(contracts()[2],empty));enter_b(s);s.submit(s.action('pass_priority','B'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'empty_library_draw_rule_not_implemented'):s.submit(s.action('pass_priority','A'))
        self.assertEqual(s.report(),before);self.assertEqual(s.state.step,'upkeep');self.assertEqual(s.state.priority_player,'A');self.assertEqual(s.state.status,'in_progress')

    def test_unsupported_untap_restriction_and_draw_effect_fail_closed(self):
        rules,sem,initial=contracts();old=next(x for x in sem if x.card_id=='pebble-resource');b=old.to_dict();b.pop('semantics_id');b['restrictions']=['does_not_untap'];new=CardGameplaySemantics.create(b)
        initial=changed(initial,lambda b:[o.update(semantics_id=new.identity) for o in b['objects'] if o['card_id']=='pebble-resource'])
        s=loaded(state=initial,sem=[new if d.identity==old.identity else d for d in sem]);before=s.state.to_dict();self.assertEqual(s.submit(s.action('pass_priority','A'))['status'],'UNSUPPORTED');self.assertEqual(s.state.to_dict(),before)
        initial=changed(contracts()[2],lambda b:b['active_effects'].append({'effect_id':'draw-replacement','capability':'replacement_effects','affected_actions':['draw_for_turn'],'knowledge':'unsupported'}))
        s=loaded(state=initial);enter_b(s);s.submit(s.action('pass_priority','B'));before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'active_effect:draw-replacement'):s.submit(s.action('pass_priority','A'))
        self.assertEqual(s.report(),before)

    def test_explicit_library_contract_is_reused_and_closed(self):
        state=contracts()[2]
        for edit in [lambda b:b.pop('library_order'),lambda b:b.update(library_order=None),lambda b:b['library_order'].update({'B:library':['b-top','b-top']}),lambda b:b['library_order'].update({'B:library':['a-next']}),lambda b:b['library_order'].update({'B:library':[False]})]:
            with self.assertRaises(GameplayContractError):changed(state,edit)

    def test_source_bound_snapshot_windows_policy_and_profile_pairing(self):
        rules,sem,state=contracts();base=rules.to_dict()
        for edit in [lambda b:b['parameters']['turn_steps'].reverse(),lambda b:b['parameters']['turn_start'].pop('priority_windows'),lambda b:b['parameters']['turn_start'].update(draw_count=True),lambda b:b['rules'].__setitem__(slice(None),[r for r in b['rules'] if r['category']!='upkeep'])]:
            b=deepcopy(base);b.pop('rules_snapshot_id');edit(b)
            with self.assertRaises(GameplayContractError):GameplayRulesSnapshot.create(b)
        with self.assertRaises(TypeError):STATE_SCHEMAS_BY_PROFILE[TURN_STRUCTURE_PROFILE]='gameplay-state-v1'
        old=ROOT/'tests/fixtures/turn_lifecycle_v1';old_rules=load_rules_snapshot(old/'rules-snapshot.json');old_sem=[load_card_semantics(p) for p in old.glob('*.semantics.json')]
        bad=changed(state,lambda b:b.update(rules_snapshot_id=old_rules.identity))
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):GameplaySession(old_rules,old_sem,bad)
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):GameplayRulesEngine(old_rules,old_sem).evaluate_action(bad,action(bad,'pass_priority','A'))
        b=state.to_dict();b.pop('state_id');b['schema_version']='gameplay-state-v2'
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):GameplaySession(rules,sem,GameState.create(b))

    def test_unknown_upkeep_evidence_cannot_authorize_window_actions(self):
        rules,sem,state=contracts();b=rules.to_dict();b.pop('rules_snapshot_id')
        for r in b['rules']:
            if r['category']=='upkeep':r['status']='unknown';r['rule_hash']=rule_identity(r)
        rules=GameplayRulesSnapshot.create(b);new=[]
        for d in sem:
            v=d.to_dict();v.pop('semantics_id');v['rules_snapshot_id']=rules.identity;new.append(CardGameplaySemantics.create(v))
        ids={d.card_id:d.identity for d in new}
        state=changed(state,lambda b:(b.update(rules_snapshot_id=rules.identity),[o.update(semantics_id=ids[o['card_id']]) for o in b['objects']]))
        s=GameplaySession(rules,new,state);before=s.state.to_dict();e=s.submit(s.action('pass_priority','A'))
        self.assertEqual(e['status'],'INDETERMINATE');self.assertEqual(s.state.to_dict(),before)
        self.assertTrue(any(x.startswith('rule_coverage:fictional.turn-structure.upkeep') for x in e['legality']['unknown_requirements']))

    def test_replay_native_and_session_recompute_and_rehash_tampering_rejects(self):
        for prefix in ['', 'stack-']:
            r,sem,initial=contracts(prefix);s=self.demo(prefix);report=s.report();engine=GameplayRulesEngine(r,sem);state=initial
            self.assertEqual(replay_session(r,sem,report,expected_session_id=report['session_id']).report(),report)
            for e in report['entries']:
                for raw in e['transitions']:
                    t=GameTransition.from_dict(raw);self.assertEqual(engine.replay_transition(state,t).identity,t.identity);state=GameState.from_dict(t.after_state)
            bad=deepcopy(report);bad['entries'][1]['transitions'][-1]['after_state']['step']='draw';bad['session_id']=content_identity('gameplay-session-v0',{k:v for k,v in bad.items() if k!='session_id'})
            with self.assertRaises(GameplayContractError):replay_session(r,sem,bad)

    def test_state_history_library_and_public_view_ownership(self):
        r,sem,initial=contracts();before=initial.to_dict();s=GameplaySession(r,sem,initial);prior=s.state;enter_b(s);pass_window(s)
        self.assertEqual(initial.to_dict(),before);self.assertEqual(prior.to_dict(),before)
        report=s.report();report['initial_state']['library_order']['B:library'].clear();report['entries'].clear();view=s.view();view['players'][0]['life']=999
        self.assertEqual(s.state.to_dict()['players'][0]['life'],10);self.assertEqual(list(s.state.library_order['B:library']),['b-next']);self.assertEqual(len(s.report()['entries']),4)
        self.assertNotIn('library_order',s.view());self.assertTrue(all('objects' not in z for z in s.view()['zones'] if z['visibility']=='hidden'))

    def test_exact_historical_v0_and_v1_golden_replays(self):
        for dirname,rulesdir in [('gameplay_session_v0','gameplay_rules'),('turn_lifecycle_v1','turn_lifecycle_v1')]:
            f=ROOT/'tests/fixtures'/dirname;d=ROOT/'tests/fixtures'/rulesdir;report=json.loads((f/'history.json').read_text());r=load_rules_snapshot(d/'rules-snapshot.json');sem=[load_card_semantics(p) for p in d.glob('*.semantics.json')]
            self.assertEqual(replay_session(r,sem,report,expected_session_id=report['session_id']).report(),report)

    def test_actual_public_cli_and_load_both_scenarios_read_only(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()}
        for prefix in ['', 'stack-']:
            args=['--rules',str(FIX/'rules-snapshot.json'),'--state',str(FIX/(prefix+'initial-state.json'))]
            for p in sorted(FIX.glob('*.semantics.json')):args+=['--semantics',str(p)]
            for mode in ['json','text']:
                out=io.StringIO()
                with patch('sys.stdin',io.StringIO((FIX/(prefix+'actions.jsonl')).read_text())),redirect_stdout(out):self.assertEqual(main(args+['--format',mode]),0)
                self.assertIn(self.demo(prefix).state.identity,out.getvalue())
            with redirect_stdout(io.StringIO()):self.assertEqual(main(args+['--replay',str(FIX/(prefix+'history.json'))]),0)
            self.assertEqual(load_gameplay_session(rules_path=FIX/'rules-snapshot.json',semantics_paths=sorted(FIX.glob('*.semantics.json')),state_path=FIX/(prefix+'initial-state.json')).state.identity,contracts(prefix)[2].identity)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()})

    def test_exact_fictional_source_and_preservation_successors(self):
        import turn_structure_preservation as guard
        r=contracts()[0].to_dict();source=next(s for s in r['sources'] if s['source_id']=='fictional-turn-structure-v2')
        self.assertEqual(source['content_hash'],'sha256:'+hashlib.sha256((FIX/'fictional-rules.txt').read_bytes()).hexdigest())
        self.assertEqual(set(guard.ledger()['replacements']),guard.REPLACEMENT_PATHS)
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();self.assertEqual(hashlib.sha256(guard.preceding_bytes(name,raw)).hexdigest(),pin['old_sha256'])
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'\n# unrelated change\n')
