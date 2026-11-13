"""Exact reversible lifecycle successors; never relax historical source checks."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/turn_lifecycle_v1/source-successors.json'
REPLACEMENT_PATHS = frozenset(('src/gameplay_rules/models.py', 'src/gameplay_rules/engine.py', 'src/gameplay_rules/session.py', 'tests/gameplay_session_preservation.py', 'tests/query_attachment_performance_preservation.py'))
LEDGER_SHA256 = '52316bf9c54ebf5b7202ac7fc6e5dcaed3a9130f6562ae3fc4332f0c022fa516'


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact lifecycle source ledger required')
    return json.loads(raw)


def preceding_bytes(name, raw):
    from turn_structure_preservation import preceding_bytes as structure_preceding
    raw = structure_preceding(name, raw)
    if type(raw) is not bytes:
        raise AssertionError('exact source bytes required')
    pin = ledger()['replacements'].get(name)
    if pin is None:
        return raw
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256']:
        return raw
    if digest != pin['new_sha256']:
        raise AssertionError('unreviewed lifecycle source successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode():
            raise AssertionError('exact lifecycle delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact lifecycle predecessor required')
    return raw
