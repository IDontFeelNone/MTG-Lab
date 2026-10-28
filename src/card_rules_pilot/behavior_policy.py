"""Bounded conditional behavior over recomputed, pending mana classifications.

The public adapter supplies admitted retained rule facts and actual authored
criterion inputs. This generic calculation has no Card, provider, subject-name,
proposal-label or text-recognition input. It creates no game state or action.
"""
from __future__ import annotations

import hashlib
import json

from .contract import PilotError, canonical, owned, seal
from . import reasoning_policy as classification_policy

POLICY_VERSION = 'card-rules-mana-behavior-policy-v1'
RESULT_VERSION = 'card-rules-mana-behavior-calculation-v1'
HYPOTHETICAL_VERSION = 'card-rules-mana-behavior-priority-hypothetical-v1'
LIMIT = 262_144
_AUTHORITY_RAW = owned({
    'authority': 'CONDITIONAL_BEHAVIOR_IMPLICATIONS_FROM_PENDING_READINGS_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
    'execution_authority': 'BLOCKED',
})


def _authority():
    return json.loads(_AUTHORITY_RAW)


RESTRICTIONS = (
    'All activation, casting, targeting, payment, trigger occurrence, output, response, countering and concrete legality questions remain unevaluated.',
    'No semantic approval, canonical admission or gameplay execution authority is created.',
    'The pending interpretation and its declared scope are assumptions, not established Card semantics or current Oracle verification.',
    'Gained abilities, changed text, copies, external modifiers and arbitrary game states remain outside the retained-text successor reading.',
    'Source coverage does not establish procedure completeness or execution readiness.',
    'Stack implications concern only the selected qualifying ability; they do not establish restrictions on a permanent or every action an opponent could take.',
    'Separate abilities remain separate; no repeatable sequence, combo or successful payment follows.',
)
# Exact canonical retained-rule content pins are integrity bindings, not prose
# tests. The adapter additionally admits enclosing manifests and own-field/domain
# identities. No ambient file is read here and missing facts never get defaults.
_RULE_CONTENT_HASHES = {'602.2': 'c38f87b66a028de1bf4bb19df7f2eb47a42acc7870caac6d28bf9109c3d7d43f', '602.2a': '55c6b37a966ef850b045b879511acc37d05231c74cabdbe865270847145356ba', '605.1': 'b6f0dfc3c5abc9d3bf51b9f867300b93f6fe9842728267420406275d00ef67ff', '605.1a': 'd9646feb8992b717495548b41c0909f7213b36c08e0edf83ddede37b9fb065df', '605.1b': '4d37dc136fabce71a0c2ab95450082c2d7e21baf6ced5a7b8f99ac7e52bf219f', '605.2': 'a59f137f1358f34a45cc0df6060d68991a58bcdca3fb0c40d67ba0ef49cdf5bf', '605.3': '6640cbb2310d226143fad37bbcfb48643a7496a099253ffdfc2a7dbc281a9ee9', '605.3a': '8545691998afa8988fd4b111e0261a24bd07bdaaaccb6adb7efb2b7a88b9c916', '605.3b': 'aec8f28d60f70003087d36ccc7a7a9e826d97a5f02a1cd3fb43a3484a0fc8512', '605.3c': 'a2ce54eb9fbf58b178a90663f0fbaa95d5295ae351a33acef5650c98d4aa8567', '605.4': 'a48c5bceed6c3d4652da339d6e08c70090892db0a7391ec57d31f1c9b0dea249', '605.4a': 'c699d1927c8c11b0cdd8a1ca06ca3a46205150d8ae51ef02bd31e9d83a132fae', '605.5': 'c2953327306fdaeda51dd3558e667b0cbbb3fef8d2a10c7e6427d2dbd9f20df0', '605.5a': '204ee11d197b0ab7f971b582398194b572da30cd5c64720aa5e65aee5c3a8be3', '605.5b': 'aeb49ae52595469ab1cf1323255754c0463364bfe612f8eb509a6d3e71653a06', '115.6': '0c607623fe1c241159dc83945485389daff128f9438a1f6067c121f85bc6ce10', '606.1': '276b4048b0ba24b5340667c453371da5b027cab1d8affb78922794bec7a5702b', '606.2': 'd6c4649d2d1d529135a2b802e43a1e11833aaa33a21cc74692ce3abdc3930730', '405.6c': 'f2a038f368bb6501b3bd7d968e5a32b3b9b5e881b5712b6703d72bd1c1dcb9c8', '601.2a': '213a6f59d23a15eacd9801e1af0e51a987e4c77d87eee7d5fe1a744ff86ad2c2', '106.12': '04bb0f0559f9414fd82ef32a0683665d82fb2ad94b690576ed936b64e14122e6', '106.12a': '59b3fc37e58824e749cf77981206ec399c568ec5a25206c59320ee151afb4418', '106.12b': '2f31a065d0cd7482e0b1fc69200573538b699c18962a21a2c6bcd34d22f0aa58', '614.15': '58cc5662951bd2a66e81684944c8af85fd7dca6ca994650db66f144b3fa8a5fe'}

