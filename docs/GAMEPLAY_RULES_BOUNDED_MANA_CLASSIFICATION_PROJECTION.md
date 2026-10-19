# Bounded Mana Classification Dependency Projection

## Current review state

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.
Canonical main and branch base: `7082d7c048ef764d5e5ec8d5ea42e2ab9d3dbb28`
(PR #196 merged). Branch: `codex/cr-bounded-mana-classification`.
Result: **BOUNDED_MANA_CLASSIFICATION_DEPENDENCIES_PROJECTED**.
This is SOURCE-VERIFIED, STRUCTURED, NON-EXECUTABLE and REVIEW-BOUND.

Exactly `115.6`, `606.1`, `606.2` add three real source units, taking coverage
from 81 to 84. They supply a shared target-requirement distinction and the bounded
loyalty category needed by mana-classification consumers. Their narrow source
coherence requires no fourth unit. There is no synthetic `606` rule.

## Source verification and anchors

The owner-supplied external official TXT was read and independently verified:
SHA-256 `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`,
977752 bytes, effective 2026-09-25. Existing verification lineage remains
`sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3`;
existing correspondence remains
`sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def`.

Each new anchor uses `MULTI_LINE_RULE_BLOCK_ANCHOR` and
`EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR`. One-line blocks
are valid. Internal terminators are preserved exactly. The fixed release locator
terminates 115.6 before 115.7, 606.1 before 606.2, and 606.2 before 606.3.
It checks the immediate loyalty-section heading context without projecting that
heading. Missing/duplicate markers, malformed numbering, ambiguous continuation,
termination or examples, overlap and unexpected local family shape are rejected.
It is not a general CR parser. All three selected blocks have
`NO_EXPLICIT_OUTGOING_NUMBERED_REFERENCES`; this was checked against their bytes.
No official source prose, examples, attachment paths or TXT are retained.
Historical anchors remain unchanged.

| Unit | Physical lines | Count | Byte start inclusive | Byte end exclusive | Span SHA-256 |
|---|---:|---:|---:|---:|---|
| 115.6 | 861–861 | 1 | 84221 | 84454 | `sha256:f3d24c3d8001e92b65cbb753528c7406b566cf5888a581bd3acef46656a2e850` |
| 606.1 | 2717–2717 | 1 | 339602 | 339692 | `sha256:8e1c075037967528ab69b5d48e4c8cd9c60687a1567027fd4d6cd634d2ce6b6f` |
| 606.2 | 2719–2719 | 1 | 339696 | 339832 | `sha256:e8d80762ab3897d59f1a1b12dc12e1c206d4f6776007a4b28a1612a5a402435c` |

## Target requirement and 115.6

A target requirement may persist even when zero targets are selected. Chosen
count describes actual selection; targeted status under this rule depends on
one or more actually chosen targets. Zero selected targets therefore does not
establish absence of a target requirement. Target legality is a separate question.

The source does not recognize requirements in arbitrary Card or ability text.
Activated/triggered target grammar, keyword targeting, Aura targeting, general
recognition, legality, selection and changes/reselection remain blocked and
unprojected. The `target_requirement_semantics` capability receives bounded source
coverage only for the requirement-versus-count distinction. No parser, selection
mechanism, target counter or targeting runtime exists in this milestone.

## Loyalty classification and 606.1–2

606.1 supplies context: some activated abilities belong to a loyalty category
subject to special rules. 606.2 supplies the loyalty-symbol-in-activation-cost
classification criterion. Its normal planeswalker association is contextual;
it does not establish that only planeswalkers can have loyalty abilities.
No symbol, cost, ability or planeswalker parser is supplied.

`loyalty_ability_classification` is
REPRESENTED_WITH_OPEN_SEMANTIC_DEPENDENCIES. `loyalty_ability_execution` has
INCOMPLETE source coverage and remains BLOCKED. Classification does not imply
execution. Deferred 606.3–606.6 and broader semantic boundaries include activation
timing, stack/main-phase state, prior activation history, counter changes,
modified/combined costs, negative-cost sufficiency and payment. These are outside
the authorized classification scope.

## Append-only consumer reassessments

605.1a and 605.1b each receive DIRECT_REFERENCE_RESOLVED for their explicit
115.6 dependency. Ability target-requirement semantic closure remains OPEN;
real classification execution remains BLOCKED. Historical rule identities,
dependency arrays and projection records are unchanged.

605.1a's original source citation is broad `606`. Its new state is
SECTION_DEPENDENCY_PARTIALLY_REPRESENTED_FOR_CLASSIFICATION. Broad section
resolution remains OPEN; the classification relationship is REPRESENTED;
execution behavior is UNPROJECTED. Derived evidence maps 606.1 and 606.2 to the
loyalty exclusion without inventing either as a direct CR citation from 605.1a.
Projecting these two children cannot resolve the unprojected 606.3–606.6 family.

Activated classification still lacks real target and loyalty-symbol recognition,
library movement, replacement effects, potential mana output and Card/effect
semantics. Triggered classification still lacks target recognition, general
trigger semantics, relationship evaluation, potential output and Card/effect
semantics. All criteria retain descriptive evidence without executable closure.

601.2g gains no direct dependency: its existing 605 section remains source-resolved,
while execution still requires real classification and activation semantics.
Madness remains indirect: `702.35b → bounded casting → 601.2g → 605`.
No new direct Madness citation is created.

## Design-to-source correspondence

PR #196's immutable design package is
`sha256:af42a280e70618102a71381f43122fb98c5e60367f63bd33750677a9a7d9646c`.
Its PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED observations are reviewed anew,
without retroactively changing their authority. The review verifies requirement
versus selected count, targeted status, narrow coherence, absent legality/parser
semantics, loyalty category and loyalty-symbol criterion. Refinements explicitly
preserve the zero-selection nuance and contextual planeswalker qualification.
An additional boundary records missing symbol and cost recognition. There are
no contradicted observations or discrepancies; prior design bytes are unchanged.

## Composite coverage and immutable evidence

The read-only composite preserves eight separate projection identities:

| Projection | Units |
|---|---:|
| Foundational | 20 |
| Direct foundational dependencies | 12 |
| Object-control exceptions | 7 |
| Zone-change exceptions | 12 |
| Zone-change direct dependencies | 12 |
| Bounded casting | 5 |
| Bounded mana abilities | 13 |
| Bounded mana classification dependencies | 3 |
| Total | 84 |

The package at
`reference-reviews/gameplay-rules-bounded-mana-classification-projection/`
contains eight canonical JSON records and a manifest. Its loader independently
pins every file of all eleven prior packages, then reproduces closed authored
findings. Rehashed findings, extra source/TXT, noncanonical bytes, symlinks and
hardlinks are rejected. Offline relocation does not change identities. Offline
loading verifies retained metadata; fresh source reproduction separately requires
the actual exact external artifact. Package writes require a new or empty directory.

Projection: `sha256:315f49def03d5e33e8f5934c4c09cf00da3603152c52839f47472b60f1b34884`.

Package: `sha256:57c9a21ec6a253ad9bfc3a650ec2edc8a389a456eb555a213c3a3f5c673eea73`.

## Readiness, permissions and remaining frontiers

Mana classification now covers 605.1, 605.1a/b, 605.2, 605.5, 605.5a/b plus
115.6 and 606.1–2, but semantic closure remains OPEN and execution BLOCKED.
Mana abilities, casting, object control and Madness remain execution-blocked.
The target real profile `magic-comprehensive-rules-20260925-v1` remains
DESIGN_ONLY / NOT EXECUTABLE / REAL_EXECUTION_PROFILE_NOT_READY.

405.6c, the large 602.2 procedure, shared 603 subsystem, 603.7d/e/f delayed
controller frontier and 613 remain unprojected. Broad 606 and 606.3–6 remain
unprojected. Other retained frontiers include 114, 901.6, 902.6, 904.7, 905.5,
601.2a/c/d/e/i, 601.3, 733, 700.2, 702.47, 118.8, 118.9 and 107.3.

There are no engine, snapshot, execution-profile, fictional-gameplay, targeting,
loyalty, activated/triggered ability, stack, priority, mana-production, Oracle/Card
semantics or simulation changes. Product Rules, Tier A, Card Intelligence, MB2,
canonical state, SOURCE_POLICY_CLEARED_PLANS and writer/admission are unchanged.
Historical acquisition identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`
is preserved. `source_policy_clearance=not_granted`; private retention,
redistribution, free service, commercial service and AI export remain NOT_ESTABLISHED.

## Exactly one next recommendation — not authorized

Recommend **Bounded Mana Stack-Exception Projection**, proposed source scope
`405.6c`. It is a small immediate dependency of 605.3b and avoids expansion into
the large shared activation/trigger subsystems. A future task must require the
exact verified TXT and verify standalone coherence. Inspect 405.6 as parent
context only; if parent projection proves necessary, stop for a separately
reviewed scope rather than auto-expand. This recommendation authorizes no work.

## Validation

Focused source and package tests exercise actual artifact reproduction locally;
CI exercises deterministic offline metadata and rejection proofs. Protected-source
inventory tests cover every prior source file, and eleven-package byte pins cover
historical projections and anchors. Full unittest discovery and the publication
regression provide runtime, source/versioning, fictional gameplay, Product Rules,
intelligence, historical replay and writer regression coverage. Validation results
are reported with the draft PR. No merge or next milestone is authorized here.
