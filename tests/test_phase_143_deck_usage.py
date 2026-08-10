import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import warnings
import zipfile

from card_intelligence.deck_usage import (DeckUsageEvidenceError, PILOT_NAMES, canonical_bytes,
                                          decode_deck_archive, load_deck_usage, project_decks)
from scripts.verify_deck_usage_boundary import EVIDENCE_PATH, verify

IDS = {name: f"card-{index}" for index, name in enumerate(PILOT_NAMES)}
KWARGS = {"dataset_timestamp": "2026-08-09T00:00:00Z",
          "retrieved_at": "2026-08-09T01:00:00Z", "source_sha256": "a" * 64,
          "source_byte_count": 100}


def decoded(path, deck, content=None):
    content = canonical_bytes(deck) if content is None else content
    return {"source_record_identity": path,
            "source_content_sha256": hashlib.sha256(content).hexdigest(), "deck": deck}


def archive(entries):
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(output, "w") as value:
            for name, document in entries:
                value.writestr(name, canonical_bytes(document))
    return output.getvalue()


class Phase143DeckUsageTests(unittest.TestCase):
    def decks(self):
        return [
            decoded("decks/commander-one.json",
                    {"code": "shared", "name": "Repeated Name", "type": "Commander",
                     "commander": [{"name": "Command Tower"}],
                     "mainBoard": [{"name": "Sol Ring"}, {"name": "Command Tower"}],
                     "sideBoard": []}),
            decoded("decks/legacy-one.json",
                    {"code": "shared", "name": "Repeated Name", "type": "Commander",
                     "commander": [], "mainBoard": [{"name": "Goblin Charbelcher"},
                                                     {"name": "Brainstorm"}], "sideBoard": []}),
            decoded("decks/no-code.json",
                    {"name": "No Provider ID", "type": "Commander", "commander": [],
                     "mainBoard": [{"name": "Sol Ring"}], "sideBoard": []}),
        ]

    def document(self):
        return project_decks(self.decks(), IDS, **KWARGS)

    def test_source_identity_preserves_missing_and_duplicate_provider_ids(self):
        document = self.document()
        sol = next(x for x in document["records"] if x["card_name"] == "Sol Ring")
        self.assertEqual((sol["numerator"], sol["denominator"]), (2, 3))
        self.assertEqual([x["provider_deck_identity"] for x in sol["deck_associations"]],
                         ["shared", None])
        self.assertEqual(len({x["retained_record_id"] for x in sol["deck_associations"]}), 2)
        self.assertEqual(sum(x["deck_count"] for x in sol["formats"]), 2)

    def test_card_on_multiple_boards_counts_file_once(self):
        command = next(x for x in self.document()["records"] if x["card_name"] == "Command Tower")
        self.assertEqual((command["numerator"], command["denominator"]), (1, 3))
        self.assertEqual(command["deck_associations"][0]["boards"], ["commander", "mainBoard"])

    def test_repeated_names_types_and_provider_ids_do_not_collapse_files(self):
        document = self.document()
        self.assertTrue(all(x["denominator"] == 3 for x in document["records"]))
        matches = [a for r in document["records"] for a in r["deck_associations"]]
        self.assertEqual({a["deck_name"] for a in matches}, {"Repeated Name", "No Provider ID"})
        self.assertEqual({a["format"] for a in matches}, {"commander"})

    def test_duplicate_source_identity_fails_closed(self):
        one = self.decks()[0]
        with self.assertRaisesRegex(DeckUsageEvidenceError, "duplicate_source_record_identity"):
            project_decks([one, dict(one)], IDS, **KWARGS)

    def test_conflicting_source_content_fails_closed(self):
        one = self.decks()[0]
        conflict = decoded(one["source_record_identity"], {"name": "Different"})
        with self.assertRaisesRegex(DeckUsageEvidenceError, "conflicting_source_record_content"):
            project_decks([one, conflict], IDS, **KWARGS)

    def test_archive_decoder_rejects_duplicate_member_and_conflict(self):
        first = {"data": {"name": "One"}}
        with self.assertRaisesRegex(DeckUsageEvidenceError, "duplicate_source_record_identity"):
            decode_deck_archive(archive([("same.json", first), ("same.json", first)]))
        with self.assertRaisesRegex(DeckUsageEvidenceError, "conflicting_source_record_content"):
            decode_deck_archive(archive([("same.json", first), ("same.json", {"data": {"name": "Two"}})]))

    def test_archive_decoder_preserves_distinct_byte_identical_aliases(self):
        value = {"data": {"name": "Alias", "mainBoard": []}}
        result = decode_deck_archive(archive([("a.json", value), ("b.json", value)]))
        self.assertEqual(len(result), 2)
        self.assertNotEqual(result[0]["source_record_identity"], result[1]["source_record_identity"])
        self.assertEqual(result[0]["source_content_sha256"], result[1]["source_content_sha256"])

    def test_malformed_deck_object_and_board_are_diagnostic(self):
        with self.assertRaisesRegex(DeckUsageEvidenceError, "malformed_deck_object"):
            decode_deck_archive(archive([("bad.json", {"data": []})]))
        malformed = decoded("bad-board.json", {"name": "Bad", "mainBoard": {}})
        with self.assertRaisesRegex(DeckUsageEvidenceError, "bad-board.json.*mainBoard"):
            project_decks([malformed], IDS, **KWARGS)

    def test_deterministic_ordering_and_retained_bytes(self):
        first = project_decks(self.decks(), IDS, **KWARGS)
        second = project_decks(list(reversed(self.decks())), IDS, **KWARGS)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))

    def test_strict_loader_is_backward_compatible_and_rejects_bad_values(self):
        original = self.document()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.json"; path.write_bytes(canonical_bytes(original))
            self.assertEqual(load_deck_usage(path)["provider"], "mtgjson")
            for mutate in (lambda x: x["records"][0].update(numerator=-1),
                           lambda x: x["records"][0].update(denominator=None),
                           lambda x: x["records"][0].update(extra="unsupported")):
                value = json.loads(json.dumps(original)); mutate(value)
                value["records_sha256"] = hashlib.sha256(canonical_bytes(value["records"])).hexdigest()
                path.write_bytes(canonical_bytes(value))
                with self.assertRaises(DeckUsageEvidenceError): load_deck_usage(path)

    def test_exact_pilot_required_and_no_inference(self):
        with self.assertRaises(DeckUsageEvidenceError):
            project_decks([], {"Sol Ring": "x"}, **KWARGS)
        text = canonical_bytes(self.document()).decode().lower()
        for forbidden in ("demand_score", "buy this", "undervalued", "price_prediction", "scarcity_score"):
            self.assertNotIn(forbidden, text)

    def test_strict_loader_checks_timestamps_source_and_retained_identities(self):
        original = self.document()
        mutations = (
            lambda value: value.update(retrieved_at="not-a-timestamp"),
            lambda value: value.update(source_sha256="invalid"),
            lambda value: value.update(population_semantics="all decks, somehow"),
            lambda value: value["records"][0].update(denominator=999),
            lambda value: value["records"][5]["deck_associations"][0].update(
                retained_record_id="not-path-derived"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.json"
            for mutate in mutations:
                value = json.loads(json.dumps(original)); mutate(value)
                value["records_sha256"] = hashlib.sha256(canonical_bytes(value["records"])).hexdigest()
                path.write_bytes(canonical_bytes(value))
                with self.assertRaises(DeckUsageEvidenceError):
                    load_deck_usage(path)


class Phase143PublicationBoundaryTests(unittest.TestCase):
    def make_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        (root / "baseline.txt").write_text("baseline\n")
        protected = root / "data/canonical/snapshot.json"
        protected.parent.mkdir(parents=True); protected.write_text("{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        return temporary, root

    @staticmethod
    def write_evidence(root):
        evidence = root / EVIDENCE_PATH
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("{}\n")
        return evidence

    def test_hosted_failure_untracked_file_is_seen_and_accepted(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_evidence(root)
            old = subprocess.run(["git", "diff", "--name-only"], cwd=root, check=True,
                                 text=True, capture_output=True)
            self.assertEqual(old.stdout, "")
            report = verify(root, "pre-commit")
            self.assertTrue(report["valid"])
            self.assertEqual(report["actual_paths"], [EVIDENCE_PATH])
            self.assertEqual(report["path_statuses"][0]["status"], "??")

    def test_extra_untracked_tracked_modification_and_protected_change_fail(self):
        for changed_path in ("extra.txt", "baseline.txt", "data/canonical/snapshot.json"):
            with self.subTest(path=changed_path):
                temporary, root = self.make_repository()
                with temporary:
                    self.write_evidence(root)
                    (root / changed_path).write_text("changed\n")
                    report = verify(root, "pre-commit")
                    self.assertFalse(report["valid"])
                    self.assertIn(changed_path, report["unexpected_paths"])

    def test_unrelated_staged_file_deletion_and_rename_fail(self):
        actions = (
            lambda root: subprocess.run(["git", "add", "baseline.txt"], cwd=root, check=True),
            lambda root: (root / "baseline.txt").unlink(),
            lambda root: subprocess.run(["git", "mv", "baseline.txt", "renamed.txt"], cwd=root, check=True),
        )
        for action in actions:
            temporary, root = self.make_repository()
            with temporary:
                self.write_evidence(root)
                (root / "baseline.txt").write_text("modified\n")
                action(root)
                self.assertFalse(verify(root, "pre-commit")["valid"])

    def test_symlink_and_absent_expected_file_fail(self):
        temporary, root = self.make_repository()
        with temporary:
            self.assertIn("evidence_file_absent", verify(root, "pre-commit")["failure_reason_codes"])
            evidence = root / EVIDENCE_PATH; evidence.parent.mkdir(parents=True)
            evidence.symlink_to(root / "baseline.txt")
            self.assertIn("evidence_symlink", verify(root, "pre-commit")["failure_reason_codes"])

    def test_exact_staged_boundary_succeeds(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_evidence(root)
            subprocess.run(["git", "add", "--", EVIDENCE_PATH], cwd=root, check=True)
            report = verify(root, "staged")
            self.assertTrue(report["valid"])
            self.assertEqual(report["staged_paths"], [EVIDENCE_PATH])
            self.assertEqual(report["path_statuses"][0]["status"], "A ")

    def test_workflow_publication_remains_manual_and_bounded(self):
        workflow = (Path(__file__).parents[1] /
                    ".github/workflows/deck-usage-acquisition.yml").read_text()
        self.assertIn("verify_deck_usage_boundary.py --boundary pre-commit", workflow)
        self.assertIn("verify_deck_usage_boundary.py --boundary staged", workflow)
        self.assertIn('git add -- "$FILE"', workflow)
        self.assertIn('git push origin "HEAD:refs/heads/$BRANCH"', workflow)
        self.assertNotIn("git diff --name-only", workflow)
        self.assertNotIn("--force", workflow)
        self.assertNotIn("--auto", workflow)
        self.assertNotIn("gh pr merge", workflow)


if __name__ == "__main__": unittest.main()
