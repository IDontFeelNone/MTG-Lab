"""Finite historical views for the single two-unit casting-stage batch.

Only these individually named additions are omitted from earlier inventories.
Historical fixtures, expected counts and digests keep their original values;
unknown neighboring paths remain visible to every historical guard.
"""
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/casting_stage_family_completion/" + name
    for name in ("__init__.py", "__main__.py", "source.py", "scope.py",
                 "contracts.py", "reviews.py", "package.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-casting-stage-family-completion/" + name
    for name in ("projection.json", "preflight.json", "scope-decision.json",
                 "source-correspondence.json", "procedure-map.json",
                 "range-reassessment.json", "legality-gap-assessment.json",
                 "consumer-semantic-boundaries.json", "composite-coverage.json",
                 "preservation-readiness.json", "subsequent-recommendation.json",
                 "manifest.json")
)


def is_casting_stage_family_completion_addition(path, root=ROOT):
    """Select only the seven modules and twelve retained package files."""
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS


# Exact canonical prefixes and the single measured authored batch suffix.
DOCUMENT_APPENDICES = {'README.md': {'baseline_bytes': 34748,
               'baseline_sha256': '190990504b7b800c3c2c07d72651e142b7673763f561e5c60cb1099650d6d5e3',
               'appendix_bytes': 2672,
               'appendix_sha256': 'c7cd1baa84c2db0059738b70d43e7031f0fd2c60a6c7ea7cee5977d838b8bd45'},
 'PROJECT_INVENTORY.md': {'baseline_bytes': 89577,
                          'baseline_sha256': 'd9554d2958c7f2834295837fe3bcfda4c6332d049bfb41595995725ff0d41d74',
                          'appendix_bytes': 2672,
                          'appendix_sha256': 'c7cd1baa84c2db0059738b70d43e7031f0fd2c60a6c7ea7cee5977d838b8bd45'},
 'CHANGELOG.md': {'baseline_bytes': 55004,
                  'baseline_sha256': '3ad893c1dc053f20b7ad00e57bdc14e55a2d7791349f141e76d416bf36f2b49b',
                  'appendix_bytes': 2672,
                  'appendix_sha256': 'c7cd1baa84c2db0059738b70d43e7031f0fd2c60a6c7ea7cee5977d838b8bd45'},
 'docs/SESSION_STATE.md': {'baseline_bytes': 84630,
                           'baseline_sha256': 'ac2e22469e35da1d18ac46c073b02f41f0c20069363447f074248d5ae0df94ee',
                           'appendix_bytes': 2667,
                           'appendix_sha256': 'f84d5c11766a26c5bd9fcdb8753939e21098f4548fc963d2468a747583daba58'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 66865,
                       'baseline_sha256': 'b5287e4999fef1aae00f2ade4ecfba2961d9e1ee8efcaa898e3bff0de096f545',
                       'appendix_bytes': 2667,
                       'appendix_sha256': 'f84d5c11766a26c5bd9fcdb8753939e21098f4548fc963d2468a747583daba58'},
 'docs/HANDOFF.md': {'baseline_bytes': 95422,
                     'baseline_sha256': '36a22aaf49a7b0181b29dd04c6d9448327d4c4b5716a08391dad90a892696686',
                     'appendix_bytes': 2667,
                     'appendix_sha256': 'f84d5c11766a26c5bd9fcdb8753939e21098f4548fc963d2468a747583daba58'},
 'docs/ROADMAP.md': {'baseline_bytes': 37530,
                     'baseline_sha256': 'a28a7d6d65eb2b1d06b002611f3c05d9c2d1ebdb60b708ba2d66388f14267a18',
                     'appendix_bytes': 2667,
                     'appendix_sha256': 'f84d5c11766a26c5bd9fcdb8753939e21098f4548fc963d2468a747583daba58'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 108798,
                            'baseline_sha256': '7a1bbbf8449e8af2cfa4b9a651dfb2741204e3a4a4a824b39305755cc066aecd',
                            'appendix_bytes': 2667,
                            'appendix_sha256': 'f84d5c11766a26c5bd9fcdb8753939e21098f4548fc963d2468a747583daba58'}}


def historical_document_before_casting_stage_family_completion_append(path, raw):
    """Validate whole canonical bytes and remove only the one batch appendix.

    Exact inherited bytes are also accepted for historical adapter composition.
    Unknown names, other suffixes, altered prefixes and non-bytes fail closed.
    """
    if type(path) is not str or path not in DOCUMENT_APPENDICES:
        raise AssertionError("Only named casting-stage batch documents are adapted")
    if type(raw) is not bytes:
        raise AssertionError("Canonical document input must be bytes")
    pin = DOCUMENT_APPENDICES[path]
    length = pin["baseline_bytes"]
    if len(raw) not in (length, length + pin["appendix_bytes"]):
        raise AssertionError("Only the exact casting-stage batch appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Complete inherited casting-stage document changed")
    if appendix and hashlib.sha256(appendix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact casting-stage batch appendix changed")
    return baseline
