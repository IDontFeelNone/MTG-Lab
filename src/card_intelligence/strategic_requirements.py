"""Read-only strategic requirements over the actual public six-land overlay."""
from dataclasses import dataclass
import hashlib
import json

from card_rules_pilot import contract as c
from . import land_overlay as overlay_api, strategic_context as inputs
from . import strategic_requirements_policy as policy

VERSION = 'six-land-strategic-requirements-report-v1'
REPORT_LIMIT = 65536
READABLE_LIMIT = 32768


class RequirementsError(c.PilotError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(code + ': ' + message)


def _family(value):
    if type(value) is not str or value not in policy.family_registry():
        raise RequirementsError('UNSUPPORTED_QUESTION', 'only four exact registered question families are supported')
    return value


def _overlay_ref(family, scenario, document):
    raw = document.to_json().encode()
    return dict(kind='overlay-comparison',family=family,hypothetical=scenario,
        identity=document.to_dict()['report_id'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
        route='StrategicRequirementsConsumer.detailed(reference)')


@dataclass(frozen=True, init=False)
class StrategicRequirementsConsumer:
    _overlay: overlay_api.LandEvidenceOverlay

    @property
    def question_families(self): return tuple(policy.family_registry())

    def _source(self, family, scenario):
        doc = self._overlay.compare(_family(family), scenario)
        self._overlay.validate_report(doc.to_dict())
        value = doc.to_dict()
        if sorted(r['identity']['card_id'] for r in value['cards']) != sorted(policy.family_registry()[family]['cards']):
            raise RequirementsError('IDENTITY_CONFLICT', 'exact registered Card pair required')
        return doc

    def _report(self, kind, family=None, supplied=None, requirement_id=None):
        supplied = inputs.make_context().to_dict() if supplied is None else inputs.validate_context(supplied).to_dict()
        if kind == 'integrity':
            if family is not None or requirement_id is not None or supplied != inputs.make_context().to_dict():
                raise RequirementsError('UNSUPPORTED_INSPECTION', 'integrity inspection accepts no context or selector')
            check = self._overlay.check().to_dict()
            return c.ReviewDocument._verified(c.seal(VERSION,dict(schema_version=VERSION,kind=kind,
                policy_id=policy.POLICY_ID,input_contract_id=inputs.CONTRACT_ID,
                family=None,context=supplied,requirement_id=None,
                question_families=list(self.question_families),card_ids=list(self._overlay.card_ids),
                overlay_integrity_id=check['report_id'],authority=check['authority'],
                snapshot_scope='Checks the admitted snapshot. Another public load revalidates current source evidence.'), 'report_id'),limit=REPORT_LIMIT)
        _family(family)
        if kind not in ('requirements','missing','provenance','requirement'):
            raise RequirementsError('UNSUPPORTED_INSPECTION', 'closed report inspection required')
        if (kind == 'requirement' and type(requirement_id) is not str) or (kind != 'requirement' and requirement_id is not None):
            raise RequirementsError('UNSUPPORTED_REQUIREMENT', 'exact requirement identity required only for single-requirement inspection')
        doc = self._source(family, supplied['hypothetical'])
        source = doc.to_dict()
        cards, capabilities = [], []
        for row in source['cards']:
            identity = row['identity']
            cards.append(dict(evidence_key='card:'+identity['card_id'],identity={k:v for k,v in identity.items() if k!='joins'},
                joins=identity['joins'],mechanical_dossier_id=row['mechanical']['dossier_id'],
                mechanical_reference=row['mechanical']['detailed_reference']))
            for subject in row['subjects']:
                calc = subject['hypothetical']['calculation']
                sem = subject['accepted_semantics']
                explained = subject['explanation']
                capabilities.append(dict(evidence_key='subject:'+subject['subject_id'],
                    card_id=identity['card_id'],subject_id=subject['subject_id'],candidate_id=sem['candidate_id'],
                    classification=sem['classification'],proposed_kind=sem['proposed_kind'],
                    historical_status=sem['historical_status'],current_status=sem['current_status'],
                    written_capability=calc['accepted_written_capability'],written_cost=calc['written_cost'],
                    output_pattern=explained['dimensions']['output_pattern'],
                    dependencies=explained['dimensions']['dependencies'],procedure=explained['dimensions']['procedure'],
                    ownership={k:sem['ownership'][k] for k in ('state','damage_clause','other_subject_ids')},
                    hypothetical={k:calc[k] for k in ('state','conditional_written_output','calculation_id','scenario_id')},
                    remaining_unknowns=subject['hypothetical']['retained_unknowns'],
                    provenance=explained['provenance'],rule_refs=sem['rule_refs'],
                    explanation_reference=subject['explanation_reference'],scenario_reference=subject['scenario_reference']))
        rows = policy.compute(family=family,capabilities=capabilities,cards=cards,supplied=supplied)
        conflicts = [r['requirement_id'] for r in rows if r['status']['information']=='CONFLICTING']
        state = 'CONFLICTING' if conflicts else 'PARTIALLY_INFORMED' if (
            supplied['declarations'] or supplied['hypothetical']['assumptions'] or supplied['leads']) else 'ANSWERABLE_REQUIREMENTS_ONLY'
        selected = rows
        if kind == 'requirement':
            selected = [r for r in rows if r['requirement_id']==requirement_id]
            if not selected: raise RequirementsError('UNSUPPORTED_REQUIREMENT','foreign requirement identity for this question/context')
        if kind == 'missing': selected = [r for r in rows if r['status']['information'] in ('ABSENT','CONFLICTING')]
        if kind == 'provenance': selected = []
        categories = {name:[r for r in selected if r['category']==name] for name in (
            'universal-context','capability-context','procedure-and-ownership','strategic-validation','identity-and-permission')}
        value = dict(schema_version=VERSION,kind=kind,family=family,requirement_id=requirement_id,
            policy_id=policy.POLICY_ID,input_contract_id=inputs.CONTRACT_ID,
            question=policy.family_registry()[family]['question'],context=supplied,request_state=state,
            answerability=dict(requirements_query='ANSWERABLE',strategic_evaluation='UNSUPPORTED',
                strategic_validation='UNIMPLEMENTED_OR_UNAUTHORIZED'),
            cards=cards,capabilities=capabilities,requirements=categories,
            missing_context_inputs=[dict(requirement_id=r['requirement_id'],template_id=r['template_id']) for r in rows
                if r['category'] in ('universal-context','capability-context','procedure-and-ownership')
                and r['status']['information']=='ABSENT'],conflicting_requirements=conflicts,
            unresolved_validation=[r['requirement_id'] for r in rows if r['status']['validation']=='UNIMPLEMENTED_OR_UNAUTHORIZED'],
            provenance=dict(decision_id=source['decision_id'],accepted_collection_id=source['accepted_collection_id'],
                overlay_policy_id=source['policy_id'],design_package_id=source['design_package_id'],
                catalog_binding=source['catalog_binding'],historical_scope=source['decision_scope']),
            overlay_reference=_overlay_ref(family,supplied['hypothetical'],doc),
            full_evidence_reference=source['full_evidence_reference'],authority=source['authority'],
            unsupported_conclusions=['strategic advantage or Card strength','power scores or rankings','deck or acquisition recommendations',
                'format legality from a label','observed game state from hypothetical inputs','actual or net mana, break-even or payment feasibility',
                'deck consistency','target legality, trigger events, damage or complete triggered procedure','production eligibility or source/use permissions'],
            limitations=source['limitations']+[
                'Declared context and opaque evidence leads are unverified; no source is fetched or reference authenticated.',
                'All input fields being present does not establish strategic validation. Independent stronger evaluation remains unresolved.',
                'Accepted historical semantics are not current Oracle verification or canonical executable CardGameplaySemantics.'])
        return c.ReviewDocument._verified(c.seal(VERSION,value,'report_id'),limit=REPORT_LIMIT)

    def requirements(self, family, context=None): return self._report('requirements',family,context)
    def missing(self, family, context=None): return self._report('missing',family,context)
    def provenance(self, family, context=None): return self._report('provenance',family,context)
    def requirement(self, family, requirement_id, context=None): return self._report('requirement',family,context,requirement_id)
    def check(self): return self._report('integrity')

    def for_cards(self, namespace, card_ids, family, context=None):
        _family(family)
        if type(namespace) is not str or namespace != inputs.NAMESPACE:
            raise RequirementsError('UNSUPPORTED_NAMESPACE','explicit legacy Card namespace required')
        if type(card_ids) is not list or any(type(v) is not str for v in card_ids) or card_ids != sorted(policy.family_registry()[family]['cards']):
            raise RequirementsError('UNSUPPORTED_CARD_SCOPE','exact registered Card pair in canonical ID order required')
        return self.requirements(family,context)

    def validate_report(self, value):
        try:
            value = json.loads(c.owned(value,limit=REPORT_LIMIT))
            if type(value) is not dict or 'context' not in value:
                raise RequirementsError('INVALID_REPORT','complete requirements report required')
            expected = self._report(value.get('kind'),value.get('family'),value['context'],value.get('requirement_id'))
            c.exact(value,expected.to_dict(),limit=REPORT_LIMIT)
            return expected
        except (ValueError, KeyError, TypeError) as error:
            raise RequirementsError('REPORT_INTEGRITY_REJECTED',str(error)) from None

    def parse_report(self, raw):
        try: return self.validate_report(c.parse_json(raw,limit=REPORT_LIMIT))
        except (ValueError, KeyError, TypeError) as error:
            raise RequirementsError('REPORT_INTEGRITY_REJECTED',str(error)) from None

    def detailed(self, reference):
        try:
            reference = json.loads(c.owned(reference,limit=8192))
            if type(reference) is not dict: raise ValueError('exact detailed reference required')
            if reference.get('kind') != 'overlay-comparison': return self._overlay.detailed(reference)
            if set(reference) != {'kind','family','hypothetical','identity','bytes','sha256','route'}:
                raise ValueError('complete overlay reference required')
            doc = self._source(reference['family'],reference['hypothetical'])
            c.exact(reference,_overlay_ref(reference['family'],reference['hypothetical'],doc),limit=8192)
            return doc
        except (ValueError, KeyError, TypeError) as error:
            raise RequirementsError('REFERENCE_INTEGRITY_REJECTED',str(error)) from None


def load_strategic_requirements(**overlay_arguments):
    """Actual fresh public overlay admission once; no imported report route."""
    try:
        overlay = overlay_api.load_land_overlay(**overlay_arguments)
        if overlay.card_ids != inputs.CARD_IDS:
            raise RequirementsError('UNSUPPORTED_COHORT','exact six admitted Card identities required')
        result = object.__new__(StrategicRequirementsConsumer)
        object.__setattr__(result,'_overlay',overlay)
        # Reproduce each public report before exposing the privately held batch.
        for family in policy.family_registry(): result.requirements(family)
        result.check()
        return result
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise RequirementsError('EVIDENCE_ADMISSION_REJECTED',str(error)) from None


def render_requirements(document):
    value = document.to_dict()
    lines = ['MTG Lab — strategic context requirements',
        'Report: '+value['report_id'],'Policy: '+value['policy_id'],'Input contract: '+value['input_contract_id']]
    if value['kind']=='integrity':
        lines += [value['snapshot_scope'],'Families: '+', '.join(value['question_families'])]
    else:
        lines += [value['family']+': '+value['question'],'Request: '+value['request_state'],
            'Answerability: '+json.dumps(value['answerability'],sort_keys=True),
            'Declarations (unverified): '+json.dumps(value['context']['declarations'],sort_keys=True),
            'Hypothetical assumptions: '+json.dumps(value['context']['hypothetical']['assumptions'],sort_keys=True),
            'Opaque unverified evidence leads: '+json.dumps(value['context']['leads'],sort_keys=True)]
        for card in value['cards']:
            identity=card['identity']
            lines += ['',identity['display_name']+' — '+identity['namespace']+':'+identity['card_id'],
                'Dossier: '+card['mechanical_dossier_id'],
                'Printing: '+identity['printing']['namespace']+':'+identity['printing']['printing_id'],
                'Observation: '+identity['observation']['namespace']+':'+identity['observation']['provider_record_id'],
                'Joins: '+'; '.join(k+'='+v['status'] for k,v in card['joins'].items())]
        for cap in value['capabilities']:
            lines += ['',cap['evidence_key']+': '+cap['written_capability'],
                'Written cost: '+str(cap['written_cost'])+'; procedure: '+cap['procedure'],
                'Ownership: '+cap['ownership']['state']+'; conditional damage: '+str(cap['ownership']['damage_clause']),
                'Hypothetical '+cap['hypothetical']['state']+': '+json.dumps(cap['hypothetical']['conditional_written_output'],sort_keys=True),
                'Candidate: '+cap['candidate_id'],'Rules: '+', '.join(cap['rule_refs']),
                'Remaining unknowns: '+' '.join(cap['remaining_unknowns'])]
        for category,rows in value['requirements'].items():
            if rows: lines += ['',category]
            for row in rows:
                lines += [row['template_id']+' — '+row['status']['information']+' / '+row['status']['satisfaction']+' / '+row['status']['validation'],
                    'Need: '+row['information_needed'],'Why: '+row['rationale'],
                    'Support: '+', '.join(row['support_refs'])+'; context: '+', '.join(row['context_paths']),
                    'Future: '+row['future_consumer']+'; '+row['validation_method'],
                    'Requirement: '+row['requirement_id']]
        lines += ['','Decision: '+value['provenance']['decision_id'],
            'Accepted collection: '+value['provenance']['accepted_collection_id'],value['provenance']['historical_scope'],
            'Overlay details: '+json.dumps(value['overlay_reference'],sort_keys=True),
            'Historical evidence: '+json.dumps(value['full_evidence_reference'],sort_keys=True),
            'Unsupported: '+'; '.join(value['unsupported_conclusions']),*value['limitations']]
    lines += ['Authority: '+json.dumps(value['authority'],sort_keys=True),'']
    text='\n'.join(lines)
    if len(text.encode())>READABLE_LIMIT: raise RequirementsError('READABLE_SIZE','readable requirements bound exceeded')
    return text
