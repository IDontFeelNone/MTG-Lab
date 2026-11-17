"""Exact card-access mathematics over bounded caller declarations, not gameplay."""
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import comb

INPUT_VERSION = 'deck-draw-access-input-v1'
REPORT_VERSION = 'deck-draw-access-report-v1'
METHOD = 'multivariate-hypergeometric-exact-v1'
MAX_INPUT_BYTES = 32768
MAX_REPORT_BYTES = 65536
ASSUMPTIONS = {'sampling': 'uniform-without-replacement',
               'group_disjointness': 'caller_declared'}
LIMITATIONS = (
    'Counts, identities, group interchangeability and schedule labels are caller declarations, not verified Card or deck facts.',
    'Every subset of the declared size is equally likely; no actual shuffle or game is simulated.',
    'Cards seen means cumulative access, not cards still in hand or available to spend.',
    'Schedule labels establish no Magic turn, play/draw, mulligan or additional-draw rules.',
    'No mana feasibility, casting, combo execution, disruption success, legality, tier or win-rate conclusion follows.',
)


class DrawAccessError(ValueError):
    """Explicit bounded input rejection; no partial probability report is returned."""
    code = 'INVALID_DRAW_ACCESS_INPUT'

    def as_dict(self):
        return {'schema_version': REPORT_VERSION, 'status': self.code, 'reason': str(self)}


def _require(condition, reason):
    if not condition:
        raise DrawAccessError(reason)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def _identity(domain, value):
    return 'sha256:' + sha256(domain.encode() + b'\0' + canonical_json(value).encode()).hexdigest()


def _fields(value, required, optional=()):
    _require(type(value) is dict and set(required) <= value.keys()
             and value.keys() <= set(required) | set(optional), 'closed object fields required')


def _integer(value, minimum, maximum, label):
    _require(type(value) is int and minimum <= value <= maximum, label + ' outside supported integer bounds')


def _text(value, maximum, label):
    _require(type(value) is str and 0 < len(value) <= maximum
             and value == value.strip() and value.isprintable(), 'invalid ' + label)


def validate_draw_access(request):
    """Return an independently owned normalized request; resolve no Card identities."""
    _fields(request, ('schema_version', 'deck_size', 'groups', 'schedule', 'assumptions'))
    _require(request['schema_version'] == INPUT_VERSION, 'unsupported input version')
    _fields(request['assumptions'], ('sampling', 'group_disjointness'))
    _require(request['assumptions'] == ASSUMPTIONS, 'explicit supported sampling and disjointness assumptions required')
    size = request['deck_size']
    _integer(size, 1, 120, 'deck_size')
    raw_groups = request['groups']
    _require(type(raw_groups) is list and 1 <= len(raw_groups) <= 3, 'one through three groups required')
    groups, group_ids, card_ids = [], set(), set()
    for raw in raw_groups:
        _fields(raw, ('group_id', 'copies', 'minimum'), ('members',))
        identifier, copies, minimum = raw['group_id'], raw['copies'], raw['minimum']
        _text(identifier, 64, 'group_id')
        _require(identifier not in group_ids, 'duplicate group identity')
        group_ids.add(identifier)
        _integer(copies, 0, size, 'group copies')
        _integer(minimum, 0, copies, 'group minimum')
        group = {'group_id': identifier, 'copies': copies, 'minimum': minimum}
        if 'members' in raw:
            members = raw['members']
            _require(type(members) is list and len(members) <= copies, 'bounded member list required')
            normalized = []
            for member in members:
                _fields(member, ('card_id', 'copies'))
                card_id, quantity = member['card_id'], member['copies']
                _text(card_id, 128, 'caller card_id')
                _integer(quantity, 1, size, 'member copies')
                _require(card_id not in card_ids, 'overlapping or duplicate member identity')
                card_ids.add(card_id)
                normalized.append({'card_id': card_id, 'copies': quantity})
            _require(sum(m['copies'] for m in normalized) == copies, 'member and group copy counts disagree')
            group['members'] = sorted(normalized, key=lambda m: m['card_id'])
        groups.append(group)
    _require(sum(g['copies'] for g in groups) <= size, 'group totals exceed deck size')
    raw_schedule = request['schedule']
    _require(type(raw_schedule) is list and 1 <= len(raw_schedule) <= 21, 'one through twenty-one schedule entries required')
    schedule, labels, previous = [], set(), -1
    for entry in raw_schedule:
        _fields(entry, ('label', 'cards_seen'))
        label, seen = entry['label'], entry['cards_seen']
        _text(label, 80, 'schedule label')
        _require(label not in labels, 'duplicate schedule label')
        labels.add(label)
        _integer(seen, 0, min(20, size), 'cards_seen')
        _require(seen >= previous, 'schedule must be cumulative and nondecreasing')
        previous = seen
        schedule.append({'label': label, 'cards_seen': seen})
    normalized = {'schema_version': INPUT_VERSION, 'deck_size': size,
                  'groups': sorted(groups, key=lambda g: g['group_id']),
                  'schedule': schedule, 'assumptions': dict(ASSUMPTIONS)}
    _require(len(canonical_json(normalized).encode()) <= MAX_INPUT_BYTES, 'input byte bound exceeded')
    return normalized


