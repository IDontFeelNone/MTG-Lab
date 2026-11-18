"""Exact access analysis over complete caller-declared deck populations."""
from fractions import Fraction
from hashlib import sha256
import json

from .draw_access import (ASSUMPTIONS, INPUT_VERSION as DRAW_INPUT_VERSION,
                          DrawAccessError, assess_draw_access, canonical_json)

INPUT_VERSION = 'supplied-deck-consistency-input-v1'
REPORT_VERSION = 'supplied-deck-consistency-report-v1'
MAX_INPUT_BYTES = 131072
MAX_REPORT_BYTES = 262144
MAX_ROWS = 512


class SuppliedDeckError(ValueError):
    """A structured refusal; no partial analytical result is published."""
    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', reason=str(self),
                    real_gameplay_authorized=False)


def _require(condition, reason):
    if not condition: raise SuppliedDeckError(reason)


def _fields(value, required):
    _require(type(value) is dict and value.keys() == set(required), 'closed object fields required')


def _text(value, maximum, label):
    _require(type(value) is str and 0 < len(value) <= maximum and value == value.strip()
             and value.isprintable(), 'invalid ' + label)


def _integer(value, minimum, maximum, label):
    _require(type(value) is int and minimum <= value <= maximum, 'invalid ' + label)


def _section(value):
    _text(value, 48, 'section')
    _require(value in ('main', 'sideboard', 'commander', 'companion')
             or (value.startswith('other:') and len(value) > 6), 'unsupported section')


def _identity(version, body):
    return 'sha256:' + sha256(version.encode() + b'\0' + canonical_json(body).encode()).hexdigest()


