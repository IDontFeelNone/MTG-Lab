"""Exact at-least-one probabilities over the simulator's admitted compositions."""
from fractions import Fraction
from hashlib import sha256
import json
import re

from simulation.pack import ValidatedPackComposition, PackSimulationError
from .draw_access import canonical_json

INPUT_VERSION = 'pack-target-odds-input-v1'
REPORT_VERSION = 'pack-target-odds-report-v1'
METHOD = 'weighted-composition-target-hit-exact-v1'
INDEPENDENCE = 'independent-identically-distributed-packs'
MAX_PACKS = 10000
MAX_INPUT_BYTES = 32768
MAX_REPORT_BYTES = 65536
MAX_INTEGER_BITS = 1000000
MAX_TOTAL_POWER_BITS = 4000000


class PackOddsError(ValueError):
    """Explicit refusal; invalid or oversized requests never return partial results."""
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', code=self.code,
                    reason=self.reason, production_authorized=False)


def _require(condition, reason, code='INVALID_INPUT'):
    if not condition: raise PackOddsError(code, reason)


def _identity(domain, value):
    return 'sha256:' + sha256(domain.encode() + b'\0' + canonical_json(value).encode()).hexdigest()


def _fields(value, required, optional=()):
    _require(type(value) is dict and set(required) <= value.keys()
             and value.keys() <= set(required) | set(optional), 'closed object fields required')


def _threshold(value):
    if type(value) is str:
        _require(re.fullmatch(r'(?:0|1|0\.[0-9]{1,18}|1\.0{1,18})', value) is not None,
                 'threshold must be an unambiguous decimal in [0,1] with at most 18 places')
        return Fraction(value)
    _fields(value, ('numerator', 'denominator'))
    for name in ('numerator', 'denominator'):
        text = value[name]
        _require(type(text) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,127})', text) is not None,
                 'threshold integers must be bounded unsigned decimal strings')
    numerator, denominator = int(value['numerator']), int(value['denominator'])
    _require(0 <= numerator <= denominator and denominator > 0, 'threshold must be in [0,1]')
    return Fraction(numerator, denominator)


def validate_pack_odds(request):
    _fields(request, ('schema_version', 'target', 'pack_counts', 'independence'), ('threshold', 'box'))
    _require(type(request['schema_version']) is str and request['schema_version'] == INPUT_VERSION,
             'unsupported input version')
    _require(type(request['independence']) is str and request['independence'] == INDEPENDENCE,
             'explicit independent identically distributed pack assumption required')
    target = request['target']
    _fields(target, ('kind', 'id'), ('finish_id', 'treatment_id'))
    _require(all(type(v) is str and 0 < len(v) <= 128 and v == v.strip()
                 and v.isprintable() for v in target.values()) and target['kind'] in ('card', 'printing'),
             'exact bounded Card or Printing target required')
    counts = request['pack_counts']
    _require(type(counts) is list and 1 <= len(counts) <= 32
             and all(type(n) is int and 0 <= n <= MAX_PACKS for n in counts), 'invalid bounded pack counts')
    _require(counts == sorted(set(counts)), 'pack counts must be distinct and ascending')
    result = dict(schema_version=INPUT_VERSION, target=dict(target), pack_counts=list(counts),
                  independence=INDEPENDENCE)
    if 'threshold' in request:
        threshold = _threshold(request['threshold'])
        result['threshold'] = dict(numerator=str(threshold.numerator), denominator=str(threshold.denominator))
    if 'box' in request:
        _require('threshold' in request, 'box arithmetic requires a minimum-pack request')
        box = request['box']; _fields(box, ('packs_per_box', 'basis'))
        _require(type(box['packs_per_box']) is int and 1 <= box['packs_per_box'] <= 1000
                 and type(box['basis']) is str and box['basis'] == 'HYPOTHETICAL_CALLER_DECLARATION',
                 'V1 accepts only an explicit hypothetical pack count, never a verified flag')
        result['box'] = dict(box)
    _require(len(canonical_json(result).encode()) <= MAX_INPUT_BYTES, 'input byte bound exceeded')
    return result


