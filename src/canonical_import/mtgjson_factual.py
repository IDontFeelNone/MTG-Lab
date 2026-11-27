"""Derivative-only factual admission preparation. No provider parser or acquisition.

The existing publication verifier owns input integrity; existing promotion and
projection own canonical construction. This adapter owns the field mapping and
dependency-aware crosswalk. Its disk index is disposable, never canonical data.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid

from dataset_import.framework import EntityResolver
from providers.mtgjson.factual_retention import verify_factual_publication
from providers.mtgjson.private_policy import PrivateResearchProfile, RETENTION, IDENTIFIERS
from providers.mtgjson.reconciliation import _disk, ReconciliationLimits
from query import CanonicalQueryEngine
from query.engine import normalize_name
from validation import validate_document

VERSION = 'private-factual-admission-v1'
POLICY = 'normal-layout-factual-mapping-v1'
MAX_ROWS = 1_000_000
MAX_ROW_BYTES = 64 * 1024
MAX_DISK_BYTES = 2 * 1024**3
MAX_COHORT_PRINTINGS = 25  # Existing bounded population-review envelope.
MAX_MANIFEST_BYTES = 2 * 1024**2
CARD_FIELDS = {'name':'name', 'layout':'layout', 'colors':'colors',
    'colorIdentity':'color_identity', 'manaCost':'mana_cost', 'manaValue':'mana_value',
    'type':'type_line', 'power':'power', 'toughness':'toughness', 'loyalty':'loyalty'}
PRINT_FIELDS = ('uuid','card_reference','set_code','collector_number','language','rarity','finishes','identifiers')
_SEAL = object()
_ID = re.compile(r'[a-z0-9][a-z0-9._-]*')
_SHA = re.compile(r'[0-9a-f]{64}')


class FactualAdmissionError(ValueError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)


def require(value, reason, code='INVALID_INPUT'):
    if not value:
        raise FactualAdmissionError(code, reason)


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def identity(value):
    return 'sha256:' + hashlib.sha256(stable(value).encode()).hexdigest()


def file_hash(path):
    checksum=hashlib.sha256();total=0
    with Path(path).open('rb') as stream:
        while block:=stream.read(65536):
            total+=len(block)
            require(total<=MAX_DISK_BYTES,'integrity input exceeds supported bound','RESOURCE_BUDGET')
            checksum.update(block)
    return checksum.hexdigest()


def private_root(path, *, create=False):
    root = Path(path).absolute()
    require(not any(p.is_symlink() for p in (root,*root.parents)), 'symlink private path refused')
    require(not any((p/'.git').is_file() or (p/'.git/HEAD').is_file() for p in (root,*root.parents)),
            'private factual storage must remain outside Git', 'PRIVATE_BOUNDARY')
    if create:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(root.is_dir() and root.stat().st_mode & 0o077 == 0, 'owner-only private directory required')
    require(not any(p.is_symlink() for p in root.rglob('*')), 'symlink private content refused')
    return root


def write_once(path, value):
    raw = (stable(value)+'\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor,'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def engine_binding():
    root = Path(__file__).parents[1]
    names = ('canonical_import/mtgjson_factual.py','repository/factual_snapshot.py',
             'acquisition/promotion.py','projection/engine.py','repository/canonical.py',
             'query/engine.py','card_intelligence/mechanics.py',
             'providers/mtgjson/private_policy.py','providers/mtgjson/factual_retention.py',
             'schemas/v3/card.schema.json','schemas/v3/printing.schema.json',
             'schemas/v1/private-factual-canonical-snapshot.schema.json')
    return {name:file_hash(root/name) for name in names}


def _json(raw):
    def pairs(items):
        out = {}
        for key,value in items:
            require(key not in out, 'duplicate evidence key')
            out[key] = value
        return out
    try:
        return json.loads(raw, object_pairs_hook=pairs,
            parse_constant=lambda _: require(False,'nonfinite evidence value'))
    except (ValueError, TypeError, RecursionError):
        raise FactualAdmissionError('INVALID_INPUT','invalid bounded factual evidence') from None


def _uuid(value):
    try:
        return type(value) is str and str(uuid.UUID(value)) == value.casefold()
    except (ValueError, AttributeError):
        return False


def _known(value):
    if isinstance(value,dict) and 'status' in value:
        if value['status']=='known':return value.get('value')
        return {'status':'known_absent'} if value['status']=='known_absent' else None
    return value


def _prestate_fields(values):
    """Reuse the existing top-level assertion-path projection convention.

    Promoted values may use /name while typed/legacy records use name. Unknowns
    cannot contradict known facts, but incompatible known representations refuse.
    This is a view of existing facts, not a new interpretation or identity rule.
    """
    fields={key:_known(value) for key,value in values.get('facts',{}).items()}
    for key,value in values.items():
        if key in ('facts','metadata','assertions'):continue
        field=key[1:] if key.startswith('/') and '/' not in key[1:] else key
        value=_known(value)
        if field in fields and fields[field] is not None:
            require(value is None or fields[field]==value,
                'conflicting canonical field representations','INVALID_PRESTATE')
        else:fields[field]=value
    return fields


def current_query(query):
    require(type(query) is CanonicalQueryEngine, 'existing canonical query required')
    query.snapshot()  # Verifies an attached reader before reading roots again.
    if query._catalog_attachment is not None:
        return CanonicalQueryEngine.from_attachment(query._catalog_attachment)
    return CanonicalQueryEngine(query.game,games_root=query.games_root,data_root=query.data_root)


def _publication(directory, profile, report_id, publication_id):
    require(type(profile) is PrivateResearchProfile and profile.retention_profile == RETENTION
            and profile.retention_mode == 'limited-retention', 'original factual limited profile required',
            'SOURCE_POLICY_REFUSAL')
    profile.require_supported()
    try:
        receipt = verify_factual_publication(directory,profile=profile,expected_report_id=report_id)
        require(receipt['publication_id']==publication_id,'independent publication identity mismatch','INTEGRITY_MISMATCH')
        report = _json((Path(directory)/'output/report.json').read_bytes())
        require(report.get('report_id')==report_id==identity({k:v for k,v in report.items() if k!='report_id'}),
                'factual report changed during verification','INTEGRITY_MISMATCH')
    except FactualAdmissionError:
        raise
    except (ValueError,OSError,KeyError,TypeError):
        raise FactualAdmissionError('INTEGRITY_MISMATCH','factual publication verification refused') from None
    require(report['total_source_rows']<=MAX_ROWS,'publication row budget exceeded','RESOURCE_BUDGET')
    return report,receipt


def _baseline(db, query):
    for result in query.snapshot().entities:
        kind=result.entity_type
        if kind not in ('card','printing'):
            continue
        values=deepcopy(dict(result.canonical_values));fields=_prestate_fields(values)
        try:
            raw=query.retained_record(result.canonical_identity,entity_type=kind)
        except ValueError:
            raw={}
        aliases=[]
        if _uuid(result.canonical_identity):
            aliases.append(('oracle' if kind=='card' else 'uuid',result.canonical_identity))
        if kind=='card':
            for key in ('card_reference','oracle_id'):
                if _uuid(fields.get(key) or raw.get(key)):
                    aliases.append(('oracle',fields.get(key) or raw.get(key)))
        elif _uuid(fields.get('uuid')):
            aliases.append(('uuid',fields['uuid']))
        containers=[fields.get('external_identifiers'),fields.get('identifiers'),raw.get('external_identifiers')]
        for ids in containers:
            if isinstance(ids,dict):
                for namespace,value in ids.items():
                    if namespace in ('scryfallOracleId','oracleId') and kind=='card':
                        aliases.append(('oracle',value))
                    elif namespace=='scryfallId' and kind=='printing':
                        aliases.append(('scryfallId',value))
        db.execute('INSERT INTO baseline VALUES(?,?,?,?)',(kind,result.canonical_identity,
            normalize_name(str(fields.get('name',''))),stable(fields)))
        for namespace,value in aliases:
            if type(value) is str:
                db.execute('INSERT INTO aliases VALUES(?,?,?,?)',(kind,namespace,value.casefold(),result.canonical_identity))
    # A reviewed private factual snapshot retains crosswalk aliases separately
    # from typed Card facts. Preserve them when it is selected as a later base.
    from repository.factual_snapshot import FactualSnapshotAttachment
    if type(query._catalog_attachment) is FactualSnapshotAttachment:
        crosswalk=query._catalog_attachment.read_json(query._catalog_attachment.root/'cohort.json')['crosswalk']
        for item in crosswalk:
            kind=item['entity_type']
            require(db.execute('SELECT 1 FROM baseline WHERE kind=? AND id=?',(kind,item['canonical_identity'])).fetchone(),
                'retained crosswalk target is not in the selected base','INTEGRITY_MISMATCH')
            db.execute('INSERT INTO aliases VALUES(?,?,?,?)',(kind,'oracle' if kind=='card' else 'uuid',
                item['source_identity'],item['canonical_identity']))
    # Promoted identifier entities are a separate historical representation.
    # Never ignore them merely because a Printing lacks inline identifiers.
    for result in query.snapshot().entities:
        if result.entity_type!='identifier':continue
        fields=_prestate_fields(dict(result.canonical_values))
        namespace=fields.get('namespace',fields.get('scheme'))
        value=fields.get('value');target=fields.get('printing_uuid')
        if namespace not in ('scryfallId','scryfallOracleId','oracleId') or type(value) is not str:continue
        targets={x[0] for x in db.execute("SELECT id FROM baseline WHERE kind='printing' AND id=?",(target,))}
        targets.update(x[0] for x in db.execute("SELECT id FROM aliases WHERE kind='printing' AND namespace='uuid' AND value=?",(str(target).casefold(),)))
        kind='printing' if namespace=='scryfallId' else 'card'
        namespace='scryfallId' if kind=='printing' else 'oracle'
        if not targets:
            db.execute('INSERT INTO blocked_aliases VALUES(?,?,?)',(kind,namespace,value.casefold()))
        for printing in targets:
            canonical=printing
            if kind=='card':
                prior=json.loads(db.execute("SELECT fields FROM baseline WHERE kind='printing' AND id=?",(printing,)).fetchone()[0])
                canonical=prior.get('card_id',prior.get('card_reference'))
            if canonical:
                db.execute('INSERT INTO aliases VALUES(?,?,?,?)',(kind,namespace,value.casefold(),canonical))


def _resolve(db, kind, key, row, parent=None):
    if kind=='printing' and row['mapped_printing'] is None:
        return key,['MISSING_PRINTING_IDENTITY_EVIDENCE']
    claims=[('oracle' if kind=='card' else 'uuid',key)]
    if kind=='printing' and row['identifiers'].get('scryfallId'):
        claims.append(('scryfallId',row['identifiers']['scryfallId']))
    matches=set()
    for namespace,value in claims:
        if db.execute('SELECT 1 FROM blocked_aliases WHERE kind=? AND namespace=? AND value=?',
                (kind,namespace,value.casefold())).fetchone():
            return key,['CANONICAL_ALIAS_TARGET_UNRESOLVED']
        matches.update(x[0] for x in db.execute('SELECT id FROM aliases WHERE kind=? AND namespace=? AND value=?',
            (kind,namespace,value.casefold())))
    if len(matches)>1:
        return key,['AMBIGUOUS_CANONICAL_IDENTITY']
    if not matches:
        if kind=='card' and db.execute('SELECT 1 FROM baseline WHERE kind=? AND name=?',
                (kind,normalize_name(row['assertions'].get('name','')))).fetchone():
            return key,['NAME_ONLY_MATCH_REQUIRES_REVIEW']
        if db.execute('SELECT 1 FROM baseline WHERE kind=? AND id=?',(kind,key)).fetchone():
            return key,['UNBOUND_IDENTITY_COLLISION']
        return key,[]  # Existing Card-reference / Printing-UUID identity rule.
    selected=next(iter(matches))
    prior=json.loads(db.execute('SELECT fields FROM baseline WHERE kind=? AND id=?',(kind,selected)).fetchone()[0])
    reasons=[]
    if kind=='card':
        for source,target in CARD_FIELDS.items():
            value=prior.get(target)
            if value is not None and source in row['assertions'] and value!=row['assertions'][source]:
                reasons.append('CANONICAL_FACT_CONFLICT')
        # An alias alone does not establish a match: corroborate name and layout.
        if prior.get('name')!=row['assertions'].get('name') or prior.get('layout','normal')!='normal':
            reasons.append('CANONICAL_IDENTITY_CORROBORATION_MISSING')
    else:
        fields=row['mapped_printing']['mapped_fields']
        language={'English':'en','Japanese':'ja'}.get(fields['language'],fields['language'])
        for target,value in [('card_id',parent),('set_id',fields['set_code'].casefold()),
                             ('collector_number',fields['collector_number']),('language',language)]:
            if prior.get(target)!=value:
                reasons.append('CANONICAL_PRINTING_CONFLICT')
        for target,source in [('rarity','rarity'),('finishes','finishes'),('finish_ids','finishes')]:
            if prior.get(target) is not None and prior[target]!=fields[source]:
                reasons.append('CANONICAL_PRINTING_FACT_CONFLICT')
        for identifiers in (prior.get('external_identifiers'),prior.get('identifiers')):
            if isinstance(identifiers,dict) and any(key in row['identifiers']
                    and row['identifiers'][key].casefold()!=str(value).casefold()
                    for key,value in identifiers.items()):
                reasons.append('CANONICAL_PRINTING_IDENTIFIER_CONFLICT')
    return selected,sorted(set(reasons))


def _validate_row(row):
    keys={'partition','row','source_record_sha256','status','card_id','printing_id','facet','assertions',
        'identifiers','exceptional','relationships','mapped_card','mapped_printing','reason',
        'retention_profile','omitted_field_count'}
    require(type(row) is dict and set(row)==keys,'unsupported factual occurrence envelope')
    require(row['retention_profile']==RETENTION and type(row['assertions']) is dict
        and set(row['assertions'])<=set(CARD_FIELDS)|{'defense'},'unsupported source assertions','UNSUPPORTED_FIELD')
    require(type(row['partition']) is int and row['partition']>=0 and type(row['row']) is int and row['row']>=0
        and type(row['source_record_sha256']) is str and _SHA.fullmatch(row['source_record_sha256']),
        'invalid source occurrence binding')
    require(type(row['identifiers']) is dict and set(row['identifiers'])<=IDENTIFIERS
        and all(type(v) is str and 0<len(v)<=256 for v in row['identifiers'].values()),'unsupported source identifiers')
    require(type(row['exceptional']) is bool and type(row['relationships']) is list
        and len(row['relationships'])<=128 and all(type(v) is str and len(v)<=256 for v in row['relationships']),
        'invalid relationship evidence')
    require(type(row['facet']) is str and len(row['facet'])<=4096,'invalid face boundary')
    for kind,allowed in [('mapped_card',{'name','normalized_name','card_reference','layout','colors','mana_cost'}),
                          ('mapped_printing',set(PRINT_FIELDS))]:
        mapped=row[kind]
        if mapped is not None:
            require(type(mapped) is dict and set(mapped)=={'candidate_identifier','entity_type','mapped_fields','unknown_fields'}
                and mapped['unknown_fields']=={} and type(mapped['mapped_fields']) is dict
                and set(mapped['mapped_fields'])==allowed,'unsupported mapped factual fields')


def _documents(row, card_id, printing_id):
    fields=row['assertions']
    require(all(k in fields for k in ('name','layout','colors','colorIdentity','manaValue','type')),
        'required Card factual evidence missing','MISSING_FACT')
    require(fields['layout']=='normal' and not row['exceptional'] and not row['relationships'] and not row['facet'],
        'exceptional evidence requires specialized review','EXCEPTIONAL_REVIEW_REQUIRED')
    require('defense' not in fields,'defense is outside V1 admission','UNSUPPORTED_FIELD')
    for source,value in fields.items():
        expected=(list if source in ('colors','colorIdentity') else (int,float) if source=='manaValue' else str)
        require(type(value) in expected if isinstance(expected,tuple) else type(value) is expected,
            'literal publisher factual value required','UNSUPPORTED_SOURCE_VALUE')
    card={target:deepcopy(fields[source]) for source,target in CARD_FIELDS.items() if source in fields}
    require(type(card['name']) is str,'literal Card name required')
    card.update(id=card_id,game='magic',normalized_name=normalize_name(card['name']),schema_version='v3',assertions=[])
    # Empty cost is not evidence of absence. Leave it unknown, without a value.
    if card.get('mana_cost')=='':
        card['mana_cost']={'status':'unknown'}
    raw=row['mapped_printing']['mapped_fields']
    require(type(raw.get('finishes')) is list and bool(raw['finishes'])
        and all(type(x) is str and x for x in raw['finishes']),
        'supported literal finish availability required','MISSING_FACT')
    language={'English':'en','Japanese':'ja'}.get(raw['language'],raw['language'])
    printing=dict(schema_version='v3',id=printing_id,card_id=card_id,set_id=raw['set_code'].casefold(),
        collector_number=raw['collector_number'],language=language,assertions=[],
        rarity=deepcopy(raw['rarity']),finishes=deepcopy(raw['finishes']),external_identifiers=deepcopy(row['identifiers']))
    if isinstance(printing['rarity'],dict):printing.pop('rarity')
    for kind,doc in [('card',card),('printing',printing)]:
        try:validate_document(doc,kind,'v3')
        except ValueError:
            raise FactualAdmissionError('UNSUPPORTED_FACT','factual value does not fit the existing canonical contract') from None
    return card,printing


@dataclass(frozen=True)
class FactualAssessment:
    root: Path
    _body: str
    _index_sha256: str
    _profile: PrivateResearchProfile
    _publication: Path
    _query: CanonicalQueryEngine
    _seal: object

    @property
    def report(self):
        return json.loads(self._body)

    def verify(self):
        require(self._seal is _SEAL,'live assessment required','UNTRUSTED_INPUT')
        private_root(self.root)
        require(file_hash(self.root/'index.sqlite3')==self._index_sha256,'eligibility index changed','INTEGRITY_MISMATCH')
        report=self.report
        require(report['implementation']==engine_binding(),'assessment engine changed','INCOMPATIBLE_ENGINE')
        require(current_query(self._query).snapshot().snapshot_id==report['canonical_pre_state'],
                'canonical pre-state changed','STALE_PRESTATE')
        _publication(self._publication,self._profile,report['source']['report_id'],report['source']['publication_id'])


def assess_factual_publication(publication, *, profile, expected_report_id, expected_publication_id,
                               canonical_query, workspace):
    """Assess every supported occurrence; never read the original source archive."""
    native,receipt=_publication(publication,profile,expected_report_id,expected_publication_id)
    query=current_query(canonical_query)
    require(query.game=='magic','Magic factual catalog required')
    prestate=query.snapshot().snapshot_id
    root=private_root(workspace,create=True)
    require(not list(root.iterdir()),'dedicated empty assessment workspace required')
    path=root/'index.sqlite3'
    previous_temporary=os.environ.get('SQLITE_TMPDIR')
    os.environ['SQLITE_TMPDIR']=str(root)
    db=sqlite3.connect(path)
    try:
        db.executescript('''PRAGMA temp_store=FILE; PRAGMA cache_size=-8192;
          CREATE TABLE baseline(kind TEXT,id TEXT,name TEXT,fields TEXT,PRIMARY KEY(kind,id));
          CREATE TABLE aliases(kind TEXT,namespace TEXT,value TEXT,id TEXT);
          CREATE INDEX alias_idx ON aliases(kind,namespace,value);
          CREATE INDEX baseline_names ON baseline(kind,name);
          CREATE TABLE blocked_aliases(kind TEXT,namespace TEXT,value TEXT);
          CREATE TABLE rows(p INTEGER,n INTEGER,ck TEXT,pk TEXT,facet TEXT,alias TEXT,coord TEXT,name TEXT,payload TEXT,PRIMARY KEY(p,n));
          CREATE INDEX row_card ON rows(ck); CREATE INDEX row_print ON rows(pk);
          CREATE INDEX row_alias ON rows(alias); CREATE INDEX row_coord ON rows(coord); CREATE INDEX row_name ON rows(name);
          CREATE TABLE assertions(ck TEXT,facet TEXT,field TEXT,value TEXT);
          CREATE INDEX assertion_idx ON assertions(ck,facet,field,value);
          CREATE TABLE cards(ck TEXT PRIMARY KEY,id TEXT,reasons TEXT);
          CREATE TABLE printings(pk TEXT PRIMARY KEY,id TEXT,ck TEXT,reasons TEXT);
        ''')
        db.execute('PRAGMA max_page_count='+str(MAX_DISK_BYTES//4096))
        db.set_progress_handler(lambda: (_disk(root,ReconciliationLimits()),0)[1],10000)
        _baseline(db,query)
        count=0;source_checksum=hashlib.sha256();source_bytes=0
        with (Path(publication)/'output/assertions.jsonl').open('rb') as stream:
            while line:=stream.readline(MAX_ROW_BYTES+1):
                require(len(line)<=MAX_ROW_BYTES and line.endswith(b'\n'),'factual row exceeds bound','RESOURCE_BUDGET')
                source_checksum.update(line);source_bytes+=len(line)
                row=_json(line);_validate_row(row);count+=1
                require(count<=MAX_ROWS,'factual occurrence budget exceeded','RESOURCE_BUDGET')
                ck=row['card_id'] if _uuid(row['card_id']) else f'missing-{row["partition"]}-{row["row"]}'
                pk=row['printing_id'] if _uuid(row['printing_id']) else f'missing-{row["partition"]}-{row["row"]}'
                raw=row['mapped_printing']['mapped_fields'] if row['mapped_printing'] else {}
                coord=stable([raw.get(k) for k in ('set_code','collector_number','language')])
                name=row['assertions'].get('name')
                db.execute('INSERT INTO rows VALUES(?,?,?,?,?,?,?,?,?)',(row['partition'],row['row'],ck,pk,
                    row['facet'],row['identifiers'].get('scryfallId','').casefold(),coord,
                    normalize_name(name) if type(name) is str else '',stable(row)))
                db.executemany('INSERT INTO assertions VALUES(?,?,?,?)',[(ck,row['facet'],k,stable(v)) for k,v in row['assertions'].items()])
        require(count==native['total_source_rows'],'publication occurrence count mismatch','INTEGRITY_MISMATCH')
        require(dict(rows=count,bytes=source_bytes,sha256=source_checksum.hexdigest())==native['artifacts']['assertions.jsonl'],
                'factual occurrence artifact changed during parsing','INTEGRITY_MISMATCH')
        for part in native['partition_inventory']:
            found=db.execute('SELECT count(*),min(n),max(n) FROM rows WHERE p=?',(part['ordinal'],)).fetchone()
            require(found[0]==part['rows'] and (found[0]==0 or found[1:]==(0,found[0]-1)),
                    'partition accounting mismatch','INTEGRITY_MISMATCH')
        require(db.execute('SELECT count(DISTINCT p) FROM rows').fetchone()[0]==len([p for p in native['partition_inventory'] if p['rows']]),
                'unaccounted partition','INTEGRITY_MISMATCH')
        db.executescript('''CREATE TABLE card_conflicts AS SELECT ck FROM assertions GROUP BY ck,facet,field HAVING count(DISTINCT value)>1;
          CREATE TABLE name_conflicts AS SELECT name FROM rows WHERE name!='' GROUP BY name HAVING count(DISTINCT ck)>1;
          CREATE TABLE alias_conflicts AS SELECT alias FROM rows WHERE alias!='' GROUP BY alias HAVING count(DISTINCT pk)>1;
          CREATE TABLE coordinate_conflicts AS SELECT coord FROM rows GROUP BY coord HAVING count(DISTINCT pk)>1;
          CREATE TABLE duplicate_printings AS SELECT pk FROM rows GROUP BY pk HAVING count(*)>1;''')
        for (ck,) in db.execute('SELECT DISTINCT ck FROM rows ORDER BY ck'):
            first=json.loads(db.execute('SELECT payload FROM rows WHERE ck=? ORDER BY p,n LIMIT 1',(ck,)).fetchone()[0])
            reasons=[]
            if not _uuid(first['card_id']):reasons.append('UNRESOLVED_CARD_IDENTITY')
            if db.execute('SELECT 1 FROM card_conflicts WHERE ck=?',(ck,)).fetchone():reasons.append('CONFLICTING_CARD_FIELD')
            for (payload,) in db.execute('SELECT payload FROM rows WHERE ck=?',(ck,)):
                row=json.loads(payload)
                if set(row['assertions'])!=set(first['assertions']):
                    reasons.append('INCONSISTENT_CARD_FIELD_COVERAGE')
                if row['status']!='SUPPORTED':reasons.append('UNSUPPORTED_SOURCE_RECORD')
                if row['exceptional'] or row['relationships'] or row['facet'] or row['assertions'].get('layout')!='normal':
                    reasons.append('EXCEPTIONAL_REVIEW_REQUIRED')
            if db.execute('SELECT 1 FROM rows r JOIN alias_conflicts a ON r.alias=a.alias WHERE r.ck=?',(ck,)).fetchone():
                reasons.append('STRICT_ALIAS_COLLISION')
            cid,identity_reasons=_resolve(db,'card',ck,first);reasons+=identity_reasons
            if (not db.execute("SELECT 1 FROM baseline WHERE kind='card' AND id=?",(cid,)).fetchone()
                    and db.execute('SELECT 1 FROM rows r JOIN name_conflicts c ON r.name=c.name WHERE r.ck=?',(ck,)).fetchone()):
                reasons.append('AMBIGUOUS_NEW_CARD_NAME')
            try:
                _documents(first,cid,first['printing_id'])
            except FactualAdmissionError as error:reasons.append(error.code)
            except (TypeError,KeyError):reasons.append('MISSING_FACT')
            db.execute('INSERT INTO cards VALUES(?,?,?)',(ck,cid,stable(sorted(set(reasons)))))
        for pk,ck,payload,coord,alias in db.execute('SELECT pk,ck,payload,coord,alias FROM rows GROUP BY pk ORDER BY pk'):
            row=json.loads(payload);card_id,card_reasons=db.execute('SELECT id,reasons FROM cards WHERE ck=?',(ck,)).fetchone()
            reasons=[]
            if card_reasons!='[]':reasons.append('CARD_DEPENDENCY_UNRESOLVED')
            if not _uuid(row['printing_id']):reasons.append('UNRESOLVED_PRINTING_IDENTITY')
            if db.execute('SELECT 1 FROM duplicate_printings WHERE pk=?',(pk,)).fetchone():reasons.append('DUPLICATE_PRINTING')
            if db.execute('SELECT 1 FROM coordinate_conflicts WHERE coord=?',(coord,)).fetchone():reasons.append('COLLECTOR_COORDINATE_COLLISION')
            pid,identity_reasons=_resolve(db,'printing',pk,row,card_id);reasons+=identity_reasons
            try:_documents(row,card_id,pid)
            except FactualAdmissionError as error:reasons.append(error.code)
            except (TypeError,KeyError):reasons.append('MISSING_FACT')
            db.execute('INSERT INTO printings VALUES(?,?,?,?)',(pk,pid,ck,stable(sorted(set(reasons)))))
        # Two distinct provider groups cannot converge silently on one canonical ID.
        for table,key in [('cards','ck'),('printings','pk')]:
            for (cid,) in db.execute(f'SELECT id FROM {table} GROUP BY id HAVING count(*)>1'):
                for k,reasons in db.execute(f'SELECT {key},reasons FROM {table} WHERE id=?',(cid,)):
                    db.execute(f'UPDATE {table} SET reasons=? WHERE {key}=?',(stable(sorted(set(json.loads(reasons)+['CANONICAL_ID_COLLISION']))),k))
        for (ck,) in db.execute("SELECT DISTINCT r.ck FROM rows r JOIN printings p ON r.pk=p.pk WHERE p.reasons!='[]'"):
            reasons=json.loads(db.execute('SELECT reasons FROM cards WHERE ck=?',(ck,)).fetchone()[0])
            db.execute('UPDATE cards SET reasons=? WHERE ck=?',
                (stable(sorted(set(reasons+['PRINTING_GROUP_DEPENDENCY_UNRESOLVED']))),ck))
        db.execute("UPDATE printings SET reasons='[\"CARD_DEPENDENCY_UNRESOLVED\"]' WHERE ck IN (SELECT ck FROM cards WHERE reasons!='[]') AND reasons='[]'")
        db.commit()
        inventory={};counts={}
        for table,key,kind in [('cards','ck','card'),('printings','pk','printing')]:
            checksum=hashlib.sha256();n=0;statuses=Counter()
            name=kind+'-eligibility.jsonl'
            with (root/name).open('xb') as out:
                for record in db.execute(f'SELECT {key},id,reasons FROM {table} ORDER BY {key}'):
                    original,cid,reasons=record;reasons=json.loads(reasons)
                    row=dict(source_identity=original,canonical_identity=cid,entity_type=kind,
                        disposition='ELIGIBLE' if not reasons else 'QUARANTINED',reasons=reasons,
                        evidence_reference=dict(artifact='assertions.jsonl',source_identity=original,
                            publication_id=expected_publication_id))
                    if kind=='printing':row['parent_source_card']=db.execute('SELECT ck FROM printings WHERE pk=?',(original,)).fetchone()[0]
                    else:row['dependency_scope']='ALL_ASSOCIATED_PRINTINGS'
                    raw=(stable(row)+'\n').encode();out.write(raw);checksum.update(raw);n+=1;statuses[row['disposition']]+=1
            inventory[name]=dict(rows=n,sha256=checksum.hexdigest(),bytes=(root/name).stat().st_size)
            counts[kind]=dict(statuses)
        report=dict(schema_version=VERSION,policy=POLICY,source=dict(report_id=expected_report_id,
            publication_id=expected_publication_id,profile_id=profile.receipt()['profile_id'],
            release=json.loads(profile.release_json),artifacts=native['artifacts']),canonical_pre_state=prestate,
            implementation=engine_binding(),population=count,partition_inventory=native['partition_inventory'],
            counts=counts,artifacts=inventory,canonical_admission='NOT_PERFORMED',catalog_completeness='NOT_ESTABLISHED')
        report['assessment_id']=identity(report)
        require(current_query(canonical_query).snapshot().snapshot_id==prestate,'canonical pre-state changed','STALE_PRESTATE')
        write_once(root/'assessment.json',report)
    except (sqlite3.Error,OSError):
        raise FactualAdmissionError('RESOURCE_OR_INTEGRITY_REFUSAL','bounded eligibility storage refused; preserve workspace') from None
    finally:
        db.close()
        if previous_temporary is None:os.environ.pop('SQLITE_TMPDIR',None)
        else:os.environ['SQLITE_TMPDIR']=previous_temporary
    require(sum(p.stat().st_size for p in root.iterdir())<=MAX_DISK_BYTES,'eligibility disk budget exceeded','RESOURCE_BUDGET')
    for p in root.iterdir():p.chmod(0o600)
    return FactualAssessment(root,stable(report),file_hash(path),profile,Path(publication),canonical_query,_SEAL)


def prepare_cohort(assessment, card_ids, *, expected_assessment_id):
    """Select complete eligible Card groups; the returned manifest is NOT approval."""
    require(type(assessment) is FactualAssessment,'live factual assessment required','UNTRUSTED_INPUT')
    assessment.verify();report=assessment.report
    require(report['assessment_id']==expected_assessment_id,'independent assessment pin mismatch','INTEGRITY_MISMATCH')
    require(type(card_ids) in (tuple,list) and 0<len(card_ids)<=MAX_COHORT_PRINTINGS
            and all(type(x) is str for x in card_ids) and len(set(card_ids))==len(card_ids),'bounded unique Card selection required')
    documents={};crosswalk=[];evidence=[]
    with sqlite3.connect('file:'+str(assessment.root/'index.sqlite3')+'?mode=ro',uri=True) as db:
        for selected in sorted(card_ids):
            cards=db.execute('SELECT ck,id,reasons FROM cards WHERE id=?',(selected,)).fetchall()
            require(len(cards)==1 and cards[0][2]=='[]','selected Card requires identity/evidence review','QUARANTINED')
            ck,cid,_=cards[0];crosswalk.append(dict(entity_type='card',source_identity=ck,canonical_identity=cid))
            require(db.execute('SELECT count(*) FROM printings WHERE ck=?',(ck,)).fetchone()[0]<=MAX_COHORT_PRINTINGS,
                'selected group exceeds the bounded review envelope','RESOURCE_BUDGET')
            prints=db.execute('SELECT pk,id,reasons FROM printings WHERE ck=? ORDER BY pk',(ck,)).fetchall()
            require(prints and all(x[2]=='[]' for x in prints),'Card group is not dependency closed','QUARANTINED')
            for pk,pid,_ in prints:
                occurrences=db.execute('SELECT payload FROM rows WHERE pk=? ORDER BY p,n',(pk,)).fetchall()
                require(len(occurrences)==1,'duplicate Printing cannot be admitted','QUARANTINED')
                row=json.loads(occurrences[0][0]);card,printing=_documents(row,cid,pid)
                documents[('card',cid)]=card;documents[('printing',pid)]=printing
                crosswalk.append(dict(entity_type='printing',source_identity=pk,canonical_identity=pid))
                evidence.append(dict(partition=row['partition'],row=row['row'],
                    source_record_sha256=row['source_record_sha256'],factual_row_sha256=hashlib.sha256((stable(row)+'\n').encode()).hexdigest(),
                    oracle_identifier_field='scryfallOracleId' if 'scryfallOracleId' in row['identifiers'] else 'oracleId',
                    card_id=cid,printing_id=pid))
    require(sum(kind=='printing' for kind,_ in documents)<=MAX_COHORT_PRINTINGS,'cohort exceeds existing 25-Printing review bound','RESOURCE_BUDGET')
    require(len({cid for _,cid in documents})==len(documents),
        'existing promotion subject IDs collide across entity kinds','CROSS_KIND_IDENTITY_COLLISION')
    resolution=EntityResolver().resolve([dict(id=cid,entity_type=kind,
        identifiers={'canonical_identifier':kind+':'+cid}) for kind,cid in sorted(documents)])
    require(not resolution['rejected'] and not resolution['unresolved'],'selected identity resolution refused','QUARANTINED')
    assertions=[];transforms=[]
    timestamp=report['source']['release']['date']+'T00:00:00Z'
    source_id='mtgjson-factual-'+report['source']['release']['artifact_sha256'][:24]
    for (kind,cid),document in sorted(documents.items()):
        supports=[r for r in evidence if r['card_id']==cid] if kind=='card' else [r for r in evidence if r['printing_id']==cid]
        for field,value in sorted(document.items()):
            if field in ('schema_version','assertions'):continue
            transform={'normalized_name':'query-normalize-name-v1','language':'reviewed-language-label-v1',
                'set_id':'provider-code-casefold-v1','id':'reviewed-identity-crosswalk-v1',
                'card_id':'reviewed-identity-crosswalk-v1','game':'bound-game-v1'}.get(field,'literal-field-map-v1')
            source_field=({target:source for source,target in CARD_FIELDS.items()}.get(field,
                {'normalized_name':'name','id':'identifiers/scryfallOracleId','game':None}.get(field)) if kind=='card' else
                {'id':'uuid','card_id':'identifiers/scryfallOracleId','set_id':None,
                 'collector_number':'number','language':'language','rarity':'rarity',
                 'finishes':'finishes','external_identifiers':'identifiers'}[field])
            if field=='mana_cost' and isinstance(value,dict):transform='empty-provider-cost-preserves-unknown-v1'
            field_supports=[]
            for support in supports:
                part=next(p for p in report['partition_inventory'] if p['ordinal']==support['partition'])
                pointer=f'/data/{part["source_key"]}/cards/{support["row"]}'
                source_hint=(source_field.replace('scryfallOracleId',support['oracle_identifier_field'])
                    if source_field else None)
                factual_pointer=('/assertions/'+source_hint if kind=='card' and field in CARD_FIELDS.values() else
                    '/assertions/name' if kind=='card' and field=='normalized_name' else
                    '/card_id' if kind=='card' and field=='id' else
                    '/mapped_printing/mapped_fields/'+({'id':'uuid','card_id':'card_reference',
                        'set_id':'set_code','collector_number':'collector_number'}.get(field,field))
                    if kind=='printing' else None)
                field_supports.append(dict(support,source_field=source_field,
                    source_record_pointer=pointer,original_field_hint=source_hint,
                    original_field_presence='NOT_REESTABLISHED_FROM_ARCHIVE',
                    factual_artifact='assertions.jsonl',factual_pointer=factual_pointer,
                    source_mapping='Retained mapper output may contain documented defaults; no new default is supplied here.'
                        if kind=='printing' else 'Retained literal assertion or explicit identity/game transformation.'))
            binding=dict(subject=cid,entity_type=kind,path='/'+field,asserted_value=value,
                source_id=source_id,publication_id=report['source']['publication_id'],supports=field_supports,transformation=transform)
            aid='factual-'+identity(binding)[7:]
            assertions.append(dict(schema_version='v3',id=aid,subject_id=cid,path='/'+field,
                asserted_value=deepcopy(value),source_id=source_id,source_type='verified-factual-publication',
                evidence_class='derived',timestamp=timestamp,confidence=1.0,
                verification_status='verified',status='candidate',
                notes=stable(dict(binding=binding,verification='Exact derivative correspondence, not universal truth or current Oracle.'))))
            transforms.append(binding)
    body=dict(schema_version='private-factual-cohort-v1',policy=POLICY,assessment_id=expected_assessment_id,
        source=report['source'],canonical_pre_state=report['canonical_pre_state'],implementation=report['implementation'],
        crosswalk=sorted(crosswalk,key=lambda x:(x['entity_type'],x['canonical_identity'])),
        documents=[dict(entity_type=kind,record=doc) for (kind,_),doc in sorted(documents.items())],
        assertions=sorted(assertions,key=lambda x:x['id']),transformations=transforms,evidence=evidence,
        selected_card_ids=sorted(card_ids),dependency_closure='COMPLETE_SELECTED_CARD_PRINTING_GROUPS',
        capabilities=dict(catalog_facts=True,mechanical_semantics=False,rules_execution=False,
            format_legality=False,public_export=False,external_ai_export=False),authority='PENDING_AUTHENTICATED_ADMISSION')
    require(len(stable(body).encode())<=MAX_MANIFEST_BYTES,'cohort manifest exceeds bound','RESOURCE_BUDGET')
    return dict(body,manifest_id=identity(body))


def validate_cohort_manifest(manifest):
    """Hard factual boundary, also enforced when reopening a retained snapshot."""
    keys={'schema_version','policy','assessment_id','source','canonical_pre_state','implementation',
          'crosswalk','documents','assertions','transformations','evidence','selected_card_ids',
          'dependency_closure','capabilities','authority','manifest_id'}
    require(type(manifest) is dict and set(manifest)==keys and manifest['schema_version']=='private-factual-cohort-v1'
        and manifest['policy']==POLICY and manifest['authority']=='PENDING_AUTHENTICATED_ADMISSION'
        and manifest['dependency_closure']=='COMPLETE_SELECTED_CARD_PRINTING_GROUPS',
        'unsupported factual cohort contract','UNSUPPORTED_PROFILE')
    require(manifest['capabilities']==dict(catalog_facts=True,mechanical_semantics=False,rules_execution=False,
        format_legality=False,public_export=False,external_ai_export=False),
        'factual capabilities cannot be expanded','UNSUPPORTED_PROFILE')
    require(manifest['manifest_id']==identity({k:v for k,v in manifest.items() if k!='manifest_id'}),
        'cohort identity mismatch','INTEGRITY_MISMATCH')
    documents={};cards=set();printings=[]
    for item in manifest['documents']:
        require(set(item)=={'entity_type','record'},'closed factual document required')
        kind=item['entity_type'];record=item['record'];cid=record['id']
        allowed=({'id','schema_version','game','name','normalized_name','layout','assertions'}|set(CARD_FIELDS.values())
            if kind=='card' else {'id','schema_version','card_id','set_id','collector_number','language',
                'rarity','finishes','external_identifiers','assertions'} if kind=='printing' else set())
        require(allowed and set(record)<=allowed and record['schema_version']=='v3' and record['assertions']==[],
            'unsupported canonical factual field','UNSUPPORTED_FIELD')
        require(cid not in documents,'ambiguous promotion subject across entity kinds')
        validate_document(record,kind,'v3')
        if kind=='card':
            require(record['layout']=='normal' and record['game']=='magic'
                and record['normalized_name']==normalize_name(record['name']), 'unsupported Card characteristics')
            cards.add(cid)
        else:
            require(type(record['finishes']) is list and record['finishes']
                and set(record['external_identifiers'])<=IDENTIFIERS,'unsupported Printing characteristics')
            printings.append(record)
        documents[cid]=record
    require(cards==set(manifest['selected_card_ids']) and 0<len(printings)<=MAX_COHORT_PRINTINGS
        and all(p['card_id'] in cards for p in printings)
        and {p['card_id'] for p in printings}==cards,'incomplete factual dependency closure')
    required={(cid,'/'+field) for cid,record in documents.items() for field in record
        if field not in ('schema_version','assertions')}
    seen=set();source_id='mtgjson-factual-'+manifest['source']['release']['artifact_sha256'][:24]
    assertion_keys={'schema_version','id','subject_id','path','asserted_value','source_id','source_type',
        'evidence_class','timestamp','confidence','verification_status','status','notes'}
    for assertion in manifest['assertions']:
        require(set(assertion)==assertion_keys and assertion['schema_version']=='v3'
            and assertion['status']=='candidate' and assertion['verification_status']=='verified'
            and assertion['evidence_class']=='derived' and assertion['source_id']==source_id,
            'unsupported factual assertion')
        key=(assertion['subject_id'],assertion['path'])
        require(key in required and key not in seen and assertion['asserted_value']==documents[key[0]][key[1][1:]],
            'factual assertion does not match its subject and field','INTEGRITY_MISMATCH')
        binding=_json(assertion['notes'])['binding']
        require(assertion['id']=='factual-'+identity(binding)[7:]
            and binding['subject']==key[0] and binding['path']==key[1]
            and binding['asserted_value']==assertion['asserted_value']
            and binding['publication_id']==manifest['source']['publication_id']
            and binding['supports'] and binding in manifest['transformations'],
            'assertion transformation provenance mismatch','INTEGRITY_MISMATCH')
        seen.add(key)
    require(seen==required,'factual assertion coverage incomplete')
