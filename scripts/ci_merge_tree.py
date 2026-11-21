"""Read-only CI evidence reuse. Any uncertainty selects the unchanged full gate.

Only a single, two-parent main merge of an already successful PR tree qualifies.
GitHub's job log supplies its actual checkout and existing writer receipt; no
caller receipt, cache, branch-head success or current PR merge ref substitutes.
"""
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

WORKFLOW = '.github/workflows/python-validation.yml'
DISCOVERY = 'Run python -m unittest discover -s tests -p "test_*.py" -v'
PUBLICATION = 'Real publication validation against disposable writer expansion'
MAX_BYTES = 4 * 1024 * 1024
MAX_REQUESTS = 6
SHA = re.compile(r'[0-9a-f]{40}')
# Existing authority/persistence boundaries, not a new admission classification.
# These require full post-merge validation even with an equivalent passing tree.
HIGH_RISK_PREFIXES = (
    '.github/', 'scripts/', 'data/', 'reference-reviews/', 'migrations/',
    'src/canonical', 'src/ingestion/', 'src/external_ingestion/', 'src/dataset_import/',
    'src/production_evidence/', 'src/repository/', 'src/acquisition/',
    'src/schemas/v2/', 'src/schemas/v3/',
    'src/gameplay_rules/source_evidence/',
)
HIGH_RISK_WORDS = ('permission', 'authorization', 'policy', 'admission', 'migration',
                   'recovery', 'rollback', 'persistence', 'snapshot', 'publication', 'release')
AUTHORITY_DOCUMENTS = {'docs/ARCHITECTURE.md', 'docs/DECISIONS.md', 'docs/GOVERNANCE.md',
                       'docs/AI_CONTRIBUTING.md', 'docs/GAMEPLAY_RULES_SOURCE_VERSIONING.md'}
CANONICAL_SCHEMAS = {'card.schema.json', 'printing.schema.json', 'set.schema.json',
                     'product.schema.json', 'product-version.schema.json', 'slot.schema.json',
                     'print-sheet.schema.json', 'pack-definition.schema.json', 'source-record.schema.json',
                     'normalized-source-record.schema.json', 'normalized-candidate-artifact.schema.json',
                     'parsed-record-artifact.schema.json', 'dataset-identity.schema.json', 'promotion-audit.schema.json'}


