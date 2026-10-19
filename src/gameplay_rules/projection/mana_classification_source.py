"""Fixed three-unit September 2026 locator; no general CR parser or source retention."""
from pathlib import Path
import hashlib
import re

from gameplay_rules.errors import GameplayContractError
from .bounded_mana_source import _physical_lines, ANCHOR_TYPE, SPAN_POLICY
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _json
from .source import _verified_bytes
from .mana_classification_pins import VERIFIED_ANCHORS

SELECTED_REFERENCES = ('115.6', '606.1', '606.2')
_NEXT = {'115.6': '115.7', '606.1': '606.2', '606.2': '606.3'}
_MARKERS = {ref: (ref + '. ').encode('ascii') for ref in (*SELECTED_REFERENCES, '115.7', '606.3')}
_CITATION = re.compile(rb'(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])')


def _fail(code):
    raise GameplayContractError('bounded_mana_classification_source', code)


def validate_spans(anchors):
    if not isinstance(anchors, (list, tuple)) or len(anchors) != 3:
        _fail('EXACT_THREE_RULE_ALLOWLIST_REQUIRED')
    if [a.get('rule_reference') for a in anchors] != list(SELECTED_REFERENCES):
        _fail('EXACT_THREE_RULE_ALLOWLIST_REQUIRED')
    prior_end = prior_line = -1
    for a in anchors:
        if any(type(a.get(k)) is not int for k in ('byte_start', 'byte_end', 'starting_physical_line', 'ending_physical_line', 'line_count')):
            _fail('MALFORMED_SOURCE_SPAN')
        if (a['byte_start'] < 0 or a['byte_end'] <= a['byte_start'] or
                a['starting_physical_line'] < 1 or a['ending_physical_line'] < a['starting_physical_line'] or
                a['line_count'] != a['ending_physical_line'] - a['starting_physical_line'] + 1):
            _fail('MALFORMED_SOURCE_SPAN')
        if a['byte_start'] < prior_end or a['starting_physical_line'] <= prior_line:
            _fail('OVERLAPPING_SELECTED_SPANS')
        prior_end, prior_line = a['byte_end'], a['ending_physical_line']


def locate_anchors(data):
    """Structural fixtures have no source authority; recognize only five fixed markers."""
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail('INVALID_SOURCE_BYTES')
    lines = _physical_lines(data)
    starts = {}
    for i, (_, body, _) in enumerate(lines):
        for ref, marker in _MARKERS.items():
            if body.startswith(marker):
                if ref in starts:
                    _fail('DUPLICATE_MARKER')
                if not body[len(marker):].strip():
                    _fail('MALFORMED_NUMBERING')
                starts[ref] = i
            elif body.startswith(ref.encode()) and (len(body) == len(ref) or body[len(ref):len(ref)+1] in (b'.', b' ', b'\t')):
                _fail('MALFORMED_NUMBERING')
    if set(starts) != set(_MARKERS):
        _fail('MISSING_MARKER')
    heading = starts['606.1'] - 1
    if heading >= 0 and lines[heading][1] == b'\xc2\xa0':
        heading -= 1
    if heading < 0 or lines[heading][1] != b'606. Loyalty Abilities':
        _fail('UNEXPECTED_LOCAL_FAMILY_SHAPE')
    result = []
    for ref in SELECTED_REFERENCES:
        first, terminal = starts[ref], starts[_NEXT[ref]]
        if terminal <= first:
            _fail('AMBIGUOUS_TERMINATION')
        last = first
        separated = False
        for i in range(first + 1, terminal):
            body = lines[i][1]
            if body == b'\xc2\xa0':
                if separated or i != terminal - 1:
                    _fail('AMBIGUOUS_TERMINATION')
                separated = True
            elif body.lstrip().startswith(b'Example:'):
                _fail('AMBIGUOUS_EXAMPLE_OWNERSHIP')
            elif re.match(rb'^\s*[1-9][0-9]{2}\.', body):
                _fail('UNEXPECTED_LOCAL_FAMILY_SHAPE')
            elif body.startswith(b'  ') and body[2:].strip() and not separated:
                last = i
            else:
                _fail('AMBIGUOUS_CONTINUATION')
        start, end = lines[first][0], lines[last][0] + len(lines[last][1])
        result.append(dict(rule_reference=ref, artifact_hash='sha256:'+hashlib.sha256(data).hexdigest(),
            effective_date=EFFECTIVE_DATE, anchor_type=ANCHOR_TYPE, span_policy=SPAN_POLICY,
            starting_physical_line=first+1, ending_physical_line=last+1, line_count=last-first+1,
            byte_start=start, byte_end=end, span_sha256='sha256:'+hashlib.sha256(data[start:end]).hexdigest()))
    validate_spans(result)
    return result


def verify_bytes(data):
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH or
            'sha256:'+hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail('VERIFIED_SOURCE_ARTIFACT_MISMATCH')
    anchors = locate_anchors(data)
    if anchors != _json(VERIFIED_ANCHORS):
        _fail('VERIFIED_SOURCE_BLOCK_MISMATCH')
    for anchor in anchors:
        block = data[anchor['byte_start']:anchor['byte_end']]
        if _CITATION.search(block[len(_MARKERS[anchor['rule_reference']]):]):
            _fail('UNEXPECTED_OUTGOING_NUMBERED_REFERENCE')
    return anchors


def verified_anchors(artifact_path, *, review_root):
    if artifact_path is None or not Path(artifact_path).is_file():
        _fail('MISSING_VERIFIED_SOURCE_ARTIFACT')
    root = Path(review_root)
    data = _verified_bytes(artifact_path,
        artifact_review_root=root/'gameplay-rules-artifact-verification',
        source_root=root/'gameplay-rules-source-versioning',
        discovery_root=root/'gameplay-rules-release-discovery-closure')
    return verify_bytes(data)
