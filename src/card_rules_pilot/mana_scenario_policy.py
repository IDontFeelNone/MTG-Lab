"""Explicit hypothetical substitution over admitted descriptors; never game facts."""
import json
from . import contract as c

INPUT_VERSION = 'card-rules-hypothetical-mana-input-v1'
POLICY_VERSION = 'card-rules-hypothetical-mana-policy-v1'
RESULT_VERSION = 'card-rules-hypothetical-mana-calculation-v1'
INPUT_LIMIT = 4096
COUNT_LIMIT = 1000000
COLORS = ('W', 'U', 'B', 'R', 'G')
DIMENSIONS = ('controlled_swamp_count', 'commander_color_identity')
PATTERNS = {'swamp_count_dependent': 'controlled_swamp_count',
    'commander_color_context_dependent': 'commander_color_identity',
    'fixed_colorless': None, 'unrestricted_color_choice': None,
    'targeted_land_tapping_utility': None, 'damage_trigger_without_mana_output': None}

class UnsupportedScenario(c.PilotError):
    state = 'UNSUPPORTED'


def _assumptions(value):
    if type(value) is not list or len(value) > 4:
        raise UnsupportedScenario('UNSUPPORTED: at most four explicit assumption entries required')
    seen = set()
    for row in value:
        if type(row) is not dict or set(row) != {'dimension', 'value'}:
            raise UnsupportedScenario('UNSUPPORTED: closed assumption fields required')
        dimension, supplied = row['dimension'], row['value']
        if type(dimension) is not str or dimension not in DIMENSIONS:
            raise UnsupportedScenario('UNSUPPORTED: foreign hypothetical dimension')
        if dimension == DIMENSIONS[0]:
            if type(supplied) is not int or not 0 <= supplied <= COUNT_LIMIT:
                raise UnsupportedScenario('UNSUPPORTED: exact integer count in [0, 1000000] required')
        elif (type(supplied) is not list or any(type(x) is not str or x not in COLORS for x in supplied)
                or supplied != [color for color in COLORS if color in supplied]):
            raise UnsupportedScenario('UNSUPPORTED: unique colors in canonical W,U,B,R,G order required')
        key = c.canonical(row)
        if key in seen:
            raise UnsupportedScenario('UNSUPPORTED: duplicate assumption entry')
        seen.add(key)
    if any(sum(row['dimension'] == dim for row in value) > 2 for dim in DIMENSIONS):
        raise UnsupportedScenario('UNSUPPORTED: at most two premises per dimension')
    return value


def make_scenario(assumptions):
    value = json.loads(c.owned(assumptions, limit=INPUT_LIMIT))
    _assumptions(value)
    return c.ReviewDocument._verified(c.seal(INPUT_VERSION, {
        'schema_version': INPUT_VERSION, 'assumptions': value,
        'input_authority': 'EXPLICIT_HYPOTHETICAL_ASSUMPTIONS_NOT_OBSERVATIONS'}, 'scenario_id'), limit=INPUT_LIMIT)


def validate_scenario(value):
    value = json.loads(c.owned(value, limit=INPUT_LIMIT))
    if type(value) is not dict or set(value) != {'schema_version', 'assumptions', 'input_authority', 'scenario_id'}:
        raise UnsupportedScenario('UNSUPPORTED: complete closed scenario record required')
    expected = make_scenario(value['assumptions'])
    c.exact(value, expected.to_dict(), limit=INPUT_LIMIT)
    return expected


def parse_scenario(raw):
    return validate_scenario(c.parse_json(raw, limit=INPUT_LIMIT))


UNKNOWN_GAME_INPUTS = (
    'No actual activation, untapped resource, legal action, payment or mana production is established.',
    'Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated.',
    'No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated.',
    'Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.',
)
_POLICY_RAW = c.owned(c.seal(POLICY_VERSION, {
    'schema_version': POLICY_VERSION, 'input_version': INPUT_VERSION,
    'count_bound': COUNT_LIMIT, 'canonical_colors': list(COLORS),
    'pattern_dependencies': PATTERNS,
    'states': ['UNSPECIFIED', 'SUPPLIED', 'UNSUPPORTED', 'CONFLICTING'],
    'rules': [
        'Route only by accepted structured output pattern and dependency, never Card names, subjects, text parsing or provider annotations.',
        'A supplied count substitutes N into the accepted per-Swamp written output as quantity N of B; cost remains separate.',
        'A supplied commander identity supplies only its explicit members as conditional written color choices. Empty is an explicit empty set, not an actual usability finding.',
        'Missing remains unknown; fixed written output needs no new game-state inputs.',
        'Two different values of one dimension conflict; no conditional consequence is emitted for that dimension.',
        'Any unrelated dimension is unsupported. Comparison routing filters inputs to their matching admitted patterns only.',
        'Preserve costs, ownership and source limitations; hypothetical assumptions establish no observed facts, legal action, actual output or strategic advantage.',
    ], 'unknown_game_inputs': list(UNKNOWN_GAME_INPUTS),
    'canonical_admission': False, 'execution_authority': 'BLOCKED'}, 'policy_id'))
