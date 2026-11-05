"""Finite exact-ID evidence overlay. No strategic or gameplay authority."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from card_rules_pilot import contract as c, land_decision as d
from card_rules_pilot import land_explanation as e, mana_scenario as h, mana_scenario_policy as hp
from card_rules_pilot.land import COMPARISONS
from card_rules_pilot.cards import ACQUISITION, PROFILE_ID, QUERY_ID
from card_intelligence.mechanics import MechanicalCardIntelligence, MechanicalDossier
from repository.legacy_profile import attach_legacy_compatibility
from projection.historical_evidence import load_historical_admission

VERSION = 'six-land-exact-id-evidence-overlay-v1'
POLICY_VERSION = 'six-land-evidence-overlay-policy-v1'
DESIGN_ID = 'sha256:fdd5e2362a36b906f3158977ced62aeb7f2f41e8a5acb111fbf1c01bbe6849a5'
CARD_NAMESPACE = 'magic:legacy-promoted:card'
PRINTING_NAMESPACE = 'magic:mtgjson:printing'
OBSERVATION_NAMESPACE = 'scryfall:historical:printing-observation'
REPORT_LIMIT = 65536
READABLE_LIMIT = 32768
DESIGN_ROOT = Path(__file__).resolve().parents[2] / 'docs/design/rules-card-intelligence-v1'
JOIN_NAMES = ('historical_correspondence', 'current_identifier_edge', 'operator_production',
              'typed_seed', 'functional_role_pilot', 'contextual_comparison_pilot')

_POLICY = c.seal(POLICY_VERSION, dict(schema_version=POLICY_VERSION,
    design_package_id=DESIGN_ID, card_namespace=CARD_NAMESPACE,
    printing_namespace=PRINTING_NAMESPACE, observation_namespace=OBSERVATION_NAMESPACE,
    joins=list(JOIN_NAMES), comparison_groups=list(COMPARISONS),
    decision_id=d.DECISION_ID, collection_id=d.COLLECTION_ID,
    rules=[
        'Exact namespace and Card ID only; names are admitted display facts.',
        'Owning query, mechanical, historical promotion and semantic consumers admit evidence before composition.',
        'Current identifier, historical correspondence, pilot membership and operator authority remain independent.',
        'Use original accepted explanations and hypothetical calculations; no new semantic inference.',
        'Only the retained observation and complete selected subjects inherit acceptance, never every Printing.',
        'Another public load revalidates current roots; one batch shares one query/mechanical and rules admission.',
        'Recompute expected reports; reject foreign evidence, unknown fields and coherently rehashed substitutions.',
        'No legal action, actual mana, damage, net value, strategic superiority or production authority follows.'],
    report_byte_limit=REPORT_LIMIT, readable_byte_limit=READABLE_LIMIT,
    canonical_admission=False, execution_authority='BLOCKED'), 'policy_id')
POLICY_ID = _POLICY['policy_id']


class OverlayError(c.PilotError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(code + ': ' + message)


def policy_document():
    return c.ReviewDocument._verified(_POLICY, limit=REPORT_LIMIT)


def _design(root):
    """The fixed approved reference is not an admission of its example records."""
    root = Path(root)
    names = {'README.md', 'inventory.json', 'identity-joins.json', 'source-bindings.json',
             'contract.schema.json', 'examples.json', 'manifest.json'}
    if root.is_symlink() or not root.is_dir() or {p.name for p in root.iterdir()} != names:
        raise OverlayError('DESIGN_INTEGRITY', 'exact approved design file set required')
    manifest = c.read_json(root / 'manifest.json')
    if manifest['package_id'] != DESIGN_ID or c.identity(manifest['schema_version'], manifest, 'package_id') != DESIGN_ID:
        raise OverlayError('DESIGN_INTEGRITY', 'exact approved design identity required')
    for name, pin in manifest['files'].items():
        path = root / name
        if path.is_symlink(): raise OverlayError('DESIGN_INTEGRITY', 'symlink design input')
        raw = path.read_bytes()
        c.exact(pin, dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return c.read_json(root / 'identity-joins.json'), c.read_json(root / 'source-bindings.json')


def _reference(kind, selector, doc, scenario=None):
    raw = doc.to_json().encode()
    value = doc.to_dict()
    return dict(kind=kind, selector=selector, scenario=scenario,
        identity=value.get('report_id', value.get('dossier_id')),
        bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
        route='LandEvidenceOverlay.detailed(reference)')


@dataclass(frozen=True, init=False)
class LandEvidenceOverlay:
    _cards: bytes
    _mechanical: bytes
    _explanations: e.LandExplanationConsumer
    _scenarios: h.ManaScenarioConsumer
    _binding: bytes
    _historical_reference: bytes

    @property
    def card_ids(self): return tuple(json.loads(self._cards))
    @property
    def comparison_names(self): return tuple(COMPARISONS)

    def _select(self, namespace, card_id):
        if type(namespace) is not str or namespace != CARD_NAMESPACE:
            raise OverlayError('UNSUPPORTED_NAMESPACE', 'explicit supported Card namespace required')
        if type(card_id) is not str or card_id not in self.card_ids:
            raise OverlayError('UNSUPPORTED_CARD_ID', 'exact supported Card ID required; no name lookup')
        return card_id

    def _detail_document(self, kind, selector, scenario):
        if kind == 'historical' and selector is None and scenario is None:
            return self._explanations.detailed(self._explanations.check().to_dict()['detailed'])
        if kind == 'mechanical' and selector in self.card_ids and scenario is None:
            return MechanicalDossier(json.loads(self._mechanical)[selector])
        if kind == 'explanation' and selector in self._explanations.subject_ids and scenario is None:
            return self._explanations.explain_subject(selector)
        if kind == 'scenario' and selector in self._scenarios.subject_ids:
            return self._scenarios.evaluate(selector, scenario)
        if kind == 'explanation_comparison' and selector in COMPARISONS and scenario is None:
            return self._explanations.compare(selector)
        if kind == 'scenario_comparison' and selector in COMPARISONS:
            return self._scenarios.compare(selector, scenario)
        raise OverlayError('UNSUPPORTED_REFERENCE', 'closed detailed reference required')

    def detailed(self, reference):
        try:
            return self._read_reference(reference)
        except OverlayError:
            raise
        except (ValueError, KeyError, TypeError) as error:
            raise OverlayError('REFERENCE_INTEGRITY_REJECTED', str(error)) from None

    def _read_reference(self, reference):
        reference = json.loads(c.owned(reference, limit=8192))
        if type(reference) is not dict or set(reference) != {'kind','selector','scenario','identity','bytes','sha256','route'}:
            raise OverlayError('INVALID_REFERENCE', 'complete exact detailed reference required')
        if type(reference['kind']) is not str or (reference['selector'] is not None and type(reference['selector']) is not str):
            raise OverlayError('INVALID_REFERENCE', 'exact string selectors required')
        doc = self._detail_document(reference['kind'], reference['selector'], reference['scenario'])
        c.exact(reference, _reference(reference['kind'], reference['selector'], doc, reference['scenario']), limit=8192)
        return doc

    def _report(self, kind, selector, scenario=None, join=None):
        try:
            scenario = hp.make_scenario([]).to_dict() if scenario is None else hp.validate_scenario(scenario).to_dict()
        except ValueError as error:
            raise OverlayError('UNSUPPORTED_CONTEXT', str(error)) from None
        cards = json.loads(self._cards)
        comparison = None
        if kind in ('card', 'provenance', 'identity') and type(selector) is str and selector in cards:
            selected = [selector]
        elif kind == 'comparison' and type(selector) is str and selector in COMPARISONS:
            selected = [cid for cid, row in cards.items() if set(row['subject_ids']) & set(COMPARISONS[selector])]
            original = self._explanations.compare(selector)
            hypothetical = self._scenarios.compare(selector, scenario)
            comparison = dict(findings=original.to_dict()['comparison'],
                hypothetical_findings=hypothetical.to_dict()['comparison'],
                explanation_reference=_reference('explanation_comparison', selector, original),
                scenario_reference=_reference('scenario_comparison', selector, hypothetical, scenario),
                missing_strategic_inputs=['Declared deck, format/date, objective, alternatives and independently validated impact.',
                    'No ranking, winner, actual availability or legal interaction is established.'])
        elif kind == 'integrity' and selector is None and not scenario['assumptions']:
            selected = []
        else:
            raise OverlayError('UNSUPPORTED_SELECTOR', 'closed overlay selector required')
        if (kind == 'identity' and (type(join) is not str or join not in JOIN_NAMES)) or (kind != 'identity' and join is not None):
            raise OverlayError('UNSUPPORTED_IDENTITY_CLAIM', 'closed join selector required only for identity inspection')
        if kind in ('identity', 'provenance') and scenario['assumptions']:
            raise OverlayError('UNSUPPORTED_CONTEXT', 'identity/provenance inspection has no hypothetical dimensions')
        # Bind all submitted dimensions to the selected subject set, then route
        # only the matching accepted dependency to each original calculation.
        subjects = [sid for cid in selected for sid in cards[cid]['subject_ids']]
        descriptors = {sid: self._scenarios.evaluate(sid).to_dict()['subjects'][0]['calculation'] for sid in subjects}
        allowed = {dim for calc in descriptors.values() for dim in calc['required_hypothetical_inputs']}
        if any(row['dimension'] not in allowed for row in scenario['assumptions']):
            raise OverlayError('UNSUPPORTED_CONTEXT', 'input outside selected accepted dependencies')
        rows = []
        for cid in selected:
            row = cards[cid]
            row['subjects'] = []
            for sid in row.pop('subject_ids'):
                local = hp.make_scenario([a for a in scenario['assumptions'] if a['dimension'] in descriptors[sid]['required_hypothetical_inputs']]).to_dict()
                explained = self._explanations.explain_subject(sid)
                hypothetical = self._scenarios.evaluate(sid, local)
                er = explained.to_dict()['subjects'][0]
                hr = hypothetical.to_dict()['subjects'][0]
                row['subjects'].append(dict(subject_id=sid,
                    accepted_semantics=row['accepted_semantics'].pop(sid),
                    explanation=er, hypothetical=hr,
                    explanation_reference=_reference('explanation', sid, explained),
                    scenario_reference=_reference('scenario', sid, hypothetical, local)))
            del row['accepted_semantics']
            rows.append(row)
        status = None if join is None else rows[0]['identity']['joins'][join]['status']
        states = [s['hypothetical']['calculation']['state'] for r in rows for s in r['subjects']]
        state = 'CONFLICTING' if 'CONFLICTING' in states else 'SUPPLIED' if 'SUPPLIED' in states else 'UNSPECIFIED'
        value = dict(schema_version=VERSION, kind=kind, namespace=CARD_NAMESPACE,
            selector=selector, join=join, identity_status=status,
            policy_id=POLICY_ID, design_package_id=DESIGN_ID,
            decision_id=d.DECISION_ID, accepted_collection_id=d.COLLECTION_ID,
            decision_scope='Only the nine accepted complete subjects in their exact historical retained-text scope. Original candidates remain historically PENDING_NOT_ESTABLISHED.',
            scenario=scenario, state=state, cards=rows, comparison=comparison,
            catalog_binding=json.loads(self._binding),
            full_evidence_reference=json.loads(self._historical_reference),
            authority=dict(canonical_admission=False, execution_authority='BLOCKED',
                production_eligible=False, operator_production_snapshot_id=None,
                semantic_closure='OPEN', all_ten_activation_responsibilities='OPEN / EXECUTION_BLOCKED',
                source_policy_clearance='not_granted',
                permissions=dict.fromkeys(('private_retention','redistribution','free_service','commercial_service','ai_export'),'NOT_ESTABLISHED'),
                tier_a_restrictions='UNCHANGED_NON_PRODUCTION', global_cr_units=104, global_projections=16, land_context_units=24),
            limitations=['Historical provider assertions are not current Oracle verification or permission.',
                'Hypothetical written consequences do not establish observed state, legal activation, payment, actual/net mana, trigger events or damage.',
                'No strategic superiority, deck recommendation, financial advice or executable gameplay follows.'])
        return c.ReviewDocument._verified(c.seal(VERSION, value, 'report_id'), limit=REPORT_LIMIT)

    def card(self, namespace, card_id, scenario=None):
        return self._report('card', self._select(namespace, card_id), scenario)
    def compare(self, group, scenario=None): return self._report('comparison', group, scenario)
    def provenance(self, namespace, card_id): return self._report('provenance', self._select(namespace, card_id))
    def identity(self, namespace, card_id, join): return self._report('identity', self._select(namespace, card_id), join=join)
    def check(self): return self._report('integrity', None)
    def validate_report(self, value):
        try:
            return self._validate_report(value)
        except (ValueError, KeyError, TypeError) as error:
            raise OverlayError('REPORT_INTEGRITY_REJECTED', str(error)) from None

    def _validate_report(self, value):
        value = json.loads(c.owned(value, limit=REPORT_LIMIT))
        if type(value) is not dict or value.get('namespace') != CARD_NAMESPACE:
            raise OverlayError('INVALID_REPORT', 'complete exact overlay report required')
        expected = self._report(value.get('kind'), value.get('selector'), value.get('scenario'), value.get('join'))
        c.exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected
    def parse_report(self, raw):
        try:
            return self.validate_report(c.parse_json(raw, limit=REPORT_LIMIT))
        except (ValueError, KeyError, TypeError) as error:
            raise OverlayError('REPORT_INTEGRITY_REJECTED', str(error)) from None


def load_land_overlay(*, catalog_root, mechanical_root, review_root, cohort_root,
        decision_root, expected_profile_id, expected_query_snapshot_id,
        expected_plan_id, expected_decision_id, design_root=DESIGN_ROOT):
    """One actual query/MCI batch and one rules/decision admission, never cached.

    The only additional public seams reuse that verified reader and the admitted
    decision/explanation consumers. No neighboring private state is accessed.
    """
    try:
        matrix, pins = _design(design_root)
        catalog_root, mechanical_root = Path(catalog_root), Path(mechanical_root)
        attachment = attach_legacy_compatibility(catalog_root, game='magic',
            control_path='config/catalog_profiles/legacy-public-tier-a.json', expected_profile_id=expected_profile_id)
        mechanical = MechanicalCardIntelligence.from_attachment(attachment, data_root=mechanical_root / 'data',
            source_directory=mechanical_root / 'data/market/acquisitions' / ACQUISITION,
            expected_query_snapshot_id=expected_query_snapshot_id)
        accepted = d.load_land_decision(catalog_root=catalog_root, mechanical_root=mechanical_root,
            review_root=review_root, cohort_root=cohort_root, decision_root=decision_root,
            expected_profile_id=expected_profile_id, expected_query_snapshot_id=expected_query_snapshot_id,
            expected_plan_id=expected_plan_id, expected_decision_id=expected_decision_id,
            mechanical_reader=mechanical)
        explanations = e.from_decision(accepted)
        scenarios = h.from_explanations(explanations)
        overview = accepted.historical_overview().to_dict()
        pin_by_path = {p['path']:p for p in pins['files']}
        audit = matrix['historical_audit_path']
        historical = load_historical_admission(data_root=catalog_root / 'data',
            audit_reference=audit.removeprefix('data/'), expected_audit_sha256=pin_by_path[audit]['sha256'],
            expected_payload_sha256=pin_by_path[matrix['historical_payload_path']]['sha256'])
        # These fixed data files are independently pinned, then interpreted only
        # by their owning public contracts. No new role classification is made.
        plans = []
        for name in ('functional-role-pilot-v1.json','contextual-comparison-pilot-v1.json'):
            relative = 'config/card_intelligence/' + name
            raw = (catalog_root / relative).read_bytes()
            if hashlib.sha256(raw).hexdigest() != pin_by_path[relative]['sha256']:
                raise OverlayError('COHORT_EVIDENCE_CHANGED', 'exact pilot coverage evidence required')
            plans.append({r['card_id'] for r in json.loads(raw)['cards']})
        from repository.cards import load_card_repository
        typed_cards, _ = load_card_repository('magic', games_root=attachment.games_root)
        typed_ids = {r['id'] for r in typed_cards}
        if attachment.binding['production_eligible'] is not False:
            raise OverlayError('PRODUCTION_NOT_AUTHORIZED', 'non-production profile required')
        cards, dossiers = {}, {}
        all_cards = mechanical.query.entities(entity_type='card')
        all_printings = mechanical.query.entities(entity_type='printing')
        identifiers = mechanical.query.entities(entity_type='identifier')
        if mechanical.query.snapshot().snapshot_id != QUERY_ID or expected_profile_id != PROFILE_ID:
            raise OverlayError('CATALOG_BINDING', 'exact approved query/profile required')
        for join in matrix['cards']:
            cid, pid, provider = join['card_id'], join['printing_id'], join['provider_record_id']
            canonical = next((r for r in all_cards if r.canonical_identity == cid), None)
            printing = next((r for r in all_printings if r.canonical_identity == pid), None)
            dossier = mechanical.dossier(cid)
            dossier_value = dossier.to_dict()
            retained = overview['context']['evidence']['cards'][cid]
            proof = historical.record('printing', pid)
            if (canonical is None or canonical.canonical_values.get('card_reference') != cid
                    or printing is None or printing.canonical_values.get('card_id') != cid
                    or dossier_value['dossier_id'] != join['dossier_id']
                    or dossier_value['dossier_id'] != retained['mechanical_dossier_id']
                    or dossier_value['card_identity']['card_id'] != cid
                    or dossier_value['canonical_values'] != dict(canonical.canonical_values)
                    or dossier_value['source'] != retained['source']
                    or dossier_value['source']['provider_record_id'] != provider
                    or dossier_value['source']['oracle_id'] != cid
                    or proof['values']['identifiers'].get('scryfallId') != provider
                    or proof['values']['identifiers'].get('scryfallOracleId') != cid
                    or proof['values']['card_id'] != cid):
                raise OverlayError('IDENTITY_CONFLICT', 'exact mechanical/Card/Printing/observation relationship failed')
            edges = sorted(r.canonical_identity for r in identifiers if
                r.canonical_values.get('namespace') == 'scryfallId'
                and r.canonical_values.get('value') == provider
                and r.canonical_values.get('printing_uuid') == pid)
            memberships = sum(r.canonical_values.get('card_id') == cid for r in all_printings)
            if (edges != join['promoted_identifier_ids'] or memberships != join['printing_membership_count']
                    or cid in typed_ids or any(cid in plan for plan in plans)):
                raise OverlayError('IDENTITY_CONFLICT', 'approved identity/coverage matrix changed')
            semantics = {}
            for subject in matrix['subjects']:
                if subject['card_id'] != cid: continue
                sid = subject['subject_id']
                semantic = accepted.subject(sid).to_dict()['subjects'][0]
                explanation = explanations.explain_subject(sid).to_dict()
                if (semantic['candidate_id'] != subject['candidate_id']
                        or semantic['subject']['source_field_identity'] != subject['source_field_identity']
                        or explanation['report_id'] != subject['accepted_explanation_id']
                        or semantic['subject']['card_id'] != cid):
                    raise OverlayError('SEMANTIC_BINDING', 'exact accepted candidate/dossier/source membership required')
                semantics[sid] = dict(candidate_id=semantic['candidate_id'],
                    proposed_kind=semantic['proposed_kind'],
                    classification=semantic['original_result']['classification'],
                    ownership=semantic['written_readings']['effect_ownership'],
                    historical_status=semantic['historical_semantic_review_status'],
                    current_status=semantic['current_decision_status'], rule_refs=subject['rule_refs'])
            cards[cid] = dict(identity=dict(namespace=CARD_NAMESPACE, card_id=cid,
                display_name=canonical.canonical_values['name'],
                printing=dict(namespace=PRINTING_NAMESPACE, printing_id=pid, historical_membership_count=memberships,
                    scope='Only this retained observation is accepted; no all-Printing text equivalence.'),
                observation=dict(namespace=OBSERVATION_NAMESPACE, provider_record_id=provider,
                    acquisition=retained['source']),
                joins=dict(historical_correspondence=dict(status='ESTABLISHED',
                    audit_reference=audit, audit_sha256=pin_by_path[audit]['sha256'],
                    payload_sha256=pin_by_path[matrix['historical_payload_path']]['sha256'],
                    payload_reference=matrix['historical_payload_path'], payload_pointer=join['payload_pointer'],
                    evidence_references=proof['evidence_references']),
                    current_identifier_edge=dict(status='ESTABLISHED' if edges else 'IDENTITY_NOT_ESTABLISHED', identifier_ids=edges),
                    operator_production=dict(status='IDENTITY_NOT_ESTABLISHED', snapshot_id=None),
                    typed_seed=dict(status='IDENTITY_NOT_ESTABLISHED'),
                    functional_role_pilot=dict(status='NOT_IN_SUPPORTED_COHORT'),
                    contextual_comparison_pilot=dict(status='NOT_IN_SUPPORTED_COHORT'))),
                mechanical=dict(dossier_id=dossier_value['dossier_id'],
                    facts={k:dossier_value['fields'][k] for k in ('oracle_text','type_line','colors','color_identity','keywords')},
                    limitation='Literal historical provider assertions only; metadata is not reviewed rules semantics.',
                    detailed_reference=_reference('mechanical', cid, dossier)),
                subject_ids=list(semantics), accepted_semantics=semantics)
            dossiers[cid] = dossier_value
        mechanical.verify_inputs()
        attachment.verify_unchanged()
        result = object.__new__(LandEvidenceOverlay)
        object.__setattr__(result, '_cards', c.owned(cards))
        # Full mechanical documents keep their owning numeric representation;
        # no coercion into the overlay's integer-only report contract.
        object.__setattr__(result, '_mechanical', json.dumps(dossiers, sort_keys=True,
            separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
        object.__setattr__(result, '_explanations', explanations)
        object.__setattr__(result, '_scenarios', scenarios)
        object.__setattr__(result, '_binding', c.owned(dict(profile_id=PROFILE_ID,
            query_snapshot_id=QUERY_ID, capability_tier=attachment.binding['capability_tier'])))
        object.__setattr__(result, '_historical_reference', c.owned(_reference('historical', None, accepted.historical_overview())))
        result.check()
        return result
    except OverlayError:
        raise
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        raise OverlayError('EVIDENCE_ADMISSION_REJECTED', str(error)) from None


def render_overlay(document):
    """Readable evidence view; canonical mode retains every exact pointer."""
    value = document.to_dict()
    lines = ['MTG Lab — six-land exact-ID evidence overlay', value['decision_scope'],
        'Report: ' + value['report_id'], 'Policy: ' + value['policy_id'],
        'Decision: ' + value['decision_id'], 'Collection: ' + value['accepted_collection_id'],
        'Explicit hypothetical assumptions: ' + json.dumps(value['scenario']['assumptions']),
        'State: ' + value['state']]
    if value['join'] is not None: lines.append(value['join'] + ': ' + value['identity_status'])
    for row in value['cards']:
        identity = row['identity']
        lines += ['', identity['display_name'] + ' — ' + identity['namespace'] + ':' + identity['card_id'],
            'Printing (' + identity['printing']['namespace'] + '): ' + identity['printing']['printing_id']
                + '; historical memberships: ' + str(identity['printing']['historical_membership_count']),
            identity['printing']['scope'],
            'Observation (' + identity['observation']['namespace'] + '): ' + identity['observation']['provider_record_id'],
            'Joins: ' + '; '.join(k + '=' + v['status'] for k,v in identity['joins'].items()),
            'Mechanical dossier: ' + row['mechanical']['dossier_id'],
            'Retained type: ' + str(row['mechanical']['facts']['type_line']['value']),
            row['mechanical']['limitation']]
        for subject in row['subjects']:
            semantic = subject['accepted_semantics']; calc = subject['hypothetical']['calculation']
            provenance = subject['explanation']['provenance']
            lines += ['', subject['subject_id'] + ': ' + subject['explanation']['selected_passage'],
                'Candidate: ' + semantic['candidate_id'],
                'Classification: ' + semantic['proposed_kind'] + ' / ' + semantic['classification'],
                'Historical ' + semantic['historical_status'] + '; current ' + semantic['current_status']]
            for finding in subject['explanation']['findings']:
                lines.append(finding['category'] + ': ' + finding['text'])
            lines += ['Hypothetical ' + calc['state'] + ': ' + json.dumps(calc['conditional_written_output'], sort_keys=True),
                'Separate written cost: ' + str(calc['written_cost']),
                'Missing inputs: ' + ', '.join(calc['missing_inputs']), 'Conflict: ' + str(calc['conflict']),
                'Retained unknowns: ' + ' '.join(subject['hypothetical']['retained_unknowns']),
                'Calculation: ' + calc['calculation_id'],
                'Assessment: ' + provenance['assessment_id'],
                'Behavior: ' + provenance['behavior_calculation_id'] + '; composition: ' + provenance['composition_id'],
                'Rules: ' + ', '.join(semantic['rule_refs']),
                'Detailed explanation: ' + subject['explanation_reference']['identity'],
                'Detailed scenario: ' + subject['scenario_reference']['identity']]
    if value['comparison']:
        comparison = value['comparison']
        lines.append('Shared capabilities: ' + json.dumps(comparison['findings']['shared_capabilities'],sort_keys=True))
        for kind in ('shared','differences'):
            for dimension in comparison['findings'][kind]:
                lines.append(kind + ' ' + dimension['dimension'] + ': ' + json.dumps(dimension['premises'],sort_keys=True))
        lines += [comparison['findings']['limitation'], *comparison['missing_strategic_inputs'],
            'Original comparison: ' + comparison['explanation_reference']['identity'],
            'Hypothetical comparison: ' + comparison['scenario_reference']['identity']]
    lines += ['', 'Full historical evidence: ' + json.dumps(value['full_evidence_reference'],sort_keys=True),
        'Use provenance canonical JSON for exact source-field, candidate, assessment and detailed-reference pointers.',
        *value['limitations'], *hp.UNKNOWN_GAME_INPUTS,
        'Authority: ' + json.dumps(value['authority'],sort_keys=True), '']
    output = '\n'.join(lines)
    if len(output.encode()) > READABLE_LIMIT: raise OverlayError('READABLE_SIZE', 'readable byte bound')
    return output
