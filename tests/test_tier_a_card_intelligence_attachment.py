"""Fictional read-only Card Intelligence/acquisition attachment integration.

The existing mechanical source contract is exercised with original synthetic
bytes, not newly acquired or copied provider content. Missing buyer evidence is
deliberate; this vertical must abstain rather than invent purchase advice.
"""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import MechanicalCardIntelligence
from card_intelligence.acquisition import (CardAcquisitionAdapter,
                                          CardAcquisitionDossier,
                                          CardAcquisitionError)
from card_intelligence.mechanics import MechanicalEvidenceError, content_identity
from card_intelligence_attachment_fixture import (
    CARD_IDS, PRINTING_IDS, SOURCE_NAME, abstaining_packet, attach_fixture,
    build_intelligence_fixture, write_mechanical_source)
from legacy_profile_fixture import CONTROL, EXCLUDED_AUDIT, SELECTED_AUDITS
from query import CanonicalQueryEngine
from repository.legacy_profile import AUTHORITY, OPERATIONS
from repository import legacy_profile
from repository.snapshots import SnapshotError, attach_legacy_public
from semantic import SemanticRequest


class TierACardIntelligenceAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mtglab-fictional-intelligence-")
        self.addCleanup(self.temporary.cleanup)
        self.fixture = build_intelligence_fixture(Path(self.temporary.name))
        self.attachment = attach_fixture(self.fixture)
        self.expected = self.fixture["control"]["query_snapshot_id"]

    def mechanical(self, **changes):
        args = {"data_root": self.fixture["mechanical_data"],
                "source_directory": self.fixture["source_directory"],
                "expected_query_snapshot_id": self.expected}
        args.update(changes)
        return MechanicalCardIntelligence.from_attachment(self.attachment, **args)

    def adapter(self, mechanical=None):
        return CardAcquisitionAdapter.from_mechanical(
            mechanical or self.mechanical(), expected_query_snapshot_id=self.expected)

    def result(self, adapter=None, packet=None):
        return (adapter or self.adapter()).evaluate(
            packet or abstaining_packet(self.expected),
            source_root=Path(self.temporary.name)).to_dict()

    def test_explicit_attachment_single_query_is_shared_with_semantics_and_reasoning(self):
        original_init = CanonicalQueryEngine.__init__
        constructed = []

        def counted(query, *args, **kwargs):
            constructed.append(query)
            original_init(query, *args, **kwargs)

        with patch.object(CanonicalQueryEngine, "__init__", counted):
            engine = self.mechanical()
            adapter = self.adapter(engine)
            context = engine.reasoning_context(CARD_IDS[0]).to_dict()
        self.assertEqual(constructed, [engine.query])
        self.assertIs(adapter.mechanical, engine)
        self.assertIs(adapter.query, engine.query)
        self.assertIs(engine.context_builder._semantic._query, engine.query)
        self.assertEqual(engine.snapshot_id, self.expected)
        self.assertEqual(context["canonical_snapshot_id"], self.expected)

    def test_explicit_attachment_catalog_and_evidence_roots_are_independent(self):
        engine = self.mechanical()
        self.assertEqual(engine.query.data_root, self.fixture["catalog"] / "data")
        self.assertEqual(engine.data_root, self.fixture["mechanical_data"])
        self.assertNotEqual(engine.query.data_root, engine.data_root)
        self.assertEqual(set(engine.cards), set(CARD_IDS))

    def test_catalog_binding_separate_from_source_dossier_and_query_id(self):
        engine = self.mechanical()
        binding = engine.catalog_binding
        self.assertEqual(binding, engine.query.catalog_binding)
        self.assertNotEqual(binding["profile_id"], engine.snapshot_id)
        self.assertNotEqual(engine.source["acquisition_canonical_snapshot_identity"], engine.snapshot_id)
        self.assertNotEqual(engine.source["manifest_bytes_sha256"], binding["closure_id"])
        dossier = engine.dossier(CARD_IDS[0]).to_dict()
        self.assertEqual(dossier["schema_version"], "mechanical-card-dossier-v1")
        self.assertNotIn("catalog_binding", dossier)
        self.assertEqual(dossier["canonical_snapshot_id"], engine.snapshot_id)
        self.assertEqual(dossier["source"]["oracle_id"], CARD_IDS[0])

    def test_catalog_binding_mutation_does_not_change_attachment(self):
        engine = self.mechanical()
        changed = engine.catalog_binding
        changed["production_eligible"] = True
        changed["permissions"][OPERATIONS[0]] = "ESTABLISHED"
        self.assertFalse(engine.catalog_binding["production_eligible"])
        self.assertEqual(engine.catalog_binding["permissions"][OPERATIONS[0]], "NOT_ESTABLISHED")
        with self.assertRaises(AttributeError):
            engine.catalog_binding = changed

    def test_legacy_constructor_and_equivalent_dossier_bytes_unchanged(self):
        attached = self.mechanical()
        legacy = MechanicalCardIntelligence(self.fixture["catalog"] / "data")
        self.assertIsNone(legacy.catalog_binding)
        self.assertEqual(legacy.snapshot_id, attached.snapshot_id)
        self.assertEqual(legacy.reconciliation, attached.reconciliation)
        for identity in CARD_IDS:
            self.assertEqual(legacy.dossier(identity).to_json(), attached.dossier(identity).to_json())
            self.assertEqual(legacy.reasoning_context(identity).to_json(), attached.reasoning_context(identity).to_json())

    def test_exact_card_and_printing_relationships_no_name_or_seed_fallback(self):
        engine = self.mechanical()
        self.assertNotIn("paper-unit", engine.cards)
        self.assertEqual({x.canonical_identity for x in engine.query.related(CARD_IDS[0], "card_printings")},
                         {PRINTING_IDS[0]})
        dossier = engine.dossier(CARD_IDS[0]).to_dict()
        self.assertEqual(dossier["source"]["canonical_source_printing_ids"], [PRINTING_IDS[0]])
        for invalid in ("Cloth Cartographer", "paper-unit", "not-a-card"):
            with self.assertRaises(MechanicalEvidenceError):
                engine.dossier(invalid)

    def test_adapter_from_attachment_reuses_its_only_query(self):
        with patch("card_intelligence.acquisition.MechanicalCardIntelligence.from_attachment",
                   wraps=MechanicalCardIntelligence.from_attachment) as create:
            adapter = CardAcquisitionAdapter.from_attachment(
                self.attachment, data_root=self.fixture["mechanical_data"],
                source_directory=self.fixture["source_directory"],
                expected_query_snapshot_id=self.expected)
        self.assertEqual(create.call_count, 1)
        self.assertIs(adapter.query, adapter.mechanical.query)
        self.assertEqual(adapter.mechanical.snapshot_id, self.expected)
        self.assertEqual(set(adapter.printings), set(PRINTING_IDS))

    def test_adapter_legacy_constructor_and_decision_policy_bytes_unchanged(self):
        legacy = CardAcquisitionAdapter(self.fixture["catalog"] / "data")
        attached = self.adapter()
        packet = abstaining_packet(self.expected)
        self.assertEqual(self.result(legacy, packet), self.result(attached, packet))
        self.assertEqual(legacy.policy, attached.policy)

    def test_full_fictional_vertical_returns_deterministic_honest_abstention(self):
        adapter = self.adapter()
        result = self.result(adapter)
        self.assertEqual(result, self.result(adapter))
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")
        self.assertIsNone(result["decision"]["recommendation"]["selected_alternative_id"])
        self.assertTrue(result["blockers"])
        self.assertFalse(result["actual_purchase_advice"])
        self.assertEqual(result["canonical_snapshot_id"], self.expected)
        self.assertEqual({r["printing_id"] for r in result["candidates"]}, set(PRINTING_IDS))
        for row in result["candidates"]:
            self.assertEqual(row["source"]["resolution"], "unique")
            self.assertIsNone(row["owned_acceptable_quantity"])
            self.assertIsNone(row["complete_cost"])
        self.assertEqual(CardAcquisitionDossier(result).to_dict(), result)
        context = CardAcquisitionDossier(result).reasoning_context()
        self.assertEqual(context["dossier"]["canonical_snapshot_id"], self.expected)
        self.assertEqual(result["reconstruction"]["canonical"]["snapshot_id"], self.expected)

    def test_missing_mechanical_coverage_is_explicit_not_a_catalog_failure(self):
        rows = self.fixture["rows"][1:]
        write_mechanical_source(self.fixture["source_directory"], rows)
        engine = self.mechanical()
        self.assertEqual(engine.reconciliation["missing_canonical_card_ids"], [CARD_IDS[0]])
        dossier = engine.dossier(CARD_IDS[0]).to_dict()
        self.assertEqual(dossier["source"]["resolution"], "missing")
        self.assertEqual(dossier["fields"]["oracle_text"]["reason"], "source_binding_missing")
        self.assertNotIn("value", dossier["fields"]["oracle_text"])
        result = self.result(self.adapter(engine))
        self.assertIn("mechanical_source:" + CARD_IDS[0] + ":source_binding_missing", result["blockers"])
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")

    def test_ambiguous_mechanical_coverage_never_selects_or_falls_back(self):
        rows = copy.deepcopy(self.fixture["rows"])
        duplicate = {**rows[0], "id": "fictional-conflicting-second-record"}
        rows.append(duplicate)
        write_mechanical_source(self.fixture["source_directory"], rows)
        engine = self.mechanical()
        self.assertEqual(engine.reconciliation["ambiguous_canonical_card_ids"], [CARD_IDS[0]])
        dossier = engine.dossier(CARD_IDS[0]).to_dict()
        self.assertEqual(dossier["source"]["resolution"], "ambiguous")
        self.assertNotIn("provider_record_id", dossier["source"])
        self.assertEqual(dossier["fields"]["oracle_text"]["reason"], "source_binding_ambiguous")
        result = self.result(self.adapter(engine))
        self.assertIn("mechanical_source:" + CARD_IDS[0] + ":source_binding_ambiguous", result["blockers"])

    def test_source_identity_mismatch_does_not_match_card_name(self):
        rows = copy.deepcopy(self.fixture["rows"])
        rows[0]["oracle_id"] = "unrelated-fictional-card"
        write_mechanical_source(self.fixture["source_directory"], rows)
        engine = self.mechanical()
        self.assertEqual(engine.reconciliation["missing_canonical_card_ids"], [CARD_IDS[0]])
        self.assertEqual(engine.dossier(CARD_IDS[0]).to_dict()["source"]["resolution"], "missing")

    def test_initial_source_checksum_mismatch_rejected_independently(self):
        path = self.fixture["source_directory"] / SOURCE_NAME
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(MechanicalEvidenceError, "integrity mismatch"):
            self.mechanical()
        self.attachment.verify_unchanged()

    def test_postconstruction_source_drift_blocks_dossier_context_and_acquisition(self):
        engine = self.mechanical()
        adapter = self.adapter(engine)
        path = self.fixture["source_directory"] / SOURCE_NAME
        path.write_bytes(path.read_bytes() + b" ")
        self.attachment.verify_unchanged()
        for call in (engine.verify_inputs, lambda: engine.dossier(CARD_IDS[0]),
                     lambda: engine.reasoning_context(CARD_IDS[0]),
                     lambda: self.result(adapter)):
            with self.subTest(call=call):
                with self.assertRaises(MechanicalEvidenceError):
                    call()

    def test_rehashed_source_replacement_cannot_reuse_construction_binding(self):
        engine = self.mechanical()
        rows = copy.deepcopy(self.fixture["rows"])
        rows[0]["oracle_text"] = "Changed original fictional instruction."
        write_mechanical_source(self.fixture["source_directory"], rows)
        with self.assertRaises(MechanicalEvidenceError):
            engine.verify_inputs()

    def test_catalog_drift_blocks_without_breaking_independent_source(self):
        engine = self.mechanical()
        adapter = self.adapter(engine)
        source = (self.fixture["source_directory"] / SOURCE_NAME).read_bytes()
        path = self.fixture["catalog"] / "data/canonical/state.json"
        path.write_bytes(path.read_bytes() + b" ")
        for call in (engine.verify_inputs, lambda: engine.dossier(CARD_IDS[0]),
                     lambda: engine.reasoning_context(CARD_IDS[0]), lambda: self.result(adapter)):
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()
        self.assertEqual((self.fixture["source_directory"] / SOURCE_NAME).read_bytes(), source)

    def test_initial_wrong_expected_snapshot_is_blocked(self):
        with self.assertRaises(ValueError):
            self.mechanical(expected_query_snapshot_id="sha256:" + "0" * 64)

    def test_expected_snapshot_is_required_for_attached_construction(self):
        with self.assertRaises(TypeError):
            MechanicalCardIntelligence.from_attachment(
                self.attachment, data_root=self.fixture["mechanical_data"])

    def test_plain_dict_or_path_never_masquerades_as_verified_attachment(self):
        for value in (self.fixture["control"], self.fixture["catalog"], object()):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises((ValueError, TypeError)):
                    MechanicalCardIntelligence.from_attachment(
                        value, data_root=self.fixture["mechanical_data"],
                        expected_query_snapshot_id=self.expected)

    def test_unrestricted_legacy_root_handle_is_not_verified_attachment(self):
        legacy = attach_legacy_public(game="magic", data_root=self.fixture["catalog"] / "data")
        with self.assertRaises(SnapshotError):
            MechanicalCardIntelligence.from_attachment(
                legacy, data_root=self.fixture["mechanical_data"],
                expected_query_snapshot_id=self.expected)

    def test_missing_acquisition_artifact_cannot_fall_back_to_catalog_copy(self):
        (self.fixture["source_directory"] / "manifest.json").unlink()
        with self.assertRaises(MechanicalEvidenceError):
            self.mechanical()

    def test_mechanical_manifest_symlink_blocks_before_source_open(self):
        manifest = self.fixture["source_directory"] / "manifest.json"
        outside = Path(self.temporary.name) / "outside-manifest.json"
        manifest.rename(outside)
        manifest.symlink_to(outside)
        original = Path.read_bytes
        def guarded(path):
            if path in {manifest, outside}:
                raise AssertionError("symlink target was opened")
            return original(path)
        with patch.object(Path, "read_bytes", guarded):
            with self.assertRaises(MechanicalEvidenceError):
                self.mechanical()

    def test_mechanical_source_outside_explicit_evidence_root_is_rejected(self):
        with self.assertRaises(MechanicalEvidenceError):
            self.mechanical(source_directory=self.fixture["catalog"] / "data/market/acquisitions")

    def test_reasoning_semantic_query_cannot_be_retargeted_after_construction(self):
        engine = self.mechanical()
        engine.context_builder._semantic._query = CanonicalQueryEngine(
            "magic", data_root=self.fixture["catalog"] / "data",
            games_root=self.fixture["catalog"] / "data/canonical/games")
        with self.assertRaises(MechanicalEvidenceError):
            engine.reasoning_context(CARD_IDS[0])

    def test_cached_mechanical_row_edits_cannot_bypass_retained_source_binding(self):
        engine = self.mechanical()
        engine.rows[CARD_IDS[0]][0][1]["oracle_text"] = "Unbound cache edit."
        with self.assertRaises(MechanicalEvidenceError):
            engine.dossier(CARD_IDS[0])

    def test_cached_card_selection_cannot_expand_after_attachment(self):
        engine = self.mechanical()
        engine.cards["paper-unit"] = engine.query.entity("paper-unit", entity_type="card")
        with self.assertRaises(MechanicalEvidenceError):
            engine.dossier("paper-unit")

    def test_cached_acquisition_printing_selection_cannot_be_rewritten(self):
        adapter = self.adapter()
        adapter.printings.pop(PRINTING_IDS[0])
        with self.assertRaises(CardAcquisitionError):
            self.result(adapter)

    def test_failed_attachment_never_falls_back_to_valid_legacy_catalog(self):
        (self.fixture["catalog"] / CONTROL).write_bytes(b"{}")
        with patch.object(CanonicalQueryEngine, "__init__",
                          side_effect=AssertionError("ambient query must not be constructed")):
            with self.assertRaises(ValueError):
                self.mechanical(data_root=self.fixture["catalog"] / "data")

    def test_query_root_retargeting_blocks_dossier_and_acquisition(self):
        engine = self.mechanical()
        adapter = self.adapter(engine)
        engine.query.data_root = self.fixture["mechanical_data"]
        for call in (lambda: engine.dossier(CARD_IDS[0]), lambda: self.result(adapter)):
            with self.assertRaises(ValueError):
                call()

    def test_query_snapshot_state_cannot_be_rewritten_to_reuse_binding(self):
        engine = self.mechanical()
        engine.snapshot_id = "sha256:" + "f" * 64
        with self.assertRaises(ValueError):
            engine.verify_inputs()

    def test_adapter_rejects_mismatched_expected_snapshot(self):
        with self.assertRaises(ValueError):
            CardAcquisitionAdapter.from_mechanical(self.mechanical(),
                expected_query_snapshot_id="sha256:" + "f" * 64)

    def test_adapter_query_replacement_cannot_bypass_same_query_binding(self):
        adapter = self.adapter()
        adapter.query = CanonicalQueryEngine("magic", data_root=self.fixture["catalog"] / "data",
                                             games_root=self.fixture["catalog"] / "data/canonical/games")
        with self.assertRaises(ValueError):
            self.result(adapter)

    def test_acquisition_packet_different_snapshot_remains_blocked(self):
        packet = abstaining_packet("sha256:" + "e" * 64)
        try:
            result = self.result(packet=packet)
        except CardAcquisitionError:
            return
        self.assertIn("canonical_snapshot_mismatch", result["blockers"])
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")

    def test_reconstruction_wrong_canonical_snapshot_rejected_even_with_outer_hash(self):
        result = self.result()
        result["reconstruction"]["canonical"]["snapshot_id"] = "sha256:" + "d" * 64
        result["dossier_id"] = content_identity({k: v for k, v in result.items() if k != "dossier_id"})
        with self.assertRaises(CardAcquisitionError):
            CardAcquisitionDossier(result)

    def test_tier_b_semantic_audit_operations_remain_unsupported_before_io(self):
        engine = self.mechanical()
        semantic = engine.context_builder._semantic
        with patch("repository.legacy_profile._read", side_effect=AssertionError("Tier B must fail before reading")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("Tier B must fail before reading")):
            for operation, parameters in (("validation_statistics", {}),
                                          ("list_validation", {"state": "rejected"})):
                with self.subTest(operation=operation):
                    with self.assertRaises(SnapshotError) as caught:
                        semantic.execute(SemanticRequest(operation, parameters))
                    self.assertEqual(caught.exception.code, "unsupported_capability")

    def test_tier_a_vertical_never_reads_excluded_audit_or_source_record(self):
        excluded = {self.fixture["catalog"] / EXCLUDED_AUDIT,
                    self.fixture["catalog"] / "data/canonical/games/magic/sources/unselected-author.json"}
        original = Path.read_bytes
        inventory_read = legacy_profile._read
        opened = []

        def guarded(path):
            self.assertNotIn(path, excluded)
            opened.append(path)
            return original(path)

        def inventory_guarded(root, name):
            path = root / name
            self.assertNotIn(path, excluded)
            opened.append(path)
            return inventory_read(root, name)

        with patch.object(Path, "read_bytes", guarded), \
             patch("repository.legacy_profile._read", inventory_guarded):
            engine = self.mechanical()
            engine.dossier(CARD_IDS[0])
            engine.reasoning_context(CARD_IDS[0])
            self.result(self.adapter(engine))
        self.assertFalse(set(opened) & excluded)
        self.assertEqual({p.relative_to(self.fixture["catalog"]).as_posix()
                          for p in opened if p.is_relative_to(self.fixture["catalog"] / "data/audit")},
                         set(SELECTED_AUDITS))

    def test_no_network_or_provider_fallback_is_available(self):
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")), \
             patch("urllib.request.urlopen", side_effect=AssertionError("provider forbidden")):
            engine = self.mechanical()
            engine.dossier(CARD_IDS[0])
            engine.reasoning_context(CARD_IDS[0])
            self.result(self.adapter(engine))

    def test_intelligence_and_acquisition_are_read_only(self):
        root = Path(self.temporary.name)
        before = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in root.rglob("*") if p.is_file()}
        engine = self.mechanical()
        for identity in CARD_IDS:
            engine.dossier(identity)
            engine.reasoning_context(identity)
        self.result(self.adapter(engine))
        after = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_authority_permissions_never_promoted_by_successful_intelligence(self):
        engine = self.mechanical()
        self.result(self.adapter(engine))
        for key, value in AUTHORITY.items():
            self.assertEqual(engine.catalog_binding[key], value)
        self.assertEqual(engine.catalog_binding["permissions"], dict.fromkeys(OPERATIONS, "NOT_ESTABLISHED"))
        self.assertFalse(engine.catalog_binding["production_eligible"])

    def test_mechanical_evidence_not_added_to_tier_a_dependency_inventory(self):
        engine = self.mechanical()
        files = engine.catalog_binding["files"]
        self.assertFalse(any("market/acquisitions" in row["path"] for row in files))
        self.assertEqual({row["path"] for row in files if row["placement"] == "AUDIT_CONTEXT"},
                         set(SELECTED_AUDITS))


if __name__ == "__main__":
    unittest.main()