def parse_pack_odds(raw):
    _require(type(raw) in (str, bytes) and len(raw) <= MAX_INPUT_BYTES, 'bounded JSON bytes or text required')
    try:
        encoded = raw.encode() if type(raw) is str else raw
        _require(len(encoded) <= MAX_INPUT_BYTES, 'input byte bound exceeded')

        def unique(pairs):
            value = {}
            for key, item in pairs:
                _require(key not in value, 'duplicate JSON key')
                value[key] = item
            return value

        def nonfinite(_):
            raise PackOddsError('INVALID_INPUT', 'nonfinite JSON number')

        value = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, PackOddsError): raise
        raise PackOddsError('INVALID_INPUT', 'invalid bounded UTF-8 JSON') from None
    return validate_pack_odds(value)


class _Budget:
    def __init__(self): self.total = 0

    def check(self, value):
        _require(max(value.numerator.bit_length(), value.denominator.bit_length()) <= MAX_INTEGER_BITS,
                 'exact integer bit budget exceeded', 'RESOURCE_LIMIT')
        return value

    def power(self, value, exponent):
        if exponent == 0: return Fraction(1)
        if value in (0, 1): return value
        bits = max(value.numerator.bit_length(), value.denominator.bit_length()) * exponent
        self.total += bits
        _require(bits <= MAX_INTEGER_BITS and self.total <= MAX_TOTAL_POWER_BITS,
                 'exact exponentiation budget exceeded', 'RESOURCE_LIMIT')
        return self.check(value ** exponent)


