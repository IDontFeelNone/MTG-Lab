import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

from card_intelligence.deck_usage import (DeckUsageEvidenceError, PILOT_NAMES, canonical_bytes,
                                          decode_deck_archive, load_deck_usage, project_decks)

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


if __name__ == "__main__": unittest.main()
