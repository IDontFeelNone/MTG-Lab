"""Exact additive activation seam; no historical permission/source byte changes."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/private_activation_v1/successors.json'
LEDGER_SHA256='d1cb7baf0baecf0150ca2d79c8f816213434e503a2dcb530bdb51b3ccb72d0d4'
BASE='69f9a2c9de6d8e1abce5a13e131438568262335d'
TREE='ba42c4eccbd64ddfb88f70f5c94b746d1012365c'
ADDITIONS=frozenset(('src/providers/mtgjson/private_activation.py',
    'src/schemas/v1/private-mtgjson-activation-plan.schema.json',
    'docs/PRIVATE_MTGJSON_ACTIVATION_V1.md'))
REPLACEMENTS=frozenset(('tests/private_mtgjson_preservation.py',))
UNCHANGED=frozenset(('src/providers/mtgjson/private_import.py','src/providers/mtgjson/private_policy.py',
    'src/providers/mtgjson/reconciliation.py','src/providers/mtgjson/mapper.py',
    'src/providers/mtgjson/streaming.py','src/providers/mtgjson/validator.py',
    'src/ingestion/set_preparation.py','src/probability/draw_access.py',
    'src/card_intelligence/rules_reasoning.py','src/card_intelligence/rules_composition.py',
    'docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    '.github/workflows/python-validation.yml','scripts/ci_merge_tree.py',
    'tests/fixtures/private_mtgjson_v1/successors.json',
    'reference-reviews/v13-legacy-profile-permission-closure/permission-matrix.json'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact activation ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact activation scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized activation successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact activation edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact activation predecessor required')
    return raw


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary activation addition required')
    return True
