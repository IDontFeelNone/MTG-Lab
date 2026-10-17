"""Read-only, source-free integrity verification of inactive design metadata."""
import argparse
import json
import sys

from gameplay_rules.errors import GameplayContractError
from .package import load_design_package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package")
    parser.add_argument("--projection-root", required=True)
    parser.add_argument("--artifact-review-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--discovery-root", required=True)
    args = parser.parse_args(argv)
    try:
        records = load_design_package(args.package, projection_root=args.projection_root,
            artifact_review_root=args.artifact_review_root, source_root=args.source_root,
            discovery_root=args.discovery_root)
        print(json.dumps({"status": "VERIFIED_DESIGN_PACKAGE_INTEGRITY",
            "projection_review_id": records["projection-review.json"].identity,
            "execution_profile_design_id": records["execution-profile-design.json"].identity,
            "rules_reviewed": 20, "source_txt_required": False,
            "overall_execution_readiness": "BLOCKED", "real_rules_executable": False,
            "activation_denied": True}, sort_keys=True, separators=(",", ":")))
        return 0
    except (GameplayContractError, OSError, ValueError):
        print(json.dumps({"error": "EXECUTION_DESIGN_VERIFICATION_BLOCKED",
            "real_rules_executable": False, "activation_denied": True}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
