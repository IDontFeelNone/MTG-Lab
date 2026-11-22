"""Private, release-wide MTGJSON reconciliation; never acquisition or admission.

The existing incremental decoder and candidate mapper own provider semantics.
This consumer records *every* row before comparing assertions on disk. In
particular, it never uses the mapper's corpus-level first-Card-wins behaviour.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import resource
import sqlite3
import sys
import time

from .mapper import map_dataset
from .streaming import _decoded, _IncrementalJSON
from .validator import IDENTIFIER_POLICY, MTGJSONValidationError, validate_document
from .private_policy import RETENTION, SET_FIELDS, project_row

VERSION = "release-catalog-reconciliation-v1"
FACTUAL_VERSION = "private-mtgjson-import-report-v1"
OPERATION = "private-release-catalog-reconciliation-v1"
OUTPUT_NAMES = frozenset(('assertions.jsonl', 'conflicts.jsonl', 'duplicates.jsonl',
    'identifier-conflicts.jsonl', 'cards.jsonl', 'printings.jsonl', 'exceptional.jsonl',
    'unresolved.jsonl', 'report.json', 'report.json.tmp'))
CARD_FIELDS = ("name", "layout", "colors", "colorIdentity", "manaCost", "manaValue",
               "type", "text", "power", "toughness", "loyalty", "defense", "keywords")
LIMITATIONS = (
    "Provider identifiers and assertions are review candidates, not canonical facts.",
    "Source coverage does not establish real-world catalog completeness.",
    "One release does not establish historical Oracle revision completeness.",
    "No semantic review, gameplay execution, acquisition, admission or activation.",
    "Artifacts are private; no redistribution or AI-export permission is granted.",
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _hash(value):
    return hashlib.sha256(value if type(value) is bytes else _json(value).encode()).hexdigest()


class ReconciliationError(ValueError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=VERSION, status="REFUSED", code=self.code,
                    reason=str(self), canonical_admission="NOT_PERFORMED")


def _require(condition, reason, code="INVALID_INPUT"):
    if not condition:
        raise ReconciliationError(code, reason)


@dataclass(frozen=True)
class ReconciliationLimits:
    """Caller may tighten these hard ceilings, never enlarge them."""
    source_bytes: int = 2 * 1024**3
    decoded_bytes: int = 8 * 1024**3
    partition_bytes: int = 8 * 1024**2
    row_bytes: int = 64 * 1024
    rows: int = 1_000_000
    partitions: int = 10_000
    disk_bytes: int = 2 * 1024**3
    output_bytes: int = 512 * 1024**2
    cpu_seconds: int = 60
    wall_seconds: int = 70
    memory_bytes: int = 512 * 1024**2

    def validate(self):
        for key, ceiling in asdict(ReconciliationLimits()).items():
            value = getattr(self, key)
            _require(type(value) is int and 0 < value <= ceiling, "invalid resource limit: " + key)
        _require(self.memory_bytes >= 128 * 1024**2 and self.disk_bytes >= 1024**2,
                 "memory/disk limit below supported operating floor")


def _unique(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "duplicate JSON object key")
        value[key] = item
    return value


class _Reader(_IncrementalJSON):
    """Bound the existing decoder before accumulating a partition/value."""
    def __init__(self, stream, limits):
        class BoundedDecodedStream:
            def __init__(self): self.total = 0
            def read(self, size):
                block = stream.read(min(size, limits.decoded_bytes - self.total + 1))
                self.total += len(block)
                _require(self.total <= limits.decoded_bytes, 'decoded source exceeds budget', 'RESOURCE_BUDGET')
                return block
        super().__init__(BoundedDecodedStream(), chunk_size=min(65536, limits.partition_bytes))
        self.limits = limits
        self.decoder = json.JSONDecoder(object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ReconciliationError("INVALID_INPUT", "nonfinite JSON number")))

    def _fill(self):
        # Completed tokens can otherwise remain in the inherited buffer.
        self.buffer, self.position = self.buffer[self.position:], 0
        _require(len(self.buffer.encode()) <= self.limits.partition_bytes,
                 "partition/value exceeds byte budget", "RESOURCE_BUDGET")
        result = super()._fill()
        _require(len(self.buffer.encode()) <= self.limits.partition_bytes + self.chunk_size,
                 "partition/value exceeds byte budget", "RESOURCE_BUDGET")
        return result


def _partitions(path, limits):
    """Consume the entire envelope, rejecting duplicate sections and trailing data."""
    with _decoded(path) as stream:
        reader = _Reader(stream, limits)
        reader.char("{")
        seen, meta = set(), None
        while True:
            key = reader.value()
            _require(type(key) is str and key in ("meta", "data") and key not in seen,
                     "closed unique MTGJSON meta/data envelope required")
            seen.add(key); reader.char(":")
            if key == "meta":
                meta = reader.value()
                validate_document({"meta": meta, "data": {}})
            else:
                _require(meta is not None, "meta must precede data", "UNSUPPORTED_PROFILE")
                yield meta, None, None
                count = 0
                for set_key, source_set in reader.object_items():
                    count += 1
                    _require(count <= limits.partitions, "partition count exceeds budget", "RESOURCE_BUDGET")
                    _require(len(_json(source_set).encode()) <= limits.partition_bytes,
                             "partition exceeds byte budget", "RESOURCE_BUDGET")
                    yield meta, set_key, source_set
            reader._space()
            _require(reader.position < len(reader.buffer), "truncated source envelope")
            marker = reader.buffer[reader.position]; reader.position += 1
            if marker == "}":
                break
            _require(marker == ",", "invalid source envelope separator")
        _require(seen == {"meta", "data"}, "meta and data required")
        reader._space()
        _require(reader.position == len(reader.buffer) and reader.eof, "trailing source content")


def _identifier(value):
    return (type(value) is str and 0 < len(value) <= 256 and value == value.strip()
            and value.isprintable())


def _row(meta, key, source_set, raw, limits):
    """One-row owning mapper invocation prevents loss of repeated assertions."""
    encoded = _json(raw).encode()
    _require(len(encoded) <= limits.row_bytes, "row exceeds byte budget", "RESOURCE_BUDGET")
    row = dict(source_record_sha256=_hash(encoded), status="SUPPORTED", card_id=None,
               printing_id=None, facet="", assertions={}, identifiers={},
               exceptional=False, relationships=[], mapped_card=None, mapped_printing=None, reason=None)
    if type(raw) is not dict:
        row["status"] = "UNSUPPORTED_RECORD"
        row['reason'] = 'SOURCE_ROW_NOT_AN_OBJECT'
        return row
    if _identifier(raw.get("uuid")):
        row["printing_id"] = raw["uuid"].casefold()
    # Relationships are source assertions even when Card identity is unresolved.
    # Preserve them before any identity/schema refusal; never manufacture faces.
    row["exceptional"] = (raw.get("layout", "normal") != "normal" or
                           any(k in raw for k in ("side", "faceName", "otherFaceIds")))
    if row["exceptional"]:
        row["facet"] = _json({k: raw[k] for k in ("side", "faceName") if k in raw})
    relationships = raw.get("otherFaceIds", [])
    if type(relationships) is not list or not all(_identifier(x) for x in relationships):
        row["status"] = "UNSUPPORTED_RECORD"
        row['reason'] = 'INVALID_FACE_RELATIONSHIPS'
        return row
    row["relationships"] = sorted(x.casefold() for x in relationships)
    ids = raw.get("identifiers", {})
    if type(ids) is not dict or any(not _identifier(k) or not _identifier(v) for k, v in ids.items()):
        row["status"] = "UNSUPPORTED_RECORD"
        row['reason'] = 'MALFORMED_IDENTIFIERS'
        return row
    row["identifiers"] = ids
    refs = [ids[k].casefold() for k in ("scryfallOracleId", "oracleId") if k in ids]
    if not refs or len(set(refs)) != 1:
        row["status"] = "IDENTITY_UNRESOLVED"
        row['reason'] = 'MISSING_OR_AMBIGUOUS_ORACLE_IDENTIFIER'
        return row
    try:
        validate_document({"meta": meta, "data": {key: {**source_set, "cards": [raw]}}})
        # Extra restrictions prevent malformed optional fields reaching mapper sort/text operations.
        _require(all(k not in raw or type(raw[k]) is str for k in
                     ("layout", "manaCost", "language", "rarity", "side", "faceName")),
                 "invalid optional provider text")
        for k in ("colors", "colorIdentity", "keywords", "finishes"):
            _require(k not in raw or (type(raw[k]) is list and all(_identifier(x) for x in raw[k])),
                     "invalid provider list")
        mapped = map_dataset({"meta": meta, "data": {key: {**source_set, "cards": [raw]}}})
    except (MTGJSONValidationError, ReconciliationError, TypeError, KeyError, AttributeError):
        row["status"] = "UNSUPPORTED_RECORD"
        row['reason'] = 'INVALID_SUPPORTED_PROVIDER_ROW'
        return row
    row["mapped_card"] = next(x for x in mapped if x["entity_type"] == "card")
    row["mapped_printing"] = next(x for x in mapped if x["entity_type"] == "printing")
    row["card_id"] = row["mapped_card"]["mapped_fields"]["card_reference"]
    row["assertions"] = {k: raw[k] for k in CARD_FIELDS if k in raw}
    return row


def _schema(db, limits):
    tables = {'binding', 'partitions', 'records', 'assertions', 'conflicts',
              'duplicate_printings', 'alias_conflicts'}
    indexes = {'card_idx', 'print_idx', 'assertion_idx', 'conflict_idx', 'duplicate_idx'}
    for kind, name, sql in db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"):
        _require((kind == 'table' and name in tables and not sql.upper().startswith('CREATE VIRTUAL'))
                 or (kind == 'index' and name in indexes),
                 'unrecognized or executable checkpoint schema', 'INTEGRITY_MISMATCH')
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA cache_size=-8192")
    db.execute("PRAGMA mmap_size=0")
    db.execute("PRAGMA max_page_count=" + str(limits.disk_bytes // 2 // 4096))
    db.executescript("""
      CREATE TABLE IF NOT EXISTS binding(payload TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS partitions(seq INTEGER PRIMARY KEY, key TEXT UNIQUE,
        code TEXT UNIQUE, raw_hash TEXT, rows INTEGER);
      CREATE TABLE IF NOT EXISTS records(p INTEGER,n INTEGER,card_id TEXT,printing_id TEXT,
        facet TEXT,status TEXT,printing_hash TEXT,exceptional INTEGER,payload TEXT,
        PRIMARY KEY(p,n));
      CREATE INDEX IF NOT EXISTS card_idx ON records(card_id);
      CREATE INDEX IF NOT EXISTS print_idx ON records(printing_id);
      CREATE TABLE IF NOT EXISTS assertions(p INTEGER,n INTEGER,card_id TEXT,facet TEXT,
        field TEXT,value TEXT,PRIMARY KEY(p,n,field));
      CREATE INDEX IF NOT EXISTS assertion_idx ON assertions(card_id,facet,field,value);
    """)


def _stored(p, n, row):
    return (p, n, row["card_id"], row["printing_id"], row["facet"], row["status"],
            (row['source_record_sha256'] if row.get('retention_profile') == RETENTION else
             _hash(row["mapped_printing"]) if row["mapped_printing"] else row['source_record_sha256']),
            int(row["exceptional"]), _json(row))


def _values(p, n, row):
    return [(p, n, row["card_id"], row["facet"], field, _json(value))
            for field, value in sorted(row["assertions"].items())]


def _disk(root, limits):
    total = 0
    for path in root.rglob("*"):
        _require(not path.is_symlink(), "symlink in private workspace", "INTEGRITY_MISMATCH")
        if path.is_file():
            total += path.stat().st_size
    # SQLite may unlink an open sort file: directory enumeration alone misses it.
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if target.startswith(str(root) + '/') and target.endswith(' (deleted)'):
                total += descriptor.stat().st_size
        except FileNotFoundError:
            pass
    _require(total <= limits.disk_bytes, "private workspace disk budget exceeded", "RESOURCE_BUDGET")


class _Outputs:
    def __init__(self, root, limits):
        self.root, self.limits, self.total, self.inventory = root, limits, 0, {}

    def write(self, name, values):
        digest, count, size = hashlib.sha256(), 0, 0
        with (self.root / name).open("wb") as out:
            for value in values:
                raw = (_json(value) + "\n").encode()
                self.total += len(raw)
                _require(self.total <= self.limits.output_bytes, "output byte budget exceeded", "RESOURCE_BUDGET")
                out.write(raw); digest.update(raw); count += 1; size += len(raw)
                if count % 256 == 0:
                    _disk(self.root.parent, self.limits)
        self.inventory[name] = dict(sha256=digest.hexdigest(), bytes=size, rows=count)


def _finalize(db, output, binding, meta, limits):
    """SQL group operations and streamed artifacts, never a corpus candidate list."""
    db.executescript("""
      DROP TABLE IF EXISTS conflicts;
      CREATE TABLE conflicts AS SELECT card_id,facet,field,count(DISTINCT value) variants
        FROM assertions GROUP BY card_id,facet,field HAVING count(DISTINCT value)>1;
      CREATE INDEX conflict_idx ON conflicts(card_id);
      DROP TABLE IF EXISTS duplicate_printings;
      CREATE TABLE duplicate_printings AS SELECT printing_id,count(*) occurrences,
        count(DISTINCT printing_hash) variants FROM records WHERE printing_id IS NOT NULL
        GROUP BY printing_id HAVING count(*)>1;
      CREATE INDEX duplicate_idx ON duplicate_printings(printing_id);
      DROP TABLE IF EXISTS alias_conflicts;
      CREATE TABLE alias_conflicts(namespace TEXT,value TEXT,occurrences INTEGER);
    """)
    for namespace, policy in sorted(IDENTIFIER_POLICY.items()):
        if policy["uniqueness"] == "strict":
            db.execute("""INSERT INTO alias_conflicts SELECT ?,lower(j.value),count(DISTINCT r.printing_id)
              FROM records r,json_each(r.payload,'$.identifiers') j WHERE j.key=?
              GROUP BY lower(j.value) HAVING count(DISTINCT r.printing_id)>1""", (namespace, namespace))
    db.commit()
    out = _Outputs(output, limits)

    def occurrences():
        for p, n, payload in db.execute("SELECT p,n,payload FROM records ORDER BY p,n"):
            yield dict(partition=p, row=n, **json.loads(payload))
    out.write("assertions.jsonl", occurrences())
    out.write("conflicts.jsonl", (dict(card_id=c, facet=f, field=k, distinct_assertions=v,
        disposition="WITHHELD") for c, f, k, v in db.execute(
            "SELECT * FROM conflicts ORDER BY card_id,facet,field")))
    out.write("duplicates.jsonl", (dict(printing_id=p, occurrences=n,
        classification="CONFLICT" if v > 1 else "DUPLICATE", disposition="WITHHELD")
        for p, n, v in db.execute("SELECT * FROM duplicate_printings ORDER BY printing_id")))
    out.write("identifier-conflicts.jsonl", (dict(namespace=n, value=v, printings=c, disposition="WITHHELD")
        for n, v, c in db.execute("SELECT * FROM alias_conflicts ORDER BY namespace,value")))

    def cards():
        for card_id, count, partitions, exceptional in db.execute("""SELECT card_id,count(*),
          count(DISTINCT p),max(exceptional) FROM records WHERE card_id IS NOT NULL GROUP BY card_id ORDER BY card_id"""):
            conflict = db.execute("SELECT 1 FROM conflicts WHERE card_id=? LIMIT 1", (card_id,)).fetchone()
            unsupported = db.execute("SELECT 1 FROM records WHERE card_id=? AND status!='SUPPORTED' LIMIT 1", (card_id,)).fetchone()
            yield dict(card_id=card_id, source_occurrences=count, partition_count=partitions,
                       cross_set_relationship=partitions > 1,
                       candidate_status="WITHHELD" if conflict or exceptional or unsupported else "REVIEW_CANDIDATE",
                       canonical_admission="NOT_PERFORMED", evidence="assertions.jsonl")
    out.write("cards.jsonl", cards())

    def printings():
        for printing_id, p, n in db.execute("""SELECT printing_id,min(p),0 FROM records
          WHERE printing_id IS NOT NULL GROUP BY printing_id ORDER BY printing_id"""):
            n = db.execute("SELECT min(n) FROM records WHERE printing_id=? AND p=?", (printing_id, p)).fetchone()[0]
            row = json.loads(db.execute("SELECT payload FROM records WHERE p=? AND n=?", (p, n)).fetchone()[0])
            duplicate = db.execute("SELECT 1 FROM duplicate_printings WHERE printing_id=?", (printing_id,)).fetchone()
            conflict = db.execute("SELECT 1 FROM conflicts WHERE card_id=? LIMIT 1", (row["card_id"],)).fetchone()
            alias = db.execute("""SELECT 1 FROM alias_conflicts a,json_each(?,'$.identifiers') j
              WHERE a.namespace=j.key AND a.value=lower(j.value) LIMIT 1""", (_json(row),)).fetchone()
            withheld = duplicate or conflict or alias or row["exceptional"] or row["status"] != "SUPPORTED"
            # Do not publish an arbitrary duplicate/conflicting assertion as the chosen candidate.
            yield dict(printing_id=printing_id, card_id=None if duplicate else row["card_id"],
                mapped_candidate=None if withheld else row["mapped_printing"],
                candidate_status="WITHHELD" if withheld else "REVIEW_CANDIDATE",
                canonical_admission="NOT_PERFORMED", evidence="assertions.jsonl")
    out.write("printings.jsonl", printings())

    def exceptional():
        for p, n, payload in db.execute("SELECT p,n,payload FROM records WHERE exceptional=1 ORDER BY p,n"):
            row = json.loads(payload)
            missing = [x for x in row["relationships"] if not db.execute(
                "SELECT 1 FROM records WHERE printing_id=? LIMIT 1", (x,)).fetchone()]
            yield dict(partition=p, row=n, card_id=row["card_id"], printing_id=row["printing_id"],
                       facet=row["facet"], related_printings=row["relationships"],
                       missing_related_printings=missing, disposition="REVIEW_REQUIRED")
    out.write("exceptional.jsonl", exceptional())
    out.write("unresolved.jsonl", (dict(partition=p, row=n, status=s, reason=json.loads(v)['reason'], source_record_sha256=json.loads(v)["source_record_sha256"])
        for p, n, s, v in db.execute("SELECT p,n,status,payload FROM records WHERE status!='SUPPORTED' ORDER BY p,n")))
    count = lambda sql: db.execute(sql).fetchone()[0]
    report = dict(schema_version=VERSION, status="CANDIDATES_PREPARED", source_release=binding,
        provider_metadata=meta, partition_inventory=[dict(ordinal=p, source_key=k, set_code=c,
            source_partition_sha256=h, rows=n) for p,k,c,h,n in db.execute("SELECT * FROM partitions ORDER BY seq")],
        total_source_rows=count("SELECT count(*) FROM records"),
        unique_supported_card_identities=count("SELECT count(DISTINCT card_id) FROM records WHERE status='SUPPORTED'"),
        distinct_printing_identities=count("SELECT count(DISTINCT printing_id) FROM records"),
        conflicting_card_fields=count("SELECT count(*) FROM conflicts"),
        duplicate_printing_identities=count("SELECT count(*) FROM duplicate_printings"),
        conflicting_printing_identities=count("SELECT count(*) FROM duplicate_printings WHERE variants>1"),
        conflicting_external_identifiers=count("SELECT count(*) FROM alias_conflicts"),
        exceptional_records=count("SELECT count(*) FROM records WHERE exceptional=1"),
        unresolved_identity_records=count("SELECT count(*) FROM records WHERE status='IDENTITY_UNRESOLVED'"),
        unsupported_records=count("SELECT count(*) FROM records WHERE status='UNSUPPORTED_RECORD'"),
        source_processing_completeness="ALL_ROWS_ACCOUNTED_FOR",
        catalog_population_completeness="NOT_ESTABLISHED",
        canonical_admission="NOT_PERFORMED", production_activation="NOT_PERFORMED",
        source_use_status="HOST_AUTHORIZED_FOR_EXACT_PRIVATE_OPERATION",
        artifacts=out.inventory, limits=asdict(limits), limitations=list(LIMITATIONS))
    if 'private_scope' in binding:
        report['schema_version'] = FACTUAL_VERSION
        report['source_use_status'] = 'HOST_SCOPED_DISPOSITION_NOT_EXTERNAL_LICENSE'
        report['retention_profile'] = RETENTION
        report['real_card_execution'] = 'BLOCKED'
        report['limitations'] += [
            'Whole-artifact reads and temporary mixed processing require independent scope support.',
            'Only the declared factual projection is retained; excluded content is neither absent nor verified.',
            'Duplicate source variations include excluded-field differences; no arbitrary candidate is selected.',
            'No extra source copy is made. Replay requires the independently retained original source and host profile.',
        ]
    report["report_id"] = "sha256:" + _hash(report)
    return report


def _run(source, root, binding, limits, stop_after):
    digest = hashlib.sha256()
    total = 0
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            total += len(block)
            _require(total <= limits.source_bytes, "source byte budget exceeded", "RESOURCE_BUDGET")
            digest.update(block)
    _require(digest.hexdigest() == binding["artifact_sha256"], "source checksum mismatch", "INTEGRITY_MISMATCH")
    db = sqlite3.connect(root / "index.sqlite3")
    try:
        _schema(db, limits)
        db.set_progress_handler(lambda: (_disk(root, limits), 0)[1], 10000)
        current = db.execute("SELECT payload FROM binding").fetchall()
        if not current:
            db.execute("INSERT INTO binding VALUES(?)", (_json(dict(source=binding, limits=asdict(limits))),))
            db.commit()
        else:
            _require(current == [(_json(dict(source=binding, limits=asdict(limits))),)],
                     "workspace binding mismatch", "INTEGRITY_MISMATCH")
        _require(db.execute("PRAGMA integrity_check").fetchone() == ("ok",), "invalid index", "INTEGRITY_MISMATCH")
        completed = db.execute("SELECT count(*) FROM partitions").fetchone()[0]
        processed, seq, total_rows, meta = 0, 0, 0, None
        seen_keys, seen_codes = set(), set()
        for meta, key, source_set in _partitions(source, limits):
            if key is None:
                _require(meta["version"] == binding["version"] and meta["date"] == binding["date"],
                         "source release metadata mismatch", "INTEGRITY_MISMATCH")
                continue
            _require(_identifier(key) and type(source_set) is dict, "invalid set partition")
            code = source_set.get("code")
            _require(_identifier(code) and code.casefold() == key.casefold()
                     and _identifier(source_set.get("name")), "invalid partition identity")
            _require(key.casefold() not in seen_keys and code.casefold() not in seen_codes,
                     "duplicate partition identity")
            seen_keys.add(key.casefold()); seen_codes.add(code.casefold())
            cards = source_set.get("cards")
            _require(type(cards) is list, "partition cards must be an array")
            total_rows += len(cards)
            _require(total_rows <= limits.rows, "source row budget exceeded", "RESOURCE_BUDGET")
            partition = (seq, key, code.casefold(), _hash(source_set), len(cards))
            retained = db.execute("SELECT * FROM partitions WHERE seq=?", (seq,)).fetchone()
            if seq < completed:
                _require(retained == partition, "checkpoint partition mismatch", "INTEGRITY_MISMATCH")
            else:
                _require(retained is None, "non-prefix checkpoint", "INTEGRITY_MISMATCH")
                db.execute("BEGIN")
            try:
                for n, raw in enumerate(cards):
                    if 'private_scope' in binding:
                        # Authorization covered the COMPLETE input before any read.
                        # Filter before the owning mapper/SQLite, never just at export.
                        original = _json(raw).encode()
                        _require(len(original) <= limits.row_bytes,
                                 'row exceeds byte budget', 'RESOURCE_BUDGET')
                        selected, omitted = project_row(raw)
                        selected_set = {k: v for k, v in source_set.items() if k in SET_FIELDS}
                        row = _row({k: meta[k] for k in ('date', 'version')}, key,
                                   selected_set, selected, limits)
                        row['source_record_sha256'] = _hash(original)
                        row['retention_profile'] = RETENTION
                        row['omitted_field_count'] = omitted
                        for mapped in ('mapped_card', 'mapped_printing'):
                            if row[mapped] is not None:
                                row[mapped]['unknown_fields'] = {}
                    else:
                        row = _row(meta, key, source_set, raw, limits)
                    stored, values = _stored(seq, n, row), _values(seq, n, row)
                    if seq < completed:
                        _require(db.execute("SELECT * FROM records WHERE p=? AND n=?", (seq,n)).fetchone() == stored,
                                 "checkpoint row mismatch", "INTEGRITY_MISMATCH")
                        _require(db.execute("SELECT * FROM assertions WHERE p=? AND n=? ORDER BY field", (seq,n)).fetchall() == values,
                                 "checkpoint assertion mismatch", "INTEGRITY_MISMATCH")
                    else:
                        db.execute("INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?)", stored)
                        db.executemany("INSERT INTO assertions VALUES(?,?,?,?,?,?)", values)
                    if n % 128 == 0:
                        _disk(root, limits)
                if seq >= completed:
                    db.execute("INSERT INTO partitions VALUES(?,?,?,?,?)", partition)
                    db.commit(); processed += 1
            except BaseException:
                db.rollback(); raise
            seq += 1
            if stop_after is not None and processed >= stop_after:
                return dict(schema_version=FACTUAL_VERSION if 'private_scope' in binding else VERSION,
                            status="PAUSED", completed_partitions=seq,
                            canonical_admission="NOT_PERFORMED", source_processing_completeness="INCOMPLETE")
        _require(meta is not None and seq > 0, "release must contain at least one partition")
        _require(db.execute("SELECT count(*) FROM records").fetchone()[0] == total_rows
                 and db.execute("SELECT count(*) FROM partitions").fetchone()[0] == seq,
                 "checkpoint contains unaccounted rows", "INTEGRITY_MISMATCH")
        expected_assertions = db.execute("SELECT count(*) FROM records,json_each(records.payload,'$.assertions')").fetchone()[0]
        _require(db.execute("SELECT count(*) FROM assertions").fetchone()[0] == expected_assertions,
                 "checkpoint contains unaccounted assertions", "INTEGRITY_MISMATCH")
        # Re-hash after parsing so a changed input cannot acquire a complete report.
        with source.open("rb") as stream:
            final_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        _require(final_digest == binding["artifact_sha256"], "source changed during processing", "INTEGRITY_MISMATCH")
        output = root / "output"
        if output.exists():
            for p in output.iterdir():
                _require(p.name in OUTPUT_NAMES and p.is_file() and not p.is_symlink(),
                         "invalid output workspace", "INTEGRITY_MISMATCH")
                p.unlink()
        output.mkdir(exist_ok=True)
        result = _finalize(db, output, binding,
            {k: meta[k] for k in ('date', 'version')} if 'private_scope' in binding else meta, limits)
        _disk(root, limits)
        raw = (_json(result) + "\n").encode()
        _require(len(raw) <= min(4 * 1024**2, limits.output_bytes), "summary exceeds budget", "RESOURCE_BUDGET")
        _require(sum(item['bytes'] for item in result['artifacts'].values()) + len(raw) <= limits.output_bytes,
                 'artifacts plus summary exceed output budget', 'RESOURCE_BUDGET')
        _require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + len(raw) <= limits.disk_bytes,
                 "final summary exceeds disk budget", "RESOURCE_BUDGET")
        (output / "report.json.tmp").write_bytes(raw)
        (output / "report.json.tmp").replace(output / "report.json")
        return result
    finally:
        db.close()


def _worker_peak_memory_kib():
    # Linux ru_maxrss survives exec with the launcher's historical high-water
    # mark. VmHWM resets at exec and measures this isolated worker instead.
    try:
        with Path('/proc/self/status').open() as status:
            for line in status:
                if line.startswith('VmHWM:'):
                    fields = line.split()
                    _require(len(fields) == 3 and fields[1].isdigit() and fields[2] == 'kB',
                             'worker memory measurement unavailable', 'RESOURCE_MEASUREMENT_UNAVAILABLE')
                    return int(fields[1])
    except OSError:
        raise ReconciliationError('RESOURCE_MEASUREMENT_UNAVAILABLE', 'worker memory measurement unavailable') from None
    raise ReconciliationError('RESOURCE_MEASUREMENT_UNAVAILABLE', 'worker high-water measurement unavailable')


def _worker(connection, source, root, binding, limits, stop_after):
    started = time.monotonic()
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.disk_bytes // 2, limits.disk_bytes // 2))
        os.environ["SQLITE_TMPDIR"] = str(root)
        result = _run(source, root, binding, limits, stop_after)
        peak_memory = _worker_peak_memory_kib()
        _require(peak_memory * 1024 <= limits.memory_bytes,
                 'worker memory high-water exceeds configured budget', 'RESOURCE_BUDGET')
        connection.send((True, result, dict(seconds=round(time.monotonic()-started,6),
            peak_memory_kib=peak_memory)))
    except ReconciliationError as error:
        connection.send((False, error.as_dict(), None))
    except (MemoryError, sqlite3.OperationalError):
        connection.send((False, ReconciliationError("RESOURCE_BUDGET", "worker memory, disk or SQL budget refused").as_dict(), None))
    except (ValueError, OSError, sqlite3.DatabaseError, RecursionError, TypeError, KeyError):
        connection.send((False, ReconciliationError("INVALID_INPUT", "invalid source or private checkpoint").as_dict(), None))
    finally:
        connection.close()


def reconcile_release(source, workspace, release, *, authorize_source=None,
                      limits=None, stop_after_partitions=None, retention_profile=None,
                      source_use_receipt=None):
    """Reconcile one explicit local release in a bounded isolated worker.

    ``authorize_source`` is trusted host code, not a JSON approval flag. It must
    independently authorize whole-file processing, private source/projection
    retention and private reports for the exact release/workspace operation.
    No built-in real-provider authorizer exists. Refusal happens before source
    reads or workspace creation. Call from an importable Python main (spawn).
    ``stop_after_partitions`` deliberately pauses after N newly committed units;
    resume by calling again with the same source, release, workspace and limits.
    """
    limits = ReconciliationLimits() if limits is None else limits
    _require(sys.platform == 'linux', 'bounded worker requires Linux resource controls', 'UNSUPPORTED_PLATFORM')
    _require(type(limits) is ReconciliationLimits, "explicit supported limits required")
    limits.validate()
    _require(type(release) is dict and release.keys() == {"provider", "release_id", "version", "date", "artifact_sha256", "provenance_reference", "notice_reference"},
             "closed release binding required")
    _require(all(_identifier(v) for v in release.values()) and release["provider"] == "MTGJSON"
             and re.fullmatch("[0-9a-f]{64}", release["artifact_sha256"]), "invalid release binding")
    release = deepcopy(release)
    _require(stop_after_partitions is None or (type(stop_after_partitions) is int and stop_after_partitions > 0),
             "positive partition pause required")
    source, root = Path(source).absolute(), Path(workspace).absolute()
    _require(not any(p.is_symlink() for p in (source,*source.parents,root,*root.parents)), "symlink paths refused")
    _require(source != root and root not in source.parents, "source must be outside private workspace")
    _require(not any((p/".git"/"HEAD").is_file() or (p/".git").is_file()
                     for p in (root,*root.parents)), "workspace must be outside repository")
    bindings = dict(operation=OPERATION, release=release, limits=asdict(limits),
                    whole_artifact_read=True, private_source_and_derived_retention=True,
                    public_export=False, canonical_admission=False)
    if retention_profile is not None or source_use_receipt is not None:
        _require(retention_profile == RETENTION and type(source_use_receipt) is dict,
                 'supported explicit private retention profile required', 'SOURCE_POLICY_REFUSAL')
        bindings.update(retention_profile=retention_profile, source_use_receipt=deepcopy(source_use_receipt))
    _require(callable(authorize_source), "source-use scope not established", "SOURCE_POLICY_REFUSAL")
    try:
        authorized = authorize_source(deepcopy(bindings))
    except Exception:
        raise ReconciliationError("SOURCE_POLICY_REFUSAL", "host source-use disposition unavailable") from None
    _require(authorized is True, "exact source-use operation not authorized", "SOURCE_POLICY_REFUSAL")
    if retention_profile is not None:
        release['private_scope'] = dict(retention_profile=retention_profile,
                                        source_use_receipt=deepcopy(source_use_receipt))
    _require(source.is_file(), "source unavailable")
    _require(source.stat().st_size <= limits.source_bytes, 'source exceeds byte budget', 'RESOURCE_BUDGET')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    _require(root.stat().st_mode & 0o077 == 0, 'private workspace permissions required')
    _require(not any(p.is_symlink() for p in root.rglob('*')), 'symlink in workspace refused')
    _require(set(p.name for p in root.iterdir()) <= {"index.sqlite3", "index.sqlite3-journal", "output", "last-run.json", ".lock"},
             "workspace must be dedicated to reconciliation")
    import fcntl
    with (root / ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ReconciliationError("WORKSPACE_BUSY", "another reconciliation owns this workspace") from None
        context = multiprocessing.get_context("spawn")
        reader, writer = context.Pipe(duplex=False)
        process = context.Process(target=_worker, args=(writer,source,root,release,limits,stop_after_partitions))
        process.start(); writer.close()
        try:
            if not reader.poll(limits.wall_seconds):
                raise ReconciliationError("RESOURCE_BUDGET", "worker exceeded wall budget")
            try:
                success, value, measurement = reader.recv()
            except EOFError:
                raise ReconciliationError("RESOURCE_BUDGET", "worker terminated; no complete result") from None
            if not success:
                raise ReconciliationError(value["code"], value["reason"])
            (root / "last-run.json").write_text(_json(measurement) + "\n")
            _disk(root, limits)
            return value
        finally:
            if process.is_alive():
                process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill(); process.join(timeout=1)
            reader.close()
