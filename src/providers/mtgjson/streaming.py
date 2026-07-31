"""Memory-bounded, resumable MTGJSON AllPrintings planning primitives.

The standard library JSON decoder normally decodes the complete top-level ``data``
object.  An incremental adapter instead yields one set value at a time. SQLite and
content-addressed JSON shards retain corpus-wide state without retaining records.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import resource
import sqlite3
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from evidence import AcquisitionMetadata
from evidence.contracts import deterministic_json

from .execution import MTGJSONImportExecution
from .mapper import map_dataset
from .validator import IDENTIFIER_POLICY, MTGJSONValidationError, validate_document


SCHEMA = "mtgjson-streaming-ingestion-v1"


def _atomic(path: Path, value: Any) -> str:
    content = (deterministic_json(value) + "\n").encode()
    digest = hashlib.sha256(content).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)
    return digest


@contextmanager
def _decoded(path: Path):
    raw = path.open("rb")
    magic = raw.read(2); raw.seek(0)
    stream = gzip.GzipFile(fileobj=raw) if magic == b"\x1f\x8b" else raw
    try:
        yield stream
    finally:
        stream.close()
        if stream is not raw:
            raw.close()


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


class _IncrementalJSON:
    """Small stdlib decoder adapter which retains only the current JSON value."""

    def __init__(self, stream, chunk_size: int = 64 * 1024) -> None:
        import codecs
        self.stream, self.chunk_size = stream, chunk_size
        self.decoder = json.JSONDecoder()
        self.utf8 = codecs.getincrementaldecoder("utf-8")()
        self.buffer, self.position, self.eof = "", 0, False

    def _fill(self) -> bool:
        block = self.stream.read(self.chunk_size)
        if block:
            self.buffer += self.utf8.decode(block)
            return True
        if not self.eof:
            self.buffer += self.utf8.decode(b"", final=True); self.eof = True
        return False

    def _space(self) -> None:
        while True:
            while self.position < len(self.buffer) and self.buffer[self.position].isspace():
                self.position += 1
            if self.position < len(self.buffer) or not self._fill(): return

    def char(self, expected: str) -> None:
        self._space()
        if self.position >= len(self.buffer) or self.buffer[self.position] != expected:
            raise MTGJSONValidationError(f"expected {expected!r} while streaming JSON")
        self.position += 1

    def value(self) -> Any:
        self._space()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, self.position)
                self.position = end
                # Discard bytes belonging to completed values, bounding the buffer.
                if self.position > self.chunk_size:
                    self.buffer, self.position = self.buffer[self.position:], 0
                return value
            except json.JSONDecodeError as error:
                if not self._fill():
                    raise MTGJSONValidationError(f"invalid or truncated JSON: {error.msg}") from error

    def object_items(self) -> Iterator[tuple[str, Any]]:
        self.char("{")
        self._space()
        if self.position < len(self.buffer) and self.buffer[self.position] == "}":
            self.position += 1; return
        while True:
            key = self.value()
            if not isinstance(key, str): raise MTGJSONValidationError("JSON object key must be text")
            self.char(":")
            yield key, self.value()
            self._space()
            if self.position >= len(self.buffer) and not self._fill():
                raise MTGJSONValidationError("truncated JSON object")
            marker = self.buffer[self.position]; self.position += 1
            if marker == "}": return
            if marker != ",": raise MTGJSONValidationError("expected ',' while streaming JSON")


class StreamingMTGJSONPlanner:
    """Create deterministic per-set candidate shards and compact indexes."""

    def __init__(self, root: Path | str, *, batch_size: int = 1000,
                 targets: Iterable[str] = (), checkpoint_every: int = 1) -> None:
        self.root = Path(root)
        self.batch_size = batch_size
        self.targets = tuple(sorted({x.strip().casefold() for x in targets if x.strip()}))
        self.checkpoint_every = max(1, checkpoint_every)

    def plan(self, source: Path | str, expected_sha256: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        path = Path(source)
        source_hash = sha256_file(path)
        with path.open("rb") as source_probe:
            source_is_compressed = source_probe.read(2) == b"\x1f\x8b"
        if expected_sha256 and source_hash != expected_sha256.casefold():
            raise ValueError("SHA-256 mismatch before streaming parse")
        work = self.root / "streaming" / source_hash
        work.mkdir(parents=True, exist_ok=True)
        shards, findings = work / "candidate-shards", work / "finding-shards"
        ledger_path, manifest_path = work / "completed-sets.json", work / "manifest.json"
        meta = self._meta(path)
        dataset_id = f"mtgjson-allprintings-{meta['version']}-{source_hash[:12]}"
        acquisition = AcquisitionMetadata(meta["date"], meta["date"],
                                          "local-streamed-file", f"sha256:{source_hash}")
        ledger = self._load_ledger(ledger_path, shards)
        completed = dict(ledger.get("sets", {}))
        db_path = work / "compact-index.sqlite3"
        connection = sqlite3.connect(db_path)
        self._schema(connection)
        selected, discovered, processed_cards = [], [], 0
        try:
            for ordinal, (set_key, source_set) in enumerate(self._sets(path)):
                code, name = str(source_set.get("code", "")), str(source_set.get("name", ""))
                discovered.append({"code": code, "name": name})
                if self.targets and code.casefold() not in self.targets and name.casefold() not in self.targets:
                    continue
                selected.append(code)
                unit = f"{ordinal:06d}-{code.casefold()}"
                if unit in completed:
                    continue
                document = {"meta": meta, "data": {set_key: source_set}}
                validate_document(document)
                mapped = map_dataset(document)
                candidates = [MTGJSONImportExecution._candidate(row, dataset_id,
                    f"mtgjson-allprintings-{source_hash}", acquisition) for row in mapped]
                shard_value = {"schema_version": SCHEMA, "unit": unit, "set_code": code,
                               "candidate_count": len(candidates), "candidates": candidates}
                shard_path = shards / f"{unit}.json"
                shard_hash = _atomic(shard_path, shard_value)
                self._index_set(connection, unit, source_set, candidates)
                connection.commit()
                processed_cards += len(source_set["cards"])
                completed[unit] = {"sha256": shard_hash, "path": str(shard_path),
                                   "cards": len(source_set["cards"]),
                                   "candidates": len(candidates)}
                if len(completed) % self.checkpoint_every == 0:
                    _atomic(ledger_path, {"schema_version": SCHEMA, "source_sha256": source_hash,
                                         "sets": completed})
                    checkpoint = {"schema_version": SCHEMA, "completed_sets": len(completed),
                        "latest_set_code": code, "cards_processed": sum(
                            item["cards"] for item in completed.values()),
                        "elapsed_seconds": round(time.perf_counter() - started, 3),
                        "peak_memory_mib_observed": round(
                            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)}
                    _atomic(work / "performance-checkpoints" / "latest.json", checkpoint)
                    print(deterministic_json(checkpoint), file=sys.stderr, flush=True)
                del document, mapped, candidates, source_set
        finally:
            connection.commit()
        if self.targets:
            missing = sorted(set(self.targets) - {x["code"].casefold() for x in discovered}
                             - {x["name"].casefold() for x in discovered})
            if missing:
                connection.close()
                raise ValueError("target set names or codes were not discovered: " + ", ".join(missing))
        _atomic(ledger_path, {"schema_version": SCHEMA, "source_sha256": source_hash,
                             "sets": completed})
        finding_summary, quarantined_uuids, fatal_findings = self._write_findings(connection, findings)
        if fatal_findings:
            connection.close()
            raise MTGJSONValidationError("duplicate globally unique external identifier in streaming index")
        if quarantined_uuids:
            placeholders = ",".join("?" for _ in quarantined_uuids)
            connection.execute(f"DELETE FROM candidates WHERE source_uuid IN ({placeholders})",
                               tuple(sorted(quarantined_uuids)))
            connection.commit()
            _atomic(work / "quarantine" / "records.json", {"schema_version": SCHEMA,
                "mtgjson_uuids": sorted(quarantined_uuids),
                "disposition": "excluded from every dependency-closed batch; review required"})
        batches = self._batch_index(connection, work / "batch-index.json")
        finding_references = self._finding_references(findings)
        for batch in batches:
            package_path = work / "review-indexes" / batch["batch_id"] / "review-package.json"
            _atomic(package_path, {"schema_version": SCHEMA, "review_status": "pending",
                "candidate_ids": batch["candidate_ids"],
                "acquisition_run": {"identifier_findings": finding_references},
                "note": "Candidate payloads are content-addressed shards; this package is an index."})
            batch["review_package"] = str(package_path)
        counts = dict(connection.execute("SELECT entity_type, count(*) FROM candidates GROUP BY entity_type"))
        candidate_count = sum(counts.values())
        connection.close()
        disk = sum(p.stat().st_size for p in work.rglob("*") if p.is_file())
        elapsed = max(time.perf_counter() - started, 1e-9)
        report = {"schema_version": SCHEMA, "status": "awaiting_independent_review",
                  "dataset_identifier": dataset_id, "artifact_sha256": source_hash,
                  "source_size": path.stat().st_size,
                  "compressed": source_is_compressed,
                  "target_inputs": list(self.targets), "discovered_sets": discovered,
                  "sets_processed": len(completed), "selected_set_codes": sorted(selected),
                  "cards_processed": sum(x["cards"] for x in completed.values()),
                  "printings_processed": counts.get("printing", 0), "entity_counts": counts,
                  "candidate_count": candidate_count, "eligible_count": candidate_count,
                  "rejected_count": 0, "unresolved_count": 0,
                  "quarantined_source_record_count": len(quarantined_uuids),
                  "quarantined_candidate_count": len(quarantined_uuids),
                  "identifier_finding_count": finding_summary["total"],
                  "identifier_finding_counts": finding_summary,
                  "identifier_findings": finding_references,
                  "finding_shards": self._inventory(findings), "candidate_shards": self._inventory(shards),
                  "batch_size": self.batch_size, "batch_count": len(batches), "batches": batches,
                  "batch_plan_digest": hashlib.sha256(deterministic_json([
                      {k: v for k, v in batch.items() if k != "review_package"}
                      for batch in batches]).encode()).hexdigest(),
                  "completed_units": len(completed), "remaining_units": 0,
                  "performance": {"seconds": elapsed, "cards_per_second": round(processed_cards / elapsed, 2),
                     "peak_memory_mib_observed": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
                     "working_disk_bytes": disk, "maximum_retained_set_records": 1},
                  "canonical_write": False, "promotion_performed": False,
                  "work_root": str(work), "completed_set_ledger": str(ledger_path)}
        _atomic(manifest_path, report)
        return report

    @staticmethod
    def _meta(path: Path) -> dict[str, Any]:
        with _decoded(path) as stream:
            reader = _IncrementalJSON(stream)
            meta = None
            for key, value in reader.object_items():
                if key == "meta": meta = value; break
                if key == "data": break
            if meta is None: raise MTGJSONValidationError("dataset must contain a meta object before data")
        validate_document({"meta": meta, "data": {}})
        return meta

    @staticmethod
    def _sets(path: Path) -> Iterator[tuple[str, dict[str, Any]]]:
        with _decoded(path) as stream:
            reader = _IncrementalJSON(stream)
            reader.char("{")
            while True:
                key = reader.value(); reader.char(":")
                if key == "data":
                    yield from reader.object_items()
                    return
                reader.value(); reader._space()
                if reader.position >= len(reader.buffer) and not reader._fill(): break
                marker = reader.buffer[reader.position]; reader.position += 1
                if marker == "}": break
                if marker != ",": raise MTGJSONValidationError("expected ',' before data object")
            raise MTGJSONValidationError("dataset must contain a data object")

    @staticmethod
    def _schema(db: sqlite3.Connection) -> None:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, entity_type TEXT, card_id TEXT, unit TEXT, source_uuid TEXT);
        CREATE TABLE IF NOT EXISTS identifiers(namespace TEXT, value TEXT, uuid TEXT, unit TEXT,
          set_code TEXT, set_name TEXT, collector TEXT, language TEXT, record_json TEXT,
          PRIMARY KEY(namespace,value,uuid,unit));
        """)

    @staticmethod
    def _index_set(db: sqlite3.Connection, unit: str, source_set: Mapping[str, Any],
                   candidates: list[Mapping[str, Any]]) -> None:
        db.execute("DELETE FROM candidates WHERE unit=?", (unit,))
        db.execute("DELETE FROM identifiers WHERE unit=?", (unit,))
        card_ids = {c["mapped_fields"]["card_reference"]: hashlib.sha256(
            ("card:" + c["candidate_identifier"]).encode()).hexdigest()
            for c in candidates if c["entity_type"] == "card"}
        for candidate in candidates:
            fields = candidate["mapped_fields"]
            cid = card_ids.get(str(fields.get("card_reference", "")).casefold())
            source_uuid = fields.get("uuid") or fields.get("printing_uuid")
            db.execute("INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?)",
                       (candidate["candidate_identifier"], candidate["entity_type"], cid, unit, source_uuid))
        for card in source_set["cards"]:
            record = {"mtgjson_uuid": card["uuid"].casefold(), "card_name": card["name"],
                      "set_code": source_set["code"].casefold(), "set_name": source_set["name"],
                      "collector_number": card["number"], "language": card.get("language", "English")}
            for namespace, value in card.get("identifiers", {}).items():
                db.execute("INSERT INTO identifiers VALUES(?,?,?,?,?,?,?,?,?)", (namespace,
                    value.casefold(), record["mtgjson_uuid"], unit, record["set_code"], record["set_name"],
                    record["collector_number"], record["language"], deterministic_json(record)))

    @staticmethod
    def _load_ledger(path: Path, shards: Path) -> dict[str, Any]:
        if not path.exists():
            return {"sets": {}}
        value = json.loads(path.read_text())
        for unit, item in value.get("sets", {}).items():
            shard = shards / f"{unit}.json"
            if not shard.is_file() or hashlib.sha256(shard.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"corrupted retained candidate shard: {unit}")
        return value

    @staticmethod
    def _write_findings(db: sqlite3.Connection, root: Path) -> tuple[dict[str, Any], set[str], int]:
        rows = db.execute("SELECT namespace,value,count(*) FROM identifiers GROUP BY namespace,value HAVING count(*)>1 ORDER BY namespace,value")
        by_namespace: dict[str, int] = {}; total = fatal = 0; quarantined: set[str] = set()
        for namespace, value, count in rows:
            policy = IDENTIFIER_POLICY.get(namespace, {"provider": namespace, "scope": "not-guaranteed", "uniqueness": "not-guaranteed"})
            if policy["uniqueness"] == "scoped": continue
            affected = [json.loads(x[0]) for x in db.execute(
                "SELECT record_json FROM identifiers WHERE namespace=? AND value=? ORDER BY unit,uuid", (namespace, value))]
            same = len({(x["set_code"], x["collector_number"], x["language"]) for x in affected}) == 1
            quarantine = policy["uniqueness"] == "strict" and same
            finding = {"severity": "review-required" if quarantine or policy["uniqueness"] != "strict" else "error",
                "identifier_namespace": namespace, "identifier_value": value, "scope": policy["scope"],
                "provider": policy["provider"], "collision_count": count,
                "affected_source_records": affected,
                "disposition": "quarantine affected source-record dependency closure; require review" if quarantine else "preserve all references; require review before any unique mapping"}
            _atomic(root / f"{total:08d}-{hashlib.sha256((namespace+value).encode()).hexdigest()[:12]}.json", finding)
            total += 1; fatal += int(finding["severity"] == "error")
            if quarantine: quarantined.update(x["mtgjson_uuid"] for x in affected)
            by_namespace[namespace] = by_namespace.get(namespace, 0) + 1
        return ({"total": total, "by_namespace": by_namespace,
                 "by_severity": {"review-required": total - fatal, "error": fatal}},
                quarantined, fatal)

    def _batch_index(self, db: sqlite3.Connection, path: Path) -> list[dict[str, Any]]:
        groups: dict[str, list[str]] = {}
        for identifier, kind, card_id in db.execute("SELECT id,entity_type,card_id FROM candidates ORDER BY id"):
            key = hashlib.sha256(("card:" + identifier).encode()).hexdigest() if kind == "card" else card_id
            groups.setdefault(key or identifier, []).append(identifier)
        batches, current = [], []
        for key in sorted(groups):
            group = sorted(groups[key])
            if current and len(current) + len(group) > self.batch_size:
                batches.append(current); current = []
            current.extend(group)
        if current: batches.append(current)
        result = [{"batch_id": f"batch-{i:06d}-{hashlib.sha256(deterministic_json(ids).encode()).hexdigest()[:12]}",
                   "entity_count": len(ids), "candidate_ids": ids} for i, ids in enumerate(batches, 1)]
        _atomic(path, {"schema_version": SCHEMA, "batches": result})
        return result

    @staticmethod
    def _inventory(root: Path) -> list[dict[str, Any]]:
        return [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "byte_length": path.stat().st_size} for path in sorted(root.glob("*.json"))]

    @staticmethod
    def _finding_references(root: Path) -> list[dict[str, Any]]:
        references = []
        for path in sorted(root.glob("*.json")):
            value = json.loads(path.read_text())
            references.append({"identifier_namespace": value["identifier_namespace"],
                "identifier_value": value["identifier_value"], "severity": value["severity"],
                "disposition": value["disposition"], "collision_count": value["collision_count"],
                "detail_path": str(path), "detail_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        return references
