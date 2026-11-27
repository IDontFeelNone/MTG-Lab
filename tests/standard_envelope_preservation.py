"""Finite reversible Standard-envelope delta; no historical rebaseline."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/standard_envelope_v1/successors.json'
LEDGER_SHA256 = '85771bd4e31de0e6ecba8315ca24dae910ca38f8d4588970c64df09ff8cfaa14'
BASE = 'a949c5edd52eafbd31b06b00aabbe19d4519c4c3'
TREE = 'e4c83dcad31489be24e67a5a7ecd2daed067e7a0'
REPLACEMENTS = frozenset(('src/providers/mtgjson/reconciliation.py',
    'src/providers/mtgjson/private_import.py','src/providers/mtgjson/private_activation.py',
    'tests/factual_retention_preservation.py','tests/test_factual_retention_preservation.py'))
ADDITIONS = frozenset(('docs/MTGJSON_STANDARD_ENVELOPE_V1.md',))
UNCHANGED = frozenset(('docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    'PROJECT_INVENTORY.md',
    'reference-reviews/v13-legacy-profile-permission-closure/permission-matrix.json',
    'src/providers/mtgjson/private_policy.py','src/providers/mtgjson/factual_retention.py',
    'src/providers/mtgjson/oracle_evidence.py','src/providers/mtgjson/streaming.py',
    'src/providers/mtgjson/mapper.py','src/providers/mtgjson/validator.py',
    'src/card_intelligence/mechanics.py','src/card_intelligence/rules_reasoning.py',
    'src/card_intelligence/rules_composition.py','src/probability/draw_access.py',
    'src/probability/supplied_deck.py','.github/workflows/python-validation.yml',
    'scripts/ci_merge_tree.py','tests/fixtures/factual_limited_retention_v1/successors.json'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact Standard envelope ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['replacements'])!=REPLACEMENTS
            or set(value['additions'])!=ADDITIONS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact Standard envelope scope required')
    return value


def preceding_bytes(name,raw):
    from factual_admission_preservation import preceding_bytes as admission_preceding
    raw = admission_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old'] or pin(raw) in row['ancestors']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized Standard envelope successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact Standard envelope edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact Standard envelope predecessor required')
    return raw


def is_addition(path,root=ROOT):
    from factual_admission_preservation import is_addition as admission_addition
    if admission_addition(path, root):return True
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary Standard envelope addition required')
    return True
