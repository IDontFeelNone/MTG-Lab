"""Executable non-targeted fictional stack abilities; no real Magic admission."""
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
from gameplay_rules.models import (CardGameplaySemantics, GameAction, GameState, GameTransition,
    GameplayRulesSnapshot, STACK_ABILITY_PROFILE, stack_entry_identity)
from gameplay_rules.session import GameplaySession, load_gameplay_session, replay_session, render_session_view
from gameplay_rules.session_cli import main
from gameplay_rules.snapshots import load_rules_snapshot, load_card_semantics, load_game_state
from test_turn_structure import action, changed

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/stack_abilities_v1'


def contracts():
    return (load_rules_snapshot(FIX/'rules-snapshot.json'),
            [load_card_semantics(p) for p in sorted(FIX.glob('*.semantics.json'))],
            load_game_state(FIX/'initial-state.json'))


def session(state=None, semantics=None):
    r, sem, initial = contracts()
    return GameplaySession(r, sem if semantics is None else semantics, initial if state is None else state)


def modified_ability(edit):
    r, sem, state = contracts()
    old = next(s for s in sem if s.card_id == 'pulse-stone')
    b = old.to_dict(); b.pop('semantics_id'); edit(b)
    new = CardGameplaySemantics.create(b)
    def bind(b):
        for o in b['objects']:
            if o['semantics_id'] == old.identity: o['semantics_id'] = new.identity
    return session(changed(state, bind), [new if s.identity == old.identity else s for s in sem])


def pulse(s, actor='A', source='a-pulse', **fields):
    return s.submit(s.action('activate_ability', actor, object_id=source, ability_id='pulse', **fields))


def cycle(s):
    first = s.state.priority_player
    s.submit(s.action('pass_priority', first))
    other = s.state.priority_player
    return s.submit(s.action('pass_priority', other))


def demo():
    s = session()
    for line in (FIX/'actions.jsonl').read_text().splitlines():
        result = s.submit(GameAction.from_dict(json.loads(line)))
        assert result['status'] == 'LEGAL', result['legality']
    return s


