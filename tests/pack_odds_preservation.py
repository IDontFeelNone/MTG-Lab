"""Exact odds-only successors; all predecessor pins and historical bytes survive."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/pack_target_odds_v1/successors.json'
LEDGER_SHA256 = 'c195d944bb7fa672207d476de919da721ec30ca901e896adcc0ca4269a0de946'
ADDITIONS = frozenset(('src/probability/pack_odds.py',))
REPLACEMENTS = frozenset(('src/simulation/pack.py', 'src/probability/__main__.py',
                          'tests/draw_access_preservation.py', 'tests/test_draw_access_preservation.py'))


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact pack-odds compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != '848cf56228685f8d8dd117ba37d9e3df0f6db36a'
            or value['tree'] != '15f5d44a1b467030f44a4bed5fd526ba2a4880f9'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact pack-odds compatibility scope required')
    return value


def preceding_bytes(name, raw):
    from supplied_deck_preservation import preceding_bytes as supplied_preceding
    raw = supplied_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    expected = ledger()['replacements'][name]
    if pin(raw) == expected['old'] or hashlib.sha256(raw).hexdigest() in expected['historical_sha256']:
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized pack-odds successor')
    for edit in reversed(expected['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact pack-odds delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != expected['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from supplied_deck_preservation import is_addition as supplied_addition
    if supplied_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111):
        raise AssertionError('ordinary non-executable pack-odds source required')
    if pin(path.read_bytes()) != ledger()['additions'][name]:
        raise AssertionError('exact pack-odds source pin required')
    return True
