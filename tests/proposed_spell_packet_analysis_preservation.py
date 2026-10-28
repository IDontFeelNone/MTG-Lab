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
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | CONDITIONAL_SOURCE_PATHS | SENSITIVITY_SOURCE_PATHS | ALTERNATIVES_SOURCE_PATHS | COMPOUND_SOURCE_PATHS | CARD_RULES_PILOT_SOURCE_PATHS | MANA_REASONING_SOURCE_PATHS


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



# Exact finite successor for the separately authorized named-alternative
# comparison. Historical analysis, condition and sensitivity pins stay intact.
ALTERNATIVES_SOURCE_PATHS = frozenset({"src/proposed_spell_packets/alternatives.py"})
ALTERNATIVES_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 46684,
               'baseline_sha256': '1c8f1fbc2d40a4073dc268353717e68aa15e372c2fe90d700f776d6e2a9cb41f',
               'appendix_bytes': 1396,
               'appendix_sha256': '625156737c8af7c453114cfffe681220e93e75229167ac9ba94f8b2b8af044d1'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 101513,
                          'baseline_sha256': '247f1c63d9ca504deddfd700ae936383d2f2fe6bd0b2ab26a8b92c8d883d3a9d',
                          'appendix_bytes': 1396,
                          'appendix_sha256': '625156737c8af7c453114cfffe681220e93e75229167ac9ba94f8b2b8af044d1'},
 'CHANGELOG.md': {'baseline_bytes': 66940,
                  'baseline_sha256': '154758548a8b11bb3d38fe87037f6714bf5151667fa9880efa34b22f44f4636b',
                  'appendix_bytes': 1396,
                  'appendix_sha256': '625156737c8af7c453114cfffe681220e93e75229167ac9ba94f8b2b8af044d1'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 96531,
                           'baseline_sha256': 'bcb094e6a8c8658b7686311f2391e34f89e2264a543dda4cb2298d6f17767576',
                           'appendix_bytes': 1391,
                           'appendix_sha256': 'd287f4ddb11ecfa042717c2fb19de7ee14d6f5dca15859821876c6f1a002571b'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 78766,
                       'baseline_sha256': 'd4a0099940c05cc622538492b39fc4ecf0fc1b42e4ebfbd93ccac68fc4b70e51',
                       'appendix_bytes': 1391,
                       'appendix_sha256': 'd287f4ddb11ecfa042717c2fb19de7ee14d6f5dca15859821876c6f1a002571b'},
 'docs/HANDOFF.md': {'baseline_bytes': 107323,
                     'baseline_sha256': '25ba73ee2dbb17bd477dca220a2ce097a2a52c703fc77aa8db0030a0403703a0',
                     'appendix_bytes': 1391,
                     'appendix_sha256': 'd287f4ddb11ecfa042717c2fb19de7ee14d6f5dca15859821876c6f1a002571b'},
 'docs/ROADMAP.md': {'baseline_bytes': 49431,
                     'baseline_sha256': '423d14f8cb7cfa265c5d44307b0092b41a5e1108aec6a5a3ee2b5df9c7d36d4e',
                     'appendix_bytes': 1391,
                     'appendix_sha256': 'd287f4ddb11ecfa042717c2fb19de7ee14d6f5dca15859821876c6f1a002571b'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 120699,
                            'baseline_sha256': 'df63c0369057cdbdcbad1a8908935575c7d1b7e1f3ac424dab3ee2b7ad6d9b38',
                            'appendix_bytes': 1391,
                            'appendix_sha256': 'd287f4ddb11ecfa042717c2fb19de7ee14d6f5dca15859821876c6f1a002571b'}}
