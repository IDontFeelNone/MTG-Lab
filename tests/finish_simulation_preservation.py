"""Finite exact V0.1 source deltas; historical evidence is never repinned."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/pack_simulation_v01/source-successors.json'
LEDGER_SHA256 = '533f451c131df9e5268a2459cc47ce8105c9c92b69c95e28a5316f9c490471de'
REPLACEMENT_PATHS = frozenset(('src/canonical/models.py', 'src/query/engine.py', 'src/repository/canonical.py', 'src/repository/canonical_compatibility.py', 'src/simulation/__init__.py', 'src/simulation/pack.py', 'tests/pack_simulation_preservation.py', 'tests/query_attachment_performance_preservation.py'))


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact finish successor ledger required')
    return json.loads(raw)


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name not in REPLACEMENT_PATHS: return raw
    pin=ledger()['replacements'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==pin['old_sha256'] or digest in pin.get('historical_sha256', ()): return raw
    if digest!=pin['new_sha256']: raise AssertionError('unreviewed finish successor: exact authorized pin required')
    old=raw
    for edit in reversed(pin['edits']):
        a,b=edit['start'],edit['end']
        if old[a:b]!=edit['new'].encode(): raise AssertionError('exact finish delta required')
        old=old[:a]+edit['old'].encode()+old[b:]
    if hashlib.sha256(old).hexdigest()!=pin['old_sha256']:
        raise AssertionError('exact finish predecessor required')
    return old


def is_addition(path, root):
    name=path.relative_to(root).as_posix();pin=ledger()['additions'].get(name)
    if pin is None: return False
    if path.is_symlink() or path.stat().st_mode & 0o111: raise AssertionError('unsupported finish source mode')
    raw=path.read_bytes()
    if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise AssertionError('exact finish addition required')
    return True
