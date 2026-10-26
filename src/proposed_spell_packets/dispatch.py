"""Explicit closed version dispatch for existing offline condition workflows.

Model/definition classes remain strict per version. No migration or fallback.
"""
import json

from . import conditions as c
from . import conditions_v2 as c2
from . import sensitivity as s
from . import alternatives as a
from . import validation as v
from .authoring import read_draft_bytes


def _read(path, field, byte_limit):
    raw = read_draft_bytes(path)
    if len(raw) > byte_limit:
        v.fail('VERSIONED_INPUT_BYTE_LIMIT')
    try:
        value = json.loads(raw, object_pairs_hook=v._unique, parse_constant=v._nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        v.fail('MALFORMED_VERSIONED_INPUT_JSON')
    if type(value) is not dict or type(value.get(field)) is not str:
        v.fail('EXPLICIT_VERSION_REQUIRED')
    return value


def read_model(path):
    value = _read(path, 'model_version', c2.MODEL_BYTE_LIMIT)
    version = value['model_version']
    if version == c.MODEL_VERSION:
        return c.ConditionModel(value)
    if version == c2.MODEL_VERSION:
        return c2.ConditionModel(value)
    v.fail('UNSUPPORTED_CONDITION_MODEL_VERSION')


def read_definition(path):
    from . import alternatives_v2 as a2
    value = _read(path, 'definition_version', a.DEFINITION_BYTE_LIMIT)
    version = value['definition_version']
    if version == a.DEFINITION_VERSION:
        return a.AlternativesDefinition(value)
    if version == a2.DEFINITION_VERSION:
        return a2.AlternativesDefinition(value)
    v.fail('UNSUPPORTED_ALTERNATIVE_DEFINITION_VERSION')


# Existing API entry points own explicit version routing; their v1 classes and
# validation paths continue to reject v2 payloads when used directly.
evaluate = c.evaluate
analyze_sensitivity = s.analyze
evaluate_alternatives = a.evaluate
render_condition = c.render
render_sensitivity = s.render
render_alternatives = a.render