ALTERNATIVES_CLI_SHA256 = 'a62209a6040efae78c11d2a665dcb35c0d55ed2ff2ab0764dabb346171d3a669'
ALTERNATIVES_CLI_PATCHES = [('from .conditions import evaluate, read_model, render as render_condition\n'
  'from .sensitivity import analyze as analyze_sensitivity, render as render_sensitivity\n'
  '\n'
  '\n',
  'from .conditions import evaluate, read_model, render as render_condition\n'
  'from .sensitivity import analyze as analyze_sensitivity, render as render_sensitivity\n'
  'from .alternatives import evaluate as evaluate_alternatives, read_definition, render as '
  'render_alternatives\n'
  '\n'
  '\n'),
 ('    sensitivity.add_argument("--model", required=True, help="Exact explicit versioned '
  'condition-model JSON file")\n'
  '    sensitivity.add_argument("--json", action="store_true", help="Emit canonical '
  'hypothetical-report bytes")\n'
  '    args = parser.parse_args(argv)\n'
  '    try:\n',
  '    sensitivity.add_argument("--model", required=True, help="Exact explicit versioned '
  'condition-model JSON file")\n'
  '    sensitivity.add_argument("--json", action="store_true", help="Emit canonical '
  'hypothetical-report bytes")\n'
  '    alternatives = commands.add_parser("evaluate-alternatives", help="Compare explicitly listed '
  'fictional alternatives against shared authored requirements")\n'
  '    alternatives.add_argument("packet_id", help="Exact recorded packet identity")\n'
  '    alternatives.add_argument("--requirements", required=True, help="Explicit versioned '
  'shared-requirement definition JSON file")\n'
  '    alternatives.add_argument("--json", action="store_true", help="Emit canonical computed '
  'comparison-report bytes")\n'
  '    args = parser.parse_args(argv)\n'
  '    try:\n'),
 ('        elif args.command == "record":\n'
  '            result = workspace.record(draft=args.draft, sealed=args.sealed)\n'
  '        elif args.command == "sensitivity":\n'
  '            report = analyze_sensitivity(workspace, args.packet_id, read_model(args.model))\n',
  '        elif args.command == "record":\n'
  '            result = workspace.record(draft=args.draft, sealed=args.sealed)\n'
  '        elif args.command == "evaluate-alternatives":\n'
  '            report = evaluate_alternatives(workspace, args.packet_id, '
  'read_definition(args.requirements))\n'
  '            if args.json:\n'
  '                sys.stdout.buffer.write(report.canonical_bytes)\n'
  '            else:\n'
  '                print(render_alternatives(report))\n'
  '            return 0\n'
  '        elif args.command == "sensitivity":\n'
  '            report = analyze_sensitivity(workspace, args.packet_id, read_model(args.model))\n')]



# Exact finite successor for the owner-authorized compound v2 capability.
# All historical constants and appendix bytes above remain unchanged.
COMPOUND_SOURCE_PATHS = frozenset({
    "src/proposed_spell_packets/conditions_v2.py",
    "src/proposed_spell_packets/sensitivity_v2.py",
    "src/proposed_spell_packets/alternatives_v2.py",
    "src/proposed_spell_packets/dispatch.py",
})
COMPOUND_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 48080,
               'baseline_sha256': '0a5848d5b174af80bd389313010bafbd9320f64c8cdba1cea780ca121008ee49',
               'appendix_bytes': 1688,
               'appendix_sha256': '8b2cbc3e290be4b0b552f77048e580ae20013423730a30500c9fa6979ce614cb'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 102909,
                          'baseline_sha256': '60cdf7b67132a88541638136d30b57b7658128190de8d681f5346d7fcf63facf',
                          'appendix_bytes': 1688,
                          'appendix_sha256': '8b2cbc3e290be4b0b552f77048e580ae20013423730a30500c9fa6979ce614cb'},
 'CHANGELOG.md': {'baseline_bytes': 68336,
                  'baseline_sha256': '4a21472657b29823dbfeda2e152eb42eba7256d76ce25d0e339c6d7a000394b8',
                  'appendix_bytes': 1688,
                  'appendix_sha256': '8b2cbc3e290be4b0b552f77048e580ae20013423730a30500c9fa6979ce614cb'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 97922,
                           'baseline_sha256': 'f7084d1a83d99cbb9b7516689a0df6d20f13473d74033d00027c03f056e78084',
                           'appendix_bytes': 1683,
                           'appendix_sha256': '3a8406cf7671164dcd8a4dd895a48804a663f66a912495d67b31f5a7a0a26084'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 80157,
                       'baseline_sha256': 'e595d2bbf29c6d1ae380bda00c67a664741c83545099bdf133e13da31a00c2d8',
                       'appendix_bytes': 1683,
                       'appendix_sha256': '3a8406cf7671164dcd8a4dd895a48804a663f66a912495d67b31f5a7a0a26084'},
 'docs/HANDOFF.md': {'baseline_bytes': 108714,
                     'baseline_sha256': 'cb3a4bae8dbd6885bb666f403237cba2880069d0313fa12b33b9703dc9065cc4',
                     'appendix_bytes': 1683,
                     'appendix_sha256': '3a8406cf7671164dcd8a4dd895a48804a663f66a912495d67b31f5a7a0a26084'},
 'docs/ROADMAP.md': {'baseline_bytes': 50822,
                     'baseline_sha256': '642a321d25ca3b721647dbe77e36874af05f685b9b1fc3c5b66d8791a14beaf3',
                     'appendix_bytes': 1683,
                     'appendix_sha256': '3a8406cf7671164dcd8a4dd895a48804a663f66a912495d67b31f5a7a0a26084'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 122090,
                            'baseline_sha256': '92b733a9ace915bb44efc8cfaa935b655f8286ba46aa2c587ad35098ea4f9411',
                            'appendix_bytes': 1683,
                            'appendix_sha256': '3a8406cf7671164dcd8a4dd895a48804a663f66a912495d67b31f5a7a0a26084'}}


