import json
import tempfile
import unittest
from pathlib import Path

from canonical import Game, SheetEntry
from repository.canonical import CanonicalRepository, CanonicalRepositoryError


class CanonicalRepositoryTests(unittest.TestCase):
    def _root(self, directory):
        root = Path(directory) / "games"
        game = root / "test_game"
        game.mkdir(parents=True)
        (game / "game.json").write_text(json.dumps({"id": "test_game", "name": "Test Game"}))
        return root, game

    @staticmethod
    def _write(game, kind, name, value):
        path = game / kind
        path.mkdir(exist_ok=True)
        (path / name).write_text(json.dumps(value), encoding="utf-8")

    def test_loads_generic_game_and_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root, game = self._root(directory)
            self._write(game, "finishes", "nonfoil.json",
                        {"id": "nonfoil", "game_id": "test_game", "name": "Nonfoil"})
            repository = CanonicalRepository("test_game", games_root=root)
            self.assertIsInstance(repository.game, Game)
            self.assertEqual(repository.finishes[0].name, "Nonfoil")
            self.assertEqual(repository.cards, ())

    def test_duplicate_ids_fail_deterministically(self):
        with tempfile.TemporaryDirectory() as directory:
            root, game = self._root(directory)
            record = {"id": "foil", "game_id": "test_game", "name": "Foil"}
            self._write(game, "finishes", "a.json", record)
            self._write(game, "finishes", "b.json", record)
            with self.assertRaisesRegex(CanonicalRepositoryError,
                                        "Duplicate Finish identifier: foil"):
                CanonicalRepository("test_game", games_root=root)

    def test_missing_required_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, game = self._root(directory)
            self._write(game, "treatments", "bad.json", {"id": "borderless"})
            with self.assertRaisesRegex(CanonicalRepositoryError,
                                        "missing required fields: game_id, name"):
                CanonicalRepository("test_game", games_root=root)

    def test_broken_relationship_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, game = self._root(directory)
            self._write(game, "slots", "rare.json",
                        {"id": "rare", "name": "Rare", "sheet_id": "missing", "count": 1})
            with self.assertRaisesRegex(CanonicalRepositoryError,
                                        "references missing Sheet missing"):
                CanonicalRepository("test_game", games_root=root)

    def test_invalid_product_definition_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, game = self._root(directory)
            self._write(game, "slots", "rare.json",
                        {"id": "rare", "name": "Rare", "sheet_id": "sheet", "count": 0})
            with self.assertRaisesRegex(CanonicalRepositoryError, "count must be positive"):
                CanonicalRepository("test_game", games_root=root)

    def test_sheet_entries_are_typed_values(self):
        self.assertEqual(SheetEntry("printing", 2).weight, 2)


if __name__ == "__main__":
    unittest.main()
