"""Read-only projection integrity and optional exact-source verification CLI."""
import argparse
import json
import sys

from gameplay_rules.errors import GameplayContractError
from .package import load_projection_package
from .source import verify_projection_source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="explicit retained projection package directory")
    parser.add_argument("--artifact-review-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--discovery-root", required=True)
    parser.add_argument("--artifact", help="optional external verified TXT for source-span proof")
    args = parser.parse_args(argv)
    roots = {"artifact_review_root": args.artifact_review_root,
             "source_root": args.source_root, "discovery_root": args.discovery_root}
    try:
        projection = load_projection_package(args.package, **roots)
        if args.artifact is not None:
            result = verify_projection_source(projection, args.artifact, **roots)
        else:
            result = {"status": "VERIFIED_PROJECTION_PACKAGE_INTEGRITY",
                "projection_id": projection.identity, "selected_rule_count": 20,
                "source_spans_reverified": False, "real_rules_executable": False}
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (GameplayContractError, OSError, ValueError):
        print(json.dumps({"error": "FOUNDATIONAL_PROJECTION_VERIFICATION_BLOCKED",
                          "source_body_retained": False, "real_rules_executable": False}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
