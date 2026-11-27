"""One finite successor view; no historical ledger or authority is rebaselined."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/candidate_mana_v1/successors.json'
LEDGER_SHA256 = '96035ea5bab59fdc36d9b1d1a329e7c665ba9f63457ed7f13f42cdef39c24760'
BASE = '0569fe00615fdc5e2edc2052803c98dcf9e75bfb'
TREE = 'ad4f3f8d6168c351796e68174314b88a9d4bb777'
REPLACEMENTS = frozenset(('VISION.md', 'docs/GOVERNANCE.md', 'docs/ROADMAP.md',
    'docs/PROJECT_STATUS.md', 'PROJECT_INVENTORY.md', 'docs/PRIVATE_FACTUAL_ADMISSION_V1.md',
    'tests/factual_admission_preservation.py', 'tests/documentation_continuity_preservation.py',
    'tests/proactive_vision_preservation.py', 'tests/test_documentation_continuity.py',
    'tests/test_vision_alignment.py', 'tests/test_proactive_research_vision.py',
    'tests/test_factual_admission_preservation.py',
    'tests/test_collection_deck_preservation.py', 'tests/test_supplied_deck_preservation.py',
    'tests/test_pack_odds_preservation.py', 'tests/test_resource_assignment_preservation.py',
    'tests/test_private_mtgjson_preservation.py', 'tests/test_release_reconciliation_preservation.py',
    'tests/test_rules_composition_preservation.py', 'tests/test_rules_reasoning_preservation.py'))
ADDITIONS = frozenset(('src/card_intelligence/candidate_mana.py', 'docs/CANDIDATE_ACTIVATED_MANA_V1.md'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact candidate interpretation successor ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE or
            set(value['replacements']) != REPLACEMENTS or set(value['additions']) != ADDITIONS):
        raise AssertionError('exact candidate interpretation scope required')
    return value


def preceding_bytes(name, raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:
        return raw
    row = ledger()['replacements'][name]
    if pin(raw) == row['old'] or pin(raw) in row['ancestors']:
        return raw
    if pin(raw) != row['new']:
        raise AssertionError('unrecognized candidate interpretation successor')
    edit = row['edit']
    start, end = edit['start'], edit['end']
    if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
        raise AssertionError('exact candidate interpretation edit required')
    old = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(old) != row['old']:
        raise AssertionError('exact candidate interpretation predecessor required')
    return old


def is_addition(path, root=ROOT):
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS:
        return False
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or path.stat().st_mode & 0o111 or pin(path.read_bytes()) != ledger()['additions'][name]):
        raise AssertionError('exact ordinary candidate interpretation addition required')
    return True
