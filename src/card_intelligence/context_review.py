"""Read-only human-review preparation over the owning strategic requirements API."""
from dataclasses import dataclass
import hashlib
import json

from card_rules_pilot import contract as c
from . import context_review_input as inputs
from . import strategic_requirements as requirements_api
from . import strategic_requirements_policy as requirements_policy

POLICY_VERSION = 'coffers-wastes-context-review-policy-v1'
REPORT_VERSION = 'coffers-wastes-context-review-report-v1'
REPORT_LIMIT, READABLE_LIMIT = 65536, 32768


class ContextReviewError(c.PilotError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(code + ': ' + message)


_POLICY = c.seal(POLICY_VERSION, dict(schema_version=POLICY_VERSION,schema_id=inputs.SCHEMA_ID,
    requirements_policy_id=requirements_policy.POLICY_ID,
    mappings={
        'deck-composition': ['swamp-composition'],
        'objective-and-mana': ['deck-objective','resources-and-timing'],
        'format-legality-lead': ['format-label','format-legality'],
        'performance-lead': ['strategic-performance']},
    relevance={
        'deck-composition': 'Declared hypothetical deck quantities could inform composition review; they establish no subtype or battlefield count.',
        'objective-and-mana': 'Declared goals and resource needs frame future contextual review; they establish no available payment or achieved objective.',
        'format-legality-lead': 'The claimed dated format/source could inform independent legality review; it establishes no legality.',
        'performance-lead': 'A claimed test or comparison lead could inform independent methodological review; it establishes no performance or advantage.'},
    states=['SUBMITTED_UNVERIFIED','REQUIRES_REVIEW','CONFLICTING','INSUFFICIENT_SOURCE','OUT_OF_SCOPE'],
    rules=['Each candidate also requires the existing evidence-authentication requirement.',
        'Use exact existing requirement IDs from actual public admission, never fabricate IDs.',
        'All original requirement statuses remain unchanged, regardless of supplied records.',
        'Conflicts compare explicitly defined quantities only within identical claimed deck/version scope.',
        'Retain every assertion; never prefer a source, average quantities or convert deck counts to controlled Swamps.',
        'Any review state describes triage only; no authenticated reviewer event or approval exists.',
        'Packet integrity validates supplied bytes, not truth, legality, source authentication or permissions.',
        'Validate reports against both owning admitted evidence and the complete separately supplied packet.'],
    canonical_admission=False,execution_authority='BLOCKED'), 'policy_id')
_POLICY_RAW = c.owned(_POLICY,limit=8192)
POLICY_ID = _POLICY['policy_id']
del _POLICY


def policy_document(): return c.ReviewDocument._verified(json.loads(_POLICY_RAW),limit=8192)


def _reference(doc):
    raw=doc.to_json().encode()
    return dict(kind='strategic-requirements',family=inputs.FAMILY,report_id=doc.to_dict()['report_id'],
        bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),route='BoundContextReview.detailed(reference)')


def _conflicts(candidates):
    findings=[]
    for index, left in enumerate(candidates):
        if left['category']!='deck-composition': continue
        for right in candidates[index+1:]:
            if right['category']!='deck-composition' or left['scope']!=right['scope']: continue
            for field in ('total_lands','claimed_swamps'):
                a,b=left['payload'][field],right['payload'][field]
                if a is not None and b is not None and a!=b:
                    findings.append(dict(code='CONFLICTING_DECLARED_QUANTITY',field=field,
                        candidate_ids=[left['candidate_id'],right['candidate_id']],values=[a,b],
                        scope=left['scope'],resolution='UNRESOLVED_NO_PREFERRED_SOURCE'))
    return findings


