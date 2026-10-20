"""Fixed September 2026 locator for exactly one mana stack-exception block.

Parent and neighboring markers are transient shape checks, never source units
or retained anchors. Structural fixtures carry no source authority; verified
construction requires the exact external artifact and retained source lineage.
"""
from pathlib import Path
import hashlib
import re
from collections.abc import Mapping

from gameplay_rules.errors import GameplayContractError

from .bounded_mana_source import _physical_lines, ANCHOR_TYPE, SPAN_POLICY
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _freeze, _json
from .source import _verified_bytes


SELECTED_REFERENCES = ('405.6c',)
DIRECT_REFERENCES = ('605',)
_LOCAL_REFERENCES = ('405.6', '405.6a', '405.6b', '405.6c', '405.6d')
_MARKERS = {ref: (ref + ('. ' if ref == '405.6' else ' ')).encode('ascii')
            for ref in _LOCAL_REFERENCES}
_SEPARATOR = b'\xc2\xa0'
_NUMBERED_START = re.compile(rb'^[ \t]*[1-9][0-9]{2}(?:\.|[ \t]|$)')
_CITATION = re.compile(
    rb'(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])')

# Hash-only metadata independently reproduced from the exact owner artifact.
# No context parent/sibling anchor or official source prose is retained.
VERIFIED_ANCHORS = _freeze([{
    'rule_reference': '405.6c',
    'artifact_hash': ARTIFACT_HASH,
    'effective_date': EFFECTIVE_DATE,
    'anchor_type': ANCHOR_TYPE,
    'span_policy': SPAN_POLICY,
    'starting_physical_line': 2059,
    'ending_physical_line': 2059,
    'line_count': 1,
    'byte_start': 238794,
    'byte_end': 239105,
    'span_sha256': 'sha256:f5b86d6ad7446f5a0090739608105aabf33168403e36233806543438f122f184',
}])


def _fail(code):
    raise GameplayContractError('bounded_mana_stack_exception_source', code)


def _local_marker(body):
    """Recognize only the five fixed local context markers."""
    for ref, marker in _MARKERS.items():
        if body.startswith(marker):
            if not body[len(marker):].strip():
                _fail('MALFORMED_NUMBERING')
            return ref
    stripped = body.lstrip(b' \t')
    if any(stripped.startswith(ref.encode('ascii')) for ref in _LOCAL_REFERENCES[1:]):
        _fail('MALFORMED_NUMBERING')
    parent = b'405.6'
    if (stripped.startswith(parent) and
            (len(stripped) == len(parent) or stripped[len(parent):len(parent)+1] in (b'.', b' ', b'\t'))):
        _fail('MALFORMED_NUMBERING')
    return None


def validate_spans(anchors):
    """Check only one selected metadata span, without claiming byte access."""
    if not isinstance(anchors, (list, tuple)) or len(anchors) != 1:
        _fail('EXACT_ONE_RULE_ALLOWLIST_REQUIRED')
    if not isinstance(anchors[0], Mapping):
        _fail('MALFORMED_SOURCE_SPAN')
    anchor = anchors[0]
    if anchor.get('rule_reference') != SELECTED_REFERENCES[0]:
        _fail('EXACT_ONE_RULE_ALLOWLIST_REQUIRED')
    numeric = ('byte_start', 'byte_end', 'starting_physical_line',
               'ending_physical_line', 'line_count')
    if any(type(anchor.get(key)) is not int for key in numeric):
        _fail('MALFORMED_SOURCE_SPAN')
    if (anchor['byte_start'] < 0 or anchor['byte_end'] <= anchor['byte_start'] or
            anchor['starting_physical_line'] < 1 or
            anchor['ending_physical_line'] < anchor['starting_physical_line'] or
            anchor['line_count'] != anchor['ending_physical_line'] - anchor['starting_physical_line'] + 1):
        _fail('MALFORMED_SOURCE_SPAN')


