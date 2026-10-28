"""Actual retained Card binding checks; no classification correctness claim.

When the existing real publication writer has expanded the current catalog,
these checks require the fixed profile to reject it. They never install a
historical catalog fixture to conceal changed current data.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import cards as c
from card_intelligence.mechanics import MechanicalCardIntelligence, MechanicalEvidenceError
from query import CanonicalQueryEngine
from repository.legacy_profile import attach_legacy_compatibility
from repository.snapshots import SnapshotError


ROOT = Path(__file__).resolve().parents[1]
CONTROL = "config/catalog_profiles/legacy-public-tier-a.json"


def read(catalog=ROOT, mechanical=ROOT):
    return c.read_cards(catalog_root=catalog, mechanical_root=mechanical,
                        expected_profile_id=c.PROFILE_ID,
                        expected_query_snapshot_id=c.QUERY_ID)


def is_real_writer_expansion(root=ROOT):
    """Recognize only the existing disposable writer's exact current shape.

    This is a test-gate branch, never catalog authority or a substitute dataset.
    """
    root = Path(root)
    audit = root / "data/audit/bounded_promotions/isolated-reference-810-writer-rehearsal.json"
    if not audit.is_file() or audit.is_symlink():
        return False
    try:
        state = json.loads((root / "data/canonical/state.json").read_bytes())
    except (OSError, ValueError):
        return False
    expected = {"card": 654, "printing": 1183, "identifier": 505, "finish": 2}
    return (type(state) is dict and set(state) == set(expected)
            and all(type(state[key]) is dict and len(state[key]) == count
                    for key, count in expected.items()))


def current_catalog_intact(case):
    try:
        attach_legacy_compatibility(ROOT, control_path=CONTROL, game="magic",
                                    expected_profile_id=c.PROFILE_ID)
    except SnapshotError as error:
        if (error.code not in {"inventory_mismatch", "integrity_mismatch"}
                or not is_real_writer_expansion()):
            raise
        # A real expanded publication run changes the current input. Rejection
        # is the required capability behavior; substituting old data is forbidden.
        with case.assertRaises(SnapshotError):
            read()
        return False
    return True


def evidence_copy(destination):
    destination = Path(destination)
    source = "data/market/acquisitions/" + c.ACQUISITION
    shutil.copytree(ROOT / source, destination / source)
    for name in (c.DOSSIER_REFERENCE, c.MANIFEST_REFERENCE):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    return destination


class PilotCardEvidenceTests(unittest.TestCase):
    def test_expanded_writer_guard_requires_exact_existing_writer_shape(self):
        # Clearly fictional shape-only gate fixtures: these empty objects are
        # never passed to a query, evidence reader or interpretation contract.
        with tempfile.TemporaryDirectory(prefix="mtglab-fictional-writer-shape-") as temp:
            root = Path(temp)
            state_path = root / "data/canonical/state.json"
            state_path.parent.mkdir(parents=True)
            counts = {"card": 654, "printing": 1183, "identifier": 505, "finish": 2}
            state = {key: {str(i): {} for i in range(count)} for key, count in counts.items()}
            state_path.write_text(json.dumps(state))
            self.assertFalse(is_real_writer_expansion(root))
            audit = root / "data/audit/bounded_promotions/isolated-reference-810-writer-rehearsal.json"
            audit.parent.mkdir(parents=True)
            audit.write_text('{"fictional_shape_only":true}')
            self.assertTrue(is_real_writer_expansion(root))
            state["card"].pop("0")
            state_path.write_text(json.dumps(state))
            self.assertFalse(is_real_writer_expansion(root))
        for code, expansion in (("integrity_mismatch", False), ("missing_file", True),
                                ("identity_mismatch", True), ("inventory_mismatch", False)):
            error = SnapshotError("fictional guard rejection", code=code)
            with self.subTest(code=code, expansion=expansion), \
                    patch(__name__ + ".attach_legacy_compatibility", side_effect=error), \
                    patch(__name__ + ".is_real_writer_expansion", return_value=expansion):
                with self.assertRaises(SnapshotError) as raised:
                    current_catalog_intact(self)
                self.assertIs(raised.exception, error)

    def test_actual_exact_six_card_seven_subject_bindings_and_one_reader_query(self):
        if not current_catalog_intact(self):
            return
        created = []
        original_init = CanonicalQueryEngine.__init__

        def counted(query, *args, **kwargs):
            created.append(query)
            original_init(query, *args, **kwargs)

        # Retained selected dossiers must be validated without reconstructing
        # the full cohort or invoking per-subject live dossier reads.
        with patch.object(CanonicalQueryEngine, "__init__", counted), \
                patch.object(MechanicalCardIntelligence, "dossier", side_effect=AssertionError("no reconstruction")), \
                patch.object(MechanicalCardIntelligence, "cohort_report", side_effect=AssertionError("no cohort")), \
                patch.object(MechanicalCardIntelligence, "from_attachment", wraps=MechanicalCardIntelligence.from_attachment) as factory:
            result = read()
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(len(created), 1)
        self.assertEqual(result["canonical_snapshot_id"], c.QUERY_ID)
        self.assertEqual(set(result["cards"]), {row[0] for row in c.CARD_BINDINGS})
        self.assertEqual(set(result["subjects"]), {row[0] for row in c.SUBJECTS})
        self.assertEqual(result["acquisition"]["retained_source_sha256"], c.SOURCE_SHA256)
        self.assertEqual(result["acquisition"]["source_timestamp"], "2026-08-02T09:09:45.851000Z")
        self.assertEqual(result["acquisition"]["retrieved_at"], "2026-08-02T15:34:06Z")
        expected_rows = dict(zip((row[0] for row in c.CARD_BINDINGS), (308, 381, 120, 348, 221, 153)))
        self.assertEqual({key: value["source"]["source_record_index"] for key, value in result["cards"].items()}, expected_rows)
        for subject_id, card_id, passage, owner, _ in c.SUBJECTS:
            subject = result["subjects"][subject_id]
            self.assertEqual(subject["card_id"], card_id)
            self.assertEqual(subject["selected_passage"], passage)
            self.assertEqual(subject["owner"], owner)
            self.assertEqual(subject["complete_field_value"], subject["surrounding_before"] + passage + subject["surrounding_after"])
        subjects = result["subjects"]
        self.assertIn("doesn't untap", subjects["basalt-monolith-tap"]["surrounding_before"])
        self.assertIn("{3}: Untap", subjects["basalt-monolith-tap"]["surrounding_after"])
        self.assertIn("target land card", subjects["deathrite-shaman-first"]["selected_passage"])
        self.assertIn("Each opponent loses", subjects["deathrite-shaman-first"]["surrounding_after"])
        self.assertEqual(subjects["dark-ritual-spell"]["type_line"]["value"], "Instant")
        self.assertNotIn("Sacrifice", subjects["pitiless-plunderer-host-trigger"]["selected_passage"])
        self.assertIn("Sacrifice this token", subjects["pitiless-plunderer-host-trigger"]["surrounding_after"])
        self.assertFalse(result["catalog_binding"]["production_eligible"])
        self.assertFalse(result["catalog_binding"]["data_processing_permission_established"])
        self.assertEqual(result["catalog_binding"]["approval_state"], "not_granted")
        self.assertEqual(set(result["catalog_binding"]["permissions"].values()), {"NOT_ESTABLISHED"})

    def test_independent_relocation_read_only_and_defensive_outputs(self):
        if not current_catalog_intact(self):
            return
        with tempfile.TemporaryDirectory(prefix="mtglab-pilot-relocation-") as temp:
            directory = Path(temp)
            catalog = directory / "catalog"
            evidence = evidence_copy(directory / "evidence")
            profile = json.loads((ROOT / CONTROL).read_bytes())
            for name in [CONTROL, *(row["path"] for row in profile["files"])]:
                target = catalog / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            # The attachment inventories some names outside its readable file
            # closure. Preserve only those names as explicit empty test
            # placeholders; never inspect or supply their excluded contents.
            for namespace in profile["namespaces"]:
                for name in namespace["paths"]:
                    target = catalog / name
                    if not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.touch()
            def fingerprint():
                return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in directory.rglob("*") if path.is_file()}
            before = fingerprint()
            first = read(catalog, evidence)
            expected = deepcopy(first)
            first["catalog_binding"]["production_eligible"] = True
            first["cards"][c.CARD_BINDINGS[0][0]]["fields"]["oracle_text"]["value"] = "caller mutation"
            self.assertEqual(read(catalog, evidence), expected)
            self.assertEqual(fingerprint(), before)
            self.assertNotIn(str(directory), json.dumps(expected))
            self.assertFalse((catalog / "data/market").exists())
            self.assertFalse((evidence / "data/canonical").exists())

    def test_changed_retained_source_dossier_or_manifest_bytes_reject(self):
        if not current_catalog_intact(self):
            return
        names = ("data/market/acquisitions/" + c.ACQUISITION + "/source-mb2.json",
                 c.DOSSIER_REFERENCE, c.MANIFEST_REFERENCE)
        for name in names:
            with self.subTest(path=name), tempfile.TemporaryDirectory(prefix="mtglab-pilot-corrupt-") as temp:
                evidence = evidence_copy(Path(temp))
                path = evidence / name
                path.write_bytes(path.read_bytes() + b" ")
                with self.assertRaises((c.CardBindingError, MechanicalEvidenceError)):
                    read(mechanical=evidence)

    def test_reader_retargeting_after_attachment_is_detected_at_boundary(self):
        if not current_catalog_intact(self):
            return
        original = MechanicalCardIntelligence.from_attachment
        captured = []

        def retarget(*args, **kwargs):
            mechanical = original(*args, **kwargs)
            captured.append(mechanical)
            mechanical.data_root = ROOT / "different-evidence-root"
            return mechanical

        with patch.object(MechanicalCardIntelligence, "from_attachment", side_effect=retarget):
            with self.assertRaisesRegex(MechanicalEvidenceError, "retargeted"):
                read()
        self.assertEqual(len(captured), 1)

    def test_fixed_expectations_and_strict_retained_json_reject(self):
        for profile, query in ((True, c.QUERY_ID), (c.PROFILE_ID, True),
                               (c.QUERY_ID, c.QUERY_ID), (c.PROFILE_ID, "sha256:" + "0" * 64)):
            with self.subTest(profile=profile, query=query), self.assertRaises(c.CardBindingError):
                c.read_cards(catalog_root=ROOT, mechanical_root=ROOT,
                    expected_profile_id=profile, expected_query_snapshot_id=query)
        for raw in (b'{"fictional": 1, "fictional": 2}', b'{"fictional": NaN}', b'{"fictional": Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(c.CardBindingError):
                c._strict(raw)


if __name__ == "__main__":
    unittest.main()