def _candidate_review(candidate, requirements, conflicts):
    policy=json.loads(_POLICY_RAW)
    by_template={r['template_id']:r for r in requirements}
    eligible=[by_template[k] for k in policy['mappings'][candidate['category']]+['evidence-authentication']]
    requested=candidate['requirement_refs']
    chosen=eligible if not requested else [r for r in eligible if r['requirement_id'] in requested]
    invalid=[ref for ref in requested if ref not in {r['requirement_id'] for r in eligible}]
    # Authentication review is mandatory even when the submitter selects a subset.
    auth=by_template['evidence-authentication']
    if auth not in chosen: chosen.append(auth)
    findings=[]
    source=candidate['source'];body=candidate['content'];payload=candidate['payload']
    def issue(code, field, message): findings.append(dict(code=code,field=field,message=message))
    if candidate['category']=='deck-composition':
        total,swamps=payload['total_lands'],payload['claimed_swamps']
        if total is not None and swamps is not None and swamps>total:
            issue('INTERNALLY_INCONSISTENT_COUNTS','payload','Claimed Swamp subset exceeds the declared total; quarantine this assertion without correcting it.')
        if total is None or swamps is None: issue('MISSING_COMPOSITION_QUANTITY','payload','Incomplete declared composition; absent is not zero.')
    if source['claimed_origin'] is None: issue('MISSING_CLAIMED_ORIGIN','source.claimed_origin','No claimed source identity was supplied.')
    if (body['mode']=='reference-only' or candidate['category'] in ('format-legality-lead','performance-lead')) and source['reference'] is None:
        issue('MISSING_SOURCE_REFERENCE','source.reference','No reviewable reference was supplied; no source will be fetched.')
    if candidate['category']=='format-legality-lead' and source['source_date'] is None and source['observation_date'] is None:
        issue('MISSING_DECLARED_DATE','source','The claimed format source has no supplied date; currency and legality remain unverified.')
    if candidate['category']=='performance-lead':
        for key in ('method','sample_scope','limitations'):
            if payload[key] is None: issue('MISSING_PERFORMANCE_METADATA','payload.'+key,'Independent review needs the claimed '+key+'; no result is validated here.')
    if body['mode']=='reference-only': issue('CONTENT_ABSENT','content','Only a lead/digest is supplied; no referenced bytes were inspected.')
    if invalid: issue('OUT_OF_SCOPE_REQUIREMENT_REFERENCE','requirement_refs','These references are foreign or irrelevant to this category: '+', '.join(invalid))
    states=['SUBMITTED_UNVERIFIED','REQUIRES_REVIEW']
    if any(candidate['candidate_id'] in f['candidate_ids'] for f in conflicts) or any(f['code']=='INTERNALLY_INCONSISTENT_COUNTS' for f in findings):
        states.append('CONFLICTING')
    if any(f['code'] not in ('INTERNALLY_INCONSISTENT_COUNTS','OUT_OF_SCOPE_REQUIREMENT_REFERENCE') for f in findings): states.append('INSUFFICIENT_SOURCE')
    if invalid: states.append('OUT_OF_SCOPE')
    maps=[]
    for row in chosen:
        maps.append(dict(requirement_id=row['requirement_id'],template_id=row['template_id'],
            support_refs=row['support_refs'],relevance=policy['relevance'][candidate['category']],
            supplied_material=body['mode'],original_status=row['status'],
            review_status='REQUIRES_REVIEW',requirement_promoted=False,
            remaining_unresolved=row['information_needed'],future_consumer=row['future_consumer'],
            independent_review_required=row['validation_method']))
    return dict(candidate=candidate,review_states=states,
        disposition='QUARANTINED' if 'CONFLICTING' in states or 'OUT_OF_SCOPE' in states else 'REVIEW_ONLY',
        findings=findings,mappings=maps,authenticated_review_event=None)


