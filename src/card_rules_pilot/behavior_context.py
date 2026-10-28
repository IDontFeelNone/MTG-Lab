"""One bounded admission of three already-projected procedure units.

The public successor loader owns the original seventeen-unit context and its
four-unit successor context. This adapter reuses those private views and checks
the two complete enclosing historical packages through their actual contracts.
Only three selected rule records enter the new twenty-four-unit consumer view.
No source body or source-reproduction function is used.
"""
from __future__ import annotations

import json
from pathlib import Path

from gameplay_rules.activated_ability_projection import package as activated
from gameplay_rules.activated_ability_projection.contracts import BoundedActivatedAbilityProjection
from gameplay_rules.activated_ability_projection.source import anchor_identity as activated_anchor_identity
from gameplay_rules.casting_stage_family_completion import package as casting
from gameplay_rules.casting_stage_family_completion.contracts import CastingStageFamilyCompletionProjection
from gameplay_rules.casting_stage_family_completion.source import anchor_identity as casting_anchor_identity
from gameplay_rules.retained_stage_validation import validate_retained_stage

from .contract import PilotError, ReviewDocument, owned, seal, exact
from .reassessment import ManaContextReassessment

CONTEXT_VERSION = 'card-rules-bounded-mana-behavior-context-v1'
CONTEXT_LIMIT = 262_144
ADDITIONAL_REFERENCES = ('602.2', '602.2a', '601.2a')
ORIGINAL_REFERENCES = (
    '605.1', '605.1a', '605.1b', '605.2', '605.3', '605.3a',
    '605.3b', '605.3c', '605.4', '605.4a', '605.5', '605.5a', '605.5b',
    '115.6', '606.1', '606.2', '405.6c',
)
SUCCESSOR_REFERENCES = ('106.12', '106.12a', '106.12b', '614.15')
CONTEXT_REFERENCES = ORIGINAL_REFERENCES + SUCCESSOR_REFERENCES + ADDITIONAL_REFERENCES
ACTIVATED_PACKAGE_ID = 'sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4'
CASTING_PACKAGE_ID = 'sha256:72536eb1bbbc3422797215a3630a9f512b9d2a0b758e8a852e4903e71e047e82'
SUCCESSOR_INPUT_ID = 'sha256:780bb6f382c09939d930a5c3df400972c4b584d4b273642e399aef5e56666074'
SUCCESSOR_MANIFEST_ID = 'sha256:7f5cc3b0c51be1251ec80f1f0e7770ef586c732a42c17a4e3f596f5ade73bfb6'
_PINS = {
    '602.2': ('sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553',
              'sha256:23e189bb24316153b53bd6e0e816f632d1cc9be5e0ea45991d22fc1c9af0e9cf'),
    '602.2a': ('sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553',
               'sha256:76b57da23eb35c46e588d8e81d4d0b888087c077b10baf6fb042f287789ecb34'),
    '601.2a': ('sha256:14a1616f247b920f68af5860adce445fa597fe4159de305410de9fa70fc959c2',
               'sha256:fd34b339067b4e11d36a6ac55bb8bfc175efba108b2d9bb7f2632b26377049bc'),
}


class BehaviorContext(ReviewDocument):
    """Immutable owned context; every decoded evidence view is independent."""

    def rules(self):
        return {row['rule']['rule_reference']: row for row in self.to_dict()['rules']}


def _retained(review_root, module, package_id, projection_type):
    # The fixed manifest binds all records and their exact canonical bytes.
    # validate_retained_stage applies string projection schemas, integer review
    # schemas, their different domains and their own identity fields explicitly.
    return validate_retained_stage(Path(review_root), name=module.PACKAGE_NAME,
        package_schema=module.PACKAGE_SCHEMA, package_id=package_id,
        record_domain=module.RECORD_DOMAIN, record_names=module.RECORD_NAMES,
        projection_type=projection_type)


def _enclosing_binding(module, admitted):
    manifest = admitted['manifest']
    projection = admitted['records']['projection.json']
    return {
        'package': module.PACKAGE_NAME, 'package_id': manifest['package_id'],
        'package_schema_version': module.PACKAGE_SCHEMA,
        'projection_id': projection['projection_id'],
        'projection_schema_version': projection['schema_version'],
        'projection_file': manifest['files']['projection.json'],
        'record_ids': manifest['record_ids'],
        'review_identity_domain': module.RECORD_DOMAIN,
        'review_schema_version': 1,
        'integrity_scope': 'COMPLETE_ENCLOSING_PACKAGE_NOT_ADDITIONAL_RULE_SEMANTICS',
    }


