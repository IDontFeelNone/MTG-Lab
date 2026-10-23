"""Exact successor views for one retained-only packet design.

Only eight named retained files and eight pinned document suffixes are added.
This test-side helper owns no source projection or gameplay authority.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "80c7cee9c1448c97a76f7a9139b405cbcb4c3613"
TREE = "d3d810a7ce77cd5ce15074852628df82b0ad82c2"
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/" + name
    for name in ("contract.json", "manifest.json", "design-assessment.json",
                 "packet-a-conditional.json", "packet-b-missing.json",
                 "packet-c-unsupported.json", "packet-d-conflict.json",
                 "packet-e-compatibility.json")
)


def is_proposed_spell_evidence_packet_addition(path, root=ROOT):
    return path.relative_to(root).as_posix() in NEW_REVIEW_PATHS


DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 39362,
               'baseline_sha256': 'ccbaef6f947ede5759437a12d98ebbad1a726c5a63a6fb65faccde67c5067d7c',
               'appendix_bytes': 1861,
               'appendix_sha256': '9b4bd22a8ead630e6311559e1e84ed6458482bd45cd28e4ff4d901a3a964d5cb'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 94191,
                          'baseline_sha256': '7e5b2911bc81bfc03662812ebba160c4897d76afffcc60b46bc987f4deb0c340',
                          'appendix_bytes': 1861,
                          'appendix_sha256': '9b4bd22a8ead630e6311559e1e84ed6458482bd45cd28e4ff4d901a3a964d5cb'},
 'CHANGELOG.md': {'baseline_bytes': 59618,
                  'baseline_sha256': 'dde26ac91777647a67412a178ac51d3afcc68f33bf394d6fb171f76b633be88b',
                  'appendix_bytes': 1861,
                  'appendix_sha256': '9b4bd22a8ead630e6311559e1e84ed6458482bd45cd28e4ff4d901a3a964d5cb'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 89234,
                           'baseline_sha256': '9a22882f30eeda912393cdcef77eef1d1837cbdd5eb993d68e63e85001221492',
                           'appendix_bytes': 1856,
                           'appendix_sha256': '63b490b639263aed52a62f6a8727689ba91dd31af41ae84bf6c8bc9f9d592e5e'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 71469,
                       'baseline_sha256': '422df6c65c04ca8f228c3b0bf11f306f72326ecacdb556b86a8f4b1799afaeae',
                       'appendix_bytes': 1856,
                       'appendix_sha256': '63b490b639263aed52a62f6a8727689ba91dd31af41ae84bf6c8bc9f9d592e5e'},
 'docs/HANDOFF.md': {'baseline_bytes': 100026,
                     'baseline_sha256': 'fae96bc2e29387852214c8d6f43322f35af2778422eeeb2dd781c16d34627d9c',
                     'appendix_bytes': 1856,
                     'appendix_sha256': '63b490b639263aed52a62f6a8727689ba91dd31af41ae84bf6c8bc9f9d592e5e'},
 'docs/ROADMAP.md': {'baseline_bytes': 42134,
                     'baseline_sha256': '706b71f4abc78bc3cb40875ced5f7c4752c456d582926b3d3590377854c9deb4',
                     'appendix_bytes': 1856,
                     'appendix_sha256': '63b490b639263aed52a62f6a8727689ba91dd31af41ae84bf6c8bc9f9d592e5e'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 113402,
                            'baseline_sha256': '369c7aacd1692dd6635678448c8e22669b95c52dad37e23e32d2dc17f29eeb62',
                            'appendix_bytes': 1856,
                            'appendix_sha256': '63b490b639263aed52a62f6a8727689ba91dd31af41ae84bf6c8bc9f9d592e5e'}}


def historical_document_before_packet_append(path, raw):
    """Accept an exact canonical document or that document plus its pinned suffix."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES or type(raw) is not bytes:
        raise AssertionError("Only named packet-design document bytes are adapted")
    pin = DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact packet-design appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Canonical inherited document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact packet-design appendix changed")
    return baseline


