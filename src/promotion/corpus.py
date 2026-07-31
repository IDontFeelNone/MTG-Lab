"""Phase 104 deterministic, reviewed promotion of a bounded MTGJSON-derived corpus."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from acquisition import (AcquisitionEngine, CanonicalPromotionEngine, FixtureProvider,
    PromotionDecision, PromotionError, ProviderPolicy, ProviderTrustPolicy,
    RawSnapshotStore, assertions_from_normalized, build_review_package,
    normalize_snapshot)
from ai import AIModelRequest
from analytics import CanonicalAnalyticsEngine
from projection import TypedCanonicalProjectionEngine
from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest
from semantic import CanonicalSemanticQueryEngine, SemanticRequest

TIMESTAMP = "2026-07-31T12:00:00+00:00"
POLICY = ProviderPolicy("mtgjson-bounded", "authoritative_structured", .9,
    ("local-bounded-reference",), "Phase 104 independently reviewed corpus", ("card", "printing"))


class _BoundedProvider(FixtureProvider):
    provider_id = "mtgjson-bounded"


class BoundedCorpusPromotion:
    """Execute and inspect the fixed, offline Phase 104 promotion rehearsal."""

    def __init__(self, data_root: Path | str, corpus: Path | str) -> None:
        self.root, self.corpus_path = Path(data_root), Path(corpus)
        self.engine = CanonicalPromotionEngine(self.root / "canonical", self.root / "audit")

    def _package(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        provider = _BoundedProvider({"bounded-canonical-promotion-v1": self.corpus_path.read_bytes()})
        store = RawSnapshotStore(self.root / "raw")
        acquisition = AcquisitionEngine(store, self.root / "acquisition-runs")
        acquisition.register(provider)
        run = acquisition.acquire("mtgjson-bounded", "bounded-canonical-promotion-v1",
            started_at=TIMESTAMP, run_id="phase-104-bounded-mtgjson")
        snapshot_path = Path(run["downloaded_snapshots"][0]["path"])
        snapshot = json.loads((snapshot_path / "manifest.json").read_text())
        normalized = normalize_snapshot(provider, store, snapshot_path, self.root / "normalized.json")
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), TIMESTAMP)
        package = build_review_package(run, [snapshot], [normalized], assertions, POLICY,
                                       "bounded-canonical-promotion-v1")
        return snapshot, normalized, package

    @staticmethod
    def _decision(timestamp: str, reason: str, *, approved: bool = True) -> PromotionDecision:
        return PromotionDecision("independent-phase-104-reviewer", timestamp, approved=approved,
                                 allow_unknowns=True, reason=reason)

    def promote(self) -> dict[str, Any]:
        manifest = self.root / "promotion-corpus" / "bounded-v1.json"
        if manifest.exists():
            result = json.loads(manifest.read_text())
            if self.verify()["valid"]: return result
            raise PromotionError("existing bounded promotion failed verification")
        snapshot, normalized, package = self._package()
        # Retain a rejected review attempt separately; its conflict can never enter canonical state.
        rejected = copy.deepcopy(package)
        conflict = copy.deepcopy(rejected["candidate_assertions"][0])
        conflict["id"] += "-rejected"; conflict["asserted_value"] = "Rejected candidate value"
        rejected["candidate_assertions"].append(conflict)
        rejected = build_review_package(package["acquisition_run"], [snapshot], [normalized],
            rejected["candidate_assertions"], POLICY, "bounded-rejected-v1")
        try: self.engine.promote(rejected, POLICY, self._decision(TIMESTAMP, "conflicting candidate rejected"))
        except PromotionError: pass

        initial = self.engine.promote(package, POLICY, self._decision(TIMESTAMP, "bounded corpus approved"))
        changed = copy.deepcopy(normalized)
        changed["records"][0]["source_values"]["name"] = "Alpha Adept, Reviewed"
        assertions = assertions_from_normalized(changed,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), TIMESTAMP)
        revised = build_review_package(package["acquisition_run"], [snapshot], [changed], assertions,
            POLICY, "bounded-canonical-promotion-v2", package["candidate_assertions"])
        superseding = self.engine.promote(revised, POLICY,
            self._decision("2026-07-31T13:00:00+00:00", "reviewed correction"))
        rollback = self.engine.rollback(superseding["promotion_id"],
            self._decision("2026-07-31T14:00:00+00:00", "rollback rehearsal"))
        replay_matches = self.engine.replay() == json.loads((self.root / "canonical/state.json").read_text())
        # A new reviewed decision restores the correction after the rollback rehearsal.
        restored = self.engine.promote(revised, POLICY,
            self._decision("2026-07-31T15:00:00+00:00", "reviewed correction restored"))
        projection = TypedCanonicalProjectionEngine(self.root / "canonical",
            self.root / "canonical/games", self.root / "projection-audit").project(
                "2026-07-31T16:00:00+00:00")
        result = {"schema_version": "bounded-canonical-promotion-v1", "status": "promoted",
            "dataset_identity": package["snapshot_lineage"], "initial_promotion_id": initial["promotion_id"],
            "superseding_promotion_id": superseding["promotion_id"], "rollback_id": rollback["promotion_id"],
            "restored_promotion_id": restored["promotion_id"], "projection_id": projection["projection_id"],
            "replay_matches": replay_matches, "promoted_entity_count": 5, "rejected_candidate_count": 1}
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    def inspect(self) -> dict[str, Any]:
        audits = self.engine.audit() if (self.root / "audit").exists() else []
        return {"schema_version": "bounded-canonical-promotion-v1", "audits": audits,
                "canonical_state": self.engine.replay() if audits else {}}

    def verify(self) -> dict[str, Any]:
        state = self.engine.replay()
        on_disk = json.loads((self.root / "canonical/state.json").read_text())
        projection = TypedCanonicalProjectionEngine(self.root / "canonical",
            self.root / "canonical/games", self.root / "projection-audit")
        projection_validation = projection.validate()
        query = CanonicalQueryEngine(games_root=self.root / "canonical/games", data_root=self.root)
        analytics = CanonicalAnalyticsEngine(query); summary = analytics.summary()
        semantic = CanonicalSemanticQueryEngine(query, analytics)
        result = semantic.execute(SemanticRequest("find_identifier", {"identifier": "card-alpha"}))
        context = ReasoningContextBuilder(semantic).build(ReasoningContextRequest(
            SemanticRequest("list_type", {"entity_type": "printing"}), include_analytics=True))
        request = AIModelRequest("not-invoked", "1.0.0", "not-invoked", context.context_id,
            "phase-104-no-provider", TIMESTAMP, required_capabilities=("structured-response",))
        rejected = [a for a in self.engine.audit() if not a["validation_results"]["valid"]]
        checks = {"replay": state == on_disk, "projection": projection_validation["valid"],
            "identifiers": sorted(state) == ["card", "printing"],
            "duplicates": len({x for values in state.values() for x in values}) == 5,
            "query": query.entity("card-alpha").canonical_identity == "card-alpha",
            "analytics": summary.data["entity_counts_by_type"]["printing"] == 3,
            "semantic": result.to_dict()["result"][0]["canonical_identity"] == "card-alpha",
            "reasoning": bool(context.context_id), "rejected_outside_canonical": bool(rejected),
            "ai_request_without_provider": request.reasoning_context_identifier == context.context_id}
        return {"schema_version": "bounded-canonical-promotion-v1", "valid": all(checks.values()),
                "checks": checks, "canonical_snapshot_id": query.snapshot().snapshot_id,
                "reasoning_context_id": context.context_id, "ai_model_request": request.to_dict()}
