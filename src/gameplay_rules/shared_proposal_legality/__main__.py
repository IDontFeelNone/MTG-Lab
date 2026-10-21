"""Offline validation and explicitly selected e-only source reproduction."""
import argparse
import json
import os
from pathlib import Path

from gameplay_rules.errors import GameplayContractError
from . import package
from .source import SOURCE_ENV


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "verify-source"))
    parser.add_argument("--review-root", type=Path, default=Path("reference-reviews"))
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    target = args.package or args.review_root / package.PACKAGE_NAME
    try:
        records = package.load_package(target, review_root=args.review_root)
        result = {"status": "VALID_OFFLINE_METADATA_NOT_FRESH_SOURCE_REPRODUCTION",
            "package_id": package.manifest(records, review_root=args.review_root)["package_id"]}
        if args.command == "verify-source":
            source = os.environ.get(SOURCE_ENV)
            result["source_reproduction"] = ("SKIPPED_SOURCE_SELECTOR_UNCONFIGURED" if source is None else
                package.verify_source(records, source, review_root=args.review_root))
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except (GameplayContractError, OSError, TypeError, ValueError):
        parser.exit(1, "bounded shared proposal-legality validation failed\n")


if __name__ == "__main__":
    main()
