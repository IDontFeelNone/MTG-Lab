# Incremental migration and CI/deployment model

**Status: Architecture v13 is ACTIVE APPROVED; Stages 1–3, the Tier A Card Intelligence vertical and fictional gameplay foundation are merged; gameplay source/evidence/versioning review is pending PM inspection.**
Decision 017 is Accepted by the owner. Architecture v12 is the previous historical
baseline. Governance approval alone authorized no runtime step. Runtime milestones
require separate owner instructions. The implementation sections below record
their original milestone contexts; the latest section states the current scope.

## Stages with acceptance and rollback

| Stage | Scope | Compatibility boundary | Required tests | Rollback | Acceptance |
| --- | --- | --- | --- | --- | --- |
| Governance decision — complete | Owner accepted Decision 017 and the v13 direction; implementation not authorized | Preserve historical 004/009 and v12 replay | Decision/document consistency and Tier-0 rationale | Historical v12 remains interpretable; governance reversal requires an explicit decision | Architecture approval recorded separately from implementation, dataset permission/admission and merge |
| 2 Snapshot contract | Review manifest, identity, provenance, permission/authority and capability contracts; fictional fixtures only | No production schema/identity changes; distinguish content/report/release/query IDs | Canonical hash determinism, tampering, path escapes, extra/missing files, scope, dependency/cycle failures | Keep docs/fixtures; no production effect | Independent inspection and production-ineligible fixture validation agree |
| 3 Minimal attachment seam | Read-only verified handle through current injected-root readers; explicit fixture selection | Existing query envelope unchanged; no runtime acquisition, importer or second store | Fictional game, absent/corrupt/unsupported snapshot, root relocation, no ambient fallback | Retain legacy reader route explicitly | All required authority/compatibility gates precede consumer construction; no hidden default catalog |
| 4 Legacy public snapshot profile | Inventory current typed/promoted/knowledge/audit generations; attach in place where permitted, without copying/reformatting historical bytes | Preserve old IDs, query hashes, source projections and audit scope; source-policy review remains separate | Original historical replay unchanged; old/current calculations distinct; missing source disclosed | Existing public checkout remains interpretable | Old dossiers/audits still reject wrong snapshot; exact graph and source bindings survive |
| 5 Query/projection/collection consumers | Pass explicit attachment/evidence accessors; separate catalog and personal stores | No physical-copy upgrade, name placeholder, Identifier loss or fabricated v3 lifecycle | Actual relationships/aliases, game scope, name requirements, consumer output and historical Finish/materialization gaps | Select original compatible reader/handle explicitly | Writer/consumer validity distinguished from typed materializability and content coverage |
| 6 Intelligence/context adapters | Bind Card/Product/Market/Decision/reasoning input versions | Preserve existing mechanical source format initially; domain ownership and deterministic policy unchanged | Missing/unsupported/corrupt evidence, ABSTAIN, cross-snapshot/as-of conflict, export omission and non-leaking context | Prior explicit profile/attachment retained | No consumer invents prices/rules or fills from memory/network; contexts respect destination scope |
| 7 Existing writer release destination | Separately reviewed protected staging and immutable snapshot release/activation adapter using existing writer/review boundary | Do not bypass repository-root checks or repurpose public publisher; old approvals not portable live authority | Fictional actual-writer end-to-end: pending/rejected/forged/stale decisions, evidence/prestate changes, exact delta, closure, failure restore, concurrency, idempotency | Failed pre-activation build retains previous active root and recovery bytes | Required consumers validate actual writer output; no successful checkpoint/activation for incomplete operation; no public private-data PR |
| 8 Protected integration/deployment | Optional real snapshot only after processing/private-retention/evidence/use permissions and owner admission approval | Code+snapshot+policy selected atomically; no fork/unreviewed code receives credentials | Trusted-code protected suite, offline operation, invalid/missing/expired scope, backup/rollback drill and leak checks | Explicit intact compatible still-permitted prior snapshot | Real authority and permission evidence verified; safe diagnostic/report boundaries operational |
| 9 Generated SQL persistence | Implement approved Decision 010 direction only when performance/use requires it | Snapshot remains authoritative; DB/index output subordinate | Logical row/query/dependency parity, dialect/ordering/Decimal behavior, cache-key mismatch, rebuild and corruption | Use read-only snapshot reader or rebuild approved older generation | DB can be discarded/rebuilt from retained authorized inputs; no ORM fact authority |
| 10 Optional composition and future domains | Pin permitted core/enrichment modules into one effective root; separately authorize Rules/Deck/Competitive/Simulation/AI work | No live overlay authority, implicit precedence or expanded capability claim | Member conflict/identity/dependency and permission intersection, feature-specific deterministic tests | Previous complete effective root | New domain semantics/evidence independently approved, pinned and complete enough for requested operation |
| 11 MB2 readiness revisit | Reuse exact retained 810 recommendation and nine holds under actual established permission scopes | No changed identities, Japanese replacement, owner spelling confirmation or physical assignment inferred | Real production-format artifact checks, actual isolated writer, private audit new calculation, source/closure/privacy checks | Leave existing catalog and completed personal audit untouched | New owner-reviewed plan and later explicit admission decision; architecture acceptance alone never clears MB2 |

