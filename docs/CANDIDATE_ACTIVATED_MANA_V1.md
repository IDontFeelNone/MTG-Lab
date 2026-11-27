# Card Intelligence Candidate Activated-Mana Interpretation V1

This is pending Card Intelligence interpretation of verified imported candidate
evidence, not accepted real-card understanding. The importer still owns acquisition,
normalization, identity/provenance and evidence projection. This consumer owns
only the following written interpretation. Existing Rules Intelligence owns its
conditional classification/timing calculations. Architecture v13, Decision 017,
source-use restrictions and gameplay guards remain unchanged.

## Complete grammar and resource bounds

One complete source `text` field must match this entire ASCII grammar:

```text
passage := "{T}" space{0..8} ":" space{0..8} "Add " mana{1..8} "."
mana    := "{W}" | "{U}" | "{B}" | "{R}" | "{G}" | "{C}"
space   := ASCII U+0020
```

There is exactly one written tap-symbol cost and one fixed mana-addition
instruction. Repeated symbols represent written quantities; mixed fixed symbols
are supported. There is no numeric multiplier, choice, variable output or extra
cost. Whitespace is allowed only in the indicated colon positions. Leading or
trailing whitespace, tabs, line breaks, Unicode lookalikes, suffixes, additional
abilities and missing final punctuation do not match. No substring becomes a
complete proposal. Normalization changes only colon spacing in a separate display
value; original offsets/hash retain the exact original field.

The interpreted text is at most 8,192 UTF-8 bytes, a closed request at most
8,192 canonical JSON bytes, and the complete report at most 65,536 bytes. The
existing codec additionally bounds depth, strings, types and structure. The
fixed implementation-file read limit is 512 KiB per selected public code file.
Coverage evaluates 1–16 distinct explicit requests within 131,072 canonical bytes;
it is not an Oracle-corpus census. Existing importer, evidence-reader, source,
occurrence, reconciliation and native reasoning limits are unchanged.

## Verified evidence and existing representation

`load_candidate_mana_interpreter` binds a native canonical query, independently
selected query snapshot, existing Oracle evidence profile and import report pin,
evidence directory and retained rules root. Every assessment calls
`MechanicalCardIntelligence.inspect_mtgjson_candidate`; arbitrary text or saved
inspection JSON is not an equivalent input. The historical Scryfall source reader
is not initialized. Only original project-authored source fixtures are used in
this milestone; no real private Oracle evidence is authorized.

The request contains exact `card_id`, `printing_id`, `evidence_id` (null selects
only an unambiguous occurrence) and `reasoning` (null unless explicitly requested).
All occurrences participate in withholding checks. An occurrence selector cannot
evade another conflicting occurrence. Only unwithheld whole-card normal-layout
text is interpreted; exceptional/multiface evidence and unresolved boundaries stay
uninterpreted. A checksum cannot establish that a publisher's text is complete or
current; here complete means full consumption of the verified supplied field.

Reports reuse the existing bounded `ReviewDocument`, pending interpretation/review
vocabulary and native rules-characteristic keys. They are not a second executable
ability representation. `proposed_kind`, written cost/effect observations and
`proposed_rules_characteristics` remain `requires_review`. Each interpretation
has half-open UTF-8 evidence spans or an explicit span-based policy derivation.
The report binds the exact Card/Printing, inspection and occurrence IDs, release,
partition/row/field, record/text hashes, face boundary, provenance, notice, profile,
policy and selected implementation bytes. Literal cost/effect observations remain
separate from proposed ability kind, potential mana and absence readings.

The existing `card_rules_pilot.reasoning_policy.compute` receives its unchanged
twelve-row criteria and proposed-kind contract. Six supported written criteria
are proposed satisfied, four triggered-only criteria inapplicable and the two
classification-method obligations unknown. This does not approve those proposals
or silently complete replacement-effect assessment. Historical authored pilots
and accepted historical land readings are not modified.

## Optional conditional native reasoning

The separate `reasoning` input must explicitly contain
`interpretation_premise="TREAT_PENDING_PROPOSAL_AS_HYPOTHESIS_ONLY"`,
`characteristics` and `state`. Only `source_is_planeswalker`, `self_replacement`,
`other_replacement` and `chosen_targets` may be separately hypothesized in
`characteristics`; written proposed traits cannot be overridden. `state` accepts
only the existing payment request, priority, same-ability-unresolved and current
output fields. Omitted assumptions are UNKNOWN, not false or absent.

The existing native reasoner receives those declared premises and its unchanged
24-rule metadata context, with seven selected supporting units. Its complete
native result is retained. Explicit absence of self-replacement and zero chosen
targets, together with a supported declared payment opportunity and no unresolved
same-ability activation, can yield a conditional timing result. Missing premises
remain NEEDS_FACTS; the native same-ability restriction remains effective. A
current output declaration of ZERO is not overwritten by written mana quantity.
An incomplete interpretation cannot request affirmative downstream reasoning.

Every result retains unknown current state, control, zone, tapped status,
restrictions, external/self-replacement effects, resources, actual output and
activation legality. Conditional calculations over pending hypotheses are never
accepted semantic characteristics. No mana, payment or gameplay state is mutated.

## Replay, diagnostics and coverage

`consumer.assess(request)` returns an immutable report. Independently retain its
ID. `consumer.replay(raw, expected_report_id=pin)` re-inspects verified evidence,
recognizes the whole passage, reconstructs proposals/review criteria and recomputes
any native reasoning result. It compares the entire report, not just its hash.
Changed spans, characteristics, premises, source/context identities and results
refuse even after coherent rehashing. A different valid hypothetical request is a
different report; the independent original pin prevents substituting it.

`assess_many(requests)` reports complete/partial/unsupported/ambiguous/withheld or
unresolved outcomes and safe actual refusals. Counts partition the evaluated
request population; diagnostic categories can overlap. No unsupported recognition
produces a proposal. `replay_coverage(raw, expected_report_id=pin)` recomputes the
entire selected population. Partial recognition is diagnostic only.

Triggered abilities, quoted/granted abilities, additional costs, conditional and
variable mana, targeting, loyalty costs, intrinsic basic-land abilities, rules
execution, strategic classification and accepted semantics are outside V1.
Actual real-source operation remains separately permissioned. Inspection does
not populate admitted mechanical dossiers, change canonical facts, grant format
legality, activate gameplay, export to AI or authorize a new source acquisition.

## Synthetic validation and future admission

Original fixtures exercise the actual importer, candidate inspector, criteria and
native reasoner across distinct passages and symbols. They validate a reusable
method, not factual understanding of an actual Card. Preservation tests keep
historical imports, Oracle inspections, interpretation pilots, rules calculations,
fictional gameplay and authority records unchanged. Full local/hosted validation
and the existing actual disposable publication/readback gate remain required.

No file in the existing factual-admission `engine_binding()` is changed by this
additive interpreter. Historical manifests are not rewritten. Future admission
still requires exact live pre-state/implementation/evidence checks and independent
production authentication; changed bindings require new deterministic preparation.
Authentication and standing-policy execution remain deferred, not implemented.
