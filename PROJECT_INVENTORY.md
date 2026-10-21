# Current implementation inventory — Activated Ability Procedure Design

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.
Canonical main / branch base: `9e1335d53458913dec1907e2922b9e99339cc3c5`
(PR #198 merged). Branch: `codex/activated-ability-procedure-design`.
The owner separately authorized **ACTIVATED ABILITY PROCEDURE DESIGN** only.

The append-only [design](docs/GAMEPLAY_RULES_ACTIVATED_ABILITY_PROCEDURE_DESIGN.md)
and `reference-reviews/gameplay-rules-activated-ability-procedure-design/`
establish review contracts for the inspected `602.2` / `602.2a` / `602.2b` cluster.
The exact owner artifact is 977752 bytes, effective 2026-09-25, SHA-256
`8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
New source-inspection findings are separate from PR #196's historical
PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED observations.

The three-unit cluster is coherent for a future bounded source review. Its
`601.2b`–`601.2i` procedure import and `601.2f` cost analogy leave missing
`601.2c/d/e/i`, `733`, `701.20a` and independent gameplay semantics unresolved.
The design adds **0** projected units; the current projection allowlist is empty.
Coverage remains **85** units across **nine** projections, and
`605.3 → 602.2` remains an unresolved projected-source dependency.
No projected identity, registered anchor, real GameplayRulesSnapshot or execution
path is added. Real execution remains BLOCKED; the real profile remains
DESIGN_ONLY / NOT EXECUTABLE.

Exactly one subsequent recommendation awaits owner approval: **Bounded Activated
Ability Procedure Projection**, proposed allowlist `602.2`, `602.2a`, `602.2b`
(**3** units). Future milestone authorized: false; future source projection
authorized: false; future milestone begun: false. Stop at one draft PR for
independent PM review; do not merge or begin that recommendation.

---

## Preserved historical milestone records

The complete earlier document follows unchanged. Its former current headings,
next recommendations and “NOT AUTHORIZED” records retain their original authority.
The subsequent owner instruction authorizes only the present design milestone;
it does not retroactively change those records.

# Current implementation inventory — Bounded Mana Stack-Exception Projection

## Current status — bounded mana stack-exception projection

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.
Canonical main / branch base: `c9f46a2768cdee5e32f72e27d0255c6d4efbe175`
(PR #197 merged). Branch: `codex/cr-bounded-mana-stack-exception`.
**BOUNDED_MANA_STACK_EXCEPTION_PROJECTED** adds exactly `405.6c`:
**1** new source unit, **85** total across **nine** distinct projections.
The exact owner TXT was verified (977752 bytes, effective 2026-09-25,
SHA-256 `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`).
No source body, parent anchor or TXT is retained.

405.6 was observed only as structural parent context and remains unprojected.
Child-only scope is coherent for the existing bounded 605.3b consumer.
405.6c adds immediate mana-ability resolution, immediate mana-plus-other-effect
context without a finer ordering claim, and a distinct priority-return finding
limited to the activated-mana case. It supplies no triggered priority-return rule.

Append-only reviews resolve `605.3b → 405.6c` as DIRECT_REFERENCE_RESOLVED
and `405.6c → 605` as SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY, binding
all 13 existing concrete 605 units. No synthetic 605 unit is created.
Activated no-stack evidence remains 605.3b; triggered no-stack and immediate
resolution evidence remains 605.4a. The latter has semantic overlap without a
direct 405.6c citation. Historical rule identities, dependency arrays, anchors
and all twelve prior packages remain unchanged.

General stack and priority semantics remain OPEN; real execution remains
BLOCKED. 601.2g and Madness improve only through existing indirect routes;
109.4a controller attribution remains separate. 602.2, 603, 603.7d–f and 613
remain unprojected; broad 606 remains partially represented and OPEN, with
606.3–6 unprojected. Mana abilities, casting, object control and Madness remain
execution-blocked. The real profile remains DESIGN_ONLY / NOT EXECUTABLE /
REAL_EXECUTION_PROFILE_NOT_READY. Runtime, Oracle/Card semantics, simulation,
source policy, Product Rules, Tier A, Card Intelligence, MB2 and writer/admission
remain unchanged.

Exactly one next recommendation: **Activated Ability Procedure Design**,
centered on `602.2` with the provisional `602.2` / `602.2a` / `602.2b` cluster
as design input, **0** projected units; **NOT AUTHORIZED**. The exact source TXT
is required to inspect procedure shape and dependencies in that future design.
No future projection allowlist is authorized. Do not begin it, merge or activate real rules.
See [bounded stack-exception projection](docs/GAMEPLAY_RULES_BOUNDED_MANA_STACK_EXCEPTION_PROJECTION.md) for source anchors,
provenance, consumer reassessments, readiness and protected-state details.

## Historical status and retained context

**Architecture v13 — ACTIVE APPROVED. Decision 017 remains Accepted.**
Canonical main and branch base are
`a9943fc8ca89ced4d3d288926f63fede12f4b57a`; PR #195 is merged. Branch:
`codex/mana-ability-direct-dependency-design`.

**Mana Ability Direct Dependency Design** adds **0** real source units.
Coverage remains **81** across seven separate projections. All ten prior
retained rule/design packages, existing rule identities, source anchors and
append-only reviews remain byte-identical. The external TXT is neither required
nor opened; no source projection, new anchor or Wizards fetch occurs.

Retained bounded-mana evidence verifies exactly five outgoing targets:
`115.6`, `606`, `602.2`, `405.6c`, `603`. All remain UNRESOLVED / UNPROJECTED.
Detailed observations about their unprojected bodies are
**PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED**. The new immutable records
remain DESIGN_ONLY / NON_EXECUTABLE; existing citations are not rewritten.

The design separates four groups: bounded mana-classification dependencies;
bounded stack-exception context; the large general activated-ability procedure;
and the large shared triggered-ability subsystem. Target requirement is distinct
from chosen targets and target legality. Loyalty classification is distinct from
loyalty execution. A provisional `606.1`/`606.2` classification scope does not
resolve the whole section-level `606` citation. `405.6c` alone is provisionally
coherent with retained mana-exception context; optional parent `405.6` is reviewed
without automatic admission. General activation and triggers retain separate
contracts and their specific mana exceptions.

The read-only consumer matrix binds `605.1a`, `605.1b`, `605.3`, `605.3b`,
`605.4`, `109.4b` and `601.2g`. The shared triggered subsystem serves both
`605.4` and `109.4b`, including delayed-controller frontier `603.7d/e/f`.
Parent delayed-trigger context is preferred provisionally over isolated controller
children, pending future scope design and source verification. Existing broad
`601.2g → 605` and `109.4a → 605` remain
SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY. Section resolution supplies no
semantic closure or execution readiness; hypothetical stack-controller
attribution remains open. No new direct CR citation is invented.

Recommend exactly one next milestone: **Bounded Mana Classification Dependency
Projection — NOT AUTHORIZED**. Provisional allowlist: `115.6`, `606.1`, `606.2`
(**3** units). It addresses the shared target-requirement nuance and activated
loyalty exclusion while leaving complete `606`, target grammar, stack, activation,
triggers and runtime unresolved. That future projection requires the exact
verified owner-controlled TXT and reviewed raw-byte block anchoring; this design
does not begin it or claim any future source verification.

[The direct-dependency design](docs/GAMEPLAY_RULES_MANA_ABILITY_DIRECT_DEPENDENCY_DESIGN.md)
records scope comparisons, grouping, consumer bindings and the next decision.
Its append-only package is
`reference-reviews/gameplay-rules-mana-direct-dependency-design/`.
Mana classification, activated/triggered behavior, object control, casting and
Madness remain EXECUTION_BLOCKED. The real profile remains DESIGN_ONLY /
NOT EXECUTABLE / REAL_EXECUTION_PROFILE_NOT_READY.
**FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605** remains enforced.

Gameplay runtime, fictional behavior, Oracle/Card semantics and simulation remain
unchanged. Product Rules, Tier A, Card Intelligence, canonical catalog, MB2,
`SOURCE_POLICY_CLEARED_PLANS` and writer/admission remain unchanged. Historical
acquisition identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`
is preserved. `source_policy_clearance=not_granted`; private retention,
redistribution, free/commercial service and AI export remain NOT_ESTABLISHED.
Stop at one draft PR for PM review; do not merge, activate real rules or begin
another milestone. Historical bodies below retain their original authority,
findings and scope.

## Historical merged projection context

The following preserves the prior milestone's implementation and authorization
context. Its source-TXT precondition, pending-review description, historical
branch base and next-candidate recommendation belong to that earlier milestone;
the current review/design boundary is stated above. Later review does not rewrite
historical evidence or its original permissions.

# Current implementation inventory — Foundational Comprehensive Rules Projection

**Architecture v13 — ACTIVE APPROVED architecture. Decision 017 is Accepted.**
Architecture v12 remains the preserved historical baseline. Reviewed canonical
main: `54cd3c33875a949d9a06fb70c336f0b55fb5aef9`; PR #185 is merged.

**Core Comprehensive Rules Projection — Foundational Rules Subset** is implemented
as a structured **NON-EXECUTABLE** review projection, pending independent Project
Manager inspection. The separately authorized scope is exactly **20** references:
`101.1`, `101.2`, `101.2a`, `101.3`, `102.1`, `102.2`, `108.1`, `108.3`, `108.4`,
`108.4a`, `109.1`, `109.3`, `109.4`, `110.1`, `110.2`, `110.2a`, `400.1`, `400.2`,
`400.3`, `400.7`. Parent references do not implicitly select their children.

The external owner-supplied TXT was required to reproduce the existing verifier's
exact **977752-byte** source with SHA-256
`8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`, effective
**2026-09-25**. The verification result remains
`sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3`;
the correspondence review remains
`sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def`.
No new Wizards fetch or later currentness claim is made. The prior first-party
designation remains observed as of 2026-10-16; no full bulletin diff is claimed.

`src/gameplay_rules/projection/` supplies a separate immutable review contract,
release-specific twenty-line locator and strict package/source verification.
`reference-reviews/gameplay-rules-foundational-projection/` contains exactly
`projection.json` and `manifest.json`: project-authored paraphrases, concepts,
limitations, precise source anchors/span hashes and a dependency/exception graph.
Offline integrity checks do not claim fresh source-span proof; source-aware
verification requires access to the exact external TXT and recomputes all spans.

`104.3a`, `111.2`, `112.2`, `113.10` and `407` remain unresolved. `109.4a`–`109.4g`
and `400.7a`–`400.7k`, `400.7m` remain individually recorded unprojected exceptions.
They do not add selected rules. The graph is not complete semantic closure, and
its baseline control/zone-identity descriptions cannot become complete policies.

The owner's bounded authorization permits transient source inspection and the
retained authored projection/metadata only. No official rule prose, source TXT or
absolute local source path enters the repository. Historical source, discovery
and artifact-verification packages remain byte-identical with their original
`projection_authorized=false` values; they are not retroactively authorized.
`source_policy_clearance=not_granted` and `admission_eligible=false` remain fixed.
Broader raw retention, redistribution, service use and AI/model export permission
remain unestablished. Catalog and rules-source permissions remain separate.

No real `GameplayRulesSnapshot`, real execution profile, engine change, fictional
profile change, Oracle ingestion, real Card semantics, mana/payment,
timing/priority, casting/stack-resolution, SBA expansion or simulation is added.
No general/full Comprehensive Rules parser is introduced. Prior gameplay evidence
and protected Card Acquisition identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`
remain unchanged. Tier A, canonical catalog, pending intelligence artifacts,
markets, collections, MB2 pending state, production permissions, licensing gates
and writer/admission/OIDC behavior are preserved.

The [projection contract and reproduction instructions](docs/GAMEPLAY_RULES_FOUNDATIONAL_PROJECTION.md)
describe review scope, exact anchoring, graph boundaries and both verification
modes. The [artifact-verification history](docs/GAMEPLAY_RULES_ARTIFACT_VERIFICATION.md)
remains the source-byte/provenance record. Actual full regression, publication and
exact-head hosted-check results belong to this milestone's draft PR review record.

Stop after **one draft PR** for independent review. Do not merge or start the next
milestone. The recommended next candidate is **Foundational Dependency and
Exception Coverage Review — NOT AUTHORIZED**, requiring a separately approved
exact allowlist and source-use boundary. No implementation follows automatically.

## Preserved evidence lineage and operational boundaries

**Owner-Supplied Comprehensive Rules Artifact Verification & Readiness Closure**
is merged in PR #185 as a review-only metadata milestone. Its verifier and retained
package are unchanged. This fits Architecture v13 with no Tier-0 change and no
Decision 017 modification.

**Official Gameplay Rules Release Discovery Closure** is merged in PR #184;
**Gameplay Rules Source/Evidence Intake & Versioning** is merged in PR #183.
The original Codex `ACCESS_UNAVAILABLE` observation and its historical
`CURRENT_RULES_RELEASE_NOT_VERIFIED` / `NOT_READY_FOR_RULE_PROJECTION` result
remain unchanged. The PR #184 package is also byte-identical. Its distinct
`PM_SUPPLIED_FIRST_PARTY_OBSERVATION` remains `VERIFIED_METADATA_ONLY` designation
as of **2026-10-16**: DOCX/PDF/TXT, the `20260925` TXT/PDF family, and rules effective
**September 25, 2026**. The identified `701.71` / Empower Jace Reality Fracture
change is incorporated; the full bulletin diff is not verified. Codex did not
independently fetch Wizards, and no new network review occurred.

The owner separately supplied the exact local TXT and stated it came directly
from the designated official link without intentional modification. The offline
verifier reports `VERIFIED_EXPECTED_ARTIFACT`, UTF-8, **977752 bytes**, and SHA-256
`8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
The explicit retained operation timestamp is `2026-10-16T22:15:00-04:00`.
Title, effective date, 701.71 and Empower Jace checks all pass. This is locally
verified byte identity with owner-supplied provenance, not Wizards cryptographic
authentication or independent Codex network verification. No source body or local
absolute path enters the public package; no RawSnapshotStore is used.

The successful result plus its explicit source-correspondence review closes
`OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED`. Reproducing the existing selection yields
**READY_FOR_RULE_PROJECTION**, still only for current designation observed as of
2026-10-16 and effective release 2026-09-25. The same existing release candidate is
bound to exact bytes; no new logical release or timeless current alias is created.
In that historical metadata package, `projection_authorized=false`,
`admission_eligible=false`, `source_policy_clearance=not_granted` and
`content_retained=false` remain fixed. That readiness alone did not authorize a
structured rules projection; the present bounded task supplies separate authority.

The append-only metadata package is
`reference-reviews/gameplay-rules-artifact-verification/`. The source TXT remains
external owner-controlled input and is never copied into the repository, data,
fixtures, RawSnapshotStore or another evidence corpus.
`src/gameplay_rules/source_evidence/` retains distinct artifact, source,
observation, release, review, selection and operation-permission identities.
The lane evaluates eight source-specific operations; source-content private
retention, redistribution, free/commercial service and AI/model export remain
**NOT_ESTABLISHED**. Existing licensing gates are unchanged.

**Gameplay Rules & Interaction Intelligence Foundation** is merged in PR #182.
The `src/gameplay_rules/` fictional kernel remains unchanged:
`GameplayRulesEngine.evaluate_action` distinguishes LEGAL, ILLEGAL, INDETERMINATE
and UNSUPPORTED and executes only project-authored fictional rules/Card semantics.
PRODUCT RULES and GAMEPLAY RULES remain separate; `src/simulation/` remains
unimplemented. The current projection adds no executable rules, Oracle parser,
real Card gameplay semantics, format/deck legality, strategy or simulation.
Future serious gameplay simulation still requires reviewed executable rules semantics.

The Tier A foundation is unchanged: Stage 1 is merged in PR #176;
**V13 Stage 2 — Legacy/Public Snapshot Profile Review** is merged in PR #177;
the **Legacy/Public Profile Permission and Closure Contract** is merged in PR #178.
Its **READY_FOR_NON_PRODUCTION_STAGE3** recommendation was separately implemented
as **V13 Stage 3 — Legacy/Public Compatibility Snapshot Profile**, merged in PR #179.
The `legacy-public-compatibility-v1` profile is implemented with the same exact
Tier A both-root query identity. **V13 Tier A Card Intelligence & Acquisition Attachment Integration** is merged in PR #180; **V13 Functional-Role and Contextual-Comparison Attachment Integration** is merged in PR #181.
`MechanicalCardIntelligence.from_attachment` → `FunctionalRolePilot.from_mechanical`
→ `ContextualCardComparisonPilot.from_roles` and
`CardAcquisitionAdapter.from_mechanical` share the same query. Mechanical evidence
remains independent, roles remain `requires_review`/pending with zero approvals or KnowledgeFact writes, and comparison remains **ABSTAIN**, null selection.
**Tier B Audit-Context Capability Design Review** remains **DEFERRED** absent a
concrete consumer.

The production operator profile remains **BLOCKED**. All seven mixed-content
operation permissions remain **NOT_ESTABLISHED**, with `production_eligible=false`,
`approval_state=not_granted`, `source_policy_clearance=not_granted` and
`data_processing_permission_established=false`. Catalog and rules evidence
permissions remain separate; successful verification clears neither.

MB2's 810 selected candidates and nine multiface holds remain pending and unadmitted.
Owner spelling proposals remain unapplied and physical Printing verification stays
unresolved. Canonical data, selected audits, SourceRecords, mechanical and
role/context artifacts, markets, collections, MB2 pending execution configuration,
`SOURCE_POLICY_CLEARED_PLANS`, writer/admission/OIDC and the historical v12
auxiliary fixture remain unchanged. No merge or owner admission is performed.

See [artifact verification](docs/GAMEPLAY_RULES_ARTIFACT_VERIFICATION.md),
[release discovery history](docs/GAMEPLAY_RULES_RELEASE_DISCOVERY_CLOSURE.md),
[source versioning](docs/GAMEPLAY_RULES_SOURCE_VERSIONING.md),
[the fictional gameplay foundation](docs/GAMEPLAY_RULES_INTELLIGENCE.md),
and [the unchanged catalog permission closure](docs/V13_LEGACY_PUBLIC_PERMISSION_CLOSURE.md).

---

## Historical record boundary

Everything below retains its original milestone baseline and authorization context.
Earlier “current”, “next”, v12-active and repository-authority statements are
historical records, superseded by the current governance above. Unchanged technical
contracts remain applicable; old next-task claims do not authorize new work.

# Current milestone — collection audit and organization pilot

Canonical main independently verified: `15e19b84701dd47970a948485683f73a687be9d2` (merged GitHub PR #169, including acquisition reconstruction repair). Architecture v12 remains frozen. PR numbers are independent of project phases; no new phase number is assigned.

The bounded Collection Intelligence pilot reuses existing immutable collection imports/snapshots, canonical production identity resolution and Card Intelligence references. A source-replayed audit separates quantities, duplicate input records, physical storage, unresolved identities and personal Card review states. Append-only source-bound assessments preserve prior decisions, supersession and manual reassessment requests without performing reassessment or admitting canonical knowledge.

No authoritative 360-copy MB2 ownership inventory is retained. Six partial unverified pack reports contain 90 positions and remain evidence leads. The compressed demonstration instead declares **360 fictional copies**: 330 resolved, 15 ambiguous and 15 unresolved; an extra repeated 80-copy input row and an invalid zero row are excluded. Six exact production Cards/Printings remain distinct from the 384-Card mechanical cohort and complete-set membership. Storage is independent of strategic usefulness. Three mock-reviewed Cards, two pending Cards and one manually flagged reassessment demonstrate work tracking; actual human approvals remain zero.

[The audit contract and review materials](docs/COLLECTION_AUDIT_PILOT.md) describe quantity accounting, original-source replay, history, exact-ID queries, missing real inputs, a bounded manual ChatGPT handoff and current limitations. Existing acquisition, Product and Card demonstrations remain unchanged. Audit ownership coverage is informational and cannot replace a reviewed buyer declaration or authorize purchase advice. Pending functional roles remain unapproved; CC2 remains NOT_READY_FOR_EVALUATION; tournament acquisition stays parked.

Stop for Project Manager review of this single pilot. Do not merge automatically, import an invented real inventory, repair mixed-policy deck allocation, perform automatic reassessment, rank value, recommend sorting, optimize decks, acquire providers or begin another milestone. The required real-input next step is an authoritative dated inventory and verifiable prior reviews, under the applicable approval boundary.

---

The earlier present-state summaries below preserve their original baselines and authorizations as historical records. This summary supersedes their next-task claims; unchanged technical contracts remain current.

# Current milestone — collection-aware Card acquisition pilot

Canonical main independently verified: `3cf6ad35fcb54ed5a4b640e36af6fa2ecf99a747` (merged GitHub PR #168). Architecture v12 remains frozen. PR numbers are independent of project phases; no new phase number is assigned.

The bounded pilot uses exact production Ponder, Faithless Looting and Greater Good MB2 Printings. A reusable Card-domain adapter validates supplied objectives, ownership, exact Printing preferences, budget, availability, freshness and source-bound complete transaction costs before the existing Decision Intelligence policy runs. Collection Intelligence identity resolution reads the existing canonical query projection, including promoted production identities; no second canonical store is introduced.

The complete-input outcome is explicitly **synthetic demonstration evidence**, not purchase advice. The real-world example **ABSTAINS** because actual buyer context, ownership, objectives and reviewed current offers are missing. Historical Scryfall prices remain historical observations. Pending role candidates remain unapproved and cannot become strategic suitability scores. [The acquisition pilot contract and review materials](docs/CARD_ACQUISITION_PILOT.md) describe inputs, costs, replay, limitations and the bounded manual ChatGPT handoff.

Acquisition Intelligence is the next user-value priority, followed by Collection Intelligence and bounded deck relevance. This milestone does not authorize full inventory management, the separate mixed-policy deck-allocation repair, competitive rankings, provider acquisition, purchase execution or automatic follow-on work. Existing demonstrations, canonical records, historical market evidence, knowledge facts and Architecture v12 remain protected. CC2 remains NOT_READY_FOR_EVALUATION; tournament acquisition stays parked.

Stop for Project Manager review of this pilot. No merge, real purchase recommendation, production admission or next milestone is automatic.

---

The previous present-state summaries below retain their original milestone baselines and authorization context as historical records. This summary supersedes their next-task claims.

# Current inventory — contextual Card comparison pilot

Canonical main verified on 2026-10-12: `4d15582d6ed364f012e853c1fdb2312e54ea7c60` (merged GitHub PR #167). Architecture v12 remains frozen; GitHub PR numbers and project phases are independent.

The bounded contextual comparison uses exactly production Ponder, Faithless Looting and Greater Good in one explicitly hypothetical blue/red/green casual test shell. It separates retained mechanical facts, all eight unchanged pending role candidates, supplied context assumptions, deterministic descriptions and unverified strategic hypotheses. The existing Decision Intelligence engine returns ABSTAIN because human-reviewed context match remains unknown for every alternative. No Card is selected or approved.

[The contextual comparison contract and review materials](docs/CONTEXTUAL_CARD_COMPARISON.md) describe costs, restrictions, conditional instruction arithmetic, counterarguments, uncertainty, exact replay and one bounded manual ChatGPT handoff. Complete existing Decision contracts are retained separately to avoid duplication. This is a manual evidence handoff, not live model integration or deck optimization.

PR #167's fifteen-Card / thirty-candidate pilot is merged as pending evidence; all roles and definitions still require review. The mechanical cohort and earlier two-Card demonstration remain unchanged. Canonical data, historical sources, market observations, knowledge facts and Architecture v12 are protected. CC2 remains NOT_READY_FOR_EVALUATION. Competitive Intelligence stays parked; Deck Intelligence and Competitive Card Intelligence remain planned and unauthorized.

Stop for Project Manager review of this single comparison milestone. No role admission, Card selection, automatic follow-on or advanced intelligence implementation is authorized.

---

# Historical milestone records

Earlier milestone bodies preserve their original baseline and review status; this present summary supersedes their next-task claims.

# Current inventory — functional-role review pilot

Canonical main verified on 2026-10-12: `e4a99ae6ccffe3e7121337fe28d9127024be3743` (merged GitHub PR #166). Architecture v12 remains frozen; PR numbers and project phases are independent.

The authorized functional-role pilot prepares 30 pending candidates for exactly 15 production Cards using retained mechanical evidence: 20 directly evidenced proposed functions, four incomplete contextual interpretations, two unknown proposals and four unsupported assignments. All remain `requires_review`; no human approval or canonical knowledge admission occurs. A small provisional vocabulary, exact source-bound proposals, explicit qualifiers, a three-Card comparison and manual reasoning-context handoffs are described in [the functional-role pilot contract](docs/FUNCTIONAL_ROLE_CARD_INTELLIGENCE.md).

The 384-Card mechanical cohort and earlier two-Card demonstration remain preserved. Full-cohort classification, verified interactions/combos, strategic scoring, rankings and deck optimization remain unsupported. Competitive Intelligence stays parked; Deck Intelligence remains planned and unauthorized. CC2 evidence remains pending and `NOT_READY_FOR_EVALUATION`. Stop for Project Manager review; no follow-on milestone is automatic.

---

# Historical milestone records

Earlier milestone bodies retain their original context; the present summary supersedes their next-task claims.

# Current inventory — mechanical production-cohort evidence

Canonical main verified on 2026-10-12: `c8941c568fb275a735ab6902e3663947f21760ee` (merged GitHub PR #165). Architecture v12 remains frozen; GitHub PR numbers and project phase numbers are independent. No new phase number is assigned.

The mechanical Card Intelligence foundation produces immutable, read-only dossiers for the independently verified 384-Card production cohort from 385 retained Scryfall rows. Exact Oracle/canonical identity maps 384 rows uniquely; Essence of Ajani remains excluded. Five multi-faced Cards retain eleven explicit face objects. Root/face fields, known empty values, unknowns, nonstandard type labels, provider provenance, snapshot identities and projection omissions remain distinct. This is canonical-cohort analysis, not complete MB2 set membership.

[Mechanical contract, findings, examples and replay instructions](docs/MECHANICAL_CARD_INTELLIGENCE.md) describe all 384 retained dossiers, the descriptive cohort report, four manual contexts, and their deterministic manifest. The existing Card Intelligence CLI/query/reasoning contracts are reused; the generic Reasoning Context Builder is unchanged. No canonical records or knowledge facts are admitted. The merged Sol Ring/Counterspell demonstration remains byte-identical. Test and hosted-CI results are recorded in the milestone PR.

Functional-role classification, verified rules interactions, combo/synergy discovery, best-in-slot comparisons, competitive scores, deck optimization, forecasts and acquisition decisions remain unsupported. No provider download, model execution, live ChatGPT transport, new canonical repository, rules engine or architecture change is added. Competitive Intelligence remains parked and Deck Intelligence remains planned, with implementation unauthorized.

The CC2 pending identity bundle remains NOT_READY_FOR_EVALUATION; its six missing pairs, incomplete token and requires_review Product candidate are unchanged. No promotion, market admission, READY attestation or product evaluation occurs. Stop after this bounded milestone's single PR handoff for Project Manager approval; no next milestone is automatic.

Implementation adds `src/card_intelligence/mechanics.py`, extends the existing Card Intelligence exports/CLI, and uses `scripts/build_mechanical_cohort.py` for isolated generation/checking. Protected production remains 384 Cards, 913 Printings, 235 Identifiers, 2 Finishes, 956 observations and 140 historical/active fact files. The query's fifteen typed seed Cards remain outside the production cohort.

---

# Historical inventory records

The original milestone bodies below remain intact; the current summary supersedes earlier next-task claims.

# Current inventory — two-Card retained-evidence demonstration

Canonical main verified on 2026-10-12: `e5e11c41818b3a7e6bec85418a75a37e0ef638f0`, the merge of GitHub PR #164 including its Product `schema_version` provenance repair. PR numbers and project phases are independent; Phase 147 remains the highest numbered phase. Architecture v12 remains frozen.

The current milestone adds a bounded, read-only composition of existing canonical query, Card Intelligence, and reasoning-context capabilities for exactly the production Cards Sol Ring (`6ad8011d-3471-4369-9d68-b264cc027487`) and Counterspell (`cc187110-1148-4090-bbb8-e205694a39f5`). It repairs the promoted-audit query projection and retains deterministic dossiers, manual handoff contexts, and evidence-constrained explanation examples. The demo is a derived review output, not another canonical store, importer, provider, model integration, or Decision policy. See [the demonstration contract and replay instructions](docs/TWO_CARD_CHATGPT_DEMO.md).

Protected production census remains 384 Cards, 913 Printings, 235 Identifiers, 2 Finishes, 956 market observations across two retained MB2 acquisitions, and 140 Card Intelligence fact files including historical/superseded facts. The two dossiers use historical observations and retain source-specific demand semantics; they do not establish current offers, completed sales, global usage, or competitive rankings.

The merged Commander Collection: Black identity bundle remains non-promoting: one Product candidate requires review, six ordinary Card/Printing pairs remain unresolved, the token remains incomplete, and two existing CC2 Printings are reused. Its overall outcome is `NOT_READY_FOR_EVALUATION`. No production evidence admission, READY attestation, acquisition evaluation, or recommendation is added by this demonstration. Competitive Intelligence remains parked; Competitive Card Intelligence and Deck Intelligence remain planned and unauthorized. Stop after review of this demonstration; no follow-on milestone is automatic.

---

# Historical milestone records

All summaries below preserve their original baseline, counts, environment observations, and next-task context. Headings that originally said “current” refer to their historical milestone; the current inventory above takes precedence. Technical contracts remain applicable where unchanged.

# Bounded identity preparation inventory

Prepared a non-promoting Commander Collection: Black non-premium identity review bundle from pinned MIT-licensed original MTGJSON bytes. One Product candidate is structurally valid and requires review; six ordinary Card/Printing pairs and the exact token pair remain unresolved/excluded because native identity records were unavailable. Physical token UUID pairing is supported, but face names and variants are not inferred. Two existing CC2 Printings are reused; the nine-component manifest remains explicitly incomplete. No canonical promotion, market admission, human READY attestation or evaluation occurred.

Added isolated pending review artifacts, a read-only verification command composing existing validators, and focused regressions. No new importer, engine, schema or infrastructure subsystem. See [identity review materials](docs/FIXED_CONTENT_IDENTITY_REVIEW.md).

---

# First production fixed-content pilot — retained research dossier only

The authorized Commander Collection: Black (non-premium) attempt is **NOT_READY_FOR_EVALUATION**. Official/retailer research, exact canonical coverage, market leads, provenance/retention gaps, and a deterministic readiness dossier are retained for review. Only Sol Ring and Command Tower have canonical CC2 Printings; six Cards/Printings, the Product identity, and the token identity remain missing. No honest packet, human READY attestation, production analysis, or acquisition evaluation was produced. Architecture v12 and all existing production bytes remain unchanged.

Added [pilot review materials](docs/FIRST_FIXED_CONTENT_PILOT.md) and isolated authored JSON reports under `data/reviews/fixed-content-pilot/commander-collection-black-non-premium-2026-10-12/`. These are research/review artifacts, not admitted source snapshots or a new runtime contract/subsystem. No implementation capability changed.

---

The previous milestone summaries below retain their original baseline and authorization context. The pilot status above supersedes their next-task claims; unchanged technical contracts remain current.

# Current inventory — reconciled merged baseline

Canonical main independently verified on 2026-10-12: `dd08c76d09e4b8d10c411ade0d8445987c8875c0`, the merge of GitHub PR #161 — Fixed-Content Evidence Admission Hardening. GitHub PR numbers and project phase numbers are independent; Phase 147 remains the highest numbered project phase. No new phase number is assigned to the later named milestones.

Implemented: shared Decision Intelligence contracts, synthetic fixed-content Product analysis and sealed-versus-singles current-cost policy, packet v1, and hardened human-attested review v2. The hardening separates eligibility from approval, freezes nested inputs, requires cost provenance and freshness, validates replay, and binds review to the exact packet/window. Production fixed-content pilot assembly, readiness review, evaluation, and recommendations have not occurred. Forecasts, premium models, simulation, API/UI, live AI-provider integration, and an operational AI Advisor remain unsupported or planned.

Retained production census: 384 Cards, 913 Printings, 235 Identifiers, 2 Finishes, 956 market observations across two retained MB2 acquisitions, and 140 Card Intelligence fact files (including historical/superseded facts). No production fixed-content packet or review is retained. Existing pilot product references and partial Printing coverage are not a complete product manifest or current price evidence.

Architecture v12 remains frozen. Repository-first canonical truth, deterministic analytics and decisions, versioned immutable evidence, human-reviewed production admission, and product-neutral/game-neutral generic engines remain unchanged. AI/ChatGPT is the explanation and reasoning interface over validated outputs; it does not calculate or override acquisition decisions. Competitive Intelligence remains **PARKED / KNOWN GAP / NOT ON CURRENT CRITICAL PATH**. Competitive Card Intelligence and Deck Intelligence remain planned and unauthorized; existing collection/deck-completion helpers are not the planned Deck Intelligence decision domain.

The next candidate, requiring separate authorization, is one governed real fixed-content Product Intelligence pilot for **Commander Collection: Black (non-premium)**: complete independently verifiable official contents, exact canonical Printings, one available current sealed offer, complete compatible current singles observations, explicit transaction costs (including evidence for zeros), source digests/provenance, and a deterministic freshness window. Stop on any gap. Packet assembly and human readiness review do not authorize canonical promotion or acquisition evaluation. Only after separate evaluation authorization and an exact human-attested v2 `READY_FOR_EVALUATION` review may a production caller use `require_ready_evidence_review` before the existing Product analysis and Decision policy.

---

# Historical records — superseded for present state

The entries below preserve their original milestone context, counts, environment observations, and review instructions. They do not describe the current baseline or authorize work; the current summary above takes precedence.

# Fixed-content evidence admission hardening inventory

Added bounded admission checks and regressions in `src/product_intelligence/evidence_packet.py`
and `tests/test_fixed_content_admission_hardening.py`, strengthened nested packet schema validation,
and added `fixed-content-acquisition-evidence-review-v2.schema.json`. New public helpers separate
automated eligibility from explicit human review and verify exact packet/policy binding. Packet v1
valid numeric serialization is preserved; unknown singles amounts are nullable, and historical
review v1 cannot establish affirmative readiness. No production data or Architecture v12 change.

# Phase 126 inventory update

Added `src/market/intelligence.py`, `src/market/query.py`, Canonical Query Service market methods, collection valuation, unified JSON CLI routes, `tests/test_phase_126_market_intelligence.py`, and `docs/MARKET_INTELLIGENCE.md`. Observations are separate under `data/market/observations`; no production observation or canonical price fact was added. Architecture v12 and Phase 119 canonical state are unchanged.

# Phase 123 inventory update

`register_trusted_snapshot` is the generic checksum and immutable-byte registration boundary for refreshed AllPrintings evidence. `data/automatic_updates/phase-123-mtgjson-refresh.json` records the fail-closed HTTP 403 acquisition stop. No new production snapshot exists; the historical MB2/MSH evidence is unchanged. Phase 119 remains the sole completed production promotion at canonical digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Architecture v12 and canonical contracts are unchanged.

# Phase 122 inventory update

The new `target_availability.py` boundary inventories set-level MTGJSON metadata, distinguishes zero/multiple/incomplete/unique/unsupported results, and permits deterministic bounded evidence only for one unique target. Phase 122's retained report records zero Hobbit matches in the trusted two-set (`MB2`, `MSH`) snapshot. No Hobbit identity, candidate, descriptor, automatic run, or canonical artifact was created. Production remains exactly at Phase 119 and digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`; Architecture v12 and canonical contracts are unchanged.

# Phase 121 inventory update

Added `tests/fixtures/phase_121_synthetic/` (descriptor, retained source, eight ordered candidates, and empty isolated canonical state) and `tests/test_phase_121_synthetic_automatic_updates.py`. The generic engine now enforces payload checksum, nonempty unique inventory, provenance, immutable audit digest, and green-check auto-merge eligibility. The workflow derives its deterministic branch from the descriptor and safely reuses only an identical remote branch. No fixture artifact exists under production `data/`; Phase 119 remains its only completed promotion.

# Phase 120 inventory update

New inventory: `src/production_evidence/automatic_updates.py`, both automatic-update scripts, `config/automatic_updates/`, `.github/workflows/automatic-canonical-update.yml`, Phase 120 tests, and `docs/AUTOMATIC_CANONICAL_UPDATES.md`. Phase 119 canonical state/audit is unchanged; no second MB2 batch or MSH promotion occurred.

# Phase 118 inventory update


## Phase 119 — first verified MB2 bounded canonical promotion (2026-08-01)

Promotion **succeeded** for exactly evidence `30663562841-review-payload-v2`, batch
`mb2-batch-000001-e32022126c07`, and target MB2 / Mystery Booster 2. The immutable
Phase 115/116 review chain and every Phase 118 readiness gate were independently reverified
immediately before the write. Exact membership is 1,000 approved candidates: 384 Cards,
379 Printings, 235 Identifiers, and 2 Finishes. Candidate digest is
`e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e`. There are zero
unresolved, excluded, quarantined, fatal-conflict, or orphaned candidates. MSH/Marvel, every
other MB2 batch, and every unrelated candidate were excluded.

Canonical pre-state digest was
`0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba`; post-state digest is
`793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Immutable audit
`phase-119-mb2-batch-000001-e32022126c07` records exact membership, source/review lineage,
preflight digest `d0ea6939c6c282647e24f8873f3021430b451173477013ccaca2fff60d6e1aab`,
pre/post-state digests, deterministic dependency order, replay, and rollback metadata.

Replay with `promote(data_root)`; a byte-identical completed promotion returns idempotent
success without another write or audit. Conflicting replay fails closed. Roll back with
`rollback(data_root)`; it verifies the audited post-state, removes only this bounded canonical
state, verifies restoration of the pre-state digest, and retains immutable audit history.
Architecture v12 and canonical contracts are unchanged. Stop after Phase 119; merge remains
withheld until normal pull-request review and GitHub Actions are green.

## Historical state before Phase 119

The active authorization workflow, persistence scripts, authorization production module, Phase 117/117A tests, and current Phase 117 review artifacts are removed. `production_evidence.promotion_readiness` now computes a non-executing plan from trusted immutable evidence and Phase 115/116 review results. Operator signatures do not control readiness; normal PR review and green CI provide oversight. The exact first MB2 batch is technically ready, while promotion remains explicit, audited, rollback capable, and not performed.

Earlier Phase 117/117A inventory entries below are historical and no longer describe active architecture.

# Phase 117A inventory update

`.github/workflows/mb2-operator-authorization.yml` accepts the twelve required operator and immutable-scope inputs; `scripts/mb2_authorization_persistence.py` provides authorization-only durable Git/GitHub persistence; and `verify_authorization_artifact()` independently authenticates a retained result. Tests cover the workflow contract, safe dry run, immutable scope, authorization validation/replay/conflict, canonical isolation, and persistence boundary. Phase 117 remains unauthorized and unpromoted.

# Phase 116 inventory update

`src/production_evidence/identifier_resolution.py` and `tests/test_phase_116_identifier_resolution.py` implement and verify an immutable Phase 116 overlay over the unchanged Phase 115 review. Seven artifacts under `data/reviews/phase-116/mb2-batch-000001-e32022126c07/` retain the 21-candidate resolution ledger, the complete 820-record collision group, updated 1,000-candidate classifications, findings, dependency closure, pending decision, and readiness report. All 1,000 candidates are approved by evidence classification; signature readiness is true, while signature and promotion remain absent and promotion readiness is false.

# Phase 115 inventory update

The repository now retains a reproducible candidate-level review of exactly the first MB2 batch from production evidence revision v2: 1,000 ledger entries, findings, valid dependency closure, an immutable unsigned pending decision, and a not-ready promotion report. Counts are 979 approved, 0 excluded, and 21 requiring additional evidence. Canonical state and Architecture v12 are unchanged.

# Phase 114A inventory update

`src/production_evidence/adapter.py` now emits schema 2 review payloads; `src/production_evidence/repository.py` verifies and stores them under a derived immutable evidence identity. The manual intake workflow targets a dedicated revision branch and reports payload count/bytes. Tests cover exact extraction, isolation, integrity, missing/duplicate payloads, unresolved Card-to-Printing dependencies, immutable collisions, idempotent normalization, and no canonical/promotion authority. The original retained run is unchanged.

# Phase 113A inventory update

Phase 113A makes the retained-evidence gate valid both before and after evidence-intake PR #86.
The historical absence remains accepted on main; the present state validates run `30663562841`,
target-isolated pending MB2/MSH packages, and non-canonical/no-promotion boundaries. Independent
candidate review remains the next gate after #86 merges.

# Phase 112B inventory update

Production-evidence persistence is now a fail-closed Git/GitHub state machine in `scripts/production_evidence_persistence.py`, invoked unconditionally by the manual intake workflow. It reports every durable result, rejects ignored or empty staging and out-of-bound changes, never force-pushes, verifies the PR through GitHub APIs, and can reuse only byte-identical existing evidence. The live run is not claimed until that workflow is rerun successfully. Architecture v12 and all canonical/review/promotion behavior are unchanged.

> **Phase 113:** The independent review was rerun exclusively against the Production Evidence
> Repository. Run `30663562841` is still absent, so no MB2 batch or candidate could be selected,
> classified, or signed; no Marvel review, promotion, or canonical write occurred.

> **Phase 112A:** `src/production_evidence/adapter.py` now deterministically verifies and adapts the
> native nested MTGJSON workflow artifact to the unchanged Phase 111 intake contract. The Phase 112
> operational failure was a native-layout/root-contract mismatch, not corrupt evidence. Dry-run
> intake remains non-canonical and non-promoting; Architecture v12 is unchanged.

> **Phase 112:** A manual GitHub-native workflow securely selects and authenticates a successful
> Actions artifact, invokes Phase 111 intake and verification, confines changes to
> `data/production_runs/`, and opens a dedicated evidence-only PR. No production archive is
> committed yet; Phase 110B remains stopped at its artifact gate.
>
> **Phase 111:** Permanent production evidence storage, verified ZIP intake, deterministic indexes, and evidence CLI lookup are implemented. No production archive is committed; Phase 110B remains stopped at its artifact gate.

> **Phase 110B:** `docs/FIRST_MB2_BATCH_REVIEW.md` records that run `30663562841` and expected batch `mb2-batch-000001-e32022126c07` have no retained artifacts in this checkout. Review and decision counts remain undetermined; canonical state is unchanged.

> **Phase 110A:** the dry-run path now prepares independently verifiable, exact-set `MB2` and `MSH` review batches and retains their payloads, manifests, ID lists, closure evidence, and pending packages. No production rerun artifacts are claimed yet; promotion and merge remain withheld pending green Actions.

> **Phase 110 gate:** merged Phase 109 (`bf696c5`) is confirmed, but the first production canonical promotion failed closed before execution. The repository retains only run `30649546787`'s summary, not its candidate shards or review packages; no reviewer approval or MB2-only batch membership can be verified. Zero entities were promoted and Architecture v12 is unchanged. See `docs/FIRST_CANONICAL_PROMOTION.md`.

> **Phase 109 update:** GitHub Actions run `30649546787` is the first verified successful targeted production dry run. Its retained summary records MB2 and MSH discovery, 10,940 eligible candidates and 11 deterministic batches without writes or promotion. Candidate payload shards and streaming review-index packages were not retained, so the workflow now uploads both; another targeted dry run is required for independently reconstructable review batches. See `docs/MTGJSON_FIRST_SUCCESSFUL_PRODUCTION_RUN.md`.

> **Phase 108B update:** ambiguous same-printing-coordinate `scryfallId` collisions are now fully diagnosed and narrowly quarantined; different-coordinate collisions remain fatal. Unaffected records continue to deterministic planning, while quarantined records cannot be promoted. Official-corpus verification remains pending.

> **Phase 108A update:** `src/providers/mtgjson/validator.py` now applies explicit namespace and
> scope policy. Non-guaranteed external collisions are retained and surfaced for review throughout
> the existing import/delivery path; strict and internal identities remain fail-closed.

> **Phase 107 update:** `src/promotion/delivery.py`, `scripts/mtgjson_delivery.py`, and the manual
> MTGJSON workflow deliver checksum-verified artifacts to the Phase 106 APIs, default to dry-run,
> and bound reviewed promotion to one selected batch. Hosted official-URL access remains HTTP 403;
> Architecture v12 is unchanged.

> **Phase 94 update:** `src/reasoning/` deterministically packages public semantic responses into immutable provenance-backed AI reasoning contexts. It performs no AI inference or language generation and awaits review and green CI.

> **Phase 90 update:** the only supplied MTGJSON fixture was validated as synthetic set
> `TST`, not MB2. The pilot stopped at its evidence gate with deterministic reports and no
> registration, resolution, promotion, or canonical mutation.

> **Phase 89 update:** `src/external_ingestion/mtgjson.py` provides MTGJSON v5 detection,
> metadata/manifest generation, bounded deterministic mappings, and composition into the
> unchanged Phase 88 acquisition/review pipeline. No full corpus or MB2 data was imported.

# MTG Lab Project Inventory

> **Phase 86 update:** `src/dataset_import/` provides the registry, resolver, session orchestrator, and reporter; `src/mtglab/__main__.py` provides dataset/import CLI commands; and `data/fixtures/canonical_import/` contains the reviewed pilot.

> **Phase 84 update:** `src/acquisition/knowledge.py` adds provider policy, dataset
> identity, pre-review validation, reports, and deterministic review packages;
> `data/fixtures/knowledge/` contains test-only reviewed collectible-card inputs;
> `docs/KNOWLEDGE_ACQUISITION_PIPELINE.md` documents the lifecycle. Architecture v12 and
> canonical storage are unchanged.

> **Status: Current** — Phase 105 implements official reference dataset acquisition over the
> merged Phase 104 baseline; Architecture v12 remains unchanged.

## Phase 83 constitutional guidance

Four Tier 0 documents now preserve the project's enduring laws, architectural rationale,
long-term intent, and question-led product compass: `docs/CONSTITUTION.md`,
`docs/ARCHITECTS_NOTEBOOK.md`, `docs/FUTURE_VISION.md`, and
`docs/QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`. They add no runtime behavior, canonical data,
schema, provider, or Architecture v12 change. The Constitution governs why; existing
architecture contracts govern structure; the notebook records rationale; the vision and
questions guide future proposals without authorizing them.

> **Retained baseline:** Phase 82 raw data acquisition framework implemented on 2026-07-30.

## Current state

- **Architecture:** v12 (unchanged)
- **Latest merged baseline:** Phase 104 — bounded MTGJSON canonical promotion
- **Current milestone:** Phase 105 — Official Reference Dataset Acquisition
- **Maturity:** pre-alpha; deterministic local reference implementation
- **Validation baseline:** 253 tests passing locally
- **Canonical data:** 15 Cards and 15 Printings, including four Mystery Booster 2
  Printings; the MB2 Product is a foundation record; canonical Print Sheets and Slots
  remain unpopulated
- **Review authority:** `docs/PHASE_101_ARCHITECTURE_REVIEW.md` records current maturity, debt,
  risks, dependency direction, readiness, and roadmap recommendations

## Implemented subsystem inventory

| Subsystem | Implementation | Contract / status |
| --- | --- | --- |
| Canonical Repository | Typed game aggregate, specialized schema-backed repositories, deterministic snapshots, relationship validation, staged bulk apply | Operational v1; overlapping repository generations are consolidation debt |
| Canonical Query Engine | Stable provenance-bearing entity results; relationship, dataset, audit, validation, and deterministic exact search queries; CLI | Operational v1; sole supported read boundary for future consumers |
| Canonical Semantic Query Layer | Immutable structured operations, deterministic Query/Analytics delegation, snapshot identities, provenance, and JSON CLI | Operational v1; no AI reasoning or language generation |
| Canonical Import Pipeline | Reviewed local JSON/CSV adapters, provenance, dry-run/validation-only modes, deterministic report, atomic game-tree replacement | Operational v1; local-only and single-writer |
| Raw data acquisition | Immutable byte snapshots, provider adapters, normalized source records, assertion bridge, acquisition-run reports, offline CLI | Operational v1; no live providers or canonical promotion |
| Multi-source evidence acquisition | Immutable provider/source/dataset/artifact contracts, provider interface, deterministic reference registry, licensing gates, JSON CLI | Framework v1; no live providers, datasets, or promotion |
| Official reference dataset acquisition | Configured official URLs, resumable streaming, checksum/SHA-256 and JSON/schema gates, local registration, JSON CLI | Operational for MTGJSON AllPrintings; acquisition only |
| MTGJSON Reference Dataset Provider | Local v5 discovery, schema/artifact/dataset validation, deterministic candidate mapping, planning, JSON CLI | Operational v1; reference evidence only, no networking or promotion |
| External dataset ingestion | Canonical supplied-dataset manifest, JSON/CSV/ZIP integrity, MTGJSON v5 provider detection/mapping, registrations, review-package handoff, CLI | Operational v1; stops before human review and promotion |
| Evidence and candidate ingestion | Immutable evidence storage, parsers/normalizers, candidate validation, retained intermediate artifacts, population review | Operational for bounded reviewed workflows |
| Evidence Repository and Review | Content-verified bundles, Source Record validation, external handoff integrity/provenance/completeness/conflict reports | Operational pre-promotion gate |
| Canonical promotion | Legacy entity promotion plus Phase 85 review-package engine, deterministic versions, immutable success/failure audits, supersession, rollback, replay, and CLI | Operational v1; merged before Phase 87 |
| Observation Engine | Immutable pack reports, verification records, descriptive box summaries, dated legacy valuation snapshots | Developing; strictly non-canonical |
| Observation Import Pipeline | Plain-text multi-pack import, create-only allocation, manifest reconciliation, verification and derived summary refresh | Operational v1; single-writer multi-file workflow |
| Market Framework | Provider abstraction, service/cache, normalized immutable snapshots, append-only repository, offline manual provider | Operational v1; no live provider |
| External Mapping Layer | Versioned canonical-to-provider IDs, lifecycle/provenance, exact resolution, append-only mapping sets | Operational v1 |
| Collection Engine | Immutable ownership aggregate, acquisitions, locations, quantity operations, summaries, local repository and CLI | Operational v1 |
| Analytics Engine | Seven immutable deterministic reports, input fingerprints, optional canonical enrichment and CLI | Operational v1 factual analytics |
| Decision Engine | Explicit versioned rules, immutable explainable decisions/reports, stable fact lineage and CLI | Operational v1 deterministic reasoning |
| Probability / simulation | Package placeholder only | Not implemented; canonical rules remain evidence-blocked |
| AI Reasoning Context | Immutable content-addressed evidence packages over Semantic responses | Operational v1; only allowed reasoning input for AI adapters |
| AI Model Adapter | Provider-neutral immutable contracts, abstract interface, explicit registry, lifecycle validation, CLI | Framework v1; no provider implementation or inference |
| Research Log | Tier 0 architecture document | Implementation deferred |
| API / UI / AI advisor | Vision only | Not implemented |

## Repository layout

- `data/canonical/` — authoritative game-scoped canonical records
- `data/raw/<provider>/<dataset>/<snapshot-id>/` — generic immutable source snapshots
- `data/local/reference-datasets/` — Git-ignored official artifacts, partial transfers, manifests, and non-canonical registrations
- `data/sources/` and retained raw evidence paths — archived evidence and controlled handoffs
- `data/intermediate/` — parsed, candidate, review, and research artifacts
- `data/observations/` — immutable non-canonical opening reports
- `data/audit/` — immutable promotion decisions
- `src/canonical`, `src/repository`, `src/canonical_import` — canonical model,
  persistence/validation, and reviewed bulk import
- `src/query` — provider-neutral canonical read contract and deterministic query facade
- `src/acquisition` — source-agnostic raw snapshots, normalization, and assertion bridge
- `src/external_ingestion` — supplied-file manifests, validation, MTGJSON provider adapter, and governed handoff
- `src/providers/mtgjson` — concrete MTGJSON Reference Dataset provider over Phase 98 contracts
- `src/ingestion`, `src/evidence_review` — evidence-to-candidate and handoff review
- `src/observations`, `src/market`, `src/collection`, `src/analytics`,
  `src/decisions` — downstream domain engines
- `src/reasoning`, `src/ai` — reasoning-context packaging and provider-independent model boundary
- `src/mtglab` — command-line application namespaces
- `src/schemas/v1`, `src/validation` — versioned JSON contracts and validation
- `tests/` — deterministic tests collected by the Python validation workflow
- `docs/` — Architecture v12, subsystem contracts, governance, status, and history

## Architecture constraints and known debt

- Canonical identity and evidence provenance remain upstream of observations,
  ownership, analytics, and decisions; downstream results never promote themselves.
- No canonical MB2 rules, complete pools, probability tables, pack generator, or
  simulator are authorized by present evidence.
- Specialized canonical repositories overlap the newer typed aggregate; observation
  analytics and market snapshots overlap newer generic engines.
- Provenance is pervasive but does not yet have one cross-subsystem vocabulary or
  lineage reader.
- Filesystem stores are deterministic and appropriate for current volume, but full-
  tree loading/copying, linear lookup, and single-writer assumptions limit scale.
- The Phase 77 review is retained as historical evidence; the Phase 101 review is the
  current assessment and changes no Architecture v12 boundary.

## Documentation hierarchy

Documentation status labels have the following consistent meaning:

- **Current** — reports the active repository baseline or authorization.
- **Historical** or **Superseded** — preserves earlier decisions or plans but cannot
  override Current documents.
- **Reference** — retains a reusable contract or context without claiming current
  milestone authority.
- **Vision** — describes target-state capability and does not imply implementation.

Tier 0 purpose and institutional memory are defined by `docs/CONSTITUTION.md`, `docs/ARCHITECTS_NOTEBOOK.md`, `docs/FUTURE_VISION.md`, and `docs/QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`. Architecture and governance are defined by `docs/ARCHITECTURE.md`,
`docs/DATA_MODEL.md`, `docs/DATA_REPOSITORY.md`, `docs/RULES_ENGINE.md`, and
`docs/AI_CONTRIBUTING.md`. The current implementation assessment is
`docs/PHASE_101_ARCHITECTURE_REVIEW.md`; `ARCHITECTURE_REVIEW_v1.md` is historical. Implemented subsystem contracts include
`docs/CANONICAL_IMPORT_PIPELINE.md`, `docs/MB2_OBSERVATION_INTELLIGENCE.md`,
`docs/MARKET_PROVIDER_FRAMEWORK.md`, `docs/COLLECTION_ENGINE.md`,
`docs/ANALYTICS_ENGINE.md`, and `docs/DECISION_ENGINE.md`. This inventory describes
what exists; the architecture review evaluates it; `docs/ROADMAP.md` controls future
milestones; `CHANGELOG.md` preserves history.

Current operational state is reported by `docs/SESSION_STATE.md`,
`docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and `docs/HANDOFF.md`. Phase-specific
plans explicitly marked Historical, Superseded, or Reference remain retained artifacts.

## Session startup workflow

1. Read `docs/CONSTITUTION.md`, this inventory, and
   `docs/PHASE_101_ARCHITECTURE_REVIEW.md` (`ARCHITECTURE_REVIEW_v1.md` is historical).
2. Read `docs/SESSION_STATE.md`, `docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and
   `docs/HANDOFF.md` for the current operational state.
3. Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
   `CHANGELOG.md` for architecture, authorization, and history.
4. Treat Historical, Superseded, Reference, and Vision documents according to their
   labels; do not use them to override Current documents.
5. Confirm explicit milestone approval before changing the repository.

## Next-work boundary

Phase 105 was authorized but stopped without implementation because the required caller-supplied
AllPrintings artifact was absent. Phase 104 remains complete. The provider accepts
local evidence only and cannot promote it. Representative validation composes the existing
reviewed promotion boundary; full-corpus mapping and operations remain unproven. Mystery Booster
2 remains evidence-blocked; Simulation and operational AI advice remain unimplemented.

## Phase 80 — Canonical fact and evidence contract

- `src/schemas/v3/`: additive Card, Printing, assertion, and partial-collation schemas.
- `src/canonical/evidence.py`: uncertainty, promotion, and fail-closed consumer API.
- `docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`: authoritative v3 policy.
- No Mystery Booster 2 dataset records were added or rewritten.
> **Phase 96B update:** `src/canonical_import/evidence_package.py` verifies immutable,
> independently reviewed product-identity packages and delegates canonical writes to the
> existing promotion service. The retained MB2 Stage 1 package confirms one foundation
> Product only; all packaging composition and topology remain unresolved.
> **Phase 97 update:** `src/canonical_import/card_list_package.py` is the fail-closed Stage 2
> intake interface. No qualifying MB2 list is retained, so canonical Card/Printing counts
> remain unchanged and no promotion occurred. See `docs/MB2_STAGE_2_CARD_IMPORT.md`.
> **Phase 98 update:** `src/evidence/` provides immutable multi-source acquisition contracts,
> provider capabilities and registration, and a deterministic non-canonical reference dataset
> registry; `mtg-lab evidence` provides JSON inspection and validation. No provider networking,
> dataset population, automatic promotion, canonical contract, or Architecture v12 change exists.
> **Phase 99 update:** `src/providers/mtgjson/` implements the first concrete reference provider,
> with local-only MTGJSON v5 validation, deterministic candidate mapping, planning, and JSON CLI.
> No dataset was bundled, acquired, reviewed, promoted, or written to canonical storage.

> **Phase 100 update:** `src/providers/mtgjson/execution.py` executes local AllPrintings evidence
> through registration and deterministic candidate validation into a pending-only review queue.
> No canonical write, automatic approval, networking, or promotion is available.

## Phase 117 — First MB2 operator-authorization gate (2026-08-01)

Phase 115 reviewed the exact first MB2 batch and Phase 116 resolved its 21 identifier findings,
leaving 1,000 approved candidates (384 Cards, 379 Printings, 235 Identifiers, 2 Finishes) with
valid dependency closure and no MSH candidates. Phase 117 reverified that complete immutable
chain and retained a deterministic signature request, authorization contract, verification, and
promotion-readiness report under `data/reviews/phase-117/mb2-batch-000001-e32022126c07/`.
A human must supply identity, role, durable review reference, RFC 3339 review time, one allowed
decision, notes, and matching request/batch/candidate digests. No authorization exists and
promotion readiness is false. Authorization and promotion remain separate; no canonical write or
promotion occurred. Architecture v12 and canonical contracts are unchanged.
# Phase 124 inventory update

`src/collection/intelligence.py` and the unified CLI now provide versioned JSON/CSV import,
explicit canonical resolution outcomes, immutable collection snapshots, summaries, deck
completion, and explainable price-independent acquisition priorities. The synthetic deck
fixture and focused contract document define validation and boundaries. Canonical production
state remains Phase 119 only at digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`.
# Phase 125 inventory update

Added `src/query/service.py`, Phase 125 query tests, `docs/CANONICAL_QUERY_LAYER.md`, and
canonical Card/Product/Printing plus collection JSON CLI surfaces. The layer reuses the
existing canonical repository/query engine and Phase 124 collection/deck services. It adds
no canonical data, product, provider, pricing, simulation, recommendation, or AI integration.
# Phase 127 inventory (2026-08-01)

Added `src/market/scryfall.py`, `scripts/scryfall_market_acquisition.py`, the manual
`market-acquisition.yml` workflow, Phase 127 tests, and focused Scryfall documentation.
The outbound proxy blocked official API access with HTTP 403, so no production market
observation or collection valuation was retained. Coverage is 0/379 promoted MB2
Printings. Phase 119, canonical digest, Architecture v12, canonical contracts, and the
absence of recommendation/AI providers remain unchanged.

# Phase 127A inventory (2026-08-01)

The Phase 127 adapter remains the sole provider adapter. Acquisition manifests now inventory
source records, MB2 records, unique matched promoted Printings, known prices, and explicit
missing prices. The checked-out production observation store remains empty; no provider
payload, acquisition directory, persistence branch, or PR is present in repository state.
External GitHub run state was not reachable from this environment and is not claimed.


---

## Current milestone append — Bounded Activated Ability Procedure Projection

The subsequent owner prompt authorizes this bounded projection only. All earlier
bodies above, including their authorization flags, counts and bases, retain their
historical authority. GitHub main and PR #199's merge were independently verified
at `2aa01764db0cfbcd89bc3a30a4433c4f24ea5893`; its merge tree matches reviewed
head `6cf3f4897c919b39ec82e6b9ad2e26a4ff06c183`. The isolated branch is
`codex/cr-bounded-activated-ability-procedure`, starting at that exact main.
Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

The exact allowlist is **602.2, 602.2a, 602.2b**: three new NON-EXECUTABLE
source units, **85 → 88 distinct units** and **nine → ten projections**.
Fresh verification uses the owner-attached 977752-byte TXT, effective 2026-09-25,
SHA-256 `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
It confirms the merged design's review-only fingerprints and independently creates
new projection anchors. No official prose, examples, TXT or attachment path is retained.
See [the milestone](docs/GAMEPLAY_RULES_BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTION.md) for the source contract, relationships, reproduction,
coverage, preservation and readiness. Validation evidence is reported in the
single draft PR and completion report; required final-head hosted gates remain
necessary for independent PM review. The owner retains final merge approval.

Append-only consumer reassessment resolves `605.3 → 602.2` source correspondence.
The separate `602.2b → 601.2f` cost analogy resolves against retained evidence.
`602.2 → 733` and `602.2a → 701.20a` remain unresolved. The single imported
range `601.2b–601.2i` has eight rows: b/f/g/h projected, c/d/e/i unprojected.
No `601.2a` import, invented applicability qualifier, synthetic 605 section,
new indirect-as-direct dependency or execution claim is introduced.
Mana exceptions and hypothetical-stack controller attribution remain separate.
All ten procedure responsibilities remain **OPEN / EXECUTION_BLOCKED**.
The real profile remains **DESIGN_ONLY / NOT EXECUTABLE /
REAL_EXECUTION_PROFILE_NOT_READY**; real execution remains **BLOCKED**.

All 339 inherited src files and 115 prior gameplay evidence files (454 total)
are protected against exact canonical Git. Historical document bodies are
preserved. Source policy remains `not_granted`; private retention,
redistribution, free service, commercial service and AI export remain
NOT_ESTABLISHED. Runtime, Product Rules, Tier A, Card Intelligence, MB2,
canonical catalog, collections, admission, publication workflows and timeouts
remain unchanged.

After reassessing shared procedure, reveal, rollback, trigger, controller and
runtime frontiers, exactly one subsequent recommendation is **Shared Casting-Stage
Gap Scope Design**: a bounded review-only comparison of the four missing imported
members with other blockers, with **zero projected units and an empty projection
allowlist**. Their bodies are not inspected in this milestone. This recommendation
supplies no future source admission or execution authority.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false

Stop at the single draft PR for independent PM review. Do not merge, enable
auto-merge or begin the recommendation.


---

## Current milestone append — Shared Casting-Stage Gap Scope Design

The subsequent owner prompt authorizes only this review-only design. Earlier
bodies and appendices retain their historical authority and validation history.

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.
Canonical main / branch base: `8c2a79ecce9ae7e6ff8e7959c57271e02bf1a4cb`.
Branch: `codex/shared-casting-stage-gap-design`. PR #200's merge and reviewed
head share tree `7e9f056923fdffe1c2871d8d9c49c42ab6bfea21`.
Only complete 601.2c/d/e/i bodies were newly inspected, with exact original
artifact bytes and retained lineage reproduced; c includes its owned example.
Current projection allowlist: empty. Added units/projections/identities/registered
anchors/edges: 0. Coverage remains 88 units / ten projections; import coverage4/8.
All ten activation responsibilities remain OPEN / EXECUTION_BLOCKED; execution
BLOCKED. Source policy stays not_granted; private retention, redistribution,
free service, commercial service and AI export stay NOT_ESTABLISHED.

The new review-only package contains five immutable review records and one bound
manifest. Its four-stage matrix separates literal references, range membership,
structural context and indirect consumers; inspection creates no source coverage.
347 inherited src files and126 prior gameplay evidence files in19 directories
(473 total) remain byte-identical. Historical document bodies, identities and
manifests are preserved. The finite successor adapter preserves the original
69,051-byte inventory plus3,400-byte PR #200 appendix before this exact appendix.
New tooling is confined to scripts/tests; no runtime or projection objects added.

See [the design and validation checkpoint](docs/GAMEPLAY_RULES_SHARED_CASTING_STAGE_GAP_DESIGN.md) and
`reference-reviews/gameplay-rules-shared-casting-stage-gap-design/`.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
