"""Private, manually supplied MTGJSON import through the owning reconciler.

No network, canonical writes, source copies, external exports or policy-file loader.
"""
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urlsplit

from .private_policy import PrivateResearchProfile, SourcePolicyError, RETENTION, digest
from .reconciliation import reconcile_release

CONTROL_BYTES = 64 * 1024


def _require(condition, message):
    if not condition:
        raise SourcePolicyError(message)


def _private_path(path):
    path = Path(path).absolute()
    _require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink input refused')
    _require(not any((p / '.git').is_file() or (p / '.git' / 'HEAD').is_file()
                     for p in path.parents), 'private input must be outside Git')
    _require(path.is_file() and path.stat().st_mode & 0o077 == 0, 'owner-only private input required')
    return path


def _control(path, expected):
    path = _private_path(path)
    _require(path.stat().st_size <= CONTROL_BYTES, 'control artifact exceeds byte bound')
    raw = path.read_bytes()
    _require(len(raw) <= CONTROL_BYTES and digest(raw) == expected, 'control artifact integrity mismatch')
    return raw


def import_private_release(source, workspace, *, profile, provenance, notice,
                           limits=None, stop_after_partitions=None):
    """Return deterministic private candidates; never establish legal clearance.

    ``profile`` must come from reviewed trusted-host code, not imported JSON.
    Provenance and notice digests must be independently pinned by that host.
    Retained-source remains the default. Explicit factual limited retention
    publishes a cleanup-eligible receipt; this API never copies/deletes the source.
    """
    _require(type(profile) is PrivateResearchProfile, 'trusted-host profile required')
    profile.require_supported()  # Refuse BEFORE reading even provenance or source files.
    try:
        raw = _control(provenance, profile.provenance_sha256)
        # Controls are small and pinned; reject duplicate keys nonetheless.
        def unique(pairs):
            result = {}
            for key, value in pairs:
                _require(key not in result, 'duplicate provenance key')
                result[key] = value
            return result
        facts = json.loads(raw, object_pairs_hook=unique)
        release = json.loads(profile.release_json)
        _require(type(facts) is dict and set(facts) == {'provider', 'release_id', 'version', 'date',
            'artifact_sha256', 'source_url', 'acquired_at', 'acquisition_method'}, 'closed provenance required')
        _require(all(facts[k] == release[k] for k in ('provider', 'release_id', 'version', 'date',
            'artifact_sha256')), 'provenance release mismatch')
        _require(facts['acquisition_method'] == 'MANUALLY_SUPPLIED', 'manual source acquisition required')
        _require(type(facts['acquired_at']) is str and facts['acquired_at'].endswith('Z'), 'UTC acquisition time required')
        datetime.fromisoformat(facts['acquired_at'][:-1] + '+00:00')
        url = urlsplit(facts['source_url'])
        if profile.material == 'MIXED_MTGJSON_RELEASE':
            _require(url.scheme == 'https' and url.hostname in ('mtgjson.com', 'data.mtgjson.com')
                and url.port in (None, 443) and not url.username and not url.password
                and not url.fragment and not url.query, 'official source provenance required')
        else:
            _require(facts['source_url'].startswith('urn:mtglab:original:'), 'original fixture provenance required')
        _require(bool(_control(notice, profile.notice_sha256).strip()), 'retained notice required')
        source = _private_path(source)
        if profile.retention_profile == RETENTION and profile.retention_mode == 'limited-retention':
            # The reconciler rebuilds output/. Never consume the custodian's only
            # controls from a location that this import may legitimately replace.
            root = Path(workspace).resolve()
            _require(all(root != Path(p).resolve() and root not in Path(p).resolve().parents
                         for p in (provenance, notice)), 'factual controls must remain outside rebuildable workspace')
    except SourcePolicyError:
        raise
    except (ValueError, TypeError, OSError, RecursionError, KeyError, RuntimeError):
        raise SourcePolicyError('invalid private provenance or notice') from None
    result = reconcile_release(source, workspace, release, authorize_source=profile,
        retention_profile=profile.retention_profile, source_use_receipt=profile.receipt(),
        limits=limits, stop_after_partitions=stop_after_partitions)
    if (profile.retention_profile == RETENTION and profile.retention_mode == 'limited-retention'
            and result['status'] == 'CANDIDATES_PREPARED'):
        from .factual_retention import publish_factual_results
        publish_factual_results(workspace, profile=profile, expected_report_id=result['report_id'],
                                provenance=provenance, notice=notice)
    return result
