"""Data-driven review of the proposed, fictional evidence-packet contract."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
import proposed_spell_evidence_packet_validation as design


class ProposedSpellEvidencePacketDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = design.retained_rules()
        cls.records = design.load_package()
        cls.contract = cls.records["contract.json"]
        cls.packets = [cls.records[name] for name in design.PACKET_NAMES]

    def validate(self, candidate, **kwargs):
        return design.validate_packet(candidate, contract=self.contract,
            rules=self.rules, **kwargs)

    def test_canonical_bytes_and_safe_file_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            good = root / "good.json"
            good.write_bytes(design._canonical_candidate({"authored": True}))
            self.assertEqual(design.canonical_read(good), {"authored": True})
            for raw in (b'{"x":1,"x":2}\n', b'{"x":NaN}\n',
                    b'{"x":1}', b'{ "x": 1 }\n', b'[]\xff'):
                path = root / "bad.json"
                path.write_bytes(raw)
                with self.subTest(raw=raw), self.assertRaises(GameplayContractError):
                    design.canonical_read(path)
            link = root / "link.json"
            link.symlink_to(good)
            with self.assertRaises(GameplayContractError):
                design.canonical_read(link)
            hard = root / "hard.json"
            hard.hardlink_to(good)
            with self.assertRaises(GameplayContractError):
                design.canonical_read(hard)

    def test_five_distinct_complete_authored_outcomes(self):
        self.assertEqual([p["conclusion"]["kind"] for p in self.packets], list(design.EXPECTED_OUTCOMES))
        self.assertEqual(len({p["packet_id"] for p in self.packets}), 5)
        for packet in self.packets:
            with self.subTest(packet=packet["scenario_label"]):
                self.assertEqual(self.validate(packet), packet)
                self.assertTrue(packet["fictional"])
                self.assertEqual(packet["execution_authority"], "BLOCKED")
                self.assertTrue(packet["conclusion"]["text"])
                self.assertTrue(packet["history"]["review_observations"])
                self.assertTrue(all(row["explanation"] for row in packet["reasoning"]))

    def test_required_fields_and_strict_json_types(self):
        for field in self.contract["required"]:
            packet = deepcopy(self.packets[0])
            del packet[field]
            with self.subTest(missing=field), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet) if field != "packet_id" else packet)
        for mutate in (
                lambda p: p.update(revision=True), lambda p: p.update(revision=1.0),
                lambda p: p["contexts"][0].update(version="1"),
                lambda p: p["contexts"][0].update(version=1.0),
                lambda p: p.update(fictional=1), lambda p: p.update(unrecognized=True),
                lambda p: p["claims"][0].update(value=""),
                lambda p: p["claims"][0].update(value=42)):
            packet = deepcopy(self.packets[0])
            mutate(packet)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))

    def test_identities_and_actual_retained_bindings(self):
        zero = "sha256:" + "0" * 64
        for field in ("packet_id", "contract_id"):
            packet = deepcopy(self.packets[0]); packet[field] = zero
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                self.validate(packet)
        for field in ("package_id", "projection_id", "rule_id", "anchor_id", "artifact_hash", "retained_package"):
            packet = deepcopy(self.packets[0])
            packet["rule_evidence"][0][field] = "gameplay-rules-other-package" if field == "retained_package" else zero
            with self.subTest(binding=field), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        evidence = self.packets[0]["rule_evidence"]
        self.assertGreater(len({row["package_id"] for row in evidence}), 2)
        for row in evidence:
            self.assertEqual(row["package_id"], self.rules[row["rule_reference"]]["package_id"])
        self.assertEqual(len(self.rules), 100)

    def test_dangling_and_duplicate_local_references(self):
        for mutate in (
                lambda p: p["reasoning"][0]["claim_refs"].append("absent"),
                lambda p: p["reasoning"][0]["rule_refs"].append("absent"),
                lambda p: p["reasoning"][0]["depends_on_steps"].append("address-ban"),
                lambda p: p["question"].update(context_id="absent"),
                lambda p: p["conclusion"]["limitation_refs"].append("absent"),
                lambda p: p["claims"][0]["rule_context_refs"].append("absent"),
                lambda p: p["choices"][0].update(alternative_id="other"),
                lambda p: p["claims"].append({**p["claims"][0], "value": "another"}),
                lambda p: p["history"]["review_observations"][0]["supersedes_observation_ids"].append("review-1")):
            packet = deepcopy(self.packets[0]); mutate(packet)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))

    def test_fictional_assertions_and_review_are_separate_authorities(self):
        for mutate in (
                lambda p: p.update(fictional=False),
                lambda p: p["claims"][0].update(basis="RETAINED_VERSIONED_RULE_CONTEXT_ONLY"),
                lambda p: p["claims"][0].update(subject_id="real:card:oracle"),
                lambda p: p["claims"][0]["attribution"].update(actor_id="fictional:b:narrator"),
                lambda p: p["rule_evidence"][0].update(authority="REAL_GAMEPLAY_PROOF"),
                lambda p: p["history"]["review_observations"][0].update(authority="OWNER_APPROVAL"),
                lambda p: p["history"]["review_observations"][0].update(fictional=False)):
            packet = deepcopy(self.packets[0]); mutate(packet)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[0])
        packet["claims"][0]["value"] = "An attributed assertion, unverified and possibly false."
        self.assertEqual(self.validate(design.seal_packet(packet)), packet)

    def test_valid_unknown_unsupported_and_conflict_remain_reviewable(self):
        for packet in self.packets[1:4]:
            self.assertEqual(self.validate(packet), packet)
        missing = self.packets[1]
        self.assertIsNone(next(c["value"] for c in missing["claims"] if c["condition"] == "UNKNOWN"))
        unsupported = self.packets[2]
        self.assertEqual({c["condition"] for c in unsupported["claims"]}, {"PRESENT"})
        self.assertEqual(unsupported["reasoning"][0]["operation"], "UNSUPPORTED_EVALUATION")
        for replacement in (False, "invented"):
            packet = deepcopy(missing)
            next(c for c in packet["claims"] if c["condition"] == "UNKNOWN")["value"] = replacement
            with self.subTest(value=replacement), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        for mutate in (
                lambda p: p["reasoning"][0].update(condition="PRESENT"),
                lambda p: p["reasoning"][0].update(operation="BOUNDED_AUTHORED_REASONING")):
            packet = deepcopy(unsupported); mutate(packet)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        packet = deepcopy(missing)
        packet["conclusion"]["limitation_refs"] = ["scope"]
        packet["limitations"][1]["kind"] = "UNKNOWN"
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))

    def test_conflicts_keep_both_values_and_attributions(self):
        packet = self.packets[3]
        claims = [c for c in packet["claims"] if c["condition"] == "CONFLICTING"]
        self.assertEqual({c["value"] for c in claims}, {True, False})
        self.assertEqual(len({c["attribution"]["actor_id"] for c in claims}), 2)
        reversed_packet = deepcopy(packet)
        reversed_packet["claims"].reverse()
        self.assertEqual(self.validate(design.seal_packet(reversed_packet))["conclusion"], packet["conclusion"])
        for mutate in (
                lambda p: p["claims"].pop(2),
                lambda p: p["claims"][2].update(value=p["claims"][1]["value"]),
                lambda p: p["claims"][2].update(attribution=p["claims"][1]["attribution"]),
                lambda p: p["claims"][2].update(predicate="different fact"),
                lambda p: p["limitations"][0].update(kind="UNKNOWN")):
            candidate = deepcopy(packet); mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(candidate))

    def test_distinct_alternatives_and_contexts_do_not_combine(self):
        for mutate in (
                lambda p: p["reasoning"][0]["claim_refs"].append("brighten"),
                lambda p: p["reasoning"][1]["depends_on_steps"].append("address"),
                lambda p: p["conclusion"].update(kind="CONDITIONAL_SUPPORT"),
                lambda p: p["limitations"][0].update(kind="SCOPE")):
            packet = deepcopy(self.packets[4]); mutate(packet)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[0])
        packet["contexts"].append({**packet["contexts"][0], "context_id": "other", "version": 2})
        packet["claims"][0]["context_id"] = "other"
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))

    def test_conclusion_assumptions_preserve_direct_and_transitive_scopes(self):
        for derived in (False, True):
            for alternative in (None, "soften", "brighten"):
                packet = deepcopy(self.packets[4])
                assumption = deepcopy(packet["claims"][-1])
                assumption.update(claim_id="scoped-premise", alternative_id=alternative)
                assumption["attribution"]["statement_id"] = "statement-scoped-premise"
                packet["claims"].append(assumption)
                step = "address"
                if derived:
                    packet["reasoning"].append({**packet["reasoning"][0],
                        "step_id": "derived", "claim_refs": ["premise"],
                        "depends_on_steps": ["address"]})
                    step = "derived"
                packet["conclusion"].update(kind="CONDITIONAL_SUPPORT", step_refs=[step],
                    assumption_refs=["premise", "scoped-premise"], limitation_refs=["scope"])
                design.seal_packet(packet)
                with self.subTest(derived=derived, alternative=alternative):
                    if alternative == "brighten":
                        with self.assertRaisesRegex(GameplayContractError, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH"):
                            self.validate(packet)
                    else:
                        self.assertEqual(self.validate(packet), packet)
        packet["reasoning"].append({**packet["reasoning"][0], "step_id": "general",
            "alternative_id": None, "claim_refs": ["premise"]})
        packet["conclusion"]["step_refs"] = ["general"]
        with self.assertRaisesRegex(GameplayContractError, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH"):
            self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[4])
        assumption = deepcopy(packet["claims"][-1])
        assumption.update(claim_id="soften-premise", alternative_id="soften")
        assumption["attribution"]["statement_id"] = "statement-soften-premise"
        packet["claims"].append(assumption)
        packet["reasoning"][0]["claim_refs"].append("soften-premise")
        self.assertEqual(self.validate(design.seal_packet(packet)), packet)
        packet["conclusion"]["assumption_refs"].append("soften-premise")
        with self.assertRaisesRegex(GameplayContractError, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH"):
            self.validate(design.seal_packet(packet))

    def test_historical_observation_claim_targets_remain_bound(self):
        original = deepcopy(self.packets[0])
        successor = deepcopy(original)
        successor["revision"] = 2
        successor["history"]["supersedes_packet_ids"] = [original["packet_id"]]
        history = {original["packet_id"]: original}
        self.assertEqual(self.validate(design.seal_packet(successor), history=history), successor)
        successor["claims"][-1]["value"] = False
        with self.assertRaisesRegex(GameplayContractError, "HISTORICAL_OBSERVATION_MATERIAL_CHANGED"):
            self.validate(design.seal_packet(successor), history=history)
        observation = deepcopy(successor["history"]["review_observations"][0])
        observation.update(observation_id="review-2", reviewer_id="fictional:a:second-reviewer",
            text="A separately attributed fictional observation of the corrected premise.")
        successor["history"]["review_observations"] = [observation]
        self.assertEqual(self.validate(design.seal_packet(successor), history=history), successor)
        self.assertEqual(history[original["packet_id"]], original)

    def test_historical_observation_step_targets_include_transitive_dependencies(self):
        for change in ("step", "premise", "transitive-premise", "choice", "limitation"):
            original = deepcopy(self.packets[0])
            original["history"]["review_observations"][0]["claim_refs"] = []
            if change == "limitation":
                original["reasoning"][0]["limitation_refs"] = ["scope"]
            if change == "transitive-premise":
                dependency = {**original["reasoning"][0], "step_id": "premise-step",
                    "alternative_id": None, "claim_refs": ["premise"]}
                original["reasoning"].insert(0, dependency)
                original["reasoning"][1]["depends_on_steps"] = ["premise-step"]
                original["reasoning"][1]["claim_refs"].remove("premise")
            self.assertEqual(self.validate(design.seal_packet(original)), original)
            successor = deepcopy(original)
            successor["revision"] = 2
            successor["history"]["supersedes_packet_ids"] = [original["packet_id"]]
            if change == "step":
                successor["reasoning"][0]["explanation"] += " Revised authored reasoning."
            elif change == "choice":
                successor["choices"][0]["description"] += " Revised fictional choice description."
            elif change == "limitation":
                successor["limitations"][0]["description"] += " Additional authored restriction."
            else:
                successor["claims"][-1]["value"] = False
            with self.subTest(change=change), self.assertRaisesRegex(GameplayContractError, "HISTORICAL_OBSERVATION_MATERIAL_CHANGED"):
                self.validate(design.seal_packet(successor), history={original["packet_id"]: original})

    def test_omitted_observations_cannot_reappear_with_changed_historical_targets(self):
        original = deepcopy(self.packets[0])
        for changed in (False, True):
            middle = deepcopy(original)
            middle["revision"] = 2
            middle["history"]["supersedes_packet_ids"] = [original["packet_id"]]
            middle["history"]["review_observations"] = []
            if changed:
                middle["claims"][-1]["value"] = False
            history = {original["packet_id"]: original}
            self.assertEqual(self.validate(design.seal_packet(middle), history=history), middle)
            successor = deepcopy(middle)
            successor["revision"] = 3
            successor["history"]["supersedes_packet_ids"] = [middle["packet_id"]]
            successor["history"]["review_observations"] = deepcopy(original["history"]["review_observations"])
            history[middle["packet_id"]] = middle
            design.seal_packet(successor)
            with self.subTest(changed=changed):
                if changed:
                    with self.assertRaisesRegex(GameplayContractError, "HISTORICAL_OBSERVATION_MATERIAL_CHANGED"):
                        self.validate(successor, history=history)
                else:
                    self.assertEqual(self.validate(successor, history=history), successor)

    def test_unsupported_positive_legality_and_execution_states_fail(self):
        for field, value in (("kind", "LEGAL"), ("kind", "CASTABLE"), ("kind", "READY_TO_EXECUTE"),
                ("stage", "PROPOSAL_LEGALITY"), ("unsupported_stronger_conclusions", [])):
            packet = deepcopy(self.packets[0]); packet["conclusion"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        for value in (True, "ALLOWED", "READY_TO_EXECUTE"):
            packet = deepcopy(self.packets[0]); packet["execution_authority"] = value
            with self.subTest(execution=value), self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[1])
        packet["reasoning"][0]["condition"] = "PRESENT"
        packet["conclusion"]["kind"] = "CONDITIONAL_SUPPORT"
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[1])
        packet["reasoning"].append({**packet["reasoning"][0], "step_id": "derived",
            "condition": "PRESENT", "claim_refs": ["premise"], "limitation_refs": [], "depends_on_steps": ["condition"]})
        packet["conclusion"]["step_refs"] = ["derived"]
        packet["conclusion"]["kind"] = "CONDITIONAL_SUPPORT"
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[0])
        packet["conclusion"]["kind"] = "INDETERMINATE_MISSING"
        packet["limitations"][0]["kind"] = "UNKNOWN"
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))
        packet = deepcopy(self.packets[0])
        assumption = {**packet["claims"][-1], "claim_id": "missing-assumption", "condition": "UNKNOWN",
            "value": None, "limitation_refs": ["missing-assumption"]}
        packet["claims"].append(assumption)
        packet["limitations"].append({"limitation_id": "missing-assumption", "kind": "UNKNOWN",
            "context_ids": ["ctx"], "claim_refs": ["missing-assumption"], "step_refs": [],
            "description": "The additional named assumption has no supplied value."})
        packet["conclusion"]["assumption_refs"].append("missing-assumption")
        packet["conclusion"]["limitation_refs"].append("missing-assumption")
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(packet))
        for original in self.packets[1:4]:
            packet = deepcopy(original); packet["conclusion"]["kind"] = "CONDITIONAL_SUPPORT"
            with self.assertRaises(GameplayContractError):
                self.validate(design.seal_packet(packet))

    def test_private_snapshot_and_append_only_supersession(self):
        packet = deepcopy(self.packets[0])
        result = self.validate(packet)
        packet["claims"].clear()
        self.assertTrue(result["claims"])
        result["contexts"].clear()
        self.assertTrue(self.packets[0]["contexts"])
        packet = deepcopy(self.packets[0])
        original_rules = design.retained_rules
        def change_caller():
            packet["claims"].clear()
            return original_rules()
        with patch.object(design, "retained_rules", side_effect=change_caller):
            self.assertTrue(design.validate_packet(packet, contract=self.contract)["claims"])
        original = deepcopy(self.packets[0])
        successor = deepcopy(original)
        successor["revision"] = 2
        successor["history"]["supersedes_packet_ids"] = [original["packet_id"]]
        successor["conclusion"]["text"] += " Fictional revision with unchanged bounds."
        design.seal_packet(successor)
        with self.assertRaises(GameplayContractError):
            self.validate(successor)
        history = {original["packet_id"]: original}
        self.assertEqual(self.validate(successor, history=history), successor)
        self.assertEqual(history[original["packet_id"]], original)
        wrong = deepcopy(successor)
        wrong["revision"] = 1
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(wrong), history=history)
        wrong = deepcopy(successor)
        wrong["history"]["review_observations"][0]["text"] = "Rewritten historical observation."
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(wrong), history=history)
        observation = deepcopy(successor["history"]["review_observations"][0])
        observation.update(observation_id="review-2", supersedes_observation_ids=["review-1"],
            text="Append-only fictional correction preserving the original observation.")
        successor["history"]["review_observations"].append(observation)
        design.seal_packet(successor)
        self.assertEqual(self.validate(successor, history=history), successor)
        wrong = deepcopy(successor)
        wrong["contexts"][0]["version"] = 2
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(wrong), history=history)
        invalid_prior = deepcopy(original)
        invalid_prior["claims"][0]["rule_context_refs"] = ["absent"]
        design.seal_packet(invalid_prior)
        wrong = deepcopy(successor)
        wrong["history"]["supersedes_packet_ids"] = [invalid_prior["packet_id"]]
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(wrong), history={invalid_prior["packet_id"]: invalid_prior})
        wrong = deepcopy(successor)
        wrong["history"]["supersedes_packet_ids"] = [self.packets[1]["packet_id"]]
        with self.assertRaises(GameplayContractError):
            self.validate(design.seal_packet(wrong), history={self.packets[1]["packet_id"]: self.packets[1]})

    def test_manifest_and_fresh_retained_history_tampering_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "design"
            shutil.copytree(design.PACKAGE_ROOT, copied)
            manifest = deepcopy(self.records["manifest.json"])
            manifest["files"][design.PACKET_NAMES[0]]["bytes"] += 1
            manifest["package_id"] = design.identity(design.PACKAGE_DOMAIN, manifest, "package_id")
            (copied / "manifest.json").write_bytes(design._canonical_candidate(manifest))
            with self.assertRaises(GameplayContractError):
                design.load_package(copied)
            for mutate in (
                    lambda a: a["authorization"].update(new_source_units=0.0),
                    lambda a: a["authorization"].update(runtime_authorized=0),
                    lambda a: a.update(execution_authority="ALLOWED"),
                    lambda a: a["permissions"].update(ai_export="ESTABLISHED"),
                    lambda a: a["historical_recommendation"].update(historical_future_milestone_begun=True)):
                assessment = deepcopy(self.records["design-assessment.json"]); mutate(assessment)
                assessment["record_id"] = design.identity(design.RECORD_DOMAIN, assessment, "record_id")
                (copied / "design-assessment.json").write_bytes(design._canonical_candidate(assessment))
                manifest = deepcopy(self.records["manifest.json"])
                raw = design._canonical_candidate(assessment)
                manifest["files"]["design-assessment.json"] = {"bytes": len(raw),
                    "sha256": design.hashlib.sha256(raw).hexdigest(), "identity": assessment["record_id"]}
                manifest["package_id"] = design.identity(design.PACKAGE_DOMAIN, manifest, "package_id")
                (copied / "manifest.json").write_bytes(design._canonical_candidate(manifest))
                with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                    design.load_package(copied)
            missing_history = Path(temporary) / "reviews"
            missing_history.mkdir()
            with self.assertRaises(GameplayContractError):
                design.load_package(review_root=missing_history)
            altered = deepcopy(self.records["contract.json"])
            altered["contract_id"] = "sha256:" + "0" * 64
            with self.assertRaises(GameplayContractError):
                design.validate_contract(altered)
            altered = deepcopy(self.records["contract.json"])
            altered["properties"]["claims"] = {"$ref": "https://invalid.example/schema"}
            altered["contract_id"] = design.identity(design.CONTRACT_DOMAIN, altered, "contract_id")
            with self.assertRaises(GameplayContractError):
                design.validate_contract(altered)


if __name__ == "__main__":
    unittest.main()
