"""Strict owner-submitted hypothetical context; integrity never authenticates claims."""
import datetime
import hashlib
import json
import re

from card_rules_pilot import contract as c
from . import strategic_context as strategic

CANDIDATE_VERSION = 'coffers-wastes-context-evidence-candidate-v1'
PACKET_VERSION = 'coffers-wastes-context-evidence-packet-v1'
SCHEMA_VERSION = 'coffers-wastes-context-evidence-schema-v1'
FAMILY = 'variable-output'
CARD_IDS = ('46a07b53-ff58-4bd6-80dd-ded2eb0e29a3', '7358e164-5704-4e78-9b21-6a9bf2a968ce')
SUBJECT_IDS = ('coffers-mana', 'snow-wastes-mana')
CATEGORIES = ('deck-composition', 'objective-and-mana', 'format-legality-lead', 'performance-lead')
SOURCE_TYPES = ('owner-declaration', 'owner-supplied-excerpt', 'reference-lead')
MODES = ('declaration-only', 'reference-only', 'supplied-utf8')
CANDIDATE_LIMIT, PACKET_LIMIT = 8192, 32768
COUNT_LIMIT, MAX_CANDIDATES, CONTENT_LIMIT, TOTAL_CONTENT_LIMIT = 1000, 4, 1024, 4096
AUTHORITY = 'SUBMITTED_UNVERIFIED_NON_PRODUCTION_REVIEW_MATERIAL'


class ReviewInputError(c.PilotError):
    code = 'INVALID_SUPPLIED_EVIDENCE'


def _fields(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ReviewInputError('exact closed fields required: ' + ', '.join(fields))


def _text(value, limit, *, nullable=False):
    if value is None and nullable: return
    if (type(value) is not str or not 1 <= len(value) <= limit or not value.isprintable()
            or value.strip() != value):
        raise ReviewInputError('bounded printable nonempty text required')


def _digest(value, *, nullable=False):
    if value is None and nullable: return
    if type(value) is not str or re.fullmatch(r'sha256:[0-9a-f]{64}', value) is None:
        raise ReviewInputError('exact SHA-256 identity required')


def _date(value):
    if value is None: return
    if type(value) is not str or re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value) is None:
        raise ReviewInputError('explicit ISO calendar date or null required')
    try: datetime.date.fromisoformat(value)
    except ValueError: raise ReviewInputError('invalid explicit calendar date') from None


def _payload(category, value):
    if category == 'deck-composition':
        _fields(value, ('total_lands', 'claimed_swamps'))
        for count in value.values():
            if count is not None and (type(count) is not int or not 0 <= count <= COUNT_LIMIT):
                raise ReviewInputError('hypothetical deck counts must be integers 0..1000 or null')
        if all(v is None for v in value.values()): raise ReviewInputError('at least one declared count required')
        # Internal inconsistency is retained for quarantine, never silently repaired.
    elif category == 'objective-and-mana':
        _fields(value, ('objective', 'mana_requirements'))
        if type(value['objective']) is not str or value['objective'] not in strategic.OBJECTIVES:
            raise ReviewInputError('existing finite investigation objective required')
        _text(value['mana_requirements'], 240, nullable=True)
    elif category == 'format-legality-lead':
        _fields(value, ('format_label',))
        _text(value['format_label'], 80)
    elif category == 'performance-lead':
        _fields(value, ('method', 'sample_scope', 'limitations'))
        for text in value.values(): _text(text, 160, nullable=True)
    else: raise ReviewInputError('only four evidence categories supported')