def parse_draw_access(raw):
    """Strict UTF-8 JSON with a byte bound, duplicate-key and nonfinite rejection."""
    _require(type(raw) in (bytes, str), 'JSON bytes or text required')
    try:
        _require(len(raw) <= MAX_INPUT_BYTES, 'input byte bound exceeded')
        encoded = raw.encode('utf-8') if type(raw) is str else raw
        _require(len(encoded) <= MAX_INPUT_BYTES, 'input byte bound exceeded')

        def unique(pairs):
            result = {}
            for key, value in pairs:
                _require(key not in result, 'duplicate JSON key')
                result[key] = value
            return result

        def nonfinite(_):
            raise DrawAccessError('nonfinite JSON number')

        value = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, DrawAccessError):
            raise
        raise DrawAccessError('invalid bounded UTF-8 JSON') from None
    return validate_draw_access(value)


def _probability(size, groups, seen):
    """Count favorable subsets; group counts are dependent, never multiplied odds."""
    denominator = comb(size, seen)
    remainder = size - sum(g['copies'] for g in groups)
    ranges = [range(g['minimum'], min(g['copies'], seen) + 1) for g in groups]
    tables = [{k: comb(g['copies'], k) for k in values} for g, values in zip(groups, ranges)]
    favorable = 0
    for counts in product(*ranges):
        other = seen - sum(counts)
        if not 0 <= other <= remainder:
            continue
        ways = comb(remainder, other)
        for table, count in zip(tables, counts):
            ways *= table[count]
        favorable += ways
    exact = Fraction(favorable, denominator)
    with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
        decimal = (Decimal(exact.numerator) / Decimal(exact.denominator)).quantize(Decimal('0.000000000001'))
    return {'numerator': str(exact.numerator), 'denominator': str(exact.denominator),
            'decimal': format(decimal, '.12f'), 'decimal_places': 12, 'rounding': 'ROUND_HALF_EVEN'}


def assess_draw_access(request):
    """Assess all declared group thresholds at each cumulative sample size.

    No repository, filesystem, source evidence, random generator or game engine
    participates. Presentation fractions are reduced and encoded as strings.
    """
    normalized = validate_draw_access(request)
    cache = {}
    results = []
    for entry in normalized['schedule']:
        seen = entry['cards_seen']
        if seen not in cache:
            cache[seen] = _probability(normalized['deck_size'], normalized['groups'], seen)
        results.append({**entry, 'probability': dict(cache[seen])})
    report = {'schema_version': REPORT_VERSION, 'method': METHOD, 'status': 'CALCULATED',
              'input_id': _identity(INPUT_VERSION, normalized), 'input': normalized,
              'results': results, 'limitations': list(LIMITATIONS),
              'scope': 'CALLER_DECLARED_CARD_ACCESS_ONLY', 'real_gameplay_authorized': False}
    report['report_id'] = _identity(REPORT_VERSION, report)
    _require(len(canonical_json(report).encode()) <= MAX_REPORT_BYTES, 'report byte bound exceeded')
    return report
