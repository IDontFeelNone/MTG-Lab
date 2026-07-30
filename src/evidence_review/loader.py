"""Safe loading of an external evidence handoff without interpreting its claims."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class HandoffLoadError(ValueError):
    """Raised when a handoff manifest cannot be safely loaded."""


@dataclass(frozen=True, slots=True)
class EvidenceHandoff:
    """A parsed handoff manifest and its readable, bundle-contained artifact bytes."""

    root: Path
    manifest: Mapping[str, Any]
    artifact_content: Mapping[str, bytes]
    load_errors: tuple[str, ...]


def load_handoff(path: Path | str) -> EvidenceHandoff:
    """Load ``manifest.json`` (or an explicit manifest path) and contained artifacts.

    Artifact failures are retained as review findings rather than aborting the review.
    This allows an incomplete or damaged handoff to receive a deterministic report.
    """
    supplied = Path(path)
    manifest_path = supplied / "manifest.json" if supplied.is_dir() else supplied
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HandoffLoadError(f"Handoff manifest not found: {manifest_path}") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HandoffLoadError(f"Handoff manifest is not readable JSON: {manifest_path}") from error
    if not isinstance(manifest, dict):
        raise HandoffLoadError("Handoff manifest must be a JSON object")

    root = manifest_path.parent.resolve()
    content: dict[str, bytes] = {}
    errors: list[str] = []
    artifacts = manifest.get("artifacts", [])
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            artifact_id = artifact.get("id")
            relative = artifact.get("path")
            if not isinstance(artifact_id, str) or not isinstance(relative, str):
                continue
            artifact_path = root / relative
            resolved = artifact_path.resolve()
            if not resolved.is_relative_to(root):
                errors.append(f"artifact[{index}] path escapes the handoff: {relative}")
                continue
            try:
                content[artifact_id] = resolved.read_bytes()
            except OSError:
                errors.append(f"artifact {artifact_id} is missing or unreadable: {relative}")
    return EvidenceHandoff(root, manifest, content, tuple(sorted(errors)))


__all__ = ["EvidenceHandoff", "HandoffLoadError", "load_handoff"]
