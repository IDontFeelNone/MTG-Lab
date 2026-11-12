"""Exact finite V0.2 successors; no runtime or historical-evidence exemptions."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/pack_simulation_v02/source-successors.json'
LEDGER_SHA256='9d8640d524f84dea3da63aa12e3e9d1b27cd3b7da66d27f0c622bc9b2df9ff12'
REPLACEMENT_PATHS=frozenset(('src/canonical/__init__.py', 'src/canonical/models.py', 'src/repository/canonical.py', 'src/simulation/__init__.py', 'src/simulation/pack.py', 'tests/finish_simulation_preservation.py', 'tests/query_attachment_performance_preservation.py'))
ADDITION_PATHS=frozenset(('src/schemas/v3/pack-definition.schema.json',))


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256: raise AssertionError('exact variant successor ledger required')
    return json.loads(raw)


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    from gameplay_session_preservation import preceding_bytes as session_preceding
    raw = session_preceding(name, raw)
    if name not in REPLACEMENT_PATHS: return raw
    pin=ledger()['replacements'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==pin['old_sha256'] or digest in pin.get('historical_sha256',()): return raw
    if digest!=pin['new_sha256']: raise AssertionError('unreviewed variant successor: exact authorized pin required')
    old=raw
    for edit in reversed(pin['edits']):
        a,b=edit['start'],edit['end']
        if old[a:b]!=edit['new'].encode(): raise AssertionError('exact variant delta required')
        old=old[:a]+edit['old'].encode()+old[b:]
    if hashlib.sha256(old).hexdigest()!=pin['old_sha256']: raise AssertionError('exact variant predecessor required')
    return old


def is_addition(path, root):
    from gameplay_session_preservation import is_addition as session_addition
    if session_addition(path, root): return True
    name=path.relative_to(root).as_posix()
    if name not in ADDITION_PATHS: return False
    pin=ledger()['additions'][name]
    if path.is_symlink() or path.stat().st_mode & 0o111: raise AssertionError('unsupported variant source mode')
    raw=path.read_bytes()
    if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise AssertionError('exact variant addition required')
    return True
