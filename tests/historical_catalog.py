"""Explicit, integrity-bound original catalog for historical replay tests only.

Current-state tests and production consumers must keep using their requested data
root. This fixture never changes a caller's root or catches snapshot mismatches.
The frozen canonical bytes are separate from the checkout's mutable catalog;
unchanged historical evidence is copied only after verifying its retained pins.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

REPOSITORY = Path(__file__).resolve().parents[1]
FIXTURE = REPOSITORY / "tests/fixtures/historical_catalog"
MANIFEST_SHA256 = "ac3ce95f6f9a10cefd2c04afd6a08eb5343f5ef5931508d16c12885f3a45f25a"
_temporary = None


def _verified(raw, ref, name):
    if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError(f"historical fixture integrity mismatch: {name}")
    return raw


@lru_cache(maxsize=1)
def historical_repository():
    """Materialize the named original snapshot, never the current canonical data."""
    global _temporary
    raw = (FIXTURE / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("historical fixture manifest integrity mismatch")
    manifest = json.loads(raw)
    archive = FIXTURE / "canonical-3bf4cc27.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["canonical_archive_sha256"]:
        raise ValueError("historical canonical archive integrity mismatch")
    _temporary = tempfile.TemporaryDirectory(prefix="mtglab-historical-replay-")
    root = Path(_temporary.name)
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
    for name in ("src", "scripts", "tests", "reference-reviews", ".github"):
        (root / name).symlink_to(REPOSITORY / name, target_is_directory=True)
    from production_evidence.promotion_readiness import canonical_state_digest
    if canonical_state_digest(root / "data") != manifest["canonical_snapshot_digest"]:
        raise ValueError("historical canonical snapshot mismatch")
    return root


def historical_data():
    return historical_repository() / "data"


def bind_replay_builder(test_case, module):
    """Scope an existing retained-artifact builder to its original test fixture.

    Only the builder's existing path constants change, under unittest cleanup;
    query, acquisition, authorization and validation results are never mocked.
    """
    from unittest.mock import patch
    root = historical_repository()
    original = module.ROOT
    for name in ("ROOT", "REVIEW", "IMPORT", "ASSESSMENTS"):
        value = getattr(module, name, None)
        if isinstance(value, Path) and value.is_relative_to(original):
            scoped = patch.object(module, name, root / value.relative_to(original))
            scoped.start()
            test_case.addClassCleanup(scoped.stop)
