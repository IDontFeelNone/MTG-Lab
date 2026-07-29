"""Deterministic SHA-256 hashing for acquired evidence."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import HashingError

_SHA256_CHUNK_SIZE = 1024 * 1024


def hash_bytes(content: bytes) -> str:
    """Return the lowercase SHA-256 digest of immutable byte content."""
    return hashlib.sha256(content).hexdigest()


def hash_file(path: Path, *, chunk_size: int = _SHA256_CHUNK_SIZE) -> str:
    """Return the lowercase SHA-256 digest of a file read in bounded chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    try:
        digest = hashlib.sha256()
        with Path(path).open("rb") as evidence_file:
            for chunk in iter(lambda: evidence_file.read(chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise HashingError("Unable to hash evidence file", context={"path": str(path)}) from error
