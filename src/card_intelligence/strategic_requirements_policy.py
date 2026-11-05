"""Deterministic gap templates over admitted structured capability premises.

compute is a policy calculation, not an evidence-admission or strategy API.
Names and subject labels only identify provenance; they never choose templates.
"""
import json
from card_rules_pilot import contract as c
from . import strategic_context as context

VERSION = 'six-land-strategic-requirements-policy-v1'
REQUIREMENT_VERSION = 'six-land-strategic-requirement-v1'
TOWER, WASTES, CITADEL, COFFERS, CITY, PORT = context.CARD_IDS
_FAMILIES = {
    'mana-and-utility': dict(cards=[WASTES,PORT], question='What evidence is needed to evaluate additional independently owned utility in a declared deck or format?'),
    'variable-output': dict(cards=[WASTES,COFFERS], question='What evidence is needed to evaluate count-dependent written mana potential relative to fixed written output?'),
    'color-context': dict(cards=[TOWER,CITY], question='What evidence is needed to evaluate restricted and unrestricted written color choice in a declared context?'),
    'damage-ownership': dict(cards=[CITADEL,CITY], question='What evidence is needed to evaluate separately triggered and same-ability additional damage relationships?'),
}
MANA_PATTERNS = ('fixed_colorless','unrestricted_color_choice','swamp_count_dependent','commander_color_context_dependent')

# category, information needed, why it matters, future consumer, validation method
_TEMPLATES = {
 'format-label': ('universal-context','Declare the format and intended comparison scope.','The question needs a declared scope; a label proves no format rule or legality.','declared-context-capture','Record intent only; independently establish legality and date later.'),
 'deck-objective': ('universal-context','Declare the investigation objective for the deck plan.','Relevance depends on the objective; an objective label is not a role classification or proof of impact.','declared-context-capture','Record intent without inferring a real deck or archetype.'),
 'deck-colors': ('universal-context','Declare deck color requirements, keeping quantities and timing separate.','Color needs frame the question but do not demonstrate actual payment requirements or a legal deck.','future-deck-evidence-review','Independently admit exact deck requirements and their scope; no deck parsing here.'),
 'alternatives': ('universal-context','Declare supported exact-ID alternatives and comparison scope.','An explicit alternative set frames opportunity questions; even an empty set establishes no exhaustive search or viability.','future-comparison-context-review','Review alternatives against the declared objective and independently admitted context.'),
 'accepted-capability': ('capability-context','Retain the exact source-bound capability, costs, restrictions and ownership.','Accepted historical semantics support a written capability, not strategic strength or actual availability.','existing-read-only-overlay','Reproduce the owning admitted explanation and scenario; retain historical scope.'),
 'resources-and-timing': ('capability-context','Establish relevant mana quantities, timing, available resources and activation prerequisites.','Written cost and potential output do not establish payment, untapped availability, actual mana or spell affordability.','future-governed-gameplay-validator','Require separately reviewed rule closure and authorized state evidence before any legal-action evaluation.'),
 'hypothetical-swamps': ('capability-context','Supply an explicit hypothetical controlled Swamp count for text substitution.','A supplied count resolves only the written quantity under that assumption; missing is not zero.','existing-hypothetical-text-calculator','Use the existing bounded count contract; do not calculate net mana or payment.'),
 'swamp-composition': ('capability-context','Establish deck land composition, independently supported subtypes and hypothetical versus observed count provenance.','One assumed count proves neither deck composition, actual controlled Swamps, consistency nor a count distribution.','future-deck-and-observation-evidence-review','Independently admit composition and dated observations; do not count lands or infer subtypes here.'),
 'hypothetical-commander-colors': ('capability-context','Supply an explicit hypothetical commander color identity for written color-choice filtering.','A missing identity is not an empty identity; explicit empty choices imply no actual usability conclusion.','existing-hypothetical-text-calculator','Use the original canonical WUBRG subset contract, separate from declared deck colors.'),
 'commander-evidence': ('capability-context','Establish whether commander context is relevant and independently support the commander and its color identity.','A supplied palette, format label or Card color annotation identifies no actual commander or legal palette.','future-format-and-identity-evidence-review','Review exact identity, format/date and authority; no commander inference here.'),
 'target-relevance': ('capability-context','Establish relevant targets, target availability and interaction relevance.','A written targeted utility does not establish a legal or strategically relevant target.','future-target-and-context-review','Require scoped rule and state evidence plus independently validated objective relevance.'),
 'alternative-use-cost': ('capability-context','Evaluate timing, resource use and opportunity cost of choosing one independently owned ability over another.','Separate abilities and written costs identify a question about foregone use, not a demonstrated tempo loss or strategic advantage.','future-resource-and-strategic-review','Review declared alternatives and resource context; do not compute actual payments or net benefit.'),
 'effect-ownership': ('procedure-and-ownership','Retain separately owned versus same-ability effect relationships.','Costs, mana and damage cannot be borrowed between different subjects.','existing-read-only-overlay','Inspect accepted ownership and original additional-effect composition, without executing effects.'),
 'trigger-procedure': ('procedure-and-ownership','Obtain missing general triggered-event, placement, ordering and procedure evidence.','Accepted triggered classification does not close the unresolved ordinary-trigger frontier or establish an event.','future-reviewed-rule-and-procedure-consumer','Require separately authorized rule/dependency review and execution readiness; no new projection here.'),
 'effect-context': ('procedure-and-ownership','Establish relevant life, prevention, resource and event context before assessing actual consequences.','Written damage and its ownership do not establish life-total impact, prevention, timing or actual damage.','future-effect-context-and-consequence-review','Validate scoped consequences only after rule, state and execution authority gates; no damage execution here.'),
 'format-legality': ('strategic-validation','Independently establish format/date legality and relevant restrictions.','A user-supplied format or evidence reference is not authenticated legality evidence.','future-permissioned-format-evidence-review','Admit authoritative dated evidence separately; no lookup or new format rules here.'),
 'strategic-performance': ('strategic-validation','Provide an appropriate independent analytical or performance validation method, alternatives, counterevidence and review.','Complete input fields and supported capabilities cannot establish strength, recommendation, consistency or strategic advantage.','future-independent-strategic-validation','Predeclare objective, model, assumptions, representativeness, uncertainty and counterexamples; gameplay simulation additionally requires execution readiness.'),
 'evidence-authentication': ('strategic-validation','Authenticate contextual evidence leads and their identity, source, scope and permissions.','Opaque reference strings are leads only; their presence proves nothing about the referenced content.','future-context-evidence-admission','Independently validate source authority and content; do not dereference, read or authenticate leads here.'),
 'source-currency': ('identity-and-permission','Independently establish appropriate current text and authoritative rule/version evidence before stronger evaluation.','Accepted historical retained text is not current verified Oracle or complete current rule evidence.','future-authorized-source-and-version-review','Require separate source authority, permissions and bounded review; no acquisition or projection here.'),
 'current-identity': ('identity-and-permission','Establish any missing current identifier edges needed by a stronger consumer.','Verified historical correspondence does not promote a current identifier edge.','future-authorized-identity-admission','Preserve each exact established or missing join; no identity promotion here.'),
 'production-permission': ('identity-and-permission','Establish operator-production identity and each independently governed source/use permission before production use.','Legacy evidence and software tests establish no production eligibility or license.','future-authorized-production-and-permission-review','Separate owner approval, identity admission and source-policy clearance; all remain unresolved here.'),
 'pilot-boundary': ('identity-and-permission','Disclose the existing functional-role and contextual-comparison cohort boundary.','These subjects have no membership in those pilots; declared objectives or role labels cannot create it.','read-only-boundary-inspection','Retain NOT_IN_SUPPORTED_COHORT; a new role classification is outside this milestone.'),
}

