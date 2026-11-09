"""Exact finite review-packet preservation adapter; no evidence exemptions.

The collection regression adapter reverses only its pinned allocation repair.
"""
import hashlib

PINS = {'tests/requirements_preservation_support.py': {'old': {'bytes': 4697,
                                                        'sha256': '4a05eb68350fde23c30e4d68aa45f40b3df359d26e31eb47f1c38da775a83080'},
                                                'new': {'bytes': 5121,
                                                        'sha256': '3a20cda9c58a4fddffe24cf685f435c7c84268d9a070e9b5168ee6e3ed98cee8'}},
 'tests/proposed_spell_packet_analysis_preservation.py': {'old': {'bytes': 79282,
                                                                  'sha256': 'b3134e7ff7db2b1dcf56a925a634994afbd44b74aa4eef5ca75415909051f45b'},
                                                          'new': {'bytes': 79494,
                                                                  'sha256': '3a810a2803682541f7cfda94c24dea5301ba741d04236d74d786718b77c6c630'}}}
ADDITIONS = {'src/card_intelligence/context_review_input.py': {'bytes': 11763,
                                                   'sha256': '1c7c387ed92e6ec7427c1e623e9eaf3f25ac2bd78ffde59ab058b757db6280dc'},
 'src/card_intelligence/context_review.py': {'bytes': 19164,
                                             'sha256': 'c5906d6d6e8ea47ffa62d5de4326c9bd83cf6fa567949920e87dbf16d4a9d75a'},
 'src/card_intelligence/context_review_cli.py': {'bytes': 3388,
                                                 'sha256': '5a53ef4c7664109b2543bc31e55ce37d9ad60114230a2c8da515dd2f55a75631'}}
INJECTIONS = [("    if type(raw) is not bytes: raise AssertionError('exact source bytes required')\n", '    from context_review_preservation_support import preceding_bytes as review_preceding\n    raw = review_preceding(name, raw)\n'), ('def is_requirements_addition(path, root):\n', '    from context_review_preservation_support import is_review_addition\n    if is_review_addition(path, root): return True\n'), ('def assert_requirements_addition(path, root):\n', '    from context_review_preservation_support import is_review_addition, assert_review_addition\n    if is_review_addition(path, root): return assert_review_addition(path, root)\n')]
GUARD_SUFFIX = b"\nCONTEXT_REVIEW_SOURCE_PATHS = frozenset(('src/card_intelligence/context_review_input.py', 'src/card_intelligence/context_review.py', 'src/card_intelligence/context_review_cli.py'))\n"
EARLIER_GUARD_SHA256 = 'c0e0341674db7a2699b86fe5fedc39df574f0bd49d593eb0be9a77bc4b8e1255'


def _pin(raw): return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    from test_evidence_review_malformed import handoff_preceding_bytes
    raw = handoff_preceding_bytes(name, raw)
    from test_collection_intelligence import allocation_preceding_bytes
    raw = allocation_preceding_bytes(name, raw)
    if name not in PINS: return raw
    pin=PINS[name]
    if _pin(raw)==pin['old']: return raw
    if name.endswith('proposed_spell_packet_analysis_preservation.py') and hashlib.sha256(raw).hexdigest()==EARLIER_GUARD_SHA256: return raw
    if _pin(raw)!=pin['new']: raise AssertionError('unreviewed review-packet helper edit')
    if name.endswith('requirements_preservation_support.py'):
        text=raw.decode()
        for needle, extra in INJECTIONS:
            if text.count(needle+extra)!=1: raise AssertionError('exact successor injection required')
            text=text.replace(needle+extra,needle,1)
        raw=text.encode()
    else:
        if not raw.endswith(GUARD_SUFFIX): raise AssertionError('exact source guard suffix required')
        raw=raw[:-len(GUARD_SUFFIX)].replace(b'| STRATEGIC_REQUIREMENTS_SOURCE_PATHS | CONTEXT_REVIEW_SOURCE_PATHS\n',b'| STRATEGIC_REQUIREMENTS_SOURCE_PATHS\n',1)
    if _pin(raw)!=pin['old']: raise AssertionError('exact canonical predecessor required')
    return raw


def is_review_addition(path, root): return path.relative_to(root).as_posix() in ADDITIONS


def assert_review_addition(path, root):
    name=path.relative_to(root).as_posix()
    if name not in ADDITIONS or path.is_symlink() or path.stat().st_mode & 0o111:
        raise AssertionError('unsupported review source path or mode')
    if _pin(path.read_bytes())!=ADDITIONS[name]: raise AssertionError('exact review-packet source pin required')
