"""Finite successor views for the one closed casting-permission family batch.

Only named source/review paths and exact authored document suffixes are adapted.
Canonical Git comparisons reproduce inherited blobs and modes directly; this
helper adds no source authority and stores no whole-repository freeze fixture.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "d294835929a320fce01fb4025bdb3a4934e2eeaa"
TREE = "b846d10d3ea2438feba559a42eca7eb6fb485a45"
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/casting_permission_family/" + name
    for name in ("__init__.py", "__main__.py", "source.py", "scope.py",
                 "contracts.py", "reviews.py", "package.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-casting-permission-family/" + name
    for name in ("projection.json", "scope-preflight.json", "source-correspondence.json",
                 "permission-assessment.json", "relationship-reassessment.json",
                 "composite-coverage.json", "subsequent-recommendation.json", "manifest.json")
)


def is_casting_permission_family_addition(path, root=ROOT):
    """Exclude only the seven named modules and eight named package files."""
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS


DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 37420,
               'baseline_sha256': 'f5a3a4ca3d0e6cb4e0d36c450dec4a46772fb0b640c6fdb09937a600c3f31c83',
               'appendix_bytes': 1942,
               'appendix_sha256': '2db85f8782c610ec5caa273cc2866c00071ecd311c6d8cb6e31c438d8d3a21d4'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 92249,
                          'baseline_sha256': 'bb90b2146848ab5023b922729a8ad5a26a127745b75d5133fb56627bf6550192',
                          'appendix_bytes': 1942,
                          'appendix_sha256': '2db85f8782c610ec5caa273cc2866c00071ecd311c6d8cb6e31c438d8d3a21d4'},
 'CHANGELOG.md': {'baseline_bytes': 57676,
                  'baseline_sha256': 'e319d7be4edb2040c22e3cb741758fc7e69a3915348b92328b98cbe8dfcfc9ad',
                  'appendix_bytes': 1942,
                  'appendix_sha256': '2db85f8782c610ec5caa273cc2866c00071ecd311c6d8cb6e31c438d8d3a21d4'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 87297,
                           'baseline_sha256': '675f60619f8b0b515b491126d906b83f9edf195abb20ff7d8f571983e2af9298',
                           'appendix_bytes': 1937,
                           'appendix_sha256': '11fa75756292b7d893aaff7d2c09b0e4411c4611c651f630c93e2e7a30a431f9'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 69532,
                       'baseline_sha256': '36a92808cbe1bfdbccc271e81eab99e70e1d06b719cd2255deff2b97cde98078',
                       'appendix_bytes': 1937,
                       'appendix_sha256': '11fa75756292b7d893aaff7d2c09b0e4411c4611c651f630c93e2e7a30a431f9'},
 'docs/HANDOFF.md': {'baseline_bytes': 98089,
                     'baseline_sha256': 'e86c47e80b28b6615f3697c4952684e65de34f26f4248e6dcba8a0d6e04c4f4a',
                     'appendix_bytes': 1937,
                     'appendix_sha256': '11fa75756292b7d893aaff7d2c09b0e4411c4611c651f630c93e2e7a30a431f9'},
 'docs/ROADMAP.md': {'baseline_bytes': 40197,
                     'baseline_sha256': '97de83d22c7bf8a9dd13fdf71bfbf96514ca3139507ebf655fea16f86f13c483',
                     'appendix_bytes': 1937,
                     'appendix_sha256': '11fa75756292b7d893aaff7d2c09b0e4411c4611c651f630c93e2e7a30a431f9'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 111465,
                            'baseline_sha256': '8acf2ea4b7a78b15a1daf63c082b8f9b4502ca658afe93703b43ee00d734045d',
                            'appendix_bytes': 1937,
                            'appendix_sha256': '11fa75756292b7d893aaff7d2c09b0e4411c4611c651f630c93e2e7a30a431f9'}}


def historical_document_before_casting_permission_append(path, raw):
    """Validate complete canonical bytes and remove only this exact suffix."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES or type(raw) is not bytes:
        raise AssertionError("Only named casting-permission documents and bytes are adapted")
    pin = DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact casting-permission appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Complete canonical inherited document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact casting-permission document appendix changed")
    return baseline


