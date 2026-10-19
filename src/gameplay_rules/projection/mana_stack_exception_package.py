"""Append-only single-unit evidence package with deterministic offline reproduction.

Fresh construction requires verified bytes. Offline rebuild verifies twelve
pinned packages and reproduces closed authored records; it does not claim fresh
source access. No record is an engine snapshot or an execution profile.
"""
import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from .contracts import _json
from .dependency_package import _root, _read
from .bounded_mana_package import HISTORICAL_ACQUISITION_ID
from .mana_stack_exception_pins import PRIOR_PACKAGES
from .mana_stack_exception_reports import CANONICAL_MAIN, STATUS, projection, reports
from .mana_stack_exception_source import verified_anchors

PACKAGE_NAME = 'gameplay-rules-bounded-mana-stack-exception-projection'
RECORD_NAMES = frozenset(('projection.json', 'design-source-correspondence.json',
    'parent-scope-review.json', 'section-dependency-review.json', 'consumer-reassessment.json',
    'stack-exception-readiness.json', 'priority-readiness.json', 'overall-readiness.json',
    'composite-coverage.json'))


def _fail(message):
    raise GameplayContractError('bounded_mana_stack_exception_package', message)


def _bytes(value):
    return (deterministic_json(value)+'\n').encode('utf-8')


def verify_prior_packages(review_root):
    root = _root(review_root)
    for name, pin in _json(PRIOR_PACKAGES).items():
        package = _root(root/name)
        if {p.name for p in package.iterdir()} != set(pin['files']):
            _fail('PRIOR_PACKAGE_FILE_SET_CHANGED')
        for filename, digest in pin['files'].items():
            if hashlib.sha256(_read(package/filename)).hexdigest() != digest:
                _fail('PRIOR_PACKAGE_BYTES_CHANGED')
    # Every manifest and every record is pinned independently to canonical bytes.
    return _json(PRIOR_PACKAGES)


def rebuild_package(*, review_root):
    """Reproduce fixed metadata offline without elevating it to fresh source proof."""
    verify_prior_packages(review_root)
    root = Path(review_root)
    prior_manifest = json.loads(_read(root/'gameplay-rules-mana-direct-dependency-design/manifest.json'))
    classification_root = root/'gameplay-rules-bounded-mana-classification-projection'
    mana = json.loads(_read(root/'gameplay-rules-bounded-mana-ability-projection/projection.json'))
    composite = json.loads(_read(classification_root/'composite-coverage.json'))['findings']
    last = composite['projection_components'][-1]
    if last.pop('package_binding', None) != 'THIS_ENCLOSING_PACKAGE':
        _fail('PRIOR_SELF_PACKAGE_BINDING_REQUIRED')
    last['package_id'] = json.loads(_read(classification_root/'manifest.json'))['package_id']
    prior_rules = {}
    for name in _json(PRIOR_PACKAGES):
        candidate = root/name/'projection.json'
        if candidate.is_file():
            for rule in json.loads(_read(candidate))['rules']:
                ref = rule['rule_reference']
                if ref in prior_rules:
                    _fail('PRIOR_PROJECTION_OVERLAP')
                prior_rules[ref] = rule
    if len(prior_rules) != 84:
        _fail('EXACT_EIGHTY_FOUR_PRIOR_SOURCE_UNITS_REQUIRED')
    p = projection()
    return {'projection.json':p, **reports(prior_manifest, mana, composite, p, prior_rules)}


def build_package(artifact_path, *, review_root):
    """Only entry point for new source-verified construction."""
    verified_anchors(artifact_path, review_root=review_root)
    return rebuild_package(review_root=review_root)


def manifest(records):
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail('EXACT_NINE_RECORDS_REQUIRED')
    p = records['projection.json']
    if p != projection():
        _fail('FIXED_PROJECTION_REQUIRED')
    record_ids = {name: value.get('projection_id', value.get('review_id')) for name,value in records.items()}
    if len(set(record_ids.values())) != 9:
        _fail('DISTINCT_RECORD_IDENTITIES_REQUIRED')
    body = {'schema_version':'gameplay-bounded-mana-stack-exception-package-v1',
        'canonical_base':CANONICAL_MAIN, 'status':STATUS,
        'projection_id':p['projection_id'], 'record_ids':record_ids,
        'prior_package_ids':{name:pin['package_id'] for name,pin in _json(PRIOR_PACKAGES).items()},
        'source_binding':p['source_binding'], 'boundary_flags':p['boundary_flags'],
        'files':{name:{'bytes':len(_bytes(value)), 'sha256':hashlib.sha256(_bytes(value)).hexdigest()}
            for name,value in sorted(records.items())},
        'selected_references':['405.6c'], 'selected_rule_count':1,
        'projected_rule_count_before':84, 'new_source_units_projected':1, 'projected_rule_count_after':85,
        'additional_rules_projected':[], 'historical_anchors_changed':False,
        'historical_acquisition_identity':HISTORICAL_ACQUISITION_ID,
        'semantic_closure':'OPEN', 'execution_readiness':'BLOCKED',
        'readiness_code':'REAL_EXECUTION_PROFILE_NOT_READY'}
    return {**body, 'package_id':'sha256:'+sha256_identity({'domain':body['schema_version'],'content':body})}


def write_package(root, records, *, review_root):
    if records != rebuild_package(review_root=review_root):
        _fail('AUTHORED_RECORDS_DO_NOT_REPRODUCE')
    root = Path(root)
    if any(p.is_symlink() for p in (root,*root.parents)):
        _fail('SYMLINK_DESTINATION_FORBIDDEN')
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        _fail('APPEND_ONLY_NEW_OR_EMPTY_DESTINATION_REQUIRED')
    m = manifest(records)
    root.mkdir(parents=True, exist_ok=True)
    for name,value in {**records,'manifest.json':m}.items():
        with (root/name).open('xb') as stream:
            stream.write(_bytes(value))
    return m


def load_package(root, *, review_root):
    root = _root(root)
    if {p.name for p in root.iterdir()} != RECORD_NAMES | {'manifest.json'}:
        _fail('EXTRA_OR_MISSING_PACKAGE_FILE')
    expected = rebuild_package(review_root=review_root)
    m = manifest(expected)
    # Comparing exact canonical bytes also rejects duplicate keys, reordered or
    # rehashed findings, source prose, extra fields, and non-finite JSON values.
    for name,value in {**expected,'manifest.json':m}.items():
        if _read(root/name) != _bytes(value):
            _fail('PACKAGE_BYTES_DO_NOT_REPRODUCE')
    return expected


def verify_source(records, artifact_path, *, review_root):
    reproduced = build_package(artifact_path, review_root=review_root)
    if records != reproduced:
        _fail('EXACT_SOURCE_REPRODUCTION_FAILED')
    return {'status':'VERIFIED_EXACT_SOURCE_BLOCKS', 'selected_rule_count':1,
        'projection_id':records['projection.json']['projection_id'], 'source_body_retained':False}


def composite_view(records):
    """Return a separate view resolving the enclosing identity, without mutation."""
    m = manifest(records)
    view = _json(records['composite-coverage.json']['findings'])
    component = view['projection_components'][-1]
    if component.pop('package_binding', None) != 'THIS_ENCLOSING_PACKAGE':
        _fail('SELF_PACKAGE_BINDING_REQUIRED')
    component['package_id'] = m['package_id']
    return view