_BINDING_CONTENT_HASHES = {'602.2': '125d3f0c71b3d89ce0dba6037f401cd5d7d052d75d3a92aa68086e4886aab1b4', '602.2a': '2ee5fcf132a16d4a965d1d7c15bedb0aad8429a429720863a8b5b80bcea7d623', '605.1': '9b2b9cc77100ccbfd3e3d233f39ef4696c5303e16bd9f5f4bbd48748a264d5e7', '605.1a': '5989114ddda664bf38f3debbf37aa097a1618a05e56e93e2bcad1a0369ed1f9c', '605.1b': 'e7371aea705f1a1d4b632efe75fed5b10410b22a45921afbf1c823a1cd4e6c77', '605.2': '8ee5b7e03981055f7d16b4494227b3b1669464431812204ac8650cc9ab9718c8', '605.3': '172685488c2271dc1dcf4a4c5fc3b1bd9dc51ecfa817881df5cff1bc18f8dade', '605.3a': 'a6ba16d3cbc09954e49fdeabe079fe977aa69cb67aaff3707f50b35e5126ddfe', '605.3b': '6a71ee0c9165a6c437a24cb35a38da7160016b26752e308e57332127f25303aa', '605.3c': '3e01fc8f8110793c36d50a652dc94d689040a486983bbe7d9bfc252d3a073a93', '605.4': 'e731a4957e20b17e5eaf62e276014c4e48d44cd5b4b8ba19528f7db3543ca821', '605.4a': 'e6ff7078edfb8c8b8e65b5f46da810d9721efd78ceda8641c043f83908ef6e90', '605.5': 'a9b2c8ee6557ac360b8a95390ef302938cc506dd03c0516a49974e4546c1aa1b', '605.5a': '055814c83452c50bb546895a0903afcb70dc62edffcd76bdfcff081233b15674', '605.5b': 'c4199d90f8d4cef6295cafd653ce37abfdf406f862e0c705e209221076b19672', '115.6': '60048db06f377eb85b4b405800848b45a73e9e24e62b3480c2bab951b34d6348', '606.1': '8ddfbab7b029299f44d8156c8bbc9e8d65c9b1b105e301c40d12cb3dd58386a0', '606.2': '52e64ec353f9877ec1ae73b479c301ec1ba435af65314124d03fba6a6a0e08f4', '405.6c': '89c8630b7bfae087642ab029a8c10d7f4147ae6d6207b2bcc2d930651269d5ee', '601.2a': 'eef1d446f1db753ad942038ce5ed10d36fbffafb607b5f75251a5b9a7088cec7', '106.12': 'aa72ac80f81322637a84581422253b6fcfd5d453277e7fc568e1612fefc3519d', '106.12a': 'e620f5358931574a69c64d5aca02d772c663c58aaaa51eee5ae518565398151c', '106.12b': '2dceafdc63de41bece5329412021a07fb28de3993620296ca93999da6b8f820c', '614.15': '33efe3a1ebb5cc28fbb0e594b42b220bb361c1b629eb531d4e570ce4824be22d'}

