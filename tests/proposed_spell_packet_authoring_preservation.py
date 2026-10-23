"""Finite authoring-pilot successors, subordinate to retained evidence.

No source fixtures, history or authorization records are rewritten. Exact named
appendices compose with the inherited guards; the promoted checker can be
reconstructed byte-for-byte without keeping a second implementation.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "96d120a6543a9eb65e670d00c8fa66a0cf049c1a"
TREE = "3fa893becd3fc83e1a0731f97f24bdc1cfff8828"
NEW_SOURCE_PATHS = frozenset("src/proposed_spell_packets/" + name for name in
    ("__init__.py", "validation.py", "authoring.py", "__main__.py"))


def is_packet_authoring_addition(path, root=ROOT):
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS


DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 41223,
               'baseline_sha256': '555a5402db10bed955c4380b95e53ab4c79367c79660533da2d1c6f2c5812054',
               'appendix_bytes': 2600,
               'appendix_sha256': 'd82ed24bccc2a3bdb73e56f759392c89e4fb46c858114b281b25ce934a2e09c0'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 96052,
                          'baseline_sha256': 'e3db375efef426ce291533392dc177d46dc83a67b9b76054f83bbd177ea1adc6',
                          'appendix_bytes': 2600,
                          'appendix_sha256': 'd82ed24bccc2a3bdb73e56f759392c89e4fb46c858114b281b25ce934a2e09c0'},
 'CHANGELOG.md': {'baseline_bytes': 61479,
                  'baseline_sha256': '96817ec515445b0f05dacc777bc11ca9cca717e57d23caa8334393baea39a1b8',
                  'appendix_bytes': 2600,
                  'appendix_sha256': 'd82ed24bccc2a3bdb73e56f759392c89e4fb46c858114b281b25ce934a2e09c0'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 91090,
                           'baseline_sha256': '83fc825e6eafda07ad12732b917db61b838ee853333b14f2b5a01761bf93db79',
                           'appendix_bytes': 2595,
                           'appendix_sha256': '1ca75befd3cafdf699f8a9ad205135f9c089856acfea1f9340e5a29b2f723008'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 73325,
                       'baseline_sha256': 'f638ffba5132917d16320fd2a5d181e10a333c5b387813c2c4f6836d1222b8cc',
                       'appendix_bytes': 2595,
                       'appendix_sha256': '1ca75befd3cafdf699f8a9ad205135f9c089856acfea1f9340e5a29b2f723008'},
 'docs/HANDOFF.md': {'baseline_bytes': 101882,
                     'baseline_sha256': 'aa1c63eacd53dc6ced7df27963b1379b16e0b79d6b739518af3377f19334cca6',
                     'appendix_bytes': 2595,
                     'appendix_sha256': '1ca75befd3cafdf699f8a9ad205135f9c089856acfea1f9340e5a29b2f723008'},
 'docs/ROADMAP.md': {'baseline_bytes': 43990,
                     'baseline_sha256': 'cce57c5d85f83cb48326f061df56a85b81a9f3550cdae7507be00a2e219f4de6',
                     'appendix_bytes': 2595,
                     'appendix_sha256': '1ca75befd3cafdf699f8a9ad205135f9c089856acfea1f9340e5a29b2f723008'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 115258,
                            'baseline_sha256': '03faee6ef2d12b72fe5817968bf22374e5162afc216374ab56682a0223465d7d',
                            'appendix_bytes': 2595,
                            'appendix_sha256': '1ca75befd3cafdf699f8a9ad205135f9c089856acfea1f9340e5a29b2f723008'}}


def historical_document_before_authoring_append(path, raw):
    """Accept only an exact named pre-pilot document or its exact successor."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES or type(raw) is not bytes:
        raise AssertionError("Only named pilot document bytes are adapted")
    pin = DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact authoring-pilot appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-pilot historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact authoring-pilot appendix changed")
    return baseline


ADAPTER_PATCHES = {'tests/proposed_spell_evidence_packet_preservation.py': [('import hashlib\n',
                                                           'import hashlib\n'
                                                           'from '
                                                           'proposed_spell_packet_authoring_preservation '
                                                           'import (\n'
                                                           '    is_packet_authoring_addition, '
                                                           'historical_document_before_authoring_append,\n'
                                                           ')\n'),
                                                          ('    return '
                                                           'path.relative_to(root).as_posix() in '
                                                           'NEW_REVIEW_PATHS\n',
                                                           '    return '
                                                           '(path.relative_to(root).as_posix() in '
                                                           'NEW_REVIEW_PATHS\n'
                                                           '            or '
                                                           'is_packet_authoring_addition(path, '
                                                           'root))\n'),
                                                          ('    size = pin["baseline_bytes"]\n'
                                                           '    if len(raw) not in',
                                                           '    size = pin["baseline_bytes"]\n'
                                                           '    if len(raw) > size + '
                                                           'pin["appendix_bytes"]:\n'
                                                           '        raw = '
                                                           'historical_document_before_authoring_append(path, '
                                                           'raw)\n'
                                                           '    if len(raw) not in')],
 'tests/test_proposed_spell_evidence_packet_preservation.py': [('import hashlib\n',
                                                                'import hashlib\n'
                                                                'from '
                                                                'proposed_spell_packet_authoring_preservation '
                                                                'import '
                                                                'historical_document_before_authoring_append\n'),
                                                               ('            raw = (guard.ROOT / '
                                                                'name).read_bytes()\n'
                                                                '            old = '
                                                                'guard.historical_document_before_packet_append(name, '
                                                                'raw)\n',
                                                                '            raw = '
                                                                'historical_document_before_authoring_append(name, '
                                                                '(guard.ROOT / '
                                                                'name).read_bytes())\n'
                                                                '            old = '
                                                                'guard.historical_document_before_packet_append(name, '
                                                                'raw)\n')]}
