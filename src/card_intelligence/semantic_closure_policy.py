"""Pure bounded requirement evaluation. This function never admits evidence.

Production assessment supplies premises only through its owning validated adapter.
Synthetic graphs exercise this policy, not additional real-Card interpretations.
"""
import json
from types import MappingProxyType
from card_rules_pilot import contract as c

VERSION = 'real-card-semantic-closure-policy-v1'
REQUIREMENT_VERSION = 'real-card-semantic-closure-requirement-v1'
GRAPH_VERSION = 'semantic-closure-requirement-graph-v1'
LIMIT = 65536
DIMENSIONS = ('identity', 'text', 'rules', 'semantics', 'procedure', 'permissions', 'authorization')
LEVELS = ('validated_binding', 'retained_source', 'reviewed_source', 'accepted_interpretation',
          'reviewed_real_procedure', 'permission', 'execution_authorization')
PRECEDENCE = ('BLOCKED', 'UNSUPPORTED', 'MISSING', 'UNKNOWN', 'SATISFIED')
MEANINGS = MappingProxyType({
    'SATISFIED': 'The particular requirement has established evidence at its required authority level; not overall execution readiness.',
    'MISSING': 'Required evidence or a reviewed procedure is absent from the admitted assessment scope.',
    'UNKNOWN': 'Truth, freshness, applicability or sufficient authority is not established.',
    'UNSUPPORTED': 'The condition lies outside the supported interpretation/procedure scope.',
    'BLOCKED': 'An explicit authority restriction, contradictory premises or blocked dependency prevents stronger use.',
})


