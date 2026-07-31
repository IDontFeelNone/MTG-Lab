import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mtglab.__main__ import main
from official_datasets import AcquisitionError, DatasetDefinition, OfficialDatasetAcquisition


FIXTURE = Path(__file__).parent / "fixtures" / "mtgjson" / "AllPrintings.json"
NOW = lambda: datetime(2026, 7, 31, tzinfo=timezone.utc)


class Response:
    def __init__(self, payload, status=200, fail_after=None):
        self.payload, self.status, self.position, self.fail_after = payload, status, 0, fail_after

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size=-1):
        if self.fail_after is not None and self.position >= self.fail_after:
            raise OSError("connection lost")
        if size < 0: size = len(self.payload)
        if self.fail_after is not None:
            size = min(size, self.fail_after - self.position)
        value = self.payload[self.position:self.position + size]
        self.position += len(value)
        return value


class OfficialDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "data"
        self.payload = FIXTURE.read_bytes()

    def tearDown(self): self.temporary.cleanup()

    def engine(self, opener):
        return OfficialDatasetAcquisition(self.root, opener=opener, now=NOW)

    def test_successful_download_registers_deterministically_and_duplicate_is_safe(self):
        calls = []
        def opener(request):
            calls.append(request)
            return Response(self.payload)
        engine = self.engine(opener)
        result = engine.download("mtgjson")
        self.assertTrue(result["valid"])
        self.assertFalse(result["canonical_write"])
        self.assertEqual(Path(result["path"]).read_bytes(), self.payload)
        self.assertEqual(engine.download("mtgjson")["status"], "already_downloaded")
        self.assertEqual(len(calls), 1)
        self.assertTrue(engine.verify("mtgjson")["valid"])

    def test_interrupted_download_is_retained_and_resumed(self):
        split = 40
        responses = [Response(self.payload, fail_after=split), Response(self.payload[split:], status=206)]
        requests = []
        def opener(request):
            requests.append(request)
            return responses.pop(0)
        engine = self.engine(opener)
        with self.assertRaisesRegex(AcquisitionError, "interrupted"):
            engine.download("mtgjson")
        self.assertEqual(engine.status("mtgjson")["status"], "partial")
        result = engine.download("mtgjson")
        self.assertTrue(result["resumed"])
        self.assertEqual(requests[1].get_header("Range"), f"bytes={split}-")
        self.assertEqual(Path(result["path"]).read_bytes(), self.payload)

    def test_checksum_verification_and_corruption_fail_closed(self):
        digest = hashlib.sha256(self.payload).hexdigest()
        definition = DatasetDefinition("mtgjson", "mtgjson", "https://example/data", "AllPrintings.json",
                                       "none", "https://example/checksum",
                                       "reference-datasets/mtgjson/all-printings", "5.x")
        responses = [Response(self.payload), Response((digest + "  AllPrintings.json\n").encode())]
        with patch("official_datasets.acquisition.get_definition", return_value=definition):
            result = self.engine(lambda request: responses.pop(0)).download("mtgjson")
        self.assertTrue(result["checksum_verified"])
        Path(result["path"]).write_bytes(b"corrupt")
        self.assertFalse(self.engine(lambda request: None).verify("mtgjson")["valid"])

    def test_checksum_mismatch_and_invalid_json_are_not_registered(self):
        definition = DatasetDefinition("mtgjson", "mtgjson", "https://example/data", "AllPrintings.json",
                                       "none", "https://example/checksum",
                                       "reference-datasets/mtgjson/all-printings", "5.x")
        responses = [Response(self.payload), Response(("0" * 64).encode())]
        with patch("official_datasets.acquisition.get_definition", return_value=definition):
            with self.assertRaisesRegex(AcquisitionError, "official checksum"):
                self.engine(lambda request: responses.pop(0)).download("mtgjson")
        other = Path(self.temporary.name) / "other"
        with self.assertRaisesRegex(AcquisitionError, "validation failed"):
            OfficialDatasetAcquisition(other, opener=lambda request: Response(b"not-json"), now=NOW).download("mtgjson")

    def test_storage_and_cli_json_behavior(self):
        expected = self.root / "local/reference-datasets/mtgjson/all-printings/AllPrintings.json"
        engine = self.engine(lambda request: Response(self.payload))
        self.assertEqual(Path(engine.download("mtgjson")["path"]), expected)
        for arguments in (("list",), ("status", "mtgjson"), ("verify", "mtgjson")):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--data-root", str(self.root), "dataset", *arguments,
                                       "--format", "json"]), 0)
            self.assertIn("canonical_write", json.loads(output.getvalue()))


if __name__ == "__main__": unittest.main()
