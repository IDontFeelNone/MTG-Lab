"""Exact hypothetical target access with distinct-copy resource assignment.

Stream multivariate hypergeometric count vectors, then decide a matching once
per vector. No Card facts, game procedures, storage or experimental imports.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import comb

from .draw_access import canonical_json

INPUT_VERSION = 'declared-resource-assignment-input-v1'
REPORT_VERSION = 'declared-resource-assignment-report-v1'
METHOD = 'weighted-count-vectors-distinct-matching-v1'
MAX_INPUT_BYTES = 8192
MAX_REPORT_BYTES = 16384
MAX_POPULATION = 120
MAX_OBSERVED = 20
MAX_CLASSES = 5
MAX_KINDS = 2
MAX_DEMAND = 3
MAX_TARGET = 4
MAX_VECTORS = 10000
MAX_WORK = 5000000
ASSUMPTIONS = {
    'sampling': 'uniform-without-replacement',
    'availability': 'all-observed-resources-simultaneously-available',
    'output': 'one-unit-per-physical-copy',
    'identity_authority': 'CALLER_DECLARED',
}
LIMITATIONS = (
    'Hypothetical joint access and assignment only; declared capabilities are not verified Card facts.',
    'Observed resources are assumed statically available, not inferred from cumulative game draws.',
    'Flexible resources offer alternatives; each physical copy satisfies at most one simultaneous job.',
    'Observe-mode targets may serve resource jobs; reserve-mode target jobs require separate physical copies.',
    'No actual mana, casting legality, turn rules, gameplay, combo success, win rate or strategic ranking is established.',
)


class ResourceAssignmentError(ValueError):
    """A complete structured refusal, never a partial probability or zero."""
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', code=self.code,
                    reason=str(self), real_gameplay_authorized=False)


def _require(condition, reason, code='INVALID_INPUT'):
    if not condition:
        raise ResourceAssignmentError(code, reason)


def _fields(value, names):
    _require(type(value) is dict and value.keys() == set(names), 'closed object fields required')


def _integer(value, maximum, label, minimum=0):
    _require(type(value) is int and value >= minimum, 'invalid ' + label)
    _require(value <= maximum, label + ' exceeds V1 bound', 'UNSUPPORTED_SCOPE')


def _text(value, label):
    _require(type(value) is str and 0 < len(value) <= 64 and value == value.strip()
             and value.isprintable(), 'invalid ' + label)


def validate_resource_assignment(request):
    """Validate closed V1 declarations and return independently owned normal form.

    Classes must already be equivalent by (resource set, target membership).
    Neither omitted filler copies nor duplicate equivalent rows are invented.
    """
    _fields(request, ('schema_version', 'population_id', 'complete', 'population_size',
                      'cards_seen', 'resource_kinds', 'demands', 'target', 'classes', 'assumptions'))
    _require(type(request['schema_version']) is str and request['schema_version'] == INPUT_VERSION,
             'unsupported input version', 'UNSUPPORTED_SCOPE')
    _text(request['population_id'], 'population_id')
    _require(request['complete'] is True, 'explicit complete population required')
    size, seen = request['population_size'], request['cards_seen']
    _integer(size, MAX_POPULATION, 'population_size', 1)
    _integer(seen, MAX_OBSERVED, 'cards_seen')
    _require(seen <= size, 'sample exceeds population')
    _fields(request['assumptions'], ASSUMPTIONS)
    _require(all(type(request['assumptions'][k]) is str and request['assumptions'][k] == v
                 for k, v in ASSUMPTIONS.items()), 'unsupported analytical assumptions', 'UNSUPPORTED_SCOPE')
    kinds = request['resource_kinds']
    _require(type(kinds) is list, 'resource_kinds must be a list')
    _require(len(kinds) <= MAX_KINDS, 'at most two resource kinds', 'UNSUPPORTED_SCOPE')
    for kind in kinds:
        _text(kind, 'resource kind')
    _require(len(set(kinds)) == len(kinds), 'duplicate resource kinds')
    kinds = sorted(kinds)
    _fields(request['demands'], kinds)
    demands = {}
    for kind in kinds:
        _integer(request['demands'][kind], MAX_DEMAND, 'resource demand')
        demands[kind] = request['demands'][kind]
    target = request['target']
    _fields(target, ('minimum', 'mode'))
    _integer(target['minimum'], MAX_TARGET, 'target minimum')
    _require(type(target['mode']) is str and target['mode'] in ('observe', 'reserve'),
             'unsupported target mode', 'UNSUPPORTED_SCOPE')
    raw_classes = request['classes']
    _require(type(raw_classes) is list and len(raw_classes) > 0, 'nonempty classes required')
    _require(len(raw_classes) <= MAX_CLASSES, 'at most five equivalence classes', 'UNSUPPORTED_SCOPE')
    classes, keys = [], set()
    for row in raw_classes:
        _fields(row, ('copies', 'resources', 'target'))
        _integer(row['copies'], MAX_POPULATION, 'class copies')
        _require(type(row['target']) is bool, 'target membership must be Boolean')
        resources = row['resources']
        _require(type(resources) is list and len(resources) <= MAX_KINDS, 'bounded resource memberships required')
        for resource in resources:
            _text(resource, 'resource membership')
            _require(resource in kinds, 'undeclared resource membership')
        _require(len(set(resources)) == len(resources), 'duplicate resource membership')
        resources = sorted(resources)
        key = (tuple(resources), row['target'])
        _require(key not in keys, 'duplicate equivalence class; aggregate explicitly')
        keys.add(key)
        classes.append(dict(copies=row['copies'], resources=resources, target=row['target']))
    _require(sum(row['copies'] for row in classes) == size, 'class totals must equal complete population_size')
    normalized = dict(schema_version=INPUT_VERSION, population_id=request['population_id'],
                      complete=True, population_size=size, cards_seen=seen,
                      resource_kinds=kinds, demands=demands, target=dict(target),
                      classes=sorted(classes, key=lambda row: (row['resources'], row['target'])),
                      assumptions=dict(ASSUMPTIONS))
    _require(len(canonical_json(normalized).encode()) <= MAX_INPUT_BYTES, 'input byte bound exceeded')
    return normalized


def parse_resource_assignment(raw):
    """Strict bounded UTF-8 JSON, rejecting duplicate keys and nonfinite numbers."""
    _require(type(raw) in (str, bytes) and len(raw) <= MAX_INPUT_BYTES, 'bounded JSON bytes or text required')
    try:
        encoded = raw.encode('utf-8') if type(raw) is str else raw
        _require(len(encoded) <= MAX_INPUT_BYTES, 'input byte bound exceeded')

        def unique(pairs):
            value = {}
            for key, item in pairs:
                _require(key not in value, 'duplicate JSON key')
                value[key] = item
            return value

        def nonfinite(_):
            raise ResourceAssignmentError('INVALID_INPUT', 'nonfinite JSON number')

        value = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError):
        raise ResourceAssignmentError('INVALID_INPUT', 'invalid bounded UTF-8 JSON') from None
    return validate_resource_assignment(value)


def _vector_count(rows, seen):
    # At most 5 * 21 * 21 integer additions; no physical-hand enumeration.
    counts = [1] + [0] * seen
    for row in rows:
        counts = [sum(counts[drawn - k] for k in range(min(row['copies'], drawn) + 1))
                  for drawn in range(seen + 1)]
    return counts[seen]


def _matching(masks, demands):
    """Augmenting paths; one source position holds at most one job."""
    jobs = [kind for kind, demand in enumerate(demands) for _ in range(demand)]
    if len(jobs) > len(masks):
        return False
    occupied = [-1] * len(masks)

    def augment(job, visited):
        for source, mask in enumerate(masks):
            if source not in visited and mask & (1 << jobs[job]):
                visited.add(source)
                if occupied[source] == -1 or augment(occupied[source], visited):
                    occupied[source] = job
                    return True
        return False

    return all(augment(job, set()) for job in range(len(jobs)))


def _fraction(value):
    # Exact round-half-even with integers, independent of ambient Decimal context.
    scale = 10 ** 12
    q, r = divmod(value.numerator * scale, value.denominator)
    if 2 * r > value.denominator or (2 * r == value.denominator and q % 2):
        q += 1
    return dict(numerator=str(value.numerator), denominator=str(value.denominator),
                decimal=str(q // scale) + '.' + str(q % scale).zfill(12),
                decimal_places=12, rounding='ROUND_HALF_EVEN',
                nonzero=value > 0)


def _identity(domain, value):
    return 'sha256:' + sha256(domain.encode() + b'\0' + canonical_json(value).encode()).hexdigest()


def assess_resource_assignment(request):
    """Return an exact joint-access report or raise ResourceAssignmentError.

    Target minimum zero and zero demands are valid vacuous requirements. An
    impossible event remains a calculated zero. Static scope and deterministic
    budgets apply even to an event that could be short-circuited as impossible.
    """
    normalized = validate_resource_assignment(request)
    rows, seen = normalized['classes'], normalized['cards_seen']
    kinds = normalized['resource_kinds']
    demands = [normalized['demands'][kind] for kind in kinds]
    target_minimum, mode = normalized['target']['minimum'], normalized['target']['mode']
    masks = [sum(1 << kinds.index(kind) for kind in row['resources']) for row in rows]
    if mode == 'reserve':
        masks = [mask | ((1 << len(kinds)) if row['target'] else 0) for row, mask in zip(rows, masks)]
        demands.append(target_minimum)
    job_count = sum(demands)
    vectors = _vector_count(rows, seen)
    # Each augment may revisit at most D jobs, scanning H sources per job.
    # Add traversal/weight bookkeeping (<= 2*C per complete vector).
    work = vectors * (2 * len(rows) + max(1, job_count) ** 2 * max(1, seen))
    _require(vectors <= MAX_VECTORS and work <= MAX_WORK,
             'exact vector or matching work bound exceeded', 'RESOURCE_BUDGET_REFUSAL')
    suffix = [0] * (len(rows) + 1)
    for i in range(len(rows) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + rows[i]['copies']
    tables = [{k: comb(row['copies'], k) for k in range(min(row['copies'], seen) + 1)} for row in rows]
    selected = [0] * len(rows)
    evaluated = 0

    def visit(index, left, weight, targets):
        nonlocal evaluated
        if index == len(rows):
            evaluated += 1
            # A defensive guard never publishes a partial result.
            _require(evaluated <= vectors, 'vector execution bound exceeded', 'RESOURCE_BUDGET_REFUSAL')
            if mode == 'observe' and targets < target_minimum:
                return 0
            sources = [mask for mask, count in zip(masks, selected) for _ in range(count) if mask]
            return weight if _matching(sources, demands) else 0
        total = 0
        row = rows[index]
        for count in range(max(0, left - suffix[index + 1]), min(row['copies'], left) + 1):
            selected[index] = count
            total += visit(index + 1, left - count, weight * tables[index][count], targets + count * row['target'])
        return total

    favorable = visit(0, seen, 1, 0)
    total = comb(normalized['population_size'], seen)
    probability = Fraction(favorable, total)
    report = dict(schema_version=REPORT_VERSION, method=METHOD, status='CALCULATED',
                  scope='HYPOTHETICAL_JOINT_ACCESS_AND_ASSIGNMENT_ONLY',
                  real_gameplay_authorized=False, input_id=_identity(INPUT_VERSION, normalized),
                  input=normalized, favorable_physical_hands=str(favorable), total_physical_hands=str(total),
                  probability=_fraction(probability), event='IMPOSSIBLE' if not favorable else 'POSSIBLE',
                  computation=dict(count_vectors=vectors, vectors_evaluated=evaluated,
                                   estimated_work_units=work, max_vectors=MAX_VECTORS, max_work_units=MAX_WORK),
                  limitations=list(LIMITATIONS))
    report['report_id'] = _identity(REPORT_VERSION, report)
    _require(len(canonical_json(report).encode()) <= MAX_REPORT_BYTES, 'report byte bound exceeded', 'RESOURCE_BUDGET_REFUSAL')
    return report
