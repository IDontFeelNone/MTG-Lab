"""Unified MTG Lab command line interface."""
import argparse
import json
from pathlib import Path

from dataset_import import DatasetRegistry, ImportManager


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mtg-lab")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    commands = parser.add_subparsers(dest="command", required=True)
    dataset = commands.add_parser("dataset"); dataset_commands = dataset.add_subparsers(dest="dataset_command", required=True)
    register = dataset_commands.add_parser("register"); register.add_argument("manifest", type=Path)
    dataset_commands.add_parser("list")
    run = commands.add_parser("import"); run.add_argument("targets", nargs="*")
    run.add_argument("--version"); run.add_argument("--source", type=Path); run.add_argument("--actor")
    run.add_argument("--timestamp"); run.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv); registry = DatasetRegistry(args.data_root / "datasets")
    manager = ImportManager(args.data_root, registry)
    if args.command == "dataset":
        result = registry.register(json.loads(args.manifest.read_text())) if args.dataset_command == "register" else registry.list()
    elif args.targets and args.targets[0] == "status": result = manager.status(args.targets[1])
    elif args.targets and args.targets[0] == "report": result = manager.report(args.targets[1])
    else:
        args.dataset = args.targets[0] if args.targets else None
        missing = [name for name in ("dataset", "version", "source", "actor", "timestamp") if not getattr(args, name)]
        if missing: parser.error("import requires " + ", ".join(missing))
        result = manager.run(args.dataset, args.version, args.source, actor=args.actor,
                             timestamp=args.timestamp, allow_partial=not args.require_complete)
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
