import gzip
from email.message import Message
from io import BytesIO
from pathlib import Path
import socket
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request

from scripts.retain_pilot_printings import (
    AcquisitionTransportError, CHECKSUM_HEADERS, MTGJSONDownloader, SOURCE_HEADERS,
    SafeRedirectHandler, USER_AGENT,
)


class Response(BytesIO):
    def __init__(self, body, url, content_type="application/octet-stream", status=200):
        super().__init__(body); self.url = url; self.status = status
        self.headers = Message(); self.headers["Content-Type"] = content_type
    def geturl(self): return self.url
    def getcode(self): return self.status
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class QueueOpener:
    def __init__(self, outcomes): self.outcomes = list(outcomes); self.requests = []
    def open(self, request, timeout):
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception): raise outcome
        return outcome


class Phase135BTransportTests(unittest.TestCase):
    def setUp(self): self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()

    def downloader(self, outcomes):
        queue = QueueOpener(outcomes)
        return MTGJSONDownloader(opener_factory=lambda redirect: queue), queue

    def test_headers_checksum_and_exact_request_counts(self):
        source = gzip.compress(b'{}')
        import hashlib
        sidecar = f"{hashlib.sha256(source).hexdigest()}  AllPrintings.json.gz\n".encode()
        downloader, queue = self.downloader([
            Response(sidecar, "https://mtgjson.com/api/v5/AllPrintings.json.gz.sha256", "text/plain"),
            Response(source, "https://mtgjson.com/api/v5/AllPrintings.json.gz", "application/gzip")])
        result = downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / "source.gz")
        self.assertEqual((downloader.source_requests, downloader.checksum_requests), (1, 1))
        self.assertEqual(len(queue.requests), 2)
        self.assertEqual(queue.requests[0].get_header("User-agent"), USER_AGENT)
        self.assertEqual(queue.requests[1].get_header("User-agent"), USER_AGENT)
        self.assertEqual(queue.requests[0].get_header("Accept"), CHECKSUM_HEADERS["Accept"])
        self.assertEqual(queue.requests[1].get_header("Accept"), SOURCE_HEADERS["Accept"])
        self.assertEqual(queue.requests[1].get_header("Accept-encoding"), "identity")
        self.assertEqual(result["expected_sha256"], result["source_sha256"])

    def test_malformed_unexpected_filename_and_checksum_mismatch_fail_closed(self):
        for value in (b"bad\n", b"0" * 64 + b"  Other.json.gz\n"):
            downloader, _ = self.downloader([Response(value, "https://mtgjson.com/x")])
            with self.assertRaisesRegex(AcquisitionTransportError, "checksum"):
                downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / "bad.gz")
        sidecar = b"0" * 64 + b"  AllPrintings.json.gz\n"
        downloader, _ = self.downloader([Response(sidecar, "https://mtgjson.com/x"),
                                          Response(gzip.compress(b"x"), "https://mtgjson.com/y")])
        with self.assertRaisesRegex(AcquisitionTransportError, "did not match"):
            downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / "mismatch.gz")

    def test_redirect_policy_and_final_url_validation(self):
        handler = SafeRedirectHandler(frozenset({"mtgjson.com"}))
        request = Request("https://mtgjson.com/source")
        redirected = handler.redirect_request(request, None, 302, "Found", {}, "https://mtgjson.com/final")
        self.assertEqual(redirected.full_url, "https://mtgjson.com/final")
        for unsafe in ("http://mtgjson.com/final", "https://evil.example/final"):
            with self.assertRaises(AcquisitionTransportError):
                handler.redirect_request(request, None, 302, "Found", {}, unsafe)
        downloader, _ = self.downloader([Response(b"x", "https://evil.example/final")])
        with self.assertRaisesRegex(AcquisitionTransportError, "approved HTTPS"):
            downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / "final.gz")

    def test_403_timeout_and_transport_are_structured(self):
        cases = [
            (HTTPError("https://mtgjson.com/x", 403, "Forbidden", {}, None), "http_403"),
            (URLError(socket.timeout()), "timeout"),
            (URLError("network down"), "transport_error"),
        ]
        for outcome, expected in cases:
            downloader, _ = self.downloader([outcome])
            with self.assertRaises(AcquisitionTransportError) as caught:
                downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / f"{expected}.gz")
            self.assertEqual(caught.exception.failure_type, expected)
            self.assertEqual(downloader.source_requests, 0)

    def test_diagnostic_metadata_contains_no_corpus(self):
        downloader, _ = self.downloader([HTTPError("https://mtgjson.com/x", 403, "Forbidden", {}, None)])
        with self.assertRaises(AcquisitionTransportError):
            downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", self.root / "none.gz")
        self.assertNotIn("corpus", downloader.diagnostic)
        self.assertNotIn("body", downloader.diagnostic)


if __name__ == "__main__": unittest.main()
