"""Actual writers/local bare Git; explicitly simulated GitHub transport only."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from production_evidence.automatic_updates import (
    ADMISSION_VALIDATION_TIMEOUT_SECONDS,
    AutomaticCanonicalUpdate, GitHubPersistence, IsolatedAdmissionTestBoundary,
    admission_publication_inventory, digest,
)
from production_evidence.promotion_readiness import canonical_state_digest
from production_evidence.repository import EvidenceError
import test_automatic_update_owner_workflow as host_fixtures


class FictionalGitHubTransport:
    """TEST DOUBLE: all Git is real/local; every gh response is simulated."""
    def __init__(self, fixture):
        self.fixture = fixture
        self.calls, self.prs = [], []
        self.push_failure = self.pr_failure = self.readback_mismatch = self.wrong_pr = False
        self.compare_mismatch = False
        self.checks = [{'status': 'IN_PROGRESS', 'conclusion': None}]

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        if command[0] == 'git':
            if 'push' in command and self.push_failure:
                return subprocess.CompletedProcess(command, 1, '', 'SIMULATED_PUSH_FAILURE')
            return subprocess.run(command, **kwargs)
        if command[:3] == ['gh', 'pr', 'create']:
            if self.pr_failure:
                return subprocess.CompletedProcess(command, 1, '', 'SIMULATED_PR_CREATE_FAILURE')
            self.prs = [{'number': 1, 'url': 'https://example.invalid/SIMULATED_PR/1'}]
            document = ''
        elif command[:3] == ['gh', 'pr', 'list']:
            document = self.prs
        elif command[:3] == ['gh', 'pr', 'view']:
            head = self.fixture.git('rev-parse', 'HEAD').strip()
            document = {'number': 1, 'url': 'https://example.invalid/SIMULATED_PR/1', 'isDraft': True,
                'state': 'OPEN', 'headRefName': self.fixture.engine().descriptor.destination_branch,
                'baseRefName': 'wrong' if self.wrong_pr else 'main', 'baseRefOid': self.fixture.base,
                'headRefOid': '0'*40 if self.readback_mismatch else head, 'statusCheckRollup': self.checks}
        elif command[:2] == ['gh', 'api'] and '/git/commits/' in command[2]:
            document = {'sha': self.fixture.git('rev-parse', 'HEAD').strip(),
                'parents': [{'sha': self.fixture.base}],
                'tree': {'sha': self.fixture.git('rev-parse', 'HEAD^{tree}').strip()}}
        elif command[:2] == ['gh', 'api'] and '/compare/' in command[2]:
            files = self.fixture.git('diff', '--name-only', self.fixture.base, 'HEAD').splitlines()
            if self.compare_mismatch: files = files[:-1]
            document = {'base_commit': {'sha': self.fixture.base}, 'files': [{'filename': p} for p in files]}
        else:
            raise AssertionError('Unrecognized simulated platform command')
        return subprocess.CompletedProcess(command, 0, json.dumps(document), '')


class ExactPublicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = host_fixtures.OwnerWorkflowEntryTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        (self.root / '.git/info/exclude').write_text('.env\n')
        self.fixture.event.rename(self.root / '.git' / 'fake-platform-event.json')
        self.fixture.event = self.root / '.git' / 'fake-platform-event.json'
        self.fixture.environment['GITHUB_EVENT_PATH'] = str(self.fixture.event)
        # Seed actual nonempty canonical history using the supported writer.
        prior = self.fixture.engine()
        prior.review_boundary = IsolatedAdmissionTestBoundary(self.fixture.temporary)
        prior.execute(stop_after='query_and_analytics_smoke_tests')
        (prior.run_root / 'canonical-pre-state.bytes').rename(self.root / '.git' / 'prior-recovery.bytes')
        self.original_state = (self.root / 'data/canonical/state.json').read_bytes()
        config = deepcopy(prior.config)
        config['target'].update(batch_identifier='fictional-second', destination_branch='canonical-update/fictional-second')
        config['artifacts']['promotion_audit'] = 'audit/second-promotion.json'
        config['artifacts']['candidate_payload'] = 'evidence/second-payload.json'
        payload = json.loads(self.fixture.payload.read_bytes())
        payload['candidate_payloads'] = payload['candidate_payloads'][:2]
        for row in payload['candidate_payloads']:
            row['candidate_identifier'] = row['candidate_identifier'].replace(':1', ':2')
            row['mapped_fields']['card_reference'] = 'c2'
            if row['entity_type'] == 'printing': row['mapped_fields']['uuid'] = 'p2'
        payload['candidate_ids'] = [r['candidate_identifier'] for r in payload['candidate_payloads']]
        self.payload = self.root / 'data/evidence/second-payload.json'
        self.payload.write_text(json.dumps(payload))
        self.new_dependency = self.root / 'data/evidence/new-dependency.json'
        dependency_bytes = b'{"notice": "FICTIONAL public processing and redistribution test notice"}\n'
        config['artifacts']['receipts'].append({'path': 'evidence/new-dependency.json', 'sha256': digest(dependency_bytes)})
        config['target']['candidate_digest'] = digest(payload['candidate_ids'])
        config['integrity'].update(candidate_payload_sha256=digest(self.payload.read_bytes()), expected_candidate_count=2,
                                   canonical_pre_state_digest=canonical_state_digest(self.root / 'data'))
        self.fixture.config.write_text(json.dumps(config))
        tests = self.root / 'tests'
        tests.mkdir()
        (tests / 'test_current_catalog.py').write_text('''import os, unittest
from pathlib import Path
from query.engine import CanonicalQueryEngine
from collection.intelligence import CanonicalCollectionResolver
class ActualCurrentConsumers(unittest.TestCase):
    def test_writer_printing_relationship_and_collection(self):
        if os.environ.get("FICTIONAL_TEST_SUITE_FAILURE") == "1": self.fail("Explicit fictional suite failure")
        data = Path.cwd() / "data"
        query = CanonicalQueryEngine("magic", games_root=data / "canonical/games", data_root=data)
        self.assertEqual(query.related("p2", "printing_card")[0].canonical_identity, "c2")
        resolver = CanonicalCollectionResolver("magic", data)
        result = resolver.resolve({"entries": [{"printing_id": "p2", "language": "en", "quantity": 1}]})["results"][0]
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["card_id"], "c2")
''')
        self.git('add', '.')
        self.git('-c', 'user.name=Fictional fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'Prior simulated history and distinct pending fictional proposal')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.fixture.revision = self.base
        self.new_dependency.write_bytes(dependency_bytes)  # Not in base: must publish this exact dependency.
        self.plan = self.engine().plan()
        self.fixture.plan_id = self.plan['plan_id']
        self.fixture.inputs.update(expected_plan_id=self.plan['plan_id'], reviewed_revision=self.base)
        self.fixture.claims['sha'] = self.fixture.claims['workflow_sha'] = self.base
        self.fixture.write_event()
        remote = self.root / '.git' / 'fictional-origin.git'
        self.git('init', '--bare', '--quiet', str(remote))
        self.git('remote', 'add', 'origin', str(remote))
        self.git('push', '--quiet', 'origin', 'HEAD:refs/heads/main')
        self.transport = FictionalGitHubTransport(self)
        self.boundary = IsolatedAdmissionTestBoundary(self.fixture.temporary)

    def git(self, *args): return self.fixture.git(*args)
    def engine(self): return AutomaticCanonicalUpdate(self.root, self.fixture.config)

    def write(self):
        engine = self.engine()
        engine.review_boundary = self.boundary
        decision = self.boundary.authorize(engine.admission_bindings())
        engine.execute(stop_after='query_and_analytics_smoke_tests')
        return engine, decision

    def publish(self, engine, decision):
        return GitHubPersistence(self.transport).publish_admission(engine, self.plan, self.base, decision,
                                                                  repository='IDontFeelNone/MTG-Lab')

    def test_actual_delta_dependencies_history_and_matching_pr_reuse(self):
        engine, decision = self.write()
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'published', result)
        self.assertEqual(result['push_exit_status'], 0)
        self.assertEqual(result['validation']['tests'], 1)
        self.assertEqual(result['hosted_ci'], 'pending')
        files = result['inventory']['changed_paths']
        self.assertIn('data/canonical/state.json', files)
        self.assertIn('data/audit/second-promotion.json', files)
        self.assertIn('data/evidence/new-dependency.json', files)
        self.assertEqual(sum('/stages/' in p for p in files), 14)
        self.assertFalse(any('backup' in p or p.endswith('.bytes') for p in files))
        before = json.loads(self.original_state)
        after = json.loads((self.root / 'data/canonical/state.json').read_bytes())
        for kind, records in before.items():
            for identity, record in records.items(): self.assertEqual(after[kind][identity], record)
        self.assertEqual(self.git('rev-parse', 'HEAD^').strip(), self.base)
        self.transport.checks = [{'status': 'COMPLETED', 'conclusion': 'ACTION_REQUIRED'}]
        again = self.publish(engine, decision)
        self.assertEqual(again['status'], 'published', again)
        self.assertEqual(again['head'], result['head'])
        self.assertEqual(again['hosted_ci'], 'approval-required')
        self.assertEqual(sum(c[:3] == ['gh', 'pr', 'create'] for c in self.transport.calls), 1)
        self.assertFalse(any('merge' in c or '--force' in c or '--auto' in c for c in self.transport.calls))

    def test_unrelated_record_changes_inside_allowed_state_are_rejected(self):
        engine, decision = self.write()
        path = self.root / 'data/canonical/state.json'
        raw = path.read_bytes()
        for change in ('existing', 'extra'):
            state = json.loads(raw)
            if change == 'existing': state['card']['c1']['values']['name'] = 'Unrelated altered prior Card'
            else: state['card']['unselected'] = {'values': {'name': 'unapproved'}}
            path.write_text(json.dumps(state))
            result = self.publish(engine, decision)
            self.assertEqual(result['status'], 'blocked')
            self.assertIn('exact approved delta', result['error'])
            self.assertFalse(any('push' in c or c[0] == 'gh' for c in self.transport.calls))
        path.write_bytes(raw)

    def test_extra_staged_untracked_ignored_private_and_staged_backup_fail_closed(self):
        engine, decision = self.write()
        for name, staged in (('extra.txt', False), ('data/audit/private_crosswalk.json', True), ('.env', False)):
            with self.subTest(name=name):
                path = self.root / name
                path.write_text('PRIVATE TEST SENTINEL, not personal data')
                if staged: self.git('add', name)
                result = self.publish(engine, decision)
                self.assertEqual(result['status'], 'blocked')
                self.assertIn('unexpected', result['error'])
                if staged: self.git('restore', '--staged', '--', name)
                path.unlink()
        backup = engine.run_root / 'canonical-pre-state.bytes'
        self.git('add', str(backup.relative_to(self.root)))
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('unexpected', result['error'])

    def ignored_historical_summary(self):
        # Same demonstrated path/ignore condition; contents are fictional here.
        name = 'data/validation/production-runs/30649546787/phase109_run_evidence_summary.json'
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = b'{"notice":"FICTIONAL historical validation, not admission evidence"}\n'
        path.write_bytes(raw)
        exclude = self.root / '.git/info/exclude'
        exclude.write_text(exclude.read_text() + name + '\n')
        self.assertEqual(self.git('ls-files', '--others', '--ignored', '--exclude-standard').splitlines(), [name])
        return name, raw

    def test_copied_ignored_history_omitted_from_base_fails_with_exact_diagnostic(self):
        name, raw = self.ignored_historical_summary()
        engine, decision = self.write()
        result = self.publish(engine, decision)
        self.assertEqual((result['status'], result['publication_phase']), ('blocked', 'preflight'))
        report = json.loads(result['error'].split(': ', 1)[1])
        self.assertEqual(report['offenders'], [{'path': name, 'categories': ['ignored']}])
        self.assertEqual((self.root / name).read_bytes(), raw)
        self.assertFalse(any('push' in c or c[0] == 'gh' for c in self.transport.calls))

    def test_explicitly_seeded_tracked_ignored_history_is_preserved_not_added_to_delta(self):
        name, raw = self.ignored_historical_summary()
        # Establish the reviewed fictional base before authorizing/writing. The
        # production inventory gains no exception for this or any ignored file.
        self.git('add', '--force', '--', name)
        self.git('-c', 'user.name=Fictional fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'Seed the exact existing ignored historical summary')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.git('push', '--quiet', 'origin', 'HEAD:refs/heads/main')
        self.plan = self.engine().plan()
        engine, decision = self.write()
        inventory = admission_publication_inventory(engine, self.plan, self.base, decision)
        self.assertNotIn(name, inventory['changed_paths'])
        self.assertNotIn(name, [r['path'] for r in inventory['files']])
        self.assertEqual((self.root / name).read_bytes(), raw)
        self.assertEqual(self.git('show', self.base + ':' + name).encode(), raw)

    def test_artifact_diagnostics_group_categories_backups_and_redact_secret_filenames(self):
        engine, decision = self.write()
        sentinel = 'FICTIONAL FILE CONTENT MUST NOT APPEAR IN DIAGNOSTICS'
        names = {'data/audit/private_crosswalk.json': ['tracked_modification', 'staged'],
                 'unexpected-operator.log': ['untracked'], '.env': ['ignored'],
                 'unexpected\noperator\t.log': ['tracked_modification', 'staged']}
        for name in names:
            (self.root / name).write_text(sentinel)
        self.git('add', '--', 'data/audit/private_crosswalk.json', 'unexpected\noperator\t.log')
        tracked = 'tests/test_current_catalog.py'
        (self.root / tracked).write_text((self.root / tracked).read_text() + '# ' + sentinel + '\n')
        names[tracked] = ['tracked_modification']
        backup = engine.run_root / 'canonical-pre-state.bytes'
        backup_name = backup.relative_to(self.root).as_posix()
        self.git('add', '--', backup_name)
        names[backup_name] = ['tracked_modification', 'staged', 'improperly_staged_recovery_backup']
        credential_name = 'ghp_' + 'FICTIONALCREDENTIAL' * 2
        (self.root / credential_name).write_text(sentinel)
        result = self.publish(engine, decision)
        self.assertEqual((result['status'], result['publication_phase']), ('blocked', 'preflight'))
        error = result['error']
        self.assertNotIn(sentinel, error)
        self.assertNotIn(str(self.root), error)
        self.assertNotIn(credential_name, error)
        self.assertNotIn('\n', error)
        rows = json.loads(error.split(': ', 1)[1])['offenders']
        expected = [{'path': name, 'categories': categories} for name, categories in names.items()]
        expected.append({'path': '[redacted]', 'path_sha256': digest(credential_name.encode()),
                         'categories': ['untracked']})
        self.assertCountEqual(rows, expected)
        self.assertFalse(any('push' in c or c[0] == 'gh' for c in self.transport.calls))

    def test_path_escape_secret_and_private_dependency_bytes_are_rejected(self):
        engine, decision = self.write()
        original = self.new_dependency.read_bytes()
        for raw in (b'{"access_token":"FICTIONAL_SECRET"}', b'{"personal_inventory":["FICTIONAL"]}',
                    b'eyJhbGciOiJSUzI1NiJ9.eyJmaWN0aW9uYWwiOnRydWV9.FICTIONAL_SIGNATURE'):
            self.new_dependency.write_bytes(raw)
            with self.assertRaises(EvidenceError):
                admission_publication_inventory(engine, self.plan, self.base, decision)
        self.new_dependency.write_bytes(original)
        target = self.root / '.git' / 'escaped-dependency.json'
        self.new_dependency.rename(target)
        self.new_dependency.symlink_to(target)
        with self.assertRaises(EvidenceError):
            admission_publication_inventory(engine, self.plan, self.base, decision)

    def test_checksum_valid_sensitive_dependency_still_cannot_be_published(self):
        # A digest authenticates no person and does not turn private fields public.
        raw = b'{"access_token":"FICTIONAL_SECRET_SENTINEL_NOT_A_CREDENTIAL"}\n'
        self.new_dependency.write_bytes(raw)
        config = json.loads(self.fixture.config.read_bytes())
        config['artifacts']['receipts'][-1]['sha256'] = digest(raw)
        self.fixture.config.write_text(json.dumps(config))
        self.git('add', self.fixture.config_name)
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'Distinct fictional proposal: test refusal of sensitive fields')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.git('push', '--quiet', 'origin', 'HEAD:refs/heads/main')
        self.plan = self.engine().plan()
        engine, decision = self.write()
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('secret/private', result['error'])
        self.assertFalse(any('push' in c for c in self.transport.calls))

    def test_existing_read_only_boundary_cli_checks_full_supplied_content(self):
        engine, decision = self.write()
        saved = self.root / '.git/reviewed-plan.json'
        saved.write_text(json.dumps(self.plan))
        result = subprocess.run(['python', str(host_fixtures.ROOT/'scripts/verify_automatic_update_boundary.py'),
            '--repository-root', str(self.root), '--config', str(self.fixture.config), '--plan', str(saved),
            '--base', self.base], capture_output=True, text=True, timeout=30,
            env={**os.environ, 'PYTHONPATH': str(host_fixtures.ROOT/'src'), 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'verified-content-only')
        self.assertFalse(report['execution_authorized'])
        self.assertEqual(report['inventory'], admission_publication_inventory(engine, self.plan, self.base, decision))

    def test_staged_alternate_bytes_and_changed_payload_cannot_be_silently_replaced(self):
        engine, decision = self.write()
        path = self.root / 'data/canonical/state.json'
        raw = path.read_bytes()
        path.write_bytes(raw + b'\n')
        self.git('add', 'data/canonical/state.json')
        path.write_bytes(raw)
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('staged file differs', result['error'])
        path.write_bytes(raw)
        self.payload.write_bytes(self.payload.read_bytes() + b'\n')
        self.assertEqual(self.publish(engine, decision)['status'], 'blocked')

    def test_existing_remote_branch_is_not_overwritten(self):
        engine, decision = self.write()
        self.git('push', '--quiet', 'origin', f'{self.base}:refs/heads/{engine.descriptor.destination_branch}')
        result = self.publish(engine, decision)
        # An existing ref is not treated as permission to replace it.
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        self.assertFalse(any('push' in c for c in self.transport.calls))

    def test_wrong_local_head_and_forbidden_branch_or_base_fail_safely(self):
        from dataclasses import replace
        engine, decision = self.write()
        original = engine.descriptor
        for change in ({'base_branch': 'other'}, {'destination_branch': 'main'}):
            engine.descriptor = replace(original, **change)
            self.assertEqual(self.publish(engine, decision)['status'], 'blocked')
        engine.descriptor = original
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '--allow-empty', '-m', 'Unrelated local head; preserve it')
        head = self.git('rev-parse', 'HEAD').strip()
        result = self.publish(engine, decision)
        self.assertIn('local head/branch', result['error'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), head)
        self.assertFalse(any('push' in c for c in self.transport.calls))

    def test_staged_executable_mode_cannot_hide_inside_an_allowed_filename(self):
        engine, decision = self.write()
        self.git('add', 'data/canonical/state.json')
        self.git('update-index', '--chmod=+x', 'data/canonical/state.json')
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('file mode', result['error'])

    def test_remote_base_drift_after_validation_blocks_before_commit(self):
        engine, decision = self.write()
        validate = GitHubPersistence._required_admission_validation
        def move_after_validation(root):
            result = validate(root)
            self.git('--git-dir', str(self.root / '.git/fictional-origin.git'), 'update-ref',
                     'refs/heads/main', self.git('rev-parse', 'HEAD^').strip())
            return result
        with patch.object(GitHubPersistence, '_required_admission_validation', staticmethod(move_after_validation)):
            result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('moved during validation', result['error'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_moved_remote_base_is_rejected_before_commit(self):
        engine, decision = self.write()
        old = self.git('rev-parse', 'HEAD^').strip()
        self.git('--git-dir', str(self.root / '.git/fictional-origin.git'), 'update-ref', 'refs/heads/main', old)
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('base moved', result['error'])
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)

    def test_push_failure_retains_the_new_local_commit_without_reset(self):
        engine, decision = self.write()
        self.transport.push_failure = True
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked', result)
        self.assertEqual(result['publication_phase'], 'push')
        self.assertEqual(result['push_exit_status'], 1)
        self.assertNotEqual(result['recoverable_local_commit'], self.base)
        self.assertEqual(result['recoverable_local_commit'], self.git('rev-parse', 'HEAD').strip())

    def test_pr_creation_failure_and_readback_mismatch_are_distinct(self):
        engine, decision = self.write()
        self.transport.pr_failure = True
        result = self.publish(engine, decision)
        self.assertEqual(result['publication_phase'], 'pull_request', result)
        self.assertEqual(result['status'], 'blocked')
        head = self.git('rev-parse', 'HEAD').strip()
        self.transport.pr_failure = False
        self.transport.readback_mismatch = True
        result = self.publish(engine, decision)
        self.assertEqual(result['publication_phase'], 'readback', result)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), head)

    def test_wrong_pr_target_or_incomplete_remote_inventory_is_rejected(self):
        engine, decision = self.write()
        self.transport.wrong_pr = True
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('head/base/draft', result['error'])
        self.transport.wrong_pr = False
        self.transport.compare_mismatch = True
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('complete changed-file inventory', result['error'])

    def test_missing_acceptance_and_required_suite_failure_cannot_publish(self):
        engine, decision = self.write()
        test = self.root / 'tests/test_current_catalog.py'
        # Tracked test tampering is rejected as unrelated before the suite.
        test.write_text('raise RuntimeError("FICTIONAL SETUP ERROR")\n')
        self.assertEqual(self.publish(engine, decision)['publication_phase'], 'preflight')
        test.write_bytes(subprocess.check_output(['git', '-C', str(self.root), 'show', f'{self.base}:tests/test_current_catalog.py']))
        engine._checkpoint('query_and_analytics_smoke_tests').unlink()
        self.assertEqual(self.publish(engine, decision)['status'], 'blocked')
        self.assertFalse(any('push' in c for c in self.transport.calls))

    def test_actual_required_suite_failure_retains_diagnostics_and_never_pushes(self):
        engine, decision = self.write()
        with patch.dict(os.environ, {'FICTIONAL_TEST_SUITE_FAILURE': '1'}):
            result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked', result)
        self.assertEqual(result['publication_phase'], 'validation')
        self.assertIn('exit 1', result['error'])
        self.assertIn('FAILED', (self.root / '.git/catalog-admission-validation.log').read_text())
        self.assertFalse(any('push' in c for c in self.transport.calls))

    def test_required_suite_timeout_blocks_publication_and_preserves_writer_output(self):
        engine, decision = self.write()
        before = admission_publication_inventory(engine, self.plan, self.base, decision)
        # Test-only millisecond deadline: the real unittest subprocess and its
        # actual TimeoutExpired exercise publication, without a one-hour sleep.
        with patch('production_evidence.automatic_updates.ADMISSION_VALIDATION_TIMEOUT_SECONDS', 0.001):
            result = self.publish(engine, decision)
        self.assertEqual((result['status'], result['publication_phase']), ('blocked', 'validation'), result)
        self.assertIn('timed out after 0.001 seconds', result['error'])
        self.assertEqual(admission_publication_inventory(engine, self.plan, self.base, decision), before)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        self.assertFalse(engine._checkpoint('branch_and_pull_request_persistence').exists())
        self.assertFalse(any('push' in c or c[0] == 'gh' for c in self.transport.calls))

    def seed_validation_cache_probe(self):
        # Fictional tracked inputs are established before planning/authorization.
        # The real suite exercises explicit main-process compilation and a child
        # that enables caching while inheriting the controlled destination.
        files = {
            'src/fictional_cache_main.py': 'VALUE = "FICTIONAL_MAIN"\n',
            'src/fictional_cache_child.py': 'VALUE = "FICTIONAL_CHILD"\n',
            'tests/test_validation_cache_probe.py': '''import json, os, py_compile, subprocess, sys, unittest
from pathlib import Path
class ActualValidationCacheProbe(unittest.TestCase):
    def test_main_and_inherited_child_cache_locations(self):
        root = Path.cwd()
        cache = Path(sys.pycache_prefix)
        self.assertTrue(cache.is_relative_to(root / ".git"))
        self.assertEqual(cache.stat().st_mode & 0o777, 0o700)
        self.assertTrue(sys.dont_write_bytecode)
        main = Path(py_compile.compile(str(root / "src/fictional_cache_main.py"), doraise=True))
        self.assertTrue(main.is_file())
        self.assertTrue(main.is_relative_to(cache))
        command = [sys.executable, "-c", "import json, sys; sys.path.insert(0, 'src'); import fictional_cache_child as m; print(json.dumps({'prefix': sys.pycache_prefix, 'cached': m.__cached__, 'disabled': sys.dont_write_bytecode, 'value': m.VALUE}))"]
        child = subprocess.run(command, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "0"},
                               check=True, capture_output=True, text=True)
        result = json.loads(child.stdout)
        self.assertEqual(result["prefix"], str(cache))
        self.assertFalse(result["disabled"])
        self.assertEqual(result["value"], "FICTIONAL_CHILD")
        child_cache = Path(result["cached"])
        self.assertTrue(child_cache.is_file())
        self.assertTrue(child_cache.is_relative_to(cache))
        forbidden = os.environ.get("FICTIONAL_UNCONTROLLED_ARTIFACT")
        if forbidden:
            path = root / forbidden
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"FICTIONAL uncontrolled artifact must remain excluded")
''',
        }
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git('add', '--', *sorted(files))
        self.git('-c', 'user.name=Fictional fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'Establish fictional validation cache probes')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.git('push', '--quiet', 'origin', 'HEAD:refs/heads/main')
        self.plan = self.engine().plan()

    def test_real_validation_main_and_inherited_child_use_private_cache_without_tree_artifacts(self):
        self.seed_validation_cache_probe()
        engine, decision = self.write()
        # An inherited destination must not select a publishable directory.
        with patch.dict(os.environ, {'PYTHONPYCACHEPREFIX': str(self.root / 'unsafe-cache')}):
            result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'published', result)
        self.assertEqual(result['validation']['tests'], 2)
        self.assertFalse((self.root / 'unsafe-cache').exists())
        caches = list((self.root / '.git').glob('catalog-admission-pycache-*'))
        self.assertEqual(len(caches), 1)
        self.assertTrue(list(caches[0].rglob('fictional_cache_main.*.pyc')))
        self.assertTrue(list(caches[0].rglob('fictional_cache_child.*.pyc')))
        self.assertFalse([p for p in self.root.rglob('*') if not p.is_relative_to(self.root / '.git')
                          and (p.name == '__pycache__' or p.suffix == '.pyc')])
        self.assertFalse(any('pycache' in name or name.endswith('.pyc')
                             for name in result['inventory']['changed_paths']))

    def assert_uncontrolled_validation_artifact_rejected(self, name):
        self.seed_validation_cache_probe()
        exclude = self.root / '.git/info/exclude'
        exclude.write_text(exclude.read_text() + name + '\n')
        engine, decision = self.write()
        with patch.dict(os.environ, {'FICTIONAL_UNCONTROLLED_ARTIFACT': name}):
            result = self.publish(engine, decision)
        self.assertEqual((result['status'], result['publication_phase']), ('blocked', 'validation'), result)
        report = json.loads(result['error'].split(': ', 1)[1])
        self.assertEqual(report['offenders'], [{'path': name, 'categories': ['ignored']}])
        self.assertTrue((self.root / name).is_file())
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)
        self.assertFalse(any('push' in c or c[0] == 'gh' for c in self.transport.calls))
        self.assertIn('Ran 2 tests', (self.root / '.git/catalog-admission-validation.log').read_text())

    def test_post_validation_unrelated_ignored_file_still_blocks(self):
        self.assert_uncontrolled_validation_artifact_rejected('unrelated-validation.log')

    def test_post_validation_uncontrolled_pyc_like_file_still_blocks(self):
        self.assert_uncontrolled_validation_artifact_rejected('src/__pycache__/forged.cpython-312.pyc')

    def test_simulated_capability_cannot_publish_to_a_network_remote(self):
        engine, decision = self.write()
        self.git('remote', 'set-url', 'origin', 'https://github.com/IDontFeelNone/MTG-Lab.git')
        result = self.publish(engine, decision)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('disposable local bare remote', result['error'])
        self.assertFalse(any('ls-remote' in c for c in self.transport.calls))

    def test_actual_entry_to_writer_validation_and_simulated_publication(self):
        entry = host_fixtures.ENTRY
        factory = lambda engine, plan, sha: host_fixtures.SimulatedPlatformBoundary(engine, plan, sha, self.fixture.temporary)
        output = io.StringIO()
        with patch.dict(os.environ, self.fixture.environment), redirect_stdout(output), \
             patch.object(entry, '_signed_github_claims', return_value=self.fixture.claims), \
             patch.object(entry, 'SOURCE_POLICY_CLEARED_PLANS', frozenset({self.plan['plan_id']})), \
             patch.object(entry, 'GitHubOwnerReviewBoundary', factory), \
             patch.object(entry, 'GitHubPersistence', return_value=GitHubPersistence(self.transport)):
            code = entry.main(['admit', '--github-owner-entry', '--publish-admission-pr', '--repository-root', str(self.root),
                '--config', self.fixture.config_name, '--expected-plan-id', self.plan['plan_id'], '--reviewed-revision', self.base])
        self.assertEqual(code, 0, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['status'], 'published')

    def test_planning_and_missing_authorization_never_invoke_publication(self):
        entry = host_fixtures.ENTRY
        with patch.object(entry, 'GitHubPersistence', side_effect=AssertionError('publication invoked')):
            self.assertEqual(self.fixture.invoke('plan')[0], 0)
            output = io.StringIO()
            with redirect_stdout(output):
                code = entry.main(['admit', '--github-owner-entry', '--publish-admission-pr', '--repository-root', str(self.root),
                                  '--config', self.fixture.config_name])
            self.assertEqual(code, 1)


class AdmissionValidationTimeoutPolicyTests(unittest.TestCase):
    """Duration/result doubles test policy; they are not real full-suite runs."""
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mtglab-validation-policy-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / '.git').mkdir()
        self.command = ['python', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v']

    def test_reviewed_bounded_policy_accepts_suite_duration_over_1800(self):
        output = '\nRan 7 tests in 1853.000s\n\nOK\n'

        def simulated_elapsed_suite(command, **kwargs):
            self.assertEqual(command, self.command)
            self.assertEqual(kwargs['cwd'], self.root)
            self.assertEqual(kwargs['timeout'], 3600)
            self.assertEqual(ADMISSION_VALIDATION_TIMEOUT_SECONDS, 3600)
            # Exercise the old failure threshold without sleeping for 30 minutes.
            if kwargs['timeout'] < 1853:
                raise subprocess.TimeoutExpired(command, kwargs['timeout'])
            self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
            self.assertTrue(Path(kwargs['env']['PYTHONPYCACHEPREFIX']).is_relative_to(self.root / '.git'))
            return subprocess.CompletedProcess(command, 0, '', output)

        with patch('production_evidence.automatic_updates.subprocess.run', side_effect=simulated_elapsed_suite):
            result = GitHubPersistence._required_admission_validation(self.root)
        self.assertEqual(result, {'exit_status': 0, 'tests': 7, 'log_sha256': digest(output.encode())})
        self.assertEqual((self.root / '.git/catalog-admission-validation.log').read_text(), output)

    def test_nonzero_incomplete_zero_count_or_missing_final_success_still_fail(self):
        cases = [(1, '\nRan 7 tests in 1.000s\n\nOK\n'),
                 (0, '\nRan 7 tests in 1.000s\n\nFAILED (failures=1)\n'),
                 (0, '\nOK\n'), (0, '\nRan 0 tests in 0.000s\n\nOK\n'),
                 (0, '\nRan 7 tests in 1.000s\n')]
        for returncode, output in cases:
            with self.subTest(returncode=returncode, output=output), \
                    patch('production_evidence.automatic_updates.subprocess.run',
                          return_value=subprocess.CompletedProcess(self.command, returncode, '', output)):
                with self.assertRaisesRegex(EvidenceError, 'failed or incomplete'):
                    GitHubPersistence._required_admission_validation(self.root)
                self.assertEqual((self.root / '.git/catalog-admission-validation.log').read_text(), output)

    def test_timeout_partial_success_text_is_not_a_terminal_validation_result(self):
        error = subprocess.TimeoutExpired(self.command, ADMISSION_VALIDATION_TIMEOUT_SECONDS,
                                         output='\nRan 7 tests in 3600.001s\n\nOK\n')
        with patch('production_evidence.automatic_updates.subprocess.run', side_effect=error):
            with self.assertRaises(subprocess.TimeoutExpired):
                GitHubPersistence._required_admission_validation(self.root)


class ExpandedInventoryPreflightTests(unittest.TestCase):
    def test_actual_retained_writer_preflight_without_full_suite_or_publication(self):
        from publication_validation_regression import ExpandedPublicationValidationRegression
        fixture = ExpandedPublicationValidationRegression(methodName='runTest')
        self.addCleanup(fixture.doCleanups)
        engine, plan, decision = fixture.prepare_writer_expansion()
        inventory = admission_publication_inventory(engine, plan, fixture.base, decision)
        self.assertTrue(inventory['existing_records_preserved'])
        self.assertEqual(inventory['candidate_counts_by_type'], {'card': 270, 'printing': 270, 'identifier': 270})
        self.assertIn('data/canonical/state.json', inventory['changed_paths'])
        history = 'data/validation/production-runs/30649546787/phase109_run_evidence_summary.json'
        self.assertNotIn(history, inventory['changed_paths'])
        self.assertIn(history, fixture.git('ls-files').splitlines())
        self.assertEqual((fixture.root / history).read_bytes(),
                         subprocess.check_output(['git', 'show', fixture.base + ':' + history], cwd=fixture.root))
        backup = engine.run_root / 'canonical-pre-state.bytes'
        self.assertEqual(inventory['excluded_local_recovery_backup'], backup.relative_to(fixture.root).as_posix())
        self.assertNotIn(inventory['excluded_local_recovery_backup'], inventory['changed_paths'])
        self.assertFalse((fixture.root / '.git/catalog-admission-validation.log').exists())
        self.assertEqual(fixture.git('rev-parse', 'HEAD').strip(), fixture.base)


class PendingFirstUseTests(unittest.TestCase):
    def test_exact_recommendation_evidence_and_nine_holds_remain_pending(self):
        root = host_fixtures.ROOT
        config = json.loads((root/'config/automatic_updates/mb2-ordinary-810-pending.json').read_bytes())
        selection = config['candidate_selection']
        raw = (root/selection['path']).read_bytes()
        self.assertEqual(digest(raw), selection['sha256'])
        self.assertEqual(digest(json.loads(raw)), 'f63585f4a023e2b81656a4cca0c6811a7d598e45f065633c3a11d9a9a2b5d500')
        packet = root/'reference-reviews/mb2-reference-coverage/structured-2026-10-13/candidate-preparation.json'
        candidates = json.loads(packet.read_bytes())['candidates']
        self.assertEqual(len(candidates), 819)
        self.assertTrue(all(c['payload']['review_status']=='pending' for c in candidates))
        self.assertEqual(set(selection['held_candidate_ids']),
            {c['payload']['candidate_identifier'] for c in candidates} - set(json.loads(raw)))
        self.assertEqual(len(selection['held_candidate_ids']), 9)
        self.assertEqual(selection['counts_by_type'], {'card':270,'printing':270,'identifier':270})
        for item in config['retained_evidence_files']:
            evidence = (root/item['path']).read_bytes()
            self.assertEqual(len(evidence), item['byte_length'])
            self.assertEqual(digest(evidence), item['sha256'])
        self.assertEqual(config['launch_state'], 'pending')
        self.assertIsNone(config['artifacts']['candidate_payload'])
        self.assertFalse(host_fixtures.ENTRY.SOURCE_POLICY_CLEARED_PLANS)

    def test_pending_configuration_is_explicitly_blocked_without_authority_or_writes(self):
        output = io.StringIO()
        with redirect_stdout(output), patch.object(host_fixtures.ENTRY, 'GitHubPersistence',
                                                  side_effect=AssertionError('publication invoked')):
            code = host_fixtures.ENTRY.main(['--config', str(host_fixtures.ROOT/'config/automatic_updates/mb2-ordinary-810-pending.json')])
        self.assertEqual(code, 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('pending first-use configuration', result['error'])


if __name__ == '__main__': unittest.main()