# Exact finite additions; no directory-wide exception is introduced.
CARD_RULES_PILOT_SOURCE_PATHS = frozenset(
    "src/card_rules_pilot/" + name for name in (
        "__init__.py", "__main__.py", "contract.py", "pilot.py",
        "authored.py", "cards.py", "rules.py"))


# Exact finite successor for the bounded Card–Rules review pilot.
PILOT_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 49768,
               'baseline_sha256': '1922e4d54f9f36662b2d92fd57d8bba4382c2fc65abcf03edce8c28d4fcbc8a9',
               'appendix_bytes': 1533,
               'appendix_sha256': '68780d354423e5785a5fcc1683247aa82131f53f62277b1630a584046f6fe337'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 104597,
                          'baseline_sha256': '3d028e5eb740b356a36c666de5e0d01d4f1b3991e4a895c0ddd4e440d8a1f8ef',
                          'appendix_bytes': 1533,
                          'appendix_sha256': '68780d354423e5785a5fcc1683247aa82131f53f62277b1630a584046f6fe337'},
 'CHANGELOG.md': {'baseline_bytes': 70024,
                  'baseline_sha256': '4e8559cbc2b1ecbbc03fbf8fd7cabbd71daa0bc380ffec13c3fe4c525f20a4d8',
                  'appendix_bytes': 1533,
                  'appendix_sha256': '68780d354423e5785a5fcc1683247aa82131f53f62277b1630a584046f6fe337'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 99605,
                           'baseline_sha256': 'a4c3d7ef33e89e43fac92893fead3affe1de855f5b23d39c3c158920bab76f0b',
                           'appendix_bytes': 1528,
                           'appendix_sha256': '52c0c299f945b82e4096cfe7ecc5b394743a2672b010f4ca6401194dbb1fd953'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 81840,
                       'baseline_sha256': '5f495d58b91e0fdd3b232ad1b6c44592538d65b4b98f79d24c90aedbef6ff32b',
                       'appendix_bytes': 1528,
                       'appendix_sha256': '52c0c299f945b82e4096cfe7ecc5b394743a2672b010f4ca6401194dbb1fd953'},
 'docs/HANDOFF.md': {'baseline_bytes': 110397,
                     'baseline_sha256': '3ce0ca28ee3cfbdb643fe453be4c15bdc15f488b1614dda8ae4500e8708b3e1f',
                     'appendix_bytes': 1528,
                     'appendix_sha256': '52c0c299f945b82e4096cfe7ecc5b394743a2672b010f4ca6401194dbb1fd953'},
 'docs/ROADMAP.md': {'baseline_bytes': 52505,
                     'baseline_sha256': '0b2ebb078580afb1c638a34197c76eef239d3911adc2e7bf106797306e5044b1',
                     'appendix_bytes': 1528,
                     'appendix_sha256': '52c0c299f945b82e4096cfe7ecc5b394743a2672b010f4ca6401194dbb1fd953'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 123773,
                            'baseline_sha256': 'aa8dd87004af929d41661f399a3681320f06fb6aa86bee8ba3dea6c856043d92',
                            'appendix_bytes': 1528,
                            'appendix_sha256': '52c0c299f945b82e4096cfe7ecc5b394743a2672b010f4ca6401194dbb1fd953'}}