# The exact finite test plumbing additions, independently reversible to canonical
# Git bytes. Every old assertion, count, expected hash and negative test survives.
ADAPTER_PATCHES = {'tests/activated_ability_preservation.py': [['from casting_stage_family_completion_preservation import '
                                              'is_casting_stage_family_completion_addition\n',
                                              'from casting_permission_family_preservation import '
                                              'is_casting_permission_family_addition\n'
                                              'from casting_stage_family_completion_preservation import '
                                              'is_casting_stage_family_completion_addition\n'],
                                             ['            or '
                                              'is_casting_stage_family_completion_addition(path)',
                                              '            or is_casting_permission_family_addition(path)\n'
                                              '            or '
                                              'is_casting_stage_family_completion_addition(path)']],
 'tests/casting_stage_family_completion_preservation.py': [['import hashlib\n',
                                                            'import hashlib\n'
                                                            'from casting_permission_family_preservation '
                                                            'import (\n'
                                                            '    DOCUMENT_APPENDICES as '
                                                            'CASTING_PERMISSION_APPENDICES,\n'
                                                            '    '
                                                            'historical_document_before_casting_permission_append,\n'
                                                            ')\n'],
                                                           ['    pin = DOCUMENT_APPENDICES[path]\n',
                                                            '    if len(raw) > '
                                                            'CASTING_PERMISSION_APPENDICES[path]["baseline_bytes"]:\n'
                                                            '        raw = '
                                                            'historical_document_before_casting_permission_append(path, '
                                                            'raw)\n'
                                                            '    pin = DOCUMENT_APPENDICES[path]\n']],
 'tests/test_activated_ability_procedure_design.py': [['from casting_stage_family_completion_preservation '
                                                       'import is_casting_stage_family_completion_addition\n',
                                                       'from casting_permission_family_preservation import '
                                                       'is_casting_permission_family_addition\n'
                                                       'from casting_stage_family_completion_preservation '
                                                       'import '
                                                       'is_casting_stage_family_completion_addition\n'],
                                                      ['                         and not '
                                                       'is_casting_stage_family_completion_addition(p)',
                                                       '                         and not '
                                                       'is_casting_permission_family_addition(p)\n'
                                                       '                         and not '
                                                       'is_casting_stage_family_completion_addition(p)'],
                                                      ['            and not '
                                                       'is_casting_stage_family_completion_addition(p)',
                                                       '            and not '
                                                       'is_casting_permission_family_addition(p)\n'
                                                       '            and not '
                                                       'is_casting_stage_family_completion_addition(p)']],
 'tests/test_casting_stage_family_completion_preservation.py': [['import '
                                                                 'casting_stage_family_completion_preservation '
                                                                 'as guard\n',
                                                                 'import '
                                                                 'casting_stage_family_completion_preservation '
                                                                 'as guard\n'
                                                                 'from '
                                                                 'casting_permission_family_preservation '
                                                                 'import '
                                                                 'historical_document_before_casting_permission_append\n'],
                                                                ['                raw = (guard.ROOT / '
                                                                 'name).read_bytes()\n',
                                                                 '                raw = (guard.ROOT / '
                                                                 'name).read_bytes()\n'
                                                                 '                raw = '
                                                                 'historical_document_before_casting_permission_append(name, '
                                                                 'raw)\n']],
 'tests/test_gameplay_rules_bounded_activated_ability_preservation.py': [['from '
                                                                          'casting_stage_family_completion_preservation '
                                                                          'import '
                                                                          'is_casting_stage_family_completion_addition\n',
                                                                          'from '
                                                                          'casting_permission_family_preservation '
                                                                          'import '
                                                                          'is_casting_permission_family_addition\n'
                                                                          'from '
                                                                          'casting_stage_family_completion_preservation '
                                                                          'import '
                                                                          'is_casting_stage_family_completion_addition\n'],
                                                                         ['            and not '
                                                                          'is_casting_stage_family_completion_addition(p)',
                                                                          '            and not '
                                                                          'is_casting_permission_family_addition(p)\n'
                                                                          '            and not '
                                                                          'is_casting_stage_family_completion_addition(p)']],
 'tests/test_shared_casting_stage_preservation.py': [['from casting_stage_family_completion_preservation '
                                                      'import is_casting_stage_family_completion_addition\n',
                                                      'from casting_permission_family_preservation import '
                                                      'is_casting_permission_family_addition\n'
                                                      'from casting_stage_family_completion_preservation '
                                                      'import is_casting_stage_family_completion_addition\n'],
                                                     ['            and not '
                                                      'is_casting_stage_family_completion_addition(p)',
                                                      '            and not '
                                                      'is_casting_permission_family_addition(p)\n'
                                                      '            and not '
                                                      'is_casting_stage_family_completion_addition(p)']],
 'tests/test_shared_proposal_legality_preservation.py': [['from casting_stage_family_completion_preservation '
                                                          'import (\n',
                                                          'from casting_permission_family_preservation '
                                                          'import is_casting_permission_family_addition\n'
                                                          'from casting_stage_family_completion_preservation '
                                                          'import (\n'],
                                                         ['                 if not '
                                                          'is_casting_stage_family_completion_addition(p)',
                                                          '                 if not '
                                                          'is_casting_permission_family_addition(p)\n'
                                                          '                 and not '
                                                          'is_casting_stage_family_completion_addition(p)'],
                                                         ['            and not '
                                                          'is_casting_stage_family_completion_addition(p, '
                                                          'root)',
                                                          '            and not '
                                                          'is_casting_permission_family_addition(p, root)\n'
                                                          '            and not '
                                                          'is_casting_stage_family_completion_addition(p, '
                                                          'root)']],
 'tests/test_shared_target_allocation_preservation.py': [['from casting_stage_family_completion_preservation '
                                                          'import (\n',
                                                          'from casting_permission_family_preservation '
                                                          'import is_casting_permission_family_addition\n'
                                                          'from casting_stage_family_completion_preservation '
                                                          'import (\n'],
                                                         ['                 and not '
                                                          'is_casting_stage_family_completion_addition(p)',
                                                          '                 and not '
                                                          'is_casting_permission_family_addition(p)\n'
                                                          '                 and not '
                                                          'is_casting_stage_family_completion_addition(p)'],
                                                         ['            and not '
                                                          'is_casting_stage_family_completion_addition(p, '
                                                          'root)',
                                                          '            and not '
                                                          'is_casting_permission_family_addition(p, root)\n'
                                                          '            and not '
                                                          'is_casting_stage_family_completion_addition(p, '
                                                          'root)']],
 'tests/test_shared_target_declaration_preservation.py': [['from '
                                                           'casting_stage_family_completion_preservation '
                                                           'import (\n',
                                                           'from casting_permission_family_preservation '
                                                           'import is_casting_permission_family_addition\n'
                                                           'from '
                                                           'casting_stage_family_completion_preservation '
                                                           'import (\n'],
                                                          ['                      and not '
                                                           'is_casting_stage_family_completion_addition(p)',
                                                           '                      and not '
                                                           'is_casting_permission_family_addition(p)\n'
                                                           '                      and not '
                                                           'is_casting_stage_family_completion_addition(p)'],
                                                          ['            and not '
                                                           'is_casting_stage_family_completion_addition(p)',
                                                           '            and not '
                                                           'is_casting_permission_family_addition(p)\n'
                                                           '            and not '
                                                           'is_casting_stage_family_completion_addition(p)']]}