def _payload(value):
    # Hex integers avoid Python's process-wide decimal integer-string limit.
    characters = (value.numerator.bit_length() + value.denominator.bit_length() + 7) // 4
    _require(characters + 256 <= MAX_REPORT_BYTES, 'exact fraction output budget exceeded', 'RESOURCE_LIMIT')
    scale = 10 ** 12
    quotient, remainder = divmod(value.numerator * scale, value.denominator)
    if 2 * remainder > value.denominator or (2 * remainder == value.denominator and quotient % 2):
        quotient += 1
    return dict(exact_fraction=dict(encoding='hexadecimal-integers', numerator=hex(value.numerator),
                                   denominator=hex(value.denominator)),
                decimal=str(quotient // scale) + '.' + str(quotient % scale).zfill(12),
                decimal_places=12, rounding='ROUND_HALF_EVEN',
                is_zero=value == 0, is_certain=value == 1)


def assess_pack_target(composition, request):
    """Analyze one owning-reader view; never infer a physical pack distribution."""
    normalized = validate_pack_odds(request)
    _require(type(composition) is ValidatedPackComposition, 'owning validated composition view required', 'MODEL_NOT_READY')
    try:
        target = composition.resolve_target(normalized['target'])
    except PackSimulationError as error:
        raise PackOddsError('TARGET_NOT_READY', ', '.join(error.requirements)) from None
    body = composition.to_dict(); context = body['context']; budget = _Budget()
    matched = {(v['printing_id'], v['finish_id']) for v in target['matched_outcomes']}
    weights = dict(context['variant_entries']) if context['variant_model'] else {context['pack_id']: 1}
    total = sum(weights.values()); miss = Fraction(0)
    for variant_id, weight in sorted(weights.items()):
        variant_miss = Fraction(1)
        draws, _ = context['candidates'][variant_id]
        for _, _, count, entries in draws:
            pool_total = sum(w for _, w in entries)
            hit = sum(w for outcome, w in entries
                      if ((outcome[0], outcome[1]) if context['finish_aware'] else (outcome, None)) in matched)
            slot_miss = budget.power(Fraction(pool_total - hit, pool_total), count)
            variant_miss = budget.check(variant_miss * slot_miss)
        miss = budget.check(miss + Fraction(weight, total) * variant_miss)
    single = 1 - miss
    cache = {0: Fraction(0), 1: single}

    def at(count):
        if count not in cache: cache[count] = budget.check(1 - budget.power(miss, count))
        return cache[count]

    results = [dict(packs=n, probability=_payload(at(n))) for n in normalized['pack_counts']]
    solver = dict(status='NOT_REQUESTED')
    if 'threshold' in normalized:
        threshold = _threshold(normalized['threshold'])
        if threshold == 0:
            minimum = 0
        elif single == 0:
            minimum = None; solver = dict(status='IMPOSSIBLE_ZERO_PROBABILITY')
        elif single == 1:
            minimum = 1
        elif threshold == 1:
            minimum = None; solver = dict(status='NO_FINITE_SOLUTION')
        else:
            low, high = 0, 1
            while high < MAX_PACKS and at(high) < threshold:
                low, high = high, min(MAX_PACKS, high * 2)
            if at(high) < threshold:
                minimum = None
                solver = dict(status='NOT_REACHED_WITHIN_BOUND', tested_bound=MAX_PACKS,
                              probability_at_bound=_payload(at(MAX_PACKS)), exact_comparison='P(bound) < threshold')
            else:
                while high - low > 1:
                    middle = (low + high) // 2
                    if at(middle) >= threshold: high = middle
                    else: low = middle
                minimum = high
        if minimum is not None:
            _require(at(minimum) >= threshold and (minimum == 0 or at(minimum - 1) < threshold),
                     'minimum-pack proof failed', 'INTERNAL_INVARIANT')
            solver = dict(status='REACHED', minimum_packs=minimum, probability=_payload(at(minimum)),
                          previous_probability=_payload(at(minimum - 1)) if minimum else None,
                          minimality='EXACT_RATIONAL_COMPARISON')
    box = None
    if 'box' in normalized:
        box = dict(normalized['box'], status='NOT_APPLICABLE')
        if solver['status'] == 'REACHED':
            needed = solver['minimum_packs']; count = box['packs_per_box']
            boxes = (needed + count - 1) // count
            box.update(status='ARITHMETIC_ONLY', boxes=boxes, packs=boxes * count,
                       surplus_packs=boxes * count - needed)
    sources = {**context['sources'], **body['field_sources']}
    report = dict(schema_version=REPORT_VERSION, method=METHOD, status='CALCULATED',
                  input=normalized, input_id=_identity(INPUT_VERSION, dict(
                      composition_id=body['composition_id'], request=normalized)),
                  model=dict(game=context['game'], product_id=context['product_id'],
                      product_version_id=context['version_id'], pack_definition_id=context['pack_id'],
                      simulation_model=context['model'], simulator_version=context['report_version'],
                      query_snapshot_id=context['query_snapshot_id'], input_id=context['input_id'],
                      composition_id=body['composition_id']),
                  target_resolution=target, single_pack_probability=_payload(single),
                  pack_results=results, solver=solver, box_arithmetic=box,
                  bounds=dict(max_packs=MAX_PACKS, max_integer_bits=MAX_INTEGER_BITS,
                              max_total_power_bits=MAX_TOTAL_POWER_BITS, max_report_bytes=MAX_REPORT_BYTES),
                  source_references=[dict(id=k, content_id=_identity('pack-odds-source-v1', v))
                                     for k, v in sorted(sources.items())],
                  production_authorized=False, scope='DECLARED_MODEL_ODDS_ONLY_NON_PRODUCTION',
                  limitations=[
                      'Probabilities describe the admitted mathematical model, not verified physical manufacturing.',
                      'Repeated-pack probabilities are conditional on the explicitly declared independent identically distributed pack assumption.',
                      'No expected-copy count, multiple-copy distribution, box correlation or physical guarantee is established.',
                      'Finish and singular fixed-treatment predicates infer no missing eligibility or probabilities.',
                      'Source declarations and checksums do not grant source-use rights, authenticated approval or production admission.',
                      'A rounded decimal zero is not impossibility; use the exact fraction and is_zero flag.'])
    report['report_id'] = _identity(REPORT_VERSION, report)
    _require(len(canonical_json(report).encode()) + 1 <= MAX_REPORT_BYTES, 'report byte budget exceeded', 'RESOURCE_LIMIT')
    return report
