"""Conservative pending subjects from freshly inspected candidate evidence.

The predecessor owns mana recognition; this module owns only source accounting,
local boundaries and hypothesis scope. Nothing here admits semantics or actions.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from . import candidate_mana as v1
from .mechanics import MechanicalCardIntelligence, MechanicalEvidenceError
from .rules_reasoning import CONTEXT_ID, RulesReasoningError, load_rules_reasoner
from card_rules_pilot import contract as c
from providers.mtgjson.private_policy import SourcePolicyError

VERSION = 'candidate-ability-segmentation-v1'
POLICY = 'field-start-tap-passages-lf-opaque-stop-v1'
TEXT_BYTES = 8192
REQUEST_BYTES = 8192
REPORT_BYTES = 65536
MAX_SEGMENTS = 16
MAX_UNRESOLVED = 1
MAX_REGIONS = 33
MAX_REQUESTS = 16
COVERAGE_BYTES = 131072
SCOPE_HYPOTHESIS = 'HYPOTHETICAL_NO_RELEVANT_SURROUNDING_EFFECTS'
_ROOT = Path(__file__).resolve().parents[1]
_CODE = ('card_intelligence/candidate_abilities.py', *v1._CODE)


class CandidateSegmentationError(v1.CandidateInterpretationError):
    pass


def _require(condition, reason, code='INVALID_INPUT'):
    if not condition:
        raise CandidateSegmentationError(code, reason)


def _id(domain, value):
    return c.identity(domain, value, 'id')


def _implementation():
    pins = []
    for name in _CODE:
        path = _ROOT / name
        _require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 512*1024,
                 'bounded packaged implementation required', 'IMPLEMENTATION_MISMATCH')
        pins.append(dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return _id('candidate-ability-implementation-v1', dict(files=pins))


_IMPORTED_CODE = _implementation()


def _request(raw):
    try:
        value = json.loads(c.owned(raw, limit=REQUEST_BYTES))
        # The existing identity and hypothesis vocabulary remains authoritative.
        base = dict(value, reasoning=None)
        v1._request(base)
        reason = value['reasoning']
        if reason is not None:
            _require(type(reason) is dict and set(reason) == {
                'segment_id', 'interpretation_premise', 'characteristics', 'state', 'scope_assumption'},
                'one closed selected-segment reasoning request required')
            _require(type(reason['segment_id']) is str and len(reason['segment_id']) == 71
                     and reason['segment_id'].startswith('sha256:'), 'exact selected segment required')
            v1._request(dict(value, reasoning={k:reason[k] for k in (
                'interpretation_premise', 'characteristics', 'state')}))
            scope = reason['scope_assumption']
            _require(scope is None or (type(scope) is dict and set(scope) == {
                'field_id', 'segment_id', 'dependency_id', 'assumption'}
                and scope['assumption'] == SCOPE_HYPOTHESIS),
                'closed hypothetical context scope required', 'SCOPE_ASSUMPTION_REQUIRED')
        return value
    except CandidateSegmentationError:
        raise
    except (c.PilotError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        raise CandidateSegmentationError('INVALID_INPUT', 'bounded closed request required') from None


def _tap_header(text, start):
    """Boundary witness only: existing written tap-cost spelling, not effects."""
    if not text.startswith('{T}', start):
        return None
    i = start + 3
    for _ in range(8):
        if i < len(text) and text[i] == ' ': i += 1
    if i >= len(text) or text[i] != ':': return None
    i += 1
    for _ in range(8):
        if i < len(text) and text[i] == ' ': i += 1
    if i >= len(text) or text[i].isspace(): return None
    if not ('A' <= text[i] <= 'Z'): return None
    return i


def _partition(text):
    """Pure pending boundary calculation; it confers no evidence authority.

    P (LF P)* [LF U], anchored at field start. P is recognized by V1; U
    starts with the same tap header and consumes ALL remaining text. Never
    resume after U. Any uncertain separator/continuation holds the whole field.
    """
    _require(type(text) is str, 'literal supplied field required')
    _require(len(text) <= TEXT_BYTES, 'complete source field exceeds bound', 'RESOURCE_BUDGET')
    try: raw = text.encode('utf-8')
    except UnicodeError:
        raise CandidateSegmentationError('INVALID_FIELD', 'valid UTF-8 field required') from None
    _require(len(raw) <= TEXT_BYTES, 'complete source field exceeds bound', 'RESOURCE_BUDGET')

    def unresolved(code):
        return [(0, len(text), 'UNRESOLVED')], [code]

    if not text: return unresolved('EMPTY_FIELD')
    if any(x in text for x in ('"', "'", '“', '”', '‘', '’', '(', ')')):
        return unresolved('QUOTED_GRANTED_OR_REMINDER_CONTEXT')
    if any(ord(ch) < 32 and ch != '\n' or ord(ch) == 127 for ch in text):
        return unresolved('UNSUPPORTED_SEPARATOR_OR_CONTROL')
    depth = 0
    for ch in text:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        if depth not in (0, 1): return unresolved('UNBALANCED_OR_NESTED_SYMBOL')
    if depth: return unresolved('UNBALANCED_OR_NESTED_SYMBOL')
    if not text.endswith('.'): return unresolved('TRUNCATED_OR_UNSUPPORTED_END')
    regions, start, count = [], 0, 0
    while True:
        match = v1._PATTERN.match(text, start)
        if match is None:
            if count and _tap_header(text, start) is not None:
                regions.append((start, len(text), 'UNRESOLVED'))
                return regions, ['OPAQUE_REMAINDER_NOT_SEGMENTED']
            return unresolved('UNSUPPORTED_OR_UNCERTAIN_PREFIX')
        end = match.end()
        if end != len(text) and (text[end] != '\n' or _tap_header(text, end+1) is None):
            return unresolved('UNCERTAIN_CONTINUATION_OR_SEPARATOR')
        _require(v1._recognize(text[start:end])['status'] == 'SUPPORTED_COMPLETE',
                 'complete predecessor recognition required', 'IMPLEMENTATION_MISMATCH')
        count += 1
        _require(count <= MAX_SEGMENTS, 'segment count exceeds bound', 'RESOURCE_BUDGET')
        regions.append((start, end, 'SUPPORTED_ABILITY'))
        if end == len(text): return regions, []
        regions.append((end, end+1, 'SEPARATOR'))
        start = end + 1


def _materialize(text, evidence, implementation):
    ranges, diagnostics = _partition(text)
    raw = text.encode('utf-8')
    field = dict(value=text, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                 span=v1._span(text, 0, len(text)))
    field['field_id'] = _id('candidate-source-field-v1', dict(evidence=evidence,
        sha256=field['sha256'], bytes=field['bytes']))
    regions, segments = [], []
    for ordinal, (start, end, kind) in enumerate(ranges):
        literal = text[start:end]
        region = dict(kind=kind, ordinal=ordinal, value=literal,
            span=v1._span(text, start, end), sha256=hashlib.sha256(literal.encode()).hexdigest())
        region['region_id'] = _id('candidate-text-region-v1', dict(field_id=field['field_id'],
            policy=POLICY, implementation=implementation, **region))
        regions.append(region)
        if kind != 'SUPPORTED_ABILITY': continue
        sid = _id('candidate-ability-segment-v1', dict(field_id=field['field_id'],
            evidence=evidence, ordinal=len(segments), span=region['span'],
            sha256=region['sha256'], policy=POLICY, implementation=implementation))
        proposal = v1._recognize(literal)['proposal']
        relative = deepcopy(proposal['spans'])
        for span in proposal['spans'].values():
            span['start'] += region['span']['start']; span['end'] += region['span']['start']
        criteria = v1._criteria(proposal)
        # V1's two refs coincide only for a whole-field subject. Do not carry
        # that coincidence into the new versioned, multi-subject wrapper.
        criteria['evidence_refs'] = dict(
            selected_passage=dict(field_id=field['field_id'], span=region['span']),
            full_oracle_field=dict(field_id=field['field_id'], span=field['span']),
            retained_rules_context=CONTEXT_ID)
        before = dict(kind='FIELD_START') if start == 0 else dict(
            kind='PRECEDING_SUPPORTED_PASSAGE_AND_LF', separator_span=v1._span(text, start-1, start))
        after = dict(kind='FIELD_END') if end == len(text) else dict(
            kind='LF_AND_NEXT_TAP_HEADER', separator_span=v1._span(text, end, end+1),
            header_span=v1._span(text, end+1, _tap_header(text, end+1)))
        segments.append(dict(segment_id=sid, ordinal=len(segments), region_id=region['region_id'],
            identity_scope='LOCAL_PENDING_SUBJECT_NOT_CANONICAL_ABILITY',
            boundary=dict(status='SUPPORTED_WRITTEN_BOUNDARY_REQUIRES_REVIEW', before=before, after=after),
            proposal=proposal, review_criteria=criteria,
            transformation=dict(operation='SEGMENT_UTF8_OFFSETS_PLUS_ORIGINAL_FIELD_START',
                relative_spans=relative, original_field_start=region['span']['start'])))
    _require(len(regions) <= MAX_REGIONS and sum(r['kind']=='UNRESOLVED' for r in regions) <= MAX_UNRESOLVED,
             'region count exceeds bound', 'RESOURCE_BUDGET')
    position = 0
    for region in regions:
        _require(region['span']['start'] == position, 'source accounting gap or overlap', 'ACCOUNTING_MISMATCH')
        position = region['span']['end']
    reconstructed = ''.join(r['value'] for r in regions).encode()
    _require(position == len(raw) and reconstructed == raw, 'exact source reconstruction required', 'ACCOUNTING_MISMATCH')
    unresolved = [r['region_id'] for r in regions if r['kind']=='UNRESOLVED']
    complete = bool(segments) and not unresolved
    coverage = dict(byte_accounting=dict(status='COMPLETE', source_bytes=len(raw), accounted_bytes=position,
        reconstructed_sha256=hashlib.sha256(reconstructed).hexdigest()),
        segmentation='COMPLETE_SUPPORTED_WRITTEN_FAMILY' if complete else 'INCOMPLETE',
        established_local_subjects=len(segments), supported_mechanical_proposals=len(segments),
        unresolved_regions=len(unresolved), unresolved_bytes=sum(
            len(r['value'].encode()) for r in regions if r['kind']=='UNRESOLVED'),
        total_ability_count=len(segments) if complete else None,
        total_ability_count_scope='PENDING_CLOSED_WRITTEN_FAMILY_NOT_ACCEPTED_CARD_SEMANTICS',
        card_mechanical_completeness='NOT_ESTABLISHED', semantic_review='requires_review')
    dependencies = dict(field_id=field['field_id'], segment_ids=[s['segment_id'] for s in segments],
        unresolved_region_ids=unresolved, surrounding_effects='UNKNOWN',
        independent_abilities='NOT_ESTABLISHED',
        scope_hypothesis_required=bool(segments) and (len(segments)>1 or bool(unresolved)))
    dependencies['dependency_id'] = _id('candidate-cross-ability-context-v1', dependencies)
    return dict(field=field, regions=regions, segments=segments, coverage=coverage,
        dependencies=dependencies, diagnostics=diagnostics,
        status='SUPPORTED_SEGMENTATION' if complete else 'PARTIAL_SEGMENTATION' if segments else 'UNRESOLVED')


def _reason(reason, material, reasoner):
    if reason is None: return None
    selected = [s for s in material['segments'] if s['segment_id'] == reason['segment_id']]
    _require(len(selected) == 1, 'independently supported selected boundary required', 'SEGMENT_MISMATCH')
    dependencies = material['dependencies']
    expected_scope = dict(field_id=material['field']['field_id'], segment_id=reason['segment_id'],
        dependency_id=dependencies['dependency_id'], assumption=SCOPE_HYPOTHESIS)
    _require(reason['scope_assumption'] == (expected_scope if dependencies['scope_hypothesis_required'] else None),
             'exact hypothetical surrounding-context scope required', 'SCOPE_ASSUMPTION_REQUIRED')
    traits = {k:v['value'] for k,v in selected[0]['proposal']['proposed_rules_characteristics'].items()}
    traits.update(dict(source_is_planeswalker='UNKNOWN', self_replacement='UNKNOWN',
                       other_replacement='UNKNOWN', chosen_targets='UNKNOWN'))
    traits.update(reason['characteristics'])
    state = dict(mana_payment_request='UNKNOWN', priority='UNKNOWN',
                 same_ability_unresolved='UNKNOWN', current_mana_output='UNKNOWN')
    state.update(reason['state'])
    try:
        return reasoner.assess(dict(schema_version='real-card-rules-reasoning-input-v1',
            question='ACTIVATED_MANA_PAYMENT_TIMING_EXCEPTION', scenario_id=reason['segment_id'],
            evidence_context_id=CONTEXT_ID, characteristics=traits, state=state)).to_dict()
    except RulesReasoningError as error:
        raise CandidateSegmentationError(error.code, 'native conditional reasoning refused premises') from None


@dataclass(frozen=True, init=False)
class CandidateAbilityInterpreter:
    _query: object
    _controls: dict
    _review_root: Path
    _implementation: str
    _predecessor: str

    def assess(self, raw):
        request = _request(raw)
        _require(_implementation() == self._implementation == _IMPORTED_CODE
                 and v1._code_identity() == self._predecessor == v1._IMPORTED_CODE,
                 'packaged interpretation implementation changed', 'IMPLEMENTATION_MISMATCH')
        try:
            reasoner = load_rules_reasoner(review_root=self._review_root, expected_context_id=CONTEXT_ID)
            inspected = MechanicalCardIntelligence.inspect_mtgjson_candidate(self._query,
                **self._controls, card_id=request['card_id'], printing_id=request['printing_id'])
        except (MechanicalEvidenceError, SourcePolicyError, RulesReasoningError, c.PilotError, OSError):
            raise CandidateSegmentationError('EVIDENCE_REFUSED', 'owning verified evidence refused') from None
        rows = inspected['evidence']['occurrences']
        chosen = [r for r in rows if request['evidence_id'] is None or r['evidence_id'] == request['evidence_id']]
        if request['evidence_id'] is not None:
            _require(len(chosen) == 1, 'selected occurrence absent', 'OCCURRENCE_MISMATCH')
        evidence = dict(inspection_id=inspected['inspection_id'], query_snapshot_id=inspected['query_snapshot_id'],
            canonical_card_id=request['card_id'], canonical_printing_id=request['printing_id'],
            import_report_id=inspected['evidence']['report_id'],
            source_use_profile_id=inspected['evidence']['source_use_profile_id'],
            occurrence_ids=[r['evidence_id'] for r in rows], selected_occurrence=None)
        material = dict(status='EVIDENCE_UNRESOLVED', field=None, regions=[], segments=[], dependencies=None,
            diagnostics=['MISSING_OCCURRENCE'], coverage=dict(byte_accounting=dict(status='NOT_AVAILABLE'),
                total_ability_count=None, card_mechanical_completeness='NOT_ESTABLISHED'))
        if inspected['evidence']['status'] == 'WITHHELD':
            material.update(status='WITHHELD', diagnostics=sorted({'WITHHELD_EVIDENCE'} |
                {condition for row in rows for condition in row['conditions']}))
        elif len(chosen) > 1:
            material.update(status='AMBIGUOUS', diagnostics=['MULTIPLE_OCCURRENCES'])
        elif len(chosen) == 1:
            selected = chosen[0]; text = selected['text']
            if (selected['candidate_status'] != 'UNADMITTED_SOURCE_EVIDENCE' or selected['conditions']
                or text['status'] != 'SUPPLIED' or text['face_boundary'].get('kind') != 'WHOLE_CARD'):
                material['diagnostics'] = ['UNRESOLVED_OR_UNSUPPORTED_TEXT_OWNERSHIP']
            else:
                evidence['selected_occurrence'] = {k:selected[k] for k in ('evidence_id','card_id','printing_id',
                    'source_release','source_partition','source_partition_sha256','source_row',
                    'source_record_sha256','provenance_sha256','notice_sha256')}
                evidence['selected_occurrence']['text'] = {k:text[k] for k in (
                    'source_field','source_pointer','face_boundary','status')}
                material = _materialize(text['value'], evidence, self._implementation)
        _require(request['reasoning'] is None or bool(material['segments']),
                 'supported selected boundary required for reasoning', 'INCOMPLETE_SEGMENTATION')
        native = _reason(request['reasoning'], material, reasoner)
        body = dict(schema_version=VERSION, request=request, policy_version=POLICY,
            implementation_id=self._implementation, predecessor_implementation_id=self._predecessor,
            evidence=evidence, **material, native_conditional_reasoning=native,
            reasoning_basis='PENDING_SEGMENT_READING_AND_SCOPE_HYPOTHESES_ONLY' if native else None,
            unresolved_characteristics=[*v1._GAPS, 'cross_ability_effects', 'accepted_card_semantics'],
            authority=dict(v1._AUTHORITY), limitations=[
                'Byte accounting is not complete ability segmentation or Card understanding.',
                'Boundaries and written characteristics require independent semantic review.',
                'Opaque text cannot certify a later ability; surrounding effects remain unknown.',
                'Local subject IDs are not canonical, executable or cross-release ability identities.',
                'Hypothetical native conclusions establish neither legal activation nor actual output.'])
        try: return c.ReviewDocument._verified(c.seal(VERSION, body, 'report_id'), limit=REPORT_BYTES)
        except (c.PilotError, UnicodeError):
            raise CandidateSegmentationError('REPORT_BUDGET', 'bounded segmentation report required') from None

    def replay(self, raw, *, expected_report_id):
        try:
            value = c.parse_json(raw, limit=REPORT_BYTES)
            _require(type(expected_report_id) is str and value.get('report_id') == expected_report_id,
                     'independently pinned report required', 'REPORT_ID_MISMATCH')
            result = self.assess(value['request'])
            c.exact(value, result.to_dict(), limit=REPORT_BYTES)
            return result
        except CandidateSegmentationError: raise
        except (c.PilotError, KeyError, TypeError):
            raise CandidateSegmentationError('INVALID_REPORT', 'segmentation does not reproduce from evidence') from None

    def assess_many(self, requests):
        _require(type(requests) is list and 0 < len(requests) <= MAX_REQUESTS,
                 'one to sixteen explicit requests required', 'COVERAGE_BUDGET')
        try: normalized = [_request(r) for r in json.loads(c.owned(requests, limit=COVERAGE_BYTES))]
        except (c.PilotError, ValueError, TypeError, UnicodeError, RecursionError):
            raise CandidateSegmentationError('COVERAGE_BUDGET', 'bounded request population required') from None
        _require(len({c.canonical(r) for r in normalized}) == len(normalized), 'duplicate request refused')
        counts, reports, refusals = {}, [], []
        for index, request in enumerate(normalized):
            try:
                value = self.assess(request).to_dict(); status = value['status']
                reports.append(dict(request_index=index, report_id=value['report_id'],
                    status=status, coverage=value['coverage']))
            except CandidateSegmentationError as error:
                status = 'REFUSED'; refusals.append(dict(request_index=index, code=error.code))
            counts[status] = counts.get(status, 0) + 1
        body = dict(schema_version='candidate-ability-coverage-v1', requests=normalized,
            evaluated_requests=len(normalized), counts=counts, reports=reports, refusals=refusals,
            policy_version=POLICY, implementation_id=self._implementation,
            coverage_scope='ONLY_EXPLICIT_EVALUATED_REQUESTS_NOT_UNIQUE_CARDS_OR_ORACLE_CORPUS',
            authority=dict(v1._AUTHORITY))
        try:
            return c.ReviewDocument._verified(c.seal(body['schema_version'], body, 'report_id'), limit=COVERAGE_BYTES)
        except c.PilotError:
            raise CandidateSegmentationError('COVERAGE_BUDGET', 'bounded coverage report required') from None

    def replay_coverage(self, raw, *, expected_report_id):
        try:
            value = c.parse_json(raw, limit=COVERAGE_BYTES)
            _require(type(expected_report_id) is str and value.get('report_id') == expected_report_id,
                     'independently pinned coverage required', 'REPORT_ID_MISMATCH')
            result = self.assess_many(value['requests'])
            c.exact(value, result.to_dict(), limit=COVERAGE_BYTES)
            return result
        except CandidateSegmentationError: raise
        except (c.PilotError, KeyError, TypeError):
            raise CandidateSegmentationError('INVALID_REPORT', 'coverage does not reproduce') from None


def load_candidate_ability_interpreter(query, *, expected_query_snapshot_id, evidence_directory,
        profile, expected_report_id, review_root, expected_context_id=CONTEXT_ID):
    """Only trusted host code selects existing native evidence controls."""
    load_rules_reasoner(review_root=review_root, expected_context_id=expected_context_id)
    result = object.__new__(CandidateAbilityInterpreter)
    object.__setattr__(result, '_query', query)
    object.__setattr__(result, '_controls', dict(expected_query_snapshot_id=expected_query_snapshot_id,
        evidence_directory=Path(evidence_directory).absolute(), profile=profile, expected_report_id=expected_report_id))
    object.__setattr__(result, '_review_root', Path(review_root).absolute())
    object.__setattr__(result, '_implementation', _implementation())
    object.__setattr__(result, '_predecessor', v1._code_identity())
    _require(result._implementation == _IMPORTED_CODE and result._predecessor == v1._IMPORTED_CODE,
             'packaged implementation changed after import', 'IMPLEMENTATION_MISMATCH')
    return result
