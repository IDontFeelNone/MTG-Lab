"""Actual public handoff rejection and valid-report preservation regressions."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evidence_review import (EvidenceHandoff, HandoffLoadError, load_handoff,
    render_json_report, render_markdown_report, review_handoff,
    validate_report)
from evidence_review.validator import validate_handoff
import test_evidence_review as original


def malformed_cases():
    """Each mutation is JSON data, not authenticated evidence or source authority."""
    cases = []
    for name in ('sources', 'artifacts', 'required_artifact_ids', 'claims'):
        for label, value in [('null', None), ('string', 'capture'), ('object', {}),
                             ('integer', 1), ('boolean', True)]:
            cases.append((name + '-' + label, (name,), value))
        for label, value in [('null-item', None), ('string-item', 'capture'),
                             ('object-item', {}), ('array-item', []), ('number-item', 3)]:
            # A string is valid in required_artifact_ids; use an invalid identifier.
            if name == 'required_artifact_ids' and label == 'string-item': value = 'INVALID ID'
            cases.append((name + '-' + label, (name,), [value]))
    for path in [('artifacts', 0, 'source_ids'), ('claims', 0, 'artifact_ids'),
                 ('claims', 0, 'source_ids')]:
        for label, value in [('null', None), ('string', 'capture'), ('object', {}),
                             ('integer', 1), ('boolean', False), ('null-item', [None]),
                             ('object-item', [{}]), ('array-item', [[]]),
                             ('mixed-item', ['capture', 1]), ('invalid-id', ['INVALID ID'])]:
            cases.append(('.'.join(map(str, path)) + '-' + label, path, value))
    for path in [('id',), ('sources', 0, 'id'), ('artifacts', 0, 'id'), ('claims', 0, 'id')]:
        for label, value in [('null', None), ('array', []), ('object', {}),
                             ('integer', 2), ('empty', ''), ('invalid', 'INVALID ID')]:
            cases.append(('.'.join(map(str, path)) + '-' + label, path, value))
    for path, value in [(('title',), None), (('created_at',), None),
                        (('sources', 0, 'reference'), {}), (('sources', 0, 'retrieved_at'), False),
                        (('artifacts', 0, 'path'), []), (('artifacts', 0, 'media_type'), {}),
                        (('artifacts', 0, 'byte_size'), True), (('artifacts', 0, 'sha256'), []),
                        (('claims', 0, 'topic'), []), (('claims', 0, 'value'), {}),
                        (('claims', 0, 'statement'), None), (('notes',), []),
                        (('unexpected',), 'field'), (('schema_version',), None),
                        (('schema_version',), 'v999'), (('schema_version',), [])]:
        cases.append(('.'.join(map(str, path)) + '-metadata', path, value))
    return cases


def changed(manifest, path, value):
    result = copy.deepcopy(manifest); target = result
    for key in path[:-1]: target = target[key]
    target[path[-1]] = value
    return result


def fixture(root):
    path = original.EvidenceReviewTests().make_handoff(root)
    return path, json.loads(path.read_text())


def valid_cases(base):
    cases = {'complete': copy.deepcopy(base)}
    for name, path, value in [
        ('wrong-size', ('artifacts', 0, 'byte_size'), 1),
        ('wrong-digest', ('artifacts', 0, 'sha256'), '0' * 64),
        ('unknown-source', ('artifacts', 0, 'source_ids'), ['absent']),
        ('unknown-required', ('required_artifact_ids',), ['absent']),
        ('unsupported', ('claims', 0, 'artifact_ids'), ['absent']),
        ('no-claims', ('claims',), [])]:
        cases[name] = changed(base, path, value)
    duplicate = copy.deepcopy(base); duplicate['artifacts'].append(dict(base['artifacts'][0], id='copy'))
    cases['duplicate'] = duplicate
    conflict = copy.deepcopy(base); conflict['claims'].append(dict(base['claims'][0], id='claim-b', value='beta'))
    cases['conflict'] = conflict
    repeated = copy.deepcopy(base); repeated['claims'].append(copy.deepcopy(base['claims'][0]))
    cases['repeated-claim'] = repeated
    cases['missing-file'] = copy.deepcopy(base)
    return cases


# Filled from the unmodified canonical implementation before runtime edits.
VALID_REPORT_PINS = {'complete': ['52a092b809ae286c78a61faffd250c4b5660cbe6d3cc971892a9d39a53e34d43', 'e5866a674da79c2c9f4a2ad2069b4a1ee349bc7110197cbbee12634b4528560c'], 'wrong-size': ['bdfef72a5be69302380b8cdd74178c9f3e13ff5151223cb23caaf42f32d997b2', '61a301f584677f4a78cc08ee0dd2a5e8678a2a31c0ce1b36a195b78b1cccb802'], 'wrong-digest': ['f1f17bdfde1742b8ac83b282642394fd074c05927d5279481c30b22a5e4ca27e', 'f2ac8c159cc241d636bd51cd4c45c21213d53bfafc720cc1536a52630023f016'], 'unknown-source': ['b301dcd3a91dd8fe4a7137aa1c79246360702f1379fe768a59238146233bb413', 'c1ec80cbecb3c3a664dc67d5fd7c126adda92be8ded20000f4e9b9f71f152aaf'], 'unknown-required': ['05af104e514e36f2ba0d7d8e2af2c0f5a87adc3711a285fb573ead0df22fb5bf', '3c517945ad9ed7e9c6b2b887255c88b6b7775ba70553605172763ea3b3ca3b6b'], 'unsupported': ['c7707ccdc4bbc7ab4a9dfceb9981021974b1bff270fc72b3be9f72f0698ce907', 'f64f01e5d7408ed2ec256ecabdeca9de765576d5f7c316ea496847d1976fcc6e'], 'no-claims': ['34bcd048da650c0b02327468f5b9d56addd8f02a093db9535a2d6fb514cf817d', '7c013efacea145c9e6d9f28ceb3245700c946b795d64c074a826773bf4adb0e4'], 'duplicate': ['12667396795f9a3a7e0a55145fd60b1a9d695fa733f13f0fa7167e1ea3502c53', '174ce123bbcdc768fd03cfffa0661b6c648c8200d3664658165c4c55749731df'], 'conflict': ['2d6b63548af8c01f93c79f454181922346bbccd5460748225068dde691c81a34', '14257089625c5b018f57d40c2d82c80b8aa5a1c6605109ef715900b69b493f49'], 'repeated-claim': ['23a01b2e1f394b4f132736ccaed89addbd8b6789484571694d592222bc1ab5f4', '9c7b1b57134a04aa9707c1396e7d16f371c752c2bc9300535b651d44a2d28f53'], 'missing-file': ['ee7cf19d62d73066037b59c1519faa72636b44749bafb3049a314d15577edd79', '036e98e6302733677dd87550ff7dd109c456e317053bd2cf31e17975b99a8b53']}


# Test-only finite historical view: exact original or exact repaired source only.
HANDOFF_SOURCE_PINS = {'src/evidence_review/validator.py': {'old_sha256': '08005113365afbf39af3cb13efc5c01c0ae8f5eb6ef5cad3872cf53841f1bfd9', 'new_sha256': '3b95603fe5dd290653a9bb1e9b08de55960c01a1483eee792e72335d09c15fc0', 'old': b'"""Structural, integrity, and reference validation for evidence handoffs."""\n\nfrom __future__ import annotations\n\nimport hashlib\nfrom typing import Any\n\nfrom validation import SchemaValidationError, validate_document\n\nfrom .loader import EvidenceHandoff\n\n\ndef validate_handoff(handoff: EvidenceHandoff) -> tuple[dict[str, Any], ...]:\n    """Return deterministic validation findings; never infer domain rules."""\n    findings: list[dict[str, Any]] = []\n    try:\n        validate_document(handoff.manifest, "evidence-handoff")\n    except SchemaValidationError as error:\n        findings.append(_finding("invalid_manifest", "critical", str(error)))\n\n    for message in handoff.load_errors:\n        findings.append(_finding("artifact_unreadable", "critical", message))\n\n    sources = handoff.manifest.get("sources", [])\n    source_ids = {\n        item["id"] for item in sources\n        if isinstance(item, dict) and isinstance(item.get("id"), str)\n    } if isinstance(sources, list) else set()\n    artifacts = handoff.manifest.get("artifacts", [])\n    artifact_ids: set[str] = set()\n    if isinstance(artifacts, list):\n        for artifact in artifacts:\n            if not isinstance(artifact, dict) or not isinstance(artifact.get("id"), str):\n                continue\n            artifact_id = artifact["id"]\n            artifact_ids.add(artifact_id)\n            unknown_sources = set(artifact.get("source_ids", [])) - source_ids\n            if unknown_sources:\n                findings.append(_finding(\n                    "unknown_source_reference", "critical",\n                    f"{artifact_id}: {\', \'.join(sorted(unknown_sources))}",\n                ))\n            content = handoff.artifact_content.get(artifact_id)\n            if content is None:\n                continue\n            if isinstance(artifact.get("byte_size"), int) and len(content) != artifact["byte_size"]:\n                findings.append(_finding("size_mismatch", "critical", artifact_id))\n            digest = hashlib.sha256(content).hexdigest()\n            if isinstance(artifact.get("sha256"), str) and digest != artifact["sha256"]:\n                findings.append(_finding("hash_mismatch", "critical", artifact_id))\n    unknown_required = set(handoff.manifest.get("required_artifact_ids", [])) - artifact_ids\n    for artifact_id in sorted(unknown_required):\n        findings.append(_finding("undeclared_required_artifact", "critical", artifact_id))\n    return tuple(sorted(findings, key=lambda item: (item["code"], item["detail"])))\n\n\ndef _finding(code: str, severity: str, detail: str) -> dict[str, str]:\n    return {"code": code, "severity": severity, "detail": detail}\n\n\n__all__ = ["validate_handoff"]\n'}, 'src/evidence_review/reviewer.py': {'old_sha256': 'ed976056a9ebc36750cfa6ee2bf5c6b82b797f04d52066519fa81792685ad33f', 'new_sha256': 'ee7240a4a36f6d761a4852ada3612789fd7a5c0e71457c86292cd6e891a81528', 'old': b'"""Orchestration for deterministic evidence review."""\n\nfrom __future__ import annotations\n\nimport hashlib\nfrom typing import Any\n\nfrom .completeness import assess_completeness\nfrom .conflict_detector import conflicting_claims, duplicate_artifacts\nfrom .loader import EvidenceHandoff\nfrom .validator import validate_handoff\n\n\ndef review_handoff(handoff: EvidenceHandoff) -> dict[str, Any]:\n    """Review a handoff and return a schema-valid report-ready document."""\n    manifest = handoff.manifest\n    findings = list(validate_handoff(handoff))\n    artifacts = [item for item in manifest.get("artifacts", []) if isinstance(item, dict)]\n    sources = [item for item in manifest.get("sources", []) if isinstance(item, dict)]\n    valid_artifacts = {\n        item["id"] for item in artifacts\n        if isinstance(item.get("id"), str)\n        and item["id"] in handoff.artifact_content\n        and len(handoff.artifact_content[item["id"]]) == item.get("byte_size")\n        and hashlib.sha256(handoff.artifact_content[item["id"]]).hexdigest()\n        == item.get("sha256")\n    }\n    valid_sources = {item["id"] for item in sources if isinstance(item.get("id"), str)}\n    duplicates = list(duplicate_artifacts(manifest))\n    conflicts = list(conflicting_claims(manifest))\n    completeness = assess_completeness(manifest, valid_artifacts, valid_sources)\n\n    if findings or duplicates or conflicts:\n        recommendation = "Reject"\n    elif (completeness["unsupported_claim_ids"] or completeness["missing_artifact_ids"]\n          or completeness["orphaned_artifact_ids"]):\n        recommendation = "Needs additional evidence"\n    else:\n        recommendation = "Ready for verification"\n\n    return {\n        "schema_version": "v1",\n        "handoff_id": str(manifest.get("id", "unknown")),\n        "evidence_inventory": [\n            {\n                "id": str(item.get("id", "<unknown>")),\n                "path": str(item.get("path", "")),\n                "media_type": str(item.get("media_type", "")),\n                "integrity_verified": item.get("id") in valid_artifacts,\n                "source_ids": sorted(item.get("source_ids", [])),\n            }\n            for item in sorted(artifacts, key=lambda value: str(value.get("id", "")))\n        ],\n        "supported_claims": completeness["supported_claim_ids"],\n        "unsupported_claims": completeness["unsupported_claim_ids"],\n        "conflicting_claims": conflicts,\n        "missing_evidence": completeness["missing_artifact_ids"],\n        "orphaned_artifacts": completeness["orphaned_artifact_ids"],\n        "duplicate_artifacts": duplicates,\n        "completeness_score": completeness["score"],\n        "provenance_summary": {\n            "declared_source_count": len(valid_sources),\n            "referenced_source_ids": sorted({\n                source_id for item in artifacts for source_id in item.get("source_ids", [])\n                if isinstance(source_id, str)\n            }),\n        },\n        "validation_findings": findings,\n        "recommendation": recommendation,\n    }\n\n\n__all__ = ["review_handoff"]\n'}, 'src/evidence_review/loader.py': {'old_sha256': 'e9b4f69292a839cc0dac8aec606a0a0b57681305a3bb0d0b682b5afc0dd942a1', 'new_sha256': '9b74d44e1977c9a1225bf50d4c30b826ff95b320330dc69f16939dcf8d5f9ca6', 'old': b'"""Safe loading of an external evidence handoff without interpreting its claims."""\n\nfrom __future__ import annotations\n\nimport json\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\n\nclass HandoffLoadError(ValueError):\n    """Raised when a handoff manifest cannot be safely loaded."""\n\n\n@dataclass(frozen=True, slots=True)\nclass EvidenceHandoff:\n    """A parsed handoff manifest and its readable, bundle-contained artifact bytes."""\n\n    root: Path\n    manifest: Mapping[str, Any]\n    artifact_content: Mapping[str, bytes]\n    load_errors: tuple[str, ...]\n\n\ndef load_handoff(path: Path | str) -> EvidenceHandoff:\n    """Load ``manifest.json`` (or an explicit manifest path) and contained artifacts.\n\n    Artifact failures are retained as review findings rather than aborting the review.\n    This allows an incomplete or damaged handoff to receive a deterministic report.\n    """\n    supplied = Path(path)\n    manifest_path = supplied / "manifest.json" if supplied.is_dir() else supplied\n    try:\n        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))\n    except FileNotFoundError as error:\n        raise HandoffLoadError(f"Handoff manifest not found: {manifest_path}") from error\n    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:\n        raise HandoffLoadError(f"Handoff manifest is not readable JSON: {manifest_path}") from error\n    if not isinstance(manifest, dict):\n        raise HandoffLoadError("Handoff manifest must be a JSON object")\n\n    root = manifest_path.parent.resolve()\n    content: dict[str, bytes] = {}\n    errors: list[str] = []\n    artifacts = manifest.get("artifacts", [])\n    if isinstance(artifacts, list):\n        for index, artifact in enumerate(artifacts):\n            if not isinstance(artifact, dict):\n                continue\n            artifact_id = artifact.get("id")\n            relative = artifact.get("path")\n            if not isinstance(artifact_id, str) or not isinstance(relative, str):\n                continue\n            artifact_path = root / relative\n            resolved = artifact_path.resolve()\n            if not resolved.is_relative_to(root):\n                errors.append(f"artifact[{index}] path escapes the handoff: {relative}")\n                continue\n            try:\n                content[artifact_id] = resolved.read_bytes()\n            except OSError:\n                errors.append(f"artifact {artifact_id} is missing or unreadable: {relative}")\n    return EvidenceHandoff(root, manifest, content, tuple(sorted(errors)))\n\n\n__all__ = ["EvidenceHandoff", "HandoffLoadError", "load_handoff"]\n'}}
HANDOFF_SOURCE_PATHS = frozenset(HANDOFF_SOURCE_PINS)


def handoff_preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name not in HANDOFF_SOURCE_PINS: return raw
    pin = HANDOFF_SOURCE_PINS[name]; digest = hashlib.sha256(raw).hexdigest()
    if digest == pin['old_sha256']: return raw
    if digest != pin['new_sha256']: raise AssertionError('unreviewed handoff implementation')
    old = pin['old']
    if hashlib.sha256(old).hexdigest() != pin['old_sha256']:
        raise AssertionError('historical handoff source not reproduced')
    return old


class MalformedHandoffTests(unittest.TestCase):
    def test_historical_source_and_all_adapter_routes_reject_unpinned_edits(self):
        import query_attachment_performance_preservation as support
        from context_review_preservation_support import preceding_bytes
        root = Path(__file__).resolve().parents[1]
        for name, pin in HANDOFF_SOURCE_PINS.items():
            with self.subTest(path=name):
                raw = (root / name).read_bytes(); old = pin['old']
                self.assertEqual(handoff_preceding_bytes(name, raw), old)
                self.assertEqual(handoff_preceding_bytes(name, old), old)
                self.assertEqual(preceding_bytes(name, raw), old)
                original = dict(path=name, bytes=len(old), sha256=pin['old_sha256'])
                current = dict(path=name, bytes=len(raw), sha256=pin['new_sha256'])
                support.assert_hash_row(dict(path=name, sha256=pin['old_sha256']))
                support.assert_retained_row(original)
                self.assertEqual(support.historical_inventory_row(current), original)
                for value in (raw+b'future', b'X'+raw[1:], bytearray(raw)):
                    with self.assertRaises(AssertionError): handoff_preceding_bytes(name, value)
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / name; path.parent.mkdir(parents=True); path.write_bytes(raw+b'future')
                    actual = dict(path=name, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                    for fn, row in [(support.assert_hash_row, dict(path=name, sha256=pin['old_sha256'])),
                                    (support.assert_retained_row, original), (support.historical_inventory_row, actual)]:
                        with self.assertRaises(AssertionError): fn(row, Path(temporary))
                with self.assertRaises(AssertionError): support.assert_retained_row(dict(original, sha256='0'*64))

    def test_path_resolution_cycle_becomes_an_artifact_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory)); loop = Path(directory) / 'artifacts/loop'
            loop.symlink_to('loop'); path.write_text(json.dumps(changed(base, ('artifacts', 0, 'path'), 'artifacts/loop')))
            report = review_handoff(load_handoff(path)); validate_report(report)
            self.assertEqual(report['recommendation'], 'Reject')
            self.assertEqual(report['supported_claims'], [])
            self.assertEqual([x['code'] for x in report['validation_findings']], ['artifact_unreadable'])

    def assert_rejected(self, report):
        validate_report(report)
        self.assertEqual(report['recommendation'], 'Reject')
        self.assertIn('invalid_manifest', [x['code'] for x in report['validation_findings']])
        self.assertEqual(report['supported_claims'], [])
        self.assertEqual(report['completeness_score'], 0)
        self.assertEqual(report['evidence_inventory'], [])
        self.assertEqual(report['provenance_summary'], dict(declared_source_count=0, referenced_source_ids=[]))

    def test_malformed_json_collections_identifiers_and_metadata_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory))
            for name, keys, value in malformed_cases():
                with self.subTest(case=name):
                    path.write_text(json.dumps(changed(base, keys, value)))
                    handoff = load_handoff(path)
                    before = copy.deepcopy(handoff.manifest)
                    report = review_handoff(handoff)
                    self.assert_rejected(report)
                    self.assertEqual(handoff.manifest, before)
                    self.assertEqual(report, review_handoff(handoff))
                    self.assertEqual(json.loads(render_json_report(report)), report)
                    self.assertIn('**Recommendation:** Reject', render_markdown_report(report))

    def test_validator_returns_invalid_manifest_without_reference_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory))
            for name, keys, value in malformed_cases():
                with self.subTest(case=name):
                    path.write_text(json.dumps(changed(base, keys, value)))
                    findings = validate_handoff(load_handoff(path))
                    self.assertIn('invalid_manifest', [x['code'] for x in findings])

    def test_invalid_manifest_never_reaches_downstream_assessments(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory)); path.write_text(json.dumps(changed(base, ('sources',), None)))
            with patch('evidence_review.reviewer.assess_completeness', side_effect=AssertionError('not admitted')), \
                 patch('evidence_review.reviewer.duplicate_artifacts', side_effect=AssertionError('not admitted')), \
                 patch('evidence_review.reviewer.conflicting_claims', side_effect=AssertionError('not admitted')):
                self.assert_rejected(review_handoff(load_handoff(path)))

    def test_missing_fields_and_invalid_root_have_explicit_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory))
            for key in base:
                with self.subTest(missing=key):
                    value = copy.deepcopy(base); del value[key]; path.write_text(json.dumps(value))
                    self.assert_rejected(review_handoff(load_handoff(path)))
            for root in (None, [], 'text', 1, True):
                path.write_text(json.dumps(root))
                with self.assertRaises(HandoffLoadError): load_handoff(path)
                with self.assertRaises(HandoffLoadError):
                    review_handoff(EvidenceHandoff(Path(directory), root, {}, ()))

    def test_bad_path_and_json_use_existing_load_error_or_structured_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory))
            for bad in ('artifacts/\x00bad', '../outside', '/outside'):
                with self.subTest(path=repr(bad)):
                    path.write_text(json.dumps(changed(base, ('artifacts', 0, 'path'), bad)))
                    report = review_handoff(load_handoff(path)); validate_report(report)
                    self.assertEqual(report['recommendation'], 'Reject')
                    self.assertEqual(report['supported_claims'], [])
            path.write_text('{broken')
            with self.assertRaises(HandoffLoadError): load_handoff(path)

    def test_invalid_identifier_is_not_coerced_into_a_handoff_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory)); path.write_text(json.dumps(changed(base, ('id',), [])))
            self.assertEqual(review_handoff(load_handoff(path))['handoff_id'], 'unknown')

    def test_load_findings_retained_in_limited_reject_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory)); path.write_text(json.dumps(changed(base, ('claims',), None)))
            (Path(directory) / 'artifacts/capture.txt').unlink()
            report = review_handoff(load_handoff(path)); self.assert_rejected(report)
            self.assertEqual({x['code'] for x in report['validation_findings']}, {'invalid_manifest', 'artifact_unreadable'})

    def test_all_valid_reports_retain_exact_baseline_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            path, base = fixture(Path(directory)); content = (Path(directory) / 'artifacts/capture.txt').read_bytes()
            for name, value in valid_cases(base).items():
                with self.subTest(case=name):
                    artifact = Path(directory) / 'artifacts/capture.txt'; artifact.write_bytes(content)
                    if name == 'missing-file': artifact.unlink()
                    path.write_text(json.dumps(value)); report = review_handoff(load_handoff(path)); validate_report(report)
                    # Loader messages contain the declared path only, not the temporary root.
                    actual = [hashlib.sha256(render(report).encode()).hexdigest() for render in (render_json_report, render_markdown_report)]
                    self.assertEqual(actual, VALID_REPORT_PINS[name])
