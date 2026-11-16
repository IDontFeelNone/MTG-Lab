"""Non-executing semantic closure over public, admitted historical land evidence."""
from dataclasses import dataclass
import hashlib
import json

from card_rules_pilot import contract as c, land_decision as decision
from . import land_overlay as overlay_api, semantic_closure_policy as policy

VERSION = 'real-card-semantic-closure-report-v1'
INPUT_VERSION = 'real-card-semantic-closure-input-v1'
REPORT_LIMIT = 65536
READABLE_LIMIT = 32768
CARD_ID = '46a07b53-ff58-4bd6-80dd-ded2eb0e29a3'
SUBJECT_ID = 'snow-wastes-mana'
CANDIDATE_ID = dict(decision.CANDIDATE_IDS)[SUBJECT_ID]
CONTEXT_ID = 'sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478'
ClosureError = policy.ClosureError


def _reference(document):
    raw = document.to_json().encode('utf-8')
    return dict(kind='closure-overlay-card', identity=document.to_dict()['report_id'],
                bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                route='SemanticClosureConsumer.detailed(reference)')


def _premises(source, history):
    """Finite adapter; structured accepted descriptors, never text parsing.

    Names select nothing. This adapter does not author a new Card interpretation.
    It uses current exact authority boundaries, not guessed procedure conclusions.
    """
    row = source['cards'][0]; subject = row['subjects'][0]
    sem = subject['accepted_semantics']; explanation = subject['explanation']
    rules = history['context']['retained_rules']
    if (source['decision_id'] != decision.DECISION_ID or source['accepted_collection_id'] != decision.COLLECTION_ID
            or sem['candidate_id'] != CANDIDATE_ID or sem['current_status'] != 'ACCEPTED_BOUNDED_RETAINED_TEXT'
            or row['identity']['card_id'] != CARD_ID or subject['subject_id'] != SUBJECT_ID
            or rules['context_id'] != CONTEXT_ID):
        raise ClosureError('EVIDENCE_BINDING', 'exact accepted subject, decision and context required')
    dims = explanation['dimensions']
    if (dims['procedure'] != 'CONDITIONAL_ACTIVATED_MANA' or dims['output_pattern'] != 'fixed_colorless'
            or dims['ownership'] != 'no_additional_effect' or dims['dependencies']):
        raise ClosureError('UNSUPPORTED_BEHAVIOR', 'only the admitted fixed-output activated-mana reading is supported')
    if (source['authority']['execution_authority'] != 'BLOCKED' or source['authority']['canonical_admission'] is not False
            or rules['semantic_closure'] != 'OPEN' or rules['execution_authority'] != 'BLOCKED'):
        raise ClosureError('AUTHORITY_CONFLICT', 'no real execution or closure promotion is admitted')
    # These exact public references are admitted by the owning overlay. Evidence
    # levels describe their scope, not stronger independent verification.
    evidence = {}
    def ref(key, identity, pointer, scope):
        evidence[key] = dict(identity=identity, pointer=pointer, scope=scope)
    ref('identity', source['report_id'], '/cards/0/identity', 'Validated historical joins; current identifier edge is independent of Oracle freshness.')
    ref('text', source['report_id'], '/cards/0/subjects/0/explanation/provenance/subject_binding', 'Exact historical retained field; not fresh Oracle verification.')
    ref('accepted', source['report_id'], '/cards/0/subjects/0/accepted_semantics', 'Owner acceptance through the exact decision identity in this admitted overlay; historical scope only.')
    ref('calculation', history['report_id'], '/assessments/0/behavior', 'Original conditional behavior calculation; no action or actual mana.')
    ref('authority', source['report_id'], '/authority', 'Existing non-production, open semantic closure, blocked execution and unresolved permissions.')
    ref('rule-context', history['report_id'], '/context/retained_rules', 'Only the selected 24 rules enter semantics; enclosing packages do not expand that scope.')
    by_ref = {r['rule']['rule_reference']:r for r in rules['rules']}
    supporting = []
    for reference in sem['rule_refs']:
        if reference not in by_ref:
            raise ClosureError('MISSING_RULE_EVIDENCE', 'accepted calculation cites a rule outside the admitted context')
        r = by_ref[reference]; rule = r['rule']; key = 'rule:'+reference
        pointer = '/context/retained_rules/rules/'+str(rules['rules'].index(r))+'/rule'
        ref(key, history['report_id'], pointer, 'Retained projected source support; exact rule identity is in selected_support, not execution approval.')
        supporting.append(dict(reference=reference, rule_id=rule['rule_id'], package_id=r['package_id'],
            projection_id=r['projection_id'], source_anchor={k:rule['source_anchor'][k] for k in (
                'artifact_hash','span_sha256','byte_start','byte_end')},
            standalone_anchor_id=rule['source_anchor'].get('anchor_id'),
            review_state=rule.get('review_state', 'SEE_BOUND_REVIEW_RECORDS'),
            executable_review='NOT_ESTABLISHED',evidence_ref=key))
    review_refs = []
    for i, review in enumerate(rules['current_dependency_reviews']):
        key = 'review:'+str(i); review_refs.append(key)
        ref(key, history['report_id'], '/context/retained_rules/current_dependency_reviews/'+str(i),
            'Append-only bounded dependency/source review; not execution approval.')
    if not review_refs:
        raise ClosureError('MISSING_RULE_REVIEW', 'admitted bounded review records required')
    facts = []
    def fact(key, state, level, refs):
        facts.append(dict(key=key,state=state,level=level,evidence_refs=sorted(refs)))
    joins = row['identity']['joins']
    fact('identity.historical', 'ESTABLISHED' if joins['historical_correspondence']['status']=='ESTABLISHED' else 'UNKNOWN', 'validated_binding', ['identity'])
    fact('identity.identifier', 'ESTABLISHED' if joins['current_identifier_edge']['status']=='ESTABLISHED' else 'ABSENT', 'validated_binding', ['identity'])
    fact('identity.operator', 'ABSENT', 'validated_binding', ['identity'])
    fact('text.historical','ESTABLISHED','retained_source',['text'])
    fact('text.accepted','ESTABLISHED','accepted_interpretation',['accepted','text'])
    fact('text.current','UNKNOWN','reviewed_source',['identity','text'])
    fact('rules.retained','ESTABLISHED','retained_source',['rule-context', *('rule:'+r for r in sem['rule_refs'])])
    fact('rules.reviewed','ESTABLISHED','reviewed_source',review_refs)
    fact('rules.execution_review','ABSENT','reviewed_real_procedure',['authority','rule-context'])
    fact('rules.dependencies','UNKNOWN','reviewed_real_procedure',['authority','rule-context'])
    fact('semantics.conditional','ESTABLISHED','accepted_interpretation',['accepted','calculation'])
    fact('semantics.executable','ABSENT','reviewed_real_procedure',['authority','accepted'])
    for row_def in policy.requirements():
        if row_def['dimension']=='procedure':
            fact(row_def['key'], 'UNSUPPORTED' if row_def['key']=='procedure.external' else 'ABSENT',
                 'reviewed_real_procedure',['authority','rule-context'])
    fact('permissions.use','UNKNOWN','permission',['authority'])
    fact('authorization.closure','PROHIBITED','execution_authorization',['authority','rule-context'])
    fact('authorization.profile','PROHIBITED','execution_authorization',['authority'])
    return facts, evidence, sorted(supporting,key=lambda r:r['reference'])


