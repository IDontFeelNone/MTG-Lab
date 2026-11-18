"""Read-only composition of audited holdings, native allocation and intended-deck access."""
from collections import Counter
import copy
from hashlib import sha256
import json
from pathlib import Path
import re

from probability.draw_access import canonical_json
from probability.supplied_deck import (SuppliedDeckError, assess_supplied_decks,
                                       validate_supplied_decks, render_supplied_decks)
from query import CanonicalQueryEngine
from .audit import CollectionAudit
from .intelligence import CanonicalCollectionResolver, compare_deck

INPUT_VERSION = 'collection-deck-analysis-input-v1'
REPORT_VERSION = 'collection-deck-analysis-report-v1'
MAX_INPUT_BYTES = 196608
MAX_REPORT_BYTES = 393216
MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024


class DeckAnalysisError(ValueError):
    def as_dict(self):
        return dict(schema_version=REPORT_VERSION, status='REFUSED', reason=str(self),
                    ownership_write=False, real_gameplay_authorized=False)


def _require(condition, reason):
    if not condition: raise DeckAnalysisError(reason)


def _fields(value, names):
    _require(type(value) is dict and value.keys() == set(names), 'closed input fields required')


def _text(value, maximum=128):
    _require(type(value) is str and 0 < len(value) <= maximum and value == value.strip()
             and value.isprintable(), 'invalid bounded identity')


def _id(version, value):
    return 'sha256:' + sha256(version.encode() + b'\0' + canonical_json(value).encode()).hexdigest()


