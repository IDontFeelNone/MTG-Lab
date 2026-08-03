import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from production_evidence.pilot_printings import FILES, PILOT, PilotPrintingRetention, canonical_bytes


def corpus(path, *, missing=(), duplicate=False, conflict=False, malformed=False):
    cards = []
    for number, name in enumerate(PILOT, 1):
        if name in missing: continue
        card = {"uuid": f"00000000-0000-4000-8000-{number:012d}", "name": name,
                "number": str(number), "rarity": "rare", "language": "English",
                "finishes": ["nonfoil"], "identifiers": {"scryfallOracleId": f"oracle-{number}"},
                "isPromo": False, "isReprint": True, "isOnlineOnly": False}
        cards.append(card)
    cards.append({"uuid": "unrelated", "name": "Unrelated Card"})
    if duplicate: cards.append(dict(cards[0]))
    if conflict: cards.append({**cards[0], "number": "conflict"})
    if malformed: cards.append("bad")
    document = {"meta": {"date": "2026-08-03", "version": "5.3.0"}, "data": {
        "TST": {"code": "TST", "name": "Test Set", "releaseDate": "2020-01-01", "cards": cards},
        "MB2": {"code": "MB2", "name": "Mystery Booster 2", "cards": [dict(cards[0])]},
    }}
    # AllPrintings' streaming contract places meta before the large data object.
    path.write_bytes(gzip.compress((json.dumps(document, separators=(",", ":")) + "\n").encode(), mtime=0))


class Phase135Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root / "source.gz"; corpus(self.source)
        self.calls = 0

    def tearDown(self): self.temp.cleanup()

    def downloader(self, url, target):
        self.calls += 1; target.write_bytes(self.source.read_bytes())
        return {"status": 200, "content_type": "application/gzip"}

    def acquire(self, run="phase-135-test"):
        repo = self.root / "retained"; repo.mkdir(exist_ok=True)
        return PilotPrintingRetention(repo, self.downloader).acquire(
            run_id=run, source_url="https://mtgjson.com/api/v5/AllPrintings.json.gz",
            canonical_snapshot="sha256:canonical", acquired_at="2026-08-03T00:00:00Z")

    def test_exact_scope_fields_digests_inventory_and_one_download(self):
        result = self.acquire(); manifest = result["manifest"]
        self.assertEqual(self.calls, 1); self.assertEqual(manifest["pilot_scope"], list(PILOT))
        self.assertEqual(manifest["retained_printing_count"], 10)
        self.assertEqual(set(manifest["printing_counts_by_pilot_card"]), set(PILOT))
        destination = self.root / "retained/phase-135-test"
        self.assertEqual(tuple(sorted(x.name for x in destination.iterdir())), FILES)
        projection = (destination / "source-pilot-printings.json").read_bytes()
        self.assertEqual(hashlib.sha256(projection).hexdigest(), manifest["normalized_projection_sha256"])
        rows = json.loads(projection)["pilot_printings"]
        self.assertNotIn("Unrelated Card", [x["card_name"] for x in rows])
        self.assertEqual([x["provider_printing_id"] for x in rows], sorted(x["provider_printing_id"] for x in rows))
        required = {"provider_printing_id", "provider_card_or_oracle_id", "card_name", "set_name",
                    "set_code", "collector_number", "release_date", "language", "finishes", "rarity",
                    "frame_or_treatment", "promotional", "reprint", "digital_or_paper",
                    "source_record_identity", "dataset_publication_timestamp"}
        self.assertEqual(set(rows[0]), required); self.assertEqual(rows[0]["frame_or_treatment"], "unknown")

    def test_identical_replay_and_conflicting_replay(self):
        first = self.acquire(); before = (self.root / "retained/phase-135-test/manifest.json").read_bytes()
        second = self.acquire(); self.assertEqual(first, second); self.assertEqual(self.calls, 2)
        self.assertEqual(before, (self.root / "retained/phase-135-test/manifest.json").read_bytes())
        corpus(self.source, missing={"Brainstorm"})
        with self.assertRaisesRegex(FileExistsError, "conflicting acquisition replay"): self.acquire()

    def test_missing_malformed_duplicate_and_conflict(self):
        corpus(self.source, missing={"Wishclaw Talisman"}, duplicate=True, malformed=True)
        result = self.acquire("census")["manifest"]
        self.assertEqual(result["unmatched_pilot_cards"], ["Wishclaw Talisman"])
        self.assertEqual(result["duplicates"], 1); self.assertEqual(result["malformed_records"], 1)
        corpus(self.source, conflict=True)
        with self.assertRaisesRegex(ValueError, "conflicting provider printing identity"): self.acquire("conflict")

    def test_transport_compression_safe_identity_and_no_writes(self):
        repo = self.root / "retained"; repo.mkdir()
        for unsafe in ("../escape", "/absolute", "has space"):
            with self.assertRaisesRegex(ValueError, "unsafe"): PilotPrintingRetention(repo, self.downloader).acquire(
                run_id=unsafe, source_url="x", canonical_snapshot="x", acquired_at="x")
        def bad_type(url, target): target.write_bytes(self.source.read_bytes()); return {"status": 200, "content_type": "text/html"}
        with self.assertRaisesRegex(ValueError, "content type"): PilotPrintingRetention(repo, bad_type).acquire(
            run_id="bad-type", source_url="x", canonical_snapshot="x", acquired_at="2026-08-03T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "UTC RFC 3339"): PilotPrintingRetention(repo, self.downloader).acquire(
            run_id="bad-time", source_url="x", canonical_snapshot="x", acquired_at="")
        self.assertFalse((self.root / "data/canonical").exists())
        self.assertFalse((self.root / "data/knowledge").exists())
        self.assertFalse((self.root / "data/market").exists())


if __name__ == "__main__": unittest.main()
