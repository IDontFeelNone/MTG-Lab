"""Finite test-only set preparation additions and exact predecessor restoration."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/set_preparation_v1/successors.json'
LEDGER_SHA256='41c0375340930dbc0fdd95165a264171b7c187d0658d0f2735d2e03faf6b1126'
BASE='d8f5b6fd5fa107749bb7da7fbb1e04cebc148206'
TREE='1b15c6e6c9c43eceb8222503e403e6970bad3c58'
ADDITIONS=frozenset(('src/ingestion/set_preparation.py','docs/SET_CANDIDATE_PREPARATION_V1.md'))
REPLACEMENTS=frozenset(('tests/resource_assignment_preservation.py',))
def pin(raw):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise AssertionError('exact set preparation ledger required')
    value=json.loads(raw)
    if value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS or set(value['replacements'])!=REPLACEMENTS:
        raise AssertionError('exact set preparation scope required')
    return value
def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:raise AssertionError('exact named bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized set preparation successor')
    for edit in reversed(row['edits']):
        a,b=edit['start'],edit['end']
        if hashlib.sha256(raw[a:b]).hexdigest()!=edit['new_sha256']:raise AssertionError('exact set preparation edit required')
        raw=raw[:a]+edit['old'].encode()+raw[b:]
    if pin(raw)!=row['old']:raise AssertionError('exact historical predecessor required')
    return raw
def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file() or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]:
        raise AssertionError('exact ordinary set preparation addition required')
    return True
