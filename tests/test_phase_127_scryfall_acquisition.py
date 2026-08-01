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
from email.message import Message

from market import MarketObservationRepository, MarketValidationError
from market.scryfall import (ProviderAcquisitionError, ProviderRateLimitError,
    ScryfallMarketAdapter, canonical_json, load_payload, sha256_bytes)
from scripts.scryfall_market_acquisition import (METADATA_URL, MAX_ATTEMPTS, fetch,
    new_diagnostics, parse_bulk_metadata, run)

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


class Response:
    def __init__(self, payload=b"{}", content_type="application/json", status=200):
        self.payload, self.status = payload, status
        self.headers = Message(); self.headers["Content-Type"] = content_type
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def getcode(self): return self.status
    def read(self): return self.payload


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

    def metadata(self, **changes):
        value = {"object":"bulk_data", "type":"default_cards",
            "download_uri":"https://data.scryfall.io/default-cards/test.json",
            "updated_at":"2026-08-01T10:00:00Z"}
        value.update(changes)
        return value

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
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x?token=SECRET",429,"",{},None)), patch("time.sleep"):
            with self.assertRaisesRegex(ProviderRateLimitError, "429"): fetch("https://x?token=SECRET")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("token=SECRET")), patch("time.sleep"):
            with self.assertRaises(ProviderAcquisitionError) as caught: fetch("https://x?token=SECRET")
        self.assertNotIn("SECRET", str(caught.exception))

    def test_official_metadata_contract_and_download_uri(self):
        self.assertEqual(METADATA_URL, "https://api.scryfall.com/bulk-data/default_cards")
        metadata = canonical_json({"object":"bulk_data", "type":"default_cards",
            "download_uri":"https://data.scryfall.io/default-cards/test.json",
            "updated_at":"2026-08-01T10:00:00Z"})
        with tempfile.TemporaryDirectory() as temp, patch("urllib.request.urlopen",
                side_effect=[Response(metadata), Response(canonical_json([self.record]))]) as opened:
            root=Path(temp); (root/"canonical").mkdir(); (root/"canonical/state.json").write_bytes(self.canonical_bytes)
            report = run(root, payload_path=None, retrieved_at=NOW, persist=False, run_id="dry")
        self.assertEqual(opened.call_count, 2)
        self.assertEqual(report["source_url"], "https://data.scryfall.io/default-cards/test.json")
        self.assertTrue(report["acquisition_diagnostics"]["download_uri_obtained"])
        self.assertTrue(report["acquisition_diagnostics"]["bulk_payload_download_began"])

    def test_direct_and_list_metadata_shapes(self):
        for value, shape, inspected in (
                (self.metadata(), "direct_object", 1),
                ({"object":"list", "data":[self.metadata(type="oracle_cards"),
                                              self.metadata()]}, "list_object", 2)):
            with self.subTest(shape=shape):
                diagnostic = new_diagnostics()
                uri, updated = parse_bulk_metadata(canonical_json(value), diagnostic)
                self.assertEqual(uri, "https://data.scryfall.io/default-cards/test.json")
                self.assertEqual(updated, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))
                self.assertEqual(diagnostic["metadata_parsing_shape"], shape)
                self.assertEqual(diagnostic["bulk_entries_inspected"], inspected)
                self.assertEqual(diagnostic["default_cards_matches"], 1)
                self.assertEqual(diagnostic["selected_bulk_type"], "default_cards")
                self.assertTrue(diagnostic["updated_at_present"])
                self.assertTrue(diagnostic["download_uri_valid"])

    def test_metadata_match_cardinality_error_and_contract_fail_closed(self):
        invalid = [
            {"object":"list", "data":[self.metadata(type="oracle_cards")]},
            {"object":"list", "data":[self.metadata(), self.metadata()]},
            {"object":"list", "data":[self.metadata(object="card")]},
            {"object":"error", "code":"not_found", "details":"provider body"},
            [],
            {"object":"catalog", "data":[]},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ProviderAcquisitionError):
                parse_bulk_metadata(canonical_json(value), new_diagnostics())

    def test_metadata_download_uri_boundary(self):
        invalid = [None, "", "   ", "not a uri",
                   "http://data.scryfall.io/default-cards/test.json",
                   "https://api.scryfall.com/default-cards/test.json",
                   "https://data.scryfall.io.evil.invalid/test.json",
                   "https://user@data.scryfall.io/test.json"]
        for uri in invalid:
            diagnostic = new_diagnostics()
            with self.subTest(uri=uri), self.assertRaises(ProviderAcquisitionError) as caught:
                parse_bulk_metadata(canonical_json(self.metadata(download_uri=uri)), diagnostic)
            self.assertEqual(caught.exception.diagnostics["failing_stage"],
                             "download_uri_extraction")
            self.assertFalse(diagnostic["download_uri_valid"])

    def test_metadata_updated_at_required_and_well_formed_before_download(self):
        for updated_at in (None, "", "not-a-timestamp", "2026-08-01"):
            value = self.metadata()
            if updated_at is None:
                value.pop("updated_at")
            else:
                value["updated_at"] = updated_at
            with self.subTest(updated_at=updated_at), tempfile.TemporaryDirectory() as temp, \
                    patch("urllib.request.urlopen", return_value=Response(canonical_json(value))) as opened:
                root=Path(temp); (root/"canonical").mkdir()
                (root/"canonical/state.json").write_bytes(self.canonical_bytes)
                with self.assertRaises(ProviderAcquisitionError) as caught:
                    run(root, payload_path=None, retrieved_at=NOW, persist=False, run_id="dry")
                self.assertEqual(opened.call_count, 1)
                self.assertFalse(caught.exception.diagnostics["bulk_payload_download_began"])

    def test_structural_metadata_failure_is_not_retried_or_persisted(self):
        with tempfile.TemporaryDirectory() as temp, patch("urllib.request.urlopen",
                return_value=Response(canonical_json({"object":"list", "data":[]}))) as opened:
            root=Path(temp); (root/"canonical").mkdir()
            canonical = root/"canonical/state.json"; canonical.write_bytes(self.canonical_bytes)
            before = canonical.read_bytes()
            with self.assertRaises(ProviderAcquisitionError) as caught:
                run(root, payload_path=None, retrieved_at=NOW, persist=True, run_id="failed")
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(canonical.read_bytes(), before)
            self.assertFalse((root/"market").exists())
            self.assertFalse(caught.exception.diagnostics["bulk_payload_download_began"])

    def test_redirects_are_accepted_by_default_opener(self):
        # urlopen normally consumes redirects; a final redirected response is transparent to fetch.
        with patch("urllib.request.urlopen", return_value=Response(b"[]")) as opened:
            self.assertEqual(fetch("https://api.scryfall.com/x", sleep=lambda _: None), b"[]")
        self.assertEqual(opened.call_count, 1)

    def test_permanent_403_and_404_are_not_retried(self):
        for status in (403, 404):
            diagnostic = new_diagnostics()
            error = urllib.error.HTTPError("https://secret.invalid/?token=x", status, "", {}, None)
            with self.subTest(status=status), patch("urllib.request.urlopen", side_effect=error) as opened:
                with self.assertRaises(ProviderAcquisitionError) as caught:
                    fetch("https://secret.invalid/?token=x", diagnostics=diagnostic, sleep=lambda _: None)
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(caught.exception.diagnostics["http_status"], status)

    def test_transient_5xx_retries_then_succeeds_or_exhausts(self):
        failure = urllib.error.HTTPError("https://api.scryfall.com/x", 503, "", {}, None)
        with patch("urllib.request.urlopen", side_effect=[failure, Response(b"[]")]) as opened:
            self.assertEqual(fetch("https://api.scryfall.com/x", sleep=lambda _: None), b"[]")
        self.assertEqual(opened.call_count, 2)
        with patch("urllib.request.urlopen", side_effect=failure) as opened:
            with self.assertRaises(ProviderAcquisitionError) as caught:
                fetch("https://api.scryfall.com/x", sleep=lambda _: None)
        self.assertEqual(opened.call_count, MAX_ATTEMPTS)
        self.assertEqual(caught.exception.diagnostics["attempts"], MAX_ATTEMPTS)

    def test_timeout_and_invalid_content_type_diagnostics(self):
        with patch("urllib.request.urlopen", side_effect=TimeoutError), self.assertRaises(ProviderAcquisitionError) as caught:
            fetch("https://api.scryfall.com/x", sleep=lambda _: None)
        self.assertIsNone(caught.exception.diagnostics["http_status"])
        with patch("urllib.request.urlopen", return_value=Response(b"provider body", "text/html")):
            with self.assertRaises(ProviderAcquisitionError) as caught:
                fetch("https://api.scryfall.com/x", sleep=lambda _: None)
        diagnostic = caught.exception.diagnostics
        self.assertEqual(diagnostic["response_content_type"], "text/html")
        self.assertNotIn("provider body", json.dumps(diagnostic))
        with patch("urllib.request.urlopen", return_value=Response(b"{}", "application/octet-stream")):
            with self.assertRaises(ProviderAcquisitionError) as caught:
                fetch(METADATA_URL, diagnostics=new_diagnostics(),
                      endpoint_category="scryfall_bulk_metadata", stage="metadata_response")
        self.assertEqual(caught.exception.diagnostics["response_content_type"],
                         "application/octet-stream")

    def test_invalid_metadata_is_sanitized_and_retains_no_payload(self):
        with tempfile.TemporaryDirectory() as temp, patch("urllib.request.urlopen", return_value=Response(b"{}")):
            root=Path(temp); (root/"canonical").mkdir(); (root/"canonical/state.json").write_bytes(self.canonical_bytes)
            diagnostic = new_diagnostics()
            with self.assertRaises(ProviderAcquisitionError) as caught:
                run(root, payload_path=None, retrieved_at=NOW, persist=False, run_id="dry", diagnostics=diagnostic)
        report = caught.exception.diagnostics
        self.assertEqual(report["failing_stage"], "metadata_validation")
        self.assertTrue(report["metadata_fetched"])
        self.assertFalse(report["download_uri_obtained"])
        self.assertFalse(report["payload_bytes_retained"])
        serialized = json.dumps(report)
        self.assertNotIn("https://", serialized)
        self.assertNotIn("provider body", serialized)

    def test_workflow_reports_original_exit_and_always_uploads_artifact(self):
        workflow = (ROOT/".github/workflows/market-acquisition.yml").read_text()
        self.assertIn("STATUS=$?", workflow)
        self.assertIn('exit "$STATUS"', workflow)
        self.assertIn("cat market-acquisition-dry-run.json", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertLess(workflow.index("Upload acquisition diagnostics"),
                        workflow.index("Verify dry run and optionally persist"))

    def test_failed_cli_dry_run_writes_no_market_or_canonical_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"canonical").mkdir(); (root/"canonical/state.json").write_bytes(self.canonical_bytes)
            before=(root/"canonical/state.json").read_bytes()
            with patch("urllib.request.urlopen", return_value=Response(b"{}")):
                diagnostic = new_diagnostics()
                with self.assertRaises(ProviderAcquisitionError):
                    run(root, payload_path=None, retrieved_at=NOW, persist=False,
                        run_id="failed", diagnostics=diagnostic)
            self.assertEqual((root/"canonical/state.json").read_bytes(), before)
            self.assertFalse((root/"market").exists())

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
