"""Read-only set census and review-candidate preparation over supplied JSON.

Uses the existing supplied-file manifest/adapter, schema validator, canonical
reader and EntityResolver. No acquisition, storage, promotion or activation.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json

from dataset_import.framework import EntityResolver
from external_ingestion.framework import DatasetManifest, JsonAdapter, ExternalDatasetError
from repository.cards import load_card_repository, canonical_repository_bytes
from repository.canonical import load_canonical_repository
from pathlib import Path
from validation import validate_document, SchemaValidationError

INPUT_VERSION = 'set-candidate-preparation-input-v1'
REPORT_VERSION = 'set-candidate-preparation-report-v1'
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000


class SetPreparationError(ValueError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', code=self.code,
                    reason=str(self), canonical_admission='NOT_PERFORMED')


def _require(condition, reason, code='INVALID_INPUT'):
    if not condition:
        raise SetPreparationError(code, reason)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _hash(value):
    return sha256(value if type(value) is bytes else canonical_json(value).encode()).hexdigest()


def _closed(value, fields):
    _require(type(value) is dict and value.keys() == set(fields), 'closed object fields required')


def _text(value):
    _require(type(value) is str and 0 < len(value) <= 128 and value == value.strip()
             and value.isprintable(), 'bounded nonempty identifier required')


def _strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, 'duplicate JSON object key')
            result[key] = value
        return result
    def nonfinite(_):
        raise SetPreparationError('INVALID_INPUT', 'nonfinite JSON number')
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        raise SetPreparationError('INVALID_INPUT', 'invalid bounded JSON') from None


def prepare_set_candidates(payload, manifest, request, *, game, games_root,
                           authorize_source=None):
    """Return a deterministic PRIVATE review report; never admit records.

    ``authorize_source`` is trusted host code, not a request/config flag. It must
    independently establish processing AND private candidate retention for the
    exact bindings supplied. None refuses before source parsing. This hook is
    not a licensing determination, approval framework or production authority.
    The standalone library supplies no real-provider permission integration.
    ``games_root`` explicitly selects the existing validated canonical reader.
    """
    _text(game)
    _require(type(payload) is bytes and len(payload) <= MAX_BYTES, 'bounded JSON bytes required')
    _closed(request, ('schema_version', 'set_code', 'inventory_reference', 'expected_inventory'))
    _require(request['schema_version'] == INPUT_VERSION, 'unsupported request version')
    _text(request['set_code']); _text(request['inventory_reference'])
    _require(request['set_code'].isalnum() and request['set_code'].isascii(), 'set code must be ASCII alphanumeric')
    expected = request['expected_inventory']
    if expected is not None:
        _require(type(expected) is list and 1 <= len(expected) <= MAX_ROWS, 'bounded expected inventory required')
        keys = []
        for item in expected:
            _closed(item, ('entity_type', 'id')); _text(item['id'])
            _require(item['entity_type'] in ('card', 'printing'), 'unsupported expected entity type')
            keys.append((item['entity_type'], item['id']))
        _require(len(keys) == len(set(keys)), 'duplicate expected identity')
    else:
        keys = None
    _require(type(manifest) is dict, 'manifest object required')
    try:
        manifest_size = len(canonical_json(manifest).encode())
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise SetPreparationError('INVALID_MANIFEST', 'manifest must be bounded JSON data') from None
    _require(manifest_size <= 16384, 'bounded manifest required')
    for optional in ('notes', 'manifest_schema'):
        _require(optional not in manifest or type(manifest[optional]) is str, 'manifest optional strings required')
    allowed = {'manifest_schema','dataset_name','logical_identity','version','provider','publication_date',
               'source_attribution','license','expected_entity_types','schema_version','checksum','data_file','notes'}
    _require(manifest.keys() <= allowed, 'unknown manifest fields')
    for field in allowed - {'notes', 'expected_entity_types', 'manifest_schema'}:
        _require(type(manifest.get(field)) is str and bool(manifest[field].strip()), 'manifest string fields required')
    _require(type(manifest.get('expected_entity_types')) is list, 'manifest entity list required')
    try:
        description = DatasetManifest.from_dict(deepcopy(manifest))
    except (ExternalDatasetError, TypeError, ValueError):
        raise SetPreparationError('INVALID_MANIFEST', 'supplied-file manifest validation failed') from None
    _require(description.checksum == _hash(payload), 'source checksum mismatch', 'INTEGRITY_MISMATCH')
    _require(description.schema_version == 'supplied-canonical-records-v1'
             and description.expected_entity_types == ('card', 'printing')
             and description.data_file.endswith('.json'), 'unsupported supplied-file profile', 'UNSUPPORTED_PROFILE')
    request = deepcopy(request)
    request['set_code'] = request['set_code'].upper()
    if keys is not None:
        request['expected_inventory'] = [dict(entity_type=k, id=i) for k, i in sorted(keys)]
    bindings = dict(operation='private-set-candidate-preparation-v1', artifact_sha256=_hash(payload),
                    manifest_sha256=_hash(description.as_dict()), request_sha256=_hash(request))
    # A supplied license string, possession of bytes, or matching hash is NOT permission.
    _require(callable(authorize_source), 'source-use processing and private retention not established', 'SOURCE_POLICY_REFUSAL')
    try:
        authorized = authorize_source(deepcopy(bindings))
    except Exception:
        raise SetPreparationError('SOURCE_POLICY_REFUSAL', 'host source-use disposition unavailable') from None
    _require(authorized is True, 'host did not authorize the exact private operation', 'SOURCE_POLICY_REFUSAL')
    doc = _strict_json(payload)
    _closed(doc, ('records',))
    _require(type(doc['records']) is list and len(doc['records']) <= MAX_ROWS, 'bounded source row list required')
    # Reuse the public supplied JSON adapter after stricter closed-envelope parsing.
    try:
        rows = list(JsonAdapter().records(payload))
    except ExternalDatasetError:
        raise SetPreparationError('INVALID_INPUT', 'supplied JSON row profile failed') from None
    try:
        _require(games_root is not None and (Path(games_root) / game).is_dir(), 'explicit existing catalog required')
        load_canonical_repository(game, games_root=games_root)
        cards, printings = load_card_repository(game, games_root=games_root)
        catalog_bytes = canonical_repository_bytes(game, games_root=games_root)
    except ValueError:
        raise SetPreparationError('CATALOG_UNAVAILABLE', 'selected canonical catalog cannot be validated') from None
    catalog = {('card', c['id']): c for c in cards}
    catalog.update({('printing', p['id']): p for p in printings})
    decisions = []
    prepared = []
    observed = []
    for index, row in enumerate(rows):
        item = dict(source_index=index, source_row_sha256=_hash(row), identity=None,
                    disposition='REJECTED', reasons=[])
        decisions.append(item)
        try:
            _closed(row, ('id', 'entity_type', 'normalized', 'identifiers'))
            _text(row['id'])
            kind = row['entity_type']; _require(kind in ('card', 'printing'), 'unsupported row entity type')
            record = row['normalized']; _require(type(record) is dict, 'canonical-shaped record required')
            if type(record.get('id')) is str:
                _text(record['id'])
                item['identity'] = dict(entity_type=kind, id=record['id'])
                observed.append((kind, record['id']))
            _require(record.get('schema_version') == 'v1', 'V1 supports canonical-shaped v1 records only')
            validate_document(record, kind)
            _require(all(p['source_id'] == description.logical_identity for p in record['provenance']), 'candidate source provenance differs from manifest')
            if kind == 'card':
                _require(record['game'] == game, 'Card game differs from selected catalog')
            else:
                _require(record['set_code'].upper() == request['set_code'], 'Printing belongs to a different set')
            ids = row['identifiers']
            _require(type(ids) is dict and ids.keys() <= set(EntityResolver.NAMESPACES), 'unsupported identity namespaces')
            _require(ids.get('canonical_identifier') == record['id'], 'exact canonical identifier binding required')
            for namespace, values in ids.items():
                values = [values] if type(values) is str else values
                _require(type(values) is list and len(values) <= 16, 'bounded identifiers required')
                for value in values: _text(value)
                _require(len(values) == len(set(values)), 'duplicate aliases')
            if kind == 'card':
                _require(record.get('layout') == 'normal', 'multiface or unsupported layout requires independent review', 'UNRESOLVED_MULTIFACE')
            prior = catalog.get((kind, record['id']))
            if prior is not None:
                left = {k:v for k,v in prior.items() if k != 'provenance'}
                right = {k:v for k,v in record.items() if k != 'provenance'}
                _require(left == right, 'candidate conflicts with existing canonical record', 'CATALOG_IDENTITY_CONFLICT')
                item['catalog_relation'] = 'EXISTING_IDENTICAL_CONTENT'
            else:
                item['catalog_relation'] = 'NEW_DECLARED_IDENTITY'
            item['disposition'] = 'ELIGIBLE'
            prepared.append((index, row))
        except (SetPreparationError, SchemaValidationError, KeyError, TypeError) as error:
            item['disposition'] = 'QUARANTINED'
            item['reasons'].append(error.code if isinstance(error, SetPreparationError) else 'INVALID_SCHEMA_OR_IDENTITY')
    counts = Counter(observed)
    duplicates = [dict(entity_type=k, id=i, source_rows=n) for (k,i),n in sorted(counts.items()) if n > 1]
    row_counts = Counter(row.get('id') for row in rows if type(row.get('id')) is str)
    # Resolver owns alias collision policy. Namespace aliases are scoped by entity
    # kind, never conflating a Card identity with a Printing identity.
    resolution_rows = []
    supplied_cards = {row['normalized']['id'] for _,row in prepared if row['entity_type']=='card'}
    for card in cards:
        if card['id'] in supplied_cards:
            continue
        ids = {'canonical_identifier': 'card:' + card['id']}
        if card.get('oracle_id'):
            ids['external_identifiers'] = ['card:oracle:' + card['oracle_id']]
        resolution_rows.append(dict(id='catalog:card:' + card['id'], entity_type='card', identifiers=ids))
    for index, row in prepared:
        kind = row['entity_type']
        identifiers = {key: ([kind + ':' + value for value in values] if type(values) is list else kind + ':' + values)
                       for key,values in row['identifiers'].items()}
        if kind == 'card' and row['normalized'].get('oracle_id'):
            values = identifiers.get('external_identifiers', [])
            if type(values) is str: values = [values]
            identifiers['external_identifiers'] = sorted(set(values + ['card:oracle:' + row['normalized']['oracle_id']]))
        resolution_rows.append(dict(id=str(index), entity_type=kind, identifiers=identifiers))
    # An unresolved source row might contain an alias claim that cannot safely
    # participate in resolution. Withhold all candidates rather than hiding it.
    invalid_rows = any(item['disposition'] != 'ELIGIBLE' for item in decisions)
    resolution = EntityResolver().resolve(resolution_rows)
    refused = {int(row['source_id']): row['reason'] for row in resolution['rejected'] + resolution['unresolved']
               if row['source_id'].isdigit()}
    for index, row in prepared:
        item = decisions[index]; identity = (row['entity_type'], row['normalized']['id'])
        if invalid_rows or counts[identity] > 1 or row_counts[row['id']] > 1 or index in refused:
            item['disposition'] = 'QUARANTINED'
            item['reasons'].append(refused.get(index, 'UNRESOLVED_BATCH_PREMISES' if invalid_rows else 'DUPLICATE_RECORD'))
    # A quarantined Card never leaves its Printing dependency confidently eligible.
    eligible_cards = {row['normalized']['id'] for index,row in prepared
                      if row['entity_type']=='card' and decisions[index]['disposition']=='ELIGIBLE'}
    bad_cards = {x['identity']['id'] for x in decisions if x['identity'] and x['identity']['entity_type']=='card'
                 and x['disposition']!='ELIGIBLE'}
    eligible_cards.update(c['id'] for c in cards if c['id'] not in bad_cards)
    candidates = []
    for index, row in prepared:
        item = decisions[index]
        if row['entity_type']=='printing' and row['normalized']['card_id'] not in eligible_cards:
            item['disposition']='QUARANTINED'; item['reasons'].append('CARD_DEPENDENCY_UNRESOLVED')
        if item['disposition']=='ELIGIBLE':
            candidates.append(dict(source_index=index, entity_type=row['entity_type'], record=deepcopy(row['normalized']),
                                   review_status='pending', canonical_admission=False))
    if canonical_repository_bytes(game, games_root=games_root) != catalog_bytes:
        raise SetPreparationError('CATALOG_DRIFT', 'catalog changed during preparation')
    actual = set(observed)
    missing = sorted(set(keys)-actual) if keys is not None else []
    unexpected = sorted(actual-set(keys)) if keys is not None else []
    identity_unknown = any(item['identity'] is None for item in decisions)
    complete = ('UNKNOWN' if keys is None or identity_unknown else
                'INCOMPLETE_OR_CONTRADICTORY' if missing or unexpected or duplicates else
                'UNKNOWN' if any(i['disposition']!='ELIGIBLE' for i in decisions) else 'COMPLETE_DECLARED_INVENTORY')
    report = dict(schema_version=REPORT_VERSION, input=request, bindings={**bindings, 'catalog_sha256':_hash(catalog_bytes)},
        manifest=description.as_dict(), file_coverage=dict(status='ALL_SOURCE_ROWS_ACCOUNTED', source_rows=len(rows), accounted_rows=len(decisions)),
        declared_completeness=dict(status=complete, expected=deepcopy(request['expected_inventory']),
            observed=[dict(entity_type=k,id=i,source_rows=n) for (k,i),n in sorted(counts.items())],
            missing=[dict(entity_type=k,id=i) for k,i in missing], unexpected=[dict(entity_type=k,id=i) for k,i in unexpected]),
        duplicates=duplicates, duplicate_source_row_ids=sorted(k for k,n in row_counts.items() if n>1), identity_resolution=resolution, rows=decisions, candidates=candidates,
        accepted_candidate_rows=[i['source_index'] for i in decisions if i['disposition']=='ELIGIBLE'],
        quarantined_rows=[i['source_index'] for i in decisions if i['disposition']=='QUARANTINED'],
        identity_conflicts=dict(aliases=resolution['collisions'], catalog_rows=[i['source_index'] for i in decisions if 'CATALOG_IDENTITY_CONFLICT' in i['reasons']]),
        unresolved_multiface_rows=[i['source_index'] for i in decisions if 'UNRESOLVED_MULTIFACE' in i['reasons']],
        unresolved_identity_rows=[i['source_index'] for i in decisions if i['identity'] is None],
        candidate_preparation_status=('PARTIAL_QUARANTINED' if not rows or len(candidates)!=len(rows) else
                                      'PENDING_HUMAN_REVIEW' if complete=='COMPLETE_DECLARED_INVENTORY' else 'REVIEW_REQUIRED_POPULATION_GAPS'),
        source_use=dict(status='HOST_AUTHORIZED_PRIVATE_OPERATION_ONLY', licensing_rights='NOT_ESTABLISHED_BY_THIS_REPORT',
                        publication='NOT_AUTHORIZED', external_ai_export='NOT_AUTHORIZED'),
        canonical_admission=dict(status='NOT_PERFORMED', approved_count=0),
        real_world_set_completeness='NOT_ESTABLISHED', real_card_execution_authorized=False)
    report['report_id']='sha256:'+_hash(report)
    return report
