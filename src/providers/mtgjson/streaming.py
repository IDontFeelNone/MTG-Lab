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
        shard_inventory = self._inventory(shards)
        for batch in batches:
            batch_root = work / "review-batches" / batch["target_set_code"] / batch["batch_id"]
            payloads = [item for item in shard_inventory
                        if Path(item["path"]).stem == batch["source_unit"]]
            if not payloads:
                raise ValueError(f"missing candidate payload for batch {batch['batch_id']}")
            ids_path = batch_root / "candidate-ids.json"
            _atomic(ids_path, {"schema_version": SCHEMA,
                "target_set_code": batch["target_set_code"],
                "target_set_name": batch["target_set_name"],
                "candidate_ids": batch["candidate_ids"],
                "candidate_id_digest": batch["candidate_id_digest"]})
            closure_path = batch_root / "dependency-closure.json"
            _atomic(closure_path, {"schema_version": SCHEMA, "valid": True,
                "target_set_code": batch["target_set_code"],
                "candidate_ids": batch["candidate_ids"],
                "dependency_closure_digest": batch["dependency_closure_digest"],
                "rule": "each Printing and its Card remain in this exact target-only batch"})
            package_body = {"schema_version": SCHEMA, "review_status": "pending",
                "target_set_code": batch["target_set_code"],
                "target_set_name": batch["target_set_name"],
                "candidate_ids": batch["candidate_ids"],
                "candidate_id_digest": batch["candidate_id_digest"],
                "dependency_closure_digest": batch["dependency_closure_digest"],
                "candidate_counts_by_entity_type": batch["entity_counts"],
                "candidate_payload_references": payloads,
                "candidate_id_list": str(ids_path),
                "dependency_closure_report": str(closure_path),
                "source_lineage": {"dataset_identifier": dataset_id,
                    "source_sha256": source_hash, "source_version": meta["version"],
                    "source_date": meta["date"], "source_set_unit": batch["source_unit"]},
                "excluded_candidates": {"quarantined": sorted(quarantined_uuids),
                    "rejected": [], "unresolved": [], "unsupported": []},
                "identifier_findings": finding_references,
                "acquisition_run": {"identifier_findings": finding_references},
                "quarantine_references": ([str(work / "quarantine" / "records.json")]
                    if quarantined_uuids else []),
                "explicit_unknowns": [], "validation_state": "valid_pending_review",
                "confidence": "provider_asserted_pending_independent_review",
                "provenance": {"provider": "MTGJSON", "artifact_sha256": source_hash},
                "canonical_write": False, "promotion_performed": False,
                "approval_fields": {"independent_reviewer_identity": None,
                    "immutable_review_reference": None, "reviewed_timestamp": None,
                    "approved_candidate_ids": None, "excluded_candidate_ids": None,
                    "approval_decision": None, "reviewer_notes": None,
                    "reviewed_package_digest": None}}
            package_id = "review-" + hashlib.sha256(deterministic_json({
                "source_sha256": source_hash, "target_set_code": batch["target_set_code"],
                "candidate_id_digest": batch["candidate_id_digest"],
                "dependency_closure_digest": batch["dependency_closure_digest"]}).encode()).hexdigest()
            package = {**package_body, "review_package_identifier": package_id}
            package_path = batch_root / "review-package.json"
            package_digest = _atomic(package_path, package)
            manifest_body = {"schema_version": SCHEMA, **batch,
                "candidate_payload_references": payloads, "candidate_id_list": str(ids_path),
                "dependency_closure_report": str(closure_path),
                "review_package": str(package_path), "review_package_identifier": package_id,
                "review_package_sha256": package_digest, "canonical_write": False,
                "promotion_performed": False}
            manifest_path_for_batch = batch_root / "manifest.json"
            _atomic(manifest_path_for_batch, manifest_body)
            batch.update({"candidate_payload_references": payloads,
                "candidate_id_list": str(ids_path), "dependency_closure_report": str(closure_path),
                "review_package": str(package_path), "review_package_identifier": package_id,
                "batch_manifest": str(manifest_path_for_batch)})
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
                  "finding_shards": self._inventory(findings), "candidate_shards": shard_inventory,
                  "batch_size": self.batch_size, "batch_count": len(batches), "batches": batches,
                  "batch_plan_digest": hashlib.sha256(deterministic_json([{
                      key: batch[key] for key in ("batch_id", "target_set_code", "target_set_name",
                          "entity_count", "entity_counts", "candidate_ids", "candidate_id_digest",
                          "dependency_closure_digest")}
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
    def verify_batch(batch: Mapping[str, Any]) -> dict[str, Any]:
        """Independently verify the retained, target-specific review boundary."""
        required = ("target_set_code", "target_set_name", "candidate_ids",
                    "candidate_id_digest", "dependency_closure_digest",
                    "candidate_payload_references", "candidate_id_list",
                    "dependency_closure_report", "review_package", "batch_manifest")
        missing = [key for key in required if not batch.get(key)]
        if missing:
            raise ValueError("incomplete retained batch: " + ", ".join(missing))
        ids = batch["candidate_ids"]
        digest = hashlib.sha256(deterministic_json(ids).encode()).hexdigest()
        if digest != batch["candidate_id_digest"]:
            raise ValueError("candidate-ID digest mismatch")
        paths = [batch["candidate_id_list"], batch["dependency_closure_report"],
                 batch["review_package"], batch["batch_manifest"]]
        paths.extend(item["path"] for item in batch["candidate_payload_references"])
        if any(not Path(path).is_file() for path in paths):
            raise ValueError("missing candidate payload or review package retained artifact")
        payload_candidates = []
        payload_codes = set()
        for reference in batch["candidate_payload_references"]:
            path = Path(reference["path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
                raise ValueError("candidate payload digest mismatch")
            payload = json.loads(path.read_text())
            payload_codes.add(payload["set_code"])
            payload_candidates.extend(x["candidate_identifier"] for x in payload["candidates"])
        if payload_codes != {batch["target_set_code"]}:
            raise ValueError("cross-target contamination in retained batch")
        if not set(ids).issubset(payload_candidates):
            raise ValueError("candidate payload does not contain every batch candidate")
        package = json.loads(Path(batch["review_package"]).read_text())
        if package.get("review_status") != "pending" or package.get("candidate_ids") != ids:
            raise ValueError("review package is missing, altered, or not pending")
        if package.get("target_set_code") != batch["target_set_code"]:
            raise ValueError("cross-target contamination in review package")
        closure = json.loads(Path(batch["dependency_closure_report"]).read_text())
        if not closure.get("valid") or closure.get("candidate_ids") != ids:
            raise ValueError("dependency closure is invalid")
        return {"schema_version": SCHEMA, "valid": True,
                "batch_id": batch["batch_id"], "target_set_code": batch["target_set_code"],
                "candidate_id_digest": digest, "canonical_write": False,
                "promotion_performed": False}

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
        CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, entity_type TEXT, card_id TEXT, unit TEXT, source_uuid TEXT,
          set_code TEXT, set_name TEXT);
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
            db.execute("INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,?,?)",
                       (candidate["candidate_identifier"], candidate["entity_type"], cid, unit,
                        source_uuid, source_set["code"], source_set["name"]))
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
        groups: dict[tuple[str, str, str, str], list[tuple[str, str]]] = {}
        for identifier, kind, card_id, unit, code, name in db.execute(
                "SELECT id,entity_type,card_id,unit,set_code,set_name FROM candidates ORDER BY set_code,id"):
            key = hashlib.sha256(("card:" + identifier).encode()).hexdigest() if kind == "card" else card_id
            groups.setdefault((code, name, unit, key or identifier), []).append((identifier, kind))
        batches: list[tuple[str, str, str, list[tuple[str, str]]]] = []
        for code, name, unit in sorted({key[:3] for key in groups}):
            current: list[tuple[str, str]] = []
            for key in sorted(k for k in groups if k[:3] == (code, name, unit)):
                group = sorted(groups[key])
                if current and len(current) + len(group) > self.batch_size:
                    batches.append((code, name, unit, current)); current = []
                current.extend(group)
            if current: batches.append((code, name, unit, current))
        result = []
        for i, (code, name, unit, members) in enumerate(batches, 1):
            ids = [x[0] for x in members]
            digest = hashlib.sha256(deterministic_json(ids).encode()).hexdigest()
            entity_counts: dict[str, int] = {}
            for _, kind in members: entity_counts[kind] = entity_counts.get(kind, 0) + 1
            result.append({"batch_id": f"{code.casefold()}-batch-{i:06d}-{digest[:12]}",
                "target_set_code": code, "target_set_name": name, "source_unit": unit,
                "entity_count": len(ids), "entity_counts": entity_counts,
                "candidate_ids": ids, "candidate_id_digest": digest,
                "dependency_closure_digest": hashlib.sha256(
                    deterministic_json({"target_set_code": code, "candidate_ids": ids}).encode()).hexdigest()})
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
