"""Unified MTG Lab command line interface."""
import argparse
import json
from pathlib import Path

from dataset_import import DatasetRegistry, ImportManager
from external_ingestion import (AdapterRegistry, ExternalDatasetIngestor, MTGJSONAdapter,
                                detect_mtgjson, generate_manifest)
from query import CanonicalQueryEngine


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
    ingest = commands.add_parser("ingest")
    ingest.add_argument("ingest_targets", nargs="*"); ingest.add_argument("--manifest", type=Path)
    ingest.add_argument("--timestamp")
    adapter = commands.add_parser("adapter")
    adapter_commands = adapter.add_subparsers(dest="adapter_command", required=True)
    for name in ("detect", "inspect", "normalize"):
        command = adapter_commands.add_parser(name); command.add_argument("source", type=Path)
        if name == "normalize": command.add_argument("--timestamp", required=True)
    query = commands.add_parser("query")
    query_commands = query.add_subparsers(dest="query_command", required=True)
    entity = query_commands.add_parser("entity")
    entity.add_argument("identifier", nargs="?")
    entity.add_argument("--game", default="magic"); entity.add_argument("--type")
    entity.add_argument("--provider-id"); entity.add_argument("--external-id")
    entity.add_argument("--name"); entity.add_argument("--normalized-name")
    entity.add_argument("--printing-id"); entity.add_argument("--set-id")
    search = query_commands.add_parser("search"); search.add_argument("text")
    search.add_argument("--game", default="magic"); search.add_argument("--mode", choices=("exact", "normalized", "prefix"), default="exact")
    search.add_argument("--case-insensitive", action="store_true")
    for name in ("dataset", "provenance"):
        command = query_commands.add_parser(name); command.add_argument("identifier"); command.add_argument("--game", default="magic")
    validation = query_commands.add_parser("validation"); validation.add_argument("state", choices=("unknown", "conflicting", "unresolved", "rejected", "validation_failure", "superseded")); validation.add_argument("--game", default="magic")
    args = parser.parse_args(argv); registry = DatasetRegistry(args.data_root / "datasets")
    manager = ImportManager(args.data_root, registry)
    if args.command == "query":
        engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games",
                                      data_root=args.data_root)
        if args.query_command == "entity":
            result = engine.entities(canonical_id=args.identifier, provider_id=args.provider_id,
                external_id=args.external_id, entity_type=args.type, card_name=args.name,
                normalized_name=args.normalized_name, printing_id=args.printing_id, set_id=args.set_id)
            result = [item.as_dict() for item in result]
        elif args.query_command == "search":
            result = [item.as_dict() for item in engine.search(args.text, mode=args.mode,
                                                               case_insensitive=args.case_insensitive)]
        elif args.query_command == "dataset": result = engine.dataset(args.identifier)
        elif args.query_command == "provenance": result = engine.provenance(args.identifier)
        else:
            result = [item.as_dict() if hasattr(item, "as_dict") else item
                      for item in engine.validation(args.state)]
    elif args.command == "adapter":
        if args.adapter_command == "detect": result = detect_mtgjson(args.source)
        else:
            manifest = generate_manifest(args.source)
            if args.adapter_command == "inspect":
                result = {"detected": detect_mtgjson(args.source), "manifest": manifest.as_dict()}
            else:
                manifest_path = args.data_root / "adapter" / "mtgjson" / "manifest.json"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(json.dumps(manifest.as_dict(), sort_keys=True) + "\n")
                registry = AdapterRegistry(include_defaults=False); registry.register(MTGJSONAdapter())
                result = ExternalDatasetIngestor(args.data_root, registry).ingest(
                    args.source, manifest_path, timestamp=args.timestamp)
    elif args.command == "ingest":
        external = ExternalDatasetIngestor(args.data_root)
        operation = args.ingest_targets[0] if args.ingest_targets else None
        if operation == "list": result = external.list()
        elif operation in {"validate", "inspect"}:
            if len(args.ingest_targets) != 2: parser.error(f"ingest {operation} requires source")
            function = external.validate if operation == "validate" else external.inspect
            result = function(Path(args.ingest_targets[1]), args.manifest)
        else:
            if len(args.ingest_targets) != 1 or not args.timestamp: parser.error("ingest requires source and --timestamp")
            result = external.ingest(Path(args.ingest_targets[0]), args.manifest, timestamp=args.timestamp)
    elif args.command == "dataset":
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
