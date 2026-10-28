"""Fixed four-unit locator; only authorized bodies and neighboring marker tokens.

Fixture spans establish locator behavior only. Fresh authority requires exact
owner artifact bytes and the retained artifact-review lineage before inspection.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from gameplay_rules.errors import GameplayContractError
from .contracts import ARTIFACT_BYTE_LENGTH, ARTIFACT_HASH, EFFECTIVE_DATE, _freeze, _json
from .bounded_mana_source import _physical_lines, ANCHOR_TYPE, SPAN_POLICY
from .source import _verified_bytes

SELECTED_REFERENCES = ('106.12', '106.12a', '106.12b', '614.15')
_NEXT = {'106.12': '106.12a', '106.12a': '106.12b', '106.12b': '106.13', '614.15': '614.16'}
_PREVIOUS = {'106.12': '106.11', '106.12a': '106.12', '106.12b': '106.12a', '614.15': '614.14'}
_MARKER_TOKEN = re.compile(rb'^([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?:\.)?[ \t]')
_CITATION = re.compile(rb'(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])')
_NUMBERED = re.compile(rb'^\s*[1-9][0-9]{2}(?:\.|[ \t])')
_SEPARATOR = b'\xc2\xa0'


def _fail(code):
    raise GameplayContractError('mana_context_source', code)


def _anchor(ref, first, last, start, end, digest, previous_line, next_line, *, artifact_hash=ARTIFACT_HASH):
    body = dict(rule_reference=ref, artifact_hash=artifact_hash, effective_date=EFFECTIVE_DATE,
        anchor_type=ANCHOR_TYPE, span_policy=SPAN_POLICY, starting_physical_line=first,
        ending_physical_line=last, line_count=last-first+1, byte_start=start, byte_end=end,
        span_length=end-start, span_sha256='sha256:'+digest, owned_example_line_count=0,
        preceding_marker={'rule_reference':_PREVIOUS[ref], 'physical_line':previous_line, 'body_inspected':False},
        following_marker={'rule_reference':_NEXT[ref], 'physical_line':next_line, 'body_inspected':False})
    return body


VERIFIED_ANCHORS = _freeze([
    _anchor('106.12',441,441,30359,30539,'be5451d8c93e70d437105a46fed0a451dbcf34cfede94dc7cf49e87c35a0d776',439,443),
    _anchor('106.12a',443,443,30543,30759,'3091331222c64b3736973bbba06fbf53cffd2320de10209f84d1231151d90152',441,445),
    _anchor('106.12b',445,445,30763,31030,'bfa72870a81b1611c545cc70a09b010c27018a709abd6dc4a3a83926c749492c',443,447),
    _anchor('614.15',3128,3128,407923,408473,'05ff54161f347bbaef80e18138d93482a1d4330682c5cf5683dfdb8f74edb329',3126,3130),
])


def locate_anchors(data):
    """Return spans, never bodies. Marker-only neighbors confer no source units."""
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH+1:
        _fail('BOUNDED_ORIGINAL_BYTES_REQUIRED')
    lines = _physical_lines(data)
    markers, starts = {}, {}
    for index, (_, body, _) in enumerate(lines):
        token = _MARKER_TOKEN.match(body)
        if token:
            ref = token.group(1).decode('ascii')
            markers[index] = ref
            if ref in SELECTED_REFERENCES:
                if ref in starts:
                    _fail('DUPLICATE_SELECTED_MARKER')
                expected = (ref + ('. ' if ref[-1].isdigit() else ' ')).encode()
                if not body.startswith(expected) or not body[len(expected):].strip():
                    _fail('MALFORMED_SELECTED_MARKER')
                starts[ref] = index
    if set(starts) != set(SELECTED_REFERENCES):
        _fail('EXACT_FOUR_SELECTED_MARKERS_REQUIRED')
    if tuple(sorted(starts, key=starts.get)) != SELECTED_REFERENCES:
        _fail('SELECTED_MARKER_ORDER_CHANGED')
    marker_indices = sorted(markers)
    result = []
    for ref in SELECTED_REFERENCES:
        first = starts[ref]
        position = marker_indices.index(first)
        if position == 0 or position+1 >= len(marker_indices):
            _fail('NEIGHBOR_MARKER_MISSING')
        previous, terminal = marker_indices[position-1], marker_indices[position+1]
        if markers[previous] != _PREVIOUS[ref] or markers[terminal] != _NEXT[ref]:
            _fail('UNEXPECTED_NEIGHBOR_MARKER')
        last, examples, separated = first, 0, False
        for index in range(first+1, terminal):
            body = lines[index][1]
            if body == _SEPARATOR:
                if separated or index != terminal-1:
                    _fail('AMBIGUOUS_UNIT_TERMINATION')
                separated = True
            elif not separated and body.lstrip().startswith(b'Example:'):
                last, examples = index, examples+1
            elif not separated and body.startswith(b'  ') and body[2:].strip() and not _NUMBERED.match(body):
                last = index
            else:
                _fail('AMBIGUOUS_OWNED_CONTINUATION')
        start = lines[first][0]
        end = lines[last][0]+len(lines[last][1])
        anchor = _anchor(ref,first+1,last+1,start,end,hashlib.sha256(data[start:end]).hexdigest(),
            previous+1,terminal+1,artifact_hash='sha256:'+hashlib.sha256(data).hexdigest())
        anchor['owned_example_line_count'] = examples
        result.append(anchor)
    return result


def literal_citations(data, anchors):
    """Scan only owned authorized blocks; numbering and structure are separate."""
    result = {}
    for a in anchors:
        ref = a['rule_reference']
        if ref not in SELECTED_REFERENCES:
            _fail('EXTRA_SOURCE_UNIT_FORBIDDEN')
        marker = (ref + ('. ' if ref[-1].isdigit() else ' ')).encode()
        block = data[a['byte_start']:a['byte_end']]
        result[ref] = sorted(set(m.group(1).decode() for m in _CITATION.finditer(block[len(marker):])))
    return result


def verify_bytes(data):
    if type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH or 'sha256:'+hashlib.sha256(data).hexdigest() != ARTIFACT_HASH:
        _fail('EXACT_OWNER_ARTIFACT_REQUIRED')
    anchors = locate_anchors(data)
    if anchors != _json(VERIFIED_ANCHORS):
        _fail('COMPLETE_RAW_SPANS_DO_NOT_REPRODUCE')
    if literal_citations(data,anchors) != {'106.12':['605'],'106.12a':[],'106.12b':[],'614.15':[]}:
        _fail('LITERAL_CITATIONS_DO_NOT_REPRODUCE')
    return anchors


def verified_anchors(artifact_path, *, review_root):
    if artifact_path is None or not Path(artifact_path).is_file():
        _fail('MISSING_FRESH_OWNER_ARTIFACT')
    root = Path(review_root)
    data = _verified_bytes(artifact_path,
        artifact_review_root=root/'gameplay-rules-artifact-verification',
        source_root=root/'gameplay-rules-source-versioning',
        discovery_root=root/'gameplay-rules-release-discovery-closure')
    return verify_bytes(data)
