import json
import tempfile
import unittest
from pathlib import Path

from observations import MarketSnapshotStore, ObservationVerifier, VerificationStore, analyze_box
from observations.verification import ObservationError


RAW = {
    "observation_id": "pack-1",
    "cards": [
        {"position": 1, "reported_name": "  Sol Ring! ", "reported_treatment": "future_frame"},
        {"position": 2, "reported_name": "Unknown Card", "reported_treatment": None},
        {"position": 3, "reported_name": "Sol Ring", "reported_treatment": "future_frame"},
    ],
}


class ObservationIntelligenceTests(unittest.TestCase):
    def test_verification_is_derived_immutable_and_detects_raw_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            verifier = ObservationVerifier(
                [{"id": "magic.card.sol-ring", "name": "Sol Ring", "printing_id": "magic.mb2.123.en"}],
                verifier="test-index-v1",
            )
            record = verifier.verify(RAW, verified_at="2026-07-30T00:00:00+00:00")
            self.assertEqual(record["cards"][0]["normalized_name"], "sol ring")
            self.assertEqual(record["cards"][0]["canonical_card_id"], "magic.card.sol-ring")
            self.assertEqual(record["cards"][1]["verification_status"], "unmatched")
            store = VerificationStore(Path(directory) / "derived")
            path = store.save(record)
            self.assertEqual(json.loads(path.read_text())["raw_sha256"], record["raw_sha256"])
            with self.assertRaisesRegex(ObservationError, "already exists"):
                store.save(record)
            changed = {**RAW, "cards": RAW["cards"][:-1]}
            with self.assertRaisesRegex(ObservationError, "changed"):
                store.assert_matches_raw(record, changed)

    def test_snapshot_and_observed_ev_analytics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot_path = MarketSnapshotStore(root).capture(
                snapshot_id="vendor-close", captured_on="2026-07-30", provider="vendor",
                currency="usd", prices={"magic.mb2.123.en": "2.345"},
            )
            snapshot = MarketSnapshotStore.load(snapshot_path)
            verification = ObservationVerifier(
                [{"id": "magic.card.sol-ring", "name": "Sol Ring", "printing_id": "magic.mb2.123.en"}],
                verifier="test",
            ).verify(RAW, verified_at="2026-07-30T00:00:00+00:00")
            report = analyze_box([RAW], [verification], snapshot)
            self.assertEqual(report["pack_ev"], [{"observation_id": "pack-1", "value": "4.70"}])
            self.assertEqual(report["box_ev"], "4.70")
            self.assertEqual(report["duplicates"], [{"normalized_name": "sol ring", "count": 2}])
            self.assertEqual(report["treatments"], {"future_frame": 2, "standard_or_unreported": 1})
            with self.assertRaisesRegex(ObservationError, "already exists"):
                MarketSnapshotStore(root).capture(
                    snapshot_id="vendor-close", captured_on="2026-07-30", provider="vendor",
                    currency="USD", prices={},
                )
