"""Closed four-rule metadata contracts, immutable canonical bytes and own domains."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping

from gameplay_rules.errors import GameplayContractError
from .bounded_mana_contracts import SOURCE_BINDING, BOUNDARY_FLAGS
from .contracts import _json
from .mana_context_source import SELECTED_REFERENCES, VERIFIED_ANCHORS

CANONICAL_MAIN = '2accac9e5d108b0964b9b503d999dcb89888f6f6'
PACKAGE_SCHEMA = 'gameplay-mana-classification-source-context-package-v1'
PROJECTION_SCHEMA = 'gameplay-mana-classification-source-context-projection-v1'
RULE_DOMAIN = 'gameplay-mana-classification-source-context-rule-v1'
ANCHOR_DOMAIN = 'gameplay-mana-classification-source-context-anchor-v1'
RECORD_LIMIT = 524_288
PACKAGE_LIMIT = 1_048_576


def _fail(code):
    raise GameplayContractError('mana_context_contract', code)


def canonical(value, *, limit=PACKAGE_LIMIT):
    """Own plain strict JSON before semantic validation or subsequent use."""
    nodes = [0]
    def inspect(item,depth=0):
        nodes[0] += 1
        if depth > 24 or nodes[0] > 100_000:
            _fail('JSON_STRUCTURE_BOUND')
        if type(item) is dict:
            for key,child in item.items():
                if type(key) is not str or not key or len(key)>128:
                    _fail('EXACT_STRING_KEYS_REQUIRED')
                inspect(child,depth+1)
        elif type(item) is list:
            for child in item:
                inspect(child,depth+1)
        elif type(item) is str:
            if len(item)>16_384:
                _fail('STRING_BOUND')
        elif item is not None and type(item) not in (int,bool):
            _fail('STRICT_JSON_TYPES_REQUIRED')
        elif type(item) is int and not -(2**63)<=item<2**63:
            _fail('INTEGER_BOUND')
    inspect(value)
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
    if len(raw)>limit:
        _fail('JSON_BYTE_BOUND')
    return raw


def own(value, *, limit=PACKAGE_LIMIT):
    return json.loads(canonical(value,limit=limit))


def seal(domain,value,field):
    body=own(value)
    body.pop(field,None)
    return {**body,field:'sha256:'+hashlib.sha256(canonical({'domain':domain,'content':body})[:-1]).hexdigest()}


@dataclass(frozen=True, init=False)
class ContextPackage(Mapping):
    """Private canonical package; every exposed decoded value is independent."""
    _raw: bytes

    @classmethod
    def _verified(cls,value):
        result=object.__new__(cls)
        object.__setattr__(result,'_raw',canonical(value))
        return result

    def to_dict(self):
        return json.loads(self._raw)

    def to_json(self):
        return self._raw.decode()

    def __getitem__(self,key):
        return self.to_dict()[key]

    def __iter__(self):
        return iter(self.to_dict())

    def __len__(self):
        return len(self.to_dict())


def authority():
    return {'semantic_review_status':'PENDING_NOT_ESTABLISHED',
        'review':{'status':'requires_review','human_attestation':None,'canonical_admission':False},
        'execution_authority':'BLOCKED'}


def _rule_content():
    return {
        '106.12':{
            'knowledge_kind':'TAP_FOR_MANA_DEFINITION_CONTEXT',
            'described_action':'ACTIVATION_OF_PERMANENT_MANA_ABILITY',
            'activation_cost_requirement':'CONTAINS_TAP_SYMBOL',
            'literal_numbered_citations':['605'],
            'structural_parent':'106',
            'broader_106_projected':False,
        },
        '106.12a':{
            'knowledge_kind':'TAPPED_FOR_MANA_TRIGGER_CONTEXT',
            'trigger_wording_context':'PERMANENT_TAPPED_FOR_MANA_WITH_OPTIONAL_SPECIFIED_MANA_TYPE',
            'referent':'MANA_ABILITY_WITH_TAP_SYMBOL_COST_FROM_106_12',
            'relationship':'RESOLUTION_OF_REFERENT_ABILITY_AND_MANA_PRODUCTION',
            'specified_type_condition':'IF_TRIGGER_REQUIRES_TYPE_PRODUCTION_MUST_HAVE_THAT_TYPE',
            'literal_numbered_citations':[],
            'structural_parent':'106.12',
            'event_detection_implemented':False,
        },
        '106.12b':{
            'knowledge_kind':'TAPPED_FOR_MANA_REPLACEMENT_CONTEXT',
            'replacement_wording_context':'PERMANENT_TAPPED_FOR_MANA_WITH_OPTIONAL_SPECIFIED_TYPE_AND_OR_AMOUNT',
            'referent':'MANA_ABILITY_WITH_TAP_SYMBOL_COST_FROM_106_12',
            'modified_event':'MANA_PRODUCTION_DURING_REFERENT_ABILITY_RESOLUTION',
            'specified_constraints':'APPLICABLE_TYPE_AND_OR_AMOUNT_MUST_BE_PRODUCED',
            'literal_numbered_citations':[],
            'structural_parent':'106.12',
            'replacement_recognition_implemented':False,
        },
        '614.15':{
            'knowledge_kind':'SELF_REPLACEMENT_DEFINITION_AND_ORDERING_CONTEXT',
            'effect_category':'SOME_REPLACEMENTS_ARE_RESOLVING_SPELL_OR_ABILITY_EFFECTS_RATHER_THAN_CONTINUOUS_EFFECTS',
            'replacement_scope':'PART_OR_ALL_OF_RESOLVING_SPELL_OR_ABILITY_OWN_EFFECTS',
            'creation_text_context':{
                'usual_location':'ABILITY_WHOSE_EFFECT_IS_REPLACED',
                'separate_ability_possible':True,
                'separate_ability_emphasis':'ESPECIALLY_WITH_PRECEDING_ABILITY_WORD',
            },
            'ordering_knowledge':{
                'event_context':'APPLYING_REPLACEMENT_EFFECTS_TO_AN_EVENT',
                'self_replacements_precede_other_replacements':True,
                'ordering_execution_implemented':False,
            },
            'literal_numbered_citations':[],
            'structural_parent':'614',
            'broader_614_projected':False,
            'replacement_recognition_implemented':False,
        },
    }


def projection():
    content=_rule_content()
    rules=[]
    for raw in _json(VERIFIED_ANCHORS):
        anchor=seal(ANCHOR_DOMAIN,raw,'anchor_id')
        ref=anchor['rule_reference']
        rules.append(seal(RULE_DOMAIN,{'rule_reference':ref,'source_anchor':anchor,**content[ref]},'rule_id'))
    return seal(PROJECTION_SCHEMA,{
        'schema_version':PROJECTION_SCHEMA,'canonical_base':CANONICAL_MAIN,
        'projection_kind':'NON_EXECUTABLE','status':'PROJECTED_FOR_REVIEW',
        'selected_references':list(SELECTED_REFERENCES),'selected_rule_count':4,
        'new_source_units_projected':4,'total_projected_rule_count':104,'resulting_projection_count':16,
        'source_binding':_json(SOURCE_BINDING),'boundary_flags':_json(BOUNDARY_FLAGS),
        'source_anchor_policy':'EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR',
        'authorship':'STRUCTURED_PROJECT_AUTHORED_PARAPHRASE_BOUND_TO_VERIFIED_SOURCE',
        'rules':rules,'additional_rules_projected':[],
        'semantic_closure':'OPEN','all_ten_activation_responsibilities':'OPEN / EXECUTION_BLOCKED',
        'subsystem_completion':{'mana':False,'triggers':False,'replacements':False},**authority(),
    },'projection_id')
