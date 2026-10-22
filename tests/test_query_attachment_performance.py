"""Detached query values and content identities remain safe when snapshots are reused."""
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Mapping
import unittest
from unittest.mock import patch

from legacy_profile_fixture import CONTROL, build_legacy_fixture, read, save
from query.engine import CanonicalQueryEngine, QueryResult, _plain
from repository.legacy_profile import LegacyCompatibilityAttachment, attach_legacy_compatibility
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