ADAPTER_BASE_SHA256 = {'tests/activated_ability_preservation.py': '5c955a9516581b5ac6478b603ecfbfbc5e484d01a9a5bd4dc3dfb855ac7ee17f',
 'tests/casting_stage_family_completion_preservation.py': '91e650fcd1a61c5d5880d85d6758a4f5637f5f6f1e2979a86c1b72a8669b4ab8',
 'tests/test_activated_ability_procedure_design.py': 'f091b426a743c6519020ed82620c8835fcc88038c4fcd7ca125e690311c8e467',
 'tests/test_casting_stage_family_completion_preservation.py': '3a5d5b39ae0000a91c6d48bc690098b69ba0ad63230b964b41e6e2e52defbf1c',
 'tests/test_gameplay_rules_bounded_activated_ability_preservation.py': '12d68ef11faf8cb1567c1b1324e8aadfa6b09960ecb0b2644320ee69564a5366',
 'tests/test_shared_casting_stage_preservation.py': 'd5704e4cf5b20b5d4445b5542aec830f1031dd2d7046a472d0ac73b9bbcdef94',
 'tests/test_shared_proposal_legality_preservation.py': 'bf49630d7e66f4c564364844f12db75b81dbbfb52f07293d45ce25436a8860c2',
 'tests/test_shared_target_allocation_preservation.py': 'e5af964aba0f302e4ea81a330bef7f194f8e24bca0e7f9e7f530c940c6e36ce1',
 'tests/test_shared_target_declaration_preservation.py': '38336dc463b08183454bf603f8b15341d79a58d73d945a8ef8621b4a1782bf0a'}

