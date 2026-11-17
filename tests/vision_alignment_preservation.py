"""Exact test-only vision successor; original PR #242 pins are unchanged.

Reverse only two hash-pinned files. Unknown changes cannot become historical
bytes, and no runtime, source-use, admission or execution authority is granted.
"""
import hashlib

BASE = 'fa693fe53f7efa3d80a0a51f47ef709a197bee3f'
TREE = 'cfbebbe6e3d302a67b7270d3623c366fac4290b4'
PINS = {'VISION.md': {'edits': [{'end': 851,
                          'new_sha256': 'a3532611b42c28499be862e819f46246f7a89ad9eaa8258f36cdb179c9bbf256',
                          'old': '',
                          'start': 291},
                         {'end': 1209,
                          'new_sha256': '46d043f7b2ffa3e567b5a59d1544d118ad7d33dc3d236ff69b265d05446ea30a',
                          'old': '',
                          'start': 1135},
                         {'end': 2275,
                          'new_sha256': 'b54dd15659764152ad145feae0ae49e755cf723028bd4280953fc9cd6f2fb49f',
                          'old': '',
                          'start': 2146},
                         {'end': 3225,
                          'new_sha256': 'acea60921be43fc0c23d3a3acfbe54596110dca8cacacbc16fb1153564318bec',
                          'old': '',
                          'start': 2866},
                         {'end': 4345,
                          'new_sha256': 'fde5c01d034ca6eac38e8685d384caf6ce8d9939e634eaf6b93cc77b46e4627a',
                          'old': '',
                          'start': 4161},
                         {'end': 5368,
                          'new_sha256': 'cfb28c5dac5061d5e3d06388c7ab82c858c38a742762dbe1fba21f13f5ff21af',
                          'old': '',
                          'start': 5005},
                         {'end': 5491,
                          'new_sha256': '018c630cb92a1ec8d3948c8791b5b5ddd0c5acd49c650f8dc91b899a58d72ed3',
                          'old': 'Preserve hypotheses, evidence, experiments, outcomes, counterexamples '
                                 'and\n',
                          'start': 5402},
                         {'end': 5863,
                          'new_sha256': 'ff902743e3ad699fc209e022737139d95f90013c075c7ec28a3c0cafe7c292a8',
                          'old': '',
                          'start': 5706},
                         {'end': 7094,
                          'new_sha256': '64852660079b0ad6d11debf97e4c0957e4deb57e3d1ff09f56f1b1343182f4dd',
                          'old': '',
                          'start': 6797}],
               'new': {'bytes': 7094,
                       'sha256': '66a345656e2c51506d01dd458e83971b492792fda0fb74e241eb0013e975268e'},
               'old': {'bytes': 4956,
                       'sha256': '33494503d2595295c1c406ad859faa3a4aaeb4afb3052ba4e3a5cda799eb445a'}},
 'tests/test_documentation_continuity.py': {'edits': [{'end': 6236,
                                                       'new_sha256': '59ab2f44655a9a253297dbde9aaf6834d451aead040b2a1ae16908042c33378f',
                                                       'old': '',
                                                       'start': 6121}],
                                            'new': {'bytes': 8534,
                                                    'sha256': 'ffff0dee42c88193599f8cbed9752ca95b6df7181329bde93109ebd273ce55b1'},
                                            'old': {'bytes': 8419,
                                                    'sha256': '32499f0ca028b8e62c7f3a49d289f05b77d9782569c656a283c24dd25838da1f'}}}


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def restore(name, raw):
    if type(name) is not str or name not in PINS or type(raw) is not bytes:
        raise AssertionError('exact named vision successor bytes required')
    expected = PINS[name]
    if pin(raw) == expected['old']:
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized vision-alignment successor')
    for edit in reversed(expected['edits']):
        start, end = edit['start'], edit['end']
        if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
            raise AssertionError('exact approved vision delta required')
        raw = raw[:start] + edit['old'].encode('utf-8') + raw[end:]
    if pin(raw) != expected['old']:
        raise AssertionError('exact pre-refinement bytes required')
    return raw


def preceding_bytes(name, raw):
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named document bytes required')
    return restore(name, raw) if name in PINS else raw
