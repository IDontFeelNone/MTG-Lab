"""Finite authored pending land readings, bound to admitted retained evidence.

The tables select complete subjects explicitly. Reproduction is correspondence,
not text parsing, keyword recognition, cost payment or semantic attestation.
"""
from __future__ import annotations

import hashlib
import json

from .authored import CRITERIA
from .contract import PilotError, canonical, owned, seal
from .land_cards import CARD_BINDINGS, SUBJECTS

PLAN_VERSION = 'card-rules-land-mana-utility-plan-v1'
CANDIDATE_VERSION = 'card-rules-land-mana-utility-pending-interpretation-v1'
INPUT_VERSION = 'card-rules-land-mana-utility-interpretations-v1'
MANIFEST_VERSION = 'card-rules-land-mana-manifest-v1'
INPUT_LIMIT = 262_144
PLAN_LIMIT = 65_536
PREPARED_AT = '2026-10-29T00:00:00Z'
PLAN_ID = 'sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5'

LIMITATIONS = (
    'Complete retained-text interpretations remain pending; integrity and tests supply no semantic attestation.',
    'Historical provider observation is not current Oracle verification or an official Card ruling.',
    'No actual payment, legal target, action sequence, trigger event, damage, output or strategic ranking is determined.',
    'Complete-retained-text self-replacement assessment does not resolve gained abilities, changed text, copies, other effects or arbitrary game states.',
    'Unknown Swamp count and commander color context remain unknown rather than zero or an empty palette.',
    'Broad 603, Commander rules, general mana-payment rules, land-play rules and all unlisted source dependencies remain outside this consumer.',
)


def authority():
    return {'authority': 'ENGINEER_AUTHORED_SOURCE_BOUND_PENDING_LAND_READINGS_ONLY',
        'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
        'review': {'status': 'requires_review', 'human_attestation': None,
                   'canonical_admission': False}, 'execution_authority': 'BLOCKED'}


