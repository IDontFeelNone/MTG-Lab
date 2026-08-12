import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

from card_intelligence.deck_usage import PILOT_NAMES
from card_intelligence.repository import KnowledgeRepository
from card_intelligence.topdeck_provider import (TopDeckProbeError, authorization_header,
    canonical_bytes, competitive_metrics, project_tournaments, safe_request_descriptor)

ROOT = Path(__file__).resolve().parents[1]
IDS = {name: f"00000000-0000-4000-8000-{index:012d}" for index, name in enumerate(PILOT_NAMES, 1)}


def tree_digest(relative):
    base = ROOT / relative; digest = hashlib.sha256()
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        digest.update(path.relative_to(base).as_posix().encode() + b"\0"); digest.update(path.read_bytes())
    return digest.hexdigest()


def tournament():
    return [{"TID": "T-147", "tournamentName": "Synthetic", "game": "Magic: The Gathering",
             "format": "Modern", "startDate": "2026-08-01", "participantCount": 32,
             "standings": [{"standing": 8, "deckId": "deck-8", "wins": 5, "draws": 1,
                            "losses": 2, "name": "discarded player", "email": "discarded@example.test",
                            "deckObj": {"mainboard": [{"name": "Brainstorm", "count": 4},
                                                       {"name": "Counterspell", "count": 2}],
                                        "sideboard": {"Brainstorm": 1}}}],
             "rounds": [{"round": 1, "matches": []}]}]


class Phase147TopDeckProbeTests(unittest.TestCase):
    def test_exact_scope_determinism_identity_date_format_deck_and_results(self):
        rows = project_tournaments(tournament(), IDS)
        self.assertEqual(canonical_bytes(rows), canonical_bytes(project_tournaments(tournament(), IDS)))
        self.assertEqual(len(rows), 2)
        brain = next(r for r in rows if r["card_name"] == "Brainstorm")
        self.assertEqual((brain["tournament_id"], brain["event_date"], brain["format"]),
                         ("T-147", "2026-08-01", "Modern"))
        self.assertEqual((brain["mainboard_count"], brain["sideboard_count"]), (4, 1))
        self.assertEqual((brain["placement"], brain["wins"], brain["draws"], brain["losses"]), (8, 5, 1, 2))
        self.assertEqual(brain["event_size"], 32)
        self.assertTrue(brain["rounds_available"])
        self.assertFalse(any(k in canonical_bytes(rows).decode().lower() for k in
                             ("player", "email", "username", "discord", "recommendation", "prediction", "value_score")))
        with self.assertRaisesRegex(TopDeckProbeError, "exact ten"):
            project_tournaments(tournament(), dict(list(IDS.items())[:-1]))

    def test_literal_metrics_count_card_once_per_deck_and_isolate_format(self):
        rows = project_tournaments(tournament(), IDS)
        extra = copy.deepcopy(rows[0]); extra.update(format="Legacy", tournament_id="T-2", deck_identity="D-2")
        metrics = competitive_metrics(rows + [extra], event_format="Modern")["Brainstorm"]
        self.assertEqual(metrics, {"retained_tournament_deck_count": 1, "retained_tournament_count": 1,
            "retained_copies_main_deck": 4, "retained_copies_sideboard": 1,
            "top_8_count": 1, "top_16_count": 1, "first_place_count": 0,
            "aggregate_wins": 5, "aggregate_draws": 1, "aggregate_losses": 2})

    def test_missing_decklists_malformed_records_duplicates_and_conflicts_fail_closed(self):
        missing = tournament(); missing[0]["standings"][0].pop("deckObj")
        self.assertEqual(project_tournaments(missing, IDS), [])
        for mutation, message in [
            (lambda x: x[0].pop("TID"), "requires TID"),
            (lambda x: x[0]["standings"][0].update(wins="5"), "malformed wins"),
            (lambda x: x[0]["standings"][0]["deckObj"].update(mainboard="bad"), "malformed mainboard")]:
            value = tournament(); mutation(value)
            with self.assertRaisesRegex(TopDeckProbeError, message): project_tournaments(value, IDS)
        duplicate = tournament(); duplicate[0]["standings"].append(copy.deepcopy(duplicate[0]["standings"][0]))
        with self.assertRaisesRegex(TopDeckProbeError, "duplicate"): project_tournaments(duplicate, IDS)
        duplicate[0]["standings"][1]["wins"] = 6
        with self.assertRaisesRegex(TopDeckProbeError, "conflicting"): project_tournaments(duplicate, IDS)

    def test_api_key_is_required_and_safe_diagnostics_exclude_it(self):
        with self.assertRaisesRegex(TopDeckProbeError, "TOPDECK_API_KEY"):
            authorization_header("")
        secret = "phase147-secret-never-log"
        self.assertEqual(authorization_header(secret)["Authorization"], secret)
        diagnostic = json.dumps(safe_request_descriptor({"game": "Magic: The Gathering"}))
        self.assertNotIn(secret, diagnostic); self.assertNotIn("Authorization", diagnostic)
        self.assertNotIn(secret, "\n".join(f"{k}={v}" for k, v in os.environ.items()))

    def test_retention_gate_and_protected_production_boundaries(self):
        review = (ROOT / "docs/PHASE_147_TOPDECK_PROVIDER_PROBE.md").read_text()
        self.assertIn("production retention remains blocked", review)
        self.assertIn("human/provider clarification is required", review)
        self.assertFalse((ROOT / "data/card_intelligence/competitive").exists())
        facts = KnowledgeRepository(ROOT / "data/knowledge").validate()
        self.assertEqual(len(facts), 140)
        self.assertFalse(any("competitive" in f.predicate or "tournament" in f.predicate for f in facts))
        self.assertEqual(tree_digest("data/canonical"), "e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19")
        self.assertEqual(tree_digest("data/market/observations"), "34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9")
        self.assertEqual(len(list((ROOT / "data/market/observations").rglob("*.json"))), 956)


if __name__ == "__main__":
    unittest.main()
