"""Finite factual-admission successor view, without historical rebaselining.

Only individually pinned additions and reversible byte edits are recognized.
This helper grants no source-use, canonical admission or execution authority.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/factual_admission_v1/successors.json'
LEDGER_SHA256 = '92531fff5c1544406fc08061116985f5f78d6bff28b0794d4bfaeb882b521291'
BASE = 'fe4505f7e53f0a0bd4c6d237c4a5a4b1c2a0b32c'
TREE = '73e31ae612d447ac7bc6d82bb46e3e9f35f33f86'
REPLACEMENTS = frozenset(('src/query/engine.py','src/card_intelligence/mechanics.py',
    'tests/standard_envelope_preservation.py','tests/test_standard_envelope_preservation.py',
    'tests/test_factual_retention_preservation.py','tests/validation_performance_preservation.py',
    'tests/test_draw_access_preservation.py','tests/query_attachment_performance_preservation.py'))
ADDITIONS = frozenset(('src/canonical_import/mtgjson_factual.py',
    'src/repository/factual_snapshot.py','src/schemas/v1/private-factual-canonical-snapshot.schema.json',
    'docs/PRIVATE_FACTUAL_ADMISSION_V1.md'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact factual admission successor ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE
            or set(value['replacements'])!=REPLACEMENTS or set(value['additions'])!=ADDITIONS):
        raise AssertionError('exact factual admission scope required')
    return value


def preceding_bytes(name,raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old'] or pin(raw) in row['ancestors']:return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized factual admission successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact factual admission edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact factual admission predecessor required')
    return raw


def is_addition(path,root=ROOT):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary factual admission addition required')
    return True