@dataclass(frozen=True, init=False)
class SemanticClosureConsumer:
    _overlay: overlay_api.LandEvidenceOverlay
    _source: bytes
    _history: bytes

    def assess(self, namespace, card_id, subject_id):
        if (type(namespace) is not str or namespace != overlay_api.CARD_NAMESPACE
                or type(card_id) is not str or card_id != CARD_ID
                or type(subject_id) is not str or subject_id != SUBJECT_ID):
            raise ClosureError('UNSUPPORTED_SUBJECT', 'exact pilot Card namespace, UUID and accepted subject required')
        source, history = json.loads(self._source), json.loads(self._history)
        facts, evidence, supporting = _premises(source, history)
        result = policy.evaluate(policy.requirements(), facts, evidence)
        row = source['cards'][0]; sub = row['subjects'][0]; rules = history['context']['retained_rules']
        observed = row['identity']['observation']['acquisition']
        input_doc = c.seal(INPUT_VERSION,dict(schema_version=INPUT_VERSION,namespace=namespace,card_id=card_id,
            subject_id=subject_id,candidate_id=CANDIDATE_ID,decision_id=source['decision_id'],
            collection_id=source['accepted_collection_id'],overlay_report_id=source['report_id'],
            historical_report_id=history['report_id'],context_id=rules['context_id'],
            policy_id=policy.POLICY_ID,graph_id=result['graph_id']), 'input_id')
        findings = result['requirements']
        value = dict(schema_version=VERSION,input=input_doc,policy_id=policy.POLICY_ID,
            scope='NON_EXECUTING_SELECTED_HISTORICAL_ABILITY_ONLY',
            identity=row['identity'],mechanical_dossier_id=row['mechanical']['dossier_id'],
            text=dict(binding=sub['explanation']['provenance']['subject_binding'],
                source_binding=sub['explanation']['provenance']['source_binding'],
                observation_timestamp=observed['source_timestamp'],retrieved_at=observed['retrieved_at'],
                oracle_freshness='UNKNOWN_NOT_CURRENTLY_VERIFIED',staleness='NOT_ASSESSED_NO_AMBIENT_CLOCK_INFERENCE'),
            accepted_semantics=sub['accepted_semantics'],
            conditional_capability=dict(dimensions=sub['explanation']['dimensions'],
                written_instruction=sub['hypothetical']['calculation']['accepted_written_capability'],
                behavior_calculation_id=sub['explanation']['provenance']['behavior_calculation_id'],
                explanation_id=sub['explanation_reference']['identity'],
                scenario_calculation_id=sub['hypothetical']['calculation']['calculation_id']),
            rules=dict(context_id=rules['context_id'],selected_support=supporting,
                dependency_reviews=[dict(package=r['package'],record=r['record'],review_id=r['review_id']) for r in rules['current_dependency_reviews']],
                unresolved_frontiers=[dict(**r,status='UNKNOWN',retained_support='MISSING_IN_SELECTED_CONTEXT',
                    applicability='UNKNOWN_FOR_SELECTED_ACTION',scope='RETAINED_LITERAL_REFERENCE_NOT_CLOSED_FOR_EXECUTION')
                    for r in rules['unresolved_frontiers'] if r['origin'] in ('602.2','602.2a')],
                scope_limit='24-rule admitted consumer context; 104/16 describes retained global coverage, not full semantic closure.'),
            requirements=findings,status_meanings=dict(policy.MEANINGS),status_precedence=list(policy.PRECEDENCE),
            established=[r['requirement_id'] for r in findings if r['status']=='SATISFIED'],
            missing=[r['requirement_id'] for r in findings if r['status']=='MISSING'],
            unknown=[r['requirement_id'] for r in findings if r['status']=='UNKNOWN'],
            unsupported=[r['requirement_id'] for r in findings if r['status']=='UNSUPPORTED'],
            blocked=[r['requirement_id'] for r in findings if r['status']=='BLOCKED'],
            evidence=evidence,disposition='BLOCKED_NON_EXECUTING_ASSESSMENT',
            evidence_admissibility='ADMITTED_EXISTING_NON_PRODUCTION_REVIEW_SCOPE_NOT_A_USE_LICENSE',
            authority=source['authority'],real_execution_profile_id=None,
            detailed_references=dict(overlay=_reference(c.ReviewDocument._verified(source,limit=REPORT_LIMIT)),
                historical=source['full_evidence_reference'],explanation=sub['explanation_reference'],
                scenario=sub['scenario_reference'],mechanical=row['mechanical']['detailed_reference']),
            limitations=[
                'SATISFIED is requirement-specific; no completeness percentage, readiness flag or execution permission follows.',
                'Historical acceptance is not current Oracle verification, production identity or source-use clearance.',
                'Fictional priority, cost, mana, stack and checkpoint execution supplies no real-procedure proof.',
                'The non-targeted mana exception does not eliminate control, timing, payment, output, checkpoint or recovery dependencies.',
                'Literal frontiers come only from admitted records; missing procedure categories are requirements, not invented CR citations.',
                'Basic/Snow labels establish no intrinsic ability, land-play or snow-payment semantics.',
                'No game state, legal activation, actual mana, strategic value or real-card execution is calculated.'])
        return c.ReviewDocument._verified(c.seal(VERSION,value,'report_id'),limit=REPORT_LIMIT)

    def check(self):
        """Check this admitted snapshot; another public load revalidates current roots."""
        return self.assess(overlay_api.CARD_NAMESPACE,CARD_ID,SUBJECT_ID)

    def validate_report(self, value):
        expected=self.check()
        c.exact(value,expected.to_dict(),limit=REPORT_LIMIT)
        return expected

    def parse_report(self, raw):
        return self.validate_report(c.parse_json(raw,limit=REPORT_LIMIT))

    def detailed(self, reference):
        source = c.ReviewDocument._verified(json.loads(self._source),limit=REPORT_LIMIT)
        if type(reference) is dict and reference.get('kind')=='closure-overlay-card':
            c.exact(reference,_reference(source),limit=8192)
            return source
        allowed = self.check().to_dict()['detailed_references']
        if not any(reference==v for k,v in allowed.items() if k!='overlay'):
            raise ClosureError('UNSUPPORTED_REFERENCE','exact admitted detailed reference required')
        return self._overlay.detailed(reference)