# Exact finite successor for bounded classification reasoning; existing pins stay intact.
MANA_REASONING_SOURCE_PATHS = frozenset({
    "src/card_rules_pilot/reasoning.py",
    "src/card_rules_pilot/reasoning_policy.py",
})
MANA_REASONING_DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 51301,
               'baseline_sha256': 'a989941cac649d77af5b18a85c485f4bffcae2f6bbcc4f27c38a7870924d16fd',
               'appendix_bytes': 1621,
               'appendix_sha256': '67094c7962efe386f7139831ac7677b736fb1b2137ecc635440187a28130f5f0'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 106130,
                          'baseline_sha256': 'df2fed4dfc4403924c645cb67c6886908d411b6f3c96706231f5c472a3215fb3',
                          'appendix_bytes': 1621,
                          'appendix_sha256': '67094c7962efe386f7139831ac7677b736fb1b2137ecc635440187a28130f5f0'},
 'CHANGELOG.md': {'baseline_bytes': 71557,
                  'baseline_sha256': 'e0031a038871f965164a064ccd04f29ffa6e26e410e6463281b16ec5e6df723a',
                  'appendix_bytes': 1621,
                  'appendix_sha256': '67094c7962efe386f7139831ac7677b736fb1b2137ecc635440187a28130f5f0'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 101133,
                           'baseline_sha256': 'e00a88aca8cd8afcc1808d45a37593b4c337260a7559e5696e297bc518465c68',
                           'appendix_bytes': 1616,
                           'appendix_sha256': 'efed1b1e1530a0201b68711491bcf8404d2ac7fa1787b82394e947238b201624'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 83368,
                       'baseline_sha256': '58b7eb6cc70959bdb565a36bd3b94431cf0869d6aabae5c3ebb75144d7d22f03',
                       'appendix_bytes': 1616,
                       'appendix_sha256': 'efed1b1e1530a0201b68711491bcf8404d2ac7fa1787b82394e947238b201624'},
 'docs/HANDOFF.md': {'baseline_bytes': 111925,
                     'baseline_sha256': '048c6236789d042a2dfc14173508731a555de5e3293b6c8e335250195912c545',
                     'appendix_bytes': 1616,
                     'appendix_sha256': 'efed1b1e1530a0201b68711491bcf8404d2ac7fa1787b82394e947238b201624'},
 'docs/ROADMAP.md': {'baseline_bytes': 54033,
                     'baseline_sha256': '27bafc9d6d936d036a15e6e80f7e7b26da0a64f814178c415fd6a61f9e522244',
                     'appendix_bytes': 1616,
                     'appendix_sha256': 'efed1b1e1530a0201b68711491bcf8404d2ac7fa1787b82394e947238b201624'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 125301,
                            'baseline_sha256': 'c4ff87c2b88a386e4e61a60fcae8e3ac25dd6b6d9e56292cc2c4943ec262710d',
                            'appendix_bytes': 1616,
                            'appendix_sha256': 'efed1b1e1530a0201b68711491bcf8404d2ac7fa1787b82394e947238b201624'}}