SQL generation comes after reader/consumer parity, not before, because there is
no current SQLAlchemy production runtime to migrate. Composition and rich rules
modules are deferred beyond the first single-snapshot attachment scope.

## Public CI tier

- Run schemas, transformations, identity/relationship, query, projection, decision,
  domain-completeness and deterministic tests with original fictional datasets.
  Keep variable cohort sizes and a second fictional game to expose hardcoding.
- Verify snapshots/examples without network or private production data. Include
  tampering, scope/authorization failures, absent optional evidence, path attacks,
  incompatible code/schema/policy and no-fallback cases.
- Retain historical public fixtures and their exact assertions at their original
  snapshot scope; do not apply their census to an expanded current catalog.
  Their continued permitted distribution needs its own policy assessment, not a
  blanket inference from prior publication. This review changes no existing fixture.
- Public contributors need no production credentials. CI output publishes only
  safe fictional data/contract results; no rich source corpus, protected contexts,
  personal audit, signing secrets or auth headers.
- Deterministic fixture generation pins template/generator/version/configuration;
  publication of a fixture never declares any real provider dataset approved.

If a future policy decision requires restricting an old fixture, retain its hashes,
expected behavior and lawful authorized replay placement; add public fictional
equivalent contract coverage. Do not silently remove failures, repin old expected
hashes or expose private production data to restore a public test.

## Protected production-integration CI tier

- Run only reviewed trusted code/dependencies on scoped protected runners. No
  fork PR or arbitrary caller script receives production mounts or credentials.
- Select exact approved snapshot, source evidence and permitted operations.
  Personal integration inputs are separately scoped synthetic or expressly
  authorized private fixtures; the catalog secret is not the collection secret.
- Run complete relevant schema/graph/provenance/admission/query/collection/
  intelligence integration and actual writer/activation recovery checks.
  An unsupported domain/source remains unsupported; never fabricate fixture facts.
- Keep data, logs, DBs, contexts and caches private/retention-bound. Emit only
  reviewed contentless/aggregate conclusions publicly, tied to reviewed code
  and permitted identity metadata. No general public artifact upload.
- Report tested code/snapshot/check-profile identities, exit status, failures,
  setup errors and unrun checks separately. Protected success does not license
  redistribution or authenticate an owner decision by itself.

## Deployment flows

| Mode | Explicit flow | Failure behavior |
| --- | --- | --- |
| Public developer checkout | Install public code, choose fictional fixture profile, verify and attach, run query/domain tests; original dataset not required for meaningful core coverage | Missing fixture is a blocked requested operation, not silent production selection |
| Optional operator dataset | Supply manifest/bytes through supported explicit acquisition/intake, establish permission/scope, validate dependencies and trusted admission, seal and select | Caller-supplied or incomplete material stays noncanonical; untrusted/forbidden required fields block |
| Production | Pin reviewed code/configuration; transfer exact authorized release; verify authority/permissions/compatibility; run consumer acceptance; stage DB if required; atomically activate | Preserve active allowed snapshot on failed update; no public seed/live provider fallback |
| Offline operation | Attach locally retained permitted complete snapshot/evidence with exact requested as-of/config/seed | Missing required bytes or invalid use scope returns blocked/replay-unavailable; no network demand hidden in queries |
| Snapshot update | Explicit acquisition → candidates → review/permission → actual writer → validate → seal → compare-and-swap expected current root | Concurrent/stale bindings or unsupported new scope block; no automatic reassessment/physical assignment |
| Rollback | Explicitly select intact, compatible, still-permitted old root and matching cache/rebuild; bind new operations to chosen root | Incompatible code/schema/expired permission means rollback unavailable; old personal audits remain unchanged |

