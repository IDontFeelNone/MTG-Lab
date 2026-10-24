"""Exact finite successor accounting for the read-only dependency analysis pilot.

Historical assertions compose through pinned suffixes and reversible adapters.
No broad path exclusion or second evidence inventory is introduced.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "99813ea7b98c1fc1a2deda31479464ef83a47c31"
TREE = "12aea934a43be4a13cb27fc33129dabf4238b5d8"
NEW_SOURCE_PATHS = frozenset({"src/proposed_spell_packets/analysis.py"})


def is_packet_analysis_addition(path, root=ROOT):
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS


DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 43823,
               'baseline_sha256': 'e28b4f2ff79fd1ab2d740057d6c55cb808d16c568805707fc147e532a1ca0fe2',
               'appendix_bytes': 878,
               'appendix_sha256': 'e4047008137caf5d6124c15296689bff37272e2342064dd7caa11ef934dc5dbf'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 98652,
                          'baseline_sha256': '3fbc9546057fba562792b9ef55618aa1ac5ee7233445d32c3e1a4d4018d10c8a',
                          'appendix_bytes': 878,
                          'appendix_sha256': 'e4047008137caf5d6124c15296689bff37272e2342064dd7caa11ef934dc5dbf'},
 'CHANGELOG.md': {'baseline_bytes': 64079,
                  'baseline_sha256': 'be07df33723801e8f2945bbf9949b7398d71c4a8881feb5fafbebce204ea57c7',
                  'appendix_bytes': 878,
                  'appendix_sha256': 'e4047008137caf5d6124c15296689bff37272e2342064dd7caa11ef934dc5dbf'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 93685,
                           'baseline_sha256': '7d279977482b197d7a981df1ea27d40e987a8faeb5e93eb158afc62c289c59e1',
                           'appendix_bytes': 873,
                           'appendix_sha256': 'd3e4bc3d3e85f39dec689b2bd78e2dce333919ed0b45ddfb08e4e4bf4d9cdc33'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 75920,
                       'baseline_sha256': '62b79a87b2200802c5a2b30e27bf02200aae702bff37275a69b32b4a87b7a3b6',
                       'appendix_bytes': 873,
                       'appendix_sha256': 'd3e4bc3d3e85f39dec689b2bd78e2dce333919ed0b45ddfb08e4e4bf4d9cdc33'},
 'docs/HANDOFF.md': {'baseline_bytes': 104477,
                     'baseline_sha256': '8cbeb455664d98b8c7502e40648fff447ba7e3bd53a14dbdee232d23e5c4a36e',
                     'appendix_bytes': 873,
                     'appendix_sha256': 'd3e4bc3d3e85f39dec689b2bd78e2dce333919ed0b45ddfb08e4e4bf4d9cdc33'},
 'docs/ROADMAP.md': {'baseline_bytes': 46585,
                     'baseline_sha256': '7db69e22b7d43424b352b1ba76d58e7ff4731fb28a39885590b2b11bd165fa23',
                     'appendix_bytes': 873,
                     'appendix_sha256': 'd3e4bc3d3e85f39dec689b2bd78e2dce333919ed0b45ddfb08e4e4bf4d9cdc33'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 117853,
                            'baseline_sha256': 'c63f3e94199174254652fc270bcc6c2ee859575ee3334b5765f457212a6329fb',
                            'appendix_bytes': 873,
                            'appendix_sha256': 'd3e4bc3d3e85f39dec689b2bd78e2dce333919ed0b45ddfb08e4e4bf4d9cdc33'}}

ADAPTER_PATCHES = {'tests/proposed_spell_packet_authoring_preservation.py': [('import hashlib\n',
                                                            'import hashlib\n'
                                                            'from '
                                                            'proposed_spell_packet_analysis_preservation '
                                                            'import (\n'
                                                            '    '
                                                            'is_packet_analysis_addition, '
                                                            'historical_document_before_analysis_append,\n'
                                                            ')\n'),
                                                           ('    return '
                                                            'path.relative_to(root).as_posix() '
                                                            'in '
                                                            'NEW_SOURCE_PATHS\n',
                                                            '    return '
                                                            '(path.relative_to(root).as_posix() '
                                                            'in '
                                                            'NEW_SOURCE_PATHS\n'
                                                            '            or '
                                                            'is_packet_analysis_addition(path, '
                                                            'root))\n'),
                                                           ('    size = '
                                                            'pin["baseline_bytes"]\n'
                                                            '    if len(raw) '
                                                            'not in',
                                                            '    size = '
                                                            'pin["baseline_bytes"]\n'
                                                            '    if len(raw) > '
                                                            'size + '
                                                            'pin["appendix_bytes"]:\n'
                                                            '        raw = '
                                                            'historical_document_before_analysis_append(path, '
                                                            'raw)\n'
                                                            '    if len(raw) '
                                                            'not in')],
 'tests/test_proposed_spell_packet_authoring_preservation.py': [('import '
                                                                 'hashlib\n',
                                                                 'import '
                                                                 'hashlib\n'
                                                                 'from '
                                                                 'proposed_spell_packet_analysis_preservation '
                                                                 'import '
                                                                 'historical_document_before_analysis_append\n'),
                                                                ('            '
                                                                 'raw = '
                                                                 '(guard.ROOT '
                                                                 '/ '
                                                                 'name).read_bytes()\n'
                                                                 '            '
                                                                 'old = '
                                                                 'guard.historical_document_before_authoring_append(name, '
                                                                 'raw)\n',
                                                                 '            '
                                                                 'raw = '
                                                                 'historical_document_before_analysis_append(name, '
                                                                 '(guard.ROOT '
                                                                 '/ '
                                                                 'name).read_bytes())\n'
                                                                 '            '
                                                                 'old = '
                                                                 'guard.historical_document_before_authoring_append(name, '
                                                                 'raw)\n')]}
ADAPTER_BASE_SHA256 = {'tests/proposed_spell_packet_authoring_preservation.py': 'b5440eeacc7c3e8314dce583efd5567481b7a27af3967f237248351ce4768860',
 'tests/test_proposed_spell_packet_authoring_preservation.py': '03d1a7bd3af1f016b1f98a4e21a3e8a147fb3acd92715c8d7a1750e876c0a084'}
EXACT_SUCCESSORS = {'src/proposed_spell_packets/__main__.py': {'baseline_sha256': 'e21a90062b93966f0721d2c96c5a9de75cdad0eb47ece17dc5fc41054abdbc2c',
                                            'successor_sha256': 'a105b2ff3388bc817f1b17b0571053184b223dcd5917379107640d0917823918'}}


def historical_document_before_analysis_append(path, raw):
    """Return the exact inherited document; reject all unaccounted suffixes."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES or type(raw) is not bytes:
        raise AssertionError("Only named analysis-pilot document bytes are adapted")
    pin = DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact analysis-pilot appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-analysis historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact analysis-pilot appendix changed")
    return baseline