# Exact reversible public API/CLI integration against PR #216 main. These files
# remain finite post-historical additions to earlier guards; this separate check
# proves their inherited content independently of that source-path accounting.
MANA_REASONING_SOURCE_PATCHES = {'src/card_rules_pilot/__init__.py': [("__all__ = ['PLAN_ID', 'PilotError', 'InterpretationCandidate', "
                                       "'ReviewReport',\n"
                                       "           'fixed_plan', 'load_pilot', 'render']\n",
                                       "__all__ = ['PLAN_ID', 'PilotError', 'InterpretationCandidate', "
                                       "'ReviewReport',\n"
                                       "           'fixed_plan', 'load_pilot', 'render']\n"
                                       '\n'
                                       'from .reasoning import load_reasoning, render_reasoning, '
                                       'ManaEvidenceReasoning, ReasoningReport\n'
                                       '\n'
                                       "__all__ += ['load_reasoning', 'render_reasoning', "
                                       "'ManaEvidenceReasoning', 'ReasoningReport']\n")],
 'src/card_rules_pilot/__main__.py': [("    compare = commands.add_parser('compare', help='all seven pending "
                                       "proposals')\n"
                                       "    compare.add_argument('--json', action='store_true')\n"
                                       "    commands.add_parser('check', help='explicit read-only byte "
                                       "reproduction check of retained candidates/report')\n"
                                       '    args = parser.parse_args(argv)\n',
                                       "    compare = commands.add_parser('compare', help='all seven pending "
                                       "proposals')\n"
                                       "    compare.add_argument('--json', action='store_true')\n"
                                       "    analyze = commands.add_parser('analyze', help='computed "
                                       "conditional evidence analysis for one subject')\n"
                                       "    analyze.add_argument('subject_id')\n"
                                       "    analyze.add_argument('--json', action='store_true')\n"
                                       "    for name in ('analyze-all', 'review-impact'):\n"
                                       "        derived = commands.add_parser(name, help='bounded computed "
                                       "pending-review reasoning')\n"
                                       "        derived.add_argument('--json', action='store_true')\n"
                                       "    commands.add_parser('check', help='explicit read-only byte "
                                       "reproduction check of retained candidates/report')\n"
                                       '    args = parser.parse_args(argv)\n'),
                                      ('            '
                                       'expected_query_snapshot_id=args.expected_query_snapshot_id,\n'
                                       '            expected_plan_id=args.expected_plan_id)\n'
                                       "        if args.command == 'check':\n"
                                       '            report = pilot.comparison()\n'
                                       '            directory = args.plan.parent\n',
                                       '            '
                                       'expected_query_snapshot_id=args.expected_query_snapshot_id,\n'
                                       '            expected_plan_id=args.expected_plan_id)\n'
                                       "        if args.command in ('analyze', 'analyze-all', "
                                       "'review-impact'):\n"
                                       '            from .reasoning import _from_pilot, render_reasoning\n'
                                       '            reasoning = _from_pilot(pilot)\n'
                                       '            document = (reasoning.subject(args.subject_id) if '
                                       "args.command == 'analyze'\n"
                                       '                else reasoning.comparison() if args.command == '
                                       "'analyze-all'\n"
                                       '                else reasoning.review_impact())\n'
                                       '            sys.stdout.write(document.to_json() if args.json else '
                                       'render_reasoning(document))\n'
                                       "        elif args.command == 'check':\n"
                                       '            report = pilot.comparison()\n'
                                       '            directory = args.plan.parent\n')]}
MANA_REASONING_SOURCE_SHA256 = {'src/card_rules_pilot/__init__.py': {'baseline_sha256': 'ec4e10c5f5595541208ca52b683cb3b60a89ccb1426b03989d91a4a1e580223c',
                                      'successor_sha256': '2093c7424b37f6106539fd705bd5f92fad3265e57f91f70b78f6f77b85a25feb'},
 'src/card_rules_pilot/__main__.py': {'baseline_sha256': '2176be0b968e46585403b619b7b5507eb466320d2155859dc50e46b157bf8478',
                                      'successor_sha256': 'c8caad5badb9da31d6db5a8b45457a5c4bee4e26b63c333fa77e856b990d427d'}}


def historical_mana_reasoning_source_bytes(name, raw):
    """Reconstruct only the two exact public integration predecessors."""
    if type(name) is not str or name not in MANA_REASONING_SOURCE_PATCHES or type(raw) is not bytes:
        raise AssertionError("Only exact mana reasoning API/CLI bytes are adapted")
    pins = MANA_REASONING_SOURCE_SHA256[name]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pins['baseline_sha256']:
        return raw
    if digest != pins['successor_sha256']:
        raise AssertionError("Exact mana reasoning API/CLI successor changed")
    for old, new in reversed(MANA_REASONING_SOURCE_PATCHES[name]):
        before, after = old.encode(), new.encode()
        if raw.count(after) != 1:
            raise AssertionError("Exact mana reasoning integration snippet changed")
        raw = raw.replace(after, before, 1)
    if hashlib.sha256(raw).hexdigest() != pins['baseline_sha256']:
        raise AssertionError("PR #216 canonical API/CLI bytes changed")
    return raw


