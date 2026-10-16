"""Explicit offline TXT verification CLI; emits metadata-only JSON to stdout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from gameplay_rules.errors import GameplayContractError
from .artifacts import ArtifactVerificationRequest, verify_local_artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="explicit operator-supplied local TXT path")
    parser.add_argument("--request", required=True, help="metadata-only verification request JSON")
    parser.add_argument("--expected-request-id", required=True)
    parser.add_argument("--release-candidate-id", required=True)
    parser.add_argument("--discovery-source-reference-id", required=True)
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--observed-at", default=None, help="optional retained ISO timestamp; no implicit clock")
    args = parser.parse_args(argv)
    try:
        request_path = Path(args.request)
        # Request is authored metadata, still bounded and integrity-verified.
        from .artifacts import _open_regular_no_symlinks
        descriptor = _open_regular_no_symlinks(request_path)
        if descriptor is None:
            raise GameplayContractError("artifact_request_binding", "verification request unavailable")
        import os
        with os.fdopen(descriptor, "rb") as stream:
            encoded = stream.read(65537)
        if len(encoded) > 65536:
            raise GameplayContractError("artifact_request_binding", "verification request exceeds metadata limit")
        request = ArtifactVerificationRequest.from_json(encoded)
        result = verify_local_artifact(args.artifact, request,
                                      expected_request_id=args.expected_request_id,
                                      expected_release_candidate_id=args.release_candidate_id,
                                      expected_discovery_source_reference_id=args.discovery_source_reference_id,
                                      game_id=args.game_id, observed_at=args.observed_at)
        print(json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        return 0 if result.status == "VERIFIED_EXPECTED_ARTIFACT" else 1
    except (GameplayContractError, OSError):
        # No absolute paths or source snippets in CLI failure output.
        print(json.dumps({"error": "ARTIFACT_VERIFICATION_BLOCKED", "content_retained": False,
                          "projection_authorized": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
