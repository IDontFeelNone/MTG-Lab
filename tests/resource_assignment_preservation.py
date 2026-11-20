"""Finite exact resource-analysis additions and CLI successor; test-only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/resource_assignment_v1/successors.json'
LEDGER_SHA256 = '0f5b49fb78d2798749c31cd4acbd73896eb430b246a58523c98a45597a1ca726'
BASE = 'b8311cb060a3ac2ba09ae0d02d8a86e86cde3397'
TREE = '6c574de11b137df14e9f31db06d134b41324231a'
ADDITIONS = frozenset(('src/probability/resource_assignment.py', 'docs/DECLARED_RESOURCE_ASSIGNMENT_V1.md'))
REPLACEMENTS = frozenset(('src/probability/__main__.py', 'tests/workbench_preservation.py', 'tests/test_supplied_deck_preservation.py'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact resource-assignment compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE or set(value['additions']) != ADDITIONS
            or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact resource-assignment compatibility scope required')
    return value


def preceding_bytes(name, raw):
    from set_preparation_preservation import preceding_bytes as set_preceding
    raw = set_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    row = ledger()['replacements'][name]
    if pin(raw) == row['old'] or pin(raw) in row['historical']:
        return raw
    if pin(raw) != row['new']:
        raise AssertionError('unrecognized resource-assignment successor')
    for edit in reversed(row['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact resource-assignment edit required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != row['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from set_preparation_preservation import is_addition as set_addition
    if set_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS:
        return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(path.read_bytes()) != ledger()['additions'][name]):
        raise AssertionError('exact ordinary non-executable resource-analysis addition required')
    return True
