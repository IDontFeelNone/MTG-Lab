"""Validated JSON and Markdown rendering for evidence review reports."""

from __future__ import annotations

import json
from typing import Any, Mapping

from validation import validate_document


def validate_report(report: Mapping[str, Any]) -> None:
    """Validate a report against its declared versioned schema."""
    version = report.get("schema_version")
    if not isinstance(version, str):
        raise ValueError("Review report has no schema_version")
    validate_document(report, "evidence-review-report", version)


def render_json_report(report: Mapping[str, Any]) -> str:
    """Render stable machine-readable JSON after schema validation."""
    validate_report(report)
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def render_markdown_report(report: Mapping[str, Any]) -> str:
    """Render a stable human-readable summary after schema validation."""
    validate_report(report)
    lines = [
        f"# Evidence Review: {report['handoff_id']}", "",
        f"**Recommendation:** {report['recommendation']}",
        f"**Completeness score:** {report['completeness_score']}%", "",
        "## Evidence inventory", "",
        "| Artifact | Media type | Integrity | Sources |", "| --- | --- | --- | --- |",
    ]
    for item in report["evidence_inventory"]:
        integrity = "verified" if item["integrity_verified"] else "failed"
        lines.append(f"| `{item['id']}` | {item['media_type']} | {integrity} | {', '.join(item['source_ids'])} |")
    for title, key in (
        ("Supported claims", "supported_claims"),
        ("Unsupported claims", "unsupported_claims"),
        ("Missing evidence", "missing_evidence"),
        ("Orphaned artifacts", "orphaned_artifacts"),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- `{value}`" for value in report[key])
        if not report[key]:
            lines.append("- None")
    lines.extend(["", "## Provenance summary", "",
                  f"- Declared sources: {report['provenance_summary']['declared_source_count']}",
                  "- Referenced sources: " + (", ".join(report["provenance_summary"]["referenced_source_ids"]) or "None"),
                  "", "## Conflicts, duplicates, and validation findings", ""])
    issues = ([f"Conflict on `{item['topic']}`: {', '.join(item['claim_ids'])}" for item in report["conflicting_claims"]]
              + [f"Duplicate {item['field']}: {', '.join(item['artifact_ids'])}" for item in report["duplicate_artifacts"]]
              + [f"{item['code']}: {item['detail']}" for item in report["validation_findings"]])
    lines.extend(f"- {issue}" for issue in issues)
    if not issues:
        lines.append("- None")
    return "\n".join(lines) + "\n"


__all__ = ["render_json_report", "render_markdown_report", "validate_report"]
