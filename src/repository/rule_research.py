"""Validated access to retained, non-canonical product-rule research artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from validation import SchemaValidationError, validate_document

from .evidence import EvidenceRepositoryError, load_evidence_bundle
from .sources import SourceLoadError, load_source_record

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_RESEARCH_ROOT = _PROJECT_ROOT / "data" / "intermediate" / "research"
_DEFAULT_GAMES_ROOT = _PROJECT_ROOT / "data" / "canonical" / "games"


class RuleResearchError(ValueError):
    """Raised when retained rule research is invalid or not evidence-grounded."""


def load_rule_research(
    game: str,
    product_id: str,
    phase: str,
    *,
    research_root: Path | None = None,
    evidence_root: Path | None = None,
    games_root: Path | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Load and cross-validate a Rule Claim Matrix and its sufficiency report."""
    root = Path(research_root) if research_root is not None else _DEFAULT_RESEARCH_ROOT
    directory = root / product_id / phase
    matrix = _load_json(directory / "rule-claim-matrix.json", "rule-claim-matrix")
    report = _load_json(
        directory / "evidence-sufficiency-report.json", "evidence-sufficiency-report"
    )
    for artifact in (matrix, report):
        if artifact["game"] != game or artifact["product_id"] != product_id:
            raise RuleResearchError("Research artifact identity does not match its path")
    if report["rule_claim_matrix_id"] != matrix["id"]:
        raise RuleResearchError("Sufficiency report references a different Rule Claim Matrix")

    claim_ids = [claim["id"] for claim in matrix["claims"]]
    if len(claim_ids) != len(set(claim_ids)):
        raise RuleResearchError("Rule Claim Matrix contains duplicate claim identifiers")
    if claim_ids != sorted(claim_ids):
        raise RuleResearchError("Rule Claim Matrix claims must use deterministic id order")

    classified = (
        report["known_claim_ids"]
        + report["partially_known_claim_ids"]
        + report["unknown_claim_ids"]
    )
    if len(classified) != len(set(classified)) or set(classified) != set(claim_ids):
        raise RuleResearchError("Sufficiency report must classify every claim exactly once")
    for field in ("known_claim_ids", "partially_known_claim_ids", "unknown_claim_ids"):
        if report[field] != sorted(report[field]):
            raise RuleResearchError(f"{field} must use deterministic id order")

    canonical_games = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    bundles: dict[str, Any] = {}
    for claim in matrix["claims"]:
        source_ids = set(claim["source_record_ids"])
        if claim["classification"] == "unsupported" and (
            source_ids or claim["evidence_references"] or claim["source_locators"]
        ):
            raise RuleResearchError(
                f"Unsupported claim {claim['id']} must not cite supporting evidence"
            )
        for source_id in source_ids:
            try:
                load_source_record(game, product_id, source_id, games_root=canonical_games)
            except SourceLoadError as error:
                raise RuleResearchError(
                    f"Claim {claim['id']} references invalid source {source_id}: {error}"
                ) from error
        evidence_sources: set[str] = set()
        for reference in claim["evidence_references"]:
            bundle_id = reference["bundle_id"]
            if bundle_id not in bundles:
                try:
                    bundles[bundle_id] = load_evidence_bundle(
                        game,
                        bundle_id,
                        evidence_root=evidence_root,
                        games_root=canonical_games,
                    )
                except EvidenceRepositoryError as error:
                    raise RuleResearchError(
                        f"Claim {claim['id']} references invalid evidence: {error}"
                    ) from error
            bundle = bundles[bundle_id]
            artifacts = {artifact.id: artifact for artifact in bundle.artifacts}
            if reference["artifact_id"] not in artifacts:
                raise RuleResearchError(
                    f"Claim {claim['id']} references missing artifact "
                    f"{reference['artifact_id']} in {bundle_id}"
                )
            evidence_sources.update(
                entry["source_id"] for entry in artifacts[reference["artifact_id"]].provenance
            )
        if not source_ids.issubset(evidence_sources):
            missing = ", ".join(sorted(source_ids - evidence_sources))
            raise RuleResearchError(
                f"Claim {claim['id']} sources are not attributed by its evidence: {missing}"
            )
    return matrix, report


def rule_research_bytes(
    game: str,
    product_id: str,
    phase: str,
    **kwargs: Any,
) -> bytes:
    """Return deterministic derived bytes for a validated research pair."""
    matrix, report = load_rule_research(game, product_id, phase, **kwargs)
    return json.dumps(
        {"matrix": matrix, "report": report}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _load_json(path: Path, schema_name: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuleResearchError(f"Cannot load {schema_name}: {path}") from error
    if not isinstance(document, dict):
        raise RuleResearchError(f"{schema_name} must be a JSON object")
    try:
        validate_document(document, schema_name)
    except SchemaValidationError as error:
        raise RuleResearchError(str(error)) from error
    return document


__all__ = ["RuleResearchError", "load_rule_research", "rule_research_bytes"]