Production result identity includes code revision, snapshot/query IDs, schema/
policy/transform/engine versions, configuration and source manifests, independent
market/user/rules inputs, and PRNG algorithm/version/seed when applicable. A fresh
render timestamp is display metadata, not silently a new analytical input.

## V13 Stage 1 — Fictional Canonical Snapshot Attachment

**Implementation status: merged in PR #176.** The owner separately
authorized this fictional-only runtime checkpoint after architecture acceptance.
See [the API and supported contract](V13_STAGE1_SNAPSHOT_ATTACHMENT.md).
The numbered migration rows above are planning workstreams, not separately approved
milestones. Stage 1 is restricted to the fictional contract/attachment subset.

Implemented scope:

- Generic snapshot manifest verification and an immutable fictional snapshot fixture.
- Explicit read-only attachment through existing query/collection readers.
- Integrity, version and compatibility validation; missing/corrupt/incompatible
  snapshots fail closed.
- Relocation determinism, no ambient fallback, and preservation of the existing
  explicit legacy/public profile and all historical bytes/hashes.

Explicitly excluded: real MB2 data; protected/provider datasets; production
admission; provider acquisition; SQL persistence; module composition; writer
destination changes; Rules Intelligence; Deck Intelligence expansion; simulation;
AI transport/model integration. Architecture approval does not clear source
policy, select a production snapshot or authorize any of these operations.

## V13 Stage 2 — Legacy/Public Snapshot Profile Review

**Review status: separately authorized and complete, pending PM inspection.**
See [the retained review and Stage 3 blockers](V13_STAGE2_LEGACY_PUBLIC_PROFILE_REVIEW.md).
No real snapshot profile or runtime migration is implemented. The current query
requires mixed representations, audit context and explicit roots; historical
materialization gaps and operation-specific rights remain unresolved.

## Permission and closure contract — review complete

PR #177 is merged. The separately owner-authorized
[Legacy/Public Profile Permission and Closure Contract](V13_LEGACY_PUBLIC_PERMISSION_CLOSURE.md)
is complete, pending PM review, at canonical main
`d4e673a31714e30eb4056c43fca76b159008c813`.
The Stage 1/2 sections above preserve their original milestone context.

## Historical Stage 3 recommendation — separately authorized and implemented below

**V13 Stage 3 — Legacy/Public Compatibility Snapshot Profile** is
**READY_FOR_NON_PRODUCTION_STAGE3** as an engineering scope only: Tier A's40
in-place dependencies, explicit both-root parity, separate source/audit context,
a bounded read-side audit inventory and unsupported-capability failures before I/O.
No new corpus, source-derived value reformatting or production authority.
The production operator profile remains BLOCKED and the underlying seven operation
permission scopes remain NOT_ESTABLISHED. A non-production flag is no license.

No runtime work begins here. No writer/default-root/projection/schema change,
real-data admission, provider acquisition, SQL/composition, protected snapshot,
service, rules/simulation/AI implementation or source-policy clearance is authorized.
Future code must preserve fictional/legacy behavior, exact historical hashes,
known incompleteness and existing production data. See the closure contract's
explicit Stage 3 acceptance criteria and stop conditions.

## V13 Stage 3 — Legacy/Public Compatibility Snapshot Profile

**Implementation status: merged in PR #179.** The owner separately authorized only non-production Tier A after
PR #178 merged. The historical recommendation above records its original
authorization context and is not the current task state.

The separately named `legacy-public-compatibility-v1` profile verifies the exact
40-file in-place closure: 33 core catalog files, five SourceRecord references and
two audit-context files. Existing query/repository/Collection readers receive an
explicit bounded read inventory; the other 28 audit files and three unselected
SourceRecords are not read. Unsupported Tier B/C operations fail before excluded
I/O. Empty namespaces, one game and absent optional knowledge state are bound.
No real source values are copied or reformatted into new catalog artifacts.