def admit_context(*, review_root, successor):
    """Reuse one actual admitted successor and freshly admit the extra context.

    An imported report or caller-supplied hash is never an admission input. The
    caller obtains the successor through load_reassessment for this invocation.
    """
    if type(successor) is not ManaContextReassessment:
        raise PilotError('actual admitted successor required; reports are not evidence')
    # Snapshot public independent views before inspecting or validating them.
    comparison = json.loads(owned(successor.comparison().to_dict()))
    integrity = json.loads(owned(successor.check().to_dict()))
    if (comparison['input_id'] != SUCCESSOR_INPUT_ID
            or integrity['manifest_id'] != SUCCESSOR_MANIFEST_ID):
        raise PilotError('exact PR #218 successor input and manifest required')
    original = comparison['context']['original_comparison']
    evidence = original['candidates'][0]['rules_evidence']
    inherited = evidence['rules']
    if tuple(row['rule']['rule_reference'] for row in inherited) != ORIGINAL_REFERENCES:
        raise PilotError('exact original seventeen-unit interpretation context required')
    for candidate in original['candidates']:
        exact(candidate['rules_evidence'], evidence)
    source = comparison['context']['source_package']
    projection = source['projection.json']
    if tuple(rule['rule_reference'] for rule in projection['rules']) != SUCCESSOR_REFERENCES:
        raise PilotError('exact separately identified four-unit successor addition required')
    coverage = source['composite-coverage.json']['findings']
    if (type(coverage['total_projected_rule_count']) is not int
            or coverage['total_projected_rule_count'] != 104
            or type(coverage['total_projection_count']) is not int
            or coverage['total_projection_count'] != 16
            or len(set(coverage['projected_references'])) != 104):
        raise PilotError('global retained source coverage must remain 104/16')
    rules = list(inherited)
    rules.extend({'package': 'gameplay-rules-mana-classification-source-context',
        'package_id': source['manifest.json']['package_id'],
        'projection_id': projection['projection_id'],
        'projection_schema_version': projection['schema_version'], 'rule': rule}
        for rule in projection['rules'])
    admitted_activated = _retained(review_root, activated, ACTIVATED_PACKAGE_ID,
        BoundedActivatedAbilityProjection)
    admitted_casting = _retained(review_root, casting, CASTING_PACKAGE_ID,
        CastingStageFamilyCompletionProjection)
    enclosing = []
    for module, admitted, selected, anchor_identity in (
        (activated, admitted_activated, ('602.2', '602.2a'), activated_anchor_identity),
        (casting, admitted_casting, ('601.2a',), casting_anchor_identity),
    ):
        enclosing.append(_enclosing_binding(module, admitted))
        projection = admitted['records']['projection.json']
        selected_rules = [rule for rule in projection['rules'] if rule['rule_reference'] in selected]
        if tuple(rule['rule_reference'] for rule in selected_rules) != selected:
            raise PilotError('exact additional retained rule selection required')
        for rule in selected_rules:
            if ((projection['projection_id'], rule['rule_id']) != _PINS[rule['rule_reference']]
                    or rule['source_anchor']['anchor_id'] != anchor_identity(rule['source_anchor'])
                    or rule['source_anchor']['rule_reference'] != rule['rule_reference']):
                raise PilotError('additional rule own identity or anchor binding changed')
            rules.append({'package': module.PACKAGE_NAME,
                'package_id': admitted['manifest']['package_id'],
                'projection_id': projection['projection_id'],
                'projection_schema_version': projection['schema_version'], 'rule': rule})
    if tuple(row['rule']['rule_reference'] for row in rules) != CONTEXT_REFERENCES or len(set(CONTEXT_REFERENCES)) != 24:
        raise PilotError('exact twenty-four distinct retained units required')
    body = {
        'schema_version': CONTEXT_VERSION,
        'context_kind': 'CONSUMER_REUSE_OF_EXISTING_RETAINED_UNITS_ONLY',
        'original_interpretation_context_count': 17,
        'successor_interpretation_context_count': 21,
        'behavior_context_count': 24, 'references': list(CONTEXT_REFERENCES),
        'newly_reused_references': list(ADDITIONAL_REFERENCES),
        'new_source_units': 0, 'new_projections': 0,
        'global_source_units': 104, 'global_projections': 16,
        'source_inspection_allowlist': [], 'source_admission_allowlist': [],
        'fresh_source_reproduction': False,
        'successor_input_id': comparison['input_id'],
        'successor_manifest_id': integrity['manifest_id'],
        'historical_acquisition_identity': source['manifest.json']['historical_acquisition_identity'],
        'source_binding': evidence['source_binding'],
        'rules': rules, 'additional_enclosing_package_bindings': enclosing,
        'relationships': [
            {'from': '602.2', 'to': '602.2a', 'kind': 'STRUCTURAL_PARENT_CHILD'},
            {'from': '601.2a', 'to': 'SPELL_PROPOSAL_CONTEXT', 'kind': 'CONSUMER_SEMANTIC_COMPOSITION'},
            {'from': '602.2/602.2a', 'to': 'ORDINARY_ACTIVATED_CONTEXT', 'kind': 'CONSUMER_SEMANTIC_COMPOSITION'},
        ],
        'unresolved_frontiers': [
            {'origin': '602.2', 'target': '733', 'relationship': 'LITERAL_CITATION'},
            {'origin': '602.2a', 'target': '701.20a', 'relationship': 'LITERAL_CITATION'},
            {'origin': '601.2a', 'target': '611.2f', 'relationship': 'LITERAL_CITATION'},
            {'origin': '601.2a', 'target': '610.5', 'relationship': 'LITERAL_CITATION'},
            {'origin': '605.4', 'target': '603', 'relationship': 'GENERAL_TRIGGERED_PROCEDURE_UNRESOLVED'},
        ],
        'literal_602_2b_import_includes_601_2a': False,
        'historical_dependency_arrays_changed': False, 'historical_reviews_changed': False,
        'source_coverage_establishes_procedure_completeness': False,
        'source_coverage_establishes_execution_readiness': False,
        'semantic_closure': 'OPEN', 'execution_authority': 'BLOCKED',
        'all_ten_activation_responsibilities': 'OPEN / EXECUTION_BLOCKED',
        'source_policy_clearance': 'not_granted',
        'permissions': {name: 'NOT_ESTABLISHED' for name in (
            'private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export')},
    }
    return BehaviorContext._verified(seal(CONTEXT_VERSION, body, 'context_id'), limit=CONTEXT_LIMIT)