ADAPTER_BASE_SHA256 = {'tests/proposed_spell_evidence_packet_preservation.py': 'b3c31e64ca224875b1ca5be8de579458fa055cc12c2ff588ccf0f97f24e40bed',
 'tests/test_proposed_spell_evidence_packet_preservation.py': '8ac760215fb70eba98ed03f9455aed76c5d4c6e72cd20ca0420ab8b61e084e1e'}
CHECKER_PROMOTION_PATCHES = [('"""Offline checks for one proposed, fictional evidence-packet design.\n'
  '\n'
  'This test helper validates representation and bindings. It performs no gameplay\n'
  'interpretation, inference, admission or execution, and writes no retained files.\n'
  '"""\n',
  '"""Shared offline structural validation for the fictional v1 evidence packet.\n'
  '\n'
  'Promoted from the corrected PR #209 checker. Validation establishes representation\n'
  'and retained bindings only, with no truth assessment, inference or execution.\n'
  '"""\n'),
 ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path(__file__).resolve().parents[2]'),
 ('if __name__ == "__main__":\n'
  '    result = load_package()\n'
  '    print(json.dumps({"status": "STRUCTURALLY_VALID_DESIGN_ONLY", "packets": '
  'len(PACKET_NAMES),\n'
  '        "package_id": result["manifest.json"]["package_id"], "execution_authority": "BLOCKED"}, '
  'sort_keys=True))\n',
  'def main():\n'
  '    """Validate the retained design package without changing its bytes."""\n'
  '    result = load_package()\n'
  '    print(json.dumps({"status": "STRUCTURALLY_VALID_DESIGN_ONLY", "packets": '
  'len(PACKET_NAMES),\n'
  '        "package_id": result["manifest.json"]["package_id"], "execution_authority": "BLOCKED"}, '
  'sort_keys=True))\n'
  '\n'
  '\n'
  'if __name__ == "__main__":\n'
  '    main()\n')]
CHECKER_ORIGINAL_SHA256 = '9bbebaf8efbf5e833957cf137c491636705a967780a702ab7ef799a110c76ce9'
CHECKER_ADAPTER_SHA256 = '04a2fa5ef4a4e343b9ccee555cdfe199c36c1d384421f0a7b0f9141cee9721b6'


def historical_adapter_bytes(name, raw):
    if type(name) is not str or name not in ADAPTER_PATCHES or type(raw) is not bytes:
        raise AssertionError("Only explicitly named pilot adapters are accepted")
    for before, after in reversed(ADAPTER_PATCHES[name]):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact finite authoring-pilot adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != ADAPTER_BASE_SHA256[name]:
        raise AssertionError("Canonical pre-pilot adapter bytes changed")
    return raw


def historical_checker_bytes(root=ROOT):
    """Reconstruct the original checker from the one shared implementation."""
    adapter = (root / "tests/proposed_spell_evidence_packet_validation.py").read_bytes()
    if hashlib.sha256(adapter).hexdigest() != CHECKER_ADAPTER_SHA256:
        raise AssertionError("Exact checker compatibility adapter changed")
    raw = (root / "src/proposed_spell_packets/validation.py").read_bytes()
    for before, after in reversed(CHECKER_PROMOTION_PATCHES):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact narrow checker extraction changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != CHECKER_ORIGINAL_SHA256:
        raise AssertionError("Promoted corrected checker differs from inherited implementation")
    return raw


def audit_canonical_git(root=ROOT):
    """Require exact base objects and verify all inherited blobs and modes.

    This explicit local audit is separate from shallow/disposable test discovery;
    missing Git history is an error, never a successful preservation claim.
    """
    root = Path(root)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
    if git("show", "-s", "--format=%T", BASE).strip().decode() != TREE:
        raise AssertionError("Exact canonical main tree required")
    files = byte_count = appended_bytes = 0
    for row in git("ls-tree", "-r", "-z", BASE).split(b"\0"):
        if not row:
            continue
        metadata, raw_name = row.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        name = raw_name.decode()
        path = root / name
        if kind != "blob" or mode not in ("100644", "100755"):
            raise AssertionError("Only regular canonical Git entries expected")
        if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):
            raise AssertionError("Inherited regular file missing or replaced: " + name)
        if ("100755" if path.stat().st_mode & 0o111 else "100644") != mode:
            raise AssertionError("Inherited executable mode changed: " + name)
        raw = path.read_bytes()
        if name in DOCUMENT_APPENDICES:
            inherited = historical_document_before_authoring_append(name, raw)
            appended_bytes += len(raw) - len(inherited)
            raw = inherited
        elif name in ADAPTER_PATCHES:
            raw = historical_adapter_bytes(name, raw)
        elif name == "tests/proposed_spell_evidence_packet_validation.py":
            raw = historical_checker_bytes(root)
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != blob:
            raise AssertionError("Inherited canonical Git blob changed: " + name)
        files += 1
        byte_count += len(raw)
    return {"canonical_base": BASE, "canonical_tree": TREE,
        "inherited_files": files, "inherited_bytes": byte_count,
        "appended_bytes": appended_bytes, "finite_preservation_adapters": len(ADAPTER_PATCHES),
        "replaced_checker_files": 1, "all_inherited_blobs_and_modes_preserved": True}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_canonical_git(), sort_keys=True))
