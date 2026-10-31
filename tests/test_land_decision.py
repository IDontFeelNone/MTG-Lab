"""Finite owner-decision provenance, negative contracts and historical preservation.

The public integration admits the actual current catalog. The actual 654-card
publication writer must reject that fixed attachment; no positive historical
catalog or new skip is installed in the disposable publication repository.
"""
from copy import deepcopy
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c
from land_test_support import ROOT, arguments as land_arguments, current_catalog_intact
from repository.snapshots import SnapshotError


EXPECTED_CANDIDATES = (
    ('snow-wastes-mana', 'sha256:7ce81b50485c09cb3ed789db287142253b55541c067d275f6750f1c9a2bc02e5'),
    ('port-mana', 'sha256:142af8b66263bb182396c134e4c9efb7b6f686be5097d875743d9e67c076748a'),
    ('port-utility', 'sha256:8dc9ba9f08113d9ee170efeadf7e4f21022e60f3e2a5694cfd088ad3657a66da'),
    ('city-mana', 'sha256:75a3a8dd76a16138dfbd8528d2680109e3f9ca542538df6b0fe6298a63e84148'),
    ('city-damage-trigger', 'sha256:0a66c251fedc138c584b64ba80b36dcf1c59ba5ae34010a45c7909dfdce658e4'),
    ('citadel-colorless', 'sha256:9df44dd22515ca823e3b65d3e56160b2bb6b1e756e5c691daa234cba744db013'),
    ('citadel-color-choice', 'sha256:83aa0a956dd278b5362466b29664874ece949dbf6f32cf74b9777bcf47d954c1'),
    ('coffers-mana', 'sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48'),
    ('tower-mana', 'sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc'),
)
HISTORICAL_FILES = {
    'plan.json': (7109, 'bed5e94c18b6145a139557a53b8d0af8ae38fbe243e4027da4e8ee9033ab2b3c'),
    'interpretations.json': (134293, '6376abbc89497ced3b399dc4606361b1eca7621df3b6ececeb60fdec0ae3df11'),
    'manifest.json': (965, 'e148fcce3c92a445d61305c488f63b5fecd83efda2a677c0355e31b13252166f'),
}
HISTORICAL_REVIEW = {
    'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False,
}
CURRENT_STATUS = 'ACCEPTED_BOUNDED_RETAINED_TEXT'


def nodes(value):
    """Walk decoded JSON without interpreting an approval or an ability."""
    yield value
    children = value.values() if type(value) is dict else value if type(value) is list else ()
    for child in children:
        yield from nodes(child)


def full_candidates(record):
    # Locate the complete original candidate array, distinct from compact ID
    # bindings. This assertion also forbids replacing all evidence with labels.
    matches = [node for node in nodes(record) if type(node) is list and node
        and all(type(row) is dict and 'candidate_id' in row and 'criteria' in row
                and type(row.get('subject')) is dict for row in node)]
    if len(matches) != 1:
        raise AssertionError('one complete historical candidate collection required')
    return matches[0]


def decision_arguments(**changes):
    from card_rules_pilot import land_decision as d
    value = land_arguments()
    value.update(decision_root=ROOT / 'data/review/land-semantic-decisions',
                 expected_decision_id=d.DECISION_ID)
    value.update(changes)
    return value


def cli_arguments():
    selected = decision_arguments()
    result = []
    for name in ('catalog_root', 'mechanical_root', 'cohort_root', 'decision_root',
                 'expected_profile_id', 'expected_query_snapshot_id',
                 'expected_plan_id', 'expected_decision_id'):
        result.extend(['--' + name.replace('_', '-'), str(selected[name])])
    return result


class LandSemanticDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from card_rules_pilot import land_decision as d
        cls.d = d
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.consumer = d.load_land_decision(**decision_arguments()) if cls.intact else None
        if cls.intact:
            cls.record = c.read_json(decision_arguments()['decision_root'] / d.OWNER_RECORD)

    def admitted(self):
        if self.intact:
            return True
        self.assertFalse(current_catalog_intact(self))
        # Missing decision files in the real writer fixture cannot become a
        # reason to substitute a different catalog or ignore its failed binding.
        with self.assertRaises(SnapshotError):
            self.d.load_land_decision(**decision_arguments())
        return False

    def rehash_record(self, value):
        return c.seal(self.d.DECISION_VERSION, value, 'decision_id')

    def test_exact_nine_current_decisions_and_original_candidate_identity_domains(self):
        if not self.admitted():
            return
        self.assertEqual(self.consumer.subject_ids, tuple(sid for sid, _ in EXPECTED_CANDIDATES))
        self.assertEqual(self.d.CANDIDATE_IDS, EXPECTED_CANDIDATES)
        candidates = full_candidates(self.record)
        self.assertEqual(tuple((row['subject']['subject_id'], row['candidate_id'])
                               for row in candidates), EXPECTED_CANDIDATES)
        for candidate in candidates:
            self.assertEqual(c.identity(candidate['schema_version'], candidate, 'candidate_id'),
                             candidate['candidate_id'])
        for sid, _ in EXPECTED_CANDIDATES:
            view = self.consumer.subject(sid).to_dict()
            self.assertEqual(view['decision_status'], CURRENT_STATUS)
            self.assertEqual(view['historical_semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
            self.consumer.validate_report(view)
        for sid, identity in EXPECTED_CANDIDATES:
            self.assertEqual(self.consumer.candidate(identity).to_json(), self.consumer.subject(sid).to_json())
        for foreign in ('sha256:' + '0' * 64, True, None,
                        # The land plan identity is not a candidate identity.
                        'sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5'):
            with self.assertRaises(ValueError):
                self.consumer.candidate(foreign)
        earlier = json.loads((ROOT / 'data/review/card-rules-mana-pilot/manifest.json').read_bytes())
        self.assertEqual(len(earlier['candidates']), 7)
        for candidate in earlier['candidates']:
            with self.subTest(unrelated_candidate=candidate['subject_id']), self.assertRaises(ValueError):
                self.consumer.candidate(candidate['candidate_id'])
        summary = self.consumer.summary().to_dict()
        self.assertEqual(summary['decision_status'], CURRENT_STATUS)
        self.assertEqual(self.record['decision_id'], self.d.DECISION_ID)
        self.assertEqual(c.identity(self.d.DECISION_VERSION, self.record, 'decision_id'),
                         self.d.DECISION_ID)
        self.consumer.validate_record(self.record)

    def test_tenth_omitted_duplicate_reordered_and_foreign_candidates_reject_when_rehashed(self):
        if not self.admitted():
            return
        changes = []
        value = deepcopy(self.record)
        rows = full_candidates(value)
        tenth = deepcopy(rows[0])
        tenth['subject']['subject_id'] = 'unauthorized-tenth-candidate'
        tenth = c.seal(tenth['schema_version'], tenth, 'candidate_id')
        rows.append(tenth)
        changes.append(value)
        value = deepcopy(self.record); full_candidates(value).pop(); changes.append(value)
        value = deepcopy(self.record); rows = full_candidates(value); rows[-1] = deepcopy(rows[0]); changes.append(value)
        value = deepcopy(self.record); full_candidates(value).reverse(); changes.append(value)
        value = deepcopy(self.record); full_candidates(value)[0]['candidate_id'] = 'sha256:' + '0' * 64; changes.append(value)
        for value in changes:
            changed = self.rehash_record(value)
            self.assertEqual(c.identity(self.d.DECISION_VERSION, changed, 'decision_id'), changed['decision_id'])
            with self.assertRaises(ValueError):
                self.consumer.validate_record(changed)

    def test_modified_owned_passage_criterion_and_stale_source_binding_are_not_new_approvals(self):
        if not self.admitted():
            return
        for mutation in ('passage', 'criterion', 'source_field', 'query', 'unknowns'):
            changed = deepcopy(self.record)
            candidate = full_candidates(changed)[6]
            if mutation == 'passage':
                candidate['subject']['selected_passage'] = '{T}: Add one mana of any color.'
            elif mutation == 'criterion':
                candidate['criteria'][1]['state'] = 'proposed_not_satisfied'
            elif mutation == 'source_field':
                candidate['source_binding']['source_field_identity'] = 'sha256:' + '1' * 64
            elif mutation == 'query':
                candidate['source_binding']['canonical_snapshot_id'] = 'sha256:' + '2' * 64
            else:
                candidate['unresolved'] = []
            candidate['candidate_id'] = c.identity(candidate['schema_version'], candidate, 'candidate_id')
            self.assertEqual(c.identity(candidate['schema_version'], candidate, 'candidate_id'), candidate['candidate_id'])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.consumer.validate_record(self.rehash_record(changed))

    def test_historical_pending_bytes_authority_and_all_computed_results_are_preserved(self):
        if not self.admitted():
            return
        for filename, (length, sha256) in HISTORICAL_FILES.items():
            raw = (ROOT / 'data/review/land-mana-utility' / filename).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (length, sha256))
        overview = self.consumer.historical_overview()
        raw = overview.to_json().encode()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (689253,
            '0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515'))
        value = overview.to_dict()
        self.assertEqual(value['report_id'], 'sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd')
        historical = value['context']['interpretations']['candidates']
        self.assertEqual(full_candidates(self.record), historical)
        for row in [value, *historical, *value['assessments']]:
            self.assertEqual(row['review'], HISTORICAL_REVIEW)
            self.assertEqual(row['semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
            self.assertEqual(row['execution_authority'], 'BLOCKED')
        kinds = {row['subject_id']: row['behavior']['branch'] for row in value['assessments']}
        self.assertEqual(kinds['port-utility'], 'CONDITIONAL_ORDINARY_ACTIVATED')
        self.assertEqual(kinds['city-damage-trigger'], 'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER')
        self.assertTrue(all(kinds[sid] == 'CONDITIONAL_ACTIVATED_MANA'
                            for sid in kinds if sid not in ('port-utility', 'city-damage-trigger')))
        self.assertEqual(tuple(row['name'] for row in value['comparisons']),
                         ('mana-and-utility', 'damage-ownership', 'variable-output', 'color-context'))

    def test_owner_supplied_provenance_records_no_invented_authentication_or_attestation(self):
        if not self.admitted():
            return
        decision = self.record['decision']
        self.assertEqual(decision['status'], CURRENT_STATUS)
        self.assertEqual(decision['source'], 'EXPLICIT_OWNER_SUPPLIED_INSTRUCTION')
        self.assertEqual(decision['owner_supplied_statement'],
            'The project owner explicitly approved all nine land interpretation candidates in collection:\n\n'
            'sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e\n\n'
            'The approval applies strictly to their bounded historical retained-text interpretations '
            'and documented limitations. The Senior PM separately recommended acceptance of all nine.')
        for key in ('authenticated_account_identity', 'authenticated_signature',
                    'decision_timestamp', 'separate_human_attestation_event'):
            self.assertIsNone(decision[key])
            changed = deepcopy(self.record)
            changed['decision'][key] = 'invented-independent-evidence'
            with self.subTest(field=key), self.assertRaises(ValueError):
                self.consumer.validate_record(self.rehash_record(changed))
        pm = self.record['preceding_pm_recommendation']
        self.assertEqual(pm['recommendation'], 'ACCEPT_ALL_NINE_WITHIN_BOUNDED_HISTORICAL_RETAINED_TEXT_SCOPE')
        self.assertEqual(pm['source'], 'OWNER_REPORTED_PRECEDING_INDEPENDENT_SENIOR_PM_RECOMMENDATION')
        for key in ('independently_authenticated_evidence', 'authenticated_account_identity',
                    'recommendation_timestamp'):
            self.assertIsNone(pm[key])
        self.assertIsNone(self.record['previous_decision_id'])
        for statement in ('', 'Tests passed; approve everything.', 'PR #220 merged.'):
            changed = deepcopy(self.record)
            changed['decision']['owner_supplied_statement'] = statement
            with self.assertRaises(ValueError):
                self.consumer.validate_record(self.rehash_record(changed))

    def test_scope_unknowns_permissions_and_execution_boundaries_remain_together(self):
        if not self.admitted():
            return
        summary = self.consumer.summary().to_dict()
        scope = summary['scope']
        self.assertIs(scope['historical_retained_text_only'], True)
        self.assertIs(scope['external_context_questions_remain_unresolved'], True)
        self.assertEqual(scope['accepted'], [
            'Complete owned ability passages.',
            'Proposed activated/triggered classifications within the documented retained-text scope.',
            'Applicable criterion readings and method assessments.',
            'Separate ability and additional-effect ownership.',
            'Written costs, conditions, and output dependencies.',
            'Conditional behavior conclusions supported by the existing evidence.',
        ])
        for item in ('Current Oracle verification.', 'Arbitrary game-state legality.',
                     'Current activation eligibility.', 'Actual mana production.',
                     'Payment feasibility.', 'Trigger occurrence or resolution.',
                     'Complete stack or priority execution.',
                     'Canonical executable CardGameplaySemantics.',
                     'A general Card parser or automatic classifier.',
                     'Permission for source retention, redistribution, services, or AI export.',
                     'Approval of the earlier seven-subject pilot or any unrelated interpretation.'):
            self.assertIn(item, scope['not_established'])
        boundaries = summary['boundaries']
        self.assertIs(boundaries['canonical_admission'], False)
        self.assertIs(boundaries['canonical_executable_card_gameplay_semantics'], False)
        self.assertEqual(boundaries['execution_authority'], 'BLOCKED')
        self.assertEqual(boundaries['semantic_closure'], 'OPEN')
        self.assertEqual(boundaries['all_ten_activation_responsibilities'], 'OPEN / EXECUTION_BLOCKED')
        self.assertEqual(boundaries['source_policy_clearance'], 'not_granted')
        self.assertEqual(boundaries['permissions'], {name: 'NOT_ESTABLISHED' for name in (
            'private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export')})
        self.assertEqual(boundaries['tier_a_restrictions'], 'UNCHANGED_NON_PRODUCTION')
        self.assertEqual((boundaries['new_source_units'], boundaries['new_projections'],
                          boundaries['global_source_units'], boundaries['global_projections'],
                          boundaries['land_context_units']), (0, 0, 104, 16, 24))
        self.assertEqual(boundaries['fresh_source_inspection_allowlist'], [])
        self.assertEqual(boundaries['new_source_projection_allowlist'], [])
        self.assertIs(boundaries['fresh_oracle_verification'], False)
        self.assertIs(boundaries['fresh_cr_txt_verification'], False)
        originals = {row['subject']['subject_id']: row for row in full_candidates(self.record)}
        for row in summary['subjects']:
            original = originals[row['subject_id']]
            self.assertEqual(row['current_decision_status'], CURRENT_STATUS)
            self.assertEqual(row['historical_review'], HISTORICAL_REVIEW)
            self.assertEqual(row['remaining_unknowns'], original['unresolved'])
            self.assertEqual(row['limitations'], original['limitations'])
            self.assertEqual(row['criteria'], original['criteria'])
            self.assertEqual(row['written_readings'], original['descriptive_readings'])
            self.assertIs(row['canonical_admission'], False)
            self.assertEqual(row['execution_authority'], 'BLOCKED')
        for key, value in (('canonical_admission', True), ('execution_authority', 'ACTIVE'),
                           ('source_policy_clearance', 'granted'), ('new_source_units', False),
                           ('land_context_units', 25)):
            changed = deepcopy(self.record); changed['boundaries'][key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                self.consumer.validate_record(self.rehash_record(changed))
        changed = deepcopy(self.record); changed['scope']['not_established'] = []
        with self.assertRaises(ValueError):
            self.consumer.validate_record(self.rehash_record(changed))

    def test_actual_fresh_public_admission_rejects_coherently_changed_candidate_evidence(self):
        if not self.admitted():
            return
        from card_rules_pilot import land_authored
        original = self.consumer.summary().to_json()
        with tempfile.TemporaryDirectory(prefix='mtglab-land-decision-cohort-') as directory:
            cohort = Path(directory) / 'cohort'
            shutil.copytree(ROOT / 'data/review/land-mana-utility', cohort)
            collection = c.read_json(cohort / 'interpretations.json')
            candidate = collection['candidates'][6]
            candidate['subject']['selected_passage'] = '{T}: Add one mana of any color.'
            candidate['subject']['passage_end'] = candidate['subject']['passage_start'] + len(candidate['subject']['selected_passage'])
            collection['candidates'][6] = c.seal(candidate['schema_version'], candidate, 'candidate_id')
            collection = c.seal(collection['schema_version'], collection, 'interpretations_id')
            (cohort / 'interpretations.json').write_bytes(c.canonical(collection))
            manifest = land_authored.build_manifest(c.read_json(cohort / 'plan.json'), collection)
            (cohort / 'manifest.json').write_bytes(c.canonical(manifest))
            self.assertEqual(c.identity(collection['schema_version'], collection, 'interpretations_id'), collection['interpretations_id'])
            self.assertEqual(c.identity(manifest['schema_version'], manifest, 'manifest_id'), manifest['manifest_id'])
            # Real public catalog, acquisition, dossier and rule reads remain in
            # this call; only the caller-selected cohort root is a changed copy.
            with self.assertRaises(ValueError):
                self.d.load_land_decision(**decision_arguments(cohort_root=cohort))
        self.assertEqual(self.consumer.summary().to_json(), original)

    def test_report_recomputation_rejects_generic_acceptance_and_authority_changes(self):
        if not self.admitted():
            return
        report = self.consumer.summary().to_dict()
        for key, new_value in (('execution_authority', 'READY'), ('canonical_admission', True),
                               ('decision_status', 'ACCEPTED_WITHOUT_LIMITATIONS'),
                               ('historical_semantic_review_status', CURRENT_STATUS),
                               ('schema_version', 'future-approval-service-v2'),
                               ('selector', 'foreign-subject'), ('kind', 'approve')):
            changed = deepcopy(report)
            changed[key] = new_value
            changed = c.seal(self.d.REPORT_VERSION, changed, 'report_id')
            with self.subTest(field=key), self.assertRaises(ValueError):
                self.consumer.validate_report(changed)
        for selector in ('foreign-subject', 'earlier-seven-pilot', True, None, 9):
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                self.consumer.subject(selector)
        for value in ({}, {'kind': True}, {'kind': 'summary', 'selector': True}):
            with self.assertRaises(ValueError):
                self.consumer.validate_report(value)

    def test_independent_views_and_deterministic_owned_summary(self):
        if not self.admitted():
            return
        document = self.consumer.summary()
        raw = document.to_json()
        self.assertEqual(c.canonical(document.to_dict()), raw.encode())
        view = document.to_dict()
        view.clear()
        record = deepcopy(self.record)
        self.consumer.validate_record(record)
        full_candidates(record)[0]['criteria'].clear()
        for _ in range(2):
            self.assertEqual(self.consumer.summary().to_json(), raw)
            self.assertEqual(self.consumer.validate_report(document.to_dict()).to_json(), raw)
        self.consumer.validate_report(self.consumer.check().to_dict())

    def test_strict_json_types_duplicate_keys_nonfinite_and_unpinned_identities_reject(self):
        if not self.admitted():
            return
        changes = []
        for key, replacement in (('schema_version', True), ('decision_id', True),
                                  ('decision_id', 'sha256:' + 'a' * 64)):
            changed = deepcopy(self.record); changed[key] = replacement; changes.append(changed)
        changed = deepcopy(self.record)
        candidate = full_candidates(changed)[0]
        candidate['review']['canonical_admission'] = 0
        candidate['subject']['passage_start'] = False
        changes.append(self.rehash_record(changed))
        for changed in changes:
            with self.assertRaises(ValueError):
                self.consumer.validate_record(changed)
        with self.assertRaises(ValueError):
            self.consumer.validate_record(True)
        with self.assertRaises(ValueError):
            self.consumer.validate_record({'number': 1.0})
        for raw in (b'{"decision_id":"first","decision_id":"second"}\n',
                    b'{"x":NaN}\n', b'{"x":Infinity}\n', b'{"x":1.0}\n',
                    b'{ "x":1 }\n', b'{}', b'[]\ntrailing'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                c.parse_json(raw)
        for expected in (True, None, 'sha256:' + 'b' * 64):
            with self.assertRaises(ValueError):
                self.d.load_land_decision(**decision_arguments(expected_decision_id=expected))

    def test_finite_record_reader_rejects_extra_files_noncanonical_json_and_later_mutation(self):
        if not self.admitted():
            return
        from land_test_support import consumer as admitted_lands
        original = self.consumer.summary().to_json()
        with tempfile.TemporaryDirectory(prefix='mtglab-land-owner-record-') as directory:
            root = Path(directory) / 'decisions'
            shutil.copytree(decision_arguments()['decision_root'], root)
            path = root / self.d.OWNER_RECORD
            baseline = path.read_bytes()
            # Reuse only a genuinely admitted original land consumer for these
            # record-reader negatives; the source-admission integration above
            # remains real and unpatched.
            with patch.object(self.d, 'load_lands', return_value=admitted_lands()):
                admitted = self.d.load_land_decision(**decision_arguments(decision_root=root))
                path.write_bytes(baseline.replace(b'{', b'{ ', 1))
                with self.assertRaises(ValueError):
                    self.d.load_land_decision(**decision_arguments(decision_root=root))
                for malformed in (b'{"decision_id":"first","decision_id":"second"}\n',
                                  b'{"decision_id":NaN}\n', b'{"decision_id":1.0}\n'):
                    path.write_bytes(malformed)
                    with self.assertRaises(ValueError):
                        self.d.load_land_decision(**decision_arguments(decision_root=root))
                changed = deepcopy(self.record)
                changed['decision']['owner_supplied_statement'] = 'Generic approval flag=true'
                path.write_bytes(c.canonical(self.rehash_record(changed)))
                with self.assertRaises(ValueError):
                    self.d.load_land_decision(**decision_arguments(decision_root=root))
                path.write_bytes(baseline)
                (root / 'unauthorized-later-approval.json').write_bytes(b'{}\n')
                with self.assertRaises(ValueError):
                    self.d.load_land_decision(**decision_arguments(decision_root=root))
                self.assertEqual(admitted.summary().to_json(), original)
        self.assertEqual(self.consumer.summary().to_json(), original)

    def test_cli_all_routes_match_canonical_readable_views_and_expose_limits(self):
        from card_rules_pilot import land_decision_cli as cli
        if not self.admitted():
            actual = self.run_cli('summary')
            self.assertEqual(actual.returncode, 2, actual.stderr.decode())
            self.assertEqual(actual.stdout, b'')
            self.assertIn(b'bounded land semantic decision rejected:', actual.stderr)
            return
        routes = [('summary', None, self.consumer.summary()),
                  ('check', None, self.consumer.check())]
        routes.extend(('subject', sid, self.consumer.subject(sid)) for sid, _ in EXPECTED_CANDIDATES)
        for command, selector, document in routes:
            for as_json in (True, False):
                out = io.StringIO()
                suffix = ([selector] if selector is not None else []) + (['--json'] if as_json else [])
                with self.subTest(command=command, subject=selector, json=as_json), \
                        patch.object(self.d, 'load_land_decision', return_value=self.consumer) as load, \
                        contextlib.redirect_stdout(out):
                    status = cli.main(['--review-root', str(ROOT / 'reference-reviews'),
                                       command, *cli_arguments(), *suffix])
                self.assertEqual(status, 0)
                load.assert_called_once_with(**decision_arguments())
                self.assertEqual(out.getvalue(), document.to_json() if as_json
                                 else self.d.render_land_decision(document))
                if not as_json:
                    self.assertIn('requires_review', out.getvalue())
                    self.assertIn('BLOCKED', out.getvalue())
                    for limitation in document.to_dict()['scope']['not_established']:
                        self.assertIn(limitation, out.getvalue())
                    for subject in document.to_dict()['subjects']:
                        for unknown in subject['remaining_unknowns']:
                            self.assertIn(unknown, out.getvalue())

    def run_cli(self, command, *suffix):
        return subprocess.run([sys.executable, '-m', 'card_rules_pilot.land_decision_cli',
            '--review-root', str(ROOT / 'reference-reviews'), command,
            *cli_arguments(), *suffix, '--json'], cwd=ROOT, capture_output=True,
            env=dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1'))

    def test_real_cli_and_api_are_read_only_and_deterministic(self):
        if not self.admitted():
            return
        roots = [ROOT / 'data/review', ROOT / 'reference-reviews',
                 ROOT / 'data/market/acquisitions/scryfall-mb2-30754638264-1']
        profile_path = ROOT / 'config/catalog_profiles/legacy-public-tier-a.json'
        profile = json.loads(profile_path.read_bytes())
        fixed = {profile_path, *(ROOT / row['path'] for row in profile['files'])}
        def snapshot():
            paths = fixed | {path for root in roots for path in root.rglob('*') if path.is_file()}
            return {str(path): (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in paths}
        before = snapshot()
        expected = self.consumer.summary().to_json().encode()
        actual = self.run_cli('summary')
        self.assertEqual(actual.returncode, 0, actual.stderr.decode())
        self.assertEqual(actual.stdout, expected)
        self.consumer.validate_report(json.loads(actual.stdout))
        self.consumer.check()
        self.consumer.historical_overview()
        self.assertEqual(snapshot(), before)
        self.assertEqual(self.consumer.summary().to_json().encode(), expected)

    def test_cli_mutation_commands_missing_pins_and_failures_emit_no_partial_report(self):
        from card_rules_pilot import land_decision_cli as cli
        for suffix in (['approve'], ['append'], ['ingest'], ['activate'],
                       ['summary', '--catalog-root', str(ROOT)]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    cli.parser().parse_args(['--review-root', str(ROOT / 'reference-reviews'), *suffix])
                self.assertEqual(raised.exception.code, 2)
        for command, selector, replacement in (
                ('summary', None, ValueError('changed retained evidence')),
                ('subject', 'foreign-subject', self.consumer if self.intact
                 else ValueError('incompatible expanded catalog'))):
            out, err = io.StringIO(), io.StringIO()
            replacement_args = ({'side_effect': replacement} if isinstance(replacement, Exception)
                                else {'return_value': replacement})
            with patch.object(self.d, 'load_land_decision', **replacement_args), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    cli.main(['--review-root', str(ROOT / 'reference-reviews'), command,
                              *cli_arguments(), *([selector] if selector is not None else []), '--json'])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('bounded land semantic decision rejected:', err.getvalue())


if __name__ == '__main__':
    unittest.main()
