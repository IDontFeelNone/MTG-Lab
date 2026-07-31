#!/usr/bin/env python3
"""Local Phase 107 MTGJSON dataset-delivery command."""
import argparse
import json
from pathlib import Path

from promotion import MTGJSONDatasetDelivery


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--target", action="append", default=[],
                        help="set name or discovered set code (repeatable; dry-run only)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "plan", "list", "verify-batch", "review-package", "promote"):
        command = commands.add_parser(name)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--sha256", required=True)
        if name in ("plan", "list", "verify-batch", "review-package"):
            command.add_argument("--batch")
        if name == "promote":
            command.add_argument("--batch", required=True)
            command.add_argument("--reviewer", required=True)
            command.add_argument("--review-reference", required=True)
    commands.add_parser("verify-downstream")
    rollback = commands.add_parser("rollback")
    rollback.add_argument("--promotion-id", required=True)
    rollback.add_argument("--actor", required=True)
    rollback.add_argument("--timestamp", required=True)
    args = parser.parse_args(argv)
    delivery = MTGJSONDatasetDelivery(args.data_root, batch_size=args.batch_size)
    try:
        if args.command == "verify": result = delivery.verify(args.source, args.sha256)
        elif args.command in ("plan", "list"):
            result = delivery.plan(args.source, args.sha256, args.batch,
                                   targets=tuple(args.target))
            if args.command == "list": result = result["manifest"]["batches"]
        elif args.command == "verify-batch":
            if not args.batch: raise ValueError("--batch is required")
            result = delivery.verify_batch(args.source, args.sha256, args.batch,
                                           targets=tuple(args.target))
        elif args.command == "review-package":
            if not args.batch: raise ValueError("--batch is required")
            result = delivery.review_package(args.source, args.sha256, args.batch,
                                              targets=tuple(args.target))
        elif args.command == "promote":
            result = delivery.promote(args.source, args.sha256, args.batch,
                                      reviewer=args.reviewer, review_reference=args.review_reference)
        elif args.command == "verify-downstream": result = delivery.ingestion.verify_downstream()
        else: result = delivery.rollback(args.promotion_id, actor=args.actor, timestamp=args.timestamp)
    except (OSError, ValueError, KeyError, IndexError) as error:
        print(json.dumps({"valid": False, "error": str(error), "canonical_write": False}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