def load_semantic_closure(*, catalog_root, mechanical_root, review_root, cohort_root,
        decision_root, expected_profile_id, expected_query_snapshot_id,
        expected_plan_id, expected_decision_id):
    """One current public overlay admission; no copied report is an input."""
    try:
        overlay = overlay_api.load_land_overlay(catalog_root=catalog_root,mechanical_root=mechanical_root,
            review_root=review_root,cohort_root=cohort_root,decision_root=decision_root,
            expected_profile_id=expected_profile_id,expected_query_snapshot_id=expected_query_snapshot_id,
            expected_plan_id=expected_plan_id,expected_decision_id=expected_decision_id)
        source = overlay.card(overlay_api.CARD_NAMESPACE,CARD_ID).to_dict()
        history = overlay.detailed(source['full_evidence_reference']).to_dict()
        _premises(source,history)
        result = object.__new__(SemanticClosureConsumer)
        object.__setattr__(result,'_overlay',overlay)
        object.__setattr__(result,'_source',c.owned(source,limit=REPORT_LIMIT))
        object.__setattr__(result,'_history',c.owned(history))
        result.check()
        return result
    except (ValueError,OSError,KeyError,TypeError) as error:
        raise ClosureError('EVIDENCE_ADMISSION_REJECTED',str(error)) from None