class Inconclusive(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Inconclusive(reason)


def sha(value):
    require(type(value) is str and SHA.fullmatch(value), 'invalid commit identity')
    return value


def utc(value):
    require(type(value) is str and value.endswith('Z'), 'missing evidence time')
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        require(target.scheme == 'https' and target.hostname and not target.username
                and not target.password and target.port in (None, 443)
                and (target.hostname == 'api.github.com' or target.hostname.endswith(
                    ('.blob.core.windows.net', '.actions.githubusercontent.com', '.githubusercontent.com'))),
                'unexpected GitHub log redirect')
        redirected = super().redirect_request(request, fp, code, message, headers, newurl)
        # Never forward the API credential to artifact/log storage.
        redirected.remove_header('Authorization')
        return redirected


class GitHub:
    def __init__(self, repository, token):
        require(type(repository) is str and re.fullmatch(r'[\w.-]+/[\w.-]+', repository),
                'invalid repository')
        require(bool(token), 'read-only Actions credential unavailable')
        self.root = 'https://api.github.com/repos/' + repository
        self.token, self.requests = token, 0
        self.opener = urllib.request.build_opener(SafeRedirect())

    def get(self, path, *, text=False):
        require(path.startswith('/') and not path.startswith('//'), 'invalid API path')
        self.requests += 1
        require(self.requests <= MAX_REQUESTS, 'evidence request budget exceeded')
        request = urllib.request.Request(self.root + path, headers={
            'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'MTG-Lab-CI-verifier'})
        with self.opener.open(request, timeout=20) as response:
            raw = response.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'evidence response budget exceeded')
        return raw.decode('utf-8') if text else json.loads(raw)


def high_risk(paths):
    return any(name in AUTHORITY_DOCUMENTS or name.startswith(HIGH_RISK_PREFIXES)
               or (name.startswith('src/schemas/') and Path(name).name in CANONICAL_SCHEMAS)
               or any(word in name.lower() for word in HIGH_RISK_WORDS) for name in paths)


def log_evidence(raw):
    """Describe the real GitHub job log; duplicate/partial claims do not qualify."""
    require(type(raw) is str and len(raw.encode()) <= MAX_BYTES, 'invalid job log')
    lines = [re.sub(r'^\d{4}-\S+Z ', '', line).rstrip('\r') for line in raw.splitlines()]
    checkouts = [lines[i + 1] for i, line in enumerate(lines[:-1])
                 if line == '[command]/usr/bin/git log -1 --format=%H']
    require(len(checkouts) == 1, 'one actual checkout identity required')
    checkout = sha(checkouts[0])
    summary_rows = [(i,line) for i,line in enumerate(lines) if re.fullmatch(r'Ran \d+ tests? in [\d.]+s', line)]
    outcome_rows = [(i,line) for i,line in enumerate(lines) if re.fullmatch(r'OK(?: \(skipped=\d+\))?', line)]
    summaries, outcomes = [row[1] for row in summary_rows], [row[1] for row in outcome_rows]
    receipts = [json.loads(line) for line in lines if line.startswith('{"actual_writer_card_count"')]
    require(len(summaries) == len(outcomes) == 2 and len(receipts) == 1
            and re.fullmatch(r'Ran 1 test in [\d.]+s', summaries[1]) and outcomes[1] == 'OK',
            'complete discovery and one successful publication integration required')
    receipt_line = next(line for line in lines if line.startswith('{"actual_writer_card_count"'))
    positions = [summary_rows[0][0], outcome_rows[0][0], lines.index(receipt_line),
                 summary_rows[1][0], outcome_rows[1][0]]
    require(positions == sorted(set(positions)), 'discovery/publication log order differs')
    count = int(summaries[0].split()[1])
    require(count > 0, 'empty discovery is not validation')
    receipt = receipts[0]
    nested, validation = receipt['nested_discovery'], receipt['validation']
    require(receipt['actual_writer_card_count'] == 654 and receipt['simulated_platform_only'] is True
            and receipt['published_to'] == 'disposable_local_bare_remote', 'actual disposable writer required')
    require(sha(receipt['published_head']) == sha(receipt['readback_head']), 'publication readback mismatch')
    require(type(validation['exit_status']) is int and validation['exit_status'] == 0
            and type(nested['tests']) is int and type(validation['tests']) is int
            and nested['tests'] == count == validation['tests']
            and type(nested['skipped']) is int and 0 <= nested['skipped'] <= count
            and type(nested['log_sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', nested['log_sha256'])
            and nested['log_sha256'] == validation['log_sha256'], 'nested validation mismatch')
    return checkout, {'outer_tests': count, 'outer_summary': summaries[0], 'outer_outcome': outcomes[0],
                      'writer': receipt}


def verify_merge(api, repository, commit, tree, parents):
    """Return evidence only for the latest complete successful equivalent PR run."""
    base, head = parents
    prs = api.get('/commits/' + commit + '/pulls?per_page=100')
    require(type(prs) is list and len(prs) < 100, 'ambiguous associated PR inventory')
    selected = [p for p in prs if p.get('merged_at') and p.get('merge_commit_sha') == commit
                and p['head']['sha'] == head and p['base']['sha'] == base
                and p['base']['ref'] == 'main' and p['base']['repo']['full_name'] == repository]
    require(len(selected) == 1, 'single exact merged PR required')
    pr = selected[0]
    runs = api.get('/actions/workflows/python-validation.yml/runs?event=pull_request&head_sha='
                   + head + '&per_page=100')
    require(type(runs['total_count']) is int and 0 < runs['total_count'] < 100
            and len(runs['workflow_runs']) == runs['total_count'], 'complete PR run inventory required')
    run = max(runs['workflow_runs'], key=lambda row: row['id'])
    require(run['event'] == 'pull_request' and run['path'] == WORKFLOW and run['head_sha'] == head
            and run['repository']['full_name'] == repository and run['status'] == 'completed'
            and run['conclusion'] == 'success', 'latest PR validation is not successful')
    require(type(run['id']) is int and run['id'] > 0, 'invalid run identity')
    jobs = api.get('/actions/runs/' + str(run['id']) + '/jobs?per_page=100')
    require(jobs['total_count'] == len(jobs['jobs']) and 0 < len(jobs['jobs']) < 100
            and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in jobs['jobs']),
            'incomplete or unsuccessful workflow jobs')
    tests = [j for j in jobs['jobs'] if j['name'] == 'test']
    require(len(tests) == 1, 'original test check required')
    job = tests[0]
    require(utc(job['completed_at']) <= utc(pr['merged_at']), 'validation did not finish before merge')
    for name in (DISCOVERY, PUBLICATION):
        steps = [s for s in job['steps'] if s['name'] == name]
        require(len(steps) == 1 and steps[0]['status'] == 'completed'
                and steps[0]['conclusion'] == 'success', 'required validation step did not run')
    require(type(job['id']) is int and job['id'] > 0, 'invalid job identity')
    checkout, observed = log_evidence(api.get('/actions/jobs/' + str(job['id']) + '/logs', text=True))
    tested = api.get('/git/commits/' + checkout)
    require(tested['sha'] == checkout and tested['tree']['sha'] == tree
            and [p['sha'] for p in tested['parents']] == [base, head], 'tested merge tree or ancestry differs')
    return dict(pr=pr['number'], run_id=run['id'], job_id=job['id'], tested_commit=checkout,
                tested_tree=tree, workflow_url='https://github.com/' + repository + '/actions/runs/' + str(run['id']),
                validation=observed)


def decide(event_name, event, repository, commit, tree, parents, paths, api=None):
    full = dict(schema_version='ci-validation-scope-v1', full=True, commit=commit, tree=tree)
    if event_name != 'push':
        return dict(full, reason='PR and manual runs always execute full validation')
    if (event.get('ref') != 'refs/heads/main' or len(parents) != 2
            or event.get('before') != parents[0] or event.get('after') != commit):
        return dict(full, reason='direct, batched or unexpected main history requires full validation')
    if high_risk(paths):
        return dict(full, reason='authority, CI, import, persistence, recovery or release boundary changed')
    try:
        require(api is not None, 'Actions evidence unavailable')
        evidence = verify_merge(api, repository, sha(commit), sha(tree), [sha(p) for p in parents])
    except (Inconclusive, KeyError, ValueError, TypeError, OSError, urllib.error.URLError) as error:
        # Never emit credentials, signed redirect URLs or raw provider error bodies.
        detail = str(error) if isinstance(error, Inconclusive) else type(error).__name__
        return dict(full, reason='prior validation evidence inconclusive: ' + detail)
    return dict(full, full=False, reason='successful exact PR merge tree verified', evidence=evidence)


def git(*args):
    return subprocess.check_output(['git', *args], timeout=10)


def main():
    # Fail closed even if inspection unexpectedly terminates before completion.
    output = Path(os.environ['GITHUB_OUTPUT'])
    with output.open('a') as stream:
        stream.write('full=true\n')
    commit = git('rev-parse', 'HEAD').decode().strip()
    require(commit == os.environ['GITHUB_SHA'], 'workflow checkout differs from event commit')
    tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
    parents = git('show', '-s', '--format=%P', 'HEAD').decode().split()
    event_name = os.environ['GITHUB_EVENT_NAME']
    event_path = Path(os.environ['GITHUB_EVENT_PATH'])
    require(event_path.stat().st_size <= MAX_BYTES, 'event budget exceeded')
    event = json.loads(event_path.read_bytes())
    paths = []
    if event_name == 'push' and len(parents) == 2:
        paths = git('diff', '--name-only', '--no-renames', '-z', parents[0], commit).decode().split('\0')[:-1]
    api = None
    if event_name == 'push':
        try:
            api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ.get('GH_TOKEN'))
        except Inconclusive:
            pass
    result = decide(event_name, event, os.environ['GITHUB_REPOSITORY'], commit, tree, parents, paths, api)
    print(json.dumps(result, sort_keys=True))
    with output.open('a') as stream:
        stream.write('full=' + str(result['full']).lower() + '\n')
    with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as stream:
        stream.write('## Validation scope\n\n```json\n' + json.dumps(result, indent=2, sort_keys=True) + '\n```\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
