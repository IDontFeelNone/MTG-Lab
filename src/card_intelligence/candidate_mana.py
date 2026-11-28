"""Pending interpretations of a closed written-ability family, never admission.

Only the existing candidate inspector supplies evidence. The internal recognizer
has no evidence authority. Native review criteria and rules calculations retain
their original ownership and conditional meaning.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from card_rules_pilot import contract as c
from card_rules_pilot import reasoning_policy as review_policy
from .mechanics import MechanicalCardIntelligence, MechanicalEvidenceError
from .rules_reasoning import CONTEXT_ID, load_rules_reasoner, RulesReasoningError
from providers.mtgjson.private_policy import SourcePolicyError

VERSION = 'candidate-activated-mana-interpretation-v1'
POLICY_VERSION = 'single-written-tap-fixed-mana-v1'
TEXT_BYTES = 8192
REPORT_BYTES = 65536
MAX_REQUESTS = 16
HYPOTHESIS = 'TREAT_PENDING_PROPOSAL_AS_HYPOTHESIS_ONLY'
_PATTERN = re.compile(r'(?P<cost>\{T\})[ ]{0,8}:[ ]{0,8}(?P<effect>Add (?P<mana>(?:\{[WUBRGC]\}){1,8}))\.')
_CODE = ('card_intelligence/candidate_mana.py', 'card_intelligence/mechanics.py',
         'providers/mtgjson/oracle_evidence.py', 'card_rules_pilot/contract.py',
         'card_rules_pilot/reasoning_policy.py', 'card_rules_pilot/land_context.py',
         'card_intelligence/rules_reasoning.py', 'card_intelligence/mana_window.py')
_ROOT = Path(__file__).resolve().parents[1]
_AUTHORITY = dict(review_status='requires_review', human_attestation=None,
    semantic_authority='NOT_ESTABLISHED', canonical_admission=False,
    admitted_dossier_populated=False, current_oracle_verified=False,
    legal_activation='NOT_ESTABLISHED', actual_mana_output='UNKNOWN',
    format_legality='NOT_ESTABLISHED', execution_authority='BLOCKED',
    game_actions_performed=False, external_ai_export=False)
_GAPS = ('current_game_state', 'source_control', 'source_zone', 'source_tapped_status',
         'timing_restrictions', 'ability_restrictions', 'external_effects',
         'self_replacement_effects', 'resource_availability', 'activation_legality',
         'actual_mana_produced')


class CandidateInterpretationError(c.PilotError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)

    def as_dict(self):
        return dict(status='REFUSED', code=self.code, reason=str(self), authority=dict(_AUTHORITY))


def _require(value, reason, code='INVALID_INPUT'):
    if not value:
        raise CandidateInterpretationError(code, reason)


def _code_identity():
    pins = []
    for name in _CODE:
        path = _ROOT/name
        _require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 512*1024,
                 'bounded packaged implementation required', 'IMPLEMENTATION_MISMATCH')
        pins.append(dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return c.identity('candidate-mana-implementation-v1', dict(files=pins), 'implementation_id')


_IMPORTED_CODE = _code_identity()


def _request(value):
    try:
        value = json.loads(c.owned(value, limit=8192))
    except (c.PilotError, ValueError, TypeError):
        raise CandidateInterpretationError('INVALID_INPUT', 'bounded closed request required') from None
    _require(type(value) is dict and set(value) == {'card_id', 'printing_id', 'evidence_id', 'reasoning'},
             'exact identity, occurrence selection and optional reasoning fields required')
    for key in ('card_id', 'printing_id'):
        _require(type(value[key]) is str and 0 < len(value[key]) <= 256, 'bounded exact identities required')
    _require(value['evidence_id'] is None or (type(value['evidence_id']) is str and
             re.fullmatch(r'sha256:[0-9a-f]{64}', value['evidence_id'])), 'exact occurrence identity required')
    reason = value['reasoning']
    if reason is not None:
        _require(type(reason) is dict and set(reason) == {'interpretation_premise', 'characteristics', 'state'}
                 and reason['interpretation_premise'] == HYPOTHESIS,
                 'explicit hypothetical use of pending interpretation required', 'HYPOTHESIS_REQUIRED')
        _require(type(reason['characteristics']) is dict and set(reason['characteristics']) <=
                 {'source_is_planeswalker', 'self_replacement', 'other_replacement', 'chosen_targets'},
                 'written characteristics cannot be overridden')
        _require(type(reason['state']) is dict and set(reason['state']) <=
                 {'mana_payment_request', 'priority', 'same_ability_unresolved', 'current_mana_output'},
                 'closed separate game-state assumptions required')
    return value


def _span(text, start, end):
    """Half-open UTF-8 offsets, always against the original complete field."""
    return dict(start=len(text[:start].encode()), end=len(text[:end].encode()), encoding='UTF-8')


def _recognize(text):
    """Pure diagnostic/interpretation, with no source or semantic authority."""
    if type(text) is not str:
        return dict(status='UNSUPPORTED', diagnostics=['UNSUPPORTED_TEXT_TYPE'], proposal=None)
    if len(text.encode()) > TEXT_BYTES:
        return dict(status='UNSUPPORTED', diagnostics=['TEXT_BUDGET_EXCEEDED'], proposal=None)
    match = _PATTERN.fullmatch(text)
    if match is None:
        codes = []
        if any(x in text for x in ('"', '“', '”', 'gains ', 'has ')):
            codes.append('QUOTED_OR_GRANTED_ABILITY')
        if '\n' in text or text.count(':') > 1:
            codes.append('ADDITIONAL_OR_AMBIGUOUS_ABILITY')
        if re.search(r'\btarget\b', text, re.IGNORECASE): codes.append('TARGETING_SYNTAX')
        if re.search(r'\b(if|unless|for each|choose|any color)\b', text, re.IGNORECASE):
            codes.append('CONDITIONAL_OR_CHOICE_OUTPUT')
        if '{X}' in text or re.search(r'\bthat much\b', text): codes.append('VARIABLE_OUTPUT')
        if ':' in text and text.split(':', 1)[0].strip() != '{T}': codes.append('UNSUPPORTED_COST')
        prefix = _PATTERN.match(text)
        if prefix: codes.append('UNPARSED_SUFFIX')
        if text.startswith('{T}: Add ') and not text.endswith('.'): codes.append('INCOMPLETE_PASSAGE')
        if not codes: codes.append('UNSUPPORTED_SYNTAX')
        status = ('AMBIGUOUS' if 'ADDITIONAL_OR_AMBIGUOUS_ABILITY' in codes else
                  'PARTIAL_RECOGNITION' if '{T}' in text or 'Add ' in text else 'UNSUPPORTED')
        return dict(status=status, diagnostics=sorted(codes), proposal=None)
    spans = {key: _span(text, *match.span(key)) for key in ('cost', 'effect', 'mana')}
    spans['whole_passage'] = _span(text, 0, len(text))
    symbols = re.findall(r'\{([WUBRGC])\}', match['mana'])
    traits = dict(ability_kind='ACTIVATED', target_requirement='NONE', potential_mana='YES',
                  loyalty_symbol_in_cost='NO', cost_library_movement='NO', effect_library_movement='NO')
    whole = ['whole_passage']
    derivations = dict(ability_kind=whole, target_requirement=whole,
        potential_mana=['effect'], loyalty_symbol_in_cost=['cost'],
        cost_library_movement=['cost'], effect_library_movement=['effect'])
    proposal = dict(proposed_kind='proposed_activated_ability',
        review=dict(status='requires_review', human_attestation=None, canonical_admission=False),
        written_characteristics=dict(cost=dict(literal=match['cost'], tap_symbol=True, span_ref='cost'),
            effect=dict(literal=match['effect'], proposed_kind='fixed_mana_addition', span_ref='effect',
                        symbols=[dict(symbol=s, quantity=symbols.count(s), derivation=dict(
                            operation='COUNT_LITERAL_SYMBOL_TOKENS', span_ref='mana'))
                            for s in 'WUBRGC' if s in symbols]),
            expressed_conditionality=dict(value='NONE_IN_COMPLETE_SUPPORTED_PASSAGE', span_ref='whole_passage')),
        proposed_rules_characteristics={k:dict(value=v, review_status='requires_review',
            derivation=dict(policy=POLICY_VERSION, span_refs=derivations[k])) for k,v in traits.items()},
        spans=spans, normalization=dict(original_text_unchanged=True,
            canonical_spelling='{T}: '+match['effect']+'.', operation='ASCII_COLON_SPACING_ONLY'),
        scope='PROPOSED_READING_OF_COMPLETE_WRITTEN_PASSAGE_NOT_ACCEPTED_CARD_SEMANTICS')
    return dict(status='SUPPORTED_COMPLETE', diagnostics=[], proposal=proposal)


def _criteria(proposal):
    definitions = review_policy.policy_document()['criterion_definitions']
    supported = {'activated_kind', 'no_target', 'potential_mana', 'not_loyalty',
                 'no_library_cost_movement', 'no_library_effect_movement'}
    rows = [dict(criterion_id=row['criterion_id'], state=(
        'proposed_satisfied' if row['criterion_id'] in supported else
        'unknown' if row['criterion_id'] in ('self_replacement_considered', 'other_replacements_disregarded')
        else 'inapplicable'), rule_refs=row['rule_refs']) for row in definitions]
    result = review_policy.compute(proposed_kind=proposal['proposed_kind'], criteria=rows,
                                  kind_evidence_refs=['selected_passage', 'rule:605.1a'])
    return dict(policy_id=review_policy.POLICY_ID, criteria=rows, native_result=result,
        evidence_refs=dict(selected_passage='proposal.spans.whole_passage',
            full_oracle_field='proposal.spans.whole_passage', retained_rules_context=CONTEXT_ID),
        interpretation_review_status='requires_review')


@dataclass(frozen=True, init=False)
class CandidateManaInterpreter:
    _query: object
    _controls: dict
    _review_root: Path
    _implementation: str

    def assess(self, value):
        request = _request(value)
        _require(_code_identity() == self._implementation == _IMPORTED_CODE,
                 'packaged interpretation implementation changed', 'IMPLEMENTATION_MISMATCH')
        try:
            reasoner = load_rules_reasoner(review_root=self._review_root, expected_context_id=CONTEXT_ID)
            inspected = MechanicalCardIntelligence.inspect_mtgjson_candidate(self._query,
                **self._controls, card_id=request['card_id'], printing_id=request['printing_id'])
        except (MechanicalEvidenceError, SourcePolicyError, RulesReasoningError, c.PilotError, OSError):
            raise CandidateInterpretationError('EVIDENCE_REFUSED', 'owning candidate or rules evidence refused') from None
        rows = inspected['evidence']['occurrences']
        chosen = [r for r in rows if request['evidence_id'] is None or r['evidence_id'] == request['evidence_id']]
        if request['evidence_id'] is not None:
            _require(len(chosen) == 1, 'selected occurrence not present in verified evidence', 'OCCURRENCE_MISMATCH')
        result = dict(status='EVIDENCE_UNRESOLVED', diagnostics=['MISSING_OCCURRENCE'], proposal=None)
        selected = None
        if inspected['evidence']['status'] == 'WITHHELD':
            result.update(status='WITHHELD', diagnostics=sorted({x for row in rows for x in row['conditions']}
                                                             | {'WITHHELD_EVIDENCE'}))
        elif len(chosen) > 1:
            result.update(status='AMBIGUOUS', diagnostics=['MULTIPLE_OCCURRENCES'])
        elif len(chosen) == 1:
            selected = chosen[0]
            text = selected['text']
            if (selected['candidate_status'] != 'UNADMITTED_SOURCE_EVIDENCE' or selected['conditions']
                    or text['status'] != 'SUPPLIED' or text['face_boundary'].get('kind') != 'WHOLE_CARD'):
                result.update(diagnostics=['UNRESOLVED_OR_UNSUPPORTED_TEXT_OWNERSHIP'])
            else:
                result = _recognize(text['value'])
        criteria = _criteria(result['proposal']) if result['proposal'] is not None else None
        native = None
        if request['reasoning'] is not None:
            _require(result['proposal'] is not None, 'complete supported proposal required for reasoning',
                     'INCOMPLETE_INTERPRETATION')
            assumptions = request['reasoning']
            traits = {k:v['value'] for k,v in result['proposal']['proposed_rules_characteristics'].items()}
            traits.update(dict(source_is_planeswalker='UNKNOWN', self_replacement='UNKNOWN',
                               other_replacement='UNKNOWN', chosen_targets='UNKNOWN'))
            traits.update(assumptions['characteristics'])
            state = dict(mana_payment_request='UNKNOWN', priority='UNKNOWN',
                         same_ability_unresolved='UNKNOWN', current_mana_output='UNKNOWN')
            state.update(assumptions['state'])
            try:
                native = reasoner.assess(dict(schema_version='real-card-rules-reasoning-input-v1',
                    question='ACTIVATED_MANA_PAYMENT_TIMING_EXCEPTION', scenario_id=selected['evidence_id'],
                    evidence_context_id=CONTEXT_ID, characteristics=traits, state=state)).to_dict()
            except RulesReasoningError as error:
                raise CandidateInterpretationError(error.code, 'native conditional reasoning refused premises') from None
        evidence = dict(inspection_id=inspected['inspection_id'], query_snapshot_id=inspected['query_snapshot_id'],
            import_report_id=inspected['evidence']['report_id'],
            source_use_profile_id=inspected['evidence']['source_use_profile_id'],
            occurrence_ids=[r['evidence_id'] for r in rows], selected_occurrence=None)
        if selected is not None:
            evidence['selected_occurrence'] = {k:selected[k] for k in ('evidence_id', 'card_id', 'printing_id',
                'source_release', 'source_partition', 'source_partition_sha256', 'source_row',
                'source_record_sha256', 'provenance_sha256', 'notice_sha256')}
            text = selected['text']
            evidence['selected_occurrence']['text'] = dict(source_field=text['source_field'],
                source_pointer=text['source_pointer'], face_boundary=text['face_boundary'], status=text['status'])
            if type(text.get('value')) is str:
                evidence['selected_occurrence']['text'].update(
                    sha256=hashlib.sha256(text['value'].encode()).hexdigest(), bytes=len(text['value'].encode()))
        body = dict(schema_version=VERSION, request=request, policy_version=POLICY_VERSION,
            implementation_id=self._implementation, evidence=evidence, **result, review_criteria=criteria,
            native_conditional_reasoning=native,
            reasoning_basis='PENDING_INTERPRETATION_AS_HYPOTHESIS_NOT_ACCEPTED_SEMANTICS' if native else None,
            unresolved_characteristics=list(_GAPS), authority=dict(_AUTHORITY),
            limitations=['Source integrity does not establish current Oracle or correct semantics.',
                'Whole-field recognition supports only the closed written family; no external Card context is inferred.',
                'Written mana is not actual output; written tap cost is not current ability to tap.',
                'Conditional native findings do not establish legal activation or semantic acceptance.'])
        try:
            return c.ReviewDocument._verified(c.seal(VERSION, body, 'report_id'), limit=REPORT_BYTES)
        except c.PilotError:
            raise CandidateInterpretationError('REPORT_BUDGET', 'bounded interpretation report required') from None

    def replay(self, raw, *, expected_report_id):
        try:
            value = c.parse_json(raw, limit=REPORT_BYTES)
            _require(type(expected_report_id) is str and value.get('report_id') == expected_report_id,
                     'independently pinned interpretation identity required', 'REPORT_ID_MISMATCH')
            expected = self.assess(value['request'])
            c.exact(value, expected.to_dict(), limit=REPORT_BYTES)
            return expected
        except CandidateInterpretationError:
            raise
        except (c.PilotError, KeyError, TypeError):
            raise CandidateInterpretationError('INVALID_REPORT', 'report does not reproduce from verified evidence') from None

    def assess_many(self, requests):
        _require(type(requests) is list and 0 < len(requests) <= MAX_REQUESTS,
                 'one to sixteen explicit requests required', 'COVERAGE_BUDGET')
        # Own and cap the complete population before reading any evidence.
        requests = json.loads(c.owned(requests, limit=MAX_REQUESTS*8192))
        normalized = [_request(r) for r in requests]
        _require(len({c.canonical(r) for r in normalized}) == len(normalized), 'duplicate coverage request refused')
        reports, refusals, counts, diagnostics = [], [], Counter(), Counter()
        for index, request in enumerate(normalized):
            try:
                report = self.assess(request).to_dict()
                reports.append(dict(request_index=index, report_id=report['report_id'], status=report['status']))
                counts[report['status']] += 1
                diagnostics.update(report['diagnostics'])
            except CandidateInterpretationError as error:
                refusals.append(dict(request_index=index, code=error.code))
                counts['REFUSED'] += 1
        value = c.seal('candidate-mana-coverage-v1', dict(schema_version='candidate-mana-coverage-v1',
            requests=normalized, evaluated_requests=len(normalized), counts=dict(sorted(counts.items())),
            overlapping_diagnostics=dict(sorted(diagnostics.items())), reports=reports, refusals=refusals,
            policy_version=POLICY_VERSION, implementation_id=self._implementation,
            coverage_scope='ONLY_EXPLICIT_EVALUATED_REQUESTS_NOT_ORACLE_CORPUS', authority=dict(_AUTHORITY)), 'report_id')
        return c.ReviewDocument._verified(value, limit=MAX_REQUESTS*8192)

    def replay_coverage(self, raw, *, expected_report_id):
        try:
            value = c.parse_json(raw, limit=MAX_REQUESTS*8192)
            _require(value.get('report_id') == expected_report_id,
                     'independently pinned coverage identity required', 'REPORT_ID_MISMATCH')
            expected = self.assess_many(value['requests'])
            c.exact(value, expected.to_dict(), limit=MAX_REQUESTS*8192)
            return expected
        except CandidateInterpretationError:
            raise
        except (c.PilotError, KeyError, TypeError):
            raise CandidateInterpretationError('INVALID_REPORT', 'coverage does not reproduce') from None


def load_candidate_mana_interpreter(query, *, expected_query_snapshot_id, evidence_directory,
                                    profile, expected_report_id, review_root,
                                    expected_context_id=CONTEXT_ID):
    """Trusted host selects native verified controls; request JSON cannot install them."""
    load_rules_reasoner(review_root=review_root, expected_context_id=expected_context_id)
    result = object.__new__(CandidateManaInterpreter)
    object.__setattr__(result, '_query', query)
    object.__setattr__(result, '_controls', dict(expected_query_snapshot_id=expected_query_snapshot_id,
        evidence_directory=Path(evidence_directory).absolute(), profile=profile, expected_report_id=expected_report_id))
    object.__setattr__(result, '_review_root', Path(review_root).absolute())
    object.__setattr__(result, '_implementation', _code_identity())
    _require(result._implementation == _IMPORTED_CODE, 'implementation changed after import', 'IMPLEMENTATION_MISMATCH')
    return result