class StackAbilityTests(unittest.TestCase):
    def test_activation_pays_once_defers_effect_and_keeps_real_source_separate(self):
        s = session(); before = s.state.to_dict(); result = pulse(s)
        self.assertEqual(result['status'], 'LEGAL'); self.assertEqual(len(result['transitions']), 1)
        after = s.state.to_dict(); entry = after['stack_entries'][0]
        self.assertEqual(after['stack'], [entry['entry_id']])
        self.assertEqual(entry['kind'], 'activated_ability')
        self.assertEqual(entry['source_object_id'], 'a-pulse')
        self.assertEqual(entry['origin_action_id'], result['request']['action_id'])
        self.assertEqual(entry['entry_id'], stack_entry_identity(entry))
        self.assertNotIn('card_id', entry)
        self.assertNotIn(entry['entry_id'], {o['object_id'] for o in after['objects']})
        self.assertEqual(len(after['objects']), len(before['objects']))
        source = next(o for o in after['objects'] if o['object_id'] == 'a-pulse')
        self.assertEqual(source['zone_id'], 'A:battlefield'); self.assertTrue(source['tapped'])
        self.assertEqual(after['players'][0]['mana_pool'], {'red': 1, 'blue': 1})
        self.assertEqual([p['life'] for p in after['players']], [10, 10])
        self.assertEqual(result['transitions'][0]['zone_changes'], [])
        self.assertEqual(s.state.priority_player, 'A')

    def test_both_players_can_respond_and_mixed_stack_resolves_lifo(self):
        s = demo(); history = s.report(); self.assertEqual(history, json.loads((FIX/'history.json').read_text()))
        self.assertEqual(s.view(), json.loads((FIX/'final-view.json').read_text()))
        self.assertEqual(render_session_view(s.view()), (FIX/'final-view.txt').read_text())
        entries = history['entries']
        self.assertEqual(entries[1]['transitions'][-1]['after_state']['priority_player'], 'B')
        typed = entries[3]['transitions'][0]['after_state']['stack_entries']
        self.assertEqual([e['kind'] for e in typed], ['activated_ability', 'activated_ability', 'spell'])
        self.assertEqual([e['source_object_id'] for e in typed], ['a-pulse', 'b-pulse', 'response'])
        self.assertEqual([p['life'] for p in entries[5]['transitions'][-1]['after_state']['players']], [10, 10])
        self.assertEqual([p['life'] for p in entries[7]['transitions'][-1]['after_state']['players']], [10, 12])
        self.assertEqual([p['life'] for p in s.state.players], [12, 12])
        self.assertEqual(s.state.stack, ()); self.assertEqual(s.state.stack_entries, ())
        objs = {o['object_id']: o for o in s.state.objects}
        for who in ['a', 'b']:
            self.assertEqual(objs[who+'-pulse']['zone_id'], who.upper()+':battlefield')
            self.assertTrue(objs[who+'-pulse']['tapped'])
        self.assertEqual(objs['response']['zone_id'], 'B:graveyard')
        self.assertEqual(sum(len(e['transitions']) for e in entries), 19)

    def test_single_pass_does_not_resolve_or_apply_effect(self):
        s = session(); pulse(s); entry_id = s.state.stack[0]
        s.submit(s.action('pass_priority', 'A'))
        self.assertEqual(s.state.stack, (entry_id,)); self.assertEqual(s.state.players[0]['life'], 10)
        self.assertEqual(s.state.priority_player, 'B')

    def test_each_resolution_requires_new_pass_cycle_and_checkpoint(self):
        s = session(); pulse(s); s.submit(s.action('pass_priority','A')); pulse(s,'B','b-pulse')
        e = cycle(s)
        self.assertEqual([t['action']['kind'] for t in e['transitions']], ['pass_priority','perform_state_based_actions','resolve_top_of_stack','perform_state_based_actions'])
        self.assertEqual(len(s.state.stack), 1)
        for t in e['transitions'][:-1]: self.assertIsNone(t['after_state']['priority_player'])
        self.assertEqual(s.state.priority_player, 'A')
        cycle(s); self.assertEqual(s.state.stack, ())

    def test_repeated_tap_activation_and_stale_request_do_not_double_pay(self):
        s = session(); request = s.action('activate_ability','A',object_id='a-pulse',ability_id='pulse')
        s.submit(request); old = s.state.to_dict()
        self.assertEqual(pulse(s)['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), old)
        with self.assertRaisesRegex(GameplayContractError, 'stale_state'): s.submit(request)
        self.assertEqual(s.state.to_dict(), old)

    def test_two_entries_from_untapped_source_have_distinct_origins_and_costs(self):
        s = modified_ability(lambda b: b['abilities'][0].update(tap_cost=False))
        pulse(s); pulse(s)
        entries = s.state.stack_entries
        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0]['entry_id'], entries[1]['entry_id'])
        self.assertNotEqual(entries[0]['origin_action_id'], entries[1]['origin_action_id'])
        self.assertEqual(s.state.players[0]['mana_pool']['red'], 0)
        before = s.state.to_dict(); self.assertEqual(pulse(s)['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), before)
        cycle(s); self.assertEqual(s.state.players[0]['life'], 12)
        cycle(s); self.assertEqual(s.state.players[0]['life'], 14)

    def test_priority_controller_missing_ability_and_source_zone_reject(self):
        for actor, source, ability in [('B','b-pulse','pulse'),('A','b-pulse','pulse'),('A','a-pulse','missing')]:
            s = session(); before = s.state.to_dict()
            result = s.submit(s.action('activate_ability',actor,object_id=source,ability_id=ability))
            self.assertEqual(result['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), before)
        state = changed(contracts()[2], lambda b: next(o for o in b['objects'] if o['object_id']=='a-pulse').update(zone_id='A:hand'))
        s = session(state); self.assertEqual(pulse(s)['status'], 'ILLEGAL')

    def test_insufficient_or_bad_payment_preserves_state_and_stack(self):
        state = changed(contracts()[2], lambda b: b['players'][0]['mana_pool'].update(red=0))
        s = session(state); before = s.state.to_dict()
        self.assertEqual(pulse(s)['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), before)
        s = session(); before = s.state.to_dict()
        self.assertEqual(pulse(s,payment={'red':2})['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), before)

    def test_controller_not_owner_receives_effect_and_pays_cost(self):
        def control(b):
            next(o for o in b['objects'] if o['object_id']=='a-pulse').update(owner='B',zone_id='B:battlefield')
        s=session(changed(contracts()[2],control));pulse(s)
        self.assertEqual(s.state.stack_entries[0]['controller'],'A')
        cycle(s)
        self.assertEqual([p['life'] for p in s.state.players],[12,10])
        source=next(o for o in s.state.objects if o['object_id']=='a-pulse')
        self.assertEqual((source['owner'],source['controller'],source['zone_id']),('B','A','B:battlefield'))

    def test_resolution_never_pays_cost_again_or_moves_source(self):
        s = session(); pulse(s); after = s.state.to_dict(); e = cycle(s)
        resolution = e['transitions'][-2]
        self.assertEqual(resolution['zone_changes'], [])
        self.assertEqual(s.state.players[0]['mana_pool'], after['players'][0]['mana_pool'])
        self.assertEqual(s.state.objects, GameState.from_dict(after).objects)
        self.assertEqual(s.state.players[0]['life'], 12)
        self.assertEqual(s.state.stack_entries, ())

    def test_existing_no_stack_mana_activation_remains_immediate(self):
        s = session(); before = s.state.players[0]['mana_pool']['red']
        e = s.submit(s.action('activate_ability','A',object_id='a-resource',ability_id='make-red'))
        self.assertEqual(e['status'], 'LEGAL'); self.assertEqual(s.state.players[0]['mana_pool']['red'], before+2)
        self.assertEqual(s.state.stack, ()); self.assertEqual(s.state.stack_entries, ())

    def test_unknown_or_unsupported_ability_effects_and_costs_fail_closed(self):
        changes = [lambda b: b.update(completeness='unknown'),
                   lambda b: b['abilities'][0].update(effect={'kind':'add_mana','amount':{'red':1}}),
                   lambda b: b['abilities'][0].update(effect={'kind':'adjust_life','target':'opponent','amount':2}),
                   lambda b: b['abilities'][0].update(effect={'kind':'triggered_ability'}),
                   lambda b: b['abilities'][0]['mana_cost'].update(kind='life'),
                   lambda b: b['abilities'][0]['mana_cost'].update(unsupported=['sacrifice']),
                   lambda b: b.update(restrictions=['only_during_main']),
                   lambda b: b.update(unsupported_text=['replacement or continuous effect'])]
        for edit in changes:
            with self.subTest(edit=edit):
                s = modified_ability(edit); before = s.state.to_dict()
                self.assertIn(pulse(s)['status'], ['INDETERMINATE','UNSUPPORTED']); self.assertEqual(s.state.to_dict(), before)

    def test_target_fields_and_extra_timing_permissions_reject(self):
        for edit in [lambda b: b['abilities'][0].update(targets=['opponent']), lambda b: b['abilities'][0].update(timing='sorcery')]:
            with self.assertRaises(GameplayContractError): modified_ability(edit)
        rules = contracts()[0].to_dict(); rules.pop('rules_snapshot_id'); rules['parameters']['stack_activation']['timing']='sorcery'
        with self.assertRaises(GameplayContractError): GameplayRulesSnapshot.create(rules)

    def test_source_departure_controller_semantics_and_unknown_interactions_block(self):
        r, sem, _ = contracts(); engine = GameplayRulesEngine(r,sem)
        history = demo().report(); boundary = GameState.from_dict(history['entries'][7]['transitions'][1]['after_state'])
        edits = [lambda b: next(o for o in b['objects'] if o['object_id']=='b-pulse').update(zone_id='B:graveyard'),
                 lambda b: b['objects'].__setitem__(slice(None), [o for o in b['objects'] if o['object_id']!='b-pulse']),
                 lambda b: next(o for o in b['objects'] if o['object_id']=='b-pulse').update(controller='A'),
                 lambda b: next(o for o in b['objects'] if o['object_id']=='b-pulse').update(knowledge='unknown')]
        for edit in edits:
            with self.subTest(edit=edit):
                state = changed(boundary, edit); result = engine.apply_action(state, action(state,'resolve_top_of_stack'))
                self.assertNotIsInstance(result, GameTransition); self.assertIn(result.status, ['UNSUPPORTED','INDETERMINATE'])

    def test_life_loss_checkpoint_runs_after_ability_before_priority(self):
        s = modified_ability(lambda b: b['abilities'][0]['effect'].update(amount=-10))
        pulse(s); self.assertEqual(s.state.status, 'in_progress')
        e = cycle(s)
        self.assertEqual(e['transitions'][-2]['after_state']['players'][0]['life'], 0)
        self.assertIsNone(e['transitions'][-2]['after_state']['priority_player'])
        self.assertEqual((s.state.status,s.state.loser_ids,s.state.winner_ids), ('ended',('A',),('B',)))
        before = s.state.to_dict(); self.assertEqual(s.submit(s.action('pass_priority','A'))['status'], 'ILLEGAL'); self.assertEqual(s.state.to_dict(), before)

    def test_changed_source_semantics_and_forged_ability_binding_do_not_resolve(self):
        r,sem,_=contracts();old=next(v for v in sem if v.card_id=='pulse-stone')
        body=old.to_dict();body.pop('semantics_id');body['abilities'][0]['effect']['amount']=3
        altered=CardGameplaySemantics.create(body);engine=GameplayRulesEngine(r,sem+[altered])
        before=GameState.from_dict(demo().report()['entries'][7]['transitions'][1]['after_state'])
        def drift(b):next(o for o in b['objects'] if o['object_id']=='b-pulse')['semantics_id']=altered.identity
        state=changed(before,drift)
        result=engine.apply_action(state,action(state,'resolve_top_of_stack'))
        self.assertEqual(result.status,'UNSUPPORTED')
        self.assertIn('stack_ability_source_state_not_supported',result.unsupported_dimensions)
        def forge(b):
            entry=b['stack_entries'][-1];entry['ability_id']='foreign';entry['entry_id']=stack_entry_identity(entry);b['stack'][-1]=entry['entry_id']
        state=changed(before,forge)
        self.assertEqual(engine.apply_action(state,action(state,'resolve_top_of_stack')).status,'UNSUPPORTED')

    def test_draw_failure_remains_supported_under_new_profile(self):
        def end(b): b.update(phase='ending',step='end')
        s = session(changed(contracts()[2],end))
        for who in ['A','B','B','A']: self.assertEqual(s.submit(s.action('pass_priority',who))['status'], 'LEGAL')
        self.assertEqual((s.state.status,s.state.failed_draw_players,s.state.loser_ids), ('ended',('B',),('B',)))

    def test_rollback_after_resolution_checkpoint_failure_preserves_whole_submission(self):
        s = session(); pulse(s); s.submit(s.action('pass_priority','A')); before = s.report()
        original = GameplayRulesEngine.apply_action
        def block(engine,state,request):
            if request.kind=='perform_state_based_actions' and state.players[0]['life']==12:
                raise GameplayContractError('injected_checkpoint_failure','test only')
            return original(engine,state,request)
        with patch.object(GameplayRulesEngine,'apply_action',block):
            with self.assertRaises(GameplayContractError): s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.report(), before)
        self.assertEqual(s.submit(s.action('pass_priority','B'))['status'], 'LEGAL')

    def test_typed_stack_validation_rejects_forged_membership_and_identity(self):
        s = session(); pulse(s); state = s.state
        edits = [lambda b: b.update(stack_entries=None),lambda b: b.update(stack=[]),
                 lambda b: b['stack_entries'][0].update(kind='triggered_ability'),
                 lambda b: b['stack_entries'][0].update(card_id='fabricated-card'),
                 lambda b: b['stack_entries'][0].update(entry_id='sha256:'+'0'*64),
                 lambda b: b['stack_entries'][0].update(controller='foreign'),
                 lambda b: b['stack_entries'][0].update(origin_action_id=True)]
        for edit in edits:
            with self.subTest(edit=edit), self.assertRaises(GameplayContractError): changed(state, edit)
        def advance(b): b.update(priority_player=None,pending_system_actions=['perform_state_based_actions','advance_step_or_phase'])
        with self.assertRaises(GameplayContractError): changed(state,advance)

    def test_duplicate_origins_and_confused_card_entry_namespaces_reject(self):
        s = modified_ability(lambda b: b['abilities'][0].update(tap_cost=False));pulse(s);pulse(s)
        def duplicate(b):
            e=b['stack_entries'][1];e['origin_action_id']=b['stack_entries'][0]['origin_action_id'];e['entry_id']=stack_entry_identity(e);b['stack'][1]=e['entry_id']
        with self.assertRaises(GameplayContractError): changed(s.state,duplicate)
        def alias(b):
            b['objects'].append(dict(b['objects'][0],object_id=b['stack'][0]))
        with self.assertRaises(GameplayContractError): changed(s.state,alias)

    def test_replay_tampering_rejects_even_with_rehashed_after_state(self):
        s = session(); before = s.state; e = pulse(s); r,sem,_=contracts();engine=GameplayRulesEngine(r,sem)
        body=deepcopy(e['transitions'][0]);body.pop('transition_id');after=body['after_state'];after.pop('state_id');after['players'][0]['life']=12
        after=GameState.create(after);body['after_state']=after.to_dict();body['after_state_id']=after.identity
        forged=GameTransition.create(body)
        with self.assertRaisesRegex(GameplayContractError,'replay_mismatch'):engine.replay_transition(before,forged)

    def test_deterministic_native_and_session_replay_and_private_views(self):
        r,sem,initial=contracts();s=demo();before=initial.to_dict();report=s.report()
        self.assertEqual(replay_session(r,sem,report,expected_session_id=report['session_id']).report(),report)
        self.assertEqual(demo().report(),report)
        report['entries'][0]['transitions'][0]['after_state']['stack_entries'].clear()
        self.assertEqual(len(s.report()['entries'][0]['transitions'][0]['after_state']['stack_entries']),1)
        self.assertEqual(initial.to_dict(),before)

    def test_public_loader_cli_readable_json_and_replay_are_read_only(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()}
        args=['--rules',str(FIX/'rules-snapshot.json'),'--state',str(FIX/'initial-state.json')]
        for p in sorted(FIX.glob('*.semantics.json')):args+=['--semantics',str(p)]
        for mode in ['text','json']:
            out=io.StringIO()
            with patch('sys.stdin',io.StringIO((FIX/'actions.jsonl').read_text())),redirect_stdout(out):
                self.assertEqual(main(args+['--format',mode]),0)
            self.assertIn(demo().state.identity,out.getvalue())
        with redirect_stdout(io.StringIO()):self.assertEqual(main(args+['--replay',str(FIX/'history.json')]),0)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in FIX.iterdir() if p.is_file()})

    def test_public_typed_stack_summary_distinguishes_cards_and_hides_nonpublic_source(self):
        s=session();pulse(s);view=s.view()
        self.assertEqual(view['stack_count'],1)
        self.assertEqual(next(z['count'] for z in view['zones'] if z['kind']=='stack'),0)
        self.assertEqual(view['stack_entries'][0]['kind'],'activated_ability')
        self.assertIn('Stack entries (1)',render_session_view(view))
        self.assertIn('source a-pulse',render_session_view(view))
        def hide(b):next(o for o in b['objects'] if o['object_id']=='a-pulse').update(zone_id='A:hand')
        hidden=session(changed(s.state,hide));view=hidden.view()
        self.assertIsNone(view['stack_entries'][0]['source_object_id'])
        self.assertIsNone(view['stack_entries'][0]['ability_id'])
        self.assertNotIn('a-pulse',render_session_view(view))
        self.assertEqual(hidden.submit(hidden.action('pass_priority','A'))['status'],'UNSUPPORTED')

    def test_old_profiles_and_new_state_pairings_are_explicit(self):
        r,sem,initial=contracts();body=initial.to_dict();body.pop('state_id');body.pop('stack_entries');body['schema_version']='gameplay-state-v4'
        with self.assertRaisesRegex(GameplayContractError,'incompatible_state_profile'):session(GameState.create(body))
        from test_draw_failure import contracts as prior
        old_rules, old_sem, old_state = prior()
        old = next(v for v in old_sem if v.card_id=='pebble-resource')
        b=old.to_dict();b.pop('semantics_id');b['abilities'][0].update(uses_stack=True,effect={'kind':'adjust_life','target':'controller','amount':2})
        new=CardGameplaySemantics.create(b)
        def bind(b):
            for o in b['objects']:
                if o['semantics_id']==old.identity:o.update(semantics_id=new.identity,tapped=False)
        old_session=GameplaySession(old_rules,[new if v.identity==old.identity else v for v in old_sem],changed(old_state,bind))
        self.assertEqual(old_session.submit(old_session.action('activate_ability','A',object_id='a-resource',ability_id='make-red'))['status'],'UNSUPPORTED')

    def test_unknown_mechanics_and_manual_system_actions_fail_closed(self):
        s=session();before=s.state.to_dict()
        for kind in ['counter_ability','trigger_ability','attack','select_target']:
            self.assertEqual(s.submit(s.action(kind,'A'))['status'],'UNSUPPORTED');self.assertEqual(s.state.to_dict(),before)
        with self.assertRaises(GameplayContractError):s.submit(s.action('resolve_top_of_stack',None))

    def test_explicit_rule_policy_source_and_exact_historical_successors(self):
        import stack_ability_preservation as guard
        from pack_simulation_preservation import preceding_bytes
        rules=contracts()[0].to_dict();source=next(s for s in rules['sources'] if s['source_id']=='fictional-stack-abilities-v1')
        self.assertEqual(source['content_hash'],'sha256:'+hashlib.sha256((FIX/'fictional-rules.txt').read_bytes()).hexdigest())
        rules.pop('rules_snapshot_id');rules['rules']=[r for r in rules['rules'] if r['category']!='stack_activation']
        with self.assertRaises(GameplayContractError):GameplayRulesSnapshot.create(rules)
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            self.assertIsInstance(preceding_bytes(name,raw),bytes)
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'\n# unreviewed drift\n')


if __name__=='__main__':unittest.main()
