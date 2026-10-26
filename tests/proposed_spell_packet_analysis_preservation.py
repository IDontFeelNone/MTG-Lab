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
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | CONDITIONAL_SOURCE_PATHS | SENSITIVITY_SOURCE_PATHS


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


# Exact finite successor for the separately authorized conditional pilot. The
# historical analysis constants above remain unchanged.
CONDITIONAL_SOURCE_PATHS = frozenset({"src/proposed_spell_packets/conditions.py"})
CONDITIONAL_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 44701,
               'baseline_sha256': '40ced5619bf2aaee4e077dda39431e3c25f0fcbacc7b291e33c53a8c965f722d',
               'appendix_bytes': 929,
               'appendix_sha256': '06cf9706ffdab1dfdfac9f6ee88f5a3dcff14b45ae637758aaa97ac7144ba6dc'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 99530,
                          'baseline_sha256': 'c13e2c88ca8186e65a94a4d495fe547dace71179158f0ceef92ba7249d6bb11a',
                          'appendix_bytes': 929,
                          'appendix_sha256': '06cf9706ffdab1dfdfac9f6ee88f5a3dcff14b45ae637758aaa97ac7144ba6dc'},
 'CHANGELOG.md': {'baseline_bytes': 64957,
                  'baseline_sha256': '1cfc984e081d4dfa45ef5d7d459e12f43fecf3d33f6f2fb323ee32f98cef3c8d',
                  'appendix_bytes': 929,
                  'appendix_sha256': '06cf9706ffdab1dfdfac9f6ee88f5a3dcff14b45ae637758aaa97ac7144ba6dc'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 94558,
                           'baseline_sha256': '6a193471b9a92f786afba78c843f66bce3ea9301b221ec5d41b9a78cbf88c772',
                           'appendix_bytes': 924,
                           'appendix_sha256': '59828605ec3d9dce8d812ead90806ea90d7a62324394267bcbbaa132709a5c1e'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 76793,
                       'baseline_sha256': '7170ec746b82ecaf5d784fb9c71064c18c2a6a78e3fc43afc5a926777b27007a',
                       'appendix_bytes': 924,
                       'appendix_sha256': '59828605ec3d9dce8d812ead90806ea90d7a62324394267bcbbaa132709a5c1e'},
 'docs/HANDOFF.md': {'baseline_bytes': 105350,
                     'baseline_sha256': '41405df121d588d2bffe498a289a0b36eeae9d3f8b15b8fac3611de0a5ccc47e',
                     'appendix_bytes': 924,
                     'appendix_sha256': '59828605ec3d9dce8d812ead90806ea90d7a62324394267bcbbaa132709a5c1e'},
 'docs/ROADMAP.md': {'baseline_bytes': 47458,
                     'baseline_sha256': 'bd1e6033ba9f45d5dc582c7ba7e635283c2db52b4e01aa6ad0ff26a85448af65',
                     'appendix_bytes': 924,
                     'appendix_sha256': '59828605ec3d9dce8d812ead90806ea90d7a62324394267bcbbaa132709a5c1e'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 118726,
                            'baseline_sha256': '6b9bfe703227e13ac4ac4c6cec9554b287ebc4a582c19216ea9f12df124afdfc',
                            'appendix_bytes': 924,
                            'appendix_sha256': '59828605ec3d9dce8d812ead90806ea90d7a62324394267bcbbaa132709a5c1e'}}
CONDITIONAL_CLI_PATCHES = [('from .validation import PACKET_NAMES\n',
  'from .validation import PACKET_NAMES\n'
  'from .conditions import evaluate, read_model, render as render_condition\n'),
 ('    comparison.add_argument("--json", action="store_true", help="Emit '
  'deterministic derived-report bytes")\n',
  '    comparison.add_argument("--json", action="store_true", help="Emit '
  'deterministic derived-report bytes")\n'
  '    evaluation = commands.add_parser("evaluate", help="Compute one '
  'explicitly authored fictional condition under selected assertions")\n'
  '    evaluation.add_argument("packet_id", help="Exact recorded packet '
  'identity")\n'
  '    evaluation.add_argument("--model", required=True, help="Separate '
  'explicit versioned condition-model JSON file")\n'
  '    evaluation.add_argument("--json", action="store_true", help="Emit '
  'canonical immutable computed-result bytes")\n'),
 ('            result = workspace.record(draft=args.draft, '
  'sealed=args.sealed)\n',
  '            result = workspace.record(draft=args.draft, '
  'sealed=args.sealed)\n'
  '        elif args.command == "evaluate":\n'
  '            report = evaluate(workspace, args.packet_id, '
  'read_model(args.model))\n'
  '            if args.json:\n'
  '                sys.stdout.buffer.write(report.canonical_bytes)\n'
  '            else:\n'
  '                print(render_condition(report))\n'
  '            return 0\n')]
