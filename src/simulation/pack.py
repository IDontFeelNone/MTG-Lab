"""Generic independent weighted draws; no physical or gameplay collation inference."""
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from query import CanonicalQueryEngine
from repository.sources import load_source_record
from validation import validate_document

VERSION = 'pack-simulation-v0'
ALGORITHM = 'sha256-counter-rejection-256-v1'
MODEL = 'independent-weighted-with-replacement-v1'
VARIANT_VERSION = 'pack-simulation-v0.2'
VARIANT_MODEL = 'weighted-finish-pack-variants-with-replacement-v1'
FINISH_VERSION = 'pack-simulation-v0.1'
FINISH_MODEL = 'independent-finish-weighted-with-replacement-v1'
MAX_CARDS = 1024
MAX_SLOTS = 32
MAX_POOL = 10000
MAX_INTEGER = 2**64 - 1
MAX_COMPOSITION_BYTES = 4 * 1024 * 1024
_VIEW_KEY = object()


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


@dataclass(frozen=True, init=False)
class ValidatedPackComposition:
    """Immutable owning-reader view; hashes confer no production authority."""
    _encoded: bytes

    def __init__(self, encoded, *, _key=None):
        _require(_key is _VIEW_KEY and type(encoded) is bytes, 'OWNING_COMPOSITION_ADMISSION_REQUIRED')
        object.__setattr__(self, '_encoded', encoded)

    def to_dict(self):
        """Detached composition and original evidence, without a private query handle."""
        return json.loads(self._encoded)

    def resolve_target(self, target):
        _require(type(target) is dict and {'kind', 'id'} <= target.keys()
                 and target.keys() <= {'kind', 'id', 'finish_id', 'treatment_id'}, 'INVALID_TARGET_FIELDS')
        _require(type(target['kind']) is str and target['kind'] in ('card', 'printing'), 'INVALID_TARGET_KIND')
        _require(all(type(v) is str and 0 < len(v) <= 128 and v == v.strip()
                     and v.isprintable() for v in target.values()), 'INVALID_TARGET_IDENTITY')
        body = self.to_dict(); context = body['context']; catalog = body['catalog']

        def known(kind, identifier):
            rows = catalog[kind].get(identifier, [])
            _require(len(rows) == 1 and rows[0]['uncertainty'] == 'known'
                     and rows[0]['supersession_state'] == 'current', 'UNKNOWN_AMBIGUOUS_OR_UNRESOLVED_TARGET_' + kind.upper())

        known(target['kind'], target['id'])
        for field, kind in (('finish_id', 'finish'), ('treatment_id', 'treatment')):
            if field in target: known(kind, target[field])
        if 'finish_id' in target:
            _require(context['finish_aware'], 'LEGACY_FINISH_PROBABILITY_UNSUPPORTED')

        def field_value(pid, field):
            raw = body['printing_evidence'][pid]
            _require(field in raw, 'EXPLICIT_TARGET_' + field.upper() + '_EVIDENCE_REQUIRED')
            if raw['schema_version'] == 'v3':
                assertions = [a for a in raw['assertions'] if a['path'] == '/' + field
                              and a['status'] not in ('rejected', 'superseded')]
                _require(assertions and all(a['subject_id'] == pid and a['status'] == 'promoted'
                         and a['verification_status'] in ('confirmed', 'verified')
                         and a['evidence_class'] not in ('unknown', 'conflicting')
                         and a['asserted_value'] == raw[field] for a in assertions),
                         'UNRESOLVED_TARGET_' + field.upper() + '_EVIDENCE')
                source_ids = {a['source_id'] for a in assertions}
            else:
                source_ids = {p['source_id'] for p in raw.get('provenance', []) if field in p['field_paths']}
            _require(source_ids and all(body['field_sources'].get(s, {}).get('verification_status') == 'confirmed'
                                       for s in source_ids), 'UNCONFIRMED_TARGET_FIELD_SOURCE')
            return raw[field]

        eligible = set()
        for pid in body['printing_evidence']:
            if target['kind'] == 'card':
                card_id = field_value(pid, 'card_id')
                known('card', card_id)
                _require(card_id == catalog['printing'][pid][0]['card_id'], 'TARGET_CARD_JOIN_CONFLICT')
                matches = card_id == target['id']
            else:
                matches = pid == target['id']
            if not matches: continue
            _require(field_value(pid, 'id') == pid, 'TARGET_PRINTING_IDENTITY_CONFLICT')
            if 'treatment_id' in target:
                treatments = field_value(pid, 'treatments')
                _require(type(treatments) is list and len(treatments) <= 1
                         and all(type(t) is str for t in treatments), 'AMBIGUOUS_FIXED_TREATMENT')
                if target['treatment_id'] not in treatments: continue
            eligible.add(pid)
        outcomes = set()
        for draws, _ in context['candidates'].values():
            for _, _, _, entries in draws:
                for outcome, _ in entries:
                    pid, finish = outcome if context['finish_aware'] else (outcome, None)
                    if pid in eligible and ('finish_id' not in target or target['finish_id'] == finish):
                        outcomes.add((pid, finish))
        matched = [dict(printing_id=p, finish_id=f) for p, f in sorted(outcomes)]
        return dict(target=dict(target), matched_outcomes=matched,
                    target_id=_identity('pack-target-resolution-v1', dict(
                        composition_id=body['composition_id'], target=target, matched_outcomes=matched)))


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

    def inspect(self, product_id, *, pack_definition_id=None):
        """Admit every composition without drawing; target facts stay source-bound."""
        _require(type(product_id) is str and product_id != '', 'INVALID_PRODUCT_ID')
        _require(pack_definition_id is None or type(pack_definition_id) is str, 'INVALID_PACK_DEFINITION_ID')
        try:
            context = self._admit(product_id, pack_definition_id)
            catalog = {k: {} for k in ('card', 'printing', 'finish', 'treatment')}
            for entity in self._query.snapshot().entities:
                if entity.entity_type not in catalog: continue
                row = dict(uncertainty=entity.uncertainty, supersession_state=entity.supersession_state)
                if entity.entity_type == 'printing': row['card_id'] = entity.as_dict()['canonical_values']['card_id']
                catalog[entity.entity_type].setdefault(entity.canonical_identity, []).append(row)
            printing_evidence = {}; field_sources = dict(context['sources'])
            for record in context['records']:
                if record['kind'] != 'printing': continue
                raw = self._query.retained_record(record['id'], entity_type='printing')
                printing_evidence[record['id']] = raw
                for evidence in raw.get('assertions', raw.get('provenance', [])):
                    source_id = evidence['source_id']
                    if source_id in field_sources: continue
                    try:
                        field_sources[source_id] = load_source_record(self._query.game, product_id, source_id,
                                                                      games_root=self._query.games_root)
                    except (ValueError, OSError, KeyError, TypeError):
                        pass  # Absence remains absence; resolve_target refuses if this field is needed.
            body = dict(context=context, catalog=catalog, printing_evidence=printing_evidence,
                        field_sources=field_sources)
            body['composition_id'] = _identity('validated-pack-composition-v1', body)
            encoded = _json(body)
            _require(len(encoded) <= MAX_COMPOSITION_BYTES, 'COMPOSITION_VIEW_BYTE_BOUND_EXCEEDED')
            return ValidatedPackComposition(encoded, _key=_VIEW_KEY)
        except PackSimulationError:
            raise
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            raise PackSimulationError('INVALID_DEFINITION_OR_SOURCE_EVIDENCE') from None

    def _admit(self, product_id, pack_id):
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
        variant_model = selected['canonical_values']['schema_version'] == 'v3'
        pack = record('pack_definition', pack_id, 'pack-definition', 'v3' if variant_model else 'v2')
        _require(version_id in product_raw['version_ids'] and version['product_id'] == product_id
                 and pack['product_version_id'] == version_id, 'PRODUCT_PACK_RELATIONSHIP_MISMATCH')
        _require(any(c['component_type'] == 'pack_definition' and c['component_id'] == pack_id
                     for c in version['components']), 'PACK_NOT_IN_PRODUCT_VERSION')
        model = pack.get('metadata', {}).get('simulation_model')
        _require(pack.get('metadata') == {'simulation_model': model}
                 and (model == VARIANT_MODEL if variant_model else model in (MODEL, FINISH_MODEL)),
                 'UNSUPPORTED_OR_MISSING_COLLATION_MODEL')
        finish_aware = variant_model or model == FINISH_MODEL
        report_version = VARIANT_VERSION if variant_model else FINISH_VERSION if finish_aware else VERSION
        _require(not product_raw.get('metadata') and not version.get('metadata'), 'UNSUPPORTED_PRODUCT_METADATA')

        def composition(pack):
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
            return draws, total_cards

        candidates = {}
        if variant_model:
            variant_entries = sorted((v['pack_definition_id'], v['weight']) for v in pack['variants'])
            _require(0 < len(variant_entries) <= MAX_SLOTS
                     and len({v for v, _ in variant_entries}) == len(variant_entries),
                     'EMPTY_OVERSIZED_OR_DUPLICATE_VARIANTS')
            _require(all(type(w) is int and 0 < w <= MAX_INTEGER for _, w in variant_entries)
                     and sum(w for _, w in variant_entries) <= MAX_INTEGER, 'INVALID_VARIANT_WEIGHTS')
            aggregate_slots = aggregate_cards = aggregate_entries = 0
            for identifier, _ in variant_entries:
                child = record('pack_definition', identifier, 'pack-definition')
                _require(child['product_version_id'] == version_id, 'VARIANT_PRODUCT_VERSION_MISMATCH')
                _require(child.get('metadata') == {'simulation_model': FINISH_MODEL},
                         'VARIANT_REQUIRES_FINISH_AWARE_COMPOSITION')
                candidate = composition(child)
                candidates[identifier] = candidate
                aggregate_slots += len(candidate[0]); aggregate_cards += candidate[1]
                aggregate_entries += sum(len(d[3]) for d in candidate[0])
                _require(aggregate_slots <= MAX_SLOTS and aggregate_cards <= MAX_CARDS
                         and aggregate_entries <= MAX_POOL, 'VARIANT_AGGREGATE_BOUND_EXCEEDED')
        else:
            draws, total_cards = composition(pack)
        records = [records[key] for key in sorted(records)]
        inputs = dict(query_snapshot_id=snapshot.snapshot_id, records=records, sources=sources)
        input_id = _identity('pack-simulation-input-v0.2' if variant_model else
                             'pack-simulation-input-v0.1' if finish_aware else 'pack-simulation-input-v0', inputs)
        if not variant_model: candidates[pack_id] = (draws, total_cards)
        return dict(game=snapshot.game, query_snapshot_id=snapshot.snapshot_id, product_id=product_id,
                    version_id=version_id, pack_id=pack_id, model=model, report_version=report_version,
                    variant_model=variant_model, finish_aware=finish_aware, candidates=candidates,
                    variant_entries=variant_entries if variant_model else [], records=records,
                    sources=sources, input_id=input_id)

    def _generate(self, product_id, pack_id, seed, recorded_at):
        context = self._admit(product_id, pack_id)
        variant_model = context['variant_model']; finish_aware = context['finish_aware']
        variant_entries = context['variant_entries']; candidates = context['candidates']
        if not variant_model: draws, total_cards = candidates[pack_id]
        records = context['records']; sources = context['sources']; input_id = context['input_id']
        model = context['model']; report_version = context['report_version']; version_id = context['version_id']
        counter = 0; slots = []; variant_result = {}
        if variant_model:
            total_weight = sum(w for _, w in variant_entries)
            ticket, counter = _ticket(seed, counter, total_weight)
            identifier = _select(variant_entries, ticket)
            draws, total_cards = candidates[identifier]
            variant_result = dict(selected_variant_id=identifier,
                                  selected_variant_weight=dict(variant_entries)[identifier],
                                  variant_total_weight=total_weight)
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
                    game=context['game'], product_id=product_id, product_version_id=version_id,
                    pack_definition_id=pack_id, query_snapshot_id=context['query_snapshot_id'], input_id=input_id,
                    database_version=None, production_authorized=False,
                    scope='EXPLICIT_DEFINITION_MODEL_ONLY_NON_PRODUCTION', card_count=total_cards,
                    slots=slots, **variant_result, evidence_references=[dict(kind=r['kind'], id=r['id'],
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
    if report['schema_version'] == VARIANT_VERSION:
        lines += [VARIANT_VERSION + ': selected variant ' + report['selected_variant_id'] +
                  ' (weight ' + str(report['selected_variant_weight']) + '/' +
                  str(report['variant_total_weight']) + ')']
    if report['schema_version'] in (FINISH_VERSION, VARIANT_VERSION):
        lines += [report['schema_version'] + ': explicit Printing + Finish outcomes']
        lines += [s['slot_id'] + ': ' + ', '.join(
            o['printing_id'] + ' [' + o['finish_id'] + ']' for o in s['outcomes']) for s in report['slots']]
    else:
        lines += [s['slot_id'] + ': ' + ', '.join(s['printing_ids']) for s in report['slots']]
    lines += ['Input: ' + report['input_id'], 'No physical collation or production authority established.']
    return '\n'.join(lines) + '\n'
