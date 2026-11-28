"""One exact vision successor and two compatibility insertions; test use only."""
import hashlib
import json

BASE = '6a91770194320e7d790567bbf07acf7e2fb4c480'
TREE = '582b467efbb8995655e119000d54a2fa8d979dfc'
PATHS = frozenset(('VISION.md', 'tests/vision_alignment_preservation.py',
                   'tests/test_vision_alignment.py'))
PINS = {'VISION.md': {'edit': {'end': 7957,
                        'new_sha256': 'ac9d44e0b7b95abd5de44cea4cf0a42cccf2b2c29b11e4dc728767ca87e349f4',
                        'start': 5368},
               'historical': [{'bytes': 4956,
                               'sha256': '33494503d2595295c1c406ad859faa3a4aaeb4afb3052ba4e3a5cda799eb445a'}],
               'new': {'bytes': 9683,
                       'sha256': 'ab0e0d02c9afceb4f436c1ef711468bb8c619ebc80759bfd1ba3ee2e9ed26f8d'},
               'old': {'bytes': 7094,
                       'sha256': '66a345656e2c51506d01dd458e83971b492792fda0fb74e241eb0013e975268e'}},
 'tests/test_vision_alignment.py': {'edit': {'end': 824,
                                             'new_sha256': '14d02087b4808f78309b9adf4b1422b02e3ee6243cbab24e96191a93ae2bed92',
                                             'start': 701},
                                    'new': {'bytes': 5433,
                                            'sha256': '6b902b795cc69e3504707317993d012eebad3719bfbab0eed118bcee14d0e03a'},
                                    'old': {'bytes': 5310,
                                            'sha256': '3ff4276082eabe298f05bd480c963ba4a50d640a9dc80683650ccff1dd85210b'}},
 'tests/vision_alignment_preservation.py': {'edit': {'end': 3770,
                                                     'new_sha256': 'c51488ba33db7aebe857c37af99d513409825333e1839db91e9d58b67548c26b',
                                                     'start': 3644},
                                            'new': {'bytes': 4750,
                                                    'sha256': '34efbecb800e325128f5c12ead597ec490220927347b06dcc607c7babba1f550'},
                                            'old': {'bytes': 4624,
                                                    'sha256': 'ffde6e723e18770270299e06ac330663d00ab77a97fd8d9a5f8dafd3e8b970e6'}}}
PINS_SHA256 = '735e76f3c478660a59edfe625433e9d5c123b4575afe45ee7cfbfa6d58fd1d6a'


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def restore(name, raw):
    from candidate_mana_preservation import preceding_bytes as candidate_preceding
    raw = candidate_preceding(name, raw)
    if type(name) is not str or name not in PATHS or type(raw) is not bytes:
        raise AssertionError('exact named proactive vision bytes required')
    encoded = json.dumps(PINS, sort_keys=True, separators=(',', ':')).encode()
    if set(PINS) != PATHS or hashlib.sha256(encoded).hexdigest() != PINS_SHA256:
        raise AssertionError('exact proactive vision compatibility pins required')
    expected = PINS[name]
    if pin(raw) == expected['old'] or pin(raw) in expected.get('historical', []):
        return raw
    if pin(raw) != expected['new']:
        raise AssertionError('unrecognized proactive vision successor')
    edit = expected['edit']
    start, end = edit['start'], edit['end']
    if hashlib.sha256(raw[start:end]).hexdigest() != edit['new_sha256']:
        raise AssertionError('exact proactive vision insertion required')
    old = raw[:start] + raw[end:]
    if pin(old) != expected['old']:
        raise AssertionError('exact pre-proactive historical bytes required')
    return old


def preceding_bytes(name, raw):
    from candidate_mana_preservation import preceding_bytes as candidate_preceding
    raw = candidate_preceding(name, raw)
    if type(name) is not str or type(raw) is not bytes:
        raise AssertionError('exact named source bytes required')
    return restore(name, raw) if name in PATHS else raw
