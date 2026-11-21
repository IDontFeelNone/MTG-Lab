"""Bounded CI routing, actual-checkout evidence and fail-closed regressions."""
import copy
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ci_merge_tree', ROOT/'scripts/ci_merge_tree.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
BASE, HEAD, MERGE, TESTED, TREE, WRITER = (c*40 for c in '123456')
REPOSITORY = 'example/project'


def receipt():
    return dict(actual_writer_card_count=654, simulated_platform_only=True,
                published_to='disposable_local_bare_remote', published_head=WRITER, readback_head=WRITER,
                nested_discovery=dict(tests=3561, skipped=31, log_sha256='a'*64),
                validation=dict(exit_status=0, tests=3561, log_sha256='a'*64))


def log(value=None):
    lines = ['[command]/usr/bin/git log -1 --format=%H', TESTED,
             'Ran 3561 tests in 123.456s', 'OK (skipped=31)',
             json.dumps(value if value is not None else receipt(), sort_keys=True),
             'Ran 1 test in 234.567s', 'OK']
    return '\n'.join('2026-11-21T01:00:00.0000000Z '+line for line in lines)


class API:
    def __init__(self):
        self.calls = []
        self.prs = [dict(number=42, merged_at='2026-11-21T02:00:00Z', merge_commit_sha=MERGE,
                         head=dict(sha=HEAD), base=dict(sha=BASE, ref='main', repo=dict(full_name=REPOSITORY)))]
        self.runs = dict(total_count=1, workflow_runs=[dict(id=20, event='pull_request', path=ci.WORKFLOW,
                         head_sha=HEAD, repository=dict(full_name=REPOSITORY), status='completed', conclusion='success')])
        self.jobs = dict(total_count=1, jobs=[dict(id=30, name='test', status='completed', conclusion='success',
                         completed_at='2026-11-21T01:59:00Z', steps=[dict(name=name,status='completed',conclusion='success')
                         for name in (ci.DISCOVERY,ci.PUBLICATION)])])
        self.log = log()
        self.commit = dict(sha=TESTED, tree=dict(sha=TREE), parents=[dict(sha=BASE),dict(sha=HEAD)])

    def get(self, path, *, text=False):
        self.calls.append((path,text))
        if path.startswith('/commits/'):return self.prs
        if path.startswith('/actions/workflows/'):return self.runs
        if path.startswith('/actions/runs/'):return self.jobs
        if path.startswith('/actions/jobs/'):return self.log
        if path.startswith('/git/commits/'):return self.commit
        raise AssertionError(path)


