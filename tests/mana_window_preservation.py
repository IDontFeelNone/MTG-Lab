"""Finite exact addition accounting; original inventories and pins stay intact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/mana_window_v1/source-successors.json'
LEDGER_SHA256 = '814944bb1c293b68be71b16a322bca4de3fd906d1ce331cf9aeb2e144dfdf4c0'
ADDITIONS = frozenset(('src/card_intelligence/mana_window.py',))
REPLACEMENTS = frozenset(('tests/semantic_closure_preservation.py',))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact mana-window preservation ledger required')
    value = json.loads(raw)
    if (value['base'] != 'a039baa62377283b950cf64a9078dc3bb34ec07c'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact mana-window preservation scope required')
    return value


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name not in REPLACEMENTS: return raw
    pin = ledger()['replacements'][name]; digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256'] or digest in pin['historical_sha256']: return raw
    if digest != pin['new_sha256']: raise AssertionError('unreviewed mana-window preservation successor')
    for edit in reversed(pin['edits']):
        a,b = edit['start'],edit['end']
        if raw[a:b] != edit['new'].encode(): raise AssertionError('exact preservation delta required')
        raw = raw[:a]+edit['old'].encode()+raw[b:]
    if hashlib.sha256(raw).hexdigest() != pin['old_sha256']:
        raise AssertionError('exact historical preservation predecessor required')
    return raw


def is_addition(path, root=ROOT):
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file() or path.stat().st_mode & 0o111:
        raise AssertionError('ordinary non-executable mana-window addition required')
    pin = ledger()['additions'][name]; raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise AssertionError('exact mana-window addition pin required')
    return True
