"""Finite test-only addition accounting; inherited evidence and pins stay intact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/draw_access_v1/successors.json'
LEDGER_SHA256 = 'b9805847403bd97cd42a081123cc59032e5c516c2ffe62526ef640912a16ec16'
ADDITIONS = frozenset(('src/probability/draw_access.py', 'src/probability/__main__.py'))
REPLACEMENTS = frozenset(('tests/validation_performance_preservation.py',
                          'tests/documentation_continuity_preservation.py',
                          'tests/test_rules_card_integration_design.py',
                          'tests/test_context_review_authorization_design.py',
                          'tests/test_shared_proposal_legality_preservation.py'))


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact draw-access compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != '75cd68ca86a533b4a8f0fef52e260f06daed88fd'
            or value['tree'] != '5a4240d6bde7e9c2676b2ddbf951def8b382bd74'
            or set(value['additions']) != ADDITIONS or set(value['replacements']) != REPLACEMENTS):
        raise AssertionError('exact draw-access compatibility scope required')
    return value


def preceding_bytes(name, raw):
    from pack_odds_preservation import preceding_bytes as odds_preceding
    raw = odds_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name not in REPLACEMENTS:
        return raw
    expected = ledger()['replacements'][name]
    if pin(raw) == expected['old'] or hashlib.sha256(raw).hexdigest() in expected['historical_sha256']:
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized draw-access successor')
    for edit in reversed(expected['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact approved draw-access delta required')
        raw = raw[:start] + edit['old'].encode() + raw[end:]
    if pin(raw) != expected['old']:
        raise AssertionError('exact historical predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from pack_odds_preservation import is_addition as odds_addition
    if odds_addition(path, root): return True
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS:
        return False
    if (any(p.is_symlink() for p in (path, *path.parents))
            or not path.is_file() or path.stat().st_mode & 0o111):
        raise AssertionError('ordinary non-executable draw-access source required')
    from pack_odds_preservation import preceding_bytes as odds_preceding
    if pin(odds_preceding(name, path.read_bytes())) != ledger()['additions'][name]:
        raise AssertionError('exact draw-access source pin required')
    return True