The existing explicit both-root query has 1,566 entities: 399 Cards, 928 Printings,
235 Identifiers, two Finishes, Game and Product. Its query identity remains
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`.
Bare-constructor scope/root inference, unrestricted legacy behavior and Stage 1's
fictional contract remain unchanged. The fixed profile blocks legitimate expanded
catalog bytes instead of silently repinning or substituting an old catalog.

`production_eligible=false`, `approval_state=not_granted`,
`source_policy_clearance=not_granted` and processing permission false remain fixed.
All seven operation permissions remain NOT_ESTABLISHED; the production operator
profile remains BLOCKED. Known Finish gaps, incomplete typed materialization,
zero Product slots and absent rules/mechanical evidence remain explicit.

The [Stage 3 API and validation scope](V13_STAGE3_LEGACY_PUBLIC_COMPATIBILITY_PROFILE.md)
describes fictional relocation/security tests, selected-source/audit boundaries,
unchanged historical replay and the permitted current-public in-place parity
characterization. This is no writer, acquisition, permission or production
activation milestone.

## V13 Tier A Card Intelligence & Acquisition Attachment Integration

**Implementation status: merged in PR #180.** The owner separately authorized this
existing-consumer integration after PR #179 merged, from canonical main
`4ef94dd704b052a7fbaf15d034fe65c015be256f`.

The explicit mechanical reader constructs one query through
`CanonicalQueryEngine.from_attachment`. Card acquisition reuses the same
MechanicalCardIntelligence/query, including exact Printing relationships. The
semantic query and ReasoningContextBuilder use that same query; contexts preserve
their existing canonical snapshot binding. Outer catalog/profile binding remains
separate from mechanical source/acquisition, dossier and request identities.

Mechanical retained-source validation remains independent and outside Tier A.
Catalog drift, source drift, reader retargeting and mismatched expected query or
request snapshots block instead of falling back to legacy roots. Legacy
constructors and retained dossier/reconstruction formats remain unchanged. No
provider lookup, corpus copy, new purchase rule, real-data admission or permission
clearance is introduced. See [the API and tests](V13_TIER_A_CARD_INTELLIGENCE_ATTACHMENT.md).

Tier B Audit-Context Capability Design Review is deliberately **DEFERRED**. The
implemented vertical needs no excluded audit/history API; existing Tier B/C gates
remain intact. All fixed non-production/permission flags and seven NOT_ESTABLISHED
operation states remain unchanged. The production operator profile remains BLOCKED.

## V13 Functional-Role and Contextual-Comparison Attachment Integration

**Implementation status: merged in PR #181.** The owner separately authorized
this final small Card Intelligence
consumer integration after PR #180 merged, from canonical main
`bea66e1b52eae0c20dc82a6959b2ecbd7c9698e6`.

`FunctionalRolePilot.from_mechanical` requires and reuses the exact attached
MechanicalCardIntelligence. `ContextualCardComparisonPilot.from_roles` reuses that
exact roles instance. Their query, semantic query and ReasoningContextBuilder are
the same objects already established by MCI. Live catalog binding remains separate
from unchanged mechanical, role, comparison, Decision and reasoning artifact IDs.
Catalog/source/role-plan/vocabulary/context drift blocks without fallback or
refreshed hashes. Existing legacy constructors remain unchanged.

The original 15 Cards and 30 candidates remain pending/requires_review. The
three-Card comparison, eight pending roles and unknown human-reviewed-context
metric still produce ABSTAIN with null selection. No role approval, knowledge
write, scoring, selection, legality or verified interaction is introduced. The
profile stays Tier A; Tier B Audit-Context Capability Design Review is deliberately
**DEFERRED** because the completed vertical requires no full audit operation.
Source permissions, MB2 pending state, source-policy registry and writer/admission
behavior remain unchanged. See [the API and limits](V13_ROLE_COMPARISON_ATTACHMENT_INTEGRATION.md).

## Gameplay Rules & Interaction Intelligence Foundation

**Implementation status: merged in PR #182.** The owner separately authorized
this design/contracts/generic primitives/fictional-proof domain after PR #181
merged, from canonical main
`da8c5a4053ba749a1c0af9b6044ee0560c10156e`.

The package `src/gameplay_rules/` adds immutable versioned rules/state/action/
semantics/result/transition contracts and a deterministic fictional two-player
kernel. Explicit snapshot selection, rule references and capability manifests
preserve unknown/unsupported outcomes. Check and apply are separate; payment,
priority, stack, land allowance, zone changes and one life-threshold SBA have
bounded fictional proofs. No real Card semantics, real rules corpus, arbitrary
Oracle parsing, complete Magic rules, strategy, deck/format legality or simulation
is implemented. Product Rules remain the unchanged Product/Pack/collation domain.
See [the contracts and explicit limitations](GAMEPLAY_RULES_INTELLIGENCE.md).

This fits the existing v13 future-domain boundary without Decision 017 or Tier-0
changes. Existing Tier A catalog/query/Collection and Card Intelligence behavior,
production canonical data, MB2 pending state, source-policy registry and writer/
admission/OIDC remain unchanged. Bounded first-party source access attempts
produced EVIDENCE_UNAVAILABLE, no current rules/version verification and no
permission clearance; all executable proof data is project-authored fiction.

## Gameplay Rules Source/Evidence Intake & Versioning

**Implementation status: merged in PR #183.** The owner separately authorized
this review-only milestone after PR #182 merged, from canonical main
`65f209032dfed80735146a01531c87d0d0b0861b`.

`src/gameplay_rules/source_evidence/` provides immutable metadata/review/version
contracts, bounded explicit first-party intake and scoped release selection.
Official index designation, source authority, exact artifact bytes, effective/
version metadata, reviewed supersession/update incorporation and per-operation
permissions remain separate bindings. Evidence unavailability, ambiguity and
conflict remain explicit; there is no implicit latest/max-date/filename fallback.
The June PDF and reported later update require verified first-party closure,
not assumption. The single official rules-index access attempt on 2026-10-16
returned ACCESS_UNAVAILABLE under the environment network policy, with no origin
HTTP status, source body/hash or designated artifact. The retained review is
NOT_READY_FOR_RULE_PROJECTION / CURRENT_RULES_RELEASE_NOT_VERIFIED; no official
version/effective date or update incorporation was established.

This is not rules projection, executable real-card semantics, a new source-policy
clearance, production admission, a real corpus bundle or runtime activation.
Existing evidence/provider/registry licensing gates, the fictional gameplay
kernel and all catalog/intelligence/writer/historical boundaries are unchanged.
See [source evidence and versioning](GAMEPLAY_RULES_SOURCE_VERSIONING.md).

## Official Gameplay Rules Release Discovery Closure

**Implementation status: implemented as a metadata-only review/verification
handoff, pending independent Project Manager inspection.** The separately
owner-authorized milestone starts from canonical main
`988ac4bc384da8e4b62f89790727c2e79373eea2` after PR #183 merged. It fits the
existing v13 evidence domain; Decision 017 and the fictional kernel are unchanged.

The original ACCESS_UNAVAILABLE observation and eight-file package are preserved.
A distinct PM_SUPPLIED_FIRST_PARTY_OBSERVATION dated 2026-10-16 establishes
VERIFIED_METADATA_ONLY designation of the September 25, 2026 Comprehensive Rules
in DOCX/PDF/TXT as of that review; the observed TXT/PDF filenames contain
20260925. Its observed 701.71 Empower Jace marker establishes the identified
Reality Fracture change's incorporation,
not verification of the full bulletin diff. Codex did not independently fetch
Wizards; no HTTP receipt, exact artifact URL/basename, hash or byte length is
invented. The new sibling review package binds the earlier historical package.

An explicit offline local TXT verifier hashes bounded bytes and checks title,
effective date and selected markers. It copies no body, performs no network
request, invokes no RawSnapshotStore and authorizes no projection. No real TXT
was supplied. NOT_READY_FOR_RULE_PROJECTION remains, narrowed to
OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED. All source-content permissions stay
NOT_ESTABLISHED and existing evidence/registry gates remain unchanged. See
[the provenance and local handoff](GAMEPLAY_RULES_RELEASE_DISCOVERY_CLOSURE.md).

## Next implementation candidate — NOT AUTHORIZED

**Owner-Supplied Comprehensive Rules Artifact Verification** is the recommended
smallest prerequisite. Supply the exact designated TXT locally, verify its exact
byte identity against the retained request, and perform an explicit source review.
This closes an integrity/readiness gap; it does not establish source permissions
or authorize a real rules projection.

No real rules projection, Oracle parser, Card semantics intake, gameplay
simulation, Deck/format legality, additional Tier A migration, Tier B audit
support, SQL, protected snapshot, provider/Card acquisition, MB2 admission or
source-policy clearance begins automatically. The next milestone requires
separate owner authorization even if a future reviewed selection is complete.
