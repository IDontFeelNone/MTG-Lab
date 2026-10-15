"""Read-only legacy catalog census; emits review metadata, never a snapshot.

Only Git-tracked inputs are read. No source values, user records, network, writer,
attachment, approval or policy decision is produced. All output is to stdout.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROLES = ('CANONICAL_SNAPSHOT_CONTENT', 'CANONICAL_SNAPSHOT_CONTROL_METADATA',
    'SOURCE_EVIDENCE_PLANE', 'AUDIT_PROVENANCE_HISTORY', 'GENERATED_PERSISTENCE_INDEX',
    'TEMPORAL_MARKET_EVIDENCE', 'DERIVED_CARD_PRODUCT_DECISION_INTELLIGENCE',
    'PERSONAL_USER_DATA', 'HISTORICAL_TEST_REPLAY_FIXTURE', 'UNSUPPORTED_UNRESOLVED')
PERSONAL = ('data/collections', 'data/review/collection-audit-pilot')
INPUT_ROOTS = ('data', 'reference-reviews/mb2-reference-coverage',
    'reference-reviews/mb2-810-source-policy', 'reference-reviews/mb2-810-production-readiness',
    'tests/fixtures/historical_catalog', 'tests/fixtures/historical_replay')
FAMILY_ROLES = {
    'audit': ROLES[3], 'automatic_updates': ROLES[3], 'canonical': ROLES[0],
    'card_intelligence': ROLES[6], 'collections': ROLES[7], 'deck_requirements': ROLES[6],
    'evidence': ROLES[2], 'evidence-packages': ROLES[2], 'fixtures': ROLES[8],
    'intermediate': ROLES[9], 'knowledge': ROLES[6], 'market': ROLES[5],
    'observations': ROLES[2], 'processed': ROLES[4], 'production_runs': ROLES[2],
    'raw': ROLES[2], 'reference': ROLES[1], 'review': ROLES[8],
    'reviews': ROLES[3], 'sources': ROLES[2], 'validation': ROLES[8],
    # Isolated writer/publication rehearsal inputs, never production authority.
    'test-evidence': ROLES[8],
}
TYPED = {'card': 'cards/*/card.json', 'printing': 'printings/*/printing.json',
    'product': 'products/*/product.json', 'product_version': 'product_versions/*.json',
    'pack_definition': 'packs/*.json', 'slot': 'slots/*/slot.json',
    'print_sheet': 'print_sheets/*/print-sheet.json', 'finish': 'finishes/*.json',
    'rarity': 'rarities/*.json', 'treatment': 'treatments/*.json'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                       allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def tracked(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--', *INPUT_ROOTS],
                            check=True, stdout=subprocess.PIPE)
    paths = sorted(x.decode('utf-8') for x in result.stdout.split(b'\0') if x)
    for name in paths:
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or p.as_posix() != name:
            raise ValueError('unsafe tracked review path')
        target = root / name
        if not target.is_file() or any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError('missing or symlinked tracked input')
    return paths


def personal(name):
    return any(name == p or name.startswith(p + '/') for p in PERSONAL)


def role(name):
    if personal(name): return ROLES[7]
    if name.startswith('tests/fixtures/'): return ROLES[8]
    if name.startswith('reference-reviews/'): return ROLES[2]
    parts = PurePosixPath(name).parts
    family = parts[1]
    if family not in FAMILY_ROLES: raise ValueError('unclassified data family: ' + family)
    if family == 'canonical':
        if name.endswith('.gitkeep'): return ROLES[1]
        if 'sources' in parts: return ROLES[2]
        if parts[-1] in ('metadata.json', 'packs.json', 'slots.json'): return ROLES[1]
    if family == 'market' and parts[2] == 'acquisitions': return ROLES[2]
    if family == 'production_runs' and 'summaries' in parts: return ROLES[4]
    if family == 'card_intelligence' and parts[2] == 'demand': return ROLES[2]
    return FAMILY_ROLES[family]


def canonical_boundary(root, paths):
    expected = {p for p in paths if p.startswith('data/canonical/')}
    actual = set()
    for path in (root / 'data/canonical').rglob('*'):
        if path.is_symlink():
            raise ValueError('untracked or symlinked canonical input')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
        elif not path.is_dir():
            raise ValueError('nonregular canonical input')
    if actual != expected:
        raise ValueError('untracked or missing canonical input')


def versions(documents):
    return dict(sorted(Counter(str(x.get('schema_version', 'unversioned')) for x in documents).items()))


def inspect(root: Path, *, baseline_revision: str):
    root = root.resolve(strict=True)
    paths = tracked(root)
    canonical_boundary(root, paths)
    inventory = []
    for name in paths:
        if personal(name): continue  # no user-file paths, hashes or values in this package
        raw = (root / name).read_bytes()
        inventory.append({'path': name, 'byte_length': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                          'role': role(name)})
    families = []
    roots = sorted(set('data/' + p.split('/')[1] for p in paths if p.startswith('data/')) |
                   set(p for p in INPUT_ROOTS if p != 'data' and any(n == p or n.startswith(p + '/') for n in paths)))
    for family in roots:
        members = [p for p in paths if p == family or p.startswith(family + '/')]
        public = [r for r in inventory if r['path'] in members]
        schema_counts = Counter()
        for entry in public:
            if entry['path'].endswith('.json'):
                doc = read(root / entry['path'])
                schema_counts[str(doc.get('schema_version', 'unversioned')) if isinstance(doc, dict) else 'json-array'] += 1
        families.append({'schema_versions': dict(sorted(schema_counts.items())), 'path': family, 'exists': (root / family).exists(),
            'primary_role': FAMILY_ROLES[family.split('/')[1]] if family.startswith('data/') else role(members[0]),
            'member_roles': sorted(set(r['role'] for r in public)),
            'retained_file_count': len(public), 'retained_inventory_digest': digest(public),
            'personal_detail_omitted': family == 'data/collections'})
    games = {}
    game_directories = sorted({root / Path(*PurePosixPath(p).parts[:4]) for p in paths
                               if p.startswith('data/canonical/games/') and len(PurePosixPath(p).parts) > 4})
    for directory in game_directories:
        kinds = {}
        for kind, pattern in TYPED.items():
            documents = [read(p) for p in sorted(directory.glob(pattern)) if str(p.relative_to(root)) in paths]
            ids = sorted(x['id'] for x in documents)
            kinds[kind] = {'count': len(ids), 'schema_versions': versions(documents), 'ordered_id_digest': digest(ids)}
        sources = [read(root / p) for p in paths if p.startswith(str(directory.relative_to(root)) + '/')
                   and '/sources/' in p and p.endswith('.json') and not p.endswith('.manifest.json')]
        kinds['source_record'] = {'count': len(sources), 'schema_versions': versions(sources)}
        kinds['game'] = {'count': int((directory / 'game.json').is_file()),
                         'schema_versions': versions([read(directory/'game.json')]) if str((directory/'game.json').relative_to(root)) in paths else {}}
        games[directory.name] = kinds
    state_path = root / 'data/canonical/state.json'
    state = read(state_path) if 'data/canonical/state.json' in paths else {}
    promoted = {kind: {'count': len(rows), 'schema_versions': versions(rows.values()),
                      'ordered_id_digest': digest(sorted(rows))} for kind, rows in sorted(state.items())}
    overlap = {}
    for game in games:
        overlap[game] = {}
        for kind in ('card', 'printing'):
            docs = [read(p) for p in (root/'data/canonical/games'/game).glob(TYPED[kind]) if p.relative_to(root).as_posix() in paths]
            overlap[game][kind] = len({x['id'] for x in docs} & set(state.get(kind, {})))
        names = {x['name'].casefold() for x in [read(p) for p in
            (root/'data/canonical/games'/game).glob(TYPED['card']) if p.relative_to(root).as_posix() in paths]}
        overlap[game]['shared_name_count_not_identity_mapping'] = len(names &
            {x['values']['name'].casefold() for x in state.get('card', {}).values()})
    cards, printings, identifiers, finishes = (state.get(k, {}) for k in ('card','printing','identifier','finish'))
    missing_finish = Counter(f for p in printings.values() for f in p['values'].get('finish_ids', []) if f not in finishes)
    relationships = {'orphan_printing_card_count': sum(p['values'].get('card_id') not in cards for p in printings.values()),
        'orphan_identifier_printing_count': sum(i['values'].get('printing_uuid') not in printings for i in identifiers.values()),
        'unresolved_finish_reference_counts': dict(sorted(missing_finish.items())),
        'language_labels': dict(sorted(Counter(p['values'].get('language') for p in printings.values()).items())),
        'identifier_namespace_counts': dict(sorted(Counter(i['values'].get('namespace') for i in identifiers.values()).items()))}
    canonical = [{'path': ref['path'].removeprefix('data/canonical/'), 'sha256': ref['sha256']}
                 for ref in inventory if ref['path'].startswith('data/canonical/')]
    # This existing admission/pre-state recipe has no trailing newline.
    canonical_boundary(root, paths)
    canonical_digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return {'document_kind': 'review_inventory_not_snapshot', 'format_version': 'legacy-public-review-v1',
        'baseline_revision': baseline_revision, 'production_eligible': False, 'approval_state': 'not_granted',
        'source_policy_clearance': 'not_granted', 'games': games, 'promoted_state': promoted,
        'typed_state_overlap': overlap, 'promoted_relationships': relationships,
        'canonical_tree_digest': canonical_digest,
        'canonical_file_count': len(canonical),
        'canonical_json_file_count': sum(p.startswith('data/canonical/') and p.endswith('.json') for p in paths),
        'separate_planes': {
            'knowledge_fact_files': sum(p.startswith('data/knowledge/facts/') and p.endswith('.json') for p in paths),
            'knowledge_fact_kinds': dict(sorted(Counter(read(root/p).get('kind') for p in paths if p.startswith('data/knowledge/facts/') and p.endswith('.json')).items())),
            'market_files_by_area': dict(sorted(Counter(p.split('/')[2] for p in paths if p.startswith('data/market/')).items())),
            'audit_json_files': sum(p.startswith('data/audit/') and p.endswith('.json') for p in paths)},
        'optional_knowledge_state_present': (root/'data/canonical/knowledge/state.json').exists(),
        'inventory_digest': digest(inventory), 'families': families, 'files': inventory,
        'excluded_personal_roots': list(PERSONAL)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.root, baseline_revision=args.baseline_revision), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
