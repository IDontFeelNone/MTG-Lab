"""Exact finite pack-v0 successors; historical records/gates are unchanged."""
import hashlib
REPLACEMENTS = {'src/query/engine.py': {'old_sha256': '85e9b8a02a23c674ff7e2325d4704ef93537337eec56d6b1bc8e8d9c31d22a3c', 'new_sha256': '40c81e32dddd86724c8362694d37cc1f54fdca60a35b77e4d1eb1e4f05910052', 'insertion': b'    def retained_record(self, identifier: str, *, entity_type: str) -> dict[str, Any]:\n        """Independent source view for strict downstream schema validation.\n\n        Typed compatibility defaults are not evidence of explicit source fields.\n        Ambiguous namespaces and state-only entities have no such record route.\n        This accessor grants no new attachment capability or source authority.\n        """\n        matches = self.entities(canonical_id=identifier)\n        if (len(matches) != 1 or matches[0].entity_type != entity_type\n                or identifier not in self._raw):\n            raise QueryError("unique retained record is unavailable")\n        return deepcopy(self._raw[identifier])\n\n', 'original': b''}, 'src/mtglab/__main__.py': {'old_sha256': '43ea45057d868dbb0b53235fd37dc0ac2ee04b073089d304df2893e571b85fff', 'new_sha256': 'cef1decaca7229a1bc51a8fb814ee905a30ee402f9d80e346b3932572ee97b95', 'insertion': b'    pack = commands.add_parser("pack")\n    pack_commands = pack.add_subparsers(dest="pack_command", required=True)\n    single = pack_commands.add_parser("simulate")\n    single.add_argument("--game", default="magic"); single.add_argument("--product-id", required=True)\n    single.add_argument("--definition-id"); single.add_argument("--seed", type=int, required=True)\n    single.add_argument("--recorded-at"); single.add_argument("--format", choices=("json", "text"), default="json")\n    args = parser.parse_args(argv)\n    if args.command == "pack":\n        from simulation import load_pack_simulator, PackSimulationError, render_pack_report\n        try:\n            result = load_pack_simulator(args.game, data_root=args.data_root).generate(\n                args.product_id, pack_definition_id=args.definition_id, seed=args.seed,\n                recorded_at=args.recorded_at)\n        except PackSimulationError as error:\n            print(render_pack_report(error.as_dict(), readable=args.format == "text"), end="")\n            return 2\n        print(render_pack_report(result, readable=args.format == "text"), end="")\n        return 0\n    registry = DatasetRegistry(args.data_root / "datasets")\n', 'original': b'    args = parser.parse_args(argv); registry = DatasetRegistry(args.data_root / "datasets")\n'}, 'tests/proposed_spell_packet_analysis_preservation.py': {'old_sha256': '3a810a2803682541f7cfda94c24dea5301ba741d04236d74d786718b77c6c630', 'new_sha256': 'aaf8d0b49768a3d92eb49c64f4dcc96324f72591deceb1ad48fc38c2391c88c9', 'insertion': b'    from pack_simulation_preservation import is_addition\n    if is_addition(path, root): return True\n', 'original': b''}}
ADDITIONS = {'src/simulation/__init__.py': {'bytes': 333, 'sha256': '44e477994585bec51e2e7a7a17b7eda8dc757257144607384bd626e2e9997634'}, 'src/simulation/pack.py': {'bytes': 12435, 'sha256': '54a1f94e22c080691e46d772807a96f600a7fb3f309007f0187c5798b733b59d'}}


def preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name not in REPLACEMENTS: return raw
    pin = REPLACEMENTS[name]; digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256']: return raw
    if digest != pin['new_sha256']: raise AssertionError('unreviewed pack-v0 successor: exact authorized pin required')
    if raw.count(pin['insertion']) != 1: raise AssertionError('exact pack-v0 insertion required')
    old = raw.replace(pin['insertion'], pin['original'], 1)
    if hashlib.sha256(old).hexdigest() != pin['old_sha256']: raise AssertionError('exact historical predecessor required')
    return old


def is_addition(path, root):
    name = path.relative_to(root).as_posix()
    if name not in ADDITIONS: return False
    pin = ADDITIONS[name]
    if path.is_symlink() or path.stat().st_mode & 0o111: raise AssertionError('unsupported pack-v0 source mode')
    raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise AssertionError('exact pack-v0 addition pin required')
    return True
