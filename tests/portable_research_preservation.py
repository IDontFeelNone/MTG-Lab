"""Exact finite successor for portable research; original pins stay unchanged."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/portable_research_v1/successors.json'
LEDGER_SHA256 = 'c7aba41b404be611cc955fa83eed41d3971d2b08e2f6a280762e2c6b338583ed'
BASE = '4649c7ddef44978c67f876f095788cc162ad38a2'
TREE = '6107d4e0d28b9cb9b94e703d0ca2f2feb6b7592c'
ADDITIONS = frozenset((
    'src/workbench/investigations.py', 'src/workbench/research.py', 'src/workbench/research_example.py',
    'src/workbench/assets/research-panel.html', 'src/workbench/assets/research.js', 'src/workbench/assets/research.css',
    'src/schemas/v1/portable-deck-investigation.schema.json', 'docs/PORTABLE_DECK_RESEARCH_V1.md',
    'tests/fixtures/portable_research_v1/example-investigation.json',
    'tests/fixtures/portable_research_v1/example-handoff.txt'))
REPLACEMENTS = frozenset(('tests/set_preparation_preservation.py',))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact portable research ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE or set(value['additions']) != ADDITIONS
            or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact portable research scope required')
    return value


def preceding_bytes(name, raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    row = ledger()['replacements'][name]
    if pin(raw) == row['old']:
        return raw
    if pin(raw) != row['new']:
        raise AssertionError('unrecognized portable research successor')
    for edit in reversed(row['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact portable research edit required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != row['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS:
        return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(path.read_bytes()) != ledger()['additions'][name]):
        raise AssertionError('exact ordinary portable research addition required')
    return True
