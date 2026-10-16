"""Bounded first-party metadata intake with explicit local transport doubles."""
import hashlib
import json
import socket
import unittest
from unittest.mock import patch

from acquisition import AcquisitionError, ProviderRequest, ProviderResponse, RawSnapshotStore
from gameplay_rules.source_evidence.intake import (
    MetadataTransportResponse, UrllibMetadataTransport, WizardsRulesMetadataProvider,
)
from gameplay_rules_source_fixture import (
    ARTIFACT_BODY, ARTIFACT_URL, EFFECTIVE_DATE, HTML_BODY, LocalMetadataTransport,
    OBSERVED_AT, PAGE_URL, RULES_VERSION, response,
)


class GameplayRulesSourceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.transport = LocalMetadataTransport({PAGE_URL: response()})
        self.provider = WizardsRulesMetadataProvider(self.transport)

    def retrieve(self, *, provider=None, url=PAGE_URL, observed_at=OBSERVED_AT):
        provider = provider or self.provider
        request = provider.build_request("rules-source", {"url": url, "observed_at": observed_at})
        result = provider.retrieve(request)
        provider.validate_response(result)
        return result

    def custom(self, value, *, url=PAGE_URL, **policy):
        transport = LocalMetadataTransport({url: value})
        return self.retrieve(provider=WizardsRulesMetadataProvider(transport, **policy), url=url), transport

    def test_page_observation_binds_exact_page_bytes_not_designated_rules_artifact(self):
        result = self.retrieve()
        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.payload, b"")
        self.assertFalse(result.metadata["body_retained"])
        self.assertEqual(result.metadata["artifact_sha256"], "sha256:" + hashlib.sha256(HTML_BODY).hexdigest())
        self.assertEqual(result.metadata["byte_length"], len(HTML_BODY))
        self.assertNotEqual(result.metadata["artifact_sha256"], "sha256:" + hashlib.sha256(ARTIFACT_BODY).hexdigest())
        self.assertEqual([row["url"] for row in result.metadata["designated_links"]], [ARTIFACT_URL])
        self.assertEqual([call["url"] for call in self.transport.calls], [PAGE_URL])

    def test_only_explicit_structured_effective_date_and_version_are_metadata(self):
        result = self.retrieve()
        self.assertEqual(result.metadata["metadata_fields"],
                         {"effective_date": EFFECTIVE_DATE, "rules_version": RULES_VERSION})
        self.assertEqual(result.metadata["observed_at"], OBSERVED_AT)
        self.assertFalse(result.provenance["release_selected"])
        self.assertFalse(result.provenance["automatic_document_following"])

    def test_unlabeled_prose_or_filename_date_is_not_a_rules_version_claim(self):
        body = b"Original fictional page published 2032-02-09; current newest rules maybe version 9."
        result, _ = self.custom(response(body=body))
        self.assertEqual(result.metadata["metadata_fields"], {})
        self.assertEqual(result.metadata["designated_links"], [])

    def test_direct_artifact_hash_is_distinct_from_page_hash(self):
        result, _ = self.custom(response(ARTIFACT_URL, content_type="text/plain", body=ARTIFACT_BODY), url=ARTIFACT_URL)
        self.assertEqual(result.metadata["artifact_sha256"], "sha256:" + hashlib.sha256(ARTIFACT_BODY).hexdigest())
        self.assertEqual(result.metadata["metadata_fields"], {})
        self.assertEqual(result.payload, b"")

    def test_pdf_is_hashed_without_parsing_or_retaining_corpus(self):
        body = b"%PDF-1.7\nOriginal fictional local binary test payload\n"
        result, _ = self.custom(response(ARTIFACT_URL, content_type="application/pdf", body=body), url=ARTIFACT_URL)
        self.assertEqual(result.metadata["artifact_sha256"], "sha256:" + hashlib.sha256(body).hexdigest())
        self.assertEqual(result.metadata["metadata_fields"], {})
        self.assertEqual(result.payload, b"")

    def test_same_url_changed_bytes_makes_new_hash_without_overwriting_observation(self):
        first = self.retrieve()
        old = dict(first.metadata)
        self.transport.responses[PAGE_URL]["body"] += b"Changed original fictional bytes."
        second = self.retrieve(observed_at="2032-01-07T12:00:00Z")
        self.assertNotEqual(first.metadata["artifact_sha256"], second.metadata["artifact_sha256"])
        self.assertEqual(first.metadata, old)
        self.assertNotEqual(first.metadata["observed_at"], second.metadata["observed_at"])

    def test_identical_retrieval_is_deterministic_given_explicit_observation_time(self):
        first, second = self.retrieve(), self.retrieve()
        self.assertEqual(first.metadata, second.metadata)
        self.assertEqual(first.provenance, second.provenance)
        self.assertEqual(first.payload, b"")

    def test_http_403_is_unavailable_not_a_permission_or_authority_verdict(self):
        result, _ = self.custom(response(status=403, body=b"DO NOT RETAIN THIS ERROR BODY"))
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.metadata["accessibility"], "HTTP_403")
        self.assertIsNone(result.metadata["artifact_sha256"])
        self.assertEqual(result.metadata["metadata_fields"], {})
        self.assertFalse(result.provenance["release_selected"])
        self.assertNotIn("permission_status", result.metadata)

    def test_http_404_does_not_declare_supersession_or_withdrawal(self):
        result, _ = self.custom(response(status=404, body=b"DO NOT RETAIN"))
        self.assertEqual(result.metadata["accessibility"], "HTTP_404")
        self.assertIsNone(result.metadata["artifact_sha256"])
        self.assertNotIn("supersedes", result.metadata)
        self.assertNotIn("superseded_by", result.metadata)

    def test_timeout_and_transport_unavailability_are_explicit(self):
        for error, status in ((TimeoutError("fixture"), "TIMEOUT"), (OSError("fixture"), "ACCESS_UNAVAILABLE")):
            with self.subTest(status=status):
                result, _ = self.custom(error)
                self.assertEqual(result.metadata["accessibility"], status)
                self.assertIsNone(result.metadata["artifact_sha256"])
                self.assertEqual(result.payload, b"")

    def test_nonofficial_insecure_credentialed_or_ambiguous_urls_fail_before_transport(self):
        unsafe = ("http://magic.wizards.com/en/rules", "https://example.invalid/rules",
                  "https://magic.wizards.com.evil.invalid/rules", "https://user:secret@magic.wizards.com/en/rules",
                  "https://magic.wizards.com/en/rules?token=secret", "https://magic.wizards.com/en/rules#fragment",
                  "https://magic.wizards.com:444/en/rules", "https://magic.wizards.com\\evil/rules",
                  "https://magic.wizards.com/en/%0d%0arules")
        for url in unsafe:
            with self.subTest(url=url), self.assertRaises(AcquisitionError):
                self.retrieve(url=url)
        self.assertEqual(self.transport.calls, [])

    def test_request_requires_only_url_and_explicit_observed_timestamp(self):
        for parameters in ({"url": PAGE_URL}, {"url": PAGE_URL, "observed_at": "2032-01-06"},
                           {"url": PAGE_URL, "observed_at": OBSERVED_AT, "headers": {"Authorization": "secret"}},
                           {"url": PAGE_URL, "observed_at": OBSERVED_AT, "cookies": "secret"}):
            with self.subTest(parameters=parameters), self.assertRaises(AcquisitionError):
                self.provider.build_request("rules-source", parameters)
        self.assertEqual(self.transport.calls, [])

    def test_retrieve_revalidates_forged_provider_request(self):
        request = ProviderRequest("rules-source", {"url": "https://example.invalid", "observed_at": OBSERVED_AT})
        with self.assertRaises(AcquisitionError):
            self.provider.retrieve(request)
        self.assertEqual(self.transport.calls, [])

    def test_approved_redirect_is_bounded_and_explicit(self):
        transport = LocalMetadataTransport({PAGE_URL: response(status=302, location=ARTIFACT_URL),
                                            ARTIFACT_URL: response(ARTIFACT_URL, content_type="text/plain", body=ARTIFACT_BODY)})
        result = self.retrieve(provider=WizardsRulesMetadataProvider(transport))
        self.assertEqual(result.metadata["requested_url"], PAGE_URL)
        self.assertEqual(result.metadata["resolved_url"], ARTIFACT_URL)
        self.assertEqual([call["url"] for call in transport.calls], [PAGE_URL, ARTIFACT_URL])

    def test_redirect_outside_domain_is_blocked_before_second_request(self):
        result, transport = self.custom(response(status=302, location="https://outside.invalid/rules.txt"))
        self.assertEqual(result.metadata["accessibility"], "REDIRECT_BLOCKED")
        self.assertEqual(len(transport.calls), 1)

    def test_redirect_limit_and_silent_transport_redirect_are_blocked(self):
        result, transport = self.custom(response(status=302, location=ARTIFACT_URL), max_redirects=0)
        self.assertEqual(result.metadata["accessibility"], "REDIRECT_BLOCKED")
        self.assertEqual(len(transport.calls), 1)
        result, _ = self.custom(response(url=ARTIFACT_URL))
        self.assertEqual(result.metadata["accessibility"], "REDIRECT_BLOCKED")

    def test_mime_and_encoding_fail_closed_without_payload_or_hash(self):
        for changes in ({"content_type": "application/zip"}, {"content_encoding": "gzip"}):
            result, _ = self.custom(response(**changes))
            with self.subTest(changes=changes):
                self.assertEqual(result.metadata["accessibility"], "CONTENT_TYPE_UNSUPPORTED")
                self.assertIsNone(result.metadata["artifact_sha256"])
                self.assertEqual(result.payload, b"")

    def test_response_limit_is_enforced_and_passed_to_transport(self):
        result, transport = self.custom(response(body=b"x" * 41), max_response_bytes=40, timeout_seconds=3)
        self.assertEqual(result.metadata["accessibility"], "ARTIFACT_TOO_LARGE")
        self.assertIsNone(result.metadata["artifact_sha256"])
        self.assertEqual(transport.calls[0]["max_response_bytes"], 40)
        self.assertEqual(transport.calls[0]["timeout_seconds"], 3)

    def test_policy_cannot_request_unbounded_size_redirects_or_timeout(self):
        for options in ({"max_response_bytes": 0}, {"max_response_bytes": 10**9}, {"max_redirects": 6},
                        {"timeout_seconds": 31}, {"timeout_seconds": float("inf")}, {"timeout_seconds": True}):
            with self.subTest(options=options), self.assertRaises(AcquisitionError):
                WizardsRulesMetadataProvider(self.transport, **options)

    def test_conflicting_or_malformed_structured_metadata_is_not_guessed(self):
        for body in (HTML_BODY.replace(b"</head>", b'<meta name="rules-version" content="conflict"></head>'),
                     HTML_BODY.replace(b"2032-01-01", b"not-a-date"), b"\xff\xfe"):
            result, _ = self.custom(response(body=body))
            with self.subTest(body=body):
                self.assertEqual(result.metadata["accessibility"], "PARSE_METADATA_FAILED")
                self.assertEqual(result.metadata["metadata_fields"], {})
                self.assertEqual(result.payload, b"")

    def test_external_designation_links_are_not_followed_or_retained(self):
        body = b'<a href="https://outside.invalid/rules.txt">Rules</a>'
        result, transport = self.custom(response(body=body))
        self.assertEqual(result.metadata["designated_links"], [])
        self.assertEqual(len(transport.calls), 1)

    def test_no_raw_snapshot_store_or_normalization_or_registry_bypass(self):
        with patch.object(RawSnapshotStore, "store", side_effect=AssertionError("No raw body storage")):
            result = self.retrieve()
        self.assertEqual(result.payload, b"")
        with self.assertRaises(AcquisitionError):
            list(self.provider.emit_records(b"", "application/json"))
        with self.assertRaises(AcquisitionError):
            self.provider.validate_response(ProviderResponse(b"forbidden body", "application/json"))

    def test_local_transport_execution_requires_no_network_or_real_provider_data(self):
        with patch.object(socket, "socket", side_effect=AssertionError("No network")), \
             patch.object(UrllibMetadataTransport, "fetch", side_effect=AssertionError("No ambient transport")):
            result = self.retrieve()
        self.assertEqual(result.metadata["accessibility"], "AVAILABLE")
        retained = json.dumps({"metadata": result.metadata, "provenance": result.provenance})
        self.assertNotIn(HTML_BODY.decode(), retained)
        self.assertNotIn("headers", retained)
        self.assertNotIn("Authorization", retained)
        self.assertFalse(result.provenance["release_selected"])
