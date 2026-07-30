import json
from pathlib import Path

import pytest

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


def test_verification_is_derived_immutable_and_detects_raw_changes(tmp_path: Path):
    verifier = ObservationVerifier(
        [{"id": "magic.card.sol-ring", "name": "Sol Ring", "printing_id": "magic.mb2.123.en"}],
        verifier="test-index-v1",
    )
    record = verifier.verify(RAW, verified_at="2026-07-30T00:00:00+00:00")
    assert record["cards"][0]["normalized_name"] == "sol ring"
    assert record["cards"][0]["canonical_card_id"] == "magic.card.sol-ring"
    assert record["cards"][1]["verification_status"] == "unmatched"
    store = VerificationStore(tmp_path / "derived")
    path = store.save(record)
    assert json.loads(path.read_text())["raw_sha256"] == record["raw_sha256"]
    with pytest.raises(ObservationError, match="already exists"):
        store.save(record)
    changed = {**RAW, "cards": RAW["cards"][:-1]}
    with pytest.raises(ObservationError, match="changed"):
        store.assert_matches_raw(record, changed)


def test_snapshot_and_observed_ev_analytics(tmp_path: Path):
    snapshot_path = MarketSnapshotStore(tmp_path).capture(
        snapshot_id="vendor-close", captured_on="2026-07-30", provider="vendor",
        currency="usd", prices={"magic.mb2.123.en": "2.345"},
    )
    snapshot = MarketSnapshotStore.load(snapshot_path)
    verification = ObservationVerifier(
        [{"id": "magic.card.sol-ring", "name": "Sol Ring", "printing_id": "magic.mb2.123.en"}],
        verifier="test",
    ).verify(RAW, verified_at="2026-07-30T00:00:00+00:00")
    report = analyze_box([RAW], [verification], snapshot)
    assert report["pack_ev"] == [{"observation_id": "pack-1", "value": "4.70"}]
    assert report["box_ev"] == "4.70"
    assert report["duplicates"] == [{"normalized_name": "sol ring", "count": 2}]
    assert report["treatments"] == {"future_frame": 2, "standard_or_unreported": 1}
    with pytest.raises(ObservationError, match="already exists"):
        MarketSnapshotStore(tmp_path).capture(
            snapshot_id="vendor-close", captured_on="2026-07-30", provider="vendor",
            currency="USD", prices={},
        )
