"""Closed, bounded JSON ownership for the fixed pending interpretation pilot."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

PLAN_VERSION = 'card-rules-mana-pilot-plan-v1'
CANDIDATE_VERSION = 'card-rules-mana-interpretation-candidate-v1'
REPORT_VERSION = 'card-rules-mana-review-report-v1'
PLAN_LIMIT = 65_536
CANDIDATE_LIMIT = 131_072
REPORT_LIMIT = 1_048_576


class PilotError(ValueError):
    """Invalid binding or representation, never a semantic-review outcome."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def owned(value, *, limit=REPORT_LIMIT):
    budget = [0]
    def inspect(node, depth=0):
        budget[0] += 1
        if depth > 20 or budget[0] > 100_000:
            raise PilotError('JSON structure limit')
        if type(node) is dict:
            for key, child in node.items():
                if type(key) is not str or not key or len(key) > 128:
                    raise PilotError('bounded exact string keys required')
                inspect(child, depth + 1)
        elif type(node) is list:
            for child in node:
                inspect(child, depth + 1)
        elif type(node) is str:
            if len(node) > 16_384:
                raise PilotError('string limit')
        elif node is not None and type(node) not in (bool, int):
            raise PilotError('exact JSON scalar types required; floats unsupported')
        elif type(node) is int and not -(2**63) <= node < 2**63:
            raise PilotError('integer limit')
    inspect(value)
    raw = canonical(value)
    if len(raw) > limit:
        raise PilotError('canonical byte limit')
    return raw


def identity(domain, value, own_field):
    # The trailing file LF is not part of the established domain/content hash.
    material = {'domain': domain, 'content': {
        key: child for key, child in value.items() if key != own_field}}
    return 'sha256:' + hashlib.sha256(owned(material)[:-1]).hexdigest()


def seal(domain, value, own_field):
    value = json.loads(owned(value))
    value[own_field] = identity(domain, value, own_field)
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PilotError('duplicate JSON key')
        result[key] = value
    return result


def _nonfinite(_):
    raise PilotError('nonfinite JSON value')


def read_json(path, *, limit=REPORT_LIMIT):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise PilotError('symlink input forbidden')
    if not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size > limit:
        raise PilotError('bounded ordinary input file required')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    return parse_json(raw, limit=limit)


def parse_json(raw, *, limit=REPORT_LIMIT):
    if type(raw) is not bytes or len(raw) > limit:
        raise PilotError('bounded JSON bytes required')
    try:
        value = json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
        if owned(value, limit=limit) != raw:
            raise PilotError('canonical JSON bytes required')
        return value
    except (ValueError, UnicodeError, RecursionError) as error:
        raise PilotError(str(error)) from None


def exact(value, expected, *, limit=REPORT_LIMIT):
    """Exact fixed-plan reproduction, not prose entailment or classification."""
    raw = owned(value, limit=limit)
    if raw != owned(expected, limit=limit):
        raise PilotError('fixed authored contract or exact evidence binding mismatch')
    return raw


@dataclass(frozen=True, init=False)
class ReviewDocument:
    """Privately owned immutable bytes; all decoded views are independent."""
    _raw: bytes

    @classmethod
    def _verified(cls, value, *, limit):
        result = object.__new__(cls)
        object.__setattr__(result, '_raw', owned(value, limit=limit))
        return result

    def to_dict(self):
        return json.loads(self._raw)

    def to_json(self):
        return self._raw.decode('utf-8')


class InterpretationCandidate(ReviewDocument):
    """Pending authored interpretation; no KnowledgeFact or packet interface."""


class ReviewReport(ReviewDocument):
    """Computed presentation of the same seven pending proposals."""
