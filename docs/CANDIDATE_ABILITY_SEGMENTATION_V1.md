# Candidate Ability Segmentation V1

This additive Card Intelligence consumer derives pending local subjects from fresh
`MechanicalCardIntelligence.inspect_mtgjson_candidate` inspection. It uses the
unchanged Candidate Activated-Mana V1 recognizer and twelve-row review calculation,
and optionally the unchanged native conditional Rules Intelligence reasoner.
It is not accepted Card semantics, a general Oracle parser or an executable model.

## Closed boundary policy

Let P mean a **complete full match** of the existing V1 grammar, unchanged:

```text
"{T}" ASCII-space{0..8} ":" ASCII-space{0..8} "Add " mana{1..8} "."
mana := "{W}" | "{U}" | "{B}" | "{R}" | "{G}" | "{C}"
```

The recognized field shape is `P (LF P)* [LF U]`, anchored at the field start.
LF is exactly U+000A. U begins with the same bounded written tap-cost header,
followed by an uppercase ASCII letter, and consumes **all remaining text** as one
unresolved region. U does not establish a single ability or permit extraction
of any later familiar passage. No additional cost or effect grammar is interpreted.

A supported P must end at field end or at LF followed by the witnessed next tap
header. A newline, colon or period alone never establishes a boundary. An unknown
prefix, uncertain continuation, same-line suffix, unsupported separator, leading or
trailing text or missing final period leaves the whole field unresolved. Global
quote/apostrophe/parenthesis, unsupported control and unbalanced/nested-brace guards
also leave it unresolved. These are conservative refusals of interpretation, not
claims that the supplied Card text is malformed. CRLF, blank-line separators,
reminder text, quotations and multiface segmentation are outside this policy.

For original synthetic `P / P`, both subjects receive pending proposals. For
`P / tap-draw passage / P`, only the first P receives a proposal; the entire rest
is unresolved, including the final P. A restriction after P without a supported
next header cannot be detached from P. No supported-looking substring bypasses this.

## Evidence, accounting and identities

Only native verified query/identity/relationship/source/profile/report controls
supply evidence. Requests cannot install raw text, saved inspections or authority.
Existing global withholding and occurrence ambiguity remain effective; selecting
an occurrence does not evade conflict conditions. Only unwithheld normal whole-card
text enters segmentation. No historical source reader is initialized.

The report retains the exact decoded field, its UTF-8 hash and full-field span.
Ordered supported, LF-separator and unresolved regions retain their exact literals,
hashes and half-open original-field UTF-8 spans. Runtime checks require no gaps,
no overlaps and exact byte reconstruction. No whitespace is silently trimmed.
Unavailable or withheld evidence reports accounting NOT_AVAILABLE, not zero-byte
success. Empty supplied text is accounted for but remains unresolved.

Each local subject ID binds canonical Card/Printing, native inspection and source
occurrence/face/field, field hash, position/ordinal, offsets, policy and implementation.
Identical passages at different positions have distinct IDs. These are pending
local subjects, not canonical, executable or stable cross-release ability identities.

The existing recognizer supplies proposals; relative spans are translated by adding
the subject's original-field byte start. Transformation provenance preserves the
relative spans. Existing review computation is reused, but its new wrapper binds
selected_passage to the subject span and full_oracle_field to the entire field.
The predecessor's whole-field reference coincidence is never copied as authority.
Both classification-method obligations remain unknown; all semantics require review.

## Coverage and conditional reasoning

Accounting, closed-family segmentation, supported proposals, unresolved bytes/regions,
surrounding-effect uncertainty and Card-level completeness are separate measurements.
An unresolved remainder makes total_ability_count null. A complete closed-family
count is explicitly a pending written-family count. Card mechanical completeness
and accepted semantics remain NOT_ESTABLISHED even when every byte is accounted for.

All subjects share a deterministic unresolved-context dependency binding. Sibling
or remainder effects are not assumed irrelevant. Optional reasoning selects exactly
one subject; its ID becomes the native scenario_id. Written traits come only from
that subject's existing proposal. No sibling characteristics can be supplied.

Every multi-subject or supported-plus-unresolved reasoning request requires an exact
field/selected-subject/dependency-bound `HYPOTHETICAL_NO_RELEVANT_SURROUNDING_EFFECTS`
assumption. This is a research hypothesis, not evidence of independence. Uncertain
selected boundaries cannot be bypassed by an assumption. Interpretation hypotheses
and game-state assumptions remain separate; omitted native fields stay UNKNOWN.
The complete native result is retained. Same-ability repeat restrictions remain
effective. Legal activation, current ability to tap and actual mana output remain
unknown. No payment, mana generation, gameplay or static-resource inference occurs.

## API, replay and bounds

`load_candidate_ability_interpreter` accepts the same trusted native evidence and
rules-root controls as V1. `assess` accepts exact card_id, printing_id, evidence_id
(null or independently selected occurrence) and reasoning (null or one closed request).
The reasoning object contains segment_id, interpretation_premise, characteristics,
state and scope_assumption. The latter is null for one whole-field P, otherwise the
exact field_id, segment_id, dependency_id and named hypothesis. This never authenticates
an Owner or accepts semantics.

Independently retain report IDs. `replay(raw, expected_report_id=pin)` freshly
inspects evidence and recomputes accounting, boundaries, local IDs, proposals, spans,
coverage, criteria and native reasoning, comparing the complete report. A valid
checksum alone cannot substitute a report. `assess_many` and `replay_coverage` use
the same recomputation for only their explicit request population; counts are not
claims about unique Cards or an Oracle corpus.

Bounds: field/request 8,192 UTF-8/canonical bytes respectively; report 65,536 bytes;
16 supported subjects, one unresolved remainder, 16 separators, 33 regions; one
native reasoning request per assessment; 1–16 distinct coverage requests within
131,072 canonical bytes. Replay performs one assessment or at most 16 for coverage.
Overflow refuses rather than truncating. Reports may refuse their byte budget even
when individual counts fit. Packaged code reads remain at most 512 KiB per file.
All importer, evidence-reader, codec and native rules limits remain unchanged.

## Preservation and next bounded milestone

All V1 implementation-bound files and the twelve factual-admission implementation
files remain unchanged. Historical V1 report identities and replay are preserved.
The prepared real cohort is neither reassessed nor admitted; future execution still
requires live verification of every bound input and independent production authority.
Authentication is deferred; actual private admission remains HOLD. Established
iPhone-first, bounded standing-authorization and proactive research requirements
remain intact; no authorization implementation is supplied here.

After successful delivery and merge verification, the recommended **separately
authorized** next milestone is Private Factual Snapshot-to-Candidate Interpretation
Compatibility V1. The current inspector requires legacy card_reference/uuid fields
absent from admitted v3 records and assumes canonical IDs directly select provider
evidence. Original synthetic scoping reproduced refusal even with equal IDs.
The reviewed crosswalk is the proposed bridge; preserve both namespaces and exact
parent/source/version bindings. Do not manufacture fields, match by name, weaken
identity checks or reopen authentication. That repair is not implemented here.

All implementation fixtures are original synthetic material. No real Oracle,
private factual records or retained archive is acquired, read or processed. No
semantic acceptance, canonical promotion, legality, gameplay, external AI export
or public redistribution authority is granted by inspection or these reports.