def historical_document_before_mana_reasoning_append(path, raw):
    """Remove only eight exact reasoning suffixes, retaining PR #216 bytes."""
    if (type(path) is not str or path not in MANA_REASONING_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named mana reasoning document bytes are adapted")
    pin = MANA_REASONING_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact mana reasoning appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("PR #216 canonical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact mana reasoning appendix changed")
    return baseline


def historical_document_before_card_rules_pilot_append(path, raw):
    """Remove only these exact eight appendices, retaining canonical-base bytes."""
    if (type(path) is not str or path not in PILOT_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named Card–Rules pilot document bytes are adapted")
    pin = PILOT_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_mana_reasoning_append(path, raw)
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact Card–Rules pilot appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-pilot canonical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact Card–Rules pilot appendix changed")
    return baseline


def historical_document_before_compound_append(path, raw):
    """Remove only the exact named compound appendix; retain all prior bytes."""
    if (type(path) is not str or path not in COMPOUND_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named compound document bytes are adapted")
    pin = COMPOUND_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_card_rules_pilot_append(path, raw)
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact compound appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-compound historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact compound appendix changed")
    return baseline


# Only these exact public API/CLI dispatch snippets may precede v1 calculation.
COMPOUND_DISPATCH_PATCHES = {'src/proposed_spell_packets/__main__.py': [('from .conditions import '
                                             'evaluate, read_model, render as '
                                             'render_condition\n'
                                             'from .sensitivity import analyze '
                                             'as analyze_sensitivity, render '
                                             'as render_sensitivity\n'
                                             'from .alternatives import '
                                             'evaluate as '
                                             'evaluate_alternatives, '
                                             'read_definition, render as '
                                             'render_alternatives\n',
                                             'from .dispatch import (evaluate, '
                                             'read_model, render_condition,\n'
                                             '                       '
                                             'analyze_sensitivity, '
                                             'render_sensitivity,\n'
                                             '                       '
                                             'evaluate_alternatives, '
                                             'read_definition, '
                                             'render_alternatives)\n')],
 'src/proposed_spell_packets/conditions.py': [('    """Fresh boundary '
                                               'validation once, then compute '
                                               'solely from owned '
                                               'snapshots."""\n',
                                               '    """Fresh boundary '
                                               'validation once, then compute '
                                               'solely from owned '
                                               'snapshots."""\n'
                                               '    from . import '
                                               'conditions_v2 as v2\n'
                                               '    if type(model) is '
                                               'v2.ConditionModel or '
                                               '(type(model) is dict and '
                                               'model.get("model_version") == '
                                               'v2.MODEL_VERSION):\n'
                                               '        return '
                                               'v2.evaluate(workspace, '
                                               'packet_id, model)\n'),
                                              ('def render(result):\n',
                                               'def render(result):\n'
                                               '    from . import '
                                               'conditions_v2 as v2\n'
                                               '    if type(result) is '
                                               'v2.ConditionResult:\n'
                                               '        return '
                                               'v2.render(result)\n')],
 'src/proposed_spell_packets/sensitivity.py': [('    """\n',
                                                '    """\n'
                                                '    from . import '
                                                'conditions_v2 as c2, '
                                                'sensitivity_v2 as v2\n'
                                                '    if type(model) is '
                                                'c2.ConditionModel or '
                                                '(type(model) is dict and '
                                                'model.get("model_version") == '
                                                'c2.MODEL_VERSION):\n'
                                                '        return '
                                                'v2.analyze(workspace, '
                                                'packet_id, model)\n'),
                                               ('def render(report):\n',
                                                'def render(report):\n'
                                                '    from . import '
                                                'sensitivity_v2 as v2\n'
                                                '    if type(report) is '
                                                'v2.SensitivityReport:\n'
                                                '        return '
                                                'v2.render(report)\n')],
 'src/proposed_spell_packets/alternatives.py': [('    """Freshly admit actual '
                                                 'packet/root/history once, '
                                                 'then compare owned '
                                                 'scopes."""\n',
                                                 '    """Freshly admit actual '
                                                 'packet/root/history once, '
                                                 'then compare owned '
                                                 'scopes."""\n'
                                                 '    from . import '
                                                 'alternatives_v2 as v2\n'
                                                 '    if type(definition) is '
                                                 'v2.AlternativesDefinition or '
                                                 '(type(definition) is dict '
                                                 'and '
                                                 'definition.get("definition_version") '
                                                 '== v2.DEFINITION_VERSION):\n'
                                                 '        return '
                                                 'v2.evaluate(workspace, '
                                                 'packet_id, definition)\n'),
                                                ('def render(report):\n',
                                                 'def render(report):\n'
                                                 '    from . import '
                                                 'alternatives_v2 as v2\n'
                                                 '    if type(report) is '
                                                 'v2.AlternativesReport:\n'
                                                 '        return '
                                                 'v2.render(report)\n')]}
COMPOUND_DISPATCH_SHA256 = {'src/proposed_spell_packets/__main__.py': {'baseline_sha256': 'a62209a6040efae78c11d2a665dcb35c0d55ed2ff2ab0764dabb346171d3a669',
                                            'successor_sha256': '877ebb244d707e82dc7ff373bf906f668b9595bcac43d73895b8ef75a53d6c7b'},
 'src/proposed_spell_packets/conditions.py': {'baseline_sha256': '4004e59906649c5195e8c52d2bf410b555cc2b2f6fcc3947e6335a0145c6fe72',
                                              'successor_sha256': '536503eb443e556279def66cd8ce4ac4137ec2424617ec4770bdfe813dacd486'},
 'src/proposed_spell_packets/sensitivity.py': {'baseline_sha256': '34d5b2b15ecad959fe4e81639e6529b980aa15ff2da07b1c8014605e5ab1f37b',
                                               'successor_sha256': 'c125786ecef1426593ba656f24cc23970d4690f167f028bb27ac73477d76cf64'},
 'src/proposed_spell_packets/alternatives.py': {'baseline_sha256': '4170aa3d5c3a823d81f59ee4ac7ea6830ac98ecd0189aa331f62ad29650c7ef5',
                                                'successor_sha256': '34a615b4a8e28edd4f1c6614a6d4e583b62ac8c32fe33c230945ba5969c2826a'}}


def historical_compound_dispatch_bytes(name, raw):
    """Restore exact pre-compound API bytes without copying v1 implementations."""
    if (type(name) is not str or name not in COMPOUND_DISPATCH_PATCHES
            or type(raw) is not bytes):
        raise AssertionError("Only named compound dispatch bytes are adapted")
    pins = COMPOUND_DISPATCH_SHA256[name]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == pins["baseline_sha256"]:
        return raw
    if digest != pins["successor_sha256"]:
        raise AssertionError("Exact compound dispatch successor changed")
    for before, after in reversed(COMPOUND_DISPATCH_PATCHES[name]):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact compound dispatch adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != pins["baseline_sha256"]:
        raise AssertionError("Historical v1 API bytes changed")
    return raw

def historical_sensitivity_cli_bytes(raw):
    """Reconstruct only the exact PR #213 CLI from the named successor."""
    if type(raw) is not bytes:
        raise AssertionError("Exact alternatives CLI bytes required")
    if hashlib.sha256(raw).hexdigest() == SENSITIVITY_CLI_SHA256:
        return raw
    if hashlib.sha256(raw).hexdigest() != ALTERNATIVES_CLI_SHA256:
        raw = historical_compound_dispatch_bytes("src/proposed_spell_packets/__main__.py", raw)
    if hashlib.sha256(raw).hexdigest() != ALTERNATIVES_CLI_SHA256:
        raise AssertionError("Exact alternatives CLI successor changed")
    for before, after in reversed(ALTERNATIVES_CLI_PATCHES):
        old, new = before.encode(), after.encode()
        if raw.count(new) != 1:
            raise AssertionError("Exact alternatives CLI adaptation changed")
        raw = raw.replace(new, old, 1)
    if hashlib.sha256(raw).hexdigest() != SENSITIVITY_CLI_SHA256:
        raise AssertionError("Historical sensitivity CLI changed")
    return raw


def historical_document_before_alternatives_append(path, raw):
    """Strip only the exact alternatives appendix, retaining all prior bytes."""
    if (type(path) is not str or path not in ALTERNATIVES_DOCUMENT_APPENDICES
            or type(raw) is not bytes):
        raise AssertionError("Only named alternatives document bytes are adapted")
    pin = ALTERNATIVES_DOCUMENT_APPENDICES[path]
    size = pin["baseline_bytes"]
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_compound_append(path, raw)
    if len(raw) not in (size, size + pin["appendix_bytes"]):
        raise AssertionError("Only the exact alternatives appendix is permitted")
    baseline, suffix = raw[:size], raw[size:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Pre-alternatives historical document changed")
    if suffix and hashlib.sha256(suffix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact alternatives appendix changed")
    return baseline


def historical_conditional_cli_bytes(raw):
    """Reconstruct only the exact PR #212 CLI from this narrow successor."""
    if type(raw) is not bytes:
        raise AssertionError("Exact sensitivity CLI bytes required")
    if hashlib.sha256(raw).hexdigest() == CONDITIONAL_CLI_SHA256:
        return raw
    if hashlib.sha256(raw).hexdigest() != SENSITIVITY_CLI_SHA256:
        raw = historical_sensitivity_cli_bytes(raw)
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
    if len(raw) > size + pin["appendix_bytes"]:
        raw = historical_document_before_alternatives_append(path, raw)
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
