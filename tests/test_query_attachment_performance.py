"""Detached query values and content identities remain safe when snapshots are reused."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Mapping
import unittest
from unittest.mock import patch

from legacy_profile_fixture import CONTROL, binding, build_legacy_fixture, read, save
from query.engine import CanonicalQueryEngine, QueryResult, _plain
from repository.legacy_profile import (LegacyCompatibilityAttachment, attach_legacy_compatibility,
                                       closure_identity, profile_identity)
from repository.snapshots import SnapshotError


def original_plain(value):
    """The retained conversion contract, independently of the optimized converter."""
    if is_dataclass(value):
        return original_plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): original_plain(child)
                for key, child in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [original_plain(child) for child in value]
    return value


@dataclass
class NestedValue:
    title: str
    values: list


@dataclass
class OuterValue:
    nested: NestedValue
    mixed_keys: dict
    sequence: tuple


def sample_values():
    nested = NestedValue("Étoile 雪", [{"values": [None, True, False, 1, 1.0, -0.0, 2.5]}])
    return {"nested": nested, "sequence": (["é", "e\u0301"], ("雪", None)),
            "mixed_keys": {2: "two", "10": "ten", 1: "numeric key", "1": "string key"}}


def make_result(values=None, provenance=None):
    return QueryResult("original-fixture", "card", sample_values() if values is None else values,
                       {"source_ids": ["original-author"],
                        "evidence_assertions": [{"id": "evidence", "values": [1, None]}]}
                       if provenance is None else provenance,
                       .75, "unknowns_reviewed", "superseded")


class QueryConversionIsolationTests(unittest.TestCase):
    def test_conversion_preserves_dataclasses_json_values_and_mapping_key_order(self):
        source = sample_values()
        value = OuterValue(source["nested"], source["mixed_keys"], source["sequence"])
        expected = original_plain(value)
        self.assertEqual(_plain(value), expected)
        self.assertEqual(list(_plain(value)), list(expected))
        self.assertEqual(list(_plain(value)["mixed_keys"]), ["1", "10", "2"])
        self.assertEqual(_plain(value)["mixed_keys"]["1"], "string key")
        self.assertEqual(_plain(value)["sequence"], [["é", "e\u0301"], ["雪", None]])
        self.assertEqual(json.dumps(_plain(value), ensure_ascii=False, sort_keys=True),
                         json.dumps(expected, ensure_ascii=False, sort_keys=True))

    def test_constructor_aliases_cannot_change_result_content(self):
        values = sample_values()
        provenance = {"source_ids": ["original-author"],
                      "evidence_assertions": [{"id": "evidence", "values": [1, None]}]}
        expected = original_plain({"canonical_identity": "original-fixture", "entity_type": "card",
                                   "canonical_values": values, "provenance_summary": provenance,
                                   "confidence": .75, "uncertainty": "unknowns_reviewed",
                                   "supersession_state": "superseded"})
        result = make_result(values, provenance)
        values["nested"].title = "changed"
        values["nested"].values[0]["values"].append("changed")
        values["sequence"][0].append("changed")
        values["mixed_keys"]["1"] = "changed"
        provenance["source_ids"].clear()
        provenance["evidence_assertions"][0]["values"].append("changed")
        self.assertEqual(result.as_dict(), expected)

    def test_exported_as_dict_values_cannot_change_result_content(self):
        result = make_result()
        expected = result.as_dict()
        exported = result.as_dict()
        exported["canonical_values"]["nested"]["values"][0]["values"].append("changed")
        exported["canonical_values"]["sequence"][0].clear()
        exported["provenance_summary"]["source_ids"].clear()
        exported["provenance_summary"]["evidence_assertions"][0]["values"].append("changed")
        exported["confidence"] = 0
        self.assertEqual(result.as_dict(), expected)

    def test_nested_reads_and_shallow_mapping_copies_are_detached(self):
        result = make_result()
        expected = result.as_dict()
        nested = result.canonical_values["nested"]
        self.assertIsInstance(nested, dict)
        self.assertIsInstance(nested["values"], list)
        nested["values"][0]["values"].clear()
        result.canonical_values["sequence"][0].append("changed")
        result.provenance_summary["source_ids"].append("changed")
        dict(result.canonical_values)["nested"]["values"].clear()
        dict(result.provenance_summary)["evidence_assertions"][0]["values"].clear()
        with self.assertRaises(TypeError):
            result.canonical_values["changed"] = True
        self.assertEqual(result.as_dict(), expected)

    def test_generic_dataclass_export_remains_detached_and_supported(self):
        result = make_result()
        expected = result.as_dict()
        exported = asdict(result)
        self.assertEqual(original_plain(exported), expected)
        exported["canonical_values"]["nested"]["values"].clear()
        exported["provenance_summary"]["source_ids"].clear()
        self.assertEqual(result.as_dict(), expected)

    def test_mapping_keys_cannot_retain_caller_owned_comparison_hooks(self):
        class MutableKey(str):
            def __str__(self):
                return self

            def __lt__(self, other):
                return str.__gt__(self, other) if self.reverse else str.__lt__(self, other)

        aliases = [MutableKey(value) for value in ("a", "b", "c", "d")]
        for key in aliases:
            key.reverse = False
        result = make_result({aliases[0]: 1, aliases[1]: 2},
                             {aliases[2]: 3, aliases[3]: 4})
        expected = json.dumps(result.as_dict(), sort_keys=True, separators=(",", ":"))
        for key in aliases:
            key.reverse = True
        self.assertEqual(json.dumps(result.as_dict(), sort_keys=True, separators=(",", ":")), expected)
        for mapping in (result.canonical_values, result.provenance_summary):
            for key in mapping:
                self.assertIs(type(key), str)
                with self.assertRaises(AttributeError):
                    key.reverse = True


class QueryScalarOwnershipTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.control = build_legacy_fixture(self.root)
        self.state_path = self.root / "data/canonical/state.json"
        self.original_entities = [item.as_dict() for item in self.engine().snapshot().entities]

    def engine(self):
        return CanonicalQueryEngine(self.control["game"], data_root=self.root / "data",
                                    games_root=self.root / "data/canonical/games")

    def write_confidence(self, confidence):
        state = read(self.state_path)
        state["card"]["cloth-unit"]["confidence"] = confidence
        # Ordinary JSON state supports floating-point confidence. The fictional
        # snapshot control writer intentionally accepts only integer JSON numbers.
        self.state_path.write_text(json.dumps(state, sort_keys=True, separators=(",", ":"),
                                              ensure_ascii=False, allow_nan=False))

    def expected_entities(self, confidence):
        entities = deepcopy(self.original_entities)
        next(item for item in entities if item["canonical_identity"] == "cloth-unit")["confidence"] = confidence
        return entities

    @staticmethod
    def payload(entities):
        return json.dumps(entities, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

    def test_json_state_rejects_non_numeric_confidence_before_public_access(self):
        for confidence in (["before"], {"nested": ["before"]}, True, False, "0.75"):
            with self.subTest(confidence=confidence):
                self.write_confidence(confidence)
                with self.assertRaisesRegex(TypeError, "confidence"):
                    engine = self.engine()
                    engine.entity("cloth-unit").confidence
                    engine.snapshot()

    def test_correctly_bound_attachment_rejects_mutable_confidence_safely(self):
        for confidence in (["before"], {"nested": ["before"]}):
            with self.subTest(confidence=confidence):
                self.write_confidence(confidence)
                control = deepcopy(self.control)
                control["files"] = [binding(self.root, row["path"], row["placement"])
                    if row["path"] == "data/canonical/state.json" else row
                    for row in control["files"]]
                control["closure_id"] = closure_identity(control["files"])
                # Independently describe the malformed fixture's exact would-be
                # query bytes; the reader must reject rather than bless them.
                control["query_snapshot_id"] = "sha256:" + hashlib.sha256(
                    self.payload(self.expected_entities(confidence))).hexdigest()
                control["profile_id"] = profile_identity(control)
                save(self.root / CONTROL, control)
                attachment = attach_legacy_compatibility(self.root, control_path=CONTROL,
                    game=control["game"], expected_profile_id=control["profile_id"])
                attachment.verify_unchanged()
                with self.assertRaises(SnapshotError) as caught:
                    engine = CanonicalQueryEngine.from_attachment(attachment)
                    engine.entity("cloth-unit").confidence
                    engine.snapshot()
                self.assertEqual(caught.exception.code, "invalid_catalog")
                self.assertEqual(str(caught.exception), "selected canonical catalog is invalid")
                attachment.verify_unchanged()

    def test_json_numeric_and_null_confidence_preserve_exact_output_identity_and_warm_reuse(self):
        identities = {}
        for confidence in (0, 1, 0.0, 1.0, -0.0, .75, None):
            label = json.dumps(confidence)
            with self.subTest(confidence=label):
                self.write_confidence(confidence)
                engine = self.engine()
                result = engine.entity("cloth-unit")
                snapshot = engine.snapshot()
                expected = self.payload(self.expected_entities(confidence))
                self.assertIs(type(result.confidence), type(confidence))
                self.assertEqual(self.payload([item.as_dict() for item in snapshot.entities]), expected)
                self.assertEqual(snapshot.snapshot_id, "sha256:" + hashlib.sha256(expected).hexdigest())
                if type(confidence) is int and confidence == 1:
                    self.assertEqual(snapshot.snapshot_id, self.control["query_snapshot_id"])
                with patch("query.engine._plain", side_effect=AssertionError("warm result conversion")):
                    repeated = engine.snapshot()
                self.assertEqual(repeated.snapshot_id, snapshot.snapshot_id)
                self.assertEqual(repeated.as_dict(), snapshot.as_dict())
                identities[label] = snapshot.snapshot_id
        self.assertNotEqual(identities["1"], identities["1.0"])
        self.assertNotEqual(identities["0"], identities["0.0"])
        self.assertNotEqual(identities["0.0"], identities["-0.0"])

    def test_other_scalar_result_fields_reject_mutable_or_non_string_values(self):
        for field in ("canonical_identity", "entity_type", "uncertainty", "supersession_state"):
            for value in (["before"], {"nested": ["before"]}, None, 1):
                with self.subTest(field=field, value=value):
                    arguments = make_result().as_dict()
                    arguments[field] = value
                    with self.assertRaisesRegex(TypeError, field):
                        QueryResult(**arguments)

    def test_scalar_subclasses_cannot_retain_mutable_caller_attributes(self):
        class Text(str):
            def __str__(self):
                return "overridden conversion"

        class Integer(int):
            def __int__(self):
                return 99

        class Floating(float):
            def __float__(self):
                return 99.0

        for scalar, expected in ((Integer(1), 1), (Floating(.75), .75)):
            arguments = make_result().as_dict()
            original_text = {field: arguments[field] for field in
                ("canonical_identity", "entity_type", "uncertainty", "supersession_state")}
            aliases = []
            for field in ("canonical_identity", "entity_type", "uncertainty", "supersession_state"):
                alias = Text(arguments[field])
                alias.nested = ["before"]
                aliases.append(alias)
                arguments[field] = alias
            scalar.nested = ["before"]
            arguments["confidence"] = scalar
            result = QueryResult(**arguments)
            exported = result.as_dict()
            for field in ("canonical_identity", "entity_type", "uncertainty", "supersession_state"):
                self.assertIs(type(getattr(result, field)), str)
                self.assertEqual(getattr(result, field), original_text[field])
            self.assertIs(type(result.confidence), type(expected))
            self.assertEqual(result.confidence, expected)
            for alias in [*aliases, scalar]:
                alias.nested.append("changed")
            self.assertEqual(result.as_dict(), exported)


class QuerySnapshotReuseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.root = self.work / "catalog"
        self.control = build_legacy_fixture(self.root)
        self.attachment = self.attach(self.root)
        self.engine = CanonicalQueryEngine.from_attachment(self.attachment)

    def attach(self, root):
        return attach_legacy_compatibility(root, control_path=CONTROL,
            game=self.control["game"], expected_profile_id=self.control["profile_id"])

    def assert_content_identity(self, snapshot):
        payload = json.dumps([item.as_dict() for item in snapshot.entities], sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(snapshot.snapshot_id, "sha256:" + hashlib.sha256(payload).hexdigest())

    def test_repeated_snapshot_identity_matches_its_content_and_fixture_control(self):
        expected = self.engine.snapshot().as_dict()
        for _ in range(3):
            snapshot = self.engine.snapshot()
            self.assertEqual(snapshot.snapshot_id, self.control["query_snapshot_id"])
            self.assertEqual(snapshot.as_dict(), expected)
            self.assert_content_identity(snapshot)
        with patch("query.engine._plain",
                   side_effect=AssertionError("warm snapshot must not rematerialize results")):
            reused = self.engine.snapshot()
        self.assertEqual(reused.as_dict(), expected)
        self.assert_content_identity(reused)

    def test_nested_snapshot_and_entity_reads_cannot_contaminate_reused_content(self):
        first = self.engine.snapshot()
        expected = first.as_dict()
        card = next(item for item in first.entities if item.canonical_identity == "paper-unit")
        card.provenance_summary["source_ids"].clear()
        card.provenance_summary["evidence_assertions"][0]["claim"] = "changed"
        self.engine.entity("paper-unit").provenance_summary["promotion_history"].clear()
        exported = first.as_dict()
        exported["entities"].clear()
        self.assertEqual(first.as_dict(), expected)
        repeated = self.engine.snapshot()
        self.assertEqual(repeated.as_dict(), expected)
        self.assert_content_identity(first)
        self.assert_content_identity(repeated)

    def test_warm_snapshots_still_reject_roots_game_inventory_and_attachment_retargeting(self):
        other_root = self.work / "other-catalog"
        shutil.copytree(self.root, other_root)
        other_attachment = self.attach(other_root)
        replacements = {"data_root": other_root / "data",
                        "games_root": other_root / "data/canonical/games",
                        "game": "another-game", "_read_inventory": None,
                        "_catalog_attachment": other_attachment}
        for name, replacement in replacements.items():
            with self.subTest(attribute=name):
                engine = CanonicalQueryEngine.from_attachment(self.attachment)
                for _ in range(3):
                    self.assert_content_identity(engine.snapshot())
                setattr(engine, name, replacement)
                with self.assertRaises(SnapshotError):
                    engine.snapshot()
        # Clearing the handle must not turn a warmed attached query into an
        # unrestricted reader and bypass the current verification boundary.
        self.engine.snapshot()
        self.engine._catalog_attachment = None
        with self.assertRaises(SnapshotError):
            self.engine.snapshot()

    def test_warm_snapshot_rechecks_current_attachment_after_access(self):
        self.engine.snapshot()
        selected = self.root / ("data/canonical/games/" + self.control["game"]
                                + "/cards/paper-unit/card.json")
        original_verify = LegacyCompatibilityAttachment.verify_unchanged
        checks = []

        def verify(attachment):
            checks.append(attachment)
            if len(checks) == 2:
                selected.write_bytes(selected.read_bytes() + b" ")
            return original_verify(attachment)

        with patch.object(LegacyCompatibilityAttachment, "verify_unchanged", verify):
            with self.assertRaises(SnapshotError):
                self.engine.snapshot()
        self.assertGreaterEqual(len(checks), 2)


class QueryAuditConstructionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.control = build_legacy_fixture(self.root)
        self.data = self.root / "data"
        state = read(self.data / "canonical/state.json")
        self.audits = {}
        for label in ("amber", "violet"):
            identifier, promotion = label + "-unit", label + "-promotion"
            assertion = {"id": label + "-assertion", "source_id": label + "-author",
                         "value": label + " fictional value", "status": "candidate"}
            state["card"][identifier] = {"entity_type": "card", "values": {"name": label},
                "promotion_id": promotion, "evidence_references": [assertion["id"]],
                "confidence": 1, "uncertainty_state": "known", "superseded_status": False}
            audit = {"promotion_id": promotion, "promoted_entities": [identifier],
                     "rejected_entities": [], "validation_results": {"valid": True},
                     "review_package": {"provider": {"provider_id": label + "-provider"},
                                        "candidate_assertions": [assertion]}}
            self.audits[label] = audit
            save(self.data / "audit" / (label + ".json"), audit)
        save(self.data / "canonical/state.json", state)

    def engine(self):
        return CanonicalQueryEngine(self.control["game"], data_root=self.data,
                                    games_root=self.data / "canonical/games")

    def test_construction_materializes_audits_once_and_keeps_distinct_entity_lineage(self):
        audit_paths = tuple(sorted((self.data / "audit").rglob("*.json")))
        observed = Counter()
        original_read = Path.read_bytes

        def read_bytes(path):
            if path in audit_paths:
                observed[path] += 1
            return original_read(path)

        with patch.object(Path, "read_bytes", read_bytes):
            engine = self.engine()
        self.assertEqual(observed, Counter({path: 1 for path in audit_paths}))
        for label, audit in self.audits.items():
            with self.subTest(entity=label):
                provenance = engine.entity(label + "-unit").provenance_summary
                self.assertEqual(provenance["evidence_assertions"],
                                 audit["review_package"]["candidate_assertions"])
                self.assertEqual(provenance["source_ids"], [label + "-author"])
                self.assertEqual(provenance["provider_policy"],
                                 audit["review_package"]["provider"])
                self.assertEqual([row["promotion_id"] for row in provenance["promotion_history"]],
                                 [label + "-promotion"])
                expected_hash = hashlib.sha256((self.data / "audit" / (label + ".json")).read_bytes()).hexdigest()
                self.assertEqual(provenance["promotion_history"][0]["audit_reference"]["sha256"],
                                 expected_hash)

    def test_postconstruction_audit_queries_reread_current_files_and_return_detached_values(self):
        engine = self.engine()
        engine.snapshot()
        returned = engine.related("amber-promotion", "promotion_audits")[0]
        returned["review_package"]["candidate_assertions"][0]["value"] = "caller mutation"
        returned["promoted_entities"].clear()
        self.assertEqual(engine.related("amber-promotion", "promotion_audits")[0], self.audits["amber"])
        changed = read(self.data / "audit/amber.json")
        changed.update(rejected_entities=["amber-unit"], validation_results={"valid": False},
                       result="changed-current-audit")
        save(self.data / "audit/amber.json", changed)
        self.assertEqual(engine._audit_records(promotion_id="amber-promotion"), (changed,))
        self.assertEqual(engine.related("amber-promotion", "promotion_audits"), (changed,))
        self.assertIn(changed, engine.validation("rejected"))
        self.assertIn(changed, engine.validation("validation_failure"))


if __name__ == "__main__":
    unittest.main()