_POLICY = c.seal(VERSION, dict(schema_version=VERSION, input_contract_id=context.CONTRACT_ID,
    families=_FAMILIES, templates={k:list(v) for k,v in _TEMPLATES.items()},
    information_states=['ABSENT','HYPOTHETICAL_SUPPLIED','DECLARED_UNVERIFIED','ADMITTED_EXISTING_EVIDENCE','CONFLICTING'],
    validation_states=['EXISTING_EVIDENCE_ONLY','HYPOTHETICAL_TEXT_ONLY','UNIMPLEMENTED_OR_UNAUTHORIZED'],
    rules=['Select templates by explicit structured output descriptors, ownership, procedure and declared question; never Card names or text searches.',
        'Keep information authority, bounded satisfaction and independent validation as separate dimensions.',
        'Record declared values and opaque leads without authenticating them or reading their contents.',
        'Even complete supplied fields never establish strategic validation, production authority or legal gameplay.',
        'Conflicts remain local to their dimensions and propagate to request status without choosing a preferred premise.'],
    canonical_admission=False, execution_authority='BLOCKED'), 'policy_id')
_POLICY_RAW = c.owned(_POLICY,limit=65536)
_FAMILY_RAW = c.owned(_FAMILIES)
POLICY_ID = json.loads(_POLICY_RAW)['policy_id']
del _POLICY, _FAMILIES, _TEMPLATES


def policy_document():
    return c.ReviewDocument._verified(json.loads(_POLICY_RAW), limit=65536)


def family_registry():
    return json.loads(_FAMILY_RAW)