# Each entry is independently authored. No retained string is inspected to select
# a kind, criterion state, cost, output pattern, relationship or condition.
_READINGS = {
    'snow-wastes-mana': {
        'cost': '{T}', 'instruction': 'Add {C}.', 'pattern': 'fixed_colorless',
        'dependencies': [], 'siblings': [], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The entire retained Card field is one tap-cost mana activation. Its complete cost and mana effect contain no separate instruction replacing this resolving effect. The retained Basic Snow Land type line is considered as context, without importing intrinsic abilities, snow-payment semantics or land-play rules.',
        'counterevidence': ['The retained type line includes Basic and Snow; these labels do not provide the excluded payment, intrinsic-ability or land-play semantics.'],
        'unknowns': ['Available untapped resource, current activation permission and payment feasibility remain unknown.'],
    },
    'port-mana': {
        'cost': '{T}', 'instruction': 'Add {C}.', 'pattern': 'fixed_colorless',
        'dependencies': [], 'siblings': ['port-utility'], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The selected tap-cost mana activation is separate from the paid targeted land-tapping activation. Both are reviewed in the full retained Card field. The second activation directs tapping a target land; it does not replace any part of this selected activation\'s own mana-addition effect. Its cost and target do not belong to this subject.',
        'counterevidence': ['The full Card field does include a target requirement and a paid cost, but both belong to the separately selected utility activation.'],
        'unknowns': ['Current payment feasibility, actual output and activation legality remain unknown.'],
    },
    'port-utility': {
        'cost': '{1}, {T}', 'instruction': 'Tap target land.', 'pattern': 'targeted_land_tapping_utility',
        'dependencies': ['legal_target_land', 'available_payment'], 'siblings': ['port-mana'],
        'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The complete selected activation pays the written mana and tap costs and instructs tapping a target land. The other activation adds colorless mana and remains separately owned. Neither complete instruction replaces this resolving tapping effect; mana paid as cost is not output and the separate mana activation cannot supply output to this subject.',
        'counterevidence': ['The Card also produces mana through its other activation; that does not make this targeted effect a mana instruction.', 'A targeted land-tapping instruction does not establish a legal target, available payment, response window or prevention of any particular payment.'],
        'unknowns': ['A legal target, available payment, successful activation and strategic impact remain unestablished.'],
    },
    'city-mana': {
        'cost': '{T}', 'instruction': 'Add one mana of any color.', 'pattern': 'unrestricted_color_choice',
        'dependencies': [], 'siblings': ['city-damage-trigger'], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The complete selected activation taps this land and adds one mana of any color. The separately retained becomes-tapped damage trigger is also inspected. Its own damage instruction does not replace part or all of this activation\'s resolving mana effect and is not an additional effect owned by this activation. No triggering event or sequence is inferred.',
        'counterevidence': ['The retained Card does have a damage instruction in a separately owned trigger; absence of damage in this activation is not absence of another Card effect.'],
        'unknowns': ['Actual activation, mana choice/output and whether any tapped event or damage occurs remain unknown.'],
    },
    'city-damage-trigger': {
        'cost': None, 'instruction': 'it deals 1 damage to you.', 'pattern': 'damage_trigger_without_mana_output',
        'dependencies': ['actual_trigger_event', 'ordinary_trigger_procedure_603'],
        'siblings': ['city-mana'], 'effect_state': 'separate_triggered_ability',
        'damage': 'it deals 1 damage to you.',
        'context': 'The complete selected subject relates becoming tapped to damage. It is separate from the mana activation. The broader becomes-tapped relationship is not a retained taps-for-mana restriction and does not itself require mana-ability resolution or production. No event is detected. Exclusion from mana classification supplies no ordinary-trigger stack placement, ordering, response timing or damage-resolution procedure at the broad-603 frontier.',
        'counterevidence': ['Becoming tapped can be associated with a mana activation in a concrete state; that possible association does not narrow this complete retained trigger to the qualifying relationship.', 'The adjacent activation adds mana, but it is separately owned and does not provide output to this damage trigger.'],
        'unknowns': ['Whether an event occurs, ordinary-trigger placement/ordering/timing under broad 603 and any actual damage remain unresolved.'],
    },
    'citadel-colorless': {
        'cost': '{T}', 'instruction': 'Add {C}.', 'pattern': 'fixed_colorless',
        'dependencies': [], 'siblings': ['citadel-color-choice'], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The selected complete colorless activation taps this land and adds colorless mana. The other complete activation includes both color-choice mana addition and damage. Both are reviewed as whole-field context. The second activation neither replaces the selected colorless effect nor donates its damage sentence to it.',
        'counterevidence': ['The whole Card field contains damage, owned by the other activation; this selected activation cannot inherit that clause.'],
        'unknowns': ['Current payment feasibility, actual activation and output remain unknown.'],
    },
    'citadel-color-choice': {
        'cost': '{T}', 'instruction': 'Add one mana of any color.', 'pattern': 'unrestricted_color_choice',
        'dependencies': [], 'siblings': ['citadel-colorless'], 'effect_state': 'same_ability_additional_effect',
        'damage': 'This land deals 3 damage to you.',
        'context': 'The entire selected activation contains the mana sentence and the damage sentence after one tap cost. The separately retained colorless activation is also reviewed. Damage is an additional effect of this selected activation, not a cost and not an instruction replacing part of its own resolving mana effect. The colorless activation neither replaces this effect nor gains its damage. This authored ownership reading supports only a conditional same-ability consequence with retained 405.6c.',
        'counterevidence': ['The complete activation has a nonmana damage effect as well as mana production; the second sentence must not be dropped or split into another subject.', 'The other colorless activation is a separate option and does not include this damage sentence.'],
        'unknowns': ['Actual mana, damage, prevention, life totals and fine-grained ordering remain unevaluated.'],
    },
    'coffers-mana': {
        'cost': '{2}, {T}', 'instruction': 'Add {B} for each Swamp you control.',
        'pattern': 'swamp_count_dependent', 'dependencies': ['controlled_swamp_count', 'available_payment'],
        'siblings': [], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The whole retained field is one activation with a paid mana cost and tap cost, followed by an output instruction depending on each Swamp controlled. This written dependency describes the mana effect rather than replacing a prior own effect. No separate retained instruction changes that resolving effect. Potential production is assessed conditionally; the count, actual output, available resources and net benefit remain separate unknowns.',
        'counterevidence': ['The activation costs mana before any output, and its written output depends on a count; potential production does not establish actual or net usable mana.', 'No Swamp count is supplied. Unknown is not zero, and no subtype recognition, counting, break-even threshold or executable sequence is performed.'],
        'unknowns': ['Controlled Swamp count, available payment, actual output and net benefit remain unknown.'],
    },
    'tower-mana': {
        'cost': '{T}', 'instruction': "Add one mana of any color in your commander's color identity.",
        'pattern': 'commander_color_context_dependent', 'dependencies': ['commander_color_identity'],
        'siblings': [], 'effect_state': 'no_additional_effect', 'damage': None,
        'context': 'The complete retained activation taps this land and describes a color choice restricted by the commander\'s color identity. The whole field contains no separate instruction replacing this own effect; the restriction is part of the written output description. Potential mana under a suitable external context remains a pending reading, while no commander, color identity, palette or actual output is supplied.',
        'counterevidence': ['The output is more restricted than an unrestricted any-color instruction; the dependency cannot be discarded.', 'Unknown external commander context is not an empty palette and is not automatically a classification failure. Card color identity and provider annotations do not establish this context.'],
        'unknowns': ['Commander identity, commander color identity, permitted palette and actual output remain unknown.'],
    },
}


