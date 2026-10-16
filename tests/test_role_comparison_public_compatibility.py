"""Characterize existing public bytes in place, without permission or activation."""
import hashlib
import json
from pathlib import Path
import unittest

from card_intelligence.comparison import ContextualCardComparisonPilot, comparison_explanation
from card_intelligence.mechanics import MechanicalCardIntelligence, stable_json
from card_intelligence.roles import FunctionalRolePilot
from repository.legacy_profile import attach_legacy_compatibility
from repository.snapshots import SnapshotError

ROOT = Path(__file__).resolve().parents[1]
CONTROL = "config/catalog_profiles/legacy-public-tier-a.json"
EXPECTED_QUERY = "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"


def digest(value):
    raw = value.encode() if isinstance(value, str) else stable_json(value).encode()
    return hashlib.sha256(raw).hexdigest()


class RoleComparisonPublicCompatibilityTests(unittest.TestCase):
    def test_current_public_exact_role_comparison_parity_or_explicit_baseline_drift_block(self):
        control = json.loads((ROOT / CONTROL).read_bytes())

        def attach():
            return attach_legacy_compatibility(ROOT, control_path=CONTROL, game="magic",
                expected_profile_id=control["profile_id"])

        intact = all(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
                     for row in control["files"])
        # A writer-produced expanded checkout is a genuinely different current
        # catalog. The reviewed old profile must block rather than use history.
        if not intact:
            with self.assertRaises(SnapshotError):
                MechanicalCardIntelligence.from_attachment(attach(), data_root=ROOT / "data",
                    expected_query_snapshot_id=EXPECTED_QUERY)
            return
        protected_paths = [ROOT / row["path"] for row in control["files"]]
        for family in ("data/review/functional-role-pilot", "data/review/contextual-card-comparison",
                       "data/review/card-acquisition-pilot"):
            protected_paths.extend(path for path in (ROOT / family).rglob("*") if path.is_file())
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected_paths}
        mechanical = MechanicalCardIntelligence.from_attachment(attach(), data_root=ROOT / "data",
            expected_query_snapshot_id=EXPECTED_QUERY)
        attached_roles = FunctionalRolePilot.from_mechanical(mechanical)
        attached_comparison = ContextualCardComparisonPilot.from_roles(attached_roles)
        legacy_roles = FunctionalRolePilot(ROOT / "data")
        legacy_comparison = ContextualCardComparisonPilot(ROOT / "data")
        self.assertIs(attached_roles.mechanical, mechanical)
        self.assertIs(attached_comparison.roles, attached_roles)
        self.assertEqual(mechanical.snapshot_id, EXPECTED_QUERY)
        self.assertEqual(len(attached_roles.cards), 15)
        self.assertEqual(attached_roles.report()["candidate_count"], 30)
        self.assertEqual(digest(sorted(attached_roles.cards)), digest(sorted(legacy_roles.cards)))
        self.assertEqual(attached_roles.plan_identity, legacy_roles.plan_identity)
        self.assertEqual(attached_roles.vocabulary_identity, legacy_roles.vocabulary_identity)
        self.assertEqual(digest(attached_roles.report()), digest(legacy_roles.report()))
        self.assertEqual(digest(attached_roles.comparison()), digest(legacy_roles.comparison()))
        for card_id in sorted(attached_roles.cards):
            with self.subTest(card_id=card_id):
                attached = attached_roles.dossier(card_id)
                legacy = legacy_roles.dossier(card_id)
                self.assertEqual(digest(attached), digest(legacy))
                self.assertEqual(attached["dossier_id"], legacy["dossier_id"])
                self.assertEqual([c["candidate_id"] for c in attached["role_candidates"]],
                                 [c["candidate_id"] for c in legacy["role_candidates"]])
                self.assertTrue(all(c["review"]["status"] == "requires_review"
                                    for c in attached["role_candidates"]))
                self.assertEqual(digest(attached_roles.reasoning_context(card_id).to_json()),
                                 digest(legacy_roles.reasoning_context(card_id).to_json()))
        attached = attached_comparison.dossier().to_dict()
        legacy = legacy_comparison.dossier().to_dict()
        self.assertEqual(digest(attached), digest(legacy))
        self.assertEqual(attached["comparison_id"], legacy["comparison_id"])
        self.assertEqual(attached_comparison.context_identity, legacy_comparison.context_identity)
        self.assertEqual(attached_comparison.plan_identity, legacy_comparison.plan_identity)
        self.assertEqual(digest(attached_comparison.decision_inputs()),
                         digest(legacy_comparison.decision_inputs()))
        recommendation = attached["decision_intelligence"]["reasoning_context"]["recommendation"]
        self.assertEqual(recommendation["outcome"], "abstain")
        self.assertIsNone(recommendation["selected_alternative_id"])
        handoff, previous = attached_comparison.reasoning_context(), legacy_comparison.reasoning_context()
        self.assertEqual(digest(handoff), digest(previous))
        self.assertEqual(handoff["handoff_id"], previous["handoff_id"])
        self.assertTrue(all(c["canonical_snapshot_id"] == EXPECTED_QUERY for c in handoff["canonical_contexts"]))
        self.assertEqual(digest(comparison_explanation(attached_comparison.dossier())),
                         digest(comparison_explanation(legacy_comparison.dossier())))
        self.assertEqual({path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before}, before)


if __name__ == "__main__":
    unittest.main()