def make_candidate(*, category, source, scope, assertion, payload, content=None,
                   claimed_use_restrictions=None, requirement_refs=None, notes=None):
    """Create an immutable submitted candidate, never an authentication or approval."""
    value = json.loads(c.owned(dict(category=category, source=source, scope=scope,
        assertion=assertion, payload=payload, content=content,
        claimed_use_restrictions=claimed_use_restrictions,
        requirement_refs=[] if requirement_refs is None else requirement_refs,
        notes=[] if notes is None else notes), limit=CANDIDATE_LIMIT))
    category, source, scope = value['category'], value['source'], value['scope']
    if type(category) is not str or category not in CATEGORIES: raise ReviewInputError('unsupported evidence category')
    _fields(source, ('type', 'claimed_origin', 'reference', 'source_date', 'observation_date'))
    if type(source['type']) is not str or source['type'] not in SOURCE_TYPES: raise ReviewInputError('unsupported declared source type')
    _text(source['claimed_origin'], 120, nullable=True)
    _text(source['reference'], 160, nullable=True)
    _date(source['source_date']); _date(source['observation_date'])
    _fields(scope, ('deck_id', 'deck_version', 'kind'))
    _text(scope['deck_id'], 64); _text(scope['deck_version'], 32)
    if type(scope['kind']) is not str or scope['kind'] != 'declared-hypothetical-deck':
        raise ReviewInputError('only declared hypothetical deck scope is authorized')
    _text(value['assertion'], 240); _payload(category, value['payload'])
    _text(value['claimed_use_restrictions'], 160, nullable=True)
    refs = value['requirement_refs']
    if type(refs) is not list or len(refs) > 4: raise ReviewInputError('at most four exact requirement references')
    for ref in refs: _digest(ref)
    if refs != sorted(set(refs)): raise ReviewInputError('unique sorted requirement references required')
    notes = value['notes']
    if type(notes) is not list or len(notes) > 3: raise ReviewInputError('at most three provenance notes')
    for note in notes: _text(note, 120)
    if len(notes) != len(set(notes)): raise ReviewInputError('duplicate note')
    body = value['content']
    if body is None:
        mode = 'reference-only' if category in ('format-legality-lead','performance-lead') or source['type']=='reference-lead' else 'declaration-only'
        body = dict(mode=mode, text=None, digest=None)
    _fields(body, ('mode', 'text', 'digest'))
    if type(body['mode']) is not str or body['mode'] not in MODES: raise ReviewInputError('unsupported content mode')
    if source['type']=='owner-supplied-excerpt' and body['mode']!='supplied-utf8':
        raise ReviewInputError('an owner-supplied excerpt requires directly supplied bytes')
    if source['type']=='reference-lead' and body['mode']!='reference-only':
        raise ReviewInputError('a reference lead has no supplied source content')
    if category in ('format-legality-lead','performance-lead') and body['mode']=='declaration-only':
        raise ReviewInputError('a source lead must explicitly distinguish absent from supplied content')
    if body['mode'] == 'supplied-utf8':
        if type(body['text']) is not str: raise ReviewInputError('directly supplied UTF-8 text required')
        try: raw = body['text'].encode('utf-8')
        except UnicodeError: raise ReviewInputError('invalid UTF-8 content') from None
        if not 1 <= len(raw) <= CONTENT_LIMIT or any(ord(ch) < 32 and ch not in '\n\r\t' for ch in body['text']):
            raise ReviewInputError('supplied content must contain 1..1024 bounded UTF-8 bytes')
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if body['digest'] is not None and body['digest'] != digest: raise ReviewInputError('supplied content digest mismatch')
        body['digest'] = digest
    else:
        if body['text'] is not None: raise ReviewInputError('absent content mode requires null text')
        _digest(body['digest'], nullable=True)
        if body['mode'] == 'declaration-only' and body['digest'] is not None:
            raise ReviewInputError('declaration-only content has no content digest')
    value['content'] = body
    value.update(schema_version=CANDIDATE_VERSION, authority=AUTHORITY,
        source_authentication='NOT_ESTABLISHED', permissions='NOT_ESTABLISHED')
    return c.ReviewDocument._verified(c.seal(CANDIDATE_VERSION,value,'candidate_id'),limit=CANDIDATE_LIMIT)