def _fraction(value):
    # Small exact rational presentation, including signed comparison differences.
    scale = 10 ** 12
    q, r = divmod(abs(value.numerator) * scale, value.denominator)
    if 2 * r > value.denominator or (2 * r == value.denominator and q % 2): q += 1
    decimal = ('-' if value < 0 else '') + str(q // scale) + '.' + str(q % scale).zfill(12)
    return dict(numerator=str(value.numerator), denominator=str(value.denominator),
                decimal=decimal, decimal_places=12, rounding='ROUND_HALF_EVEN')


def _exact(row):
    return Fraction(int(row['numerator']), int(row['denominator']))


def validate_supplied_decks(request):
    """Normalize explicit quantities; resolve no names, aliases or canonical facts."""
    _fields(request, ('schema_version', 'decks'))
    _require(type(request['schema_version']) is str and request['schema_version'] == INPUT_VERSION,
             'unsupported input version')
    decks = request['decks']
    _require(type(decks) is list and 1 <= len(decks) <= 2, 'one or two decks required')
    normalized = []; deck_ids = set()
    for deck in decks:
        _fields(deck, ('deck_id', 'identity_authority', 'complete', 'draw_population',
                       'entries', 'groups', 'schedule', 'assumptions'))
        _text(deck['deck_id'], 128, 'deck_id')
        _require(deck['deck_id'] not in deck_ids, 'duplicate deck identity')
        deck_ids.add(deck['deck_id'])
        _require(type(deck['identity_authority']) is str and deck['identity_authority'] == 'CALLER_DECLARED',
                 'only explicit caller-declared identities are supported')
        _require(deck['complete'] is True, 'complete draw population declaration required')
        population = deck['draw_population']; _fields(population, ('section', 'declared_size'))
        _section(population['section']); _integer(population['declared_size'], 1, 120, 'declared size')
        entries = deck['entries']
        _require(type(entries) is list and 1 <= len(entries) <= MAX_ROWS, 'bounded nonempty deck entries required')
        totals = {}
        for entry in entries:
            _fields(entry, ('card_id', 'section', 'quantity'))
            _text(entry['card_id'], 128, 'caller Card identity'); _section(entry['section'])
            _integer(entry['quantity'], 0, 120, 'quantity')
            key = entry['section'], entry['card_id']
            totals[key] = totals.get(key, 0) + entry['quantity']
            _integer(totals[key], 0, 120, 'aggregated quantity')
        rows = [dict(section=s, card_id=c, quantity=q) for (s, c), q in sorted(totals.items())]
        selected = {c: q for (s, c), q in totals.items() if s == population['section']}
        size = sum(selected.values())
        _require(size == population['declared_size'], 'selected population and declared size disagree')
        groups = deck['groups']
        _require(type(groups) is list and 1 <= len(groups) <= 3, 'one through three analytical groups required')
        normalized_groups = []; group_ids = set(); member_ids = set()
        for group in groups:
            _fields(group, ('group_id', 'members', 'minimum'))
            _text(group['group_id'], 64, 'group identity')
            _require(group['group_id'] not in group_ids, 'duplicate group identity')
            group_ids.add(group['group_id']); _integer(group['minimum'], 0, 120, 'group minimum')
            members = group['members']
            _require(type(members) is list and 1 <= len(members) <= 120, 'bounded nonempty member identities required')
            for member in members:
                _text(member, 128, 'group member')
                _require(member in selected, 'group member not declared in selected population')
                _require(member not in member_ids, 'duplicate or overlapping group member')
                member_ids.add(member)
            normalized_groups.append(dict(group_id=group['group_id'], members=sorted(members), minimum=group['minimum']))
        _fields(deck['assumptions'], ASSUMPTIONS)
        _require(deck['assumptions'] == ASSUMPTIONS, 'explicit supported draw-access assumptions required')
        schedule = deck['schedule']
        _require(type(schedule) is list and 1 <= len(schedule) <= 21, 'bounded nonempty observation schedule required')
        observations = []; labels = set(); previous = -1
        for entry in schedule:
            _fields(entry, ('label', 'cards_seen')); _text(entry['label'], 80, 'observation label')
            _integer(entry['cards_seen'], 0, min(size, 20), 'cards seen')
            _require(entry['label'] not in labels and entry['cards_seen'] >= previous,
                     'schedule must have unique labels and cumulative nondecreasing counts')
            labels.add(entry['label']); previous = entry['cards_seen']; observations.append(dict(entry))
        normalized.append(dict(deck_id=deck['deck_id'], identity_authority='CALLER_DECLARED', complete=True,
            draw_population=dict(population), entries=rows, groups=sorted(normalized_groups, key=lambda g:g['group_id']),
            schedule=observations, assumptions=dict(ASSUMPTIONS)))
    result = dict(schema_version=INPUT_VERSION, decks=normalized)
    _require(len(canonical_json(request).encode()) <= MAX_INPUT_BYTES, 'raw input byte budget exceeded')
    _require(len(canonical_json(result).encode()) <= MAX_INPUT_BYTES, 'input byte budget exceeded')
    return result


def parse_supplied_decks(raw):
    _require(type(raw) in (str, bytes) and len(raw) <= MAX_INPUT_BYTES, 'bounded UTF-8 JSON required')
    try:
        encoded = raw.encode() if type(raw) is str else raw
        _require(len(encoded) <= MAX_INPUT_BYTES, 'input byte budget exceeded')
        def unique(pairs):
            value = {}
            for key, item in pairs:
                _require(key not in value, 'duplicate JSON key'); value[key] = item
            return value
        def nonfinite(_): raise SuppliedDeckError('nonfinite JSON number')
        value = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, SuppliedDeckError): raise
        raise SuppliedDeckError('invalid bounded UTF-8 JSON') from None
    return validate_supplied_decks(value)