POLICY_ID = json.loads(_POLICY_RAW)['policy_id']


def policy_document(): return json.loads(_POLICY_RAW)


def compute(*, descriptor, scenario):
    descriptor = json.loads(c.owned(descriptor))
    if type(descriptor) is not dict or set(descriptor) != {
            'pattern', 'dependencies', 'written_instruction', 'written_cost', 'ownership', 'damage_clause'}:
        raise UnsupportedScenario('UNSUPPORTED: exact admitted descriptor fields required')
    pattern = descriptor['pattern']
    if type(pattern) is not str or pattern not in PATTERNS:
        raise UnsupportedScenario('UNSUPPORTED: unadmitted output pattern')
    if (type(descriptor['dependencies']) is not list
            or any(type(x) is not str for x in descriptor['dependencies'])
            or type(descriptor['written_instruction']) is not str
            or descriptor['written_cost'] is not None and type(descriptor['written_cost']) is not str
            or descriptor['ownership'] not in ('no_additional_effect', 'same_ability_additional_effect', 'separate_triggered_ability')
            or descriptor['damage_clause'] is not None and type(descriptor['damage_clause']) is not str):
        raise UnsupportedScenario('UNSUPPORTED: malformed admitted descriptor')
    dimension = PATTERNS[pattern]
    expected_deps = {
        'swamp_count_dependent': ['controlled_swamp_count', 'available_payment'],
        'commander_color_context_dependent': ['commander_color_identity'],
        'fixed_colorless': [], 'unrestricted_color_choice': [],
        'targeted_land_tapping_utility': ['legal_target_land', 'available_payment'],
        'damage_trigger_without_mana_output': ['actual_trigger_event', 'ordinary_trigger_procedure_603'],
    }
    c.exact(descriptor['dependencies'], expected_deps[pattern])
    scenario = validate_scenario(scenario).to_dict()
    assumptions = scenario['assumptions']
    if any(row['dimension'] != dimension for row in assumptions):
        raise UnsupportedScenario('UNSUPPORTED: context does not belong to this output dependency')
    state = 'CONFLICTING' if len(assumptions) == 2 else 'SUPPLIED' if assumptions else 'UNSPECIFIED'
    consequence = None
    if state != 'CONFLICTING':
        if pattern == 'swamp_count_dependent' and assumptions:
            consequence = {'kind': 'HYPOTHETICAL_WRITTEN_QUANTITY', 'quantity': assumptions[0]['value'], 'mana_symbol': 'B'}
        elif pattern == 'commander_color_context_dependent' and assumptions:
            consequence = {'kind': 'HYPOTHETICAL_WRITTEN_COLOR_CHOICES', 'quantity': 1, 'colors': assumptions[0]['value'],
                'empty_set_does_not_establish_actual_unusability': True}
        elif pattern == 'fixed_colorless':
            consequence = {'kind': 'FIXED_WRITTEN_OUTPUT', 'quantity': 1, 'mana_symbol': 'C'}
        elif pattern == 'unrestricted_color_choice':
            consequence = {'kind': 'WRITTEN_ANY_COLOR_CHOICE', 'quantity': 1, 'colors': list(COLORS)}
    missing = [dimension] if dimension and not assumptions else []
    return c.seal(RESULT_VERSION, {'schema_version': RESULT_VERSION,
        'policy_id': POLICY_ID, 'scenario_id': scenario['scenario_id'], 'state': state,
        'required_hypothetical_inputs': [dimension] if dimension else [],
        'missing_inputs': missing, 'supplied_assumptions': assumptions,
        'accepted_written_capability': descriptor['written_instruction'],
        'conditional_written_output': consequence,
        'written_cost': descriptor['written_cost'], 'ownership': descriptor['ownership'],
        'conditional_damage_clause_not_executed': descriptor['damage_clause'],
        'mode': 'EXPLAINABLE_ONLY' if pattern in ('targeted_land_tapping_utility', 'damage_trigger_without_mana_output') else 'WRITTEN_OUTPUT_ONLY',
        'conflict': 'Different premises for the same dependency; no value selected.' if state == 'CONFLICTING' else None,
        'unknown_game_inputs': list(UNKNOWN_GAME_INPUTS),
        'unsupported_conclusions': ['actual mana production', 'net usable mana', 'payment feasibility', 'legal action', 'strategic superiority'],
        'canonical_admission': False, 'execution_authority': 'BLOCKED'}, 'calculation_id')
