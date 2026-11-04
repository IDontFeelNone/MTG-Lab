"""Public read-only route to the owning historical admission verifier.

This does not promote records or infer current identifier/production authority.
The caller selects an independently pinned existing audit and exact namespaces.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .engine import _historical_admission_records, _retained_path, ProjectionValidationError

AUDIT_SHA256 = '1abdf8da7188d0ad24c234237dcd3827de38ec631ab6b411f06c1455c127021d'
PAYLOAD_SHA256 = '007e69530bac92de3794089623f6fa1610f374ceb4f8f3c75a96502ddc6fba1d'
PRINTING_IDS = frozenset((
    '7d33713f-d665-53c5-b64c-6f231f87da02', '6c27e26c-a874-5c4d-99eb-ee4631b5bb0c',
    'c5303dc2-a1e9-595c-a64c-dff67a63c2a5', '6c3d86fb-e909-5234-be5d-52ba8b0983b4',
    'ba922209-7f94-5910-a92f-1053503c90dd', 'e1a2139f-241f-59a3-86d6-4f3c070b52a8'))


@dataclass(frozen=True, init=False)
class HistoricalAdmissionEvidence:
    _records: bytes

    def record(self, entity_type, identifier):
        records = json.loads(self._records)
        if type(entity_type) is not str or type(identifier) is not str or entity_type != 'printing' or identifier not in PRINTING_IDS:
            raise ProjectionValidationError('exact historical entity type and ID required')
        if entity_type not in records or identifier not in records[entity_type]:
            raise ProjectionValidationError('historical correspondence not established')
        return records[entity_type][identifier]


def load_historical_admission(*, data_root, audit_reference, expected_audit_sha256,
        expected_payload_sha256):
    """Validate original payload/preflight/review/lineage through its owner.

    Privately own independently decoded views. A digest is an integrity pin,
    additional to the actual owning verifier, not an admission substitute.
    """
    if expected_audit_sha256 != AUDIT_SHA256 or expected_payload_sha256 != PAYLOAD_SHA256:
        raise ProjectionValidationError('exact approved six-land historical evidence pins required')
    root = Path(data_root).absolute()
    path = _retained_path(root, audit_reference)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ProjectionValidationError('symlink historical evidence forbidden')
    raw = path.read_bytes()
    if len(raw) > 1048576 or hashlib.sha256(raw).hexdigest() != expected_audit_sha256:
        raise ProjectionValidationError('exact historical audit integrity required')
    # The independent raw pin also rejects duplicate-key rewrites. The owner
    # verifies the complete original source-to-record preflight, not just IDs.
    from production_evidence import bounded_promotion as first
    payload_path = _retained_path(root, f'production_runs/{first.EVIDENCE_ID}/review_payloads/mb2/{first.BATCH_ID}.json')
    if any(p.is_symlink() for p in (payload_path, *payload_path.parents)):
        raise ProjectionValidationError('symlink historical payload forbidden')
    payload_raw = payload_path.read_bytes()
    if len(payload_raw) > 8388608 or hashlib.sha256(payload_raw).hexdigest() != expected_payload_sha256:
        raise ProjectionValidationError('exact historical payload integrity required')
    records = _historical_admission_records(root, json.loads(raw))
    if path.read_bytes() != raw or payload_path.read_bytes() != payload_raw:
        raise ProjectionValidationError('historical audit changed during admission')
    records = {'printing': {pid: records['printing'][pid] for pid in sorted(PRINTING_IDS)}}
    result = object.__new__(HistoricalAdmissionEvidence)
    object.__setattr__(result, '_records', json.dumps(records, sort_keys=True,
        separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
    return result
