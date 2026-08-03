import gzip
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.retain_pilot_printings import (
    AcquisitionTransportError,
    MAX_CHECKSUM_SIDECAR_BYTES,
    MTGJSONDownloader,
    parse_checksum_sidecar,
)
from tests.test_phase_135b_mtgjson_transport import QueueOpener, Response


DIGEST = "0123456789abcdef" * 4


class Phase135CChecksumParserTests(unittest.TestCase):
    def parse(self, value: bytes):
        return parse_checksum_sidecar(value)

    def assert_reason(self, value: bytes, reason: str):
        with self.assertRaises(AcquisitionTransportError) as caught:
            self.parse(value)
        self.assertEqual(caught.exception.failure_type, "malformed_checksum")
        self.assertEqual(caught.exception.metadata["checksum_failure_reason"], reason)
        return caught.exception.metadata

    def test_exact_observed_mtgjson_digest_only_and_trailing_newline(self):
        # The hosted response that exposed Phase 135B is one bare digest.
        for value in (DIGEST.encode(), f"{DIGEST}\n".encode()):
            digest, metadata = self.parse(value)
            self.assertEqual(digest, DIGEST)
            self.assertEqual(metadata["checksum_syntax"], "digest_only")

    def test_standard_gnu_text_binary_and_bsd_formats(self):
        cases = {
            f"{DIGEST}  AllPrintings.json.gz": "gnu_text",
            f"{DIGEST} *AllPrintings.json.gz": "gnu_binary",
            f"SHA256 (AllPrintings.json.gz) = {DIGEST}": "bsd",
        }
        for value, syntax in cases.items():
            digest, metadata = self.parse(value.encode())
            self.assertEqual(digest, DIGEST)
            self.assertEqual(metadata["checksum_syntax"], syntax)
            self.assertEqual(metadata["checksum_filename_candidate"], "AllPrintings.json.gz")

    def test_uppercase_digest_is_normalized(self):
        self.assertEqual(self.parse(DIGEST.upper().encode())[0], DIGEST)

    def test_alternate_traversal_absolute_url_and_relative_filename_rejected(self):
        names = ("Other.json.gz", "../AllPrintings.json.gz", "/AllPrintings.json.gz",
                 "https://mtgjson.com/AllPrintings.json.gz", "./AllPrintings.json.gz",
                 "user:pass@AllPrintings.json.gz")
        for name in names:
            metadata = self.assert_reason(f"{DIGEST}  {name}".encode(), "unsafe_or_unexpected_filename")
            self.assertEqual(metadata["checksum_filename_candidate"], name)

    def test_multiple_malformed_extra_line_binary_nul_and_oversized_rejected(self):
        cases = (
            (f"{DIGEST} {DIGEST}".encode(), "multiple_digests"),
            (b"not-a-digest", "malformed_digest"),
            (f"{DIGEST}\nextra".encode(), "extra_line"),
            (f"{DIGEST}\n\n".encode(), "extra_line"),
            (DIGEST.encode() + b"\x00", "nul_byte"),
            (b"\xff", "invalid_utf8"),
            (DIGEST.encode() + b"\t", "control_character"),
            (b"x" * (MAX_CHECKSUM_SIDECAR_BYTES + 1), "sidecar_too_large"),
        )
        for value, reason in cases:
            self.assert_reason(value, reason)

    def test_failure_diagnostics_are_bounded_and_corpus_free_before_source_request(self):
        sidecar = b"x" * (MAX_CHECKSUM_SIDECAR_BYTES + 1)
        queue = QueueOpener([Response(sidecar, "https://mtgjson.com/checksum")])
        downloader = MTGJSONDownloader(opener_factory=lambda redirect: queue)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AcquisitionTransportError):
                downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", Path(directory) / "source.gz")
        self.assertEqual((downloader.checksum_requests, downloader.source_requests), (1, 0))
        self.assertLessEqual(len(downloader.diagnostic["checksum_sidecar_text_escaped"]), 270)
        self.assertNotIn("body", downloader.diagnostic)
        self.assertEqual(downloader.diagnostic["checksum_failure_reason"], "sidecar_too_large")

    def test_success_requests_source_once_and_still_verifies_source_digest(self):
        source = gzip.compress(b"bounded test fixture")
        digest = hashlib.sha256(source).hexdigest()
        for sidecar in (digest.encode(), f"{digest}  AllPrintings.json.gz\n".encode()):
            queue = QueueOpener([
                Response(sidecar, "https://mtgjson.com/checksum"),
                Response(source, "https://mtgjson.com/source", "application/gzip"),
            ])
            downloader = MTGJSONDownloader(opener_factory=lambda redirect: queue)
            with tempfile.TemporaryDirectory() as directory:
                result = downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz",
                                    Path(directory) / "source.gz")
            self.assertEqual((downloader.checksum_requests, downloader.source_requests), (1, 1))
            self.assertEqual(result["source_sha256"], digest)

    def test_checksum_mismatch_remains_fatal(self):
        source = gzip.compress(b"fixture")
        queue = QueueOpener([
            Response(("0" * 64).encode(), "https://mtgjson.com/checksum"),
            Response(source, "https://mtgjson.com/source", "application/gzip"),
        ])
        downloader = MTGJSONDownloader(opener_factory=lambda redirect: queue)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(AcquisitionTransportError, "did not match"):
                downloader("https://mtgjson.com/api/v5/AllPrintings.json.gz", Path(directory) / "source.gz")


if __name__ == "__main__":
    unittest.main()
