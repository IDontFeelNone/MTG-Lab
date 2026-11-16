"""Finite exact addition accounting; original inventories and pins stay intact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/semantic_closure_v1/source-successors.json'
LEDGER_SHA256 = 'c83b4b5ef48eb775eb0edeb66fa3ccee320aebf269d2f4535c5db7f496f6aa69'
ADDITIONS = frozenset(('src/card_intelligence/semantic_closure.py',
                       'src/card_intelligence/semantic_closure_policy.py'))
REPLACEMENTS = frozenset(('tests/pack_simulation_preservation.py', 'tests/overlay_preservation_support.py',
                          'tests/stack_ability_preservation.py'))


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact semantic-closure preservation ledger required')
    value = json.loads(raw)
    if (value['base'] != '6fde7c3df38245ee827eec2cd2900793945c9761'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact semantic-closure preservation scope required')
    return value


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name not in REPLACEMENTS: return raw
    pin = ledger()['replacements'][name]; digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256'] or digest in pin['historical_sha256']: return raw
    if digest != pin['new_sha256']: raise AssertionError('unreviewed semantic-closure preservation successor')
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
        raise AssertionError('ordinary non-executable semantic-closure addition required')
    pin = ledger()['additions'][name]; raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise AssertionError('exact semantic-closure addition pin required')
    return True
