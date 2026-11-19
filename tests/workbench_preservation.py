"""Exact, reversible application additions; original historical pins are unchanged."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/local_workbench_v1/successors.json'
LEDGER_SHA256 = '7c83b47659a33b09baacd0434ff81806b9dd3e7a3a087c460b66b6dde6ab1515'
BASE = '6d76c45fbb46198b01d1e2069dbd909365592e3e'
TREE = 'ea3934dc172ed17ccc3fbcbf59bab6fde32efae4'
ADDITIONS = frozenset(('src/workbench/__init__.py','src/workbench/__main__.py',
    'src/workbench/adapter.py','src/workbench/server.py','src/workbench/assets/index.html',
    'src/workbench/assets/app.js','src/workbench/assets/app.css','docs/LOCAL_DECK_WORKBENCH_V1.md'))
REPLACEMENTS = frozenset(('tests/collection_deck_preservation.py',))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact workbench compatibility ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS):
        raise AssertionError('exact workbench compatibility scope required')
    return value


def preceding_bytes(name, raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized workbench successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact workbench edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary non-executable workbench addition required')
    return True