def assess_supplied_decks(request):
    """Derive population counts, delegate exact mathematics and compare equivalent events."""
    normalized = validate_supplied_decks(request); reports = []
    for deck in normalized['decks']:
        selected = [dict(card_id=r['card_id'], quantity=r['quantity']) for r in deck['entries']
                    if r['section'] == deck['draw_population']['section']]
        quantities = {r['card_id']:r['quantity'] for r in selected}; groups = []
        for g in deck['groups']:
            groups.append(dict(group_id=g['group_id'], minimum=g['minimum'],
                copies=sum(quantities[c] for c in g['members']),
                members=[dict(card_id=c, copies=quantities[c]) for c in g['members'] if quantities[c]]))
        impossible = [g['group_id'] for g in groups if g['minimum'] > g['copies']]
        derived = dict(schema_version=DRAW_INPUT_VERSION, deck_size=deck['draw_population']['declared_size'],
                       groups=groups, schedule=deck['schedule'], assumptions=deck['assumptions'])
        if impossible:
            # An empty event is exactly zero. Do not forge an admissible v1 engine
            # request by clipping a minimum or inventing copies. No combinatorics
            # are reimplemented; all nonempty-population calculations use the owner.
            engine = None
            results = [dict(**entry, probability=_fraction(Fraction(0))) for entry in deck['schedule']]
        else:
            try: engine = assess_draw_access(derived)
            except DrawAccessError as error: raise SuppliedDeckError(str(error)) from None
            results = engine['results']
        reports.append(dict(deck_id=deck['deck_id'], deck_input_id=_identity('supplied-deck-v1', deck),
            deck_size=derived['deck_size'], selected_section=deck['draw_population']['section'],
            selected_quantities=selected, derived_groups=groups, results=results,
            status='IMPOSSIBLE_POPULATION_REQUIREMENT' if impossible else 'CALCULATED',
            impossible_group_ids=impossible, draw_access_report=engine,
            assumptions=dict(deck['assumptions']), identity_authority='CALLER_DECLARED'))
    comparison = dict(status='NOT_REQUESTED', reasons=[], baseline_deck_id=None, candidate_deck_id=None, differences=[])
    if len(reports) == 2:
        a, b = normalized['decks']; reasons = []
        def event(deck):
            return sorted((tuple(g['members']), g['minimum']) for g in deck['groups'])
        if event(a) != event(b): reasons.append('TARGET_IDENTITIES_OR_MINIMUM_REQUIREMENTS_DIFFER')
        if a['schedule'] != b['schedule']: reasons.append('OBSERVATION_SCHEDULES_DIFFER')
        if a['draw_population']['section'] != b['draw_population']['section']: reasons.append('SELECTED_SECTIONS_DIFFER')
        if a['assumptions'] != b['assumptions']: reasons.append('SAMPLING_ASSUMPTIONS_DIFFER')
        comparison.update(status='ABSTAINED' if reasons else 'COMPARABLE', reasons=reasons,
                          baseline_deck_id=a['deck_id'], candidate_deck_id=b['deck_id'])
        if not reasons:
            comparison['differences'] = [dict(label=x['label'], cards_seen=x['cards_seen'],
                candidate_minus_baseline=_fraction(_exact(y['probability']) - _exact(x['probability'])))
                for x, y in zip(reports[0]['results'], reports[1]['results'])]
    report = dict(schema_version=REPORT_VERSION, status='ASSESSED', input=normalized,
        input_id=_identity(INPUT_VERSION, normalized), configurations=reports, comparison=comparison,
        bounds=dict(max_decks=2, max_rows_per_deck=MAX_ROWS, max_deck_size=120, max_cards_seen=20,
                    max_groups=3, max_input_bytes=MAX_INPUT_BYTES, max_report_bytes=MAX_REPORT_BYTES),
        real_gameplay_authorized=False, scope='CALLER_SUPPLIED_DECK_ACCESS_ONLY', limitations=[
            'Completeness, Card identities, quantities, section selection and interchangeability are caller declarations, not canonical admissions.',
            'Only the explicitly selected section is sampled uniformly without replacement; no other section is silently included.',
            'Observation labels establish no Magic turn, mulligan, play/draw or additional-draw rules.',
            'No casting, mana feasibility, combo success, legality, strategic superiority, disruption success or win rate follows.',
            'Comparison uses identical member identities, minima, selected section and full observation schedule; labels alone never establish equivalent events.',
            'No analytical mapping, private collection access, source acquisition or AI export is performed.'])
    report['report_id'] = _identity(REPORT_VERSION, report)
    _require(len(canonical_json(report).encode()) + 1 <= MAX_REPORT_BYTES, 'report byte budget exceeded')
    return report


def render_supplied_decks(report, *, readable=False):
    if not readable: return canonical_json(report) + '\n'
    if report['status'] == 'REFUSED': return 'REFUSED: ' + report['reason'] + '\n'
    lines = ['Supplied deck access (caller declarations; no gameplay or strategic ranking)']
    for deck in report['configurations']:
        lines.append(deck['deck_id'] + ': ' + str(deck['deck_size']) + ' cards from ' + deck['selected_section'])
        for group in deck['derived_groups']:
            lines.append(group['group_id'] + ': ' + str(group['copies']) + ' declared copies; minimum '
                         + str(group['minimum']))
        if deck['impossible_group_ids']:
            lines.append('Impossible population requirements: ' + ', '.join(deck['impossible_group_ids']))
        for row in deck['results']:
            p = row['probability']; lines.append(row['label'] + ' (' + str(row['cards_seen']) + ' seen): '
                + p['numerator'] + '/' + p['denominator'] + ' = ' + p['decimal'])
    lines.append('Comparison: ' + report['comparison']['status'])
    for row in report['comparison']['differences']:
        p = row['candidate_minus_baseline']; lines.append(row['label'] + ' candidate minus baseline: '
            + p['numerator'] + '/' + p['denominator'] + ' = ' + p['decimal'])
    lines.extend(report['comparison']['reasons']); lines.extend(report['limitations'])
    return '\n'.join(lines) + '\n'
