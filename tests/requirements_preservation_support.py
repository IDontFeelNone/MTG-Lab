"""Exact finite test-only preservation adapters; no admission exemptions.

Reconstruct two predecessor helper files byte-for-byte. Every runtime predecessor
and evidence/report/policy/workflow file remains unchanged. Only four exact new
requirements module paths are excluded from older source censuses, with raw pins.
"""
import hashlib

PINS = {'tests/overlay_preservation_support.py': {'new': {'bytes': 23989,
                                                   'sha256': 'ebbb70e934ef59b2256503efab1230485f88d28aaa305acb2071e29bb38a3205'},
                                           'old': {'bytes': 23047,
                                                   'sha256': '74475dba2d3e2892732ac6b20234d43a310f2a9cde029dc94f17076968402b99'}},
 'tests/proposed_spell_packet_analysis_preservation.py': {'new': {'bytes': 79282,
                                                                  'sha256': 'b3134e7ff7db2b1dcf56a925a634994afbd44b74aa4eef5ca75415909051f45b'},
                                                          'old': {'bytes': 78983,
                                                                  'sha256': 'c0e0341674db7a2699b86fe5fedc39df574f0bd49d593eb0be9a77bc4b8e1255'}}}
ADDITIONS = {'src/card_intelligence/strategic_context.py': {'bytes': 6897,
                                                'sha256': '31707e059b03aff7f97519a98773eb0c46b14d7735203ddd9a23a7fd3a7efe03'},
 'src/card_intelligence/strategic_requirements.py': {'bytes': 15885,
                                                     'sha256': '0d7680acfd67b4e301c5c2751ddcd61f87bc80c5a1b4107a615df7d98bffae2c'},
 'src/card_intelligence/strategic_requirements_cli.py': {'bytes': 4892,
                                                         'sha256': '42588fd495c4b0bffb1b9948b3859eff63cbf43cf87112e953dbe5bb883ac0b3'},
 'src/card_intelligence/strategic_requirements_policy.py': {'bytes': 16330,
                                                            'sha256': 'def767f440101ebd12c077d78bf6ca287958967df4cbf0233deeba2210a027b7'}}
GUARD_SUFFIX = b"\nSTRATEGIC_REQUIREMENTS_SOURCE_PATHS = frozenset(('src/card_intelligence/strategic_context.py', 'src/card_intelligence/strategic_requirements_policy.py', 'src/card_intelligence/strategic_requirements.py', 'src/card_intelligence/strategic_requirements_cli.py'))\n"
HELPER_SUFFIX = b'\n# Exact requirements-only successor: original overlay/source pins stay intact.\n_before_requirements_historical = historical_source_bytes\n_before_requirements_addition = is_overlay_addition\n_before_requirements_assertion = assert_overlay_addition\n\n\ndef historical_source_bytes(name, raw):\n    from requirements_preservation_support import preceding_bytes\n    return _before_requirements_historical(name, preceding_bytes(name, raw))\n\n\ndef is_overlay_addition(path, root):\n    from requirements_preservation_support import is_requirements_addition\n    return is_requirements_addition(path, root) or _before_requirements_addition(path, root)\n\n\ndef assert_overlay_addition(path, root):\n    from requirements_preservation_support import is_requirements_addition, assert_requirements_addition\n    if is_requirements_addition(path, root):\n        return assert_requirements_addition(path, root)\n    return _before_requirements_assertion(path, root)\n'


def _pin(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    from context_review_preservation_support import preceding_bytes as review_preceding
    raw = review_preceding(name, raw)
    if name not in PINS:return raw
    pin=PINS[name]
    if _pin(raw)==pin['old']:return raw
    if _pin(raw)!=pin['new']:raise AssertionError('unreviewed preservation adapter edit')
    if name.endswith('overlay_preservation_support.py'):
        if not raw.endswith(HELPER_SUFFIX):raise AssertionError('exact helper suffix required')
        raw=raw[:-len(HELPER_SUFFIX)]
    else:
        if not raw.endswith(GUARD_SUFFIX):raise AssertionError('exact source guard suffix required')
        raw=raw[:-len(GUARD_SUFFIX)].replace(b'| LAND_OVERLAY_SOURCE_PATHS | STRATEGIC_REQUIREMENTS_SOURCE_PATHS\n',b'| LAND_OVERLAY_SOURCE_PATHS\n',1)
    if _pin(raw)!=pin['old']:raise AssertionError('predecessor not exactly reconstructed')
    return raw


def is_requirements_addition(path, root):
    from context_review_preservation_support import is_review_addition
    if is_review_addition(path, root): return True
    return path.relative_to(root).as_posix() in ADDITIONS


def assert_requirements_addition(path, root):
    from context_review_preservation_support import is_review_addition, assert_review_addition
    if is_review_addition(path, root): return assert_review_addition(path, root)
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS or path.is_symlink() or path.stat().st_mode & 0o111:
        raise AssertionError('unsupported requirements source path/mode')
    if _pin(path.read_bytes())!=ADDITIONS[name]:raise AssertionError('exact requirements source pin required')
