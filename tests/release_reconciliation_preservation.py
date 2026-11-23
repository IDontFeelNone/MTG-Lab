"""Finite additive reconciliation scope; every predecessor pin stays intact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/release_reconciliation_v1/successors.json'
LEDGER_SHA256 = '602ab5215846e6047fbfcd7a3e98488047b8a6baf648ddb70f8891bbb7a5fb1d'
BASE = 'c1b2826ea3a80fdead9570c444e1d56f1f46c0ad'
TREE = '3359eaae6283325a8d75059b7284d91ea5a15ae5'
ADDITIONS = frozenset(('src/providers/mtgjson/reconciliation.py',
    'src/schemas/v1/release-catalog-reconciliation-report.schema.json',
    'docs/RELEASE_CATALOG_RECONCILIATION_V1.md',
    'tests/fixtures/release_reconciliation_v1/original-release.json'))
REPLACEMENTS = frozenset(('tests/ci_workflow_preservation.py',))
UNCHANGED = frozenset(('src/providers/mtgjson/streaming.py','src/providers/mtgjson/mapper.py',
    'src/providers/mtgjson/validator.py','src/providers/mtgjson/execution.py',
    'src/dataset_import/framework.py','src/ingestion/set_preparation.py',
    'docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    '.github/workflows/python-validation.yml'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact reconciliation ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE or set(value['additions']) != ADDITIONS
            or set(value['replacements']) != REPLACEMENTS or set(value['unchanged']) != UNCHANGED):
        raise AssertionError('exact reconciliation scope required')
    return value


def preceding_bytes(name, raw):
    from rules_reasoning_preservation import preceding_bytes as reasoning_preceding
    raw = reasoning_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS: return raw
    row = ledger()['replacements'][name]
    if pin(raw) == row['old']: return raw
    if pin(raw) != row['new']:
        raise AssertionError('unrecognized reconciliation successor')
    for edit in reversed(row['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact reconciliation edit required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != row['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from rules_reasoning_preservation import is_addition as reasoning_addition
    if reasoning_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    from private_mtgjson_preservation import preceding_bytes as private_preceding
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(private_preceding(name,path.read_bytes())) != ledger()['additions'][name]):
        raise AssertionError('exact ordinary reconciliation addition required')
    return True
