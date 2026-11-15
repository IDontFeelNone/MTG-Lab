"""Exact finite source successors; no relaxation of historical evidence pins."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/draw_failure_v1/source-successors.json'
LEDGER_SHA256 = '890f626d95ae8f02534a28181a26b39d9254bcc036033de22f2a207904e52f70'
PATHS = frozenset(('src/gameplay_rules/engine.py', 'src/gameplay_rules/models.py', 'tests/canonical_import_recovery_preservation.py'))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact draw-failure source ledger required')
    value = json.loads(raw)
    if value['base'] != '63824571ee43673d77aff3822335779fa8b8b7ef' or set(value['replacements']) != PATHS:
        raise AssertionError('exact draw-failure predecessor scope required')
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
        raise AssertionError('unreviewed draw-failure successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode():
            raise AssertionError('exact draw-failure delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact draw-failure predecessor required')
    return raw