CONDITIONAL_CLI_SHA256 = 'cc4a118c6da405792ae3de0d96a41cad204d1b8fdc1da1491b8656d7cb497012'


# Exact finite successor for the separately authorized missing-input sensitivity
# milestone. All historical analysis and conditional pins above remain intact.
SENSITIVITY_SOURCE_PATHS = frozenset({"src/proposed_spell_packets/sensitivity.py"})
SENSITIVITY_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 45630,
               'baseline_sha256': 'd7885ffefb69c6a018451f5c9b8c11be2d895d8fee0c46e83ecc1cc5612fdfb5',
               'appendix_bytes': 1054,
               'appendix_sha256': 'cb10ecebf347b1f9ac235e6176782ea95ecfe373f3cfff929cfc709dff4c6e30'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 100459,
                          'baseline_sha256': '9a9a7f52e201deadddbdfb2ae7a9eae020951675dca7bd70f772ed6864564790',
                          'appendix_bytes': 1054,
                          'appendix_sha256': 'cb10ecebf347b1f9ac235e6176782ea95ecfe373f3cfff929cfc709dff4c6e30'},
 'CHANGELOG.md': {'baseline_bytes': 65886,
                  'baseline_sha256': 'f6938b1e3d9048d9ef663afb2b743a6012d8f53c841802e24b69f314c09bc110',
                  'appendix_bytes': 1054,
                  'appendix_sha256': 'cb10ecebf347b1f9ac235e6176782ea95ecfe373f3cfff929cfc709dff4c6e30'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 95482,
                           'baseline_sha256': '90987bdf6627f84bc401f014b4597a4bdd9db9c9d8ba05f70ff217c5c7cb9122',
                           'appendix_bytes': 1049,
                           'appendix_sha256': 'b930291fb26228b94771256c950951a7ca1da10d7a101989539e4329b1848273'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 77717,
                       'baseline_sha256': '5d0ef26692be3df47a81bd6e965d56c61814d2d61ed5b41e9409a93e384b2337',
                       'appendix_bytes': 1049,
                       'appendix_sha256': 'b930291fb26228b94771256c950951a7ca1da10d7a101989539e4329b1848273'},
 'docs/HANDOFF.md': {'baseline_bytes': 106274,
                     'baseline_sha256': '93524ed275d2db82944fd08a1ed4b94fa747f4b62bb99d31d74cd2a25873d74c',
                     'appendix_bytes': 1049,
                     'appendix_sha256': 'b930291fb26228b94771256c950951a7ca1da10d7a101989539e4329b1848273'},
 'docs/ROADMAP.md': {'baseline_bytes': 48382,
                     'baseline_sha256': '39455cc7e3a45e0c19c2f02877b20324fbe257b2d0f94185d55a5f259ad929ab',
                     'appendix_bytes': 1049,
                     'appendix_sha256': 'b930291fb26228b94771256c950951a7ca1da10d7a101989539e4329b1848273'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 119650,
                            'baseline_sha256': '1fc7b74c107ffb8ca51f4bb6a81df1f529b1c8eaee83ce5533575ac72f9527ab',
                            'appendix_bytes': 1049,
                            'appendix_sha256': 'b930291fb26228b94771256c950951a7ca1da10d7a101989539e4329b1848273'}}


SENSITIVITY_CONDITION_SHA256 = {"baseline_sha256": "ebfe49ce04b8ecfc77cbd27fa74ff16a30b1dd8a4b0c4983f94c25e95ce36ca1",
                                "successor_sha256": "4004e59906649c5195e8c52d2bf410b555cc2b2f6fcc3947e6335a0145c6fe72"}
