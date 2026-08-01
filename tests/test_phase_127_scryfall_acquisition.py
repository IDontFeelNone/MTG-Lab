"""Phase 127 Scryfall acquisition, isolation, integrity, and failure tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch
import urllib.error

from market import MarketObservationRepository, MarketValidationError
from market.scryfall import (ProviderAcquisitionError, ProviderRateLimitError,
    ScryfallMarketAdapter, canonical_json, load_payload, sha256_bytes)
from scripts.scryfall_market_acquisition import fetch, run

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


class Phase127Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical_bytes = (ROOT / "data/canonical/state.json").read_bytes()
        cls.state = json.loads(cls.canonical_bytes)
        cls.printing_id, cls.printing = next(iter(cls.state["printing"].items()))
        values = cls.printing["values"]
        cls.record = {"object":"card", "id":values["identifiers"]["scryfallId"],
            "set":"mb2", "collector_number":values["collector_number"], "lang":"en",
            "finishes":[values["finish_ids"][0]],
            "prices":{"usd":"1.2300", "usd_foil":None, "usd_etched":None}}

    def adapter(self, state=None):
        return ScryfallMarketAdapter(state or self.state, "sha256:canonical")

    def test_payload_validation_and_source_digest(self):
        raw = canonical_json([self.record])
        self.assertEqual(load_payload(raw)[0]["id"], self.record["id"])
        self.assertEqual(sha256_bytes(raw), hashlib.sha256(raw).hexdigest())
        with self.assertRaises(MarketValidationError): load_payload(b"{}")
        with self.assertRaises(MarketValidationError): self.adapter().validate_record({"id":"x"})

    def test_exact_identifier_mapping_normalization_decimal_and_missing(self):
        observations, mappings = self.adapter().normalize([self.record], observed_at=NOW,
            retrieved_at=NOW, source_url="fixture", source_digest="a"*64)
        self.assertEqual(mappings[0]["mapping_method"], "canonical_external_identifier")
        self.assertEqual(observations[0].entity_id, self.printing_id)
        self.assertEqual(observations[0].price, Decimal("1.2300"))
        missing = dict(self.record); missing["prices"] = {"usd":None,"usd_foil":None,"usd_etched":None}
        values, _ = self.adapter().normalize([missing], observed_at=NOW, retrieved_at=NOW,
            source_url="fixture", source_digest="b"*64)
        self.assertIsNone(values[0].price)

    def test_deterministic_normalization_and_currency(self):
        a, _ = self.adapter().normalize([self.record], observed_at=NOW, retrieved_at=NOW,
            source_url="fixture", source_digest="a"*64)
        b, _ = self.adapter().normalize([self.record], observed_at=NOW, retrieved_at=NOW,
            source_url="fixture", source_digest="a"*64)
        self.assertEqual(a[0].to_dict(), b[0].to_dict())
        self.assertEqual(a[0].currency, "USD")

    def test_tuple_mapping_language_finish_isolation_unmatched(self):
        record = dict(self.record); record["id"] = "00000000-0000-4000-8000-000000000000"
        resolution = self.adapter().resolve(record, self.record["finishes"][0])
        self.assertEqual(resolution.method, "set_collector_language_finish")
        wrong = dict(record); wrong["lang"] = "fr"
        self.assertEqual(self.adapter().resolve(wrong, self.record["finishes"][0]).status, "unmatched")
        self.assertEqual(self.adapter().resolve(record, "foil" if self.record["finishes"][0] != "foil" else "nonfoil").status, "unmatched")

    def test_ambiguous_and_conflicting_mapping(self):
        state = json.loads(self.canonical_bytes)
        duplicate = json.loads(json.dumps(self.printing)); state["printing"]["duplicate-printing"] = duplicate
        resolution = self.adapter(state).resolve(self.record, self.record["finishes"][0])
        self.assertEqual(resolution.status, "ambiguous")
        adapter = ScryfallMarketAdapter(self.state, "sha256:x", {self.record["id"]:"missing"})
        self.assertEqual(adapter.resolve(self.record, self.record["finishes"][0]).status, "rejected")

    def test_mb2_only_target_isolation(self):
        other = dict(self.record); other["set"] = "msh"; other["id"] = "other"
        observations, mappings = self.adapter().normalize([other], observed_at=NOW,
            retrieved_at=NOW, source_url="fixture", source_digest="a"*64)
        self.assertFalse(observations); self.assertEqual(mappings[0]["status"], "rejected")

    def test_append_replay_conflict_and_tamper_detection(self):
        observation = self.adapter().normalize([self.record], observed_at=NOW, retrieved_at=NOW,
            source_url="fixture", source_digest="a"*64)[0][0]
        with tempfile.TemporaryDirectory() as temp:
            repository = MarketObservationRepository(Path(temp))
            path = repository.append(observation)
            self.assertEqual(path, repository.append(observation))
            path.write_text(path.read_text().replace('"1.2300"', '"9.99"'))
            with self.assertRaises(MarketValidationError): repository.load(path)
            with self.assertRaises(MarketValidationError): repository.append(observation)

    def test_run_manifest_digests_verification_and_no_canonical_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/"canonical").mkdir(); (root/"canonical/state.json").write_bytes(self.canonical_bytes)
            payload = root/"payload.json"; payload.write_bytes(canonical_json([self.record]))
            before = hashlib.sha256((root/"canonical/state.json").read_bytes()).hexdigest()
            result = run(root, payload_path=payload, retrieved_at=NOW, persist=True, run_id="one")
            self.assertEqual(result["observation_count"], 1)
            self.assertEqual(result["source_record_count"], 1)
            self.assertEqual(result["mb2_record_count"], 1)
            self.assertEqual(result["matched_printing_count"], 1)
            self.assertEqual(result["known_price_observation_count"], 1)
            self.assertEqual(result["missing_price_observation_count"], 0)
            self.assertFalse(result["canonical_write"]); self.assertFalse(result["promotion_performed"])
            normalized = (root/"market/acquisitions/one/normalized.json").read_bytes()
            self.assertEqual(result["normalized_sha256"], sha256_bytes(normalized))
            self.assertEqual(before, hashlib.sha256((root/"canonical/state.json").read_bytes()).hexdigest())
            for path in (root/"market/observations").glob("*/*/*/*.json"):
                MarketObservationRepository(root/"market/observations").load(path)

    def test_provider_failure_rate_limit_and_secret_redaction(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x?token=SECRET",429,"",{},None)):
            with self.assertRaisesRegex(ProviderRateLimitError, "429"): fetch("https://x?token=SECRET")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("token=SECRET")):
            with self.assertRaises(ProviderAcquisitionError) as caught: fetch("https://x?token=SECRET")
        self.assertNotIn("SECRET", str(caught.exception))

    def test_cli_unknown_contract_and_no_recommendation_behavior(self):
        command = [sys.executable,"-m","mtglab","--data-root","data","market","printing",self.printing_id]
        completed = subprocess.run(command, cwd=ROOT, env={**os.environ,"PYTHONPATH":"src"},
            capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        for key in ("provider","observation_timestamp","currency","confidence","provenance","canonical_snapshot_identity","status"):
            self.assertIn(key, output)
        production_observations = tuple((ROOT / "data/market/observations").glob("*/*/*/*.json"))
        self.assertEqual(output["status"], "known" if production_observations else "unknown")
        self.assertNotIn("recommend", json.dumps(output).lower())

    def test_production_lifecycle_state_is_internally_valid(self):
        """Production may legitimately be empty or contain only verified observations."""
        root = ROOT / "data/market/observations"
        paths = tuple(root.glob("*/*/*/*.json")) if root.exists() else ()
        repository = MarketObservationRepository(root)
        for path in paths:
            observation = repository.load(path)
            self.assertEqual(observation.provider, "scryfall")
            self.assertEqual(observation.entity_type, "printing")
            self.assertEqual(observation.currency, "USD")
            self.assertIn(observation.entity_id, self.state["printing"])


if __name__ == "__main__": unittest.main()