def render_closure(document):
    v = document.to_dict() if hasattr(document,'to_dict') else document
    lines = [v['identity']['display_name']+' — non-executing semantic closure',
        v['identity']['namespace']+':'+v['identity']['card_id']+' / '+v['input']['subject_id'],
        'Disposition: '+v['disposition'],
        'Historical text: '+v['text']['binding']['selected_passage'],
        'Observation: '+v['text']['observation_timestamp']+'; retrieved '+v['text']['retrieved_at'],
        'Current Oracle: '+v['text']['oracle_freshness'],
        'Accepted candidate: '+v['input']['candidate_id'], 'Owner decision: '+v['input']['decision_id'],
        'Conditional procedure: '+v['conditional_capability']['dimensions']['procedure'], '']
    for r in v['requirements']:
        lines += [r['key']+' ['+r['status']+']: '+r['question'],
            '  Why: '+r['why'], '  Needed: '+r['needed'],
            '  Evidence: '+(', '.join(r['evidence_refs']) or 'none')+'; requirement '+r['requirement_id']]
    lines += ['', 'Retained supporting rules: '+', '.join(r['reference'] for r in v['rules']['selected_support']),
        'Exact rule, review, source and calculation identities: inspect canonical evidence/requirements.',
        'Semantic closure OPEN; execution BLOCKED; source clearance not_granted; permissions NOT_ESTABLISHED.',
        *v['limitations'], 'Integrity-checked detail: SemanticClosureConsumer.detailed(detailed_references[...]).',
        'Policy: '+v['policy_id'],'Report: '+v['report_id']]
    text = '\n'.join(lines)+'\n'
    if len(text.encode())>READABLE_LIMIT: raise ClosureError('OUTPUT_BOUND','readable output exceeds bound')
    return text


def main(argv=None):
    import argparse
    import sys
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Read-only historical real-Card closure assessment; no execution')
    for name in ('catalog-root','mechanical-root','review-root','cohort-root','decision-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-profile-id','expected-query-snapshot-id','expected-plan-id','expected-decision-id'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--json',action='store_true')
    commands=parser.add_subparsers(dest='command',required=True)
    assess=commands.add_parser('assess')
    for name in ('namespace','card-id','subject-id'): assess.add_argument('--'+name,required=True)
    commands.add_parser('check')
    commands.add_parser('validate').add_argument('file',type=Path)
    commands.add_parser('detail').add_argument('file',type=Path)
    args=parser.parse_args(argv)
    try:
        consumer=load_semantic_closure(**{k:getattr(args,k) for k in (
            'catalog_root','mechanical_root','review_root','cohort_root','decision_root',
            'expected_profile_id','expected_query_snapshot_id','expected_plan_id','expected_decision_id')})
        if args.command=='assess': doc=consumer.assess(args.namespace,args.card_id,args.subject_id)
        elif args.command=='validate': doc=consumer.validate_report(c.read_json(args.file,limit=REPORT_LIMIT))
        elif args.command=='detail': doc=consumer.detailed(c.read_json(args.file,limit=8192))
        else: doc=consumer.check()
        sys.stdout.write(doc.to_json() if args.json or args.command=='detail' else render_closure(doc))
        return 0  # Successful assessment, never a readiness/approval result.
    except (ValueError,OSError) as error:
        sys.stderr.write(json.dumps(dict(code=getattr(error,'code','EVIDENCE_REJECTED'),message=str(error)),sort_keys=True)+'\n')
        return 2


if __name__=='__main__':
    raise SystemExit(main())
