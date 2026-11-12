"""Real multi-action fictional transitions over the unchanged gameplay kernel."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import CardGameplaySemantics, GameAction, GameState, content_identity
from gameplay_rules.session import (GameplaySession, decode_session_json, load_gameplay_session,
                                    replay_session, render_session_view)
from gameplay_rules.session_cli import main
from gameplay_rules.snapshots import load_card_semantics, load_game_state, load_rules_snapshot

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'tests/fixtures/gameplay_rules'
FIXTURE=ROOT/'tests/fixtures/gameplay_session_v0'


def loaded(state=None, semantics=None):
    return GameplaySession(load_rules_snapshot(OLD/'rules-snapshot.json'),
        semantics if semantics is not None else [load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))],
        state or load_game_state(FIXTURE/'initial-state.json'))


def change(state, mutate):
    b=state.to_dict();b.pop('state_id');mutate(b);return GameState.create(b)


def cli_args():
    return ['--rules',str(OLD/'rules-snapshot.json'),'--state',str(FIXTURE/'initial-state.json')]+[
        arg for path in sorted(OLD.glob('*.semantics.json')) for arg in ('--semantics',str(path))]


class GameplaySessionTests(unittest.TestCase):
    def demo(self):
        session=loaded()
        for line in (FIXTURE/'actions.jsonl').read_text().splitlines():session.submit(GameAction.from_dict(json.loads(line)))
        return session

    def test_complete_actual_short_game_and_exact_native_history(self):
        session=self.demo();r=session.report();state=session.state.to_dict()
        self.assertEqual(r,json.loads((FIXTURE/'history.json').read_text()))
        self.assertEqual(state['turn_number'],2);self.assertEqual(state['active_player'],'B')
        self.assertEqual((state['phase'],state['step'],state['priority_player']),('beginning','start','B'))
        self.assertEqual([p['life'] for p in state['players']],[10,8])
        objects={o['object_id']:o for o in state['objects']}
        self.assertEqual(objects['moss-plot']['zone_id'],'A:battlefield')
        self.assertEqual(objects['ember-scroll']['zone_id'],'A:graveyard')
        self.assertTrue(objects['pebble-resource']['tapped'])
        self.assertEqual(state['stack'],[]);self.assertEqual(state['revision'],20)
        self.assertEqual(len(r['entries']),15)
        self.assertEqual([e['status'] for e in r['entries']],['ILLEGAL','ILLEGAL','LEGAL','LEGAL','LEGAL','ILLEGAL','LEGAL','LEGAL','LEGAL','LEGAL','UNSUPPORTED','LEGAL','LEGAL','LEGAL','LEGAL'])
        self.assertEqual(sum(len(e['transitions']) for e in r['entries']),20)

    def test_actual_mana_generation_payment_and_separate_land_capability(self):
        session=self.demo();entries=session.report()['entries']
        mana=entries[6]['transitions'][0]['after_state'];cast=entries[7]['transitions'][0]['after_state']
        self.assertEqual(mana['players'][0]['mana_pool'],{'red':2})
        self.assertEqual(cast['players'][0]['mana_pool'],{'red':0})
        self.assertEqual(cast['stack'],['ember-scroll'])
        self.assertEqual(entries[6]['request']['object_id'],'pebble-resource')
        self.assertEqual(entries[4]['request']['object_id'],'moss-plot')

    def test_wrong_priority_and_unpayable_cost_preserve_state(self):
        s=loaded();before=s.state.to_dict()
        denied=s.submit(s.action('pass_priority','B'))
        self.assertEqual(denied['status'],'ILLEGAL');self.assertIn('actor_lacks_priority',denied['legality']['failed_requirements'])
        self.assertEqual(s.state.to_dict(),before);self.assertEqual(denied['transitions'],[])
        s=loaded(load_game_state(OLD/'game-state.json'));before=s.state.to_dict()
        denied=s.submit(s.action('cast_spell','A',object_id='ember-scroll'))
        self.assertEqual(denied['status'],'ILLEGAL');self.assertTrue(denied['legality']['payment']['failed_requirements'])
        self.assertEqual(s.state.to_dict(),before)

    def test_land_timing_and_exhausted_allowance_are_kernel_rejections(self):
        s=loaded();self.assertEqual(s.submit(s.action('play_land','A',object_id='moss-plot'))['status'],'ILLEGAL')
        initial=load_game_state(OLD/'game-state.json')
        initial=change(initial,lambda b:b['objects'].append(dict(next(o for o in b['objects'] if o['object_id']=='moss-plot'),object_id='second-plot')))
        s=loaded(initial);s.submit(s.action('play_land','A',object_id='moss-plot'));before=s.state.to_dict()
        denied=s.submit(s.action('play_land','A',object_id='second-plot'))
        self.assertIn('land_play_allowance_exhausted',denied['legality']['failed_requirements']);self.assertEqual(before,s.state.to_dict())

    def test_exact_system_queue_order_and_resolution_requires_both_passes(self):
        s=loaded(load_game_state(OLD/'game-state.json'))
        s.submit(s.action('activate_ability','A',object_id='pebble-resource',ability_id='make-red'))
        s.submit(s.action('cast_spell','A',object_id='ember-scroll'))
        one=s.submit(s.action('pass_priority','A'));self.assertEqual(len(one['transitions']),1)
        self.assertEqual(s.state.stack,('ember-scroll',));self.assertEqual(s.state.priority_player,'B')
        two=s.submit(s.action('pass_priority','B'))
        self.assertEqual([t['action']['kind'] for t in two['transitions']],['pass_priority','perform_state_based_actions','resolve_top_of_stack','perform_state_based_actions'])
        self.assertEqual(s.state.priority_player,'A');self.assertEqual(s.state.stack,())

    def test_stack_resolves_only_top_and_returns_priority_between_objects(self):
        initial=load_game_state(OLD/'game-state.json')
        def setup(b):
            b['players'][0]['mana_pool']={'blue':2}
            b['objects'].append(dict(next(o for o in b['objects'] if o['object_id']=='swift-lantern'),object_id='second-lantern'))
        s=loaded(change(initial,setup))
        for obj in ('swift-lantern','second-lantern'):s.submit(s.action('cast_spell','A',object_id=obj))
        self.assertEqual(s.state.stack,('swift-lantern','second-lantern'))
        s.submit(s.action('pass_priority','A'));s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.state.stack,('swift-lantern',));self.assertEqual(s.state.priority_player,'A')
        s.submit(s.action('pass_priority','A'));s.submit(s.action('pass_priority','B'))
        self.assertEqual(s.state.stack,())

    def test_unmodeled_mechanics_and_unknown_state_do_not_execute(self):
        s=loaded();before=s.state.to_dict()
        result=s.submit(s.action('declare_attackers','A'))
        self.assertEqual(result['status'],'UNSUPPORTED');self.assertEqual(before,s.state.to_dict())
        unknown=change(s.state,lambda b:b['players'][0].update(life=None));s=loaded(unknown)
        result=s.submit(s.action('pass_priority','A'));self.assertEqual(result['status'],'INDETERMINATE');self.assertEqual(s.state.to_dict(),unknown.to_dict())

    def test_unsupported_structured_effect_is_not_inferred_from_text(self):
        semantics=[load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))]
        old=next(x for x in semantics if x.card_id=='ember-scroll');b=old.to_dict();b.pop('semantics_id');b['effects']=[{'kind':'invented-target-selection'}]
        new=CardGameplaySemantics.create(b);semantics=[new if x is old else x for x in semantics]
        initial=change(load_game_state(OLD/'game-state.json'),lambda b:[o.update(semantics_id=new.identity) for o in b['objects'] if o['card_id']=='ember-scroll'])
        s=loaded(initial,semantics);result=s.submit(s.action('cast_spell','A',object_id='ember-scroll'))
        self.assertEqual(result['status'],'UNSUPPORTED');self.assertEqual(s.state.to_dict(),initial.to_dict())

    def test_contract_failure_stale_binding_and_direct_system_action_are_atomic(self):
        s=loaded();request=s.action('pass_priority','A');s.submit(request);before=s.report()
        with self.assertRaisesRegex(GameplayContractError,'stale_state'):s.submit(request)
        self.assertEqual(before,s.report())
        with self.assertRaisesRegex(GameplayContractError,'player_action_required'):s.submit(s.action('resolve_top_of_stack',None))
        self.assertEqual(before,s.report())
        with self.assertRaises(GameplayContractError):s.submit({'kind':'pass_priority'})
        self.assertEqual(before,s.report())

    def test_invalid_game_rules_object_bindings_and_initial_boundary_reject(self):
        initial=load_game_state(FIXTURE/'initial-state.json');rules=load_rules_snapshot(OLD/'rules-snapshot.json');sem=[load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))]
        for mutate in (lambda b:b.update(game_id='other-fictional-game'),lambda b:b.update(rules_snapshot_id='sha256:'+'0'*64),
                       lambda b:b.update(phase='combat'),lambda b:b.update(priority_player=None),
                       lambda b:b['objects'][0].update(semantics_id='sha256:'+'0'*64)):
            with self.assertRaises(GameplayContractError):GameplaySession(rules,sem,change(initial,mutate))

    def test_private_input_and_output_ownership_preserves_prior_states(self):
        rules=load_rules_snapshot(OLD/'rules-snapshot.json');sem=[load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))];initial=load_game_state(FIXTURE/'initial-state.json');before=initial.to_dict()
        s=GameplaySession(rules,sem,initial);first=s.state;s.submit(s.action('pass_priority','A'))
        self.assertEqual(first.to_dict(),before);self.assertEqual(initial.to_dict(),before)
        returned=s.state;object.__setattr__(returned,'_payload',initial._payload)
        self.assertEqual(s.state.priority_player,'B')
        view=s.view();view['players'][0]['life']=999;report=s.report();report['entries'].clear()
        self.assertEqual(s.view()['players'][0]['life'],10);self.assertEqual(len(s.report()['entries']),1)

    def test_replay_recomputes_every_transition_and_preserves_exact_identities(self):
        s=self.demo();r=s.report();rules=load_rules_snapshot(OLD/'rules-snapshot.json');sem=[load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))]
        again=replay_session(rules,sem,r,expected_session_id=r['session_id'])
        self.assertEqual(again.report(),r);self.assertEqual(again.state.to_dict(),s.state.to_dict())
        self.assertEqual(self.demo().report(),r)
        bad=deepcopy(r);bad['entries'][9]['transitions'][-1]['after_state']['players'][1]['life']=99
        body={k:v for k,v in bad.items() if k!='session_id'};bad['session_id']=content_identity('gameplay-session-v0',body)
        with self.assertRaises(GameplayContractError):replay_session(rules,sem,bad)
        with self.assertRaises(GameplayContractError):replay_session(rules,sem,bad,expected_session_id=r['session_id'])
        bad=deepcopy(r);bad['entries'][0]['sequence']=False
        with self.assertRaises(GameplayContractError):replay_session(rules,sem,bad)
        bad=deepcopy(r);bad['unexpected']=True
        with self.assertRaises(GameplayContractError):replay_session(rules,sem,bad)

    def test_public_display_hides_hidden_identities_and_replay_is_explicit_full_information(self):
        s=self.demo();view=s.view();self.assertEqual(view,json.loads((FIXTURE/'final-view.json').read_text()))
        self.assertEqual(render_session_view(view),(FIXTURE/'final-view.txt').read_text())
        self.assertNotIn('unobserved-library-object',json.dumps(view));self.assertNotIn('swift-lantern',render_session_view(view))
        self.assertIn('unobserved-library-object',json.dumps(s.report()))
        self.assertIn('FULL_INFORMATION_REPLAY',s.report()['scope'])

    def test_terminal_state_and_bounded_attempts_fail_closed(self):
        initial=load_game_state(OLD/'game-state.json');initial=change(initial,lambda b:b['players'][1].update(life=2))
        s=loaded(initial);s.submit(s.action('activate_ability','A',object_id='pebble-resource',ability_id='make-red'));s.submit(s.action('cast_spell','A',object_id='ember-scroll'))
        s.submit(s.action('pass_priority','A'));s.submit(s.action('pass_priority','B'));self.assertEqual(s.state.status,'ended')
        before=s.state.to_dict();self.assertEqual(s.submit(s.action('pass_priority','A'))['status'],'ILLEGAL');self.assertEqual(s.state.to_dict(),before)
        s=loaded()
        with patch('gameplay_rules.session.MAX_ATTEMPTS',0):
            with self.assertRaisesRegex(GameplayContractError,'session_bound'):s.submit(s.action('pass_priority','A'))
        self.assertEqual(len(s.report()['entries']),0)

    def test_blocked_system_bound_rolls_back_the_entire_player_submission(self):
        s=loaded();s.submit(s.action('pass_priority','A'));before=s.report()
        with patch('gameplay_rules.session.MAX_SYSTEM_TRANSITIONS',0):
            with self.assertRaisesRegex(GameplayContractError,'session_bound'):s.submit(s.action('pass_priority','B'))
        self.assertEqual(before,s.report());self.assertEqual(s.state.priority_player,'B')

    def test_rules_and_semantics_are_privately_owned_after_initialization(self):
        rules=load_rules_snapshot(OLD/'rules-snapshot.json');sem=[load_card_semantics(f) for f in sorted(OLD.glob('*.semantics.json'))]
        initial=load_game_state(FIXTURE/'initial-state.json');s=GameplaySession(rules,sem,initial);expected=s.report()
        object.__setattr__(rules,'_payload',{})
        for definition in sem:object.__setattr__(definition,'_payload',{})
        self.assertEqual(expected,s.report());self.assertEqual(s.submit(s.action('pass_priority','A'))['status'],'LEGAL')

    def test_strict_transport_duplicate_keys_nonfinite_types_and_bounds(self):
        for raw in ('{"kind":1,"kind":2}','{"x":{"a":1,"a":2}}','{"x":NaN}','broken','\ud800'):
            with self.assertRaises(GameplayContractError):decode_session_json(raw)
        with self.assertRaises(GameplayContractError):decode_session_json(' '* (2*1024*1024+1))
        self.assertEqual(decode_session_json('{"ok":true}'),{'ok':True})

    def test_actual_public_loader_and_cli_sequence_replay_json_and_text(self):
        before={p:p.read_bytes() for root in (OLD,FIXTURE) for p in root.rglob('*') if p.is_file()}
        owner=load_gameplay_session(rules_path=OLD/'rules-snapshot.json',semantics_paths=sorted(OLD.glob('*.semantics.json')),state_path=FIXTURE/'initial-state.json');self.assertEqual(owner.state.turn_number,1)
        for fmt in ('json','text'):
            out=io.StringIO()
            with patch('sys.stdin',io.StringIO((FIXTURE/'actions.jsonl').read_text())),redirect_stdout(out):code=main(cli_args()+['--format',fmt])
            self.assertEqual(code,2)  # Deliberately rejected choices do not stop later legal actions.
            if fmt=='json':
                lines=[json.loads(x) for x in out.getvalue().splitlines()];self.assertEqual(len(lines),16);self.assertEqual(lines[-1]['view'],self.demo().view())
            else:self.assertIn('Fictional turn 2: active B',out.getvalue())
            out=io.StringIO()
            with redirect_stdout(out):code=main(cli_args()+['--format',fmt,'--replay',str(FIXTURE/'history.json')])
            self.assertEqual(code,0);self.assertIn('4bc642bec3c5a95f3925b1c7ce4711dbeb1bc5140409b8cebb139fdb707be308',out.getvalue())
        self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_cli_malformed_action_does_not_prevent_later_explicit_legal_action(self):
        s=loaded();valid=json.dumps(s.action('pass_priority','A').to_dict())+'\n';out=io.StringIO()
        with patch('sys.stdin',io.StringIO('{bad}\n'+valid)),redirect_stdout(out):code=main(cli_args())
        lines=[json.loads(x) for x in out.getvalue().splitlines()];self.assertEqual(code,2);self.assertEqual(lines[1]['type'],'error');self.assertEqual(lines[2]['view']['priority_player'],'B')
        out=io.StringIO()
        with patch('gameplay_rules.session_cli.MAX_CONTRACT_BYTES',32),patch('sys.stdin',io.StringIO('x'*33+valid)),redirect_stdout(out):code=main(cli_args())
        self.assertEqual(code,2);self.assertEqual(len(out.getvalue().splitlines()),2)

    def test_exact_source_preservation_rejects_coherently_rehashed_substitution(self):
        import gameplay_session_preservation as guard
        import hashlib
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'future')
        for name in guard.ADDITION_PATHS:
            self.assertTrue(guard.is_addition(ROOT/name,ROOT))
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/name;p.parent.mkdir(parents=True);p.write_bytes((ROOT/name).read_bytes()+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,Path(d))
        self.assertFalse(guard.is_addition(ROOT/'src/gameplay_rules/future.py',ROOT))
