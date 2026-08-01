"""Unified MTG Lab command line interface."""
import argparse
import json
from pathlib import Path

from dataset_import import DatasetRegistry, ImportManager
from external_ingestion import (AdapterRegistry, ExternalDatasetIngestor, MTGJSONAdapter,
                                detect_mtgjson, generate_manifest)
from query import CanonicalQueryEngine, CanonicalQueryService, QueryError
from analytics import CanonicalAnalyticsEngine
from semantic import CanonicalSemanticQueryEngine, SemanticRequest
from reasoning import ReasoningContextBuilder, ReasoningContextError, ReasoningContextRequest
from ai import AIProviderRegistry, SCHEMA_VERSION as AI_SCHEMA_VERSION
from ai.errors import AIAdapterError
from evidence import ReferenceDatasetRegistry
from providers import MTGJSONProvider, provider_registry
from providers.mtgjson import MTGJSONImportExecution
from projection import ProjectionError, TypedCanonicalProjectionEngine
from promotion import BoundedCorpusPromotion
from acquisition import PromotionError
from official_datasets import AcquisitionError, OfficialDatasetAcquisition
from production_evidence import (EvidenceError, ProductionEvidenceRepository,
                                 WorkflowArtifactAdapter)
from collection import (CanonicalCollectionResolver, CollectionIntelligenceError,
    acquisition_priorities, collection_summary, compare_deck, create_snapshot,
    collection_value, read_import, verify_snapshot)