def historical_adapter_bytes(name, raw):
    if type(name) is not str or name not in ADAPTER_PATCHES or type(raw) is not bytes:
        raise AssertionError("Only explicitly named analysis-pilot adapters are accepted")
    for before, after in reversed(ADAPTER_PATCHES[name]):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact finite analysis-pilot adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != ADAPTER_BASE_SHA256[name]:
        raise AssertionError("Canonical pre-analysis adapter bytes changed")
    return raw


def audit_canonical_git(root=ROOT):
    """Compare every inherited blob/mode with the required canonical main.

    This explicit audit requires actual Git history. Discovery remains valid in
    shallow disposable publication checkouts and never claims source reproduction.
    """
    root = Path(root)
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
    if git("show", "-s", "--format=%T", BASE).strip().decode() != TREE:
        raise AssertionError("Exact canonical main tree required")
    files = byte_count = appended_bytes = 0
    groups = {}
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
            inherited = historical_document_before_analysis_append(name, raw)
            appended_bytes += len(raw) - len(inherited)
            raw = inherited
        elif name in ADAPTER_PATCHES:
            raw = historical_adapter_bytes(name, raw)
        elif name in EXACT_SUCCESSORS:
            pins = EXACT_SUCCESSORS[name]
            if hashlib.sha256(raw).hexdigest() != pins["successor_sha256"]:
                raise AssertionError("Exact analysis successor changed: " + name)
            raw = git("show", BASE + ":" + name)
            if hashlib.sha256(raw).hexdigest() != pins["baseline_sha256"]:
                raise AssertionError("Exact analysis baseline changed: " + name)
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != blob:
            raise AssertionError("Inherited canonical Git blob changed: " + name)
        group = name.split("/", 1)[0] if "/" in name else "root"
        groups[group] = groups.get(group, 0) + 1
        files += 1
        byte_count += len(raw)
    return {"canonical_base": BASE, "canonical_tree": TREE,
        "inherited_files": files, "inherited_bytes": byte_count,
        "groups": groups, "appended_bytes": appended_bytes,
        "finite_preservation_adapters": len(ADAPTER_PATCHES),
        "exact_successor_files": len(EXACT_SUCCESSORS),
        "all_inherited_blobs_and_modes_preserved": True}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_canonical_git(), sort_keys=True))