class CIWorkflowEfficiencyTests(unittest.TestCase):
    def result(self, api=None, **overrides):
        args = dict(event_name='push', event=dict(ref='refs/heads/main',before=BASE,after=MERGE),
                    repository=REPOSITORY,commit=MERGE,tree=TREE,parents=[BASE,HEAD],
                    paths=['src/probability/draw_access.py'],api=api or API())
        args.update(overrides)
        return ci.decide(**args)

    def test_exact_tested_tree_is_reused_with_auditable_writer_receipt(self):
        api=API();value=self.result(api)
        self.assertFalse(value['full']);self.assertEqual(len(api.calls),5)
        self.assertEqual(value['evidence']['tested_commit'],TESTED)
        self.assertEqual(value['evidence']['validation']['writer'],receipt())

    def test_complete_discovery_without_skips_can_reuse(self):
        api=API();api.log=api.log.replace('OK (skipped=31)','OK')
        self.assertFalse(self.result(api)['full'])

    def test_publication_wrapper_summary_is_required_and_ordered(self):
        for raw in (log().replace('Ran 1 test in 234.567s',''),
                    log().replace('Ran 1 test in 234.567s','Ran 0 tests in 234.567s'),
                    '\n'.join(reversed(log().splitlines()))):
            api=API();api.log=raw;self.assertTrue(self.result(api)['full'])

    def test_pr_and_manual_runs_always_full_without_api_access(self):
        for event in ('pull_request','workflow_dispatch','unknown'):
            api=API();self.assertTrue(self.result(api,event_name=event)['full']);self.assertEqual(api.calls,[])

    def test_direct_batched_tag_and_malformed_pushes_are_full(self):
        for overrides in (dict(parents=[BASE]),dict(parents=[]),dict(parents=[BASE,HEAD,TESTED]),
                          dict(event=dict(ref='refs/heads/main',before=HEAD,after=MERGE)),
                          dict(event=dict(ref='refs/tags/v1',before=BASE,after=MERGE)),
                          dict(event=dict(ref='refs/heads/main',before=BASE,after=HEAD))):
            api=API();self.assertTrue(self.result(api,**overrides)['full']);self.assertEqual(api.calls,[])

    def test_high_risk_boundaries_are_full_without_api(self):
        names=['src/canonical_import/pipeline.py','data/canonical/state.json','src/ingestion/storage.py',
               'src/repository/snapshots.py','src/production_evidence/automatic_updates.py',
               'tests/test_rollback.py','tests/test_recovery.py','reference-reviews/source/permission-matrix.json',
               'docs/GOVERNANCE.md','docs/ARCHITECTURE.md','docs/DECISIONS.md','src/schemas/v1/card.schema.json',
               'scripts/ci_merge_tree.py','.github/workflows/python-validation.yml','release-notes.md']
        for name in names:
            with self.subTest(path=name):
                api=API();self.assertTrue(self.result(api,paths=[name])['full']);self.assertEqual(api.calls,[])

    def test_analytical_artifact_schema_alone_is_not_canonical_migration(self):
        self.assertFalse(self.result(paths=['src/schemas/v1/portable-deck-investigation.schema.json'])['full'])

    def test_tree_difference_refuses_reuse(self):
        api=API();api.commit['tree']['sha']=HEAD;self.assertTrue(self.result(api)['full'])

    def test_reversed_or_changed_tested_parents_refuse_reuse(self):
        for parents in ([HEAD,BASE],[BASE,MERGE],[BASE]):
            api=API();api.commit['parents']=[dict(sha=p) for p in parents]
            self.assertTrue(self.result(api)['full'])

    def test_missing_unknown_or_ambiguous_pr_refuses(self):
        api=API();original=copy.deepcopy(api.prs)
        for rows in ([],original*2,[dict(original[0],merge_commit_sha=HEAD)]):
            api=API();api.prs=rows;self.assertTrue(self.result(api)['full'])

    def test_wrong_pr_base_head_or_repository_refuses(self):
        for key,value in (('sha',HEAD),('ref','another'),('repo',dict(full_name='foreign/project'))):
            api=API();api.prs[0]['base'][key]=value;self.assertTrue(self.result(api)['full'])
        api=API();api.prs[0]['head']['sha']=BASE;self.assertTrue(self.result(api)['full'])

    def test_pending_failed_cancelled_and_timed_out_run_refuse(self):
        for status,conclusion in (('in_progress',None),('queued',None),('completed','failure'),
                                  ('completed','cancelled'),('completed','timed_out'),('completed',None)):
            api=API();api.runs['workflow_runs'][0].update(status=status,conclusion=conclusion)
            self.assertTrue(self.result(api)['full'])

    def test_old_success_cannot_hide_a_newer_failure(self):
        api=API();api.runs['workflow_runs'].append(dict(api.runs['workflow_runs'][0],id=21,conclusion='failure'))
        api.runs['total_count']=2;self.assertTrue(self.result(api)['full'])

    def test_branch_push_wrong_workflow_and_foreign_run_refuse(self):
        for key,value in (('event','push'),('path','other.yml'),('head_sha',BASE),
                          ('repository',dict(full_name='foreign/project'))):
            api=API();api.runs['workflow_runs'][0][key]=value;self.assertTrue(self.result(api)['full'])

    def test_pagination_or_missing_runs_jobs_refuse(self):
        for field in ('runs','jobs'):
            for count in (0,2,100):
                api=API();getattr(api,field)['total_count']=count;self.assertTrue(self.result(api)['full'])

    def test_skipped_required_steps_and_failed_other_jobs_refuse(self):
        for i in (0,1):
            api=API();api.jobs['jobs'][0]['steps'][i]['conclusion']='skipped'
            self.assertTrue(self.result(api)['full'])
        api=API();api.jobs['jobs'].append(dict(api.jobs['jobs'][0],id=31,name='security',conclusion='failure'))
        api.jobs['total_count']=2;self.assertTrue(self.result(api)['full'])

    def test_renamed_test_check_missing_or_duplicate_steps_refuse(self):
        api=API();api.jobs['jobs'][0]['name']='renamed';self.assertTrue(self.result(api)['full'])
        for steps in ([],[dict(name=ci.DISCOVERY,status='completed',conclusion='success')]*2):
            api=API();api.jobs['jobs'][0]['steps']=steps;self.assertTrue(self.result(api)['full'])

    def test_post_merge_validation_is_not_pre_merge_evidence(self):
        api=API();api.jobs['jobs'][0]['completed_at']='2026-11-21T02:01:00Z'
        self.assertTrue(self.result(api)['full'])

    def test_missing_and_duplicated_checkout_logs_refuse(self):
        for raw in ('','Ran 3561 tests in 1s\nOK',log()+'\n'+log()):
            api=API();api.log=raw;self.assertTrue(self.result(api)['full'])

    def test_partial_or_forged_writer_evidence_refuses(self):
        for mutate in (lambda r:r.update(actual_writer_card_count=653),lambda r:r.update(readback_head=HEAD),
                       lambda r:r['validation'].update(exit_status=1),lambda r:r['nested_discovery'].update(tests=1),
                       lambda r:r['nested_discovery'].update(log_sha256='f'*64),
                       lambda r:r.update(published_to='production'),lambda r:r.update(simulated_platform_only=False)):
            value=receipt();mutate(value);api=API();api.log=log(value);self.assertTrue(self.result(api)['full'])

    def test_api_unavailable_or_malformed_falls_back_without_error_leak(self):
        api=API()
        for error in (OSError('SECRET_URL_OR_TOKEN'),KeyError('bad'),ValueError('bad')):
            with patch.object(api,'get',side_effect=error):
                result=self.result(api);self.assertTrue(result['full']);self.assertNotIn('SECRET',json.dumps(result))
        self.assertTrue(self.result(api=None,paths=['docs/example.md'])['schema_version'].endswith('v1'))
        result=ci.decide('push',dict(ref='refs/heads/main',before=BASE,after=MERGE),REPOSITORY,MERGE,TREE,[BASE,HEAD],[],None)
        self.assertTrue(result['full'])

    def test_response_and_request_budgets(self):
        client=ci.GitHub(REPOSITORY,'PRIVATE_TOKEN')
        client.requests=ci.MAX_REQUESTS
        with self.assertRaises(ci.Inconclusive):client.get('/anything')
        response=unittest.mock.MagicMock();response.__enter__.return_value.read.return_value=b'x'*(ci.MAX_BYTES+1)
        client.requests=0
        with patch.object(client.opener,'open',return_value=response),self.assertRaises(ci.Inconclusive):client.get('/anything')

    def test_redirect_strips_credentials_and_rejects_unsafe_destinations(self):
        request=urllib.request.Request('https://api.github.com/a',headers={'Authorization':'Bearer PRIVATE'})
        redirect=ci.SafeRedirect()
        target=redirect.redirect_request(request,None,302,'found',{},'https://logs.blob.core.windows.net/job')
        self.assertIsNone(target.get_header('Authorization'))
        for url in ('http://logs.blob.core.windows.net/job','https://evil.invalid/job','https://user@api.github.com/job',
                    'https://127.0.0.1/job','https://api.github.com:8443/job'):
            with self.assertRaises(ci.Inconclusive):redirect.redirect_request(request,None,302,'found',{},url)

    def test_main_pr_route_outputs_full_and_never_accesses_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'event').write_text('{}')
            env=dict(GITHUB_OUTPUT=str(root/'output'),GITHUB_STEP_SUMMARY=str(root/'summary'),
                     GITHUB_EVENT_PATH=str(root/'event'),GITHUB_EVENT_NAME='pull_request',
                     GITHUB_SHA=MERGE,GITHUB_REPOSITORY=REPOSITORY)
            with contextlib.redirect_stdout(io.StringIO()) as printed,patch.dict(os.environ,env),patch.object(ci,'git',side_effect=[MERGE.encode(),TREE.encode(),(BASE+' '+HEAD).encode()]),patch.object(ci,'GitHub') as api:
                self.assertEqual(ci.main(),0);api.assert_not_called()
            self.assertTrue(json.loads(printed.getvalue())['full'])
            self.assertEqual((root/'output').read_text(),'full=true\nfull=true\n')
            self.assertIn('ci-validation-scope-v1',(root/'summary').read_text())

    def test_main_verified_push_emits_reuse_only_after_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'event').write_text(json.dumps(dict(ref='refs/heads/main',before=BASE,after=MERGE)))
            env=dict(GITHUB_OUTPUT=str(root/'output'),GITHUB_STEP_SUMMARY=str(root/'summary'),
                     GITHUB_EVENT_PATH=str(root/'event'),GITHUB_EVENT_NAME='push',
                     GITHUB_SHA=MERGE,GITHUB_REPOSITORY=REPOSITORY)
            responses=[MERGE.encode(),TREE.encode(),(BASE+' '+HEAD).encode(),b'src/probability/draw_access.py\0']
            with contextlib.redirect_stdout(io.StringIO()) as printed,patch.dict(os.environ,env),patch.object(ci,'git',side_effect=responses),patch.object(ci,'GitHub',return_value=API()):
                self.assertEqual(ci.main(),0)
            self.assertFalse(json.loads(printed.getvalue())['full'])
            self.assertEqual((root/'output').read_text(),'full=true\nfull=false\n')

    def test_adapter_test_stdout_cannot_corrupt_real_publication_count(self):
        # Run the real adapter tests, then exercise the unchanged production
        # counter and independent diagnostics on their actual captured output.
        from production_evidence.automatic_updates import GitHubPersistence
        from publication_validation_regression import nested_validation_diagnostics
        stdout,stderr=io.StringIO(),io.StringIO()
        suite=unittest.TestSuite(CIWorkflowEfficiencyTests(name) for name in (
            'test_main_pr_route_outputs_full_and_never_accesses_network',
            'test_main_verified_push_emits_reuse_only_after_evidence'))
        with contextlib.redirect_stdout(stdout):
            result=unittest.TextTestRunner(stream=stderr,verbosity=2).run(suite)
        self.assertTrue(result.wasSuccessful());self.assertEqual(result.testsRun,2)
        self.assertEqual(stdout.getvalue(),'')
        child=SimpleNamespace(returncode=0,stdout=stdout.getvalue(),stderr=stderr.getvalue())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.git').mkdir()
            with patch('production_evidence.automatic_updates.subprocess.run',return_value=child):
                validation=GitHubPersistence._required_admission_validation(root)
            self.assertEqual(validation['tests'],2)
            log=(root/'.git/catalog-admission-validation.log').read_bytes()
            self.assertEqual(nested_validation_diagnostics(log,validation)['tests'],2)

    def test_unexpected_checkout_fails_job_without_emitting_skip(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            with patch.dict(os.environ,dict(GITHUB_OUTPUT=str(output),GITHUB_SHA=HEAD)),patch.object(ci,'git',return_value=MERGE.encode()):
                with self.assertRaises(ci.Inconclusive):ci.main()
            self.assertEqual(output.read_text(),'full=true\n')

    def test_workflow_keeps_original_gate_and_full_pr_manual_and_tag_routes(self):
        text=(ROOT/ci.WORKFLOW).read_text()
        self.assertIn('name: Python validation',text);self.assertIn('  test:',text)
        self.assertIn('  pull_request:',text);self.assertIn('  workflow_dispatch:',text)
        self.assertIn('    branches: [main]',text);self.assertIn("    tags: ['**']",text)
        self.assertIn(ci.PUBLICATION,text)
        self.assertIn('python tests/publication_validation_regression.py',text)
        self.assertIn('python -m unittest discover -s tests -p "test_*.py" -v',text)
        self.assertEqual(text.count("if: steps.scope.outputs.full == 'true'"),4)
        self.assertNotIn('continue-on-error',text);self.assertNotIn('paths-ignore',text)
        self.assertNotIn('cancel-in-progress',text);self.assertNotIn('write\n',text)
        self.assertNotIn('pull_request_target',text)


if __name__=='__main__':unittest.main()
