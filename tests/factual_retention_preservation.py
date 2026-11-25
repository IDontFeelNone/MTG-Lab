"""Finite exact reversible successors; no permission or historical rebaseline."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT/'tests/fixtures/factual_limited_retention_v1/successors.json'
LEDGER_SHA256 = 'a4480afaaf3ae033c1c1ffc36e7d98dab6d2b4686042458c2214c58d44847be6'
BASE = '80305c7595c6978753571df5dea7b80e1f51b3b9'
TREE = '80760bcbd5dfcd2f5c24f8d23c270df9c6d8e747'
ADDITIONS = frozenset(('src/providers/mtgjson/factual_retention.py',
    'src/schemas/v1/private-mtgjson-factual-limited-report.schema.json',
    'src/schemas/v1/private-mtgjson-activation-plan-v2.schema.json',
    'docs/FACTUAL_LIMITED_RETENTION_V1.md'))
REPLACEMENTS = frozenset(('src/providers/mtgjson/private_policy.py',
    'src/providers/mtgjson/private_import.py','src/providers/mtgjson/private_activation.py',
    'src/providers/mtgjson/reconciliation.py','docs/PRIVATE_MTGJSON_IMPORT_V1.md',
    'tests/mtgjson_evidence_preservation.py','tests/private_activation_preservation.py',
    'tests/test_mtgjson_evidence_preservation.py'))
UNCHANGED = frozenset(('docs/ARCHITECTURE.md','docs/DECISIONS.md','docs/GOVERNANCE.md','VISION.md',
    'reference-reviews/v13-legacy-profile-permission-closure/permission-matrix.json',
    'src/providers/mtgjson/oracle_evidence.py','src/card_intelligence/mechanics.py',
    'src/providers/mtgjson/mapper.py','src/providers/mtgjson/streaming.py','src/providers/mtgjson/validator.py',
    'src/card_intelligence/rules_reasoning.py','src/card_intelligence/rules_composition.py',
    'src/probability/draw_access.py','src/probability/supplied_deck.py',
    'src/schemas/v1/private-mtgjson-import-report.schema.json',
    'src/schemas/v1/private-mtgjson-activation-plan.schema.json',
    'src/schemas/v1/private-mtgjson-oracle-import-report.schema.json',
    'tests/fixtures/mtgjson_evidence_v1/successors.json',
    'tests/fixtures/private_activation_v1/successors.json','tests/fixtures/private_mtgjson_v1/successors.json',
    '.github/workflows/python-validation.yml','scripts/ci_merge_tree.py'))


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ledger():
    raw=LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:
        raise AssertionError('exact factual retention ledger required')
    value=json.loads(raw)
    if (value['base']!=BASE or value['tree']!=TREE or set(value['additions'])!=ADDITIONS
            or set(value['replacements'])!=REPLACEMENTS or set(value['unchanged'])!=UNCHANGED):
        raise AssertionError('exact factual retention scope required')
    return value


def preceding_bytes(name, raw):
    from standard_envelope_preservation import preceding_bytes as envelope_preceding
    raw = envelope_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named predecessor bytes required')
    if name not in REPLACEMENTS:return raw
    row=ledger()['replacements'][name]
    if pin(raw)==row['old'] or pin(raw) in row.get('ancestors',[]):return raw
    if pin(raw)!=row['new']:raise AssertionError('unrecognized factual retention successor')
    for edit in reversed(row['edits']):
        start,end=edit['start'],edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest()!=edit['new_sha256']:
            raise AssertionError('exact factual retention edit required')
        raw=raw[:start]+edit['old'].encode()+raw[end:]
    if pin(raw)!=row['old']:raise AssertionError('exact factual retention predecessor required')
    return raw


def is_addition(path, root=ROOT):
    from standard_envelope_preservation import is_addition as envelope_addition
    if envelope_addition(path, root):return True
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS:return False
    if (any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file()
            or path.stat().st_mode&0o111 or pin(path.read_bytes())!=ledger()['additions'][name]):
        raise AssertionError('exact ordinary factual retention addition required')
    return True
