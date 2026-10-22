"""Observations from actual publication logs remain separate from admission."""
import hashlib
import unittest

from publication_validation_regression import nested_validation_diagnostics


class PublicationValidationDiagnosticsTests(unittest.TestCase):
    def result(self, raw, count=2, **changes):
        return {"exit_status": 0, "tests": count,
                "log_sha256": hashlib.sha256(raw).hexdigest(), **changes}

    def log(self, summary="Ran 2 tests in 12.345s\n\nOK (skipped=1)\n"):
        return ("test_real (test_real.Validation.test_real) ... ok\n"
                "test_source (test_source.Validation.test_source) ... skipped 'source absent'\n"
                "\n----------------------------------------------------------------------\n" + summary).encode()

    def test_actual_duration_skip_count_and_hash_from_unchanged_log(self):
        raw = self.log()
        original = raw
        observed = nested_validation_diagnostics(raw, self.result(raw))
        self.assertEqual(observed, {"tests": 2, "elapsed_seconds": 12.345, "skipped": 1,
                                   "log_sha256": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(raw, original)

    def test_literal_success_without_skips_and_singular_test(self):
        raw = b"test_real (test_real.Validation.test_real) ... ok\n\nRan 1 test in 0.000s\n\nOK\n"
        observed = nested_validation_diagnostics(raw, self.result(raw, count=1))
        self.assertEqual((observed["tests"], observed["skipped"], observed["elapsed_seconds"]), (1, 0, 0.0))

    def test_crlf_log_is_parsed_but_original_bytes_are_hashed(self):
        raw = self.log().replace(b"\n", b"\r\n")
        observed = nested_validation_diagnostics(raw, self.result(raw))
        self.assertEqual(observed["skipped"], 1)
        self.assertEqual(observed["log_sha256"], hashlib.sha256(raw).hexdigest())

    def test_result_count_hash_and_exit_status_mismatches_are_rejected(self):
        raw = self.log()
        for change in ({"tests": 3}, {"tests": True}, {"tests": 2.0},
                       {"log_sha256": "0" * 64}, {"exit_status": 1}, {"exit_status": False}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                nested_validation_diagnostics(raw, self.result(raw, **change))

    def test_missing_failed_incomplete_or_ambiguous_summary_has_no_inferred_values(self):
        for summary in ("", "Ran 2 tests in 1.2s\n", "Ran 2 tests in 1.2s\n\nFAILED (failures=1)\n",
                        "Ran 2 tests in 1.2s\n\nOK (skipped=1)\ntrailing output\n",
                        "Ran 2 tests in 1.2s\n\nOK (skipped=1)\nRan 2 tests in 1.2s\n\nOK (skipped=1)\n",
                        "Ran 2 tests in unknowns\n\nOK (skipped=1)\n",
                        "Ran 0 tests in 0.000s\n\nOK\n",
                        "Ran 2 tests in " + "9" * 400 + "s\n\nOK (skipped=1)\n"):
            raw = self.log(summary)
            with self.subTest(summary=summary[:65]), self.assertRaises(ValueError):
                nested_validation_diagnostics(raw, self.result(raw))

    def test_skip_summary_must_match_actual_verbose_skip_entries(self):
        for summary in ("Ran 2 tests in 1.2s\n\nOK\n", "Ran 2 tests in 1.2s\n\nOK (skipped=2)\n"):
            raw = self.log(summary)
            with self.subTest(summary=summary), self.assertRaises(ValueError):
                nested_validation_diagnostics(raw, self.result(raw))

    def test_missing_or_nonbyte_content_is_rejected(self):
        for raw in (None, "Ran 2 tests in 1.2s\n\nOK\n", bytearray(self.log())):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(ValueError):
                nested_validation_diagnostics(raw, {})
        raw = self.log()
        with self.assertRaises(ValueError):
            nested_validation_diagnostics(raw, {})


if __name__ == "__main__":
    unittest.main()
