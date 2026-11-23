"""Exact private-import successor; every historical ledger/hash remains unchanged."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'tests/fixtures/private_mtgjson_v1/successors.json'
LEDGER_SHA256='9c7db032d239568fecd7e322a7239ffdec8299fa0c3fbfefbf832ec5a2e74f1c'
BASE='fc652a99a9e53c05af9118f6ce7f7f4aebd4bf90'
TREE='b6eca7446b9c761b1960d24c642441b7a0c0cfc7'
ADDITIONS=frozenset(('src/providers/mtgjson/private_policy.py','src/providers/mtgjson/private_import.py',
    'src/schemas/v1/private-mtgjson-import-report.schema.json','docs/PRIVATE_MTGJSON_IMPORT_V1.md'))
REPLACEMENTS=frozenset(('src/providers/mtgjson/reconciliation.py',
    'tests/release_reconciliation_preservation.py','tests/rules_composition_preservation.py'))
UNCHANGED=frozenset(('src/providers/mtgjson/mapper.py','src/providers/mtgjson/parser.py',
    'src/providers/mtgjson/streaming.py','src/providers/mtgjson/validator.py',
    'src/providers/mtgjson/execution.py','src/ingestion/set_preparation.py',
    'src/card_intelligence/rules_reasoning.py','src/card_intelligence/rules_composition.py',
    'src/probability/draw_access.py','src/probability/supplied_deck.py',
    'docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    '.github/workflows/python-validation.yml','scripts/ci_merge_tree.py',
    'reference-reviews/v13-legacy-profile-permission-closure/permission-matrix.json'))


def pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact private-import ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact private-import scope required')
    return value


def preceding_bytes(name,raw):
    from private_activation_preservation import preceding_bytes as activation_preceding
    raw=activation_preceding(name,raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old'] or pin(raw) in row.get('ancestors',[]):return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized private-import successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact private-import edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact private-import predecessor required')
    return raw


def is_addition(path,root=ROOT):
    from private_activation_preservation import is_addition as activation_addition
    if activation_addition(path,root):return True
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary private-import addition required')
    return True
