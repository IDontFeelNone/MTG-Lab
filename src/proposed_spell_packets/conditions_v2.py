"""Bounded authored Boolean trees over complete fictional assertion groups.

The reviewed v1 group/comparison policy is reused; composition alone is v2.
No predicate prose is interpreted and no computed report is an evidence input.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from . import conditions as c
from . import validation as v
from .authoring import read_draft_bytes

MODEL_VERSION = 'fictional-condition-model-v2'
POLICY_VERSION = 'fictional-condition-evaluator-policy-v2'
RESULT_VERSION = 'fictional-condition-result-v2'
MODEL_AUTHORITY = c.MODEL_AUTHORITY
MAX_LEAVES = 32
MAX_CLAIM_REFS = 64
MAX_EXPRESSION_NODES = 128
MAX_EXPRESSION_DEPTH = 8
MODEL_BYTE_LIMIT = 64_000
RAW_DEPTH_LIMIT = 20
RAW_NODE_LIMIT = 8192
PACKET_FIELDS = c.PACKET_FIELDS
_binding = c._binding
_token = c._token
LIMITATIONS = (
    'Only this authored v2 fictional expression under supplied unverified assertions is computed.',
    'V2 composition is decisive between children: ALL_OF with a determinate MISMATCH is MISMATCH; ANY_OF with a determinate MATCH is MATCH. Otherwise unresolved children keep the node unresolved. V1 unresolved-first flat ALL_OF is unchanged.',
    'Each complete leaf group retains the v1 unresolved-first evidence policy, including its independent known mismatches. Predicate strings remain opaque.',
    'A determined root does not establish complete evidence. Unresolved branches remain unresolved within this question and are not universally irrelevant, resolved, false or unnecessary.',
    *c.LIMITATIONS[:2],
    *c.LIMITATIONS[3:],
    'No real Card semantics, actual effect consequence, complete applicable-effect inventory, feasible choice, compatibility, casting permission, legality, payment or completion is established.',
)


def _policy_bytes():
    body = {
        'policy_version': POLICY_VERSION,
        'authority': 'BOUNDED_FICTIONAL_EXPRESSION_COMPOSITION_POLICY_ONLY',
        'leaf_policy': 'REVIEWED_V1_COMPLETE_GROUP_UNRESOLVED_FIRST_WITH_INDEPENDENT_MISMATCHES',
        'all_of': {'decisive_child': 'MISMATCH', 'otherwise_unresolved_child': 'UNRESOLVED', 'otherwise': 'MATCH'},
        'any_of': {'decisive_child': 'MATCH', 'otherwise_unresolved_child': 'UNRESOLVED', 'otherwise': 'MISMATCH'},
        'validation': 'ALL_BRANCHES_AND_COMPLETE_GROUPS_BEFORE_CALCULATION',
        'evaluation': 'EVERY_LEAF_AND_NODE_WITHOUT_SHORT_CIRCUIT',
        'execution_authority': 'BLOCKED',
    }
    body['policy_id'] = v.identity(POLICY_VERSION, body, 'policy_id')
    return v._canonical_candidate(body)


POLICY_BYTES = _policy_bytes()
POLICY_ID = json.loads(POLICY_BYTES)['policy_id']


def policy():
    """An independent view of the finite built-in algorithm identity."""
    return json.loads(POLICY_BYTES)


def _error(message):
    v.fail('CONDITION_V2_' + message)


def _owned(value, *, byte_limit=MODEL_BYTE_LIMIT, node_limit=RAW_NODE_LIMIT):
    """Exact bounded JSON types before serialization; depth is not tree depth."""
    budget = [0]
    def inspect(node, depth):
        budget[0] += 1
        if budget[0] > node_limit or depth > RAW_DEPTH_LIMIT:
            _error('JSON_STRUCTURE_LIMIT')
        if type(node) is dict:
            for key, child in node.items():
                if type(key) is not str or len(key) > 128:
                    _error('BOUNDED_STRING_KEYS_REQUIRED')
                inspect(child, depth + 1)
        elif type(node) is list:
            for child in node:
                inspect(child, depth + 1)
        elif type(node) is str:
            if len(node) > 4096:
                _error('STRING_LIMIT')
        elif node is not None and type(node) not in (bool, int):
            _error('JSON_SCALARS_REQUIRED')
    inspect(value, 0)
    raw = v._canonical_candidate(value)
    if len(raw) > byte_limit:
        _error('BYTE_LIMIT')
    return json.loads(raw)


def _leaf_adapter(definition):
    """Private structural adapter into reviewed packet/group validation helpers.

    This is never accepted as a v1 payload or exposed as a model/result identity.
    """
    return {**{key: definition[key] for key in ('packet', 'scope')},
        'operands': [{'operand_id': row['leaf_id'], 'claim_refs': row['claim_refs'],
                      'expected': row['expected']} for row in definition['leaves']]}


def _validate_expression(expression, ids):
    referenced, count = set(), [0]
    def visit(node, depth):
        count[0] += 1
        if count[0] > MAX_EXPRESSION_NODES or depth > MAX_EXPRESSION_DEPTH:
            _error('EXPRESSION_LIMIT')
        if type(node) is not dict:
            _error('EXPRESSION_OBJECT_REQUIRED')
        if set(node) == {'leaf_id'}:
            c._token(node['leaf_id'], 'LEAF_REFERENCE')
            if node['leaf_id'] not in ids:
                _error('DANGLING_LEAF_REFERENCE')
            referenced.add(node['leaf_id'])
        else:
            c._object(node, ('operator', 'children'), 'EXPRESSION_NODE')
            if type(node['operator']) is not str or node['operator'] not in ('ALL_OF', 'ANY_OF'):
                _error('UNSUPPORTED_OPERATOR')
            children = node['children']
            if type(children) is not list or not 1 <= len(children) <= 32:
                _error('NONEMPTY_BOUNDED_CHILDREN_REQUIRED')
            for child in children:
                visit(child, depth + 1)
    visit(expression, 1)
    if referenced != ids:
        _error('EVERY_DECLARED_LEAF_MUST_BE_REFERENCED')


def _validate(value):
    c._object(value, ('model_id', 'model_version', 'authority', 'condition_id',
                     'condition_name', 'packet', 'scope', 'leaves', 'expression'), 'V2_MODEL')
    if value['model_version'] != MODEL_VERSION or value['authority'] != MODEL_AUTHORITY:
        _error('MODEL_VERSION_OR_AUTHORITY_MISMATCH')
    leaves = value['leaves']
    if type(leaves) is not list or not 1 <= len(leaves) <= MAX_LEAVES:
        _error('NONEMPTY_BOUNDED_LEAVES_REQUIRED')
    for leaf in leaves:
        c._object(leaf, ('leaf_id', 'claim_refs', 'expected'), 'LEAF')
    # Reuse strict v1 scalar, packet, scope and Boolean binding validation only.
    # The flat validation envelope is private; v2 identity and tree are independent.
    adapter = _leaf_adapter(value)
    c.seal_model({**adapter, 'model_version': c.MODEL_VERSION,
        'authority': c.MODEL_AUTHORITY, 'condition_id': value['condition_id'],
        'condition_name': value['condition_name'], 'operator': 'ALL_OF'})
    _validate_expression(value['expression'], {row['leaf_id'] for row in leaves})
    if type(value['model_id']) is not str or not c.IDENTITY.fullmatch(value['model_id']):
        _error('MODEL_IDENTITY_REQUIRED')
    v.check_identity(value, MODEL_VERSION, 'model_id')


@dataclass(frozen=True, init=False)
class ConditionModel:
    canonical_bytes: bytes

    def __init__(self, value):
        owned = _owned(value)
        _validate(owned)
        object.__setattr__(self, 'canonical_bytes', v._canonical_candidate(owned))

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def model_id(self):
        return self.to_dict()['model_id']


def seal_model(value):
    owned = _owned(value)
    if type(owned) is not dict or 'model_id' in owned:
        _error('UNSEALED_MODEL_REQUIRED')
    owned['model_id'] = v.identity(MODEL_VERSION, owned, 'model_id')
    return ConditionModel(owned).to_dict()


def read_model(path):
    raw = read_draft_bytes(path)
    if len(raw) > MODEL_BYTE_LIMIT:
        _error('BYTE_LIMIT')
    try:
        value = json.loads(raw, object_pairs_hook=v._unique, parse_constant=v._nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        _error('MALFORMED_MODEL_JSON')
    return ConditionModel(value)


@dataclass(frozen=True, init=False)
class ConditionResult:
    """Computed output only; imported results cannot be trusted evidence."""
    canonical_bytes: bytes

    def __init__(self, *args, **kwargs):
        _error('RESULT_IS_COMPUTED_OUTPUT_ONLY')

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def result_id(self):
        return self.to_dict()['result_id']


def _groups(packet, definition):
    return c._groups(packet, _leaf_adapter(definition))


def _prepare(workspace, packet_id, model):
    definition = ConditionModel(model.to_dict() if type(model) is ConditionModel else model).to_dict()
    packet, history = workspace.read(packet_id)
    packet, history = v.snapshot(packet), v.snapshot(history)
    if packet['packet_id'] != packet_id:
        _error('SELECTED_PACKET_IDENTITY_MISMATCH')
    v.check_identity(packet, v.PACKET_DOMAIN, 'packet_id')
    context, groups = _groups(packet, definition)
    return packet, history, definition, context, groups


def _compose(operator, statuses):
    """Normative v2 table, used at every compound expression node."""
    decisive = 'MISMATCH' if operator == 'ALL_OF' else 'MATCH'
    neutral = 'MATCH' if operator == 'ALL_OF' else 'MISMATCH'
    return decisive if decisive in statuses else 'UNRESOLVED' if 'UNRESOLVED' in statuses else neutral


def _calculate(groups, expression, assumptions=None):
    leaves = []
    for operand, rows in groups:
        overrides = None if assumptions is None else {
            ref: value for ref, value in assumptions.items() if ref in operand['claim_refs']}
        leaf = c._operand(operand, rows, overrides)
        leaf['leaf_id'] = leaf.pop('operand_id')
        leaves.append(leaf)
    by_id = {row['leaf_id']: row['status'] for row in leaves}
    nodes = []
    def visit(node, path, parent):
        row = {'path': path, 'parent_path': parent, 'policy_version': POLICY_VERSION}
        nodes.append(row)
        if 'leaf_id' in node:
            row.update(leaf_id=node['leaf_id'], children=[], child_outcomes=[],
                status=by_id[node['leaf_id']], determining_child_paths=[],
                explanation='Complete assertion group outcome; repeated references share this one leaf calculation.')
        else:
            paths = [path + '/' + str(i) for i in range(len(node['children']))]
            statuses = [visit(child, child_path, path) for child, child_path in zip(node['children'], paths)]
            status = _compose(node['operator'], statuses)
            decisive = 'MISMATCH' if node['operator'] == 'ALL_OF' else 'MATCH'
            determining = ([p for p, s in zip(paths, statuses) if s == decisive]
                if status == decisive else [p for p, s in zip(paths, statuses) if s == 'UNRESOLVED']
                if status == 'UNRESOLVED' else paths)
            row.update(operator=node['operator'], children=paths,
                child_outcomes=[{'path': p, 'status': s} for p, s in zip(paths, statuses)],
                status=status, determining_child_paths=determining,
                explanation=('Determinate ' + decisive + ' child determines this node under v2 composition.'
                    if status == decisive else 'No decisive child; unresolved children keep this node unresolved.'
                    if status == 'UNRESOLVED' else 'Every child has the operator neutral outcome.'))
        return row['status']
    root = visit(expression, 'root', None)
    computed = {'MATCH': 'SATISFIED_UNDER_ASSERTIONS', 'MISMATCH': 'NOT_SATISFIED_UNDER_ASSERTIONS',
                'UNRESOLVED': 'INDETERMINATE'}[root]
    return leaves, nodes, computed


def _evaluate_snapshot(packet, history, definition, context, groups):
    leaves, nodes, computed = _calculate(groups, definition['expression'])
    selected = {ref for row in leaves for ref in row['claim_refs']}
    value = {'result_version': RESULT_VERSION, 'evaluator_policy_version': POLICY_VERSION,
        'evaluator_policy_id': POLICY_ID, 'evaluator_policy': policy(),
        'model_version': MODEL_VERSION, 'authority': 'NAMED_FICTIONAL_CONDITION_UNDER_ASSERTIONS_ONLY',
        'execution_authority': 'BLOCKED', 'packet': _binding(packet),
        'model_id': definition['model_id'], 'condition_model': definition,
        'condition_id': definition['condition_id'], 'condition_name': definition['condition_name'],
        'scope': definition['scope'], 'context': context, 'leaves': leaves,
        'expression_nodes': nodes, 'selected_input_findings': [
            {'leaf_id': row['leaf_id'], **finding} for row in leaves for finding in row['findings']],
        'computed_result': computed, 'explanation_trace': nodes,
        'limitations': list(LIMITATIONS),
        'retained_rule_context_authority': 'RETAINED_VERSIONED_RULE_CONTEXT_ONLY',
        'retained_rule_context': packet['rule_evidence'],
        'packet_context': {'authored_conclusion': packet['conclusion'],
            'authored_limitations': packet['limitations'],
            'unselected_claims': [row for row in packet['claims'] if row['claim_id'] not in selected],
            'authored_reasoning': packet['reasoning'], 'authored_choices': packet['choices'],
            'history': packet['history'], 'validated_ancestor_ids': sorted(history),
            'review_authority': 'AUTHORED_PACKET_OBSERVATIONS_DO_NOT_APPROVE_CONDITION_MODEL'}}
    value['result_id'] = v.identity(RESULT_VERSION, value, 'result_id')
    result = object.__new__(ConditionResult)
    object.__setattr__(result, 'canonical_bytes', v._canonical_candidate(value))
    return result


def evaluate(workspace, packet_id, model):
    return _evaluate_snapshot(*_prepare(workspace, packet_id, model))


def _render_value(value):
    lines = ['Computed condition result: ' + value['computed_result'],
        'Condition: ' + value['condition_id'] + ' | ' + value['condition_name'],
        'Model: ' + value['model_id'], 'Result: ' + value['result_id'],
        'Evaluator policy: ' + value['evaluator_policy_version'] + ' | ' + value['evaluator_policy_id']]
    lines.extend('Leaf: ' + json.dumps(row, ensure_ascii=False, sort_keys=True) for row in value['leaves'])
    lines.extend('Expression node: ' + json.dumps(row, sort_keys=True) for row in value['expression_nodes'])
    lines.append('Authored context (separate): ' + json.dumps(value['packet_context'], ensure_ascii=False, sort_keys=True))
    lines.extend('Limitation: ' + text for text in value['limitations'])
    lines.append('Execution authority: BLOCKED')
    return '\n'.join(lines)


def render(result):
    return _render_value(result.to_dict())
