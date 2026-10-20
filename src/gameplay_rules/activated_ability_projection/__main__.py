"""Bounded projection source reproduction and offline integrity review."""
import argparse
from pathlib import Path

from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from .package import build_package, load_package, manifest, verify_source, write_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "build", "validate"))
    parser.add_argument("--review-root", type=Path, default=Path("reference-reviews"))
    parser.add_argument("--package", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.command in ("inspect", "build") and args.source is None:
        parser.error("fresh source reproduction requires --source")
    if args.command in ("build", "validate") and args.package is None:
        parser.error("construction or validation requires --package")
    try:
        if args.command == "validate":
            records = load_package(args.package, review_root=args.review_root)
            result = {"status": "VALID_OFFLINE_METADATA_NOT_FRESH_SOURCE_VERIFICATION",
                "package_id": manifest(records)["package_id"]}
            if args.source is not None:
                result["fresh_source_verification"] = verify_source(records, args.source, review_root=args.review_root)
        else:
            records = build_package(args.source, review_root=args.review_root)
            result = verify_source(records, args.source, review_root=args.review_root)
            result["package_id"] = manifest(records)["package_id"]
            if args.command == "build":
                write_package(args.package, records, review_root=args.review_root)
        print(deterministic_json(result))
    except (GameplayContractError, OSError, ValueError):
        parser.exit(1, "bounded activated procedure projection validation failed\n")


if __name__ == "__main__":
    main()
