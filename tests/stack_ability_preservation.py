"""Exact finite source successors; no relaxation of historical evidence pins."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/stack_abilities_v1/source-successors.json'
LEDGER_SHA256 = '5ede86c6667625ee44cbbe4cb7eb14f11aaaff0334746211229832f7e59fb5f9'
PATHS = frozenset(('src/gameplay_rules/engine.py', 'src/gameplay_rules/models.py', 'src/gameplay_rules/session.py', 'tests/draw_failure_preservation.py'))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact stack-ability source ledger required')
    value = json.loads(raw)
    if value['base'] != '2932a7f3e1714824989944453df3adbc1c67cbba' or set(value['replacements']) != PATHS:
        raise AssertionError('exact stack-ability predecessor scope required')
    return value


def preceding_bytes(name, raw):
    if type(raw) is not bytes:
        raise AssertionError('exact source bytes required')
    if name not in PATHS:
        return raw
    pin = ledger()['replacements'][name]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256'] or digest in pin['historical_sha256']:
        return raw
    if digest != pin['new_sha256']:
        raise AssertionError('unreviewed stack-ability successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode():
            raise AssertionError('exact stack-ability delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact stack-ability predecessor required')
    return raw
