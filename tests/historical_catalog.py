"""Explicit, integrity-bound original catalog for historical replay tests only.

Current-state tests and production consumers must keep using their requested data
root. This fixture never changes a caller's root or catches snapshot mismatches.
The frozen canonical bytes are separate from the checkout's mutable catalog;
unchanged historical evidence is copied only after verifying its retained pins.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

REPOSITORY = Path(__file__).resolve().parents[1]
FIXTURE = REPOSITORY / "tests/fixtures/historical_catalog"
MANIFEST_SHA256 = "ac3ce95f6f9a10cefd2c04afd6a08eb5343f5ef5931508d16c12885f3a45f25a"
AUXILIARY_ROOT = REPOSITORY / "tests/fixtures/historical_replay"
AUXILIARY_MANIFESTS = {
    "card-acquisition-pilot": "360d732fa3ec9d4b784eef9c25f4afbec9c645cb7b983c34e25e0b4b248e85d7",
}
_temporaries = []


def _verified(raw, ref, name):
    if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError(f"historical fixture integrity mismatch: {name}")
    return raw


def _relative_path(name, allowed_roots):
    relative = PurePosixPath(name)
    if (not relative.parts or relative.is_absolute() or ".." in relative.parts
            or "\\" in name or ":" in name or relative.as_posix() != name
            or relative.parts[0] not in allowed_roots):
        raise ValueError("historical auxiliary path escape")
    return relative


def _auxiliary_path(root, name):
    relative = _relative_path(name, {"docs", "config"})
    for count in range(1, len(relative.parts) + 1):
        if root.joinpath(*relative.parts[:count]).is_symlink():
            raise ValueError("historical auxiliary symlink")
    return root.joinpath(*relative.parts)


def _auxiliary_files(fixture):
    if fixture is None:
        return ()
    if fixture not in AUXILIARY_MANIFESTS:
        raise ValueError("unknown historical auxiliary fixture")
    directory = AUXILIARY_ROOT / fixture
    if AUXILIARY_ROOT.is_symlink() or directory.is_symlink() or (directory / "manifest.json").is_symlink():
        raise ValueError("historical auxiliary symlink")
    raw = (directory / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != AUXILIARY_MANIFESTS[fixture]:
        raise ValueError("historical auxiliary manifest integrity mismatch")
    manifest = json.loads(raw)
    if manifest["historical_data_manifest_sha256"] != MANIFEST_SHA256:
        raise ValueError("historical auxiliary catalog binding mismatch")
    artifact_ref = manifest["artifact_manifest"]
    artifact_path = _relative_path(artifact_ref["path"], {"data"})
    artifact_raw = (REPOSITORY / artifact_path).read_bytes()
    if hashlib.sha256(artifact_raw).hexdigest() != artifact_ref["sha256"]:
        raise ValueError("historical auxiliary artifact binding mismatch")
    artifact = json.loads(artifact_raw)
    if (artifact["canonical_main_baseline"] != manifest["original_revision"]
            or artifact["protected_inventory"]["content_identity"] != manifest["protected_inventory_identity"]):
        raise ValueError("historical auxiliary baseline mismatch")
    return tuple((name, _verified(_auxiliary_path(directory, name).read_bytes(), ref, name))
                 for name, ref in sorted(manifest["files"].items()))


def historical_repository(*, auxiliary_fixture=None):
    """Select explicit historical dependencies; default replay roots stay unchanged.

    Auxiliary bytes are reverified even when their materialized root is cached.
    Missing/altered fixtures never fall back to current docs or live Git.
    """
    return _materialize_repository(_auxiliary_files(auxiliary_fixture))


@lru_cache(maxsize=2)
def _materialize_repository(auxiliary_files):
    """Materialize frozen data and only the explicitly bound auxiliary files."""
    raw = (FIXTURE / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("historical fixture manifest integrity mismatch")
    manifest = json.loads(raw)
    archive = FIXTURE / "canonical-3bf4cc27.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["canonical_archive_sha256"]:
        raise ValueError("historical canonical archive integrity mismatch")
    temporary = tempfile.TemporaryDirectory(prefix="mtglab-historical-replay-")
    _temporaries.append(temporary)
    root = Path(temporary.name)
    with zipfile.ZipFile(archive) as source:
        expected = {name for name, ref in manifest["files"].items()
                    if ref["storage"] == "frozen-canonical"}
        if set(source.namelist()) != expected or len(source.namelist()) != len(expected):
            raise ValueError("historical canonical archive inventory mismatch")
        for name, ref in manifest["files"].items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "data":
                raise ValueError("historical fixture path escape")
            raw = source.read(name) if name in expected else (REPOSITORY / name).read_bytes()
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_verified(raw, ref, name))
    # Code remains current; only the explicitly selected replay data is frozen.
    for name in ("config", "docs"):
        shutil.copytree(REPOSITORY / name, root / name)
    for name, raw in auxiliary_files:
        destination = _auxiliary_path(root, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    for name in ("src", "scripts", "tests", "reference-reviews", ".github"):
        (root / name).symlink_to(REPOSITORY / name, target_is_directory=True)
    from production_evidence.promotion_readiness import canonical_state_digest
    if canonical_state_digest(root / "data") != manifest["canonical_snapshot_digest"]:
        raise ValueError("historical canonical snapshot mismatch")
    return root


def historical_data():
    return historical_repository() / "data"


def bind_replay_builder(test_case, module, *, auxiliary_fixture=None):
    """Scope an existing retained-artifact builder to its original test fixture.

    Only the builder's existing path constants change, under unittest cleanup;
    query, acquisition, authorization and validation results are never mocked.
    """
    from unittest.mock import patch
    root = historical_repository(auxiliary_fixture=auxiliary_fixture)
    original = module.ROOT
    for name in ("ROOT", "REVIEW", "IMPORT", "ASSESSMENTS"):
        value = getattr(module, name, None)
        if isinstance(value, Path) and value.is_relative_to(original):
            scoped = patch.object(module, name, root / value.relative_to(original))
            scoped.start()
            test_case.addClassCleanup(scoped.stop)
