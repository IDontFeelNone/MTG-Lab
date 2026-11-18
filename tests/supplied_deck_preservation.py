"""Exact supplied-deck successors; historical pins and bytes remain authoritative."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/supplied_deck_consistency_v1/successors.json'
LEDGER_SHA256 = '0703ef4afbc95d0ac0877807236e967a1b4e54c374fd7ed2cc768ef96004d019'
ADDITIONS = frozenset(('src/probability/supplied_deck.py',
    'src/schemas/v1/supplied-deck-consistency-input.schema.json',
    'src/schemas/v1/supplied-deck-consistency-report.schema.json'))
REPLACEMENTS = frozenset(('src/probability/__main__.py', 'tests/pack_odds_preservation.py',
                          'tests/test_pack_odds_preservation.py'))


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact supplied-deck compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != 'de02981b3e859fac401ac79741a35a1fcbe0db3b'
            or value['tree'] != 'e5aef755e736cf244e9ecf00136032be419c35a5'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact supplied-deck compatibility scope required')
    return value


def preceding_bytes(name, raw):
    from collection_deck_preservation import preceding_bytes as integration_preceding
    raw = integration_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    expected = ledger()['replacements'][name]
    if pin(raw) == expected['old'] or hashlib.sha256(raw).hexdigest() in expected['historical_sha256']:
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized supplied-deck successor')
    for edit in reversed(expected['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact supplied-deck delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != expected['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from collection_deck_preservation import is_addition as integration_addition
    if integration_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111):
        raise AssertionError('ordinary non-executable supplied-deck source required')
    if pin(path.read_bytes()) != ledger()['additions'][name]:
        raise AssertionError('exact supplied-deck source pin required')
    return True