def validate_collection_decks(request):
    _fields(request, ('schema_version', 'catalog', 'collection_binding', 'deck_analysis', 'requirements'))
    _require(type(request['schema_version']) is str and request['schema_version'] == INPUT_VERSION, 'unsupported input version')
    catalog = request['catalog']; _fields(catalog, ('game', 'snapshot_id'))
    _text(catalog['game']); _require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', catalog['game']) is not None, 'invalid game identity')
    _require(type(catalog['snapshot_id']) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',catalog['snapshot_id']) is not None, 'exact catalog identity required')
    binding = request['collection_binding']; _fields(binding, ('snapshot_id','snapshot_digest','source_import_digest'))
    _text(binding['snapshot_id'])
    for key in ('snapshot_digest','source_import_digest'):
        _require(type(binding[key]) is str and re.fullmatch(r'[0-9a-f]{64}',binding[key]) is not None, 'exact collection/source digest required')
    try: supplied = validate_supplied_decks(request['deck_analysis'])
    except SuppliedDeckError as error: raise DeckAnalysisError(str(error)) from None
    raw = request['requirements']; _require(type(raw) is list and len(raw) == len(supplied['decks']), 'one requirement set per configuration required')
    sets = {}
    for entry in raw:
        _fields(entry, ('deck_id','requirements')); _text(entry['deck_id'])
        _require(entry['deck_id'] not in sets, 'duplicate requirement deck identity')
        rows = entry['requirements']; _require(type(rows) is list and 1 <= len(rows) <= 512, 'bounded positive requirements required')
        ids=set(); normalized=[]
        for row in rows:
            _fields(row, ('requirement_id','card_id','section','quantity','policy','printing_id'))
            for field in ('requirement_id','card_id','section'): _text(row[field])
            _require(row['requirement_id'] not in ids, 'duplicate requirement identity'); ids.add(row['requirement_id'])
            _require(type(row['quantity']) is int and 1 <= row['quantity'] <= 120, 'positive integer requirement required')
            _require(type(row['policy']) is str and row['policy'] in ('any','exact'), 'unsupported Printing policy')
            if row['policy'] == 'exact': _text(row['printing_id'])
            else: _require(row['printing_id'] is None, 'flexible requirement must not claim an exact Printing')
            normalized.append(dict(row))
        sets[entry['deck_id']] = sorted(normalized, key=lambda r:r['requirement_id'])
    _require(set(sets) == {d['deck_id'] for d in supplied['decks']}, 'requirement/deck identities disagree')
    for deck in supplied['decks']:
        section=deck['draw_population']['section']
        expected={r['card_id']:r['quantity'] for r in deck['entries'] if r['section']==section and r['quantity']}
        actual=Counter()
        for row in sets[deck['deck_id']]:
            _require(row['section']==section, 'coverage must select the same explicit population')
            actual[row['card_id']] += row['quantity']
        _require(dict(actual)==expected, 'Printing requirements do not reconcile with intended Card quantities')
    result=dict(schema_version=INPUT_VERSION,catalog=dict(catalog),collection_binding=dict(binding),
                deck_analysis=supplied,requirements=[dict(deck_id=d['deck_id'],requirements=sets[d['deck_id']]) for d in supplied['decks']])
    _require(len(canonical_json(request).encode()) <= MAX_INPUT_BYTES and len(canonical_json(result).encode()) <= MAX_INPUT_BYTES, 'input byte budget exceeded')
    return result


def _decode(raw, maximum):
    _require(type(raw) in (str,bytes) and len(raw)<=maximum, 'bounded JSON required')
    try:
        data=raw.encode() if type(raw) is str else raw
        _require(len(data)<=maximum,'input byte budget exceeded')
        def unique(pairs):
            d={}
            for k,v in pairs:
                _require(k not in d,'duplicate JSON key');d[k]=v
            return d
        def nonfinite(_):raise DeckAnalysisError('nonfinite JSON number')
        value=json.loads(data.decode('utf-8'),object_pairs_hook=unique,parse_constant=nonfinite)
    except (UnicodeError,ValueError,RecursionError) as error:
        if isinstance(error,DeckAnalysisError):raise
        raise DeckAnalysisError('invalid bounded UTF-8 JSON') from None
    return value


def parse_collection_decks(raw):
    return validate_collection_decks(_decode(raw,MAX_INPUT_BYTES))


def analyze_collection_decks(request, *, snapshot, source_path, source_root, catalog_root):
    """All filesystem contexts are explicit; no default private inventory or catalog."""
    value=validate_collection_decks(request)
    consistency=assess_supplied_decks(value['deck_analysis'])
    _require(all(isinstance(p,(str,Path)) for p in (source_path,source_root,catalog_root)),
             'explicit source paths and catalog root required')
    _require(type(snapshot) is dict,'explicit snapshot document required')
    try:
        _require(len(canonical_json(snapshot).encode())<=MAX_SNAPSHOT_BYTES,'snapshot byte budget exceeded')
        snapshot=copy.deepcopy(snapshot)
    except (TypeError,ValueError,UnicodeError,RecursionError):
        raise DeckAnalysisError('invalid bounded snapshot document') from None
    bindings=dict(requested_catalog=value['catalog'],requested_collection=value['collection_binding'],
                  verified_catalog_id=None,verified_collection=None,audit_id=None)
    global_reasons=[]; audit=None; resolver=None; query=None
    game=value['catalog']['game']; root=Path(catalog_root)
    try:
        if not (root/'canonical/games'/game/'game.json').is_file():raise ValueError('missing game')
        query=CanonicalQueryEngine(game,data_root=root,games_root=root/'canonical/games')
        resolver=CanonicalCollectionResolver(game,root)
        if query.snapshot().snapshot_id!=resolver.canonical_snapshot_id or query.snapshot().snapshot_id!=value['catalog']['snapshot_id']:
            raise ValueError('catalog mismatch')
        bindings['verified_catalog_id']=query.snapshot().snapshot_id
    except (ValueError,OSError,KeyError,TypeError):global_reasons.append('CATALOG_UNAVAILABLE_OR_MISMATCHED')
    if not global_reasons:
        try:
            if any(snapshot.get(k)!=v for k,v in value['collection_binding'].items()):raise ValueError('binding mismatch')
            audit=CollectionAudit(resolver).build(snapshot,source_path=source_path,source_root=source_root,assessments=())
            bindings['verified_collection']=dict(value['collection_binding'])
            bindings['audit_id']=audit['audit_id']
            if audit['quantity_census']['conflicting_owned_lot_ids']:global_reasons.append('CONFLICTING_OWNERSHIP_LOTS')
        except (ValueError,OSError,KeyError,TypeError):global_reasons.append('COLLECTION_SOURCE_OR_SNAPSHOT_NOT_VERIFIED')
    def entity(kind,identifier):
        item=query.entity(identifier,entity_type=kind)
        if item.uncertainty!='known' or item.supersession_state!='current':raise ValueError('unestablished identity')
        return item
    if not global_reasons:
        try:
            for row in snapshot['resolved_holdings']:
                if not row['row'].get('printing_id') and not row['row'].get('external_identifiers'):
                    raise ValueError('name-only resolution is not an exact inventory identity')
                p=entity('printing',row['printing_id']);c=entity('card',row['card_id'])
                if p.canonical_values['card_id']!=c.canonical_identity:raise ValueError('join mismatch')
        except (ValueError,KeyError,TypeError):global_reasons.append('REPORTED_INVENTORY_IDENTITY_NOT_ESTABLISHED')
    coverages=[]
    for deck,reqset in zip(value['deck_analysis']['decks'],value['requirements']):
        reasons=list(global_reasons)
        if not reasons:
            try:
                for row in deck['entries']:
                    if row['section']==deck['draw_population']['section']:entity('card',row['card_id'])
                for row in reqset['requirements']:
                    if row['policy']=='exact':
                        printing=entity('printing',row['printing_id'])
                        if printing.canonical_values['card_id']!=row['card_id']:raise ValueError('foreign Printing')
            except (ValueError,KeyError,TypeError):reasons.append('DECK_CARD_OR_PRINTING_JOIN_NOT_ESTABLISHED')
        coverage=dict(deck_id=deck['deck_id'],status='WITHHELD' if reasons else 'REPORTED_SNAPSHOT_COVERAGE',
            reasons=reasons,identity_basis='UNESTABLISHED' if reasons else 'EXACT_SELECTED_CATALOG_JOIN',
            intended_quantity=deck['draw_population']['declared_size'],covered_quantity=None,
            uncovered_quantity=None,completion_percentage=None,requirements=[],
            unresolved_may_affect_coverage=(any(audit['quantity_census'][k] for k in
                ('ambiguous_reported_quantity','unresolved_reported_quantity','excluded_invalid_rows','excluded_conflicting_lot_rows'))
                if audit is not None else None))
        if not reasons:
            native=dict(schema_version='deck-requirement-v1',deck_id=deck['deck_id'],requirements=[
                dict(requirement_id=r['requirement_id'],card_id=r['card_id'],section=r['section'],quantity=r['quantity'],
                     acceptable_printing_policy=r['policy'],**({'printing_id':r['printing_id']} if r['policy']=='exact' else {}))
                for r in reqset['requirements']])
            allocated=compare_deck(snapshot,native,resolver,include_allocations=True)
            coverage.update(covered_quantity=sum(r['allocated_quantity'] for r in allocated['allocation_trace']),
                uncovered_quantity=sum(r['uncovered_quantity'] for r in allocated['allocation_trace']),
                completion_percentage=allocated['completion_percentage'],requirements=allocated['allocation_trace'])
        coverages.append(coverage)
    # Recheck owning source and catalog boundaries before returning any confident coverage.
    if any(c['status']=='REPORTED_SNAPSHOT_COVERAGE' for c in coverages):
        try:
            fresh=CanonicalQueryEngine(game,data_root=root,games_root=root/'canonical/games')
            if fresh.snapshot().snapshot_id!=value['catalog']['snapshot_id']:raise ValueError('catalog drift')
            CollectionAudit(resolver).verify_source_snapshot(snapshot,source_path=source_path,source_root=source_root)
        except (ValueError,OSError,KeyError,TypeError):
            bindings['verified_catalog_id']=None;bindings['verified_collection']=None;bindings['audit_id']=None
            audit=None
            for c in coverages:
                c.update(status='WITHHELD',reasons=['INPUT_DRIFT_DURING_ANALYSIS'],identity_basis='UNESTABLISHED',
                         covered_quantity=None,uncovered_quantity=None,completion_percentage=None,requirements=[],
                         unresolved_may_affect_coverage=None)
    uncertainty=dict(scope_complete=None,physical_ownership_independently_verified=False,
        unresolved_rows=None,ambiguous_rows=None,excluded_duplicate_rows=None,invalid_rows=None,conflicting_lot_rows=None)
    if audit is not None:
        statuses=audit['identity_census']['row_status_counts'];census=audit['quantity_census']
        uncertainty.update(unresolved_rows=statuses.get('unresolved',0),ambiguous_rows=statuses.get('ambiguous',0),
            excluded_duplicate_rows=census['excluded_duplicate_input_rows'],invalid_rows=census['excluded_invalid_rows'],
            conflicting_lot_rows=census['excluded_conflicting_lot_rows'])
    report=dict(schema_version=REPORT_VERSION,status='ASSESSED',input_id=_id(INPUT_VERSION,value),bindings=bindings,
        consistency=consistency,coverage=coverages,uncertainty=uncertainty,
        allocation_scope='INDEPENDENT_ALTERNATIVES_NO_RESERVATION',ownership_write=False,real_gameplay_authorized=False,
        limitations=[
            'Coverage describes resolved reported holdings in the selected snapshot, not independently verified complete physical ownership.',
            'Uncovered quantities are shortages against that snapshot; unresolved evidence can change them.',
            'Probabilities describe the intended deck even when coverage is withheld or cards are uncovered.',
            'Alternatives reuse the same immutable snapshot independently; their allocations must not be summed or treated as simultaneous reservations.',
            'Printing-ID allocation does not establish finish-specific suitability, strategic strength, legality, casting or win rates.',
            'No private paths, raw sources, unrelated holdings, acquisition notes, AI export, ingestion or new authority are provided.'])
    report['report_id']=_id(REPORT_VERSION,report)
    _require(len(canonical_json(report).encode())+1<=MAX_REPORT_BYTES,'report byte budget exceeded')
    return report


def render_collection_decks(report, *, readable=False):
    if not readable:return canonical_json(report)+'\n'
    if report['status']=='REFUSED':return 'REFUSED: '+report['reason']+'\n'
    lines=['Collection-to-deck analysis: reported snapshot coverage; no physical reservations']
    for c in report['coverage']:
        lines.append(c['deck_id']+': '+c['status'])
        if c['status']=='WITHHELD':lines.extend(c['reasons']);continue
        lines.append(str(c['covered_quantity'])+' covered by reported holdings; '+str(c['uncovered_quantity'])+' uncovered in selected snapshot')
        for r in c['requirements']:
            uses=', '.join(p['printing_id']+' x'+str(p['quantity']) for p in r['printings']) or 'none'
            lines.append(r['requirement_id']+' ('+r['policy']+'): '+uses+'; uncovered '+str(r['uncovered_quantity']))
    lines.append(render_supplied_decks(report['consistency'],readable=True).rstrip())
    lines.append('Uncertainty: '+canonical_json(report['uncertainty']));lines.extend(report['limitations'])
    return '\n'.join(lines)+'\n'


def run_cli(args):
    try:
        with args.input.open('rb') as f:raw=f.read(MAX_INPUT_BYTES+1)
        value=parse_collection_decks(raw)
        with args.snapshot.open('rb') as f:raw_snapshot=f.read(MAX_SNAPSHOT_BYTES+1)
        _require(len(raw_snapshot)<=MAX_SNAPSHOT_BYTES,'snapshot byte budget exceeded')
        snapshot=_decode(raw_snapshot,MAX_SNAPSHOT_BYTES)
        report=analyze_collection_decks(value,snapshot=snapshot,source_path=args.source,
            source_root=args.source_root,catalog_root=args.catalog_root)
    except (ValueError,OSError,UnicodeError,RecursionError):
        report=DeckAnalysisError('analysis request or explicit input unavailable/invalid').as_dict()
    print(render_collection_decks(report,readable=args.format=='text'),end='')
    return 2 if report['status']=='REFUSED' else 0
