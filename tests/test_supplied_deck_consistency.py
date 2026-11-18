"""Supplied-population derivation, exact comparison and fail-closed integration."""
import copy
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from probability.draw_access import ASSUMPTIONS, assess_draw_access, canonical_json
from probability.supplied_deck import (INPUT_VERSION, MAX_INPUT_BYTES, SuppliedDeckError,
    assess_supplied_decks, parse_supplied_decks, render_supplied_decks, validate_supplied_decks, _fraction)

ROOT = Path(__file__).resolve().parents[1]


def deck(identifier='original', targets=3, size=60):
    return dict(deck_id=identifier, identity_authority='CALLER_DECLARED', complete=True,
        draw_population=dict(section='main', declared_size=size),
        entries=[dict(card_id='caller:target', quantity=targets, section='main'),
                 dict(card_id='caller:other', quantity=size-targets, section='main'),
                 dict(card_id='caller:side', quantity=15, section='sideboard'),
                 dict(card_id='caller:commander', quantity=1, section='commander'),
                 dict(card_id='caller:companion', quantity=1, section='companion')],
        groups=[dict(group_id='access', members=['caller:target'], minimum=1)],
        schedule=[dict(label='Opening assumption',cards_seen=7),dict(label='Later assumption',cards_seen=9)],
        assumptions=dict(ASSUMPTIONS))


def request(*decks): return dict(schema_version=INPUT_VERSION, decks=list(decks) or [deck()])


def exact(value): return Fraction(int(value['numerator']), int(value['denominator']))