def historical_adapter_bytes(name, raw):
    if type(name) is not str or name not in ADAPTER_PATCHES or type(raw) is not bytes:
        raise AssertionError("Only explicitly named test adapter bytes are accepted")
    for before, after in reversed(ADAPTER_PATCHES[name]):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact finite successor test adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != ADAPTER_BASE_SHA256[name]:
        raise AssertionError("Canonical historical test adapter bytes changed")
    return raw


def audit_canonical_git(root=ROOT):
    """Compare every inherited regular Git blob/mode, accounting for exact adapters.

    This explicit local audit requires the owner's canonical base object. Hosted
    shallow or disposable publication checkouts use existing retained guards;
    absence of this Git object is never reported as a successful Git audit.
    """
    root = Path(root)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
    if git("show", "-s", "--format=%T", BASE).strip().decode() != TREE:
        raise AssertionError("Exact canonical base tree required")
    groups = {}
    byte_count = 0
    appended_bytes = 0
    rows = git("ls-tree", "-r", "-z", BASE).split(b"\0")
    for row in rows:
        if not row:
            continue
        metadata, raw_name = row.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        name = raw_name.decode()
        path = root / name
        if kind != "blob" or mode not in ("100644", "100755"):
            raise AssertionError("Only canonical regular-file Git entries expected")
        if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):
            raise AssertionError("Inherited path missing or replaced by a symlink: " + name)
        actual_mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        if actual_mode != mode:
            raise AssertionError("Inherited Git executable mode changed: " + name)
        raw = path.read_bytes()
        if name in DOCUMENT_APPENDICES:
            inherited = historical_document_before_casting_permission_append(name, raw)
            appended_bytes += len(raw) - len(inherited)
            raw = inherited
        elif name in ADAPTER_PATCHES:
            raw = historical_adapter_bytes(name, raw)
        actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual_blob != blob:
            raise AssertionError("Inherited canonical Git blob changed: " + name)
        group = (name.split("/", 1)[0] if "/" in name else "root")
        groups[group] = groups.get(group, 0) + 1
        byte_count += len(raw)
    return {"canonical_base": BASE, "canonical_tree": TREE, "inherited_files": sum(groups.values()),
        "inherited_bytes": byte_count, "groups": groups, "appended_bytes": appended_bytes,
        "exact_finite_adapter_files": len(ADAPTER_PATCHES), "all_inherited_blobs_and_modes_preserved": True}