def _check_cards(cards):
    expected = {row[0] for row in SUBJECTS}
    if set(cards['subjects']) != expected or set(cards['cards']) != {row[0] for row in CARD_BINDINGS}:
        raise PilotError('exact six-Card nine-subject land evidence required')
    for sid, card_id, passage, owner, limitation in SUBJECTS:
        subject = cards['subjects'][sid]
        if (subject['subject_id'] != sid or subject['card_id'] != card_id
                or subject['selected_passage'] != passage or subject['owner'] != owner
                or subject['ownership_and_context_limitations'] != limitation):
            raise PilotError('exact authored complete land passage correspondence required')


def build_plan(cards_evidence):
    cards = json.loads(owned(cards_evidence))
    _check_cards(cards)
    return seal(PLAN_VERSION, {'schema_version': PLAN_VERSION, 'prepared_at': PREPARED_AT,
        'cohort': 'bounded-land-mana-utility-six-cards-nine-subjects',
        'card_count': 6, 'subject_count': 9,
        'canonical_snapshot_id': cards['canonical_snapshot_id'],
        'acquisition_binding': cards['acquisition'],
        'subjects': [{'subject_id': sid, 'card_id': card_id,
            'mechanical_dossier_id': cards['subjects'][sid]['mechanical_dossier_id'],
            'complete_passage': passage, 'owner': owner,
            'source_field_identity': cards['subjects'][sid]['source_field_identity']}
            for sid, card_id, passage, owner, _ in SUBJECTS],
        'criterion_definitions': CRITERIA,
        'scope': list(LIMITATIONS), 'supersedes_plan_ids': [],
        'historical_pilot_extended': False, **authority()}, 'plan_id')