class ClosureError(c.PilotError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(code + ': ' + message)


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ClosureError('INVALID_CONTRACT', 'exact closed fields required')


def _text(value):
    if type(value) is not str or not value or len(value) > 2048:
        raise ClosureError('INVALID_CONTRACT', 'bounded nonempty string required')


def _strings(value):
    if type(value) is not list or len(value) > 64:
        raise ClosureError('INVALID_CONTRACT', 'bounded string list required')
    for item in value: _text(item)
    if value != sorted(set(value)):
        raise ClosureError('INVALID_CONTRACT', 'sorted unique references required')


def evaluate(requirements, premises, evidence):
    """Evaluate independent local findings plus dependency effects, without authority.

    Missing input is not false evidence. Source presence cannot satisfy a stronger
    review level. Even an all-satisfied synthetic graph confers no execution right.
    """
    owned = json.loads(c.owned(dict(requirements=requirements, premises=premises, evidence=evidence), limit=LIMIT))
    requirements, premises, evidence = (owned[k] for k in ('requirements','premises','evidence'))
    if any(type(v) is not list or len(v) > 64 for v in (requirements, premises)) or not requirements:
        raise ClosureError('INVALID_CONTRACT', 'one to 64 requirements and at most 64 premises required')
    if type(evidence) is not dict or len(evidence) > 64:
        raise ClosureError('INVALID_CONTRACT', 'bounded evidence-reference map required')
    for key, ref in evidence.items():
        _text(key); _keys(ref, ('identity', 'pointer', 'scope'))
        for value in ref.values(): _text(value)
        identity = ref['identity']
        if len(identity) != 71 or not identity.startswith('sha256:') or any(x not in '0123456789abcdef' for x in identity[7:]):
            raise ClosureError('INVALID_EVIDENCE', 'domain-separated content identity required')
        if not ref['pointer'].startswith('/'):
            raise ClosureError('INVALID_EVIDENCE', 'explicit JSON evidence pointer required')
    facts = {}
    for fact in premises:
        _keys(fact, ('key', 'state', 'level', 'evidence_refs'))
        _text(fact['key']); _strings(fact['evidence_refs'])
        if fact['key'] in facts or fact['level'] not in LEVELS or fact['state'] not in (
                'ESTABLISHED', 'ABSENT', 'UNKNOWN', 'UNSUPPORTED', 'PROHIBITED', 'CONFLICTING'):
            raise ClosureError('INVALID_PREMISE', 'duplicate, foreign state or authority level')
        if set(fact['evidence_refs']) - set(evidence):
            raise ClosureError('INVALID_EVIDENCE', 'unbound or invented evidence reference')
        if fact['state'] == 'ESTABLISHED' and not fact['evidence_refs']:
            raise ClosureError('INVALID_EVIDENCE', 'established finding requires identifiable evidence')
        facts[fact['key']] = fact
    definitions = {}
    for row in requirements:
        _keys(row, ('key', 'dimension', 'question', 'why', 'needed', 'premise', 'required_level', 'dependencies'))
        for key in ('key', 'question', 'why', 'needed', 'premise'): _text(row[key])
        _strings(row['dependencies'])
        if row['key'] in definitions or row['dimension'] not in DIMENSIONS or row['required_level'] not in LEVELS:
            raise ClosureError('INVALID_REQUIREMENT', 'duplicate or unsupported requirement')
        definitions[row['key']] = row
    if any(set(r['dependencies']) - set(definitions) for r in requirements):
        raise ClosureError('INVALID_REQUIREMENT', 'missing dependency definition')
    computed, visiting = {}, set()
    def visit(key):
        if key in computed: return computed[key]
        if key in visiting: raise ClosureError('INVALID_REQUIREMENT', 'cyclic requirement graph')
        visiting.add(key); row = definitions[key]; fact = facts.get(row['premise'])
        local, reason = 'MISSING', 'NO_PREMISE'
        if fact:
            local = dict(ESTABLISHED='SATISFIED', ABSENT='MISSING', UNKNOWN='UNKNOWN',
                         UNSUPPORTED='UNSUPPORTED', PROHIBITED='BLOCKED', CONFLICTING='BLOCKED')[fact['state']]
            reason = fact['state']
            if local == 'SATISFIED' and fact['level'] != row['required_level']:
                local, reason = 'UNKNOWN', 'INSUFFICIENT_AUTHORITY_LEVEL'
        deps = [visit(k) for k in row['dependencies']]
        status = next(s for s in PRECEDENCE if s in [local, *(d['status'] for d in deps)])
        result = dict(**row, requirement_id=c.identity(REQUIREMENT_VERSION, row, 'requirement_id'),
                      local_status=local, status=status, reason=reason,
                      evidence_refs=[] if fact is None else fact['evidence_refs'],
                      unresolved_dependencies=[d['key'] for d in deps if d['status'] != 'SATISFIED'])
        visiting.remove(key); computed[key] = result
        return result
    rows = [visit(k) for k in sorted(definitions)]
    graph = c.seal(GRAPH_VERSION, dict(schema_version=GRAPH_VERSION,
        requirements=[definitions[k] for k in sorted(definitions)]), 'graph_id')
    return dict(graph_id=graph['graph_id'], requirements=rows,
        status=next(s for s in PRECEDENCE if s in [r['status'] for r in rows]),
        authority='PURE_REQUIREMENT_EVALUATION_NOT_EVIDENCE_ADMISSION', execution_authority='BLOCKED')


def requirements():
    """Reusable activation-closure questions; no Card labels or IDs are consulted."""
    rows = []
    def add(key, dim, level, question, why, needed, dependencies=()):
        rows.append(dict(key=key, dimension=dim, question=question, why=why, needed=needed,
                         premise=key, required_level=level, dependencies=sorted(dependencies)))
    add('identity.historical', 'identity', 'validated_binding', 'Exact historical identity correspondence?',
        'A Card, Printing and provider observation are separate identities.', 'Admitted exact namespace/Card/Printing/observation joins.')
    add('identity.identifier', 'identity', 'validated_binding', 'Promoted provider identifier edge?',
        'A historical observation alone does not establish the current promoted edge.', 'Exact promoted identifier-edge evidence.')
    add('identity.operator', 'identity', 'validated_binding', 'Operator-production identity established?',
        'Legacy evidence does not promote production identity.', 'Separately admitted operator snapshot and exact Card binding.')
    add('text.historical', 'text', 'retained_source', 'Exact retained text and observation provenance?',
        'Interpretation must bind exact historical bytes.', 'Source field identity, passage boundaries and observation dates.')
    add('text.accepted', 'text', 'accepted_interpretation', 'Owner-accepted interpretation of those bytes?',
        'Integrity alone supplies no semantic acceptance.', 'Exact candidate membership and bounded owner decision.', ('text.historical',))
    add('text.current', 'text', 'reviewed_source', 'Current Oracle text verified?',
        'Historical acceptance and identifier promotion are not freshness verification.', 'Independently verified current text/version and identity correspondence.')
    add('rules.retained', 'rules', 'retained_source', 'Selected supporting rule identities retained?',
        'Claims require exact rule/projection/source bindings.', 'Owning-context admission for every cited rule identity.')
    add('rules.reviewed', 'rules', 'reviewed_source', 'Bounded dependency reviews retained?',
        'Retained projection and reviewed source correspondence are distinct.', 'Exact append-only review records and their limited scopes.', ('rules.retained',))
    add('rules.execution_review', 'rules', 'reviewed_real_procedure', 'Applicable rules approved as executable semantics?',
        'A source/dependency review does not approve an execution primitive.', 'Separately reviewed applicable real-rule semantics and exception coverage.')
    add('rules.dependencies', 'rules', 'reviewed_real_procedure', 'Applicable retained dependency frontiers closed?',
        'An unresolved literal dependency cannot be replaced by a fictional procedure.', 'Reviewed support for applicable unresolved references, with unknown applicability retained.')
    add('semantics.conditional', 'semantics', 'accepted_interpretation', 'Accepted conditional capability and ownership?',
        'Classification and written output do not imply present usability.', 'Admitted classification, behavior, cost and ownership calculations.', ('text.accepted', 'rules.reviewed'))
    add('semantics.executable', 'semantics', 'reviewed_real_procedure', 'Canonical executable Card semantics admitted?',
        'Accepted descriptive readings are not CardGameplaySemantics.', 'Reviewed real semantics binding identity, rules, effects and unsupported contexts.')
    procedure_questions = (
        ('activation', 'Activation authority and exact ability identity', 'Controller, source state and applicable permission/restriction evidence.'),
        ('timing', 'Priority and mana-access timing', 'Reviewed priority and payment-window procedures; pre-activation priority when relevant.'),
        ('cost', 'Actual tap and other cost payment', 'Reviewed cost meaning, payable resources, atomic payment and source changes.'),
        ('output', 'Actual mana-production semantics', 'Reviewed output quantity, colorless identity, pool update and applicable restrictions.'),
        ('resolution', 'Mana-exception procedure and completion', 'Reviewed real no-stack/immediate-resolution and conditional priority-return implementation.'),
        ('checkpoint', 'Applicable mandatory state checks', 'Reviewed applicable real state-based checks before the next priority boundary.'),
        ('recovery', 'Illegal-action handling and rollback', 'Applicable reviewed real recovery dependencies, reversibility and deterministic proof vectors.'),
    )
    for key, question, needed in procedure_questions:
        add('procedure.'+key, 'procedure', 'reviewed_real_procedure', question+'?',
            'Fictional implementation or retained rule coverage is not approved real execution.', needed)
    add('procedure.external', 'procedure', 'reviewed_real_procedure', 'Changed text, gained abilities or external interactions?',
        'The retained subject excludes arbitrary modified game states.', 'Separately reviewed applicable effect/interaction semantics or an explicit bounded exclusion.')
    add('permissions.use', 'permissions', 'permission', 'Source-use rights established for proposed execution?',
        'Public accessibility, checksums and semantic review grant no use permission.', 'Operation-specific processing/retention/publication/service/AI-use clearance.')
    add('authorization.closure', 'authorization', 'execution_authorization', 'Real semantic closure established?',
        'Enumerated graph closure is not complete applicable semantics.', 'Reviewed closure and exception coverage for the proposed bounded real profile.')
    add('authorization.profile', 'authorization', 'execution_authorization', 'Real execution profile authorized?',
        'Fictional profiles cannot authorize real Card execution.', 'Separate explicit real-profile admission and owner activation authorization.')
    return sorted(rows, key=lambda r:r['key'])


_POLICY = c.seal(VERSION, dict(schema_version=VERSION, status_meanings=dict(MEANINGS),
    precedence=list(PRECEDENCE), levels=list(LEVELS), dimensions=list(DIMENSIONS),
    requirements=requirements(), limits=dict(requirements=64,premises=64,evidence=64,bytes=LIMIT),
    execution_authority='BLOCKED', scope='NON_EXECUTING_REQUIREMENTS_ONLY'), 'policy_id')
POLICY_ID = _POLICY['policy_id']


def policy_document():
    return c.ReviewDocument._verified(_POLICY, limit=LIMIT)
