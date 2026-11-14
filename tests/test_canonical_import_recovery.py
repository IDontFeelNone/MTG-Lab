"""Physical transaction faults against the actual owning repository API."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import warnings
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repository.canonical import (CanonicalRepository, CanonicalRepositoryError,
                                  CanonicalImportCleanupWarning)

GAME = 'recovery_fixture'
RECORDS = {
    'rarities/common.json': {'id': 'common', 'game_id': GAME, 'name': 'Candidate'},
    'rarities/new.json': {'id': 'new', 'game_id': GAME, 'name': 'New'},
}


def hashes(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


class CanonicalImportRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'games'
        self.current = self.root / GAME
        self.backup = self.root / f'.{GAME}.import-backup'
        self.staging = self.root / f'.{GAME}.import-staging'
        (self.current / 'rarities').mkdir(parents=True)
        for relative, value in {
            'game.json': {'id': GAME, 'name': 'Fictional recovery fixture'},
            'rarities/common.json': {'id': 'common', 'game_id': GAME, 'name': 'Original'},
            'rarities/retained.json': {'id': 'retained', 'game_id': GAME, 'name': 'Retained'},
        }.items():
            (self.current / relative).write_text(json.dumps(value) + '\n')
        self.original = hashes(self.current)

    def apply(self):
        return CanonicalRepository.apply_import(GAME, RECORDS, games_root=self.root)

    def test_pending_backup_blocks_retry_without_touching_recovery_bytes(self):
        self.current.rename(self.backup)
        before = hashes(self.root)
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            self.apply()
        self.assertEqual(hashes(self.root), before)

    def test_final_reload_failure_restores_original_and_keeps_candidate(self):
        initialize = CanonicalRepository.__init__

        def fail_final(reader, game, **kwargs):
            if Path(kwargs['games_root']) == self.root:
                raise OSError('injected final reload failure')
            return initialize(reader, game, **kwargs)

        with patch.object(CanonicalRepository, '__init__', fail_final):
            with self.assertRaises((CanonicalRepositoryError, OSError)):
                self.apply()
        self.assertEqual(hashes(self.current), self.original)
        self.assertTrue((self.staging / GAME / 'rarities/new.json').is_file())

    def assert_original(self):
        self.assertEqual(hashes(self.current), self.original)
        self.assertEqual({x.id for x in CanonicalRepository(GAME, games_root=self.root).rarities},
                         {'common', 'retained'})

    def assert_blocked_repeatedly(self):
        before = hashes(self.root)
        for _ in range(3):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
                self.apply()
            self.assertEqual(hashes(self.root), before)

    def reject_final(self, change=None):
        initialize = CanonicalRepository.__init__

        def reject(reader, game, **kwargs):
            if Path(kwargs['games_root']) == self.root:
                if change:
                    change()
                raise OSError('injected final reload failure')
            return initialize(reader, game, **kwargs)

        return patch.object(CanonicalRepository, '__init__', reject)

    def test_copy_failure_preserves_original_and_removes_own_staging(self):
        with patch('repository.canonical.shutil.copytree', side_effect=OSError('copy fault')):
            with self.assertRaisesRegex(OSError, 'copy fault'):
                self.apply()
        self.assert_original()
        self.assertFalse(self.staging.exists())

    def test_partial_candidate_write_preserves_original(self):
        write = Path.write_text

        def fail(path, text, **kwargs):
            if path == self.staging / GAME / 'rarities/common.json':
                write(path, text[:4], **kwargs)
                raise OSError('partial write fault')
            return write(path, text, **kwargs)

        with patch.object(Path, 'write_text', fail):
            with self.assertRaisesRegex(OSError, 'partial write fault'):
                self.apply()
        self.assert_original()
        self.assertFalse(self.staging.exists())

    def test_staged_initialization_exception_preserves_original(self):
        with patch.object(CanonicalRepository, '__init__', side_effect=OSError('validation fault')):
            with self.assertRaisesRegex(OSError, 'validation fault'):
                self.apply()
        self.assert_original()
        self.assertFalse(self.staging.exists())

    def test_invalid_staged_relationship_is_never_published(self):
        records = {'slots/broken.json': {'id': 'broken', 'name': 'Broken',
                                       'sheet_id': 'missing', 'count': 1}}
        with self.assertRaisesRegex(CanonicalRepositoryError, 'missing Sheet'):
            CanonicalRepository.apply_import(GAME, records, games_root=self.root)
        self.assert_original()
        self.assertFalse(self.staging.exists())

    def test_existing_backup_is_never_cleaned_even_with_valid_current(self):
        shutil.copytree(self.current, self.backup)
        with patch('repository.canonical.shutil.rmtree', side_effect=OSError('must not clean')) as remove:
            self.assert_blocked_repeatedly()
        remove.assert_not_called()
        self.assert_original()
        self.assertEqual(hashes(self.backup), self.original)

    def test_missing_current_with_backup_never_loads_as_empty(self):
        self.current.rename(self.backup)
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            CanonicalRepository(GAME, games_root=self.root)
        self.assert_blocked_repeatedly()
        self.assertEqual(hashes(self.backup), self.original)

    def test_orphan_staging_blocks_import_but_original_remains_readable(self):
        self.staging.mkdir()
        (self.staging / 'retain.txt').write_text('uncertain recovery material')
        self.assert_blocked_repeatedly()
        self.assert_original()

    def test_unmarked_legacy_directory_is_preserved_without_guessing_authority(self):
        orphan = self.root / 'tmp-original-import' / GAME
        shutil.copytree(self.current, orphan)
        self.apply()
        self.assertEqual(hashes(orphan), self.original)
        self.assertTrue((self.current / 'rarities/retained.json').exists())
        # The old implementation's dangerous rename gap has an exact backup.
        self.current.rename(self.backup)
        self.assert_blocked_repeatedly()
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            CanonicalRepository(GAME, games_root=self.root)
        self.assertEqual(hashes(orphan), self.original)

    def test_unrelated_tmp_named_game_is_not_misidentified_as_staging(self):
        other = self.root / 'tmp_other'
        (other / 'cards').mkdir(parents=True)
        (other / 'game.json').write_text(json.dumps({'id': 'tmp_other', 'name': 'Other game'}))
        before = hashes(other)
        CanonicalRepository('tmp_other', games_root=self.root)
        result = CanonicalRepository.apply_import('cards', {
            'rarities/common.json': {'id': 'common', 'game_id': 'cards', 'name': 'Common'}
        }, games_root=self.root)
        self.assertEqual(result.rarities[0].id, 'common')
        self.assertEqual(hashes(other), before)
        self.assert_original()

    def test_original_rename_exception_keeps_original_and_candidate(self):
        rename = Path.rename

        def fail(path, destination):
            if path == self.current:
                raise OSError('original rename fault')
            return rename(path, destination)

        with patch.object(Path, 'rename', fail):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'not committed'):
                self.apply()
        self.assert_original()
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())
        self.assert_blocked_repeatedly()

    def test_promotion_rename_exception_restores_original_and_retains_candidate(self):
        rename = Path.rename

        def fail(path, destination):
            if path == self.staging / GAME:
                raise OSError('promotion fault')
            return rename(path, destination)

        with patch.object(Path, 'rename', fail):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'not committed'):
                self.apply()
        self.assert_original()
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())
        self.assert_blocked_repeatedly()

    def test_compensation_failure_preserves_backup_and_candidate(self):
        rename = Path.rename

        def fail(path, destination):
            if path in (self.staging / GAME, self.backup):
                raise OSError('rename unavailable')
            return rename(path, destination)

        with patch.object(Path, 'rename', fail):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'compensation incomplete'):
                self.apply()
        self.assertEqual(hashes(self.backup), self.original)
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            CanonicalRepository(GAME, games_root=self.root)
        self.assert_blocked_repeatedly()

    def test_changed_valid_candidate_is_not_overwritten_by_compensation(self):
        def change():
            (self.current / 'rarities/foreign.json').write_text(json.dumps(
                {'id': 'foreign', 'game_id': GAME, 'name': 'Foreign change'}))

        with self.reject_final(change):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'compensation incomplete'):
                self.apply()
        self.assertEqual(hashes(self.backup), self.original)
        self.assertIn('foreign', {x.id for x in CanonicalRepository(GAME, games_root=self.root).rarities})
        self.assert_blocked_repeatedly()

    def test_conflicting_valid_destination_preserves_all_generations(self):
        rename = Path.rename

        def interfere(path, destination):
            if path == self.staging / GAME:
                shutil.copytree(self.backup, self.current)
                (self.current / 'rarities/foreign.json').write_text(json.dumps(
                    {'id': 'foreign', 'game_id': GAME, 'name': 'Foreign destination'}))
                raise OSError('foreign destination')
            return rename(path, destination)

        with patch.object(Path, 'rename', interfere):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'compensation incomplete'):
                self.apply()
        self.assertTrue((self.current / 'rarities/foreign.json').exists())
        self.assertEqual(hashes(self.backup), self.original)
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())
        self.assert_blocked_repeatedly()

    def test_change_during_successful_live_load_is_preserved_not_cleaned(self):
        initialize = CanonicalRepository.__init__

        def change(reader, game, **kwargs):
            initialize(reader, game, **kwargs)
            if Path(kwargs['games_root']) == self.root:
                (self.current / 'rarities/foreign.json').write_text(json.dumps(
                    {'id': 'foreign', 'game_id': GAME, 'name': 'Concurrent change'}))

        with patch.object(CanonicalRepository, '__init__', change):
            with self.assertRaisesRegex(CanonicalRepositoryError, 'compensation incomplete'):
                self.apply()
        self.assertTrue((self.current / 'rarities/foreign.json').exists())
        self.assertEqual(hashes(self.backup), self.original)
        self.assert_blocked_repeatedly()

    def test_backup_is_usable_during_final_verification(self):
        initialize = CanonicalRepository.__init__
        observed = []

        def check(reader, game, **kwargs):
            if Path(kwargs['games_root']) == self.root:
                observed.append(hashes(self.backup))
            return initialize(reader, game, **kwargs)

        with patch.object(CanonicalRepository, '__init__', check):
            result = self.apply()
        self.assertEqual(observed, [self.original])
        self.assertFalse(result.import_cleanup_pending)
        self.assertFalse(self.backup.exists())
        self.assertFalse(self.staging.exists())

    def cleanup_fault(self, partial=False):
        remove = shutil.rmtree

        def fail(path, *args, **kwargs):
            if Path(path) == self.backup:
                if partial:
                    (self.backup / 'rarities/common.json').unlink()
                raise OSError('backup cleanup fault')
            return remove(path, *args, **kwargs)

        return patch('repository.canonical.shutil.rmtree', fail)

    def test_backup_removal_failure_returns_verified_commit_with_warning(self):
        with self.cleanup_fault(), self.assertWarnsRegex(CanonicalImportCleanupWarning, 'COMMITTED'):
            result = self.apply()
        self.assertEqual({x.id for x in result.rarities}, {'common', 'new', 'retained'})
        self.assertEqual(hashes(self.backup), self.original)
        self.assertEqual(result.import_cleanup_pending, (self.backup.name, self.staging.name))
        self.assert_blocked_repeatedly()

    def test_partial_backup_cleanup_never_rolls_back_verified_publication(self):
        with self.cleanup_fault(partial=True), self.assertWarns(CanonicalImportCleanupWarning):
            result = self.apply()
        self.assertEqual({x.id: x.name for x in result.rarities}['common'], 'Candidate')
        self.assertFalse((self.backup / 'rarities/common.json').exists())
        self.assertTrue((self.current / 'rarities/new.json').exists())
        self.assert_blocked_repeatedly()

    def test_warnings_as_errors_cannot_turn_commit_into_abort(self):
        with self.cleanup_fault(), warnings.catch_warnings():
            warnings.simplefilter('error', CanonicalImportCleanupWarning)
            result = self.apply()
        self.assertTrue(result.import_cleanup_pending)
        self.assertTrue((self.current / 'rarities/new.json').exists())

    def test_staging_cleanup_failure_is_committed_and_blocks_next_import(self):
        rmdir = Path.rmdir

        def fail(path):
            if path == self.staging:
                raise OSError('staging cleanup fault')
            return rmdir(path)

        with patch.object(Path, 'rmdir', fail), self.assertWarns(CanonicalImportCleanupWarning):
            result = self.apply()
        self.assertEqual(result.import_cleanup_pending, (self.staging.name,))
        self.assertFalse(self.backup.exists())
        self.assert_blocked_repeatedly()

    def test_unexpected_staging_content_is_never_recursively_deleted(self):
        initialize = CanonicalRepository.__init__

        def leave(reader, game, **kwargs):
            initialize(reader, game, **kwargs)
            if Path(kwargs['games_root']) == self.root:
                (self.staging / 'recovery-material.txt').write_text('preserve')

        with patch.object(CanonicalRepository, '__init__', leave), self.assertWarns(CanonicalImportCleanupWarning):
            result = self.apply()
        self.assertTrue(result.import_cleanup_pending)
        self.assertEqual((self.staging / 'recovery-material.txt').read_text(), 'preserve')
        self.assert_blocked_repeatedly()

    def test_abort_cleanup_failure_keeps_primary_error_and_staging(self):
        with patch('repository.canonical.shutil.copytree', side_effect=OSError('primary copy fault')):
            with patch('repository.canonical.shutil.rmtree', side_effect=OSError('cleanup fault')):
                with self.assertRaisesRegex(OSError, 'primary copy fault') as caught:
                    self.apply()
        self.assertIn('Recovery required', caught.exception.__notes__[0])
        self.assert_original()
        self.assert_blocked_repeatedly()

    def test_fresh_import_final_failure_is_not_mistaken_for_empty_success(self):
        shutil.rmtree(self.current)
        with self.reject_final():
            with self.assertRaisesRegex(CanonicalRepositoryError, 'not committed'):
                self.apply()
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            CanonicalRepository(GAME, games_root=self.root)
        self.assert_blocked_repeatedly()
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())

    def test_success_preserves_untouched_records_inputs_and_deterministic_retry(self):
        before = deepcopy(RECORDS)
        result = self.apply()
        self.assertEqual(RECORDS, before)
        self.assertEqual({x.id for x in result.rarities}, {'common', 'new', 'retained'})
        self.assertEqual(hashes(self.current)['rarities/retained.json'], self.original['rarities/retained.json'])
        state = hashes(self.current)
        self.apply()
        self.assertEqual(hashes(self.current), state)
        self.assertFalse(self.staging.exists())
        self.assertFalse(self.backup.exists())

    def test_legitimate_empty_new_game_remains_supported(self):
        result = CanonicalRepository('new_game', games_root=self.root)
        self.assertFalse(result.cards)
        result = CanonicalRepository.apply_import('new_game', {
            'rarities/common.json': {'id': 'common', 'game_id': 'new_game', 'name': 'Common'}
        }, games_root=self.root)
        self.assertEqual(result.rarities[0].name, 'Common')
        self.assert_original()

    def test_invalid_relative_path_never_mutates_current(self):
        with self.assertRaisesRegex(CanonicalRepositoryError, 'Unsafe canonical path'):
            CanonicalRepository.apply_import(GAME, {'../escape.json': {}}, games_root=self.root)
        self.assert_original()
        self.assertFalse(self.staging.exists())

    def abrupt(self, boundary):
        code = '''import json, os, sys, shutil
from pathlib import Path
from unittest.mock import patch
from repository.canonical import CanonicalRepository
root=Path(sys.argv[1]);game=sys.argv[2];boundary=sys.argv[3];records=json.loads(sys.argv[4])
current=root/game;backup=root/('.'+game+'.import-backup');staging=root/('.'+game+'.import-staging')
rename=Path.rename;copy=shutil.copytree;remove=shutil.rmtree

def cut_rename(path,destination):
    result=rename(path,destination)
    if boundary=='between' and path==current and destination==backup:os._exit(86)
    if boundary=='promoted' and path==staging/game:os._exit(86)
    return result

def cut_copy(source,destination,*args,**kwargs):
    result=copy(source,destination,*args,**kwargs)
    if boundary=='copied' and source==current:os._exit(86)
    return result

def cut_remove(path,*args,**kwargs):
    result=remove(path,*args,**kwargs)
    if boundary=='cleanup' and path==backup:os._exit(86)
    return result
with patch.object(Path,'rename',cut_rename),patch('repository.canonical.shutil.copytree',cut_copy),patch('repository.canonical.shutil.rmtree',cut_remove):
    CanonicalRepository.apply_import(game,records,games_root=root)
os._exit(0)
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, str(self.root), GAME,
                                 boundary, json.dumps(RECORDS)], capture_output=True,
                                env={**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)}, timeout=20)
        self.assertEqual(result.returncode, 86, result.stderr.decode())

    def test_abrupt_between_renames_blocks_read_and_every_retry(self):
        self.abrupt('between')
        self.assertFalse(self.current.exists())
        self.assertEqual(hashes(self.backup), self.original)
        with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
            CanonicalRepository(GAME, games_root=self.root)
        self.assert_blocked_repeatedly()
        self.assertTrue((self.staging / GAME / 'rarities/new.json').exists())

    def test_abrupt_after_copy_preserves_current_and_orphan(self):
        self.abrupt('copied')
        self.assert_original()
        self.assertEqual(hashes(self.staging / GAME), self.original)
        self.assert_blocked_repeatedly()

    def test_abrupt_after_promotion_preserves_both_generations(self):
        self.abrupt('promoted')
        self.assertEqual(hashes(self.backup), self.original)
        self.assertTrue((self.current / 'rarities/new.json').exists())
        self.assertEqual({x.id for x in CanonicalRepository(GAME, games_root=self.root).rarities},
                         {'common', 'new', 'retained'})
        self.assert_blocked_repeatedly()

    def test_abrupt_after_cleanup_retains_verified_candidate_and_staging_guard(self):
        self.abrupt('cleanup')
        self.assertFalse(self.backup.exists())
        self.assertTrue((self.current / 'rarities/new.json').exists())
        self.assert_blocked_repeatedly()

    def test_operator_verified_copy_and_archival_enable_safe_retry(self):
        self.abrupt('between')
        recovery_root = Path(self.temp.name) / 'verified-copy'
        shutil.copytree(self.backup, recovery_root / GAME)
        self.assertEqual(hashes(recovery_root / GAME), self.original)
        self.assertEqual({x.id for x in CanonicalRepository(GAME, games_root=recovery_root).rarities},
                         {'common', 'retained'})
        self.assert_blocked_repeatedly()
        self.backup.rename(self.current)
        archive = Path(self.temp.name) / 'preserved-candidate'
        self.staging.rename(archive)
        self.assert_original()
        self.apply()
        self.assertTrue((self.current / 'rarities/retained.json').exists())
        self.assertTrue((archive / GAME / 'rarities/new.json').exists())

    def test_cooperating_second_import_cannot_enter_owned_staging(self):
        copy = shutil.copytree
        checked = []

        def observe(source, destination, *args, **kwargs):
            if source == self.current:
                with self.assertRaisesRegex(CanonicalRepositoryError, 'recovery'):
                    self.apply()
                checked.append(True)
            return copy(source, destination, *args, **kwargs)

        with patch('repository.canonical.shutil.copytree', observe):
            self.apply()
        self.assertEqual(checked, [True])
        self.assertTrue((self.current / 'rarities/retained.json').exists())

    def test_cleanup_keyboard_interrupt_explicitly_identifies_verified_commit(self):
        remove = shutil.rmtree

        def interrupt(path, *args, **kwargs):
            if Path(path) == self.backup:
                raise KeyboardInterrupt('cleanup interrupted')
            return remove(path, *args, **kwargs)

        with patch('repository.canonical.shutil.rmtree', interrupt):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.apply()
        self.assertIn('COMMITTED and verified', caught.exception.__notes__[0])
        self.assertTrue((self.current / 'rarities/new.json').exists())
        self.assertEqual(hashes(self.backup), self.original)
        self.assert_blocked_repeatedly()


class CanonicalImportSourcePreservationTests(unittest.TestCase):
    def test_exact_delta_reverses_without_changing_historical_pins(self):
        import canonical_import_recovery_preservation as guard
        from pack_simulation_preservation import preceding_bytes
        for name, pin in guard.ledger()['replacements'].items():
            raw = (guard.ROOT / name).read_bytes()
            old = guard.preceding_bytes(name, raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(), pin['old_sha256'])
            self.assertEqual(guard.preceding_bytes(name, old), old)
            # The complete existing chain must accept the current successor.
            self.assertIsInstance(preceding_bytes(name, raw), bytes)
            with self.assertRaises(AssertionError):
                guard.preceding_bytes(name, raw + b'\n# unauthorized drift\n')

    def test_rehashed_ledger_cannot_change_approved_source_scope(self):
        import canonical_import_recovery_preservation as guard
        raw = json.loads(guard.LEDGER.read_text())
        raw['replacements']['src/repository/canonical.py']['new_sha256'] = '0' * 64
        with patch.object(Path, 'read_bytes', return_value=json.dumps(raw).encode()):
            with self.assertRaisesRegex(AssertionError, 'exact canonical import recovery ledger'):
                guard.ledger()


class CanonicalImporterRecoveryIntegrationTests(unittest.TestCase):
    setUp = CanonicalImportRecoveryTests.setUp
    apply = CanonicalImportRecoveryTests.apply
    cleanup_fault = CanonicalImportRecoveryTests.cleanup_fault
    assert_blocked_repeatedly = CanonicalImportRecoveryTests.assert_blocked_repeatedly

    def test_importer_reports_applied_after_verified_cleanup_failure(self):
        from canonical_import import JSONSource, import_dataset
        source = Path(self.temp.name) / 'reviewed.json'
        source.write_text(json.dumps({'schema_version': 'v1', 'game': GAME,
            'source': 'project-authored-fictional', 'source_version': '1',
            'review_status': 'reviewed', 'rarities': [{'id': 'new', 'name': 'New'}]}))
        with self.cleanup_fault(), self.assertWarns(CanonicalImportCleanupWarning):
            report = import_dataset(JSONSource(source), GAME, games_root=self.root)
        self.assertTrue(report.applied)
        self.assertEqual({x.id for x in CanonicalRepository(GAME, games_root=self.root).rarities},
                         {'common', 'new', 'retained'})
        self.assert_blocked_repeatedly()