def _criterion(identifier, refs, sid, reading, triggered):
    active = identifier.startswith('trigger') or identifier == 'qualifying_trigger_relationship'
    state = 'proposed_satisfied' if active == triggered else 'inapplicable'
    absence = 'complete_selected_owned_subject_only'
    supporting = ['selected_passage'] + ['rule:' + ref for ref in refs]
    counter = list(reading['counterevidence'])
    unresolved = ['Human semantic review remains required.']
    if state == 'inapplicable':
        rationale = 'The other criterion family is explicitly inapplicable to this proposed ability kind; this is not a satisfied finding.'
        absence = 'no_absence_finding_inapplicable_criterion'
    elif identifier in ('activated_kind', 'triggered_kind'):
        rationale = reading['context']
        absence = 'no_absence_finding_positive_kind_reading'
    elif identifier in ('potential_mana', 'trigger_potential_mana'):
        negative = sid in ('port-utility', 'city-damage-trigger')
        state = 'proposed_not_satisfied' if negative else 'proposed_satisfied'
        rationale = ('The complete own effect is read as the stated utility/damage instruction without mana addition. A separate sibling ability supplies no production to this subject.' if negative else
            'The complete owned effect is read as potential mana addition under a suitable context. This does not determine present usability, payment or actual output. Written dependency: ' + ', '.join(reading['dependencies'] or ['none beyond the described activation and choice']))
        unresolved += reading['unknowns']
    elif identifier in ('no_target', 'trigger_no_target'):
        negative = sid == 'port-utility'
        state = 'proposed_not_satisfied' if negative else 'proposed_satisfied'
        rationale = ('The complete owned effect explicitly requires a target land. Its target is not attached to the sibling mana activation; neither a legal target nor a response window follows.' if negative else
            'The complete owned cost/event/effect is read as having no target designation. This is an authored whole-passage absence finding independent of any chosen-target count or sibling instruction.')
        unresolved += ['External effects and actual target legality are outside the retained-text reading.']
    elif identifier == 'not_loyalty':
        rationale = 'The entire selected cost is read as the written cost ' + reading['cost'] + ', without a loyalty-symbol cost; retained 606.1 and 606.2 supply classification context only.'
    elif identifier == 'no_library_cost_movement':
        rationale = 'The complete written cost ' + reading['cost'] + ' is read as requiring no card movement into or out of a library. No payment is solved.'
    elif identifier == 'no_library_effect_movement':
        rationale = 'The complete owned effect, including every additional sentence, is read as requiring no card movement into or out of a library. No sibling effect is borrowed.'
    elif identifier == 'self_replacement_considered':
        supporting += ['full_oracle_field', 'rule:614.15']
        rationale = reading['context'] + ' Under retained 614.15, the complete Card field, including separate abilities, is reviewed for text replacing part or all of this resolving ability\'s own effect. No such own-effect replacement is proposed within this complete-retained-text assessment; this is not a universal absence claim.'
        absence = 'complete_retained_card_text_only_not_universal_game_state'
        unresolved += ['Gained abilities, changed text, copies, external effects and arbitrary states remain unknown.']
    elif identifier == 'other_replacements_disregarded':
        rationale = 'Other replacement effects are disregarded for this classification assessment as 605.1a requires. This is a methodological scope choice, not an assertion that external replacement effects are absent.'
        absence = 'no_absence_finding_methodological_disregard_only'
    elif identifier == 'qualifying_trigger_relationship':
        state = 'proposed_not_satisfied'
        supporting += ['full_oracle_field', 'rule:106.12', 'rule:106.12a', 'rule:106.12b']
        rationale = 'The retained becomes-tapped relationship is broader than tapping a land for mana. It is not read as requiring the activation/resolution/production relationship in 605.1b and 106.12/106.12a, nor mana entering a pool. Possible overlap in an actual state supplies no restriction or event detection. 106.12b replacement context is distinct.'
        unresolved += ['No actual tapping event, mana-ability cause or trigger sequence is established.']
    else:
        raise PilotError('unauthored land criterion')
    return {'criterion_id': identifier, 'state': state, 'rule_refs': list(refs),
        'evidence_refs': supporting, 'rationale': rationale, 'absence_scope': absence,
        'counterevidence': counter, 'unresolved': unresolved}


