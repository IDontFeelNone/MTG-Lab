"""Generic independent weighted draws; no physical or gameplay collation inference."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

from query import CanonicalQueryEngine
from repository.sources import load_source_record
from validation import validate_document

VERSION = 'pack-simulation-v0'
ALGORITHM = 'sha256-counter-rejection-256-v1'
MODEL = 'independent-weighted-with-replacement-v1'
FINISH_VERSION = 'pack-simulation-v0.1'
FINISH_MODEL = 'independent-finish-weighted-with-replacement-v1'
MAX_CARDS = 1024
MAX_SLOTS = 32
MAX_POOL = 10000
MAX_INTEGER = 2**64 - 1


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()


def _identity(domain, value):
    return 'sha256:' + hashlib.sha256(domain.encode() + b'\0' + _json(value)).hexdigest()


class PackSimulationError(ValueError):
    """Structured refusal; missing inputs never produce a partial pack."""
    code = 'NOT_READY_FOR_SIMULATION'

    def __init__(self, *requirements):
        self.requirements = tuple(sorted(set(requirements)))
        super().__init__(self.code + ': ' + ', '.join(self.requirements))

    def as_dict(self):
        return dict(schema_version=VERSION, status=self.code,
                    missing_requirements=list(self.requirements), production_authorized=False)


def _require(condition, reason):
    if not condition:
        raise PackSimulationError(reason)


def _ticket(seed, counter, total):
    """Uniform integer in [0,total), without modulo bias; explicit counter stream."""
    limit = 2**256 - (2**256 % total)
    while True:
        digest = hashlib.sha256(ALGORITHM.encode() + b'\0' +
                                str(seed).encode() + b'\0' + str(counter).encode()).digest()
        counter += 1
        value = int.from_bytes(digest, 'big')
        if value < limit:
            return value % total, counter


def _select(entries, ticket):
    for printing_id, weight in entries:
        if ticket < weight:
            return printing_id
        ticket -= weight
    raise PackSimulationError('DRAW_OUTSIDE_DECLARED_POOL')


class _PackSimulator:
    def __init__(self, query):
        self._query = query

    def generate(self, product_id, *, pack_definition_id=None, seed, recorded_at=None):
        """Generate exactly one pack; every result remains a non-production model."""
        _require(type(seed) is int and 0 <= seed <= MAX_INTEGER, 'INVALID_SEED')
        _require(type(product_id) is str and product_id != '', 'INVALID_PRODUCT_ID')
        _require(pack_definition_id is None or type(pack_definition_id) is str,
                 'INVALID_PACK_DEFINITION_ID')
        if recorded_at is not None:
            try:
                _require(type(recorded_at) is str and recorded_at.endswith('Z'), 'INVALID_RECORDED_AT')
                datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                raise PackSimulationError('INVALID_RECORDED_AT') from None
        try:
            return self._generate(product_id, pack_definition_id, seed, recorded_at)
        except PackSimulationError:
            raise
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            raise PackSimulationError('INVALID_DEFINITION_OR_SOURCE_EVIDENCE') from None

    def _generate(self, product_id, pack_id, seed, recorded_at):
        snapshot = self._query.snapshot()
        items = {(x.entity_type, x.canonical_identity): x.as_dict() for x in snapshot.entities}
        product = items.get(('product', product_id))
        _require(product is not None, 'UNKNOWN_PRODUCT')
        values = product['canonical_values']
        versions = [v for (kind, _), v in items.items() if kind == 'product_version'
                    and v['canonical_values']['product_id'] == product_id]
        packs = [p for (kind, _), p in items.items() if kind == 'pack_definition'
                 and p['canonical_values']['product_version_id'] in
                 {v['canonical_identity'] for v in versions}]
        missing = []
        if values['lifecycle_status'] != 'validated': missing.append('PRODUCT_NOT_VALIDATED')
        if not versions: missing.append('ADMITTED_PRODUCT_VERSION_MISSING')
        if not packs:
            missing.extend(('ADMITTED_PACK_DEFINITION_MISSING', 'ADMITTED_SLOT_DEFINITIONS_MISSING',
                            'VALIDATED_PRINTING_POOLS_AND_WEIGHTS_MISSING',
                            'EXPLICIT_COLLATION_MODEL_MISSING'))
        if missing: raise PackSimulationError(*missing)
        _require(pack_id is not None, 'EXPLICIT_PACK_DEFINITION_SELECTION_REQUIRED')
        selected = next((p for p in packs if p['canonical_identity'] == pack_id), None)
        _require(selected is not None, 'UNKNOWN_OR_FOREIGN_PACK_DEFINITION')
        records = {}
        sources = {}

        def record(kind, identifier, schema, schema_version="v2"):
            if (kind, identifier) in records:
                return records[kind, identifier]['record']
            item = items.get((kind, identifier))
            _require(item is not None, 'UNKNOWN_' + kind.upper())
            _require(item['supersession_state'] == 'current' and
                     item['uncertainty'] == 'known', 'UNRESOLVED_OR_SUPERSEDED_' + kind.upper())
            raw = self._query.retained_record(identifier, entity_type=kind)
            _require(raw.get('schema_version') == schema_version,
                     'EXPLICIT_' + schema_version.upper() + '_' + kind.upper() + '_REQUIRED')
            validate_document(raw, schema, schema_version)
            _require(raw['game'] == snapshot.game and raw['id'] == identifier, 'IDENTITY_MISMATCH')
            covered = set()
            for provenance in raw['provenance']:
                covered.update(provenance['field_paths'])
                source_id = provenance['source_id']
                if source_id not in sources:
                    sources[source_id] = load_source_record(snapshot.game, product_id, source_id,
                                                           games_root=self._query.games_root)
                _require(sources[source_id]['verification_status'] == 'confirmed',
                         'UNCONFIRMED_DEFINITION_SOURCE')
            _require(set(raw) - {'schema_version', 'provenance'} == covered,
                     'INCOMPLETE_OR_UNKNOWN_FIELD_PROVENANCE')
            records[kind, identifier] = dict(kind=kind, id=identifier, record=raw, query_evidence=item)
            return raw

        product_raw = record('product', product_id, 'product')
        version_id = selected['canonical_values']['product_version_id']
        version = record('product_version', version_id, 'product-version')
        pack = record('pack_definition', pack_id, 'pack-definition')
        _require(version_id in product_raw['version_ids'] and version['product_id'] == product_id
                 and pack['product_version_id'] == version_id, 'PRODUCT_PACK_RELATIONSHIP_MISMATCH')
        _require(any(c['component_type'] == 'pack_definition' and c['component_id'] == pack_id
                     for c in version['components']), 'PACK_NOT_IN_PRODUCT_VERSION')
        model = pack.get('metadata', {}).get('simulation_model')
        _require(model in (MODEL, FINISH_MODEL) and pack['metadata'] == {'simulation_model': model},
                 'UNSUPPORTED_OR_MISSING_COLLATION_MODEL')
        finish_aware = model == FINISH_MODEL
        report_version = FINISH_VERSION if finish_aware else VERSION
        _require(not product_raw.get('metadata') and not version.get('metadata'), 'UNSUPPORTED_PRODUCT_METADATA')
        _require(len(pack['slot_ids']) <= MAX_SLOTS, 'SLOT_BOUND_EXCEEDED')
        draws = []
        total_cards = 0
        for slot_id in pack['slot_ids']:
            slot = record('slot', slot_id, 'slot')
            sheet = record('print_sheet', slot['print_sheet_id'], 'print-sheet',
                           'v3' if finish_aware else 'v2')
            _require(slot['replacement'] is True, 'WITHOUT_REPLACEMENT_UNSUPPORTED')
            _require(not slot.get('metadata') and not sheet.get('metadata'), 'UNSUPPORTED_SLOT_OR_SHEET_METADATA')
            count = slot['draw_count']; total_cards += count
            _require(type(count) is int and total_cards <= MAX_CARDS, 'CARD_COUNT_BOUND_EXCEEDED')
            entries = sorted(((e['printing_id'], e['finish_id']) if finish_aware else e['printing_id'],
                              e['weight']) for e in sheet['entries'])
            _require(0 < len(entries) <= MAX_POOL and len({p for p, _ in entries}) == len(entries),
                     'EMPTY_OVERSIZED_OR_DUPLICATE_POOL')
            _require(all(type(w) is int and 0 < w <= MAX_INTEGER for _, w in entries)
                     and sum(w for _, w in entries) <= MAX_INTEGER, 'INVALID_EXPLICIT_WEIGHTS')
            for outcome, _ in entries:
                printing_id = outcome[0] if finish_aware else outcome
                printing = items.get(('printing', printing_id))
                _require(printing is not None, 'UNKNOWN_PRINTING')
                _require(printing['supersession_state'] == 'current' and printing['uncertainty'] == 'known',
                         'UNRESOLVED_OR_SUPERSEDED_PRINTING')
                if finish_aware:
                    finish_id = outcome[1]
                    finish = items.get(('finish', finish_id))
                    _require(finish is not None and finish['uncertainty'] == 'known'
                             and finish['supersession_state'] == 'current', 'UNKNOWN_OR_UNRESOLVED_FINISH')
                    raw = self._query.retained_record(printing_id, entity_type='printing')
                    # The owning Card reader has admitted this record. Require an explicit
                    # source-bound finish fact; compatibility defaults are never sufficient.
                    _require(raw.get('schema_version') == 'v3' and type(raw.get('finishes')) is list
                             and finish_id in raw['finishes'], 'UNSUPPORTED_PRINTING_FINISH')
                    assertions = [a for a in raw['assertions'] if a['path'] == '/finishes'
                                  and a['status'] not in ('rejected', 'superseded')]
                    _require(assertions and all(a['subject_id'] == printing_id
                             and a['status'] == 'promoted'
                             and a['verification_status'] in ('confirmed', 'verified')
                             and a['evidence_class'] not in ('unknown', 'conflicting')
                             and a['asserted_value'] == raw['finishes'] for a in assertions),
                             'UNRESOLVED_PRINTING_FINISH_EVIDENCE')
                    for assertion in assertions:
                        source_id = assertion['source_id']
                        if source_id not in sources:
                            sources[source_id] = load_source_record(snapshot.game, product_id, source_id,
                                                                   games_root=self._query.games_root)
                        _require(sources[source_id]['verification_status'] == 'confirmed',
                                 'UNCONFIRMED_PRINTING_FINISH_SOURCE')
                    records['printing', printing_id] = dict(kind='printing', id=printing_id,
                                                           record=raw, query_evidence=printing)
                    records['finish', finish_id] = dict(kind='finish', id=finish_id, query_evidence=finish)
                else:
                    records['printing', printing_id] = dict(kind='printing', id=printing_id, query_evidence=printing)
            draws.append((slot_id, sheet['id'], count, entries))
        records = [records[key] for key in sorted(records)]
        inputs = dict(query_snapshot_id=snapshot.snapshot_id, records=records, sources=sources)
        input_id = _identity('pack-simulation-input-v0.1' if finish_aware else 'pack-simulation-input-v0', inputs)
        counter = 0; slots = []
        for slot_id, sheet_id, count, entries in draws:
            selected_ids = []
            for _ in range(count):
                ticket, counter = _ticket(seed, counter, sum(w for _, w in entries))
                selected_ids.append(_select(entries, ticket))
            _require(len(selected_ids) == count, 'SLOT_RESULT_COUNT_MISMATCH')
            selections = {'outcomes': [dict(printing_id=p, finish_id=f) for p, f in selected_ids]} if finish_aware else {'printing_ids': selected_ids}
            slots.append(dict(slot_id=slot_id, print_sheet_id=sheet_id, **selections))
        key = 'outcomes' if finish_aware else 'printing_ids'
        _require(sum(len(s[key]) for s in slots) == total_cards, 'PACK_RESULT_COUNT_MISMATCH')
        return dict(schema_version=report_version, status='GENERATED', simulator_version=report_version,
                    algorithm=ALGORITHM, sampling_model=model, seed=seed, recorded_at=recorded_at,
                    timestamp_authority='caller_supplied' if recorded_at is not None else 'unspecified',
                    game=snapshot.game, product_id=product_id, product_version_id=version_id,
                    pack_definition_id=pack_id, query_snapshot_id=snapshot.snapshot_id, input_id=input_id,
                    database_version=None, production_authorized=False,
                    scope='EXPLICIT_DEFINITION_MODEL_ONLY_NON_PRODUCTION', card_count=total_cards,
                    slots=slots, evidence_references=[dict(kind=r['kind'], id=r['id'],
                    content_id=_identity('pack-simulation-record-v0', r)) for r in records],
                    source_references=[dict(id=k, content_id=_identity('pack-simulation-source-v0', v))
                                       for k, v in sorted(sources.items())])


def load_pack_simulator(game='magic', *, data_root=None, attachment=None):
    """Revalidate through owning readers; no fallback for invalid/unsupported snapshots."""
    try:
        if attachment is not None:
            CanonicalQueryEngine.from_attachment(attachment)
            raise PackSimulationError('ATTACHED_SNAPSHOT_SIMULATION_CAPABILITY_UNAVAILABLE')
        if data_root is None:
            query = CanonicalQueryEngine(game)
        else:
            root = Path(data_root)
            query = CanonicalQueryEngine(game, data_root=root, games_root=root/'canonical/games')
        _require((query.games_root/game/'game.json').is_file(), 'EXPLICIT_GAME_RECORD_REQUIRED')
        return _PackSimulator(query)
    except PackSimulationError:
        raise
    except (ValueError, OSError, KeyError, TypeError, AttributeError):
        raise PackSimulationError('CANONICAL_INPUT_UNAVAILABLE_OR_INVALID') from None


def render_pack_report(report, *, readable=False):
    if not readable:
        return json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n'
    if report['status'] != 'GENERATED':
        return report['status'] + '\n' + '\n'.join('- ' + r for r in report['missing_requirements']) + '\n'
    lines = [f"{report['product_id']} / {report['pack_definition_id']}: {report['card_count']} cards",
             f"Seed {report['seed']}; {report['algorithm']}; non-production definition model"]
    if report['schema_version'] == FINISH_VERSION:
        lines += [FINISH_VERSION + ': explicit Printing + Finish outcomes']
        lines += [s['slot_id'] + ': ' + ', '.join(
            o['printing_id'] + ' [' + o['finish_id'] + ']' for o in s['outcomes']) for s in report['slots']]
    else:
        lines += [s['slot_id'] + ': ' + ', '.join(s['printing_ids']) for s in report['slots']]
    lines += ['Input: ' + report['input_id'], 'No physical collation or production authority established.']
    return '\n'.join(lines) + '\n'