from market import MarketObservationRepository, MarketQueryService


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mtg-lab")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    commands = parser.add_subparsers(dest="command", required=True)
    collection = commands.add_parser("collection")
    collection_commands = collection.add_subparsers(dest="collection_command", required=True)
    collection_import = collection_commands.add_parser("import")
    collection_import.add_argument("--input", type=Path, required=True)
    collection_import.add_argument("--snapshot-id"); collection_import.add_argument("--game", default="magic")
    for name in ("verify", "summary", "value", "duplicates", "owned", "missing", "unique", "unresolved", "acquisitions"):
        command = collection_commands.add_parser(name); command.add_argument("--snapshot", required=True)
        command.add_argument("--game", default="magic")
    deck = commands.add_parser("deck")
    deck_commands = deck.add_subparsers(dest="deck_command", required=True)
    for name in ("compare", "missing", "acquisition-priorities"):
        command = deck_commands.add_parser(name); command.add_argument("--snapshot", required=True)
        command.add_argument("--deck", type=Path, action="append", required=True); command.add_argument("--game", default="magic")
    market = commands.add_parser("market")
    market_commands = market.add_subparsers(dest="market_command", required=True)
    for name in ("card", "printing", "product"):
        command = market_commands.add_parser(name); command.add_argument("identifier")
        command.add_argument("--provider"); command.add_argument("--game", default="magic")
    history = market_commands.add_parser("history"); history.add_argument("identifier")
    history.add_argument("--entity-type", choices=("card", "printing", "product"), default="printing")
    history.add_argument("--provider"); history.add_argument("--game", default="magic")
    comparison = market_commands.add_parser("providers"); comparison.add_argument("identifier")
    comparison.add_argument("--entity-type", choices=("card", "printing", "product"), default="printing")
    comparison.add_argument("--game", default="magic")
    dataset = commands.add_parser("dataset"); dataset_commands = dataset.add_subparsers(dest="dataset_command", required=True)
    register = dataset_commands.add_parser("register"); register.add_argument("manifest", type=Path)
    listing = dataset_commands.add_parser("list"); listing.add_argument("--format", choices=("json",), default="json")
    for name in ("download", "verify", "status"):
        command = dataset_commands.add_parser(name); command.add_argument("dataset_name")
        command.add_argument("--format", choices=("json",), default="json")
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
    card_query = query_commands.add_parser("card"); card_query.add_argument("name", nargs="?")
    card_query.add_argument("--game", default="magic"); card_query.add_argument("--type")
    card_query.add_argument("--color"); card_query.add_argument("--rarity"); card_query.add_argument("--set", dest="set_name")
    card_query.add_argument("--mana-value"); card_query.add_argument("--keyword"); card_query.add_argument("--legality")
    card_query.add_argument("--identifier"); card_query.add_argument("--printings", action="store_true")
    product_query = query_commands.add_parser("product"); product_query.add_argument("identifier"); product_query.add_argument("--game", default="magic")
    printing_query = query_commands.add_parser("printing"); printing_query.add_argument("identifier"); printing_query.add_argument("--game", default="magic")
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
    analytics = commands.add_parser("analytics")
    analytics_commands = analytics.add_subparsers(dest="analytics_command", required=True)
    for name in ("summary", "entity", "dataset", "validation", "provenance"):
        command = analytics_commands.add_parser(name)
        command.add_argument("--game", default="magic")
        command.add_argument("--format", choices=("json",), default="json")
    semantic = commands.add_parser("semantic")
    semantic_commands = semantic.add_subparsers(dest="semantic_command", required=True)
    find = semantic_commands.add_parser("find"); find.add_argument("--identifier"); find.add_argument("--name")
    find.add_argument("--type"); find.add_argument("--game", default="magic"); find.add_argument("--format", choices=("json",), default="json")
    listing = semantic_commands.add_parser("list")
    selectors = listing.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--type"); selectors.add_argument("--dataset"); selectors.add_argument("--provenance")
    selectors.add_argument("--validation"); selectors.add_argument("--confidence", nargs=2, type=float, metavar=("MIN", "MAX"))
    listing.add_argument("--game", default="magic"); listing.add_argument("--format", choices=("json",), default="json")
    semantic_analytics = semantic_commands.add_parser("analytics")
    semantic_analytics.add_argument("analytics_type", nargs="?", choices=("summary", "dataset", "provenance", "validation"), default="summary")
    semantic_analytics.add_argument("--game", default="magic"); semantic_analytics.add_argument("--format", choices=("json",), default="json")
    for name in ("dataset", "provenance"):
        command = semantic_commands.add_parser(name); command.add_argument("identifier", nargs="?")
        command.add_argument("--statistics", action="store_true"); command.add_argument("--game", default="magic")
        command.add_argument("--format", choices=("json",), default="json")
    reasoning = commands.add_parser("reasoning")
    reasoning_commands = reasoning.add_subparsers(dest="reasoning_command", required=True)
    for name in ("context", "entity", "dataset", "analytics", "provenance"):
        command = reasoning_commands.add_parser(name)
        command.add_argument("identifier", nargs="?")
        command.add_argument("--game", default="magic"); command.add_argument("--type", default="card")
        command.add_argument("--max-entities", type=int, default=100)
        command.add_argument("--max-relationships", type=int, default=100)
        command.add_argument("--max-evidence", type=int, default=100)
        command.add_argument("--format", choices=("json",), default="json")
    ai = commands.add_parser("ai")
    ai_commands = ai.add_subparsers(dest="ai_command", required=True)
    for name in ("providers", "capabilities"):
        command = ai_commands.add_parser(name)
        command.add_argument("--format", choices=("json",), default="json")
    ai_validate = ai_commands.add_parser("validate")
    ai_validate.add_argument("--provider")
    ai_validate.add_argument("--version")
    ai_validate.add_argument("--capability")
    ai_validate.add_argument("--format", choices=("json",), default="json")
    evidence = commands.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    for name in ("providers", "datasets", "artifacts", "validate", "runs"):
        command = evidence_commands.add_parser(name)
        command.add_argument("--format", choices=("json",), default="json")
    for name in ("inspect", "batches", "verify"):
        command = evidence_commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--format", choices=("json",), default="json")
    evidence_intake = evidence_commands.add_parser("intake")
    evidence_intake.add_argument("archive", type=Path)
    evidence_intake.add_argument("--sha256", required=True)
    evidence_intake.add_argument("--run-id", required=True)
    evidence_intake.add_argument("--format", choices=("json",), default="json")
    evidence_normalize = evidence_commands.add_parser("normalize-workflow-artifact")
    evidence_normalize.add_argument("archive", type=Path)
    evidence_normalize.add_argument("--run-id", required=True)
    evidence_normalize.add_argument("--artifact-name", required=True)
    evidence_normalize.add_argument("--output", type=Path, required=True)
    evidence_normalize.add_argument("--sha256")
    evidence_normalize.add_argument("--repository", default="unknown/unknown")
    evidence_normalize.add_argument("--commit-sha", default="0" * 40)
    evidence_normalize.add_argument("--format", choices=("json",), default="json")
    provider = commands.add_parser("provider")
    provider_names = provider.add_subparsers(dest="provider_name", required=True)
    mtgjson = provider_names.add_parser("mtgjson")
    mtgjson_commands = mtgjson.add_subparsers(dest="provider_command", required=True)
    for name in ("validate", "inspect", "plan", "import"):
        command = mtgjson_commands.add_parser(name)
        command.add_argument("source", type=Path, nargs="?" if name == "import" else None)
        command.add_argument("--format", choices=("json",), default="json")
        if name == "validate":
            command.add_argument("--sha256")
    for name in ("candidates", "review"):
        command = mtgjson_commands.add_parser(name)
        command.add_argument("--dataset")
        command.add_argument("--format", choices=("json",), default="json")
    projection = commands.add_parser("projection")
    projection_commands = projection.add_subparsers(dest="projection_command", required=True)
    for name in ("validate", "project", "inspect"):
        command = projection_commands.add_parser(name)
        command.add_argument("projection_id", nargs="?" if name == "inspect" else None)
        command.add_argument("--game", default="magic")
        command.add_argument("--format", choices=("json",), default="json")
        if name == "project": command.add_argument("--timestamp", required=True)
    promote = commands.add_parser("promote")
    promote_commands = promote.add_subparsers(dest="promote_command", required=True)
    for name in ("corpus", "inspect", "verify"):
        command = promote_commands.add_parser(name)
        command.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv); registry = DatasetRegistry(args.data_root / "datasets")
    manager = ImportManager(args.data_root, registry)
    if args.command in {"collection", "deck"}:
        try:
            resolver = CanonicalCollectionResolver(args.game, args.data_root)
            snapshots = args.data_root / "collections" / "snapshots"
            if args.command == "collection" and args.collection_command == "import":
                imported = read_import(args.input); resolution = resolver.resolve(imported)
                result = create_snapshot(imported, resolution, snapshots, args.snapshot_id)
            else:
                snapshot_path = snapshots / f"{args.snapshot}.json"
                if args.command == "collection" and args.collection_command == "verify":
                    result = verify_snapshot(snapshot_path)
                else:
                    snapshot = json.loads(snapshot_path.read_text())
                    summary = collection_summary(snapshot, resolver)
                    if args.command == "collection":
                        if args.collection_command == "summary": result = summary
                        elif args.collection_command == "value": result = collection_value(
                            snapshot, resolver, MarketObservationRepository(args.data_root / "market" / "observations"))
                        elif args.collection_command == "duplicates": result = {
                            "schema_version":"collection-duplicates-v1", "snapshot_id":args.snapshot,
                            "duplicates":summary["duplicates"], "duplicate_count":summary["duplicate_count"]}
                        else:
                            query_engine = CanonicalQueryEngine(args.game,
                                games_root=args.data_root / "canonical" / "games", data_root=args.data_root)
                            result = CanonicalQueryService(query_engine).collection(
                                snapshot, args.collection_command).as_dict()
                    else:
                        decks = [json.loads(path.read_text()) for path in args.deck]
                        comparisons = [compare_deck(snapshot, item, resolver) for item in decks]
                        if args.deck_command == "compare": result = comparisons[0] if len(comparisons)==1 else comparisons
                        elif args.deck_command == "missing":
                            result = {"schema_version":"deck-missing-v1", "deck_id":comparisons[0]["deck_id"],
                                      "requirements":[x for x in comparisons[0]["requirements"] if x["missing_quantity"]]}
                        else: result = acquisition_priorities(comparisons)
        except (CollectionIntelligenceError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            print(json.dumps({"valid":False,"error":str(error)}, indent=2, sort_keys=True)); return 2
    elif args.command == "market":
        engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games", data_root=args.data_root)
        service = MarketQueryService(CanonicalQueryService(engine),
            MarketObservationRepository(args.data_root / "market" / "observations"))
        try:
            if args.market_command in {"card", "printing", "product"}:
                result = getattr(service, args.market_command)(args.identifier, provider=args.provider)
            elif args.market_command == "history":
                result = service.history(args.entity_type, args.identifier, provider=args.provider)
            else: result = service.provider_comparison(args.entity_type, args.identifier)
        except (QueryError, ValueError, OSError) as error:
            print(json.dumps({"valid": False, "error": str(error)}, indent=2, sort_keys=True)); return 2
    elif args.command == "promote":
        corpus = Path(__file__).parents[2] / "data/reference/mtgjson/bounded-canonical-promotion-v1.json"
        workflow = BoundedCorpusPromotion(args.data_root, corpus)
        try: result = workflow.promote() if args.promote_command == "corpus" else getattr(
            workflow, args.promote_command)()
        except (OSError, ValueError, PromotionError, ProjectionError) as error:
            print(json.dumps({"valid": False, "error": str(error)}, indent=2, sort_keys=True)); return 2
    elif args.command == "projection":
        engine = TypedCanonicalProjectionEngine(args.data_root / "canonical",
            args.data_root / "canonical" / "games", args.data_root / "projection-audit", game=args.game)
        try:
            if args.projection_command == "validate": result = engine.validate()
            elif args.projection_command == "project": result = engine.project(args.timestamp)
            else: result = engine.inspect(args.projection_id)
        except ProjectionError as error:
            print(json.dumps({"valid": False, "error": str(error)}, indent=2, sort_keys=True)); return 2
    elif args.command == "provider":
        mtgjson_provider = MTGJSONProvider()
        if args.provider_command == "validate":
            result = mtgjson_provider.validate_local(args.source, args.sha256)
        elif args.provider_command == "inspect":
            result = mtgjson_provider.inspect(args.source)
        elif args.provider_command == "plan":
            result = mtgjson_provider.plan_local(args.source)
        else:
            execution = MTGJSONImportExecution(args.data_root)
            try:
                if args.provider_command == "import": result = execution.import_dataset(args.source)
                elif args.provider_command == "candidates": result = execution.candidates(args.dataset)
                else: result = execution.review(args.dataset)
            except (OSError, ValueError) as error:
                print(json.dumps({"valid": False, "error": str(error), "canonical_write": False},
                                 indent=2, sort_keys=True)); return 2
    elif args.command == "evidence":
        evidence_registry = ReferenceDatasetRegistry(args.data_root / "evidence" / "registry")
        production_repository = ProductionEvidenceRepository(args.data_root)
        try:
            if args.evidence_command == "runs": result = production_repository.runs()
            elif args.evidence_command == "inspect": result = production_repository.inspect(args.run_id)
            elif args.evidence_command == "batches": result = production_repository.batches(args.run_id)
            elif args.evidence_command == "verify": result = production_repository.verify(args.run_id)
            elif args.evidence_command == "intake": result = production_repository.intake(
                args.archive, args.sha256, args.run_id)
            elif args.evidence_command == "normalize-workflow-artifact":
                result = WorkflowArtifactAdapter().normalize(args.archive, run_id=args.run_id,
                    artifact_name=args.artifact_name, output=args.output,
                    archive_sha256=args.sha256, repository=args.repository,
                    commit_sha=args.commit_sha)
            elif args.evidence_command == "providers":
                providers = provider_registry()
                result = {"schema_version": "1.0.0", "providers": [
                    provider.metadata().to_dict() for provider in providers.providers()]}
            elif args.evidence_command == "datasets":
                result = {"schema_version": "1.0.0", "datasets": evidence_registry.datasets()}
            elif args.evidence_command == "artifacts":
                result = {"schema_version": "1.0.0", "artifacts": evidence_registry.artifacts()}
            else:
                result = evidence_registry.validate()
        except (OSError, EvidenceError) as error:
            print(json.dumps({"valid": False, "error": str(error)}, indent=2, sort_keys=True)); return 2
    elif args.command == "ai":
        providers = AIProviderRegistry()
        try:
            if args.ai_command == "providers":
                result = {"schema_version": AI_SCHEMA_VERSION, "providers": [], "versions": providers.versions()}
            elif args.ai_command == "capabilities":
                result = {"schema_version": AI_SCHEMA_VERSION, "providers": []}
            elif args.provider:
                provider = providers.lookup(args.provider, args.version)
                if args.capability and args.capability not in provider.capabilities().capabilities:
                    from ai.errors import UnsupportedCapability
                    raise UnsupportedCapability(f"unsupported capability: {args.capability}")
                result = {"schema_version": AI_SCHEMA_VERSION, "valid": True,
                          "provider": provider.metadata().to_dict()}
            else:
                result = {"schema_version": AI_SCHEMA_VERSION, "valid": True,
                          "registered_provider_count": len(providers.providers()),
                          "message": "adapter contracts and registry are valid"}
        except AIAdapterError as error:
            print(json.dumps(error.to_dict(), indent=2, sort_keys=True)); return 2
    elif args.command == "reasoning":
        query_engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games", data_root=args.data_root)
        semantic_engine = CanonicalSemanticQueryEngine(query_engine)
        if args.reasoning_command == "entity":
            if not args.identifier: parser.error("reasoning entity requires identifier")
            semantic_request = SemanticRequest("find_identifier", {"identifier": args.identifier})
        elif args.reasoning_command == "dataset":
            if not args.identifier: parser.error("reasoning dataset requires identifier")
            semantic_request = SemanticRequest("list_dataset", {"dataset": args.identifier})
        elif args.reasoning_command == "provenance":
            if not args.identifier: parser.error("reasoning provenance requires identifier")
            semantic_request = SemanticRequest("list_provenance", {"source_id": args.identifier})
        else:
            semantic_request = SemanticRequest("list_type", {"entity_type": args.type})
        request = ReasoningContextRequest(semantic_request, include_analytics=args.reasoning_command == "analytics",
            maximum_entities=args.max_entities, maximum_relationships=args.max_relationships,
            maximum_evidence_items=args.max_evidence)
        try: result = ReasoningContextBuilder(semantic_engine).build(request).to_dict()
        except ReasoningContextError as error:
            print(json.dumps(error.to_dict(), indent=2, sort_keys=True)); return 2
    elif args.command == "semantic":
        query_engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games",
                                            data_root=args.data_root)
        engine = CanonicalSemanticQueryEngine(query_engine)
        if args.semantic_command == "find":
            if bool(args.identifier) == bool(args.name): parser.error("semantic find requires exactly one of --identifier or --name")
            operation = "find_identifier" if args.identifier else "find_name"
            parameters = {"identifier": args.identifier, "entity_type": args.type} if args.identifier else {"name": args.name}
            parameters = {key: value for key, value in parameters.items() if value is not None}
        elif args.semantic_command == "list":
            if args.type: operation, parameters = "list_type", {"entity_type": args.type}
            elif args.dataset: operation, parameters = "list_dataset", {"dataset": args.dataset}
            elif args.provenance: operation, parameters = "list_provenance", {"source_id": args.provenance}
            elif args.validation: operation, parameters = "list_validation", {"state": args.validation}
            else: operation, parameters = "list_confidence", {"minimum": args.confidence[0], "maximum": args.confidence[1]}
        elif args.semantic_command == "analytics":
            operation = {"summary": "analytics_summary", "dataset": "dataset_statistics",
                         "provenance": "provenance_statistics", "validation": "validation_statistics"}[args.analytics_type]
            parameters = {}
        elif args.semantic_command == "dataset":
            if args.statistics: operation, parameters = "dataset_statistics", {}
            elif args.identifier: operation, parameters = "list_dataset", {"dataset": args.identifier}
            else: parser.error("semantic dataset requires identifier or --statistics")
        else:
            if args.statistics: operation, parameters = "provenance_statistics", {}
            elif args.identifier: operation, parameters = "list_provenance", {"source_id": args.identifier}
            else: parser.error("semantic provenance requires identifier or --statistics")
        result = engine.execute(SemanticRequest(operation, parameters)).to_dict()
    elif args.command == "analytics":
        query_engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games",
                                            data_root=args.data_root)
        result = getattr(CanonicalAnalyticsEngine(query_engine), args.analytics_command)().to_dict()
    elif args.command == "query":
        engine = CanonicalQueryEngine(args.game, games_root=args.data_root / "canonical" / "games",
                                      data_root=args.data_root)
        service = CanonicalQueryService(engine)
        try:
            if args.query_command == "card":
                if args.printings:
                    identity = args.identifier or args.name
                    if not identity: raise QueryError("card --printings requires a name or identifier")
                    result = service.printings_for_card(identity).as_dict()
                else:
                    result = service.cards(name=args.name, type=args.type, color=args.color,
                        rarity=args.rarity, set=args.set_name, mana_value=args.mana_value,
                        keyword=args.keyword, legality=args.legality, identifier=args.identifier).as_dict()
            elif args.query_command == "product": result = service.product(args.identifier).as_dict()
            elif args.query_command == "printing": result = service.printing(args.identifier).as_dict()
            elif args.query_command == "entity":
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
        except QueryError as error:
            print(json.dumps({"valid":False,"error":str(error)}, indent=2, sort_keys=True)); return 2
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
        if args.dataset_command == "register":
            result = registry.register(json.loads(args.manifest.read_text()))
        else:
            acquisition = OfficialDatasetAcquisition(args.data_root)
            try:
                result = acquisition.list() if args.dataset_command == "list" else getattr(
                    acquisition, args.dataset_command)(args.dataset_name)
            except (AcquisitionError, OSError, ValueError) as error:
                print(json.dumps({"valid": False, "error": str(error), "canonical_write": False},
                                 indent=2, sort_keys=True)); return 2
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
