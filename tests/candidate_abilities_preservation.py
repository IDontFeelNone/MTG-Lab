"""Finite pinned segmentation successor; no historical ledger is rebaselined."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/candidate_abilities_v1/successors.json'
LEDGER_SHA256 = '60d6111c03182098e386a3aa6ff7f12dffb3424dd0bc1a70abbd74b6c3ed4c38'
BASE = 'c26d4517af58c326b6568618d8b501bf6c6ae697'
TREE = '0af5e2cc919468d7dac48ca9821882fab2c77326'
REPLACEMENTS = frozenset(('PROJECT_INVENTORY.md','docs/ROADMAP.md','docs/PROJECT_STATUS.md',
    'tests/candidate_mana_preservation.py','tests/test_candidate_mana_preservation.py'))
ADDITIONS = frozenset(('src/card_intelligence/candidate_abilities.py',
    'docs/CANDIDATE_ABILITY_SEGMENTATION_V1.md','tests/test_candidate_abilities.py',
    'tests/test_candidate_abilities_preservation.py','tests/fixtures/candidate_abilities_v1/passages.json'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact segmentation successor ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['replacements'])!=REPLACEMENTS
        or set(value['additions'])!=ADDITIONS):
        raise AssertionError('exact segmentation scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old'] or pin(raw) in row['ancestors']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized segmentation successor')
    edit=row['edit'];start,end=edit['start'],edit['end']
    if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
        raise AssertionError('exact segmentation edit required')
    old=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(old)!=row['old']:raise AssertionError('exact segmentation predecessor required')
    return old


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
        or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary segmentation addition required')
    return True
