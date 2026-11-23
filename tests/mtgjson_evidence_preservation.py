"""Exact reversible successors only; historical pins and authority are preserved."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/mtgjson_evidence_v1/successors.json'
LEDGER_SHA256='5dcb1c67983f0982a8171f9a2dce8148fbee830bde83ea998e1976c5e28fe616'
BASE='3e564772dfdb6473aac11f906c636c4547d17f2b'
TREE='420e5d9d3f464f0803261f0d531c259766bd593d'
ADDITIONS=frozenset(('src/providers/mtgjson/oracle_evidence.py',
    'src/schemas/v1/private-mtgjson-oracle-import-report.schema.json',
    'docs/MTGJSON_EVIDENCE_PROJECTION_V1.md'))
REPLACEMENTS=frozenset(('src/providers/mtgjson/private_policy.py',
    'src/providers/mtgjson/private_import.py','src/providers/mtgjson/reconciliation.py',
    'src/card_intelligence/mechanics.py','tests/private_activation_preservation.py',
    'tests/private_mtgjson_preservation.py','tests/test_private_activation_preservation.py',
    'tests/validation_performance_preservation.py','tests/query_attachment_performance_preservation.py',
    'tests/test_ci_workflow_preservation.py'))
UNCHANGED=frozenset(('docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    'src/providers/mtgjson/private_activation.py','src/providers/mtgjson/mapper.py',
    'src/providers/mtgjson/streaming.py','src/providers/mtgjson/validator.py',
    'src/ingestion/set_preparation.py','src/probability/draw_access.py',
    'src/card_intelligence/rules_reasoning.py','src/card_intelligence/rules_composition.py',
    'src/schemas/v1/private-mtgjson-import-report.schema.json',
    'tests/fixtures/private_activation_v1/successors.json',
    'tests/fixtures/private_mtgjson_v1/successors.json',
    '.github/workflows/python-validation.yml','scripts/ci_merge_tree.py',
    'reference-reviews/v13-legacy-profile-permission-closure/permission-matrix.json'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact Oracle evidence successor ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact Oracle evidence scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old']:return raw
    # Older owning adapters may pass their already reconstructed ancestor.
    if pin(raw) in row.get('ancestors',[]):return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized Oracle evidence successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact Oracle evidence edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact Oracle evidence predecessor required')
    return raw


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary Oracle evidence addition required')
    return True
