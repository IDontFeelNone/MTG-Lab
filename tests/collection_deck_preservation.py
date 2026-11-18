"""Exact integration successors; no historical bytes, pins or authority are replaced."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/collection_deck_analysis_v1/successors.json'
LEDGER_SHA256 = '3949aebfe05012cc01415b79c9fc65295862cf8e8f67cffd55b7bdb9480151b9'
ADDITIONS = frozenset(('src/collection/deck_analysis.py',
    'src/schemas/v1/collection-deck-analysis-input.schema.json',
    'src/schemas/v1/collection-deck-analysis-report.schema.json'))
REPLACEMENTS = frozenset(('src/collection/intelligence.py','src/mtglab/__main__.py',
    'tests/supplied_deck_preservation.py','tests/test_collection_intelligence.py'))


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact collection-deck compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != 'c935ed0aa78f278a6ea8ecac6e5e4d597aff114e'
            or value['tree'] != 'deeb4dcb211179eb6e4f67befed14738a7195f10'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact collection-deck compatibility scope required')
    return value


def preceding_bytes(name, raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    expected = ledger()['replacements'][name]
    if pin(raw) == expected['old'] or hashlib.sha256(raw).hexdigest() in expected['historical_sha256']:
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized collection-deck successor')
    for edit in reversed(expected['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact collection-deck delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != expected['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111):
        raise AssertionError('ordinary non-executable collection-deck source required')
    if pin(path.read_bytes()) != ledger()['additions'][name]:
        raise AssertionError('exact collection-deck source pin required')
    return True
