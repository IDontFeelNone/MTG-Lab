"""Exact finite reasoning successor; historical rules and source pins survive."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/rules_reasoning_v1/successors.json'
LEDGER_SHA256 = '747750e5698fd6efda6cd44459135458dcae0238aea1e8cae611af3bea1fc25d'
BASE = '8d9468482461dc5c1ebca44aee44c24e38a48d7f'
TREE = '0fa00199e092fa7bdf17f5de73d8a14871282552'
ADDITIONS = frozenset(('src/card_intelligence/rules_reasoning.py',
    'src/schemas/v1/real-card-rules-reasoning-input.schema.json',
    'docs/REAL_CARD_RULES_REASONING_V1.md', 'tests/fixtures/rules_reasoning_v1/payment.json'))
REPLACEMENTS = frozenset(('tests/release_reconciliation_preservation.py',))
UNCHANGED = frozenset(('docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md',
    'VISION.md','docs/RESEARCH_LOG_ARCHITECTURE.md','.github/workflows/python-validation.yml',
    'src/card_rules_pilot/land_context.py','src/card_rules_pilot/behavior_policy.py',
    'src/card_intelligence/mana_window.py','src/card_intelligence/semantic_closure.py'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact rules reasoning ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE or set(value['additions']) != ADDITIONS
            or set(value['replacements']) != REPLACEMENTS or set(value['unchanged']) != UNCHANGED):
        raise AssertionError('exact rules reasoning scope required')
    return value


def preceding_bytes(name, raw):
    from rules_composition_preservation import preceding_bytes as composition_preceding
    raw = composition_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS: return raw
    row = ledger()['replacements'][name]
    if pin(raw) == row['old']: return raw
    if pin(raw) != row['new']:
        raise AssertionError('unrecognized rules reasoning successor')
    for edit in reversed(row['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact rules reasoning edit required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != row['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from rules_composition_preservation import is_addition as composition_addition
    if composition_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(path.read_bytes()) != ledger()['additions'][name]):
        raise AssertionError('exact ordinary rules reasoning addition required')
    return True
