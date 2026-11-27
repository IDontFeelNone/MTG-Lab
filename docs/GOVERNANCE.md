# MTG Lab Governance

This document records the Project Owner-approved operating workflow. It governs
roles, approvals and documentation continuity without changing
[Architecture v13](ARCHITECTURE.md) or [Accepted Decision 017](DECISIONS.md#decision-017--public-architectural-authority-and-immutable-operator-canonical-snapshots).
Existing contributor guides supply engineering procedures within these boundaries;
this current clarification supersedes older summaries that imply mandatory
Senior PM review or updates to every state document for every routine change.

## Roles and authority

| Role | Responsibility |
| --- | --- |
| Project Owner | Owns direction, explicitly approves milestones and scope, approves architectural changes, and makes final merge decisions. |
| Project Manager (PM) | Coordinates routine work, verifies canonical repository state, proposes bounded milestones, independently reviews Codex changes and CI, and recommends MERGE, REVISE or HOLD. The PM does not independently authorize owner-gated scope. |
| Codex — Lead Software Engineer | Implements explicitly approved scope, maintains engineering correctness, runs relevant validation, creates draft PRs, and stops for review before merge or follow-on work. |
| Senior Project Manager | The separate Card Reseller ChatGPT conversation, providing occasional independent technical, architectural and project audits. It is not a mandatory gate for every routine milestone, prompt or PR and does not replace owner authority. |

Conversation statements, Git authorship, checksums and CI results do not constitute
authenticated review events or new source-use, admission or execution permission.
No new reviewer authentication or authorization mechanism is established here.

## Standard workflow

1. The PM verifies canonical GitHub main and proposes bounded work.
2. The Project Owner explicitly approves the milestone and scope.
3. Codex implements only that authorized scope.
4. Codex runs relevant validation and opens one draft PR for the milestone.
5. Hosted CI, exact-head validation and any tested merge identities are checked.
6. The PM independently reviews the changes, validation and preservation.
7. The PM returns MERGE, REVISE or HOLD as a recommendation.
8. The Project Owner makes the final merge decision.
9. Canonical main and applicable post-merge checks are verified.
10. A subsequent milestone requires separate authorization.

There is no automatic merge or follow-on implementation. An approved direction,
recommendation or roadmap entry does not authorize a milestone. Pending and
failed checks remain visible; successful checks are not unnecessarily repeated.

Canonical GitHub history, repository contracts and accepted owner decisions
establish project state. Conversation memory cannot override them. Record new
authorized scope in reviewable repository work; do not reinterpret historical
authorizations or treat an old handoff as the current instruction.

## Documentation authority map

| Document | Responsibility |
| --- | --- |
| [VISION.md](../VISION.md) | Enduring mission and aspirational capabilities; first useful release distinguished from the ultimate research ambition. |
| [README.md](../README.md) | Concise project introduction and navigation. |
| [GOVERNANCE.md](GOVERNANCE.md) | Roles, approvals and workflow. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Approved architecture and authority boundaries. |
| [DECISIONS.md](DECISIONS.md) | Accepted engineering decisions. |
| [PROJECT_INVENTORY.md](../PROJECT_INVENTORY.md) | Verified implemented functionality and limitations. |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current project state and blockers. |
| [HANDOFF.md](HANDOFF.md) | Current operational handoff and exact next action. |
| [ROADMAP.md](ROADMAP.md) | Approved, proposed, deferred and aspirational work. |

These responsibilities do not override architecture, accepted decisions,
source-policy gates or the [Research Log's authority](RESEARCH_LOG_ARCHITECTURE.md).
Older vision documents retain their historical intent; the root VISION.md is the
current product vision. Old “current” headings inside explicitly preserved
historical sections retain their original dates, scope and authorization only.

## Status vocabulary

Maturity and authorization are independent. Label the exact capability and scope,
and state blockers separately rather than inferring permission from implementation.

| Status | Meaning |
| --- | --- |
| IMPLEMENTED | A capability exists in merged code with its stated evidence, tests and limitations; this grants no broader production or execution authority. |
| APPROVED_NOT_IMPLEMENTED | The owner explicitly authorized a bounded milestone that has not yet been implemented; partial work must be reported separately. |
| PROPOSED_NOT_AUTHORIZED | A recommendation or technical direction awaits explicit implementation approval. |
| DEFERRED | Work is parked and must not begin without a new authorization. |
| ASPIRATIONAL | A long-term desired capability, without implementation commitment. |
| BLOCKED | An identified evidence, permission, dependency or validation prerequisite prevents the specified operation. |

Generic simulation does not establish accurate real-product collation. Fictional
gameplay is not real-Magic execution. Retained rules are not complete semantic
understanding. Full deck intelligence, AI tutoring and overlooked-card discovery
remain aspirations unless separately documented as implemented within a verified
scope.

## Rules-source workflow

For source-dependent work, the PM proactively tells the Project Owner when the
exact Comprehensive Rules TXT must be attached to the Codex conversation. A
path in another conversation's sandbox is not a transfer mechanism. Codex must
independently verify the supplied artifact and required provenance before use.
Documentation-only work does not require the source attachment.

Source verification, operation-specific source-use permissions, semantic review,
admission and execution remain separate gates. Technical owner authorization
does not prove third-party licensing rights. Public availability, historical
publication and metadata labels do not grant blanket permission. Existing
NOT_ESTABLISHED states remain unchanged without supported evidence and the
appropriate disposition. See [source versioning](GAMEPLAY_RULES_SOURCE_VERSIONING.md).

## Lightweight maintenance and preservation

Update only documentation materially affected by a milestone. Keep VISION.md
stable across implementation churn and GOVERNANCE.md stable unless the operating
workflow changes. Use links instead of repeating descriptions or maintaining
parallel status lists. PR bodies and validation receipts hold exact delivery
results; stable documents need not be rewritten to mirror every CI update.

Preserve byte-pinned records, original hashes, prior suffixes and historical
authorization context. The documentation-continuity compatibility adapter is
test-only: it reverses only exact approved successor bytes, checks predecessor
hashes and leaves the original reconstruction assertions intact. It neither
permits arbitrary future headers nor requires future milestones to extend it.
If a later edit encounters a preservation conflict, report it rather than
loosening checks or rebaselining history.

## Individual admission and future bounded delegation

Current production canonical admission requires an independently authenticated
exact-operation decision through the existing trusted-host boundary. Approval
covers the complete bound cohort rather than individual database transactions.
A conversation, digest, serialized decision or isolated-test capability does not
supply production authentication.

Future bounded standing authorization is established product direction, not
implemented delegation. Policy creation, amendment and revocation must use
independently authenticated Owner authority with the same iPhone-first usability
as individual approval. A host must bind every qualifying execution to the exact
active policy and its evidence, limits, validation, revocation and escalation
conditions. It must not impersonate a new human review for each execution or
expand its own permissions. Source-use, factual, semantic and gameplay authority
remain independent.

Decision 017 does not already authorize standing-policy execution. Any necessary
future amendment must identify the changed security properties, preserve the
remaining safeguards, and receive independent review and explicit Owner approval
before implementation. No authentication, enrollment or standing-policy runtime
is implemented by the candidate interpretation milestone.
