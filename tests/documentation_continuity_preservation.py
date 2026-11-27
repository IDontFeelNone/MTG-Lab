"""Exact test-only successors for the owner-approved documentation milestone.

Only five complete document prefixes and the named compatibility insertions reverse.
Historical hashes, suffixes and the predecessor validators remain authoritative.
This module grants no source, gameplay, admission or runtime permission.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '954592cd25e0e29c7d4d2764cad27f77a193a05b'
TREE = 'effe6749579bee6a61075bf01de3673491cccd21'
LEDGER = ROOT / 'tests/fixtures/documentation_continuity_v1/successors.json'
LEDGER_SHA256 = '1028116c72b31751ac6e4aba4d5ae4fe477d43264b928225603f332fb0985057'
DOCUMENTS = frozenset(('README.md', 'PROJECT_INVENTORY.md', 'docs/HANDOFF.md',
                       'docs/ROADMAP.md', 'docs/PROJECT_STATUS.md'))
HELPERS = frozenset(('tests/proposed_spell_packet_analysis_preservation.py',
                     'tests/mana_window_preservation.py',
                     'tests/test_land_decision_preservation.py',
                     'tests/test_gameplay_rules_bounded_activated_ability_preservation.py',
                     'tests/casting_permission_family_preservation.py',
                     'tests/proposed_spell_evidence_packet_preservation.py',
                     'tests/proposed_spell_packet_authoring_preservation.py'))


def _pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ledger():
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError('exact documentation compatibility ledger required')
    value = json.loads(raw)
    if (value['base'] != BASE or value['tree'] != TREE
            or set(value['replacements']) != DOCUMENTS | HELPERS):
        raise AssertionError('exact documentation compatibility scope required')
    return value


def restore(name, raw):
    """Accept only an exact approved successor or its exact main predecessor."""
    from candidate_mana_preservation import preceding_bytes as candidate_preceding
    raw = candidate_preceding(name, raw)
    if type(name) is not str or name not in DOCUMENTS | HELPERS or type(raw) is not bytes:
        raise AssertionError('only named documentation compatibility bytes are accepted')
    pin = ledger()['replacements'][name]
    if _pin(raw) == pin['old']:
        return raw
    if _pin(raw) != pin['new']:
        raise AssertionError('unrecognized documentation successor')
    for edit in reversed(pin['edits']):
        start, end = edit['start'], edit['end']
        if raw[start:end] != edit['new'].encode('utf-8'):
            raise AssertionError('exact documentation delta required')
        raw = raw[:start] + edit['old'].encode('utf-8') + raw[end:]
    if _pin(raw) != pin['old']:
        raise AssertionError('exact historical documentation predecessor required')
    return raw


def preceding_bytes(name, raw):
    """Compose before old source validators; never admit an unknown source.

    Older, smaller historical versions still pass to their existing exact-pinned
    validators. This lane cannot exempt any file from those assertions.
    """
    from draw_access_preservation import preceding_bytes as draw_preceding
    raw = draw_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    if name in HELPERS and len(raw) >= ledger()['replacements'][name]['old']['bytes']:
        return restore(name, raw)
    return raw
