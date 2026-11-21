"""Finite reversible CI successors. Historical bytes and original pins remain."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/ci_workflow_v1/successors.json'
LEDGER_SHA256 = 'b5a31080d71a874532f11383b6b9c06af40168996106a786941dedfa08698af9'
BASE = '59ccc66952e6683eb8558651e6c949b583112060'
TREE = 'd7df92987b9e2056e7cadb8bfb593c582f827fba'
ADDITIONS = frozenset(('scripts/ci_merge_tree.py', 'docs/CI_WORKFLOW_EFFICIENCY_V1.md'))
REPLACEMENTS = frozenset(('.github/workflows/python-validation.yml',
                          'tests/portable_research_preservation.py', 'tests/test_land_preservation.py',
                          'tests/query_attachment_performance_preservation.py'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact CI workflow ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS):
        raise AssertionError('exact CI workflow scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized CI workflow successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact CI workflow edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact historical CI predecessor required')
    return raw


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary CI workflow addition required')
    return True