ADAPTER_PATCHES = {'tests/casting_permission_family_preservation.py': [('import hashlib\n',
                                                      'import hashlib\n'
                                                      'from proposed_spell_evidence_packet_preservation import (\n'
                                                      '    is_proposed_spell_evidence_packet_addition,\n'
                                                      '    historical_document_before_packet_append,\n'
                                                      ')\n'),
                                                     ('return path.relative_to(root).as_posix() in '
                                                      'NEW_SOURCE_PATHS | NEW_REVIEW_PATHS',
                                                      'return (path.relative_to(root).as_posix() in '
                                                      'NEW_SOURCE_PATHS | NEW_REVIEW_PATHS\n'
                                                      '            or '
                                                      'is_proposed_spell_evidence_packet_addition(path, root))'),
                                                     ('    pin = DOCUMENT_APPENDICES[path]\n'
                                                      '    size = pin["baseline_bytes"]\n',
                                                      '    pin = DOCUMENT_APPENDICES[path]\n'
                                                      '    if len(raw) > pin["baseline_bytes"] + '
                                                      'pin["appendix_bytes"]:\n'
                                                      '        raw = '
                                                      'historical_document_before_packet_append(path, raw)\n'
                                                      '    size = pin["baseline_bytes"]\n'),
                                                     ('"""Exclude only the seven named modules and eight named '
                                                      'package files."""',
                                                      '"""Select the named family files and exact finite '
                                                      'successor design files."""')],
 'tests/test_casting_permission_family_preservation.py': [('import casting_permission_family_preservation as '
                                                           'guard\n',
                                                           'import casting_permission_family_preservation as '
                                                           'guard\n'
                                                           'from proposed_spell_evidence_packet_preservation '
                                                           'import historical_document_before_packet_append\n'),
                                                          ('                raw = (guard.ROOT / '
                                                           'name).read_bytes()\n',
                                                           '                raw = '
                                                           'historical_document_before_packet_append(name, '
                                                           '(guard.ROOT / name).read_bytes())\n')]}
ADAPTER_BASE_SHA256 = {'tests/casting_permission_family_preservation.py': 'b09cd9e4f35b16984a8479614e7069360a8f86f43dc2b9102324793c27a2e6fc',
 'tests/test_casting_permission_family_preservation.py': '37838bf122a856fbaf3f732a7b2817e2d84cee026d50a5005ac3288ceb7c4b43'}


def historical_adapter_bytes(name, raw):
    """Reverse only the two named finite compositions; original assertions survive."""
    if type(name) is not str or name not in ADAPTER_PATCHES or type(raw) is not bytes:
        raise AssertionError("Only explicitly named packet-design adapters are accepted")
    for before, after in reversed(ADAPTER_PATCHES[name]):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact finite packet-design adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != ADAPTER_BASE_SHA256[name]:
        raise AssertionError("Canonical historical adapter bytes changed")
    return raw


def audit_canonical_git(root=ROOT):
    """Independently compare every inherited Git blob/mode against canonical main.

    Explicit local audit only: missing canonical objects are errors, never a
    successful audit or a source-verification claim. No freeze fixture is added.
    """
    root = Path(root)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
    if git("show", "-s", "--format=%T", BASE).strip().decode() != TREE:
        raise AssertionError("Exact canonical main tree required")
    groups = {}
    byte_count = appended_bytes = 0
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
            inherited = historical_document_before_packet_append(name, raw)
            appended_bytes += len(raw) - len(inherited)
            raw = inherited
        elif name in ADAPTER_PATCHES:
            raw = historical_adapter_bytes(name, raw)
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != blob:
            raise AssertionError("Inherited canonical Git blob changed: " + name)
        group = name.split("/", 1)[0] if "/" in name else "root"
        groups[group] = groups.get(group, 0) + 1
        byte_count += len(raw)
    return {"canonical_base": BASE, "canonical_tree": TREE,
            "inherited_files": sum(groups.values()), "inherited_bytes": byte_count,
            "groups": groups, "appended_bytes": appended_bytes,
            "exact_finite_adapter_files": len(ADAPTER_PATCHES),
            "all_inherited_blobs_and_modes_preserved": True}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_canonical_git(), sort_keys=True))