_BRANCH_RULES = {
    'CONDITIONAL_ACTIVATED_MANA': ('605.1a', '605.2', '605.3a', '605.3b', '605.3c', '405.6c'),
    'CONDITIONAL_TRIGGERED_MANA': ('605.1b', '605.2', '605.4a'),
    'CONDITIONAL_ORDINARY_ACTIVATED': ('605.1a', '605.5', '602.2', '602.2a'),
    'CONDITIONAL_SPELL_PROPOSAL': ('605.5b', '601.2a'),
    'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER': ('605.1b', '605.5', '605.5a', '605.4'),
    'UNRESOLVED_BEHAVIOR': (),
}
_POLICY_RAW = owned(seal(POLICY_VERSION, {
    'schema_version': POLICY_VERSION,
    'classification_policy_id': classification_policy.POLICY_ID,
    'rule_content_hashes': _RULE_CONTENT_HASHES,
    'binding_content_hashes': _BINDING_CONTENT_HASHES,
    'branch_required_rule_refs': {key: list(value) for key, value in _BRANCH_RULES.items()},
    'classification_calculation': 'Recompute the unchanged classification policy from exact criterion inputs; never accept an imported result as proof.',
    'branch_rule': 'Explicit kind corroborated by a proposed_satisfied applicable kind criterion, completed applicable method, computed eligibility or substantive exclusion, no unresolved active criterion, and exact bound procedure facts jointly select a branch. The spell branch instead requires its explicit spell-kind exclusion evidence.',
    'uncertainty_rule': 'Incomplete, unmet, conflicting, indeterminate or unresolved active inputs and missing relevant facts establish no completed behavior conclusion.',
    'ordinary_placement_rule': 'Activated kind plus completed conditional exclusion plus 602.2/602.2a; never exclusion alone.',
    'priority_rule': '405.6c implication applies only to conditionally eligible activated mana abilities and requires priority immediately before activation and resolution under the stated assumptions; no converse.',
    'hypothetical_schema_version': HYPOTHETICAL_VERSION,
    'scope': list(RESTRICTIONS), **_authority(),
}, 'policy_id'), limit=32_768)
POLICY_ID = json.loads(_POLICY_RAW)['policy_id']


def policy_document():
    return json.loads(_POLICY_RAW)


def _facts(value):
    if type(value) is not dict or any(type(ref) is not str or ref not in _RULE_CONTENT_HASHES for ref in value):
        raise PilotError('closed retained behavior rule references required')
    result = {}
    for ref, binding in value.items():
        if (type(binding) is not dict or set(binding) != {
                'package', 'package_id', 'projection_id', 'projection_schema_version', 'rule'}):
            raise PilotError('closed retained rule binding required')
        if any(type(binding[key]) is not str or not binding[key] for key in (
                'package', 'package_id', 'projection_id', 'projection_schema_version')):
            raise PilotError('exact retained package/projection identity strings required')
        rule = binding['rule']
        if (type(rule) is not dict or rule.get('rule_reference') != ref or
                hashlib.sha256(canonical(rule)).hexdigest() != _RULE_CONTENT_HASHES[ref]):
            raise PilotError('exact retained behavior rule facts required; substitutions rejected')
        if hashlib.sha256(canonical(binding)).hexdigest() != _BINDING_CONTENT_HASHES[ref]:
            raise PilotError('exact retained package/projection bindings required; stale bindings rejected')
        result[ref] = binding
    return result