def validate_candidate(value):
    value = json.loads(c.owned(value, limit=CANDIDATE_LIMIT))
    _fields(value, ('schema_version','category','source','scope','assertion','payload','content',
        'claimed_use_restrictions','requirement_refs','notes','authority','source_authentication','permissions','candidate_id'))
    expected = make_candidate(**{k:value[k] for k in ('category','source','scope','assertion','payload','content',
        'claimed_use_restrictions','requirement_refs','notes')})
    c.exact(value, expected.to_dict(), limit=CANDIDATE_LIMIT)
    return expected


def make_packet(candidates=None):
    candidates = [] if candidates is None else json.loads(c.owned(candidates,limit=PACKET_LIMIT))
    if type(candidates) is not list or len(candidates) > MAX_CANDIDATES: raise ReviewInputError('at most four candidates')
    candidates = [validate_candidate(v).to_dict() for v in candidates]
    candidates.sort(key=lambda v:v['candidate_id'])
    ids = [v['candidate_id'] for v in candidates]
    if len(ids) != len(set(ids)): raise ReviewInputError('duplicate evidence candidate')
    if sum(len((v['content']['text'] or '').encode()) for v in candidates) > TOTAL_CONTENT_LIMIT:
        raise ReviewInputError('total supplied content exceeds 4096 bytes')
    value = dict(schema_version=PACKET_VERSION, schema_id=SCHEMA_ID, family=FAMILY,
        namespace=strategic.NAMESPACE,card_ids=list(CARD_IDS),subject_ids=list(SUBJECT_IDS),
        candidates=candidates,authority=AUTHORITY,canonical_admission=False,execution_authority='BLOCKED')
    return c.ReviewDocument._verified(c.seal(PACKET_VERSION,value,'packet_id'),limit=PACKET_LIMIT)


def validate_packet(value):
    value = json.loads(c.owned(value,limit=PACKET_LIMIT))
    _fields(value, ('schema_version','schema_id','family','namespace','card_ids','subject_ids','candidates',
        'authority','canonical_admission','execution_authority','packet_id'))
    expected=make_packet(value['candidates'])
    c.exact(value,expected.to_dict(),limit=PACKET_LIMIT)
    return expected


def parse_packet(raw): return validate_packet(c.parse_json(raw,limit=PACKET_LIMIT))


_SCHEMA = c.seal(SCHEMA_VERSION, dict(schema_version=SCHEMA_VERSION,
    candidate_version=CANDIDATE_VERSION,packet_version=PACKET_VERSION,categories=list(CATEGORIES),
    source_types=list(SOURCE_TYPES),content_modes=list(MODES),family=FAMILY,
    card_namespace=strategic.NAMESPACE,card_ids=list(CARD_IDS),subject_ids=list(SUBJECT_IDS),
    hypothetical_deck_count_limit=COUNT_LIMIT,max_candidates=MAX_CANDIDATES,
    candidate_byte_limit=CANDIDATE_LIMIT,packet_byte_limit=PACKET_LIMIT,
    content_byte_limit=CONTENT_LIMIT,total_content_byte_limit=TOTAL_CONTENT_LIMIT,
    definitions=dict(total_lands='Declared total land quantity in the hypothetical deck version.',
        claimed_swamps='Claimed subset of that declared total, not independently supported Card subtypes or controlled permanents.'),
    rules=['Only directly supplied owner review material; never fetch or authenticate references.',
        'Supplied bytes are hashed exactly as UTF-8, with no newline or Unicode normalization.',
        'Source identities, dates, observations, permissions and assertions remain claims.',
        'Deck scope labels are unverified and cannot authenticate that two real decks are the same.',
        'Internally inconsistent counts are retained for quarantine; no arithmetic correction.',
        'A new content identity is a different submission, not an approved revision of an earlier packet.'],
    authority=AUTHORITY,canonical_admission=False,execution_authority='BLOCKED'), 'schema_id')
_SCHEMA_RAW=c.owned(_SCHEMA,limit=8192)
SCHEMA_ID=_SCHEMA['schema_id']
del _SCHEMA


def schema_document(): return c.ReviewDocument._verified(json.loads(_SCHEMA_RAW),limit=8192)