def build_interpretations(cards_evidence, rule_context):
    cards, context = json.loads(owned(cards_evidence)), json.loads(owned(rule_context))
    _check_cards(cards)
    context = context.get('retained_rules', context)
    plan = build_plan(cards)
    refs = {r['rule']['rule_reference'] for r in context['rules']}
    if not {'614.15', '106.12', '106.12a', '106.12b', '405.6c'}.issubset(refs):
        raise PilotError('required admitted retained land rule context missing')
    candidates = []
    for sid, card_id, _, _, _ in SUBJECTS:
        reading, subject = _READINGS[sid], cards['subjects'][sid]
        card = cards['cards'][card_id]
        triggered = sid == 'city-damage-trigger'
        kind_ref = '605.1b' if triggered else '605.1a'
        evidence_refs = ['selected_passage', 'full_oracle_field']
        description = {
            'cost': {'written_cost': reading['cost'], 'payment_feasibility': 'unknown',
                'evidence_refs': evidence_refs,
                'rationale': 'The complete written activation cost is separately authored; damage belongs to the effect, and a trigger has no authored activation cost. No cost parser or payment solver is used.'},
            'output': {'pattern': reading['pattern'], 'written_instruction': reading['instruction'],
                'actual_output': 'unknown', 'dependencies': reading['dependencies'],
                'evidence_refs': evidence_refs,
                'rationale': 'Written output/utility pattern is separate from classification, present resources and actual output. Unknown count/palette is not zero/empty.'},
            'conditions': {'dependencies': reading['dependencies'],
                'supplied_game_inputs': [], 'evidence_refs': evidence_refs,
                'rationale': reading['context']},
            'effect_ownership': {'state': reading['effect_state'], 'owner_subject_id': sid,
                'card_id': card_id, 'damage_clause': reading['damage'],
                'other_subject_ids': reading['siblings'],
                'evidence_refs': evidence_refs + (['rule:405.6c'] if reading['effect_state'] == 'same_ability_additional_effect' else []),
                'rationale': reading['context'], 'counterevidence': reading['counterevidence'],
                'unresolved': reading['unknowns']},
        }
        candidates.append(seal(CANDIDATE_VERSION, {
            'schema_version': CANDIDATE_VERSION, 'prepared_at': PREPARED_AT,
            'plan_id': plan['plan_id'], 'context_id': context['context_id'],
            'subject': subject,
            'source_binding': {'card_id': card_id, 'mechanical_dossier_id': card['mechanical_dossier_id'],
                'canonical_snapshot_id': card['canonical_snapshot_id'],
                'provider_record_id': card['source']['provider_record_id'],
                'record_content_identity': card['source']['record_content_identity'],
                'source_field_identity': subject['source_field_identity']},
            'proposed_kind': 'proposed_triggered_ability' if triggered else 'proposed_activated_ability',
            'kind_evidence_refs': ['selected_passage', 'rule:' + kind_ref],
            'criteria': [_criterion(row['criterion_id'], row['rule_refs'], sid, reading, triggered) for row in CRITERIA],
            'descriptive_readings': description,
            'counterevidence': reading['counterevidence'], 'unresolved': reading['unknowns'],
            'classification_present_usability_distinct': True,
            'limitations': list(LIMITATIONS), **authority()}, 'candidate_id'))
    return seal(INPUT_VERSION, {'schema_version': INPUT_VERSION, 'plan_id': plan['plan_id'],
        'context_id': context['context_id'], 'candidates': candidates,
        **authority()}, 'interpretations_id')


def build_manifest(plan, interpretations):
    files = {}
    for name, value in (('plan.json', plan), ('interpretations.json', interpretations)):
        raw = owned(value, limit=INPUT_LIMIT)
        files[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'identity': value['plan_id' if name == 'plan.json' else 'interpretations_id']}
    return seal(MANIFEST_VERSION, {'schema_version': MANIFEST_VERSION,
        'plan_id': plan['plan_id'], 'interpretations_id': interpretations['interpretations_id'],
        'files': files, **{**authority(),
            'authority': 'CONDITIONAL_LAND_INTELLIGENCE_FROM_PENDING_READINGS_ONLY'}}, 'manifest_id')