def compute(*, family, capabilities, cards, supplied):
    """Pure requirement construction over explicit premises, not source admission."""
    if type(family) is not str or family not in family_registry(): raise context.ContextError('unsupported question family')
    supplied = context.validate_context(supplied).to_dict()
    rows = []
    templates = json.loads(_POLICY_RAW)['templates']
    declared = supplied['declarations']

    def add(template, supports, *, dimension=None, existing=False, hypothetical=None,
            lead_category=None, known_missing=False, boundary=False):
        category, needed, why, consumer, method = templates[template]
        paths = []
        if existing:
            info, satisfaction, validation = 'ADMITTED_EXISTING_EVIDENCE', 'SATISFIED_WITHIN_RETAINED_SCOPE', 'EXISTING_EVIDENCE_ONLY'
        elif hypothetical is not None:
            state = hypothetical['state']
            info = {'SUPPLIED':'HYPOTHETICAL_SUPPLIED','UNSPECIFIED':'ABSENT','CONFLICTING':'CONFLICTING'}[state]
            satisfaction = 'SATISFIED_FOR_HYPOTHETICAL_TEXT_ONLY' if state == 'SUPPLIED' else 'UNRESOLVED'
            validation = 'HYPOTHETICAL_TEXT_ONLY'
            paths = ['#/context/hypothetical']
        else:
            indices = [i for i,v in enumerate(declared) if v['dimension'] == dimension] if dimension else []
            leads = [i for i,v in enumerate(supplied['leads']) if lead_category in ('any',v['category'])]
            info = 'CONFLICTING' if len(indices) == 2 else 'DECLARED_UNVERIFIED' if indices or leads else 'ABSENT'
            satisfaction = 'DECLARATION_RECORDED_ONLY' if indices and len(indices)==1 else 'UNRESOLVED'
            validation = 'UNIMPLEMENTED_OR_UNAUTHORIZED'
            paths = ['#/context/declarations/'+str(i) for i in indices] + ['#/context/leads/'+str(i) for i in leads]
        if boundary:
            satisfaction = 'BOUNDARY_DISCLOSED_ONLY'
        if known_missing:
            satisfaction, validation = 'UNRESOLVED', 'UNIMPLEMENTED_OR_UNAUTHORIZED'
        row = dict(schema_version=REQUIREMENT_VERSION, template_id=template, category=category,
            information_needed=needed, rationale=why, created_by='DECLARED_QUESTION' if supports==['question'] else 'ADMITTED_STRUCTURED_PREMISES',
            support_refs=supports, context_paths=paths,
            status=dict(information=info,satisfaction=satisfaction,validation=validation),
            future_consumer=consumer, validation_method=method)
        rows.append(c.seal(REQUIREMENT_VERSION,row,'requirement_id'))

    for template,dim in (('format-label','format_label'),('deck-objective','deck_objective'),
                         ('deck-colors','deck_color_requirements'),('alternatives','alternatives')):
        add(template,['question'],dimension=dim)
    for cap in capabilities:
        add('accepted-capability',[cap['evidence_key']],existing=True)
    mana = [v for v in capabilities if v['output_pattern'] in MANA_PATTERNS]
    if mana: add('resources-and-timing',[v['evidence_key'] for v in mana],lead_category='deck-context',known_missing=True)
    for cap in capabilities:
        support = [cap['evidence_key']]
        if cap['output_pattern'] == 'swamp_count_dependent':
            add('hypothetical-swamps',support,hypothetical=cap['hypothetical'])
            add('swamp-composition',support,lead_category='deck-context',known_missing=True)
        if cap['output_pattern'] == 'commander_color_context_dependent':
            add('hypothetical-commander-colors',support,hypothetical=cap['hypothetical'])
            add('commander-evidence',support,lead_category='format-legality',known_missing=True)
        if cap['output_pattern'] == 'targeted_land_tapping_utility':
            add('target-relevance',support,lead_category='deck-context',known_missing=True)
            siblings = [v['evidence_key'] for v in mana if v['card_id']==cap['card_id']]
            if siblings: add('alternative-use-cost',support+siblings,lead_category='deck-context',known_missing=True)
        if cap['ownership']['damage_clause'] is not None:
            add('effect-ownership',support,existing=True)
        if cap['procedure'] == 'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER':
            add('trigger-procedure',support,lead_category='rule-procedure',known_missing=True)
    effects = [v['evidence_key'] for v in capabilities if v['ownership']['damage_clause'] is not None]
    if effects: add('effect-context',effects,lead_category='deck-context',known_missing=True)
    add('format-legality',['question'],lead_category='format-legality',known_missing=True)
    add('strategic-performance',['question'],lead_category='strategic-performance',known_missing=True)
    add('evidence-authentication',['question'],lead_category='any',known_missing=True)
    joins = [v['evidence_key'] for v in cards]
    current_established = all(v['joins']['current_identifier_edge']['status']=='ESTABLISHED' for v in cards)
    add('current-identity',joins,existing=current_established,known_missing=not current_established)
    add('source-currency',joins,known_missing=True)
    add('production-permission',joins,known_missing=True)
    add('pilot-boundary',joins,existing=True,boundary=True)
    return rows
