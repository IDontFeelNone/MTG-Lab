"""One fixed source package, fresh validation and append-only output.

Offline reproduction validates current retained files, never substitutes for the
separate fresh owner-artifact proof. No successful-validation cache is present.
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from pathlib import Path

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.casting_permission_family import package as predecessor
from gameplay_rules.casting_permission_family.contracts import CastingPermissionFamilyProjection
from gameplay_rules.retained_stage_validation import validate_retained_stage
from .dependency_package import _root, _read
from .bounded_mana_package import HISTORICAL_ACQUISITION_ID
from .bounded_mana_source import _REFERENCES as MANA_REFERENCES
from .mana_context_source import SELECTED_REFERENCES, verified_anchors
from .mana_context_contracts import (CANONICAL_MAIN, PACKAGE_SCHEMA, RECORD_LIMIT,
    PACKAGE_LIMIT, ContextPackage, canonical, own, seal, projection, authority)

PACKAGE_NAME = 'gameplay-rules-mana-classification-source-context'
RECORD_NAMES = frozenset(('projection.json','dependency-review.json','composite-coverage.json'))
PRIOR_PACKAGE_ID = 'sha256:1cf5def840852e91dc157b654006ea48f74c9c12a766f56f4fae40eda3bf7e9e'
DEFAULT_REVIEW_ROOT = Path(__file__).resolve().parents[3]/'reference-reviews'
# Exact finite canonical-base projections used for outgoing-reference accounting.
# Reopening after lineage validation is safe only when the privately owned bytes
# independently match these historical pins before interpretation or use.
_RETAINED_PROJECTION_SHA256 = MappingProxyType({
    'gameplay-rules-bounded-activated-ability-procedure-projection': '92c5cfaf55f7b9bb5d1e7858b4b23615bd8742dcbfaf04fd8f9748102a9760f8',
    'gameplay-rules-bounded-casting-projection': '3152401d4042a42a1d2dbc869e3997f48bebbb476b0a93392b32fcdb4c67cc6d',
    'gameplay-rules-bounded-mana-ability-projection': 'e558ef74088ceb241c782c7fdde9836f0cde7b5d7949ac2280efa00608498fb1',
    'gameplay-rules-bounded-mana-classification-projection': 'f4ca9c16d6f84f529382501c6199f4902a6e25c08e1dc94c4f8d1055024662b7',
    'gameplay-rules-bounded-mana-stack-exception-projection': '2ca1e99bfbbc789b2cd410953af992529484f937254418d07df9ab2a4c675d21',
    'gameplay-rules-bounded-shared-proposal-legality': 'ae4685d4efb0cbd738341ea0c3ff009e33f392e69b992b5a616f021632baf11b',
    'gameplay-rules-bounded-shared-target-allocation': '5d5b7a0f70ec657d6ab2f6f0c521b2db931f6380235d78efc46c23997984607a',
    'gameplay-rules-bounded-shared-target-declaration': 'bdfb73ec399a210cb46dd9141b2ce55a4cb804b3df5ea865086d45e4950cd19e',
    'gameplay-rules-casting-permission-family': '4d873442ff5007f4e1548a106fdbb8af385114dd8a18f3a1cd999217c4f97a24',
    'gameplay-rules-casting-stage-family-completion': '1d0cfb629b109ef1706c32be2371e265e633ccb47aab7399494620d492dd906a',
    'gameplay-rules-foundational-dependencies': '962f22de3041fdc0fe5f3a5c1ff5d6f562f5c9c5628ee8da5d3eb9008417f4f2',
    'gameplay-rules-foundational-projection': '6d4062e69f497d84f514b17d6ce26610c2ffa57b0eec5752044764e0602d9005',
    'gameplay-rules-object-control-exceptions': '38d32800cfa380f12331c73a55c4733bb98dd0f9fb7b5ee39f07b214aceb1359',
    'gameplay-rules-zone-change-direct-dependencies': 'd56cca77c87f9698a2e06d6252aa5b860d57ad62531f402190ea142889d52c26',
    'gameplay-rules-zone-change-exceptions': 'f495fc217a287ac2f379350f3eef2f5b7bac9ca350baddb3e561599055d06a51',
})


def _fail(code):
    raise GameplayContractError('mana_context_package',code)


def _snapshot(records):
    if type(records) is ContextPackage:
        return records.to_dict()
    return own(records)


def validate_historical(*, review_root):
    root=_root(review_root)
    predecessor.validate_historical(review_root=root)
    retained=validate_retained_stage(root,name=predecessor.PACKAGE_NAME,
        package_schema=predecessor.PACKAGE_SCHEMA,package_id=PRIOR_PACKAGE_ID,
        record_domain=predecessor.RECORD_DOMAIN,record_names=predecessor.RECORD_NAMES,
        projection_type=CastingPermissionFamilyProjection)
    records=retained['records']
    composite=own(records['composite-coverage.json']['findings'])
    predecessor._resolve_package_bindings(composite,PRIOR_PACKAGE_ID)
    rules=own(composite['all_prior_rule_bindings'])
    prior_projection=records['projection.json']
    for rule in prior_projection['rules']:
        rules[rule['rule_reference']]={
            'retained_package':predecessor.PACKAGE_NAME,'package_id':PRIOR_PACKAGE_ID,
            'projection_id':prior_projection['projection_id'],'rule_id':rule['rule_id'],
            'anchor_identity':rule['source_anchor']['anchor_id'],
            'source_anchor':own(rule['source_anchor']),'identity_basis':'EXISTING_STANDALONE_ID'}
    components=composite['projection_components']
    references=[ref for component in components for ref in component['projected_references']]
    if (len(references)!=100 or len(set(references))!=100 or set(references)!=set(rules)
            or len(components)!=15 or set(references)&set(SELECTED_REFERENCES)):
        _fail('EXACT_DISJOINT_100_UNIT_15_PROJECTION_PREDECESSOR_REQUIRED')
    # Preserve genuine outgoing references explicitly, including unresolved broad
    # families. This accounting does not alter any historical dependency array.
    outgoing={}
    names={value['retained_package'] for value in rules.values()}
    if names != set(_RETAINED_PROJECTION_SHA256):
        _fail('EXACT_FINITE_HISTORICAL_PROJECTION_INPUTS_REQUIRED')
    for name in sorted(names):
        raw=_read(root/name/'projection.json')
        if hashlib.sha256(raw).hexdigest()!=_RETAINED_PROJECTION_SHA256[name]:
            _fail('HISTORICAL_PROJECTION_PRIVATE_BYTES_CHANGED')
        old=json.loads(raw)
        for rule in old['rules']:
            refs=rule.get('direct_dependency_references',[])
            if refs:
                outgoing[rule['rule_reference']]=own(refs)
    return {'prior_package_id':PRIOR_PACKAGE_ID,'projection_components':components,
        'rule_bindings':rules,'historical_outgoing_references':outgoing,
        'historical_acquisition_identity':HISTORICAL_ACQUISITION_ID}


def _record(kind,body):
    schema='gameplay-mana-classification-source-context-'+kind+'-v1'
    return seal(schema,{'schema_version':schema,'canonical_base':CANONICAL_MAIN,
        'non_executable':True,'source_body_retained':False,'semantic_closure':'OPEN',
        'execution_readiness':'BLOCKED',**body,**authority()},'review_id')


def _records(binding):
    p=projection()
    rules={r['rule_reference']:r for r in p['rules']}
    all_refs=set(binding['rule_bindings'])|set(SELECTED_REFERENCES)
    unresolved=[]
    historical_accounting=[]
    for source,targets in sorted(binding['historical_outgoing_references'].items()):
        for target in targets:
            covered=target in all_refs or target=='605'
            row={'from_reference':source,'target_reference':target,
                'relationship_kind':'HISTORICAL_NUMBERED_REFERENCE_UNCHANGED',
                'historical_rule_id':binding['rule_bindings'][source]['rule_id'],
                'source_coverage':'RESOLVED_SOURCE_ONLY' if covered else 'UNRESOLVED',
                'historical_dependency_array_rewritten':False}
            historical_accounting.append(row)
            if not covered:
                unresolved.append(own(row))
    mana_bindings=[{'rule_reference':ref,**own(binding['rule_bindings'][ref])} for ref in MANA_REFERENCES]
    if len(mana_bindings)!=13:
        _fail('COMPLETE_EXISTING_605_FAMILY_REQUIRED')
    dependency=_record('dependency-review',{
        'projection_id':p['projection_id'],
        'literal_numbered_citations':{'106.12':['605'],'106.12a':[],'106.12b':[],'614.15':[]},
        'literal_citation_resolution':[
            {'from_reference':'106.12','target_reference':'605','relationship_kind':'LITERAL_NUMBERED_CITATION',
                'source_rule_id':rules['106.12']['rule_id'],'resolution':'COMPLETE_EXISTING_13_UNIT_FAMILY_SOURCE_COVERAGE_ONLY',
                'target_rule_bindings':mana_bindings,'semantic_closure_established':False,'execution_readiness_established':False}],
        'structural_relationships':[
            {'parent':'106.12','child':ref,'relationship_kind':'PARENT_SUBRULE_CONTEXT_NOT_LITERAL_CITATION'}
            for ref in ('106.12a','106.12b')],
        'semantic_support':[
            {'criterion_rule':'605.1a','support_rule':'614.15','relationship_kind':'AUTHORED_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION',
                'scope':'SELF_REPLACEMENT_ASSESSMENT_METHOD'},
            {'criterion_rule':'605.1b','support_rule':'106.12','relationship_kind':'AUTHORED_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION',
                'scope':'TAP_FOR_MANA_REFERENT'},
            {'criterion_rule':'605.1b','support_rule':'106.12a','relationship_kind':'AUTHORED_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION',
                'scope':'QUALIFYING_TRIGGER_RELATIONSHIP'}],
        'historical_outgoing_reference_accounting':historical_accounting,
        'genuine_unresolved_outgoing_references':unresolved,'new_unresolved_outgoing_references':[],
        'historical_dependency_arrays_changed':False,'historical_reviews_changed':False,
        'broad_106_projected':False,'broad_614_projected':False,'603_projected':False,'616_projected':False,
        'source_coverage_establishes_semantic_closure':False,
    })
    components=own(binding['projection_components'])
    components.append({'name':'mana_classification_source_context','package_binding':'THIS_ENCLOSING_PACKAGE',
        'projection_id':p['projection_id'],'projected_references':list(SELECTED_REFERENCES)})
    new_bindings=[{'rule_reference':ref,'rule_id':rules[ref]['rule_id'],
        'anchor_identity':rules[ref]['source_anchor']['anchor_id'],'source_anchor':own(rules[ref]['source_anchor']),
        'projection_id':p['projection_id'],'package_binding':'THIS_ENCLOSING_PACKAGE'} for ref in SELECTED_REFERENCES]
    references=[ref for component in components for ref in component['projected_references']]
    if len(references)!=104 or len(set(references))!=104 or len(components)!=16:
        _fail('EXACT_FOUR_ADDITIONS_REQUIRED')
    coverage=_record('composite-coverage',{'projection_id':p['projection_id'],'findings':{
        'view_kind':'READ_ONLY_SIXTEEN_PROJECTION_COMPOSITE','previous_count':100,'new_count':4,
        'total_projected_rule_count':104,'previous_projection_count':15,'total_projection_count':16,
        'projected_references':references,'projection_components':components,
        'all_prior_rule_bindings':own(binding['rule_bindings']),'new_rule_bindings':new_bindings,
        'additional_rules_projected':[],'prior_rule_bindings_changed':False,
        'historical_interpretation_context_unit_count':17,'separately_enriched_context_unit_count':21,
        'historical_acquisition_identity':HISTORICAL_ACQUISITION_ID,
        'complete_local_106_12_family':True,'mana_subsystem_complete':False,
        'trigger_subsystem_complete':False,'replacement_subsystem_complete':False,
        'semantic_closure':'OPEN','all_ten_activation_responsibilities':'OPEN / EXECUTION_BLOCKED'}})
    return {'projection.json':p,'dependency-review.json':dependency,'composite-coverage.json':coverage}


def _manifest(records,binding):
    p=records['projection.json']
    return seal(PACKAGE_SCHEMA,{'schema_version':PACKAGE_SCHEMA,'canonical_base':CANONICAL_MAIN,
        'projection_id':p['projection_id'],'record_ids':{
            name:record['projection_id' if name=='projection.json' else 'review_id'] for name,record in sorted(records.items())},
        'files':{name:{'bytes':len(canonical(record,limit=RECORD_LIMIT)),
            'sha256':hashlib.sha256(canonical(record,limit=RECORD_LIMIT)).hexdigest()} for name,record in sorted(records.items())},
        'source_binding':own(p['source_binding']),'prior_package_id':binding['prior_package_id'],
        'historical_acquisition_identity':HISTORICAL_ACQUISITION_ID,
        'selected_references':list(SELECTED_REFERENCES),'selected_rule_count':4,
        'projected_rule_count_before':100,'new_source_units_projected':4,'projected_rule_count_after':104,
        'existing_projection_count_before':15,'existing_projection_count_after':16,
        'additional_rules_projected':[],'historical_anchors_changed':False,
        'historical_dependency_arrays_changed':False,'source_body_retained':False,
        'source_policy_clearance':'not_granted','permissions':{
            'private_retention':'NOT_ESTABLISHED','redistribution':'NOT_ESTABLISHED',
            'free_service':'NOT_ESTABLISHED','commercial_service':'NOT_ESTABLISHED','ai_export':'NOT_ESTABLISHED'},
        'offline_reproduction':'NOT_FRESH_SOURCE_VERIFICATION','semantic_closure':'OPEN',
        'all_ten_activation_responsibilities':'OPEN / EXECUTION_BLOCKED',
        'future_milestone_authorized':False,'future_source_projection_authorized':False,'future_milestone_begun':False,
        **authority()},'package_id')


def _complete(binding):
    records=_records(binding)
    return {**records,'manifest.json':_manifest(records,binding)}


def _validate(records,expected):
    snapshot=_snapshot(records)
    if canonical(snapshot)!=canonical(expected):
        _fail('EXACT_FIXED_PACKAGE_AND_ALL_PARENT_BINDINGS_REQUIRED')
    return snapshot


def rebuild_package(*, review_root):
    """Fresh offline integrity validation of current history; no source claim."""
    return ContextPackage._verified(_complete(validate_historical(review_root=review_root)))


def build_package(artifact_path, *, review_root):
    """Fresh source reproduction requires owner artifact and retained lineage."""
    verified_anchors(artifact_path,review_root=review_root)
    return rebuild_package(review_root=review_root)


def manifest(records, *, review_root=DEFAULT_REVIEW_ROOT):
    snapshot=_snapshot(records)
    expected=_complete(validate_historical(review_root=review_root))
    return ContextPackage._verified(_validate(snapshot,expected)['manifest.json'])


def write_package(root,records,*,review_root):
    snapshot=_snapshot(records)  # caller ownership ends before validation/use
    expected=_complete(validate_historical(review_root=review_root))
    _validate(snapshot,expected)
    root=Path(root)
    if any(path.is_symlink() for path in (root,*root.parents)):
        _fail('SYMLINK_DESTINATION_FORBIDDEN')
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        _fail('APPEND_ONLY_NEW_OR_EMPTY_DESTINATION_REQUIRED')
    root.mkdir(parents=True,exist_ok=True)
    for name,value in snapshot.items():
        with (root/name).open('xb') as stream:
            stream.write(canonical(value,limit=RECORD_LIMIT))
    return ContextPackage._verified(snapshot)


def load_package(root,*,review_root):
    root=_root(root)
    if {path.name for path in root.iterdir()}!=RECORD_NAMES|{'manifest.json'}:
        _fail('EXACT_FOUR_PACKAGE_FILES_REQUIRED')
    expected=_complete(validate_historical(review_root=review_root))
    # Exact canonical bytes reject duplicates, unknown fields, wrong scalar types,
    # coherent rehashes, stale bindings and all source prose substitutions.
    for name,value in expected.items():
        raw=_read(root/name)
        if len(raw)>RECORD_LIMIT or raw!=canonical(value,limit=RECORD_LIMIT):
            _fail('RETAINED_PACKAGE_CANONICAL_BYTES_DO_NOT_REPRODUCE')
    return ContextPackage._verified(expected)


def verify_source(records,artifact_path,*,review_root):
    snapshot=_snapshot(records)
    reproduced=build_package(artifact_path,review_root=review_root)
    _validate(snapshot,reproduced.to_dict())
    return ContextPackage._verified({'status':'VERIFIED_EXACT_FOUR_COMPLETE_SOURCE_BLOCKS',
        'selected_rule_count':4,'selected_references':list(SELECTED_REFERENCES),
        'package_id':snapshot['manifest.json']['package_id'],
        'projection_id':snapshot['projection.json']['projection_id'],
        'source_anchors':[r['source_anchor'] for r in snapshot['projection.json']['rules']],
        'outgoing_numbered_citations':snapshot['dependency-review.json']['literal_numbered_citations'],
        'source_body_retained':False,'fresh_source_verification':True})


def composite_view(records,*,review_root=DEFAULT_REVIEW_ROOT):
    snapshot=_snapshot(records)
    expected=_complete(validate_historical(review_root=review_root))
    snapshot=_validate(snapshot,expected)
    view=snapshot['composite-coverage.json']['findings']
    predecessor._resolve_package_bindings(view,snapshot['manifest.json']['package_id'])
    return ContextPackage._verified(view)
