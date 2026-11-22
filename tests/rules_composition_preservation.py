"""Finite exact composition additions and reversible predecessor delegation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/rules_composition_v1/successors.json'
LEDGER_SHA256 = '0ebfef3ae46739a4e261daa71d350c2fd60c40fc5827c11ca8ac4cdba39dc49e'
BASE = '0d3f3a76b71b0bfbc0cb39b5f21dfae3cc6d06cd'
TREE = 'b49e2b383113e344b06522932074d0f4582d7432'
ADDITIONS = frozenset(('src/card_intelligence/rules_composition.py',
    'docs/RULES_REASONING_COMPOSITION_V1.md', 'tests/fixtures/rules_composition_v1/payment-pool.json'))
REPLACEMENTS = frozenset(('tests/rules_reasoning_preservation.py',))
UNCHANGED = frozenset(('src/card_intelligence/rules_reasoning.py','src/card_intelligence/mana_window.py',
    'src/probability/resource_assignment.py','src/probability/draw_access.py','src/probability/supplied_deck.py',
    'src/workbench/investigations.py','src/workbench/adapter.py','src/card_rules_pilot/land_context.py',
    'docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md',
    'docs/RESEARCH_LOG_ARCHITECTURE.md','VISION.md','.github/workflows/python-validation.yml',
    'scripts/ci_merge_tree.py'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact composition ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact composition scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized composition successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact composition edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary composition addition required')
    return True
