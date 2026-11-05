"""Bounded declared inputs, never observations, legality or strategic evidence."""
import json
from card_rules_pilot import contract as c, mana_scenario_policy as hp

VERSION = 'six-land-strategic-context-input-v1'
CONTRACT_VERSION = 'six-land-strategic-context-input-contract-v1'
LIMIT = 8192
NAMESPACE = 'magic:legacy-promoted:card'
CARD_IDS = (
    '0895c9b7-ae7d-4bb3-af17-3b75deb50a25', '46a07b53-ff58-4bd6-80dd-ded2eb0e29a3',
    '66ae2562-68e9-4c77-ba0a-57f8ff37f656', '7358e164-5704-4e78-9b21-6a9bf2a968ce',
    'f25351e3-539b-4bbc-b92d-6480acf4d722', 'f3e8dc56-2810-474e-a6a7-9c3555f94ae9')
OBJECTIVES = ('mana-flexibility', 'resource-output', 'interaction-utility', 'effect-tradeoffs')
DIMENSIONS = ('format_label', 'deck_objective', 'deck_color_requirements', 'alternatives')
LEAD_CATEGORIES = ('deck-context', 'format-legality', 'rule-procedure', 'strategic-performance')
AUTHORITY = 'DECLARED_ASSUMPTIONS_AND_LEADS_NOT_OBSERVATIONS_OR_AUTHENTICATED_EVIDENCE'


class ContextError(c.PilotError):
    code = 'UNSUPPORTED_CONTEXT'


_CONTRACT = c.seal(CONTRACT_VERSION, dict(schema_version=CONTRACT_VERSION,
    input_version=VERSION, dimensions=list(DIMENSIONS), objectives=list(OBJECTIVES),
    card_namespace=NAMESPACE, card_ids=list(CARD_IDS), colors=list(hp.COLORS),
    hypothetical_input_version=hp.INPUT_VERSION, hypothetical_count_limit=hp.COUNT_LIMIT,
    lead_categories=list(LEAD_CATEGORIES), max_declarations=8, max_values_per_dimension=2,
    max_leads=4, label_chars=80, reference_chars=160, byte_limit=LIMIT,
    authority=AUTHORITY, rules=[
        'Declarations retain their supplied order and authority; two different values of one dimension conflict.',
        'Duplicate declarations reject; colors and alternatives must be unique and canonically ordered.',
        'Format is only a bounded opaque label, never a format registry or legality assertion.',
        'Objectives express investigation intent, never a classified archetype or approved functional role.',
        'Alternatives name supported exact identities only; they neither extend the question nor establish viability.',
        'Evidence leads are not dereferenced, read, authenticated or promoted to evidence.',
        'Hypothetical counts and colors retain their original input contract and are never observed game facts.'],
    canonical_admission=False, execution_authority='BLOCKED'), 'contract_id')
_CONTRACT_RAW = c.owned(_CONTRACT,limit=LIMIT)
CONTRACT_ID = json.loads(_CONTRACT_RAW)['contract_id']
del _CONTRACT


def contract_document():
    return c.ReviewDocument._verified(json.loads(_CONTRACT_RAW), limit=LIMIT)


def _colors(value):
    if (type(value) is not list or any(type(v) is not str or v not in hp.COLORS for v in value)
            or value != [color for color in hp.COLORS if color in value]):
        raise ContextError('unique canonical W,U,B,R,G subset required')


def _value(dimension, value):
    if dimension == 'format_label':
        if type(value) is not str or not 1 <= len(value) <= 80 or not value.isprintable() or value.strip() != value:
            raise ContextError('bounded printable nonempty format label required; no verification assertion')
    elif dimension == 'deck_objective':
        if type(value) is not str or value not in OBJECTIVES:
            raise ContextError('closed investigation objective required; no role or archetype classification')
    elif dimension == 'deck_color_requirements':
        _colors(value)
    elif dimension == 'alternatives':
        if type(value) is not list or len(value) > 6:
            raise ContextError('at most six exact supported alternatives required')
        for row in value:
            if (type(row) is not dict or set(row) != {'namespace','card_id'}
                    or type(row['namespace']) is not str or row['namespace'] != NAMESPACE
                    or type(row['card_id']) is not str or row['card_id'] not in CARD_IDS):
                raise ContextError('unsupported alternative Card identity or namespace')
        ids = [row['card_id'] for row in value]
        if ids != sorted(set(ids)): raise ContextError('unique alternatives in exact Card ID order required')
    else:
        raise ContextError('foreign context dimension')


def make_context(declarations=None, *, hypothetical=None, leads=None):
    declarations = [] if declarations is None else json.loads(c.owned(declarations, limit=LIMIT))
    leads = [] if leads is None else json.loads(c.owned(leads, limit=LIMIT))
    if type(declarations) is not list or len(declarations) > 8:
        raise ContextError('bounded declaration list required')
    seen = set()
    for row in declarations:
        if (type(row) is not dict or set(row) != {'dimension','value'}
                or type(row['dimension']) is not str or row['dimension'] not in DIMENSIONS):
            raise ContextError('closed declaration fields and dimension required')
        _value(row['dimension'], row['value'])
        key = c.canonical(row)
        if key in seen: raise ContextError('duplicate declaration')
        seen.add(key)
    if any(sum(row['dimension'] == dim for row in declarations) > 2 for dim in DIMENSIONS):
        raise ContextError('at most two distinct values per dimension')
    if type(leads) is not list or len(leads) > 4:
        raise ContextError('at most four opaque evidence leads required')
    seen = set()
    for lead in leads:
        if (type(lead) is not dict or set(lead) != {'category','reference'}
                or type(lead['category']) is not str or lead['category'] not in LEAD_CATEGORIES
                or type(lead['reference']) is not str or not 1 <= len(lead['reference']) <= 160
                or not lead['reference'].isprintable() or lead['reference'].strip() != lead['reference']):
            raise ContextError('closed category and bounded opaque reference required')
        key = c.canonical(lead)
        if key in seen: raise ContextError('duplicate evidence lead')
        seen.add(key)
    scenario = hp.make_scenario([]) if hypothetical is None else hp.validate_scenario(hypothetical)
    return c.ReviewDocument._verified(c.seal(VERSION, dict(schema_version=VERSION,
        declarations=declarations, hypothetical=scenario.to_dict(), leads=leads,
        authority=AUTHORITY), 'context_id'), limit=LIMIT)


def validate_context(value):
    value = json.loads(c.owned(value, limit=LIMIT))
    fields = {'schema_version','declarations','hypothetical','leads','authority','context_id'}
    if type(value) is not dict or set(value) != fields:
        raise ContextError('complete versioned closed context record required')
    expected = make_context(value['declarations'], hypothetical=value['hypothetical'], leads=value['leads'])
    c.exact(value, expected.to_dict(), limit=LIMIT)
    return expected


def parse_context(raw):
    return validate_context(c.parse_json(raw, limit=LIMIT))