SENSITIVITY_CLI_SHA256 = "0c566b8802ba63e401b7f1f50d3cb43bb84f6883c0a8c2ea9d59c2421264f64d"
SENSITIVITY_CLI_PATCHES = [
    ("""from .validation import PACKET_NAMES
from .conditions import evaluate, read_model, render as render_condition


""", """from .validation import PACKET_NAMES
from .conditions import evaluate, read_model, render as render_condition
from .sensitivity import analyze as analyze_sensitivity, render as render_sensitivity


"""),
    ("""    evaluation.add_argument("--model", required=True, help="Separate explicit versioned condition-model JSON file")
    evaluation.add_argument("--json", action="store_true", help="Emit canonical immutable computed-result bytes")
    args = parser.parse_args(argv)
    try:
""", """    evaluation.add_argument("--model", required=True, help="Separate explicit versioned condition-model JSON file")
    evaluation.add_argument("--json", action="store_true", help="Emit canonical immutable computed-result bytes")
    sensitivity = commands.add_parser("sensitivity", help="Examine independent Boolean hypotheses for selected UNKNOWN assertion groups")
    sensitivity.add_argument("packet_id", help="Exact recorded packet identity")
    sensitivity.add_argument("--model", required=True, help="Exact explicit versioned condition-model JSON file")
    sensitivity.add_argument("--json", action="store_true", help="Emit canonical hypothetical-report bytes")
    args = parser.parse_args(argv)
    try:
"""),
    ("""        elif args.command == "record":
            result = workspace.record(draft=args.draft, sealed=args.sealed)
        elif args.command == "evaluate":
            report = evaluate(workspace, args.packet_id, read_model(args.model))
""", """        elif args.command == "record":
            result = workspace.record(draft=args.draft, sealed=args.sealed)
        elif args.command == "sensitivity":
            report = analyze_sensitivity(workspace, args.packet_id, read_model(args.model))
            if args.json:
                sys.stdout.buffer.write(report.canonical_bytes)
            else:
                print(render_sensitivity(report))
            return 0
        elif args.command == "evaluate":
            report = evaluate(workspace, args.packet_id, read_model(args.model))
"""),
]


def historical_conditional_cli_bytes(raw):
    """Reconstruct only the exact PR #212 CLI from this narrow successor."""
    if type(raw) is not bytes:
        raise AssertionError("Exact sensitivity CLI bytes required")
    if hashlib.sha256(raw).hexdigest() == CONDITIONAL_CLI_SHA256:
        return raw
    if hashlib.sha256(raw).hexdigest() != SENSITIVITY_CLI_SHA256:
        raise AssertionError("Exact sensitivity CLI successor changed")
    for before, after in reversed(SENSITIVITY_CLI_PATCHES):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact sensitivity CLI adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != CONDITIONAL_CLI_SHA256:
        raise AssertionError("Historical conditional CLI changed")
    return raw


def historical_document_before_sensitivity_append(path, raw):
    """Strip only the exact sensitivity appendix; preserve every historical body."""
    if (type(path) is not str or path not in SENSITIVITY_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named sensitivity document bytes are adapted")
    pin = SENSITIVITY_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact sensitivity appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-sensitivity historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact sensitivity appendix changed")
    return baseline


def historical_document_before_conditional_append(path, raw):
    """Strip only the exact conditional appendix, retaining the analysis body."""
    if (type(path) is not str or path not in CONDITIONAL_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named conditional-pilot document bytes are adapted")
    pin = CONDITIONAL_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_sensitivity_append(path, raw)
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact conditional-pilot appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-conditional historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact conditional-pilot appendix changed")
    return baseline


def historical_analysis_cli_bytes(raw):
    """Reconstruct the exact PR #211 CLI from the narrow conditional successor."""
    prior = EXACT_SUCCESSORS["src/proposed_spell_packets/__main__.py"]["successor_sha256"]
    if type(raw) is not bytes:
        raise AssertionError("Exact CLI bytes required")
    if hashlib.sha256(raw).hexdigest() not in (prior, CONDITIONAL_CLI_SHA256):
        raw = historical_conditional_cli_bytes(raw)
    if hashlib.sha256(raw).hexdigest() == prior:
        return raw
    if hashlib.sha256(raw).hexdigest() != CONDITIONAL_CLI_SHA256:
        raise AssertionError("Exact conditional CLI successor changed")
    for before, after in reversed(CONDITIONAL_CLI_PATCHES):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact conditional CLI adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != prior:
        raise AssertionError("Historical analysis CLI changed")
    return raw


def historical_document_before_analysis_append(path, raw):
    """Return the exact inherited document; reject all unaccounted suffixes."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES or type(raw) is not bytes:
        raise AssertionError("Only named analysis-pilot document bytes are adapted")
    pin = DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_conditional_append(path, raw)
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
            raw = historical_analysis_cli_bytes(raw)
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
