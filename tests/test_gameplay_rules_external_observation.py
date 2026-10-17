"""Provenance and integrity tests for supplied metadata, without source bodies."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.observations import ExternalSourceObservation, verify_source_binding
from gameplay_rules_source_fixture import page_reference, unbound


def unavailable_source():
    return page_reference(
        game_id="magic", observed_at="2026-10-16T17:50:48.008334Z",
        discovered_at="2026-10-16T17:50:48.008334Z", resolved_reference=None,
        accessibility="UNAVAILABLE", access_outcome="ACCESS_UNAVAILABLE", http_status=None,
        media_type=None, artifact_hash=None, byte_length=None, evidence_status="EVIDENCE_UNAVAILABLE",
        completeness="UNKNOWN",
    )


def observation_body(source=None):
    """Authored metadata reproduces the user-supplied observation, not a fetch."""
    source = source or unavailable_source()
    return {
        "game_id": "magic", "observer_class": "PM_SUPPLIED_FIRST_PARTY_OBSERVATION",
        "observation_method": "First-party Wizards web review outside Codex's blocked network environment",
        "observed_on": "2026-10-16", "source_class": "RULES_INDEX", "authority_rank": "INDEX",
        "source_reference_id": source.identity,
        "observed_designation": {
            "title": "Magic: The Gathering Comprehensive Rules", "artifact_types": ["DOCX", "PDF", "TXT"],
            "filename_date_token": "20260925", "date_token_artifact_types": ["PDF", "TXT"],
            "artifact_reference": None, "artifact_filename": None,
        },
        "effective_date": "2026-09-25", "source_provided_version": None,
        "currentness": {"claim": "CURRENT_DESIGNATION_OBSERVED", "as_of_date": "2026-10-16"},
        "observed_markers": [{"marker_id": "701.71", "heading": "Empower Jace"}],
        "relation_evidence": [{
            "source_class": "UPDATE_BULLETIN", "source_reference": None, "publication_date": "2026-09-21",
            "relation": "ANNOUNCES_RULE_CHANGE", "marker_id": "701.71", "heading": "Empower Jace",
            "at_least_identified_update_incorporated": True, "full_bulletin_diff_verified": False,
        }],
        "artifact_hash": None, "byte_length": None, "source_body_retained": False,
        "artifact_bytes_verified": False, "independent_verification_status": "NOT_INDEPENDENTLY_REPRODUCED",
        "codex_independently_fetched": False, "evidence_status": "VERIFIED_METADATA_ONLY",
        "observation_state": "EXTERNALLY_OBSERVED_FIRST_PARTY", "review_status": "REVIEWED",
        "limitations": ["Exact artifact SHA-256 and byte length were not supplied", "No source permission was established"],
        "provenance": ["Project Manager observation supplied explicitly by the owner on 2026-10-16"],
    }


class ExternalSourceObservationTests(unittest.TestCase):
    def setUp(self):
        self.source = unavailable_source()
        self.body = observation_body(self.source)
        self.observation = ExternalSourceObservation.create(self.body)

    def rejects(self, change):
        body = deepcopy(self.body)
        change(body)
        with self.assertRaises(GameplayContractError):
            ExternalSourceObservation.create(body)

    def test_original_unavailable_source_is_explicit_anchor_and_remains_unchanged(self):
        before = self.source.to_dict()
        self.assertIs(verify_source_binding(self.observation, self.source), self.observation)
        self.assertEqual(self.source.to_dict(), before)
        self.assertEqual(self.source.access_outcome, "ACCESS_UNAVAILABLE")
        self.assertEqual(self.source.evidence_status, "EVIDENCE_UNAVAILABLE")
        self.assertNotEqual(self.source.identity, self.observation.identity)

    def test_pm_provenance_is_external_metadata_not_independent_network_or_bytes(self):
        self.assertEqual(self.observation.observer_class, "PM_SUPPLIED_FIRST_PARTY_OBSERVATION")
        self.assertEqual(self.observation.observation_state, "EXTERNALLY_OBSERVED_FIRST_PARTY")
        self.assertEqual(self.observation.evidence_status, "VERIFIED_METADATA_ONLY")
        self.assertEqual(self.observation.independent_verification_status, "NOT_INDEPENDENTLY_REPRODUCED")
        for name in ("codex_independently_fetched", "artifact_bytes_verified", "source_body_retained",
                     "projection_authorized", "admission_eligible"):
            self.assertIs(getattr(self.observation, name), False)
        self.assertIsNone(self.observation.artifact_hash)
        self.assertIsNone(self.observation.byte_length)

    def test_metadata_currentness_is_scoped_to_actual_day(self):
        self.assertEqual(dict(self.observation.currentness), {
            "claim": "CURRENT_DESIGNATION_OBSERVED", "as_of_date": "2026-10-16"})
        self.assertEqual(self.observation.effective_date, "2026-09-25")
        self.assertEqual(self.observation.observed_designation["filename_date_token"], "20260925")
        self.assertEqual(self.observation.observed_designation["date_token_artifact_types"], ("PDF", "TXT"))
        self.rejects(lambda value: value["currentness"].update(as_of_date="2026-10-17"))
        self.rejects(lambda value: value["currentness"].update(claim="CURRENT_FOREVER"))

    def test_marker_proves_only_identified_bulletin_update(self):
        self.assertEqual(tuple(dict(value) for value in self.observation.observed_markers),
                         ({"marker_id": "701.71", "heading": "Empower Jace"},))
        relation = self.observation.relation_evidence[0]
        self.assertEqual(relation["publication_date"], "2026-09-21")
        self.assertIs(relation["at_least_identified_update_incorporated"], True)
        self.assertIs(relation["full_bulletin_diff_verified"], False)
        self.rejects(lambda value: value["relation_evidence"][0].update(full_bulletin_diff_verified=True))
        self.rejects(lambda value: value["relation_evidence"][0].update(marker_id="701.72"))
        self.rejects(lambda value: value["relation_evidence"][0].update(heading="A different heading"))

    def test_hash_and_length_are_unknown_and_no_filename_or_url_is_invented(self):
        self.assertIsNone(self.observation.artifact_hash)
        self.assertIsNone(self.observation.byte_length)
        self.assertIsNone(self.observation.observed_designation["artifact_filename"])
        self.assertIsNone(self.observation.observed_designation["artifact_reference"])
        self.rejects(lambda value: value.update(artifact_hash="sha256:" + "a" * 64))
        self.rejects(lambda value: value.update(byte_length=123))

    def test_supplied_digest_remains_external_metadata_and_never_verified_artifact(self):
        body = deepcopy(self.body)
        body.update(artifact_hash="sha256:" + "a" * 64, byte_length=123)
        record = ExternalSourceObservation.create(body)
        self.assertEqual(record.evidence_status, "VERIFIED_METADATA_ONLY")
        self.assertFalse(record.artifact_bytes_verified)
        self.assertNotEqual(record.identity, self.observation.identity)
        self.rejects(lambda value: value.update(evidence_status="VERIFIED_ARTIFACT"))

    def test_external_record_cannot_masquerade_as_codex_fetch_or_local_byte_verification(self):
        for name, value in (
            ("observer_class", "CODEX_NETWORK_OBSERVATION"),
            ("independent_verification_status", "INDEPENDENTLY_FETCHED"),
            ("independent_verification_status", "ARTIFACT_BYTES_VERIFIED_LOCALLY"),
            ("codex_independently_fetched", True), ("artifact_bytes_verified", True),
            ("source_body_retained", True), ("observation_state", "INDEPENDENTLY_FETCHED"),
            ("projection_authorized", True), ("admission_eligible", True),
        ):
            with self.subTest(name=name, value=value):
                self.rejects(lambda body, name=name, value=value: body.update({name: value}))

    def test_no_http_headers_corpus_or_approval_can_be_smuggled_into_metadata(self):
        for name in ("http_status", "response_headers", "source_body", "rules_text", "permission_granted"):
            with self.subTest(name=name):
                self.rejects(lambda body, name=name: body.update({name: "unretained"}))
        self.rejects(lambda value: value["observed_designation"].update(title="x" * 201))
        self.rejects(lambda value: value.update(provenance=["bounded"] * 17))

    def test_binding_requires_actual_contracts_exact_identity_game_and_source_class(self):
        with self.assertRaises(GameplayContractError):
            verify_source_binding(self.observation.to_dict(), self.source)
        with self.assertRaises(GameplayContractError):
            verify_source_binding(self.observation, self.source.to_dict())
        changed = page_reference()
        with self.assertRaises(GameplayContractError):
            verify_source_binding(self.observation, changed)
        for name, value in (("game_id", "different-game"), ("source_class", "COMPREHENSIVE_RULES")):
            body = deepcopy(self.body)
            body[name] = value
            if name == "source_class":
                body["authority_rank"] = "PRIMARY"
            with self.assertRaises(GameplayContractError):
                verify_source_binding(ExternalSourceObservation.create(body), self.source)

    def test_contract_is_deeply_immutable_and_defensive(self):
        original = self.observation.identity
        self.body["observed_designation"]["artifact_types"].append("UNDECLARED")
        copied = self.observation.to_dict()
        copied["observed_markers"][0]["heading"] = "changed"
        self.assertEqual(self.observation.identity, original)
        self.assertEqual(self.observation.observed_markers[0]["heading"], "Empower Jace")
        with self.assertRaises(TypeError):
            self.observation.currentness["as_of_date"] = "2026-10-17"
        with self.assertRaises(FrozenInstanceError):
            self.observation._payload = {}

    def test_identity_is_deterministic_and_metadata_drift_requires_new_identity(self):
        self.assertEqual(ExternalSourceObservation.create(observation_body(self.source)).identity, self.observation.identity)
        self.assertEqual(ExternalSourceObservation.from_json(json.dumps(self.observation.to_dict())).identity,
                         self.observation.identity)
        changed = unbound(self.observation)
        changed["observation_method"] = "A separately supplied observation method"
        self.assertNotEqual(ExternalSourceObservation.create(changed).identity, self.observation.identity)
        copied = self.observation.to_dict()
        copied["effective_date"] = "2026-09-24"
        with self.assertRaises(GameplayContractError):
            ExternalSourceObservation.from_dict(copied)

    def test_malformed_json_and_unbounded_metadata_are_rejected(self):
        for value in ('{"game_id":"one","game_id":"two"}', '{"game_id":NaN}'):
            with self.subTest(value=value), self.assertRaises(GameplayContractError):
                ExternalSourceObservation.from_json(value)
        self.rejects(lambda value: value.update(observed_markers=[{"marker_id": str(n), "heading": "Original"} for n in range(17)]))
        self.rejects(lambda value: value["observed_designation"].update(artifact_filename="../rules.txt"))
        self.rejects(lambda value: value["observed_designation"].update(date_token_artifact_types=["UNKNOWN"]))
        self.rejects(lambda value: value["observed_designation"].update(date_token_artifact_types=[]))
        self.rejects(lambda value: value["observed_designation"].update(artifact_reference="https://example.test/?token=secret"))
        self.rejects(lambda value: value.update(authority_rank="PRIMARY"))
        self.rejects(lambda value: value.update(observed_on="current"))


if __name__ == "__main__":
    unittest.main()
