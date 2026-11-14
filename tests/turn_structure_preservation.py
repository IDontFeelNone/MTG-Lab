"""Finite exact V2 source successors; all historical bytes remain pinned."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/turn_structure_v2/source-successors.json'
LEDGER_SHA256 = '0374d89b29489db3806b0ad6fcc5861e37d720837f4e4a3ecaaf08034f8618e3'
REPLACEMENT_PATHS = frozenset(('src/gameplay_rules/engine.py', 'src/gameplay_rules/models.py', 'src/gameplay_rules/session.py', 'tests/turn_lifecycle_preservation.py'))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact turn-structure ledger required')
    return json.loads(raw)


def preceding_bytes(name, raw):
    from canonical_import_recovery_preservation import preceding_bytes as import_preceding
    raw = import_preceding(name, raw)
    if type(raw) is not bytes:
        raise AssertionError('exact source bytes required')
    if name not in REPLACEMENT_PATHS:
        return raw
    pin = ledger()['replacements'][name]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256']:
        return raw
    if digest != pin['new_sha256']:
        raise AssertionError('unreviewed turn-structure successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode():
            raise AssertionError('exact turn-structure delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact turn-structure predecessor required')
    return raw