def _block_last(lines, first, terminal):
    """Determine one fixed local block's end without retaining its body."""
    if terminal <= first:
        _fail('AMBIGUOUS_TERMINATION')
    last = first
    for index in range(first + 1, terminal):
        body = lines[index][1]
        if body == _SEPARATOR:
            if index != terminal - 1:
                _fail('AMBIGUOUS_TERMINATION')
        elif _NUMBERED_START.match(body):
            _fail('UNEXPECTED_LOCAL_FAMILY_SHAPE')
        elif body.lstrip(b' \t').startswith(b'Example:'):
            _fail('AMBIGUOUS_CONTINUATION')
        elif body.startswith(b'  ') and body[2:].strip():
            last = index
        else:
            _fail('AMBIGUOUS_CONTINUATION')
    return last


def locate_anchors(data):
    """Inspect fixed local shape; fixture results do not verify source identity.

    Only 405.6c is returned. Internal raw line terminators remain in its span;
    the final body terminator and inter-rule separator are excluded.
    """
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail('INVALID_SOURCE_BYTES')
    lines = _physical_lines(data)
    starts = {}
    for index, (_, body, _) in enumerate(lines):
        reference = _local_marker(body)
        if reference is not None:
            if reference in starts:
                _fail('DUPLICATE_MARKER')
            starts[reference] = index
    if set(starts) != set(_LOCAL_REFERENCES):
        _fail('MISSING_MARKER')
    if starts['405.6d'] <= starts['405.6c']:
        _fail('AMBIGUOUS_TERMINATION')
    if tuple(sorted(starts, key=starts.get)) != _LOCAL_REFERENCES:
        _fail('UNEXPECTED_LOCAL_FAMILY_SHAPE')
    last = None
    for reference, next_reference in zip(_LOCAL_REFERENCES, _LOCAL_REFERENCES[1:]):
        block_last = _block_last(lines, starts[reference], starts[next_reference])
        if reference == SELECTED_REFERENCES[0]:
            last = block_last
    first = starts[SELECTED_REFERENCES[0]]
    start, end = lines[first][0], lines[last][0] + len(lines[last][1])
    result = [{
        'rule_reference': SELECTED_REFERENCES[0],
        'artifact_hash': 'sha256:' + hashlib.sha256(data).hexdigest(),
        'effective_date': EFFECTIVE_DATE,
        'anchor_type': ANCHOR_TYPE,
        'span_policy': SPAN_POLICY,
        'starting_physical_line': first + 1,
        'ending_physical_line': last + 1,
        'line_count': last - first + 1,
        'byte_start': start,
        'byte_end': end,
        'span_sha256': 'sha256:' + hashlib.sha256(data[start:end]).hexdigest(),
    }]
    validate_spans(result)
    return result


def verify_bytes(data):
    """Require exact artifact bytes, then reproduce one anchor and citation."""
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH or
            'sha256:' + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail('VERIFIED_SOURCE_ARTIFACT_MISMATCH')
    anchors = locate_anchors(data)
    if anchors != _json(VERIFIED_ANCHORS):
        _fail('VERIFIED_SOURCE_BLOCK_MISMATCH')
    anchor = anchors[0]
    block = data[anchor['byte_start']:anchor['byte_end']]
    body = block[len(_MARKERS[SELECTED_REFERENCES[0]]):]
    citations = tuple(sorted({match.group(1).decode('ascii') for match in _CITATION.finditer(body)}))
    if citations != DIRECT_REFERENCES:
        _fail('UNEXPECTED_OUTGOING_NUMBERED_REFERENCE')
    return anchors


def verified_anchors(artifact_path, *, review_root):
    """Reproduce source-verification lineage and the sole selected anchor."""
    try:
        if artifact_path is None or not Path(artifact_path).is_file():
            _fail('MISSING_VERIFIED_SOURCE_ARTIFACT')
    except (OSError, TypeError, ValueError):
        _fail('MISSING_VERIFIED_SOURCE_ARTIFACT')
    root = Path(review_root)
    data = _verified_bytes(artifact_path,
        artifact_review_root=root / 'gameplay-rules-artifact-verification',
        source_root=root / 'gameplay-rules-source-versioning',
        discovery_root=root / 'gameplay-rules-release-discovery-closure')
    return verify_bytes(data)


def source_anchor(artifact_path, *, review_root):
    """Return the verified selected anchor; no parent anchor is constructed."""
    return verified_anchors(artifact_path, review_root=review_root)[0]


verify_source = verified_anchors