class SuppliedDeckConsistencyTests(unittest.TestCase):
    def test_three_to_four_copy_benchmark_and_exact_positive_delta(self):
        r=assess_supplied_decks(request(deck(),deck('modified',4)))
        self.assertEqual([x['deck_size'] for x in r['configurations']],[60,60])
        self.assertEqual([x['results'][0]['probability']['decimal'] for x in r['configurations']],
                         ['0.315429573349','0.399499625745'])
        self.assertEqual(r['comparison']['status'],'COMPARABLE')
        a,b=r['configurations']
        for x,y,delta in zip(a['results'],b['results'],r['comparison']['differences']):
            self.assertEqual(exact(delta['candidate_minus_baseline']),exact(y['probability'])-exact(x['probability']))

    def test_derivation_delegates_to_owning_engine_without_reimplementing_math(self):
        with patch('probability.supplied_deck.assess_draw_access',wraps=assess_draw_access) as owner:
            r=assess_supplied_decks(request());self.assertEqual(owner.call_count,1)
            args=owner.call_args.args[0]
            self.assertEqual(args['deck_size'],60);self.assertEqual(args['groups'][0]['copies'],3)
            self.assertEqual(assess_draw_access(args),r['configurations'][0]['draw_access_report'])
            self.assertEqual(r['configurations'][0]['results'],assess_draw_access(args)['results'])

    def test_one_two_three_groups_match_exhaustive_small_populations(self):
        for count in (1,2,3):
            d=deck(size=6,targets=1)
            d['entries']=[dict(card_id=str(i),quantity=1,section='main') for i in range(6)]
            d['groups']=[dict(group_id=str(i),members=[str(i)],minimum=1) for i in range(count)]
            d['schedule']=[dict(label=str(n),cards_seen=n) for n in range(7)]
            r=assess_supplied_decks(request(d))['configurations'][0]
            for row in r['results']:
                hands=list(combinations(range(6),row['cards_seen']))
                wanted=set(range(count));expected=Fraction(sum(wanted<=set(h) for h in hands),len(hands))
                self.assertEqual(exact(row['probability']),expected)

    def test_impossible_joint_event_is_zero_and_certain_event_is_one(self):
        d=deck(size=4,targets=2);d['groups'][0]['minimum']=2
        d['groups'].append(dict(group_id='other',members=['caller:other'],minimum=2))
        d['schedule']=[dict(label='three',cards_seen=3),dict(label='four',cards_seen=4)]
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual([exact(x['probability']) for x in r['results']],[0,1])

    def test_requirement_exceeding_available_population_is_not_an_invalid_deck(self):
        d=deck(targets=0);d['groups'][0]['minimum']=1
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual(r['status'],'IMPOSSIBLE_POPULATION_REQUIREMENT')
        self.assertEqual(r['impossible_group_ids'],['access']);self.assertIsNone(r['draw_access_report'])
        self.assertTrue(all(exact(x['probability'])==0 for x in r['results']))
        d['groups'][0]['minimum']=0
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual(r['status'],'CALCULATED');self.assertTrue(all(exact(x['probability'])==1 for x in r['results']))

    def test_impossible_and_possible_matching_questions_can_be_compared(self):
        r=assess_supplied_decks(request(deck(targets=0),deck('modified',4)))
        self.assertEqual(r['comparison']['status'],'COMPARABLE')
        for delta,row in zip(r['comparison']['differences'],r['configurations'][1]['results']):
            self.assertEqual(delta['candidate_minus_baseline'],row['probability'])

    def test_reordering_splitting_and_aggregating_rows_preserves_full_report(self):
        value=request();expected=assess_supplied_decks(value)
        value['decks'][0]['entries'][0]['quantity']=1
        value['decks'][0]['entries'].append(dict(card_id='caller:target',quantity=2,section='main'))
        value['decks'][0]['entries'].reverse()
        self.assertEqual(assess_supplied_decks(value),expected)

    def test_main_sideboard_commander_companion_and_other_sections_remain_distinct(self):
        d=deck();d['entries'].append(dict(card_id='caller:extra',quantity=10,section='other:maybeboard'))
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual(sum(x['quantity'] for x in r['selected_quantities']),60)
        self.assertEqual({x['card_id'] for x in r['selected_quantities']},{'caller:target','caller:other'})
        d['draw_population']=dict(section='sideboard',declared_size=15)
        d['groups'][0]['members']=['caller:side']
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual(r['deck_size'],15);self.assertEqual(exact(r['results'][0]['probability']),1)

    def test_same_identity_in_other_sections_does_not_increase_selected_counts(self):
        d=deck();d['entries'].append(dict(card_id='caller:target',quantity=15,section='sideboard'))
        self.assertEqual(assess_supplied_decks(request(d))['configurations'][0]['derived_groups'][0]['copies'],3)

    def test_complete_population_and_declared_totals_are_required(self):
        for update in ({'complete':False},{'complete':1}, {'draw_population':{'section':'main','declared_size':61}},
                       {'entries':[]}, {'draw_population':{'section':'other:absent','declared_size':1}}):
            value=request();value['decks'][0].update(update)
            with self.subTest(update=update),self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)

    def test_integer_bounds_and_invalid_types_do_not_coerce(self):
        for field in ('quantity','minimum','declared_size','cards_seen'):
            for invalid in (-1,121,True,1.0,'1',None):
                value=request();d=value['decks'][0]
                row=d['entries'][0] if field=='quantity' else d['groups'][0] if field=='minimum' else d['draw_population'] if field=='declared_size' else d['schedule'][0]
                row[field]=invalid
                with self.subTest(field=field,value=invalid),self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)
        d=deck();d['schedule'][0]['cards_seen']=21
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))

    def test_closed_nested_shapes_and_source_authority_flags_refuse(self):
        for path in ((),('decks',0),('decks',0,'entries',0),('decks',0,'groups',0),
                     ('decks',0,'draw_population'),('decks',0,'schedule',0),('decks',0,'assumptions')):
            value=request();obj=value
            for key in path:obj=obj[key]
            obj['verified']=True
            with self.subTest(path=path),self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)
        for field in deck():
            value=request();del value['decks'][0][field]
            with self.subTest(field=field),self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)

    def test_unknown_overlapping_and_duplicate_members_refuse(self):
        for groups in ([dict(group_id='x',members=['absent'],minimum=1)],
                       [dict(group_id='x',members=['caller:side'],minimum=1)],
                       [dict(group_id='x',members=['caller:target']*2,minimum=1)],
                       [dict(group_id='x',members=['caller:target'],minimum=1)]*2,
                       [dict(group_id='x',members=['caller:target'],minimum=1),dict(group_id='y',members=['caller:target'],minimum=1)]):
            d=deck();d['groups']=groups
            with self.subTest(groups=groups),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))

    def test_ambiguous_missing_and_unsupported_section_selection_refuse(self):
        for invalid in (None,[],['main','sideboard'],'all','other:',' Main','unknown'):
            d=deck();d['draw_population']['section']=invalid
            with self.subTest(section=invalid),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))
        d=deck();del d['entries'][0]['section']
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))

    def test_identity_authority_is_never_inferred_from_identifier_spelling(self):
        value=request();value['decks'][0]['entries'][0]['card_id']='magic.real-looking'
        value['decks'][0]['groups'][0]['members']=['magic.real-looking']
        r=assess_supplied_decks(value)
        self.assertEqual(r['configurations'][0]['identity_authority'],'CALLER_DECLARED')
        self.assertFalse(r['real_gameplay_authorized'])
        for invalid in ('CANONICAL','VERIFIED',True,None):
            value['decks'][0]['identity_authority']=invalid
            with self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)

    def test_group_labels_alone_never_establish_equivalence(self):
        a,b=deck(),deck('modified',4);b['groups'][0]['members']=['caller:other']
        r=assess_supplied_decks(request(a,b));self.assertEqual(r['comparison']['status'],'ABSTAINED')
        self.assertFalse(r['comparison']['differences']);self.assertEqual(len(r['configurations']),2)

    def test_different_minimum_or_schedule_abstains_without_discarding_results(self):
        for change in ('minimum','count','label'):
            a,b=deck(),deck('modified',4)
            if change=='minimum':b['groups'][0]['minimum']=2
            elif change=='count':b['schedule'][1]['cards_seen']=10
            else:b['schedule'][0]['label']='Different assumption'
            r=assess_supplied_decks(request(a,b));self.assertEqual(r['comparison']['status'],'ABSTAINED')
            self.assertFalse(r['comparison']['differences']);self.assertTrue(r['configurations'][1]['results'])

    def test_equivalent_member_definitions_ignore_group_labels_and_declaration_order(self):
        a,b=deck(),deck('modified',4)
        for d in (a,b):d['groups'].append(dict(group_id='other',members=['caller:other'],minimum=1))
        b['groups'][0]['group_id']='renamed';b['groups'].reverse()
        r=assess_supplied_decks(request(a,b));self.assertEqual(r['comparison']['status'],'COMPARABLE')

    def test_different_deck_sizes_can_answer_the_same_analytical_question(self):
        r=assess_supplied_decks(request(deck(),deck('modified',3,61)))
        self.assertEqual(r['comparison']['status'],'COMPARABLE')
        self.assertLess(exact(r['comparison']['differences'][0]['candidate_minus_baseline']),0)

    def test_reversing_comparison_changes_delta_sign_without_ranking(self):
        a,b=deck(),deck('modified',4)
        r=assess_supplied_decks(request(a,b));s=assess_supplied_decks(request(b,a))
        self.assertEqual(exact(r['comparison']['differences'][0]['candidate_minus_baseline']),
                         -exact(s['comparison']['differences'][0]['candidate_minus_baseline']))
        self.assertNotIn('winner',r);self.assertNotIn('ranking',r)

    def test_analytical_mapping_is_explicitly_unsupported_not_guessed(self):
        value=request(deck(),deck('modified',4));value['mapping']={'access':'access'}
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)

    def test_bad_schedule_duplicates_order_and_small_population_bounds_refuse(self):
        for schedule in ([],None,[None],[dict(label='x',cards_seen=9),dict(label='y',cards_seen=7)],
                         [dict(label='x',cards_seen=7)]*2):
            d=deck();d['schedule']=schedule
            with self.subTest(schedule=schedule),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(deck(size=6,targets=1)))

    def test_bounded_arrays_versions_and_duplicate_deck_ids_refuse(self):
        for invalid in ([],[deck()]*3,[None],None,{},'deck'):
            with self.assertRaises(SuppliedDeckError):assess_supplied_decks(dict(schema_version=INPUT_VERSION,decks=invalid))
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(deck(),deck()))
        value=request();value['schema_version']='unknown'
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(value)
        d=deck();d['entries']*=103
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))

    def test_unsupported_assumptions_and_invented_input_fields_refuse(self):
        d=deck();d['assumptions']['sampling']='with-replacement'
        with self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))
        for field in ('name','printing_id','canonical_verified','oracle_text'):
            d=deck();d['entries'][0][field]='invented'
            with self.subTest(field=field),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))

    def test_malformed_json_duplicate_keys_nonfinite_and_budgets_refuse(self):
        for raw in (None,bytearray(b'{}'),'NaN','Infinity',b'\xff','\ud800',
                    '{"x":1,"x":2}','[','['*2000+'0'+']'*2000,b'x'*(MAX_INPUT_BYTES+1)):
            with self.subTest(raw=type(raw).__name__),self.assertRaises(SuppliedDeckError):parse_supplied_decks(raw)
        self.assertEqual(parse_supplied_decks(canonical_json(request())),validate_supplied_decks(request()))

    def test_input_and_prior_reports_are_detached_deterministic_and_content_bound(self):
        value=request();saved=copy.deepcopy(value);a=assess_supplied_decks(value);old=copy.deepcopy(a)
        a['input']['decks'][0]['entries'].clear();a['configurations'][0]['results'].clear()
        self.assertEqual(value,saved);self.assertEqual(assess_supplied_decks(value),old)
        changed=request(deck(targets=4));self.assertNotEqual(assess_supplied_decks(changed)['input_id'],old['input_id'])
        self.assertEqual(canonical_json(assess_supplied_decks(saved)),canonical_json(old))

    def test_fraction_presentation_is_exact_signed_and_independent_of_decimal_context(self):
        from decimal import localcontext,Inexact
        with localcontext() as context:
            context.prec=2;context.traps[Inexact]=True
            self.assertEqual(_fraction(Fraction(-1,3))['decimal'],'-0.333333333333')
            self.assertEqual(_fraction(Fraction(1,2*10**12))['decimal'],'0.000000000000')
        self.assertEqual(exact(_fraction(Fraction(1,10**100))),Fraction(1,10**100))

    def test_public_cli_json_text_and_api_agree_and_refusals_exit_two(self):
        value=request(deck(),deck('modified',4));expected=assess_supplied_decks(value)
        cmd=[sys.executable,'-B','-m','probability','deck-consistency','--input','-']
        for format in ('json','text'):
            run=subprocess.run(cmd+['--format',format],input=canonical_json(value).encode(),capture_output=True,cwd=ROOT)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stderr,b'')
            self.assertEqual(run.stdout,render_supplied_decks(expected,readable=format=='text').encode())
        for raw in (b'{}',b'{',b'x'*(MAX_INPUT_BYTES+1)):
            run=subprocess.run(cmd,input=raw,capture_output=True,cwd=ROOT)
            self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['status'],'REFUSED')
            self.assertNotIn('configurations',json.loads(run.stdout))

    def test_resource_report_budget_fails_without_partial_success(self):
        with patch('probability.supplied_deck.MAX_REPORT_BYTES',100),self.assertRaises(SuppliedDeckError):
            assess_supplied_decks(request())

    def test_closed_published_schemas_validate_success_impossible_abstention_and_refusal(self):
        from jsonschema import Draft202012Validator,ValidationError
        validators={}
        for name in ('input','report'):
            schema=json.loads((ROOT/f'src/schemas/v1/supplied-deck-consistency-{name}.schema.json').read_text())
            Draft202012Validator.check_schema(schema)
            validators[name]=Draft202012Validator(schema)
        for value in (request(),request(deck(targets=0)),request(deck(),deck('modified',4))):
            validators['input'].validate(value)
            report=assess_supplied_decks(value)
            validators['report'].validate(report)
            report['configurations'][0]['results'][0]['probability']['approved']=True
            with self.assertRaises(ValidationError):validators['report'].validate(report)
        different=deck('different',4);different['groups'][0]['minimum']=2
        validators['report'].validate(assess_supplied_decks(request(deck(),different)))
        validators['report'].validate(SuppliedDeckError('invalid').as_dict())

    def test_output_identity_includes_whole_input_and_exact_report_content(self):
        from hashlib import sha256
        r=assess_supplied_decks(request());original=r.pop('report_id')
        self.assertEqual(original,'sha256:'+sha256(b'supplied-deck-consistency-report-v1\0'+canonical_json(r).encode()).hexdigest())
        value=request();value['decks'][0]['entries'][2]['quantity']=14
        self.assertNotEqual(assess_supplied_decks(value)['input_id'],r['input_id'])
        self.assertEqual(assess_supplied_decks(value)['configurations'][0]['results'],r['configurations'][0]['results'])

    def test_extreme_bounds_and_zero_quantity_rows_are_explicit(self):
        d=deck(targets=120,size=120);d['schedule']=[dict(label=str(n),cards_seen=n) for n in range(21)]
        r=assess_supplied_decks(request(d))['configurations'][0]
        self.assertEqual(len(r['results']),21);self.assertEqual(exact(r['results'][0]['probability']),0)
        self.assertEqual(exact(r['results'][-1]['probability']),1)
        self.assertIn(dict(card_id='caller:other',quantity=0),r['selected_quantities'])
        d=deck(targets=1,size=1);d['schedule']=[dict(label='zero',cards_seen=0),dict(label='one',cards_seen=1)]
        self.assertEqual([exact(x['probability']) for x in assess_supplied_decks(request(d))['configurations'][0]['results']],[0,1])

    def test_selected_section_mismatch_abstains_even_with_same_event_and_counts(self):
        a,b=deck(),deck('modified',4)
        b['entries']=[dict(row,section='other:experiment') if row['section']=='main' else row for row in b['entries']]
        b['draw_population']['section']='other:experiment'
        r=assess_supplied_decks(request(a,b))
        self.assertEqual(r['comparison']['reasons'],['SELECTED_SECTIONS_DIFFER'])
        self.assertFalse(r['comparison']['differences'])

    def test_compared_delta_is_not_subtracted_from_rounded_presentation(self):
        r=assess_supplied_decks(request(deck(),deck('modified',4)))
        a,b=[Fraction(x['results'][0]['probability']['decimal']) for x in r['configurations']]
        delta=exact(r['comparison']['differences'][0]['candidate_minus_baseline'])
        self.assertNotEqual(delta,b-a)

    def test_unicode_padding_and_unsupported_shapes_fail_closed(self):
        for invalid in ('',' padded ','line\nbreak','a'*129,'\ud800',None,True,{}):
            d=deck();d['entries'][0]['card_id']=invalid
            with self.subTest(identity=repr(invalid)),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))
        for field in ('entries','groups','schedule'):
            for invalid in (None,{},(),['x']):
                d=deck();d[field]=invalid
                with self.subTest(field=field),self.assertRaises(SuppliedDeckError):assess_supplied_decks(request(d))


if __name__=='__main__':unittest.main()
