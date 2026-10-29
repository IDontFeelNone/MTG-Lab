"""Finite retained-package admission for the new land consumer's 24-rule context.

All six enclosing packages are validated once through exact fixed manifest pins,
their actual record domains and own identity fields, and their projection
contracts. Only the declared 24 rules enter consumer semantics. No historical
Card cohort or report is an admission input and no source body is opened.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gameplay_rules.source_evidence.artifact_review import verify_artifact_review_package
from gameplay_rules.projection import bounded_mana_package as mana
from gameplay_rules.projection.bounded_mana_contracts import BoundedManaProjection, BoundedManaReview
from gameplay_rules.projection import mana_classification_package as classification
from gameplay_rules.projection import mana_stack_exception_package as stack
from gameplay_rules.projection import mana_context_package as source_context
from gameplay_rules.projection.mana_context_contracts import projection as context_projection
from gameplay_rules.activated_ability_projection import package as activated
from gameplay_rules.activated_ability_projection.contracts import BoundedActivatedAbilityProjection
from gameplay_rules.casting_stage_family_completion import package as casting
from gameplay_rules.casting_stage_family_completion.contracts import CastingStageFamilyCompletionProjection
from gameplay_rules.retained_stage_validation import validate_retained_stage

from . import behavior_policy
from .behavior_context import CONTEXT_REFERENCES
from .contract import PilotError, canonical, exact, identity, read_json, seal
from .rules import ARTIFACT, VERIFICATION, RELEASE

CONTEXT_VERSION = 'card-rules-land-mana-context-v1'
CONTEXT_LIMIT = 262_144
RECORD_LIMIT = 524_288
PACKAGE_IDS = {
    'gameplay-rules-bounded-mana-ability-projection': 'sha256:010ab048c504b4da4327dbda4a666a6754f2d41e93b73ea34bc595b39c929990',
    classification.PACKAGE_NAME: 'sha256:57c9a21ec6a253ad9bfc3a650ec2edc8a389a456eb555a213c3a3f5c673eea73',
    stack.PACKAGE_NAME: 'sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1',
    source_context.PACKAGE_NAME: 'sha256:f572041b0f2da6a405b10a97d8e493f821adfbccb84f8651568d271650893edc',
    activated.PACKAGE_NAME: 'sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4',
    casting.PACKAGE_NAME: 'sha256:72536eb1bbbc3422797215a3630a9f512b9d2a0b758e8a852e4903e71e047e82',
}


def _package(root, name, schema, record_schemas, projection_validator):
    """One finite package; no directory registry or transitive reconstruction."""
    directory = root / name
    if (directory.is_symlink() or not directory.is_dir()
            or {path.name for path in directory.iterdir()} != set(record_schemas) | {'manifest.json'}):
        raise PilotError('exact retained land-context package file set required')
    manifest = read_json(directory / 'manifest.json', limit=RECORD_LIMIT)
    if (type(manifest.get('schema_version')) is not str or manifest['schema_version'] != schema
            or manifest.get('package_id') != PACKAGE_IDS[name]
            or identity(schema, manifest, 'package_id') != PACKAGE_IDS[name]
            or set(manifest.get('files', {})) != set(record_schemas)
            or set(manifest.get('record_ids', {})) != set(record_schemas)):
        raise PilotError('retained land-context manifest contract mismatch')
    records = {}
    for filename, version in record_schemas.items():
        value = read_json(directory / filename, limit=RECORD_LIMIT)
        raw = canonical(value)
        own = 'projection_id' if filename == 'projection.json' else 'review_id'
        if (type(value.get('schema_version')) is not str or value['schema_version'] != version
                or type(value.get(own)) is not str
                or identity(version, value, own) != value[own]
                or manifest['record_ids'][filename] != value[own]):
            raise PilotError('retained land-context record schema/domain/own identity mismatch')
        exact(manifest['files'][filename], {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        records[filename] = value
    projection_validator(records['projection.json'])
    if name == 'gameplay-rules-bounded-mana-ability-projection':
        for filename, value in records.items():
            if filename != 'projection.json':
                BoundedManaReview.from_dict(value)
    return {'manifest': manifest, 'records': records}


def _schemas(names, prefix):
    # This formula is the owning historical package's closed schema convention;
    # it does not inspect ability text or discover a package from the filesystem.
    return {name: prefix + name.removesuffix('.json') + '-v1' for name in sorted(names)}


def _binding(name, value):
    manifest, projection = value['manifest'], value['records']['projection.json']
    return {'package': name, 'package_id': manifest['package_id'],
        'schema_version': manifest['schema_version'], 'projection_id': projection['projection_id'],
        'projection_schema_version': projection['schema_version'],
        'record_ids': manifest['record_ids'], 'files': manifest['files'],
        'integrity_scope': 'COMPLETE_ENCLOSING_PACKAGE_NOT_ADDITIONAL_RULE_SEMANTICS'}


def read_context(review_root):
    """Fresh read-only admission, returning privately owned independent views.

    The fixed manifests bind historical review content and complete projections.
    Checking them does not admit any unselected enclosing member as rule facts.
    The unchanged behavior policy independently checks all selected rule content
    and package/projection bindings against its original exact pins.
    """
    root = Path(review_root).absolute()
    artifact = verify_artifact_review_package(root / 'gameplay-rules-artifact-verification',
        source_root=root / 'gameplay-rules-source-versioning',
        discovery_root=root / 'gameplay-rules-release-discovery-closure')
    if artifact['verification_result_id'] != VERIFICATION:
        raise PilotError('retained artifact verification identity mismatch')
    mana_name = 'gameplay-rules-bounded-mana-ability-projection'
    loaded = {
        mana_name: _package(root, mana_name, mana.PACKAGE_SCHEMA,
            {name: cls.SCHEMA for name, cls in mana.RECORD_TYPES.items()}, BoundedManaProjection.from_dict),
        classification.PACKAGE_NAME: _package(root, classification.PACKAGE_NAME,
            'gameplay-bounded-mana-classification-package-v1',
            _schemas(classification.RECORD_NAMES, 'gameplay-bounded-mana-classification-'),
            lambda value: exact(value, classification.projection())),
        stack.PACKAGE_NAME: _package(root, stack.PACKAGE_NAME,
            'gameplay-bounded-mana-stack-exception-package-v1',
            _schemas(stack.RECORD_NAMES, 'gameplay-bounded-mana-stack-exception-'),
            lambda value: exact(value, stack.projection())),
        source_context.PACKAGE_NAME: _package(root, source_context.PACKAGE_NAME,
            source_context.PACKAGE_SCHEMA,
            _schemas(source_context.RECORD_NAMES, 'gameplay-mana-classification-source-context-'),
            lambda value: exact(value, context_projection())),
    }
    for module, projection_type in ((activated, BoundedActivatedAbilityProjection),
                                    (casting, CastingStageFamilyCompletionProjection)):
        loaded[module.PACKAGE_NAME] = validate_retained_stage(root,
            name=module.PACKAGE_NAME, package_schema=module.PACKAGE_SCHEMA,
            package_id=PACKAGE_IDS[module.PACKAGE_NAME], record_domain=module.RECORD_DOMAIN,
            record_names=module.RECORD_NAMES, projection_type=projection_type)
    rows = {}
    source_binding = loaded[mana_name]['records']['projection.json']['source_binding']
    for name, admitted in loaded.items():
        projection = admitted['records']['projection.json']
        exact(projection['source_binding'], source_binding)
        for rule in projection['rules']:
            ref = rule['rule_reference']
            if ref not in CONTEXT_REFERENCES:
                continue
            anchor = rule['source_anchor']
            if (ref in rows or anchor['rule_reference'] != ref or anchor['artifact_hash'] != ARTIFACT
                    or anchor['effective_date'] != RELEASE):
                raise PilotError('land-context selected rule closure or retained anchor mismatch')
            rows[ref] = {'package': name, 'package_id': admitted['manifest']['package_id'],
                'projection_id': projection['projection_id'],
                'projection_schema_version': projection['schema_version'], 'rule': rule}
    if set(rows) != set(CONTEXT_REFERENCES) or len(rows) != 24:
        raise PilotError('exact twenty-four-rule land context required')
    facts = {ref: rows[ref] for ref in CONTEXT_REFERENCES}
    behavior_policy._facts(facts)
    source = loaded[source_context.PACKAGE_NAME]
    coverage = source['records']['composite-coverage.json']['findings']
    if (type(coverage['total_projected_rule_count']) is not int
            or coverage['total_projected_rule_count'] != 104
            or type(coverage['total_projection_count']) is not int
            or coverage['total_projection_count'] != 16
            or len(set(coverage['projected_references'])) != 104):
        raise PilotError('global retained coverage must remain 104/16')
    reviews = []
    for name, filename in ((classification.PACKAGE_NAME, 'classification-dependency-review.json'),
                           (stack.PACKAGE_NAME, 'consumer-reassessment.json'),
                           (activated.PACKAGE_NAME, 'mana-relationships.json'),
                           (source_context.PACKAGE_NAME, 'dependency-review.json')):
        value = loaded[name]['records'][filename]
        reviews.append({'package': name, 'package_id': PACKAGE_IDS[name], 'record': filename,
            'review_id': value['review_id'], 'schema_version': value['schema_version'],
            'identity_domain': activated.RECORD_DOMAIN if name == activated.PACKAGE_NAME else value['schema_version'],
            'findings': value.get('findings', {key: child for key, child in value.items()
                                           if key not in ('review_id', 'schema_version')})})
    retained = seal(CONTEXT_VERSION, {
        'schema_version': CONTEXT_VERSION,
        'context_kind': 'SEPARATE_LAND_CONSUMER_REUSE_OF_EXISTING_RETAINED_RULES',
        'references': list(CONTEXT_REFERENCES), 'rules': list(facts.values()),
        'context_count': 24, 'historical_context_counts': [17, 21, 24],
        'historical_contexts_reused_as_identity': False,
        'source_binding': source_binding, 'artifact_lineage': artifact,
        'packages': [_binding(name, admitted) for name, admitted in loaded.items()],
        'current_dependency_reviews': reviews,
        'historical_acquisition_identity': source['manifest']['historical_acquisition_identity'],
        'new_source_units': 0, 'new_projections': 0,
        'global_source_units': 104, 'global_projections': 16,
        'source_inspection_allowlist': [], 'source_projection_allowlist': [],
        'fresh_source_reproduction': False,
        'verification_scope': 'RETAINED_METADATA_INTEGRITY_NOT_FRESH_SOURCE_VERIFICATION',
        'unresolved_frontiers': [
            {'origin': '605.4', 'target': '603', 'relationship': 'GENERAL_TRIGGERED_PROCEDURE_UNRESOLVED'},
            {'origin': '602.2', 'target': '733', 'relationship': 'LITERAL_CITATION'},
            {'origin': '602.2a', 'target': '701.20a', 'relationship': 'LITERAL_CITATION'},
            {'origin': '601.2a', 'target': '611.2f', 'relationship': 'LITERAL_CITATION'},
            {'origin': '601.2a', 'target': '610.5', 'relationship': 'LITERAL_CITATION'}],
        'relationships': [
            {'from': '602.2', 'to': '602.2a', 'kind': 'STRUCTURAL_PARENT_CHILD'},
            {'from': '605.1a', 'to': '614.15', 'kind': 'CONSUMER_SEMANTIC_COMPOSITION'},
            {'from': '106.12', 'to': '106.12a', 'kind': 'STRUCTURAL_PARENT_CHILD'},
            {'from': '405.6c', 'to': 'SAME_ABILITY_ADDITIONAL_EFFECT', 'kind': 'CONSUMER_SEMANTIC_COMPOSITION'}],
        'semantic_closure': 'OPEN', 'all_ten_activation_responsibilities': 'OPEN / EXECUTION_BLOCKED',
        'execution_authority': 'BLOCKED', 'source_policy_clearance': 'not_granted',
        'permissions': {name: 'NOT_ESTABLISHED' for name in (
            'private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export')},
    }, 'context_id')
    # Reuse standard bounds without raising historical limits or nesting packages.
    from .contract import owned
    retained = json.loads(owned(retained, limit=CONTEXT_LIMIT))
    return {'retained_rules': retained, 'rule_facts': facts}