@dataclass(frozen=True, init=False)
class BoundContextReview:
    """A privately owned submission binding; no evidence-status mutation API."""
    _owner: object
    _packet_raw: bytes

    def packet(self): return inputs.validate_packet(json.loads(self._packet_raw))

    def _report(self,kind='review',candidate_id=None):
        if type(kind) is not str or kind not in ('review','candidates','provenance','conflicts','missing','candidate','integrity'):
            raise ContextReviewError('UNSUPPORTED_INSPECTION','closed review inspection required')
        if (kind=='candidate' and type(candidate_id) is not str) or (kind!='candidate' and candidate_id is not None):
            raise ContextReviewError('UNSUPPORTED_CANDIDATE','exact candidate selector required only for candidate inspection')
        packet=self.packet().to_dict();source=json.loads(self._owner._requirements_raw)
        rows=[r for group in source['requirements'].values() for r in group]
        conflicts=_conflicts(packet['candidates'])
        reviewed=[_candidate_review(v,rows,conflicts) for v in packet['candidates']]
        if kind=='candidate':
            reviewed=[v for v in reviewed if v['candidate']['candidate_id']==candidate_id]
            if not reviewed: raise ContextReviewError('UNSUPPORTED_CANDIDATE','foreign candidate identity')
        if kind in ('conflicts','integrity'): reviewed=[]
        scope_states=sorted({s for v in packet['candidates'] for s in _candidate_review(v,rows,conflicts)['review_states']})
        prerequisites=[dict(requirement_id=r['requirement_id'],template_id=r['template_id'],category=r['category'],
            needed=r['information_needed'],original_status=r['status'],support_refs=r['support_refs'],
            future_consumer=r['future_consumer'],validation_method=r['validation_method']) for r in rows]
        value=dict(schema_version=REPORT_VERSION,kind=kind,candidate_id=candidate_id,policy_id=POLICY_ID,
            schema_id=inputs.SCHEMA_ID,packet_id=packet['packet_id'],family=inputs.FAMILY,
            namespace=packet['namespace'],card_ids=packet['card_ids'],subject_ids=packet['subject_ids'],
            submission_authority=inputs.AUTHORITY,submission_candidate_ids=[v['candidate_id'] for v in packet['candidates']],
            review_states=scope_states or ['REQUIRES_REVIEW'],candidates=reviewed,conflicts=conflicts,
            requirements=prerequisites,cards=source['cards'],capabilities=source['capabilities'],
            provenance=source['provenance'],requirements_reference=self._owner._reference(),
            full_evidence_reference=source['full_evidence_reference'],authority=source['authority'],
            review_boundary=dict(authenticated_reviewer=None,review_event=None,approval=None,
                source_authentication='NOT_ESTABLISHED',permissions='NOT_ESTABLISHED',
                strategic_validation='UNIMPLEMENTED_OR_UNAUTHORIZED',evidence_promotion='UNIMPLEMENTED',
                requirement_status_changes=[],canonical_admission=False,execution_authority='BLOCKED'),
            limitations=[
                'All candidates are owner-submitted claims, never independently verified observations or facts.',
                'Content digests bind supplied bytes only; absent content is a lead, not inspected evidence.',
                'Deck counts are hypothetical composition declarations, not controlled Swamps or observed battlefield state.',
                'Claimed scope equality identifies possible contradictions only; it authenticates no deck identity.',
                'All original requirement statuses remain unchanged. No field count or candidate supplies strategic proof.',
                'No legal action, actual/net mana, payment, break-even, deck consistency, format legality or strategic advantage is calculated.',
                'Review states are triage findings; no authenticated human-review decision or approval is issued.',
                'Permission claims do not grant source-policy clearance or production eligibility.',
                'Accepted historical retained text is not current verified Oracle or executable CardGameplaySemantics.',
                'Integrity checks concern this admitted snapshot; another public load revalidates current evidence.'])
        return c.ReviewDocument._verified(c.seal(REPORT_VERSION,value,'report_id'),limit=REPORT_LIMIT)

    def report(self): return self._report()
    def candidates(self): return self._report('candidates')
    def candidate(self,candidate_id): return self._report('candidate',candidate_id)
    def provenance(self): return self._report('provenance')
    def conflicts(self): return self._report('conflicts')
    def missing(self): return self._report('missing')
    def check(self): return self._report('integrity')

    def validate_report(self,value):
        try:
            value=json.loads(c.owned(value,limit=REPORT_LIMIT))
            if type(value) is not dict: raise ValueError('complete report required')
            expected=self._report(value.get('kind'),value.get('candidate_id'))
            c.exact(value,expected.to_dict(),limit=REPORT_LIMIT)
            return expected
        except (ValueError,KeyError,TypeError) as error:
            raise ContextReviewError('REPORT_INTEGRITY_REJECTED',str(error)) from None

    def parse_report(self,raw): return self.validate_report(c.parse_json(raw,limit=REPORT_LIMIT))

    def detailed(self,reference): return self._owner.detailed(reference)


@dataclass(frozen=True, init=False)
class ContextEvidenceReview:
    _requirements: requirements_api.StrategicRequirementsConsumer
    _requirements_raw: bytes

    def _reference(self):
        return _reference(c.ReviewDocument._verified(json.loads(self._requirements_raw),limit=requirements_api.REPORT_LIMIT))

    def submit(self,packet):
        """Privately bind one complete submission; no approval or source promotion."""
        owned=inputs.validate_packet(packet)
        result=object.__new__(BoundContextReview)
        object.__setattr__(result,'_owner',self)
        object.__setattr__(result,'_packet_raw',owned.to_json().encode())
        return result

    def review(self,packet): return self.submit(packet).report()
    def validate_report(self,value,packet): return self.submit(packet).validate_report(value)

    def detailed(self,reference):
        try:
            reference=json.loads(c.owned(reference,limit=8192))
            if type(reference) is not dict: raise ValueError('exact detailed reference required')
            if reference.get('kind')!='strategic-requirements': return self._requirements.detailed(reference)
            c.exact(reference,self._reference(),limit=8192)
            expected=self._requirements.for_cards(inputs.strategic.NAMESPACE,list(inputs.CARD_IDS),inputs.FAMILY)
            self._requirements.validate_report(expected.to_dict())
            if expected.to_json().encode()!=self._requirements_raw: raise ValueError('requirements snapshot mismatch')
            return expected
        except (ValueError,KeyError,TypeError) as error:
            raise ContextReviewError('REFERENCE_INTEGRITY_REJECTED',str(error)) from None


