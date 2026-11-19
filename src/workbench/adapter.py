"""Closed local presentation boundary over the unchanged supplied-deck owner."""
from hashlib import sha256
import json

from probability.supplied_deck import SuppliedDeckError, assess_supplied_decks
from probability.draw_access import canonical_json

INPUT_VERSION = 'deck-workbench-input-v1'
REPORT_VERSION = 'deck-workbench-report-v1'
MAX_INPUT_BYTES = 196608
MAX_REPORT_BYTES = 393216


class WorkbenchError(ValueError):
    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', reason=str(self))


def _require(condition, reason):
    if not condition:
        raise WorkbenchError(reason)


def _identity(version, value):
    return 'sha256:' + sha256(version.encode() + b'\0' + canonical_json(value).encode()).hexdigest()


def parse_workbench(raw):
    """Decode strictly without coercion, duplicate keys or unbounded source input."""
    _require(type(raw) is bytes and len(raw) <= MAX_INPUT_BYTES, 'bounded UTF-8 JSON required')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def nonfinite(_):
        raise WorkbenchError('nonfinite JSON number')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError):
        raise WorkbenchError('invalid bounded UTF-8 JSON') from None


def _percent(probability):
    """Presentation only: scale the owner's exact rational by 100, half-even to 12 places."""
    n, d = int(probability['numerator']), int(probability['denominator'])
    scale = 10 ** 12
    q, r = divmod(abs(n) * 100 * scale, d)
    if 2 * r > d or (2 * r == d and q % 2):
        q += 1
    return ('-' if n < 0 else '') + str(q // scale) + '.' + str(q % scale).zfill(12)


def assess_workbench(request):
    """Return an immutable-by-ownership report; no catalog, files or collection is accessed."""
    _require(type(request) is dict and request.keys() == {'schema_version', 'labels', 'analysis'},
             'closed workbench request required')
    _require(type(request['schema_version']) is str and request['schema_version'] == INPUT_VERSION,
             'unsupported workbench version')
    try:
        _require(len(canonical_json(request).encode()) <= MAX_INPUT_BYTES, 'input byte budget exceeded')
        analysis = assess_supplied_decks(request['analysis'])
    except SuppliedDeckError as error:
        raise WorkbenchError(str(error)) from None
    except WorkbenchError:
        raise
    except (TypeError, ValueError, RecursionError):
        raise WorkbenchError('invalid bounded workbench input') from None
    labels = request['labels']
    _require(type(labels) is list and len(labels) <= 1024, 'bounded card label list required')
    identities = {row['card_id'] for deck in analysis['input']['decks'] for row in deck['entries']}
    normalized = {}
    for row in labels:
        _require(type(row) is dict and row.keys() == {'card_id', 'label'}, 'closed card label required')
        for key in ('card_id', 'label'):
            text = row[key]
            _require(type(text) is str and 0 < len(text) <= 128 and text == text.strip()
                     and text.isprintable(), 'invalid caller-local identity or label')
        _require(row['card_id'] not in normalized, 'duplicate caller-local label identity')
        normalized[row['card_id']] = row['label']
    _require(set(normalized) == identities, 'labels must bind exactly the declared card identities')
    value = dict(schema_version=INPUT_VERSION,
                 labels=[dict(card_id=k, label=v) for k, v in sorted(normalized.items())],
                 analysis=analysis['input'])
    presentation = dict(configurations=[dict(deck_id=deck['deck_id'], observations=[
        dict(label=row['label'], percent=_percent(row['probability'])) for row in deck['results']])
        for deck in analysis['configurations']], differences=[
            dict(label=row['label'], percentage_points=_percent(row['candidate_minus_baseline']))
            for row in analysis['comparison']['differences']])
    report = dict(schema_version=REPORT_VERSION, status='ASSESSED', input=value,
        input_id=_identity(INPUT_VERSION, value), analysis=analysis, presentation=presentation,
        authority='CALLER_DECLARED_ACCESS_ANALYSIS_ONLY', real_gameplay_authorized=False)
    report['report_id'] = _identity(REPORT_VERSION, report)
    _require(len(canonical_json(report).encode()) + 1 <= MAX_REPORT_BYTES, 'report byte budget exceeded')
    return report
