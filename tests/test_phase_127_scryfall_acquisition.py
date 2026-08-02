"""Phase 127G streaming gzip JSONL transport and bounded dry-run tests."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from email.message import Message
from unittest.mock import patch

from market import MarketValidationError
from market.scryfall import ProviderAcquisitionError, canonical_json, sha256_bytes
from scripts.scryfall_market_acquisition import (_parse_jsonl_stream,
    _select_bulk_descriptor, download_jsonl, new_diagnostics, parse_bulk_metadata, run)

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


class Response(io.BytesIO):
    def __init__(self, payload, content_type="application/x-ndjson", encoding=None, length=None):
        super().__init__(payload); self.status = 200; self.headers = Message()
        self.headers["Content-Type"] = content_type
        if encoding: self.headers["Content-Encoding"] = encoding
        if length is not None: self.headers["Content-Length"] = str(length)
    def __enter__(self): return self
    def __exit__(self, *args): self.close(); return False
    def getcode(self): return self.status


class Phase127GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = (ROOT/"data/canonical/state.json").read_bytes()
        state = json.loads(cls.canonical)
        cls.printing_id, printing = next(iter(state["printing"].items()))
        values = printing["values"]
        cls.record = {"object":"card", "id":values["identifiers"]["scryfallId"],
            "set":"mb2", "collector_number":values["collector_number"], "lang":"en",
            "finishes":[values["finish_ids"][0]],
            "prices":{"usd":"1.23", "usd_foil":None, "usd_etched":None}}

    def descriptor(self, **changes):
        value = {"compressed_size":123, "description":"Default cards", "id":"safe-id",
            "jsonl_download_uri":"https://data.scryfall.io/default-cards/test.jsonl",
            "name":"Default Cards", "object":"bulk_data", "type":"default_cards",
            "updated_at":"2026-08-01T10:00:00Z", "uri":"https://api.scryfall.com/bulk-data/x"}
        value.update(changes); return value

    def lines(self, *records):
        return b"".join(json.dumps(x, sort_keys=True).encode()+b"\n" for x in records)

    def parse(self, payload, **kwargs):
        diagnostics = new_diagnostics()
        result = _parse_jsonl_stream(io.BytesIO(payload), diagnostics, **kwargs)
        return result, diagnostics

    def root(self, temp):
        root=Path(temp); (root/"canonical").mkdir(); (root/"canonical/state.json").write_bytes(self.canonical)
        return root

    def test_exact_real_descriptor_key_shape_and_jsonl_selection(self):
        descriptor=self.descriptor(); diagnostic=new_diagnostics()
        transport=parse_bulk_metadata(canonical_json(descriptor),diagnostic)
        self.assertEqual(sorted(descriptor), ["compressed_size","description","id",
            "jsonl_download_uri","name","object","type","updated_at","uri"])
        self.assertEqual(transport.field,"jsonl_download_uri"); self.assertEqual(transport.format,"jsonl")
        self.assertFalse(diagnostic["download_uri_present"])
        self.assertEqual(diagnostic["transport_field_extraction_reason"],"jsonl_transport_selected")
        self.assertFalse(diagnostic["legacy_compatibility_used"])

    def test_descriptor_preserved_and_diagnostics_safe(self):
        descriptor=self.descriptor(); diagnostic=new_diagnostics()
        selection=_select_bulk_descriptor(descriptor,diagnostic)
        self.assertIs(selection.provider,descriptor); self.assertIsNot(selection.provider,selection.diagnostic_projection)
        serialized=json.dumps({"d":diagnostic,"p":selection.diagnostic_projection})
        self.assertNotIn(descriptor["jsonl_download_uri"],serialized)
        self.assertNotIn(descriptor["uri"],serialized)
        self.assertTrue(diagnostic["descriptor_selection_preserved_original_field"])
        self.assertTrue(diagnostic["transport_and_diagnostic_objects_distinct"])

    def test_transport_field_boundaries(self):
        cases=(({},"supported_transport_field_absent"),
            ({"jsonl_download_uri":17},"selected_transport_not_string"),
            ({"jsonl_download_uri":"  "},"selected_transport_blank"),
            ({"download_uri":"https://data.scryfall.io/other.json"},"conflicting_transport_fields"))
        for changes, reason in cases:
            descriptor=self.descriptor(**changes)
            if changes == {}: descriptor.pop("jsonl_download_uri")
            diagnostic=new_diagnostics()
            with self.subTest(reason=reason), self.assertRaises(ProviderAcquisitionError):
                parse_bulk_metadata(canonical_json(descriptor),diagnostic)
            self.assertEqual(diagnostic["transport_field_extraction_reason"],reason)
            self.assertNotIn("https://",json.dumps(diagnostic))

    def test_equal_dual_field_is_unambiguous_and_legacy_fixture_supported(self):
        uri="https://data.scryfall.io/default-cards/test.jsonl"
        transport=parse_bulk_metadata(canonical_json(self.descriptor(download_uri=uri)),new_diagnostics())
        self.assertEqual(transport.field,"jsonl_download_uri")
        legacy=self.descriptor(download_uri="https://data.scryfall.io/default-cards/test.json")
        legacy.pop("jsonl_download_uri"); diagnostic=new_diagnostics()
        self.assertEqual(parse_bulk_metadata(canonical_json(legacy),diagnostic).format,"json-array")
        self.assertTrue(diagnostic["legacy_compatibility_used"])

    def test_uri_security_policy(self):
        invalid=("http://data.scryfall.io/a", "https://api.scryfall.com/a",
            "https://scryfall.io.evil.test/a", "https://127.0.0.1/a",
            "https://localhost/a", "https://u:p@data.scryfall.io/a",
            "https://data.scryfall.io:444/a", "https://data.scryfall.io", "https://data.scryfall.io/a#x")
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(ProviderAcquisitionError):
                parse_bulk_metadata(canonical_json(self.descriptor(jsonl_download_uri=uri)),new_diagnostics())

    def test_valid_jsonl_blank_lines_and_deterministic_digest(self):
        payload=b"\n"+self.lines(self.record)+b"  \n"
        parsed,d=self.parse(payload)
        self.assertEqual(parsed.records,(self.record,)); self.assertEqual(parsed.source_digest,hashlib.sha256(payload).hexdigest())
        self.assertEqual(d["total_lines"],3); self.assertEqual(d["records_decoded"],1)
        self.assertEqual(d["selected_mb2_record_count"],1)

    def test_malformed_nonobject_invalid_utf8_and_shape_rejected(self):
        cases=(b'{"bad"\n', b'[]\n', b'"scalar"\n', b'\xff\n', b'{"id":"x"}\n')
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ProviderAcquisitionError): self.parse(payload)

    def test_duplicate_provider_identity_rejected(self):
        with self.assertRaises(ProviderAcquisitionError) as caught:
            self.parse(self.lines(self.record,self.record))
        self.assertEqual(caught.exception.diagnostics["duplicate_record_count"],1)

    def test_gzip_supported_and_decompression_failure(self):
        payload=self.lines(self.record); compressed=gzip.compress(payload)
        parsed,d=self.parse(compressed,compression_mode="gzip")
        self.assertEqual(parsed.records,(self.record,)); self.assertEqual(d["compression_mode"],"gzip")
        self.assertTrue(d["gzip_framing_valid"]); self.assertTrue(d["stream_completed"])
        self.assertEqual(d["compressed_bytes_read"],len(compressed))
        self.assertEqual(d["decompressed_bytes_processed"],len(payload))
        with self.assertRaises(ProviderAcquisitionError): self.parse(b"not gzip",compression_mode="gzip")
        with self.assertRaises(ProviderAcquisitionError): self.parse(b"\x1f\x8b broken",compression_mode="gzip")
        with self.assertRaises(ProviderAcquisitionError): self.parse(compressed[:-4],compression_mode="gzip")
        with self.assertRaises(ProviderAcquisitionError): self.parse(payload,content_encoding="br")

    def test_real_phase_127f_regression_application_gzip_decodes(self):
        raw=self.lines(self.record); compressed=gzip.compress(raw,mtime=0)
        diagnostics=new_diagnostics()
        with patch("urllib.request.urlopen",return_value=Response(
                compressed,"application/gzip",length=len(compressed))) as opened:
            parsed=download_jsonl("https://data.scryfall.io/redacted",diagnostics)
        self.assertEqual(opened.call_count,1)
        self.assertEqual(parsed.records,(self.record,))
        self.assertEqual(parsed.source_digest,hashlib.sha256(compressed).hexdigest())
        self.assertEqual(diagnostics["response_media_type"],"application/gzip")
        self.assertEqual(diagnostics["compression_mode"],"gzip")
        self.assertEqual(diagnostics["records_decoded"],1)

    def test_gzip_content_length_utf8_json_and_nonobject_fail_closed(self):
        cases=(b"\xff\n",b'{"bad"\n',b'[]\n')
        for raw in cases:
            compressed=gzip.compress(raw,mtime=0)
            with self.subTest(raw=raw), patch("urllib.request.urlopen",return_value=Response(
                    compressed,"application/gzip")):
                with self.assertRaises(ProviderAcquisitionError):
                    download_jsonl("https://data.scryfall.io/redacted",new_diagnostics())
        compressed=gzip.compress(self.lines(self.record),mtime=0)
        with patch("urllib.request.urlopen",return_value=Response(
                compressed,"application/gzip",length=len(compressed)+1)):
            with self.assertRaises(ProviderAcquisitionError):
                download_jsonl("https://data.scryfall.io/redacted",new_diagnostics())

    def test_content_type_and_exactly_one_download(self):
        payload=self.lines(self.record)
        for media in ("application/x-ndjson","application/jsonl","application/octet-stream","application/json"):
            with self.subTest(media=media), patch("urllib.request.urlopen",return_value=Response(payload,media)) as opened:
                self.assertEqual(download_jsonl("https://data.scryfall.io/a",new_diagnostics()).source_record_count,1)
                self.assertEqual(opened.call_count,1)
        with patch("urllib.request.urlopen",return_value=Response(payload,"text/html")):
            with self.assertRaises(ProviderAcquisitionError): download_jsonl("https://data.scryfall.io/a",new_diagnostics())
        with patch("urllib.request.urlopen",return_value=Response(payload,length=len(payload)+1)):
            with self.assertRaises(ProviderAcquisitionError): download_jsonl("https://data.scryfall.io/a",new_diagnostics())

    def test_bounded_mb2_only_selection_large_stream(self):
        other=dict(self.record); other["set"]="neo"
        payload=io.BytesIO()
        for number in range(20000):
            item=dict(other); item["id"]=f"other-{number}"; payload.write(self.lines(item))
        payload.write(self.lines(self.record))
        parsed,d=self.parse(payload.getvalue())
        self.assertEqual(len(parsed.records),1); self.assertEqual(parsed.source_record_count,20001)
        self.assertEqual(d["selected_mb2_record_count"],1)

    def test_large_gzip_stream_is_incremental_and_retains_only_mb2(self):
        other=dict(self.record); other["set"]="neo"
        raw=b"".join(self.lines(dict(other,id=f"other-{number}")) for number in range(25000))
        raw+=self.lines(self.record); compressed=gzip.compress(raw,mtime=0)
        class BoundedResponse(Response):
            def read(self,size=-1):
                if size < 0 or size > 131072: raise AssertionError("unbounded compressed read")
                return super().read(size)
        diagnostics=new_diagnostics()
        with patch("urllib.request.urlopen",return_value=BoundedResponse(
                compressed,"application/gzip")):
            parsed=download_jsonl("https://data.scryfall.io/redacted",diagnostics)
        self.assertEqual(parsed.records,(self.record,))
        self.assertEqual(parsed.source_record_count,25001)
        self.assertEqual(diagnostics["decompressed_bytes_processed"],len(raw))

    def test_complete_dry_run_census_known_missing_no_writes_and_digests(self):
        missing=dict(self.record); missing["id"]="missing-id"; missing["collector_number"]="unmatched"
        missing["prices"]={"usd":None,"usd_foil":None,"usd_etched":None}
        payload=self.lines(self.record,missing)
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp); source=root/"source.jsonl"; source.write_bytes(payload)
            before=(root/"canonical/state.json").read_bytes()
            report=run(root,payload_path=source,retrieved_at=NOW,persist=False,run_id="dry")
            again=run(root,payload_path=source,retrieved_at=NOW,persist=False,run_id="again")
            self.assertEqual(report["source_record_count"],2); self.assertEqual(report["mb2_record_count"],2)
            self.assertEqual(report["mapping_counts"],{"matched":1,"unmatched":1,"ambiguous":0,"rejected":0})
            self.assertEqual(report["known_price_observation_count"],1)
            self.assertEqual(report["missing_price_observation_count"],0)
            self.assertEqual(report["source_sha256"],sha256_bytes(payload))
            self.assertEqual(report["normalized_sha256"],again["normalized_sha256"])
            self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])
            self.assertFalse(report["persisted"]); self.assertEqual(before,(root/"canonical/state.json").read_bytes())
            self.assertFalse((root/"market").exists())

    def test_explicit_missing_price_observation(self):
        missing=json.loads(json.dumps(self.record)); missing["prices"]["usd"]=None
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp); source=root/"source.jsonl"; source.write_bytes(self.lines(missing))
            report=run(root,payload_path=source,retrieved_at=NOW,persist=False,run_id="dry")
        self.assertEqual(report["missing_price_observation_count"],1)

    def test_persist_true_is_prohibited(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            with self.assertRaisesRegex(MarketValidationError,"prohibits persist=true"):
                run(root,payload_path=None,retrieved_at=NOW,persist=True,run_id="no")

    def test_workflow_is_dry_run_only_and_retains_bounded_projection(self):
        workflow=(ROOT/".github/workflows/market-acquisition.yml").read_text()
        self.assertIn("Acquisition is nonpersistent",workflow)
        self.assertIn("market-acquisition-source-mb2.json",workflow)
        self.assertNotIn(" --persist",workflow)

    def test_workflow_installs_declared_dependencies_before_execution(self):
        workflow=(ROOT/".github/workflows/market-acquisition.yml").read_text()
        install="python -m pip install -r requirements.txt"
        self.assertIn(install,workflow)
        self.assertLess(workflow.index(install),workflow.index(
            "python scripts/scryfall_market_acquisition.py"))

    def test_acquisition_remains_nonpersistent_after_authorized_import(self):
        """Phase 127 isolation is compatible with later Phase 128 persistence."""
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp); source=root/"source.jsonl"; source.write_bytes(self.lines(self.record))
            observations=root/"market/observations"
            sentinel=observations/"existing-authorized-observation.json"
            sentinel.parent.mkdir(parents=True); sentinel.write_bytes(b"authorized-later-phase\n")
            canonical_before=(root/"canonical/state.json").read_bytes()
            observation_before={path.relative_to(observations):path.read_bytes()
                                for path in observations.rglob("*") if path.is_file()}

            report=run(root,payload_path=source,retrieved_at=NOW,persist=False,run_id="dry")

            self.assertFalse(report["persisted"])
            self.assertFalse(report["canonical_write"])
            self.assertFalse(report["promotion_performed"])
            self.assertEqual(canonical_before,(root/"canonical/state.json").read_bytes())
            self.assertEqual(observation_before,{path.relative_to(observations):path.read_bytes()
                                                for path in observations.rglob("*") if path.is_file()})

        production=tuple((ROOT/"data/market/observations").glob("*/*/*/*.json"))
        import_report=json.loads((ROOT/"data/market/imports/scryfall-mb2-30754638264-1/"
                                  "import-report.json").read_text())
        self.assertEqual(len(production),478)
        self.assertTrue(import_report["observations_persisted"])
        self.assertFalse(import_report["canonical_write"])
        self.assertFalse(import_report["promotion_performed"])


if __name__ == "__main__": unittest.main()