def _hypothetical(value):
    if value is None:
        return None
    if (type(value) is not dict or set(value) != {'schema_version', 'prior_priority'} or
            type(value['schema_version']) is not str or value['schema_version'] != HYPOTHETICAL_VERSION or
            type(value['prior_priority']) is not str or value['prior_priority'] not in ('TRUE', 'FALSE', 'UNKNOWN')):
        raise PilotError('closed bounded priority hypothetical required')
    return seal(HYPOTHETICAL_VERSION, {
        **value,
        'context_kind': 'EXPLICITLY_ASSUMED_HYPOTHETICAL_NOT_REAL_GAME_OBSERVATION',
        'other_assumptions': [
            'These hypothetical premises apply only if the selected branch is conditionally eligible activated mana.',
            'Only in that branch, the pending retained-text classification is assumed and a qualifying activated mana ability is assumed to have been activated and finished resolving.',
            'These premises are assumptions for the implication, not established activation, payment, legality or game observations.',
        ],
        'card_evidence': False, 'interpretation_revision': False,
        'executable_state_transition': False,
    }, 'hypothetical_id')


def compute(*, proposed_kind, criteria, kind_evidence_refs, rule_facts, hypothetical=None):
    """Return a fresh conditional calculation, never an action recommendation.

    Rule facts are the admitted context's immutable binding views. Missing facts
    yield an explicit unresolved result; malformed or coherently substituted
    supplied evidence rejects. All data is privately owned before any use.
    """
    value = json.loads(owned({'proposed_kind': proposed_kind, 'criteria': criteria,
        'kind_evidence_refs': kind_evidence_refs, 'rule_facts': rule_facts,
        'hypothetical': hypothetical}, limit=LIMIT))
    facts = _facts(value['rule_facts'])
    hyp = _hypothetical(value['hypothetical'])
    classified = classification_policy.compute(proposed_kind=value['proposed_kind'],
        criteria=value['criteria'], kind_evidence_refs=value['kind_evidence_refs'])
    kind = classified['branch']
    completed = classified['method_status'] == ('PROPOSED_SATISFIED' if kind == 'activated' else 'NOT_APPLICABLE')
    resolved = not classified['unresolved_requirements']
    kind_criterion = {'activated': 'activated_kind', 'triggered': 'triggered_kind'}.get(kind)
    kind_supported = (kind_criterion is None or any(
        row['criterion_id'] == kind_criterion and row['state'] == 'proposed_satisfied'
        for row in value['criteria']))
    eligible = kind_supported and completed and resolved and classified['overall_assessment'] == classification_policy.ELIGIBLE
    excluded = kind_supported and completed and resolved and classified['overall_assessment'] == classification_policy.EXCLUDED
    branch = ('CONDITIONAL_ACTIVATED_MANA' if kind == 'activated' and eligible else
              'CONDITIONAL_TRIGGERED_MANA' if kind == 'triggered' and eligible else
              'CONDITIONAL_ORDINARY_ACTIVATED' if kind == 'activated' and excluded and classified['negative_witnesses'] else
              'CONDITIONAL_SPELL_PROPOSAL' if kind == 'spell' and excluded and classified['spell_exclusion'] else
              'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER' if kind == 'triggered' and excluded and classified['negative_witnesses'] else
              'UNRESOLVED_BEHAVIOR')
    required = _BRANCH_RULES[branch]
    classification_refs = list(dict.fromkeys(
        [ref for row in value['criteria'] if row['state'] != 'inapplicable' for ref in row['rule_refs']] +
        [ref[5:] for ref in value['kind_evidence_refs'] if ref.startswith('rule:')]))
    required = tuple(dict.fromkeys((*required, *classification_refs)))
    missing = [ref for ref in required if ref not in facts]
    intended = branch
    if missing:
        branch = 'UNRESOLVED_BEHAVIOR'
    common_antecedents = [
        'The explicitly proposed kind and the applicable pending authored criterion readings are assumed within their declared scope.',
        'The unchanged classification calculation is used; its result is conditional, without semantic approval.',
    ]
    consequences = []
    unresolved = []
    def emit(key, refs, antecedents, conclusion, unknowns):
        consequences.append({
            'consequence_id': key,
            'pending_interpretation': 'EXACT_INPUT_READINGS_BOUND_BY_ENCLOSING_REPORT',
            'classification': classified['overall_assessment'],
            'method_status': classified['method_status'],
            'rule_refs': list(refs),
            'rule_bindings': [{
                'rule_reference': ref, 'package': facts[ref]['package'],
                'package_id': facts[ref]['package_id'], 'projection_id': facts[ref]['projection_id'],
                'rule_id': facts[ref]['rule']['rule_id'],
                'source_anchor': facts[ref]['rule']['source_anchor'],
            } for ref in refs],
            'antecedents': common_antecedents + list(antecedents),
            'conditional_consequence': conclusion,
            'remaining_unknowns': list(unknowns),
            **_authority(),
        })
    if branch == 'CONDITIONAL_ACTIVATED_MANA':
        mana = facts['605.3b']['rule']['semantic_distinctions']
        emit('activated_no_stack', ('605.3b',),
             ['This selected ability qualifies as an activated mana ability under the pending reading.',
              'If that qualifying ability is activated.'],
             {'stack_entry': mana['actual_stack_entry'], 'resolution_context': mana['resolution_sequence'],
              'targetable_as_stack_object': mana['targetable_as_stack_object'],
              'counterable_as_stack_object': mana['counterable_as_stack_object'],
              'respondable_as_stack_object': mana['respondable_as_stack_object'],
              'explanation': 'That qualifying activation resolves immediately after activation without becoming a stack object. Its stack-object targeting, countering and response implications concern this ability only.'},
             ['Whether any activation can occur or has occurred, costs, payment and actual resolution remain unevaluated.',
              'No conclusion concerns targeting or countering the permanent, or whether an opponent can act under another rule.'])
        opportunities = facts['605.3a']['rule']['semantic_distinctions']
        emit('activated_opportunity_categories', ('605.3a',),
             ['This selected ability qualifies as an activated mana ability.'],
             {'categories': opportunities['activation_opportunity_categories'],
              'request_contexts': opportunities['request_may_occur_during'],
              'explanation': 'These are described opportunity categories, including qualifying mana-payment requests during ongoing procedures or resolution.'},
             ['No present permission, priority, legal activation, available resources or outstanding payment is evaluated.'])
        same = facts['605.3c']['rule']['semantic_distinctions']
        emit('same_ability_restriction', ('605.3c',),
             ['Activation of this same qualifying mana ability is assumed to have begun.'],
             {'restricted_subject': same['restricted_subject'], 'begins': same['restriction_begins'],
              'ends': same['restriction_ends'],
              'explanation': 'The same ability cannot be activated again before that activation finishes resolving.'},
             ['No activation sequence, scheduler, separate-ability interaction or repeatable combo is established.'])
        immediate = facts['405.6c']['rule']
        emit('immediate_resolution_context', ('405.6c',),
             ['This is a qualifying mana ability.',
              'The additional-effect implication applies only if both mana production and an additional effect actually belong to that same qualifying ability.'],
             {'behavior': immediate['immediate_resolution']['behavior'],
              'conditional_additional_effect_context': immediate['mana_plus_additional_effect']['relationship'],
              'fine_grained_ordering': immediate['mana_plus_additional_effect']['fine_grained_ordering'],
              'explanation': '405.6c supplies immediate-resolution context. If the qualifying ability has mana plus an additional effect, both share that resolution context; no additional effect is asserted for this subject.'},
             ['Actual output, an additional effect for this subject, and ordering between parts are not established.'])
        prior = hyp['prior_priority'] if hyp else 'UNKNOWN'
        status = {'TRUE': 'CONDITIONAL_RETURN_IMPLICATION',
                  'FALSE': 'ANTECEDENT_ABSENT_NO_RETURN_CONCLUSION',
                  'UNKNOWN': 'APPLICABILITY_UNKNOWN'}[prior]
        emit('activated_priority_implication', ('405.6c',),
             ['The qualifying activated mana ability is assumed to have been activated and finished resolving.',
              'The player held priority immediately before that activation.'],
             {'prior_priority_premise': prior,
              'premise_origin': 'EXPLICIT_HYPOTHETICAL' if hyp else 'NO_REAL_GAME_PRIORITY_EVIDENCE',
              'status': status,
              'recipient_if_antecedents_hold': immediate['post_mana_activation_priority_return_context']['recipient'],
              'return_context_if_antecedents_hold': immediate['post_mana_activation_priority_return_context']['return_context'],
              'explanation': ('Under the explicit hypothetical and other assumptions, the pre-activation priority holder receives priority after resolution.' if prior == 'TRUE' else
                              'The stated antecedent is absent; 405.6c does not establish this return conclusion. It does not forbid receiving priority through another rule.' if prior == 'FALSE' else
                              'Whether the prior-priority antecedent holds is unknown, so applicability of the return implication remains unknown.'),
              'converse_inferred': False},
             ['No real game priority observation or state transition is supplied.',
              'False or unknown antecedents do not establish that a player cannot receive priority by another rule.'])
    elif branch == 'CONDITIONAL_TRIGGERED_MANA':
        trigger = facts['605.4a']['rule']['semantic_distinctions']
        emit('triggered_no_stack', ('605.4a',),
             ['This selected ability qualifies as a triggered mana ability under the pending reading.',
              'If it triggers in the described context of a causing mana ability.'],
             {'stack_entry': trigger['actual_stack_entry'], 'resolution_context': trigger['resolution_sequence'],
              'waits_for_priority': trigger['waits_for_priority'],
              'targetable_as_stack_object': trigger['targetable_as_stack_object'],
              'counterable_as_stack_object': trigger['counterable_as_stack_object'],
              'respondable_as_stack_object': trigger['respondable_as_stack_object'],
              'explanation': 'This qualifying trigger resolves immediately after the causing mana ability without using the stack or waiting for priority.'},
             ['No trigger detection, actual causing event, output, sequence execution or present legality is evaluated.',
              'Activated activation opportunities and the activated priority-return implication do not apply to this triggered branch.'])
    elif branch == 'CONDITIONAL_ORDINARY_ACTIVATED':
        ordinary = facts['602.2a']['rule']['findings']['ordinary_stack_object']
        emit('ordinary_activated_placement_context', ('602.2', '602.2a'),
             ['The explicit proposed kind is activated ability.',
              'The completed conditional classification excludes this ability from mana classification on its retained substantive negatives.',
              'If an activation proposal for this non-mana activated ability begins under the ordinary procedure.'],
             {'object_kind': ordinary['object_kind'], 'relative_stack_position': ordinary['relative_position'],
              'content': ordinary['content'], 'controller_attribution': ordinary['controller_attribution'],
              'explanation': '602.2/602.2a supply ordinary activation placement context: the ability is a noncard object at the top of the stack. The mana-ability no-stack exception is absent under this completed exclusion.'},
             ['No legal activation, successful completion, current priority, actual response window, legal response or counterspell applicability is established.',
              '602.2 to 733 and 602.2a to 701.20a remain unresolved; no recovery or reveal operation is implemented.'])
    elif branch == 'CONDITIONAL_SPELL_PROPOSAL':
        proposal = facts['601.2a']['rule']['findings']['proposal_start']
        emit('spell_proposal_start_context', ('605.5b', '601.2a'),
             ['The explicit proposed kind is a spell instruction, excluded under 605.5b.',
              'If a casting proposal begins under 601.2a.'],
             {'movement': proposal['movement'], 'subject': proposal['subject'],
              'casting_complete_at_start': proposal['casting_complete_at_start'],
              'explanation': 'At the start of a casting proposal the card or card copy moves to the top of the stack. Proposal start does not establish successful casting completion.'},
             ['Casting permission, completion, current priority, legal responses and counterspell applicability remain unevaluated.',
              'No activated-mana opportunity is granted to this spell, including during another spell resolution or an outstanding payment request.',
              '611.2f and 610.5 remain unresolved. This spell-start context is not part of the literal 602.2b b-to-i import.'])
    elif branch == 'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER':
        ordinary = facts['605.5a']['rule']['semantic_distinctions']
        emit('ordinary_triggered_route_only', ('605.5a', '605.4'),
             ['The explicit proposed kind is triggered ability.',
              'The completed conditional classification excludes the host ability from mana classification.'],
             {'route': ordinary['ordinary_procedure'], 'applicable_kind': 'TRIGGERED',
              'placement': 'UNSUPPORTED_603_FRONTIER',
              'explanation': 'The ordinary triggered-procedure route is identified, but broad 603 is outside this retained behavior context. Exclusion alone supplies no stack-placement result.'},
             ['General trigger placement, ordering, priority and response behavior remain unsupported.',
              'An ability of a created object belongs to that object; it is not imported into the host trigger analysis.'])
        unresolved.append('603 is outside this context; general triggered placement, ordering and response semantics remain unsupported.')
    else:
        unresolved += ['No completed mana-exception or ordinary-placement conclusion follows from the available classification, method and bound evidence.']
        if not kind_supported:
            unresolved.append('The applicable kind criterion does not corroborate the explicit proposed kind; contradictory kind input establishes no completed behavior conclusion.')
        if not completed:
            unresolved.append('The applicable assessment method is incomplete, unmet or conflicting; this is not a substantive non-mana property.')
        if not resolved:
            unresolved.append('Unresolved, unsupported, inapplicable or conflicting active substantive readings remain unresolved.')
        if missing:
            unresolved.append('Missing retained bindings: ' + ', '.join(missing))
    if branch in ('CONDITIONAL_ACTIVATED_MANA', 'CONDITIONAL_TRIGGERED_MANA'):
        distinction = facts['605.2']['rule']['semantic_distinctions']
        emit('classification_usability_output_separation', ('605.2',),
             ['The ability qualifies as a mana ability under the pending reading.'],
             {'classification_implies_current_activation_eligibility': distinction['classification_implies_current_activation_eligibility'],
              'classification_implies_current_output': distinction['classification_implies_current_output'],
              'explanation': 'Mana classification remains separate from present usability and actual productive output.'},
             ['Current mana output, useful mana, available resources, activation eligibility and successful payment are not evaluated.'])
    return seal(RESULT_VERSION, {
        'schema_version': RESULT_VERSION, 'policy_id': POLICY_ID,
        'policy_version': POLICY_VERSION, 'classification': classified,
        'proposed_kind': value['proposed_kind'],
        'input_readings': {'criteria': value['criteria'], 'kind_evidence_refs': value['kind_evidence_refs']},
        'branch': branch, 'branch_before_binding_check': intended,
        'required_rule_refs': list(required), 'missing_rule_refs': missing,
        'inference_steps': [
            {'step': 'recompute_classification', 'policy_id': classification_policy.POLICY_ID,
             'outcome': classified['overall_assessment']},
            {'step': 'require_kind_and_completed_resolved_classification',
             'kind': kind, 'kind_criterion_supported': kind_supported,
             'completed_method': completed, 'resolved_active_requirements': resolved,
             'outcome': intended},
            {'step': 'bind_exact_retained_facts', 'required_rule_refs': list(required),
             'missing_rule_refs': missing, 'outcome': branch},
        ],
        'hypothetical_context': hyp,
        'hypothetical_applicability': ('ACTIVATED_MANA_ONLY' if hyp and branch == 'CONDITIONAL_ACTIVATED_MANA' else
                                      'NOT_APPLICABLE_TO_THIS_BRANCH' if hyp else 'NO_HYPOTHETICAL_ASSUMED'),
        'consequences': consequences, 'remaining_unresolved': unresolved,
        'scope_restrictions': list(RESTRICTIONS), **_authority(),
    }, 'calculation_id')