def load_context_evidence_review(**requirements_arguments):
    """Fresh actual public evidence admission; exactly one shared owning batch."""
    try:
        owner=requirements_api.load_strategic_requirements(**requirements_arguments)
        source=owner.for_cards(inputs.strategic.NAMESPACE,list(inputs.CARD_IDS),inputs.FAMILY)
        source=owner.validate_report(source.to_dict())
        value=source.to_dict()
        if (sorted(v['subject_id'] for v in value['capabilities'])!=list(inputs.SUBJECT_IDS)
                or value['policy_id']!=requirements_policy.POLICY_ID): raise ValueError('exact supported subjects and requirements policy required')
        result=object.__new__(ContextEvidenceReview)
        object.__setattr__(result,'_requirements',owner)
        object.__setattr__(result,'_requirements_raw',source.to_json().encode())
        result.review(inputs.make_packet().to_dict())
        return result
    except (ValueError,OSError,KeyError,TypeError) as error:
        raise ContextReviewError('EVIDENCE_ADMISSION_REJECTED',str(error)) from None


def render_review(document):
    value=document.to_dict()
    lines=['MTG Lab — Coffers / Wastes context-evidence review',
        'Report: '+value['report_id'],'Packet: '+value['packet_id'],
        'Policy: '+value['policy_id'],'Schema: '+value['schema_id'],
        'States: '+', '.join(value['review_states']),'Submitted claims only; independent review remains required.']
    for card in value['cards']:
        lines += [card['identity']['display_name']+' — '+card['identity']['card_id'],
            'Joins: '+'; '.join(k+'='+v['status'] for k,v in card['joins'].items())]
    for cap in value['capabilities']:
        lines += [cap['subject_id']+': '+cap['written_capability'],'Written cost: '+str(cap['written_cost']),
            'Hypothetical calculation: '+cap['hypothetical']['state']+'; no supplied deck count is substituted.']
    for item in value['candidates']:
        candidate=item['candidate'];body=candidate['content']
        lines += ['',candidate['candidate_id']+' — '+candidate['category'],
            'Triage: '+', '.join(item['review_states'])+' / '+item['disposition'],
            'Claim: '+candidate['assertion'],'Declared payload: '+json.dumps(candidate['payload'],sort_keys=True),
            'Claimed source: '+json.dumps(candidate['source'],sort_keys=True),
            'Claimed hypothetical deck scope: '+json.dumps(candidate['scope'],sort_keys=True),
            'Content: '+body['mode']+'; supplied UTF-8 bytes='+str(len((body['text'] or '').encode()))+'; digest='+str(body['digest']),
            'Claimed use restrictions (unverified): '+str(candidate['claimed_use_restrictions']),
            'Supplied provenance notes: '+json.dumps(candidate['notes'])]
        for finding in item['findings']: lines += [finding['code']+': '+finding['message']]
        for mapping in item['mappings']:
            lines += ['May inform '+mapping['template_id']+' — '+mapping['requirement_id'],
                mapping['relevance'],'Still unresolved: '+mapping['remaining_unresolved'],
                'Independent review: '+mapping['independent_review_required']]
    for finding in value['conflicts']: lines += ['',finding['code']+' '+finding['field']+': '+json.dumps(finding,sort_keys=True)]
    lines += ['','Original requirements (unchanged):']
    for row in value['requirements']:
        lines += [row['template_id']+' — '+row['original_status']['information']+' / '+row['original_status']['satisfaction']+' / '+row['original_status']['validation'],
            row['needed'],'Future: '+row['future_consumer'],'Requirement: '+row['requirement_id']]
    lines += ['','Requirements detail: '+json.dumps(value['requirements_reference'],sort_keys=True),
        'Decision: '+value['provenance']['decision_id'],
        'Review boundary: '+json.dumps(value['review_boundary'],sort_keys=True),*value['limitations'],
        'Authority: '+json.dumps(value['authority'],sort_keys=True),'']
    text='\n'.join(lines)
    if len(text.encode())>READABLE_LIMIT: raise ContextReviewError('READABLE_SIZE','bounded readable output exceeded')
    return text
