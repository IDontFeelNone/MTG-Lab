"""Finite exact session additions; the existing gameplay kernel is unchanged."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/gameplay_session_v0/source-successors.json'
LEDGER_SHA256='782629828b7823369c358b01df1ee88e3ef3090661232d9f92c783ce618867e4'
ADDITION_PATHS=frozenset(('src/gameplay_rules/session.py','src/gameplay_rules/session_cli.py'))


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256: raise AssertionError('exact session source ledger required')
    return json.loads(raw)


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name!='tests/variant_simulation_preservation.py': return raw
    pin=ledger()['replacements'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==pin['old_sha256']: return raw
    if digest!=pin['new_sha256']: raise AssertionError('unreviewed session successor: exact authorized pin required')
    old=raw
    for edit in reversed(pin['edits']):
        a,b=edit['start'],edit['end']
        if old[a:b]!=edit['new'].encode(): raise AssertionError('exact session delta required')
        old=old[:a]+edit['old'].encode()+old[b:]
    if hashlib.sha256(old).hexdigest()!=pin['old_sha256']: raise AssertionError('exact session predecessor required')
    return old


def is_addition(path, root):
    name=path.relative_to(root).as_posix()
    if name not in ADDITION_PATHS: return False
    if path.is_symlink() or path.stat().st_mode & 0o111: raise AssertionError('unsupported session source mode')
    raw=path.read_bytes();pin=ledger()['additions'][name]
    if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise AssertionError('exact session source addition required')
    return True
