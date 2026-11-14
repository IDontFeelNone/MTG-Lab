"""Exact reversible source deltas; no runtime permission or historical repinning."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/canonical_import_recovery/source-successors.json'
LEDGER_SHA256 = '5174406ccb2ea36cc7f7f20fe13abc2c7648e674322d424e6bb0c1238cc4f1f0'
PATHS = frozenset(('src/repository/canonical.py', 'tests/turn_structure_preservation.py'))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact canonical import recovery ledger required')
    value = json.loads(raw)
    if value['base'] != 'ae1c8d2a8880f4fc5d5174650e5fe5f258b4e913' or set(value['replacements']) != PATHS:
        raise AssertionError('exact bounded canonical import source paths required')
    return value


def preceding_bytes(name, raw):
    if type(raw) is not bytes:
        raise AssertionError('exact source bytes required')
    if name not in PATHS:
        return raw
    pin = ledger()['replacements'][name]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256']:
        return raw
    if digest != pin['new_sha256']:
        raise AssertionError('unreviewed canonical import successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode():
            raise AssertionError('exact canonical import delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact canonical import predecessor required')
    return raw
