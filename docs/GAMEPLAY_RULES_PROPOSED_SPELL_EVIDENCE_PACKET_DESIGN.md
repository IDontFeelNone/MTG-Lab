# Proposed-spell evidence packet contract design

This is one **PROPOSED / NON_EXECUTABLE**, retained-evidence-only design package.
The owner authorized this milestone only. Architecture v13 remains ACTIVE
APPROVED; Decision 017 remains ACCEPTED. Public contracts retain authority;
retained projections are subordinate knowledge. Constitutional laws 2, 3, 6, 8,
11–14 govern uncertainty, evidence, derivation, history and human accountability.
No Tier 0 contract changes. Independent PM review and final owner merge approval
remain pending; keep the single PR draft, unmerged, auto-merge disabled.

## Authority and exact base

GitHub PR #208 was independently observed merged at
`80c7cee9c1448c97a76f7a9139b405cbcb4c3613`. Remote main equals that exact commit;
its tree `d3d810a7ce77cd5ce15074852628df82b0ad82c2` equals reviewed head
`fb426488d3f7cb676df4a9ab9cfa9b5a07914bc8`'s tree. Initial local `work` was clean
at `d294835929a320fce01fb4025bdb3a4934e2eeaa`. Fetch and a new branch from main
safely reconciled it: `codex/proposed-spell-evidence-packet-design`. No unrelated
work was present. Governance and state were reconciled in the priority established
by `AI_CONTRIBUTING.md`; retained PR #207/#208 records were read directly.

The source allowlist is **empty**. New source units **0**; new projections **0**.
No TXT is required or inspected. No additional source bodies, official examples,
Oracle text or real Card identities are obtained. Existing coverage stays **100
distinct real source units / 15 projections**, casting stages **9/9**, parent
proposal range **4/4**, single activated b–i import **8/8**, and 601.2i's separate
preceding a–h range **8/8**. See PR #208's retained
[coverage](../reference-reviews/gameplay-rules-casting-permission-family/composite-coverage.json)
and [permission/missing-input assessment](../reference-reviews/gameplay-rules-casting-permission-family/permission-assessment.json),
and PR #207's [procedure map](../reference-reviews/gameplay-rules-casting-stage-family-completion/procedure-map.json).
This package does not duplicate those inventories as its main output.

## Normative interpretation

MUST, MUST NOT and MAY below define this proposed contract. They create no runtime
admission mechanism. The packet answers: **What bounded explanation is supported
under the stated assumptions, which evidence supports it, and what prevents a
stronger conclusion?** Its only initial stage is `PERMISSION_TO_BEGIN_CASTING`.
A proposal-legality checkpoint, costs/payment, casting completion and execution
are separate questions and MUST remain unsupported stronger conclusions.

Four dimensions MUST be reported separately:

| Dimension | Meaning and limits |
|---|---|
| Structural validity | Required fields, strict types, identities, manifest relationships and references conform. Invalid identities/bindings, dangling references and malformed types are errors. Conformance establishes neither truth nor evidence sufficiency, sound reasoning or legality. |
| Evidence condition | `PRESENT`, `UNKNOWN`, `UNSUPPORTED` or `CONFLICTING`, scoped to a particular claim or reasoning step. No packet-wide READY flag or truth score exists. |
| Bounded conclusion | An authored, traceable explanation under named assumptions, with typed limitations and stronger claims explicitly unsupported. A positive result can be conditional support for its exact question only. |
| Execution authority | Always `BLOCKED`, independently of the other three dimensions and any review observation. |

An incomplete, unsupported or conflicting packet MAY be structurally valid.
A structural error MUST NOT be relabeled unknown. Validators MUST reject rather
than repair malformed data or silently normalize numeric types.

## Schema, identity and ownership

The normative machine-readable representation is
[contract.json](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/contract.json),
a closed JSON Schema 2020-12 document, plus the referential and condition obligations
below. Every property declared in its objects is **required**; no extra properties
are allowed. Empty arrays explicitly represent no supplied entries, never proof
that no relevant fact/effect exists. No object property is optional in v1;
`alternative_id` and claim `value` alone allow explicit null as described below.
Strings MUST be nonempty. Integers MUST be JSON integers (no Boolean or float
coercion), positive for revisions/context versions. Arrays MUST have unique
entries; record identifiers MUST also be unique within their collection.

Canonical bytes reuse `evidence.contracts.deterministic_json`: UTF-8, sorted keys,
compact separators, Unicode preserved, with exactly one trailing LF for files.
Duplicate JSON keys, nonfinite numbers, noncanonical bytes, symlink files or
ancestors, unexpected package entries, and identity/hash mismatches MUST fail.
Validation MUST take privately owned canonical bytes before inspecting candidates;
returned views MUST be independent copies. Caller mutation cannot alter an
already validated snapshot. The test-only helper is an offline design checker,
not a production packet builder, runtime API or admission service.

Identities are `sha256:` plus 64 lowercase hex digits. Each uses the existing
`sha256_identity({"domain": domain, "content": body})`; `body` excludes only its
own identity field. Contract changes require a new contract identity; incompatible
format changes require a new `schema_version` and `$id`. No implicit migration,
version substitution, or cross-version merge is permitted.

| Artifact / own field | Domain |
|---|---|
| JSON Schema / `contract_id` | `proposed-spell-evidence-packet-contract-v1` |
| Fictional packet / `packet_id` | `proposed-spell-evidence-packet-v1` |
| Assessment / `record_id` | `proposed-spell-evidence-packet-design-record-v1` |
| Manifest / `package_id` | `proposed-spell-evidence-packet-design-package-v1` |

The manifest binds the seven data files by exact byte count, raw SHA-256 and own
identity, plus the actual retained package IDs used. It is the sole enclosing
package identity; no packet includes that identity in its own hash, avoiding a
cycle. Packet `contract_id` MUST equal this exact schema's identity. A manifest
binding is structural evidence about retained bytes, not proof of any assertion.
Design record IDs are neither new projected rule identities, registered source
anchors, real Card identities nor GameplayRulesSnapshot/execution-profile IDs.

Contract identity:
`sha256:612f6c8a7065795e52066b30bc3b9670aacd6becbb6ae09864e6da3250d0326d`.
Design package identity:
`sha256:f152e254d42f1711c7076a248e7956280b9351a5bc40030f8c35555a3952689b`.
The manifest lists the five distinct packet identities and assessment identity.

## Field contract

Local IDs are nonempty lowercase letter/digit/hyphen tokens beginning with a
letter. They are scoped to the immutable packet. Fictional entity/lineage IDs
have the explicit `fictional:<a–e>:<token>` namespace. This v1 is a bounded
fictional design contract, not a real assertion-ingestion schema.

| Field | Required type and meaning |
|---|---|
| `schema_version`, `packet_id`, `contract_id` | Exact packet version and content identities above. |
| `record_kind`, `fictional`, `scenario_label` | `FICTIONAL_DESIGN_PACKET`, literal true, and a visibly fictional label. They MUST NOT be changed to real evidence authority. |
| `lineage_id`, `revision` | Fictional stable lineage and positive revision. Content changes create a new packet identity and preserve prior bytes. |
| `contexts[]` | At least one `{context_id, version, proposal_id, object_id, player_id, description}`. Only the context needed for this question is modeled. Context identity/version and proposal, object and asking player are inseparable bindings. |
| `question` | `{stage, context_id, text}` fixes the exact question and context; stage is always permission to begin. |
| `rule_evidence[]` | At least one `{evidence_id, retained_package, package_id, projection_id, rule_reference, rule_id, anchor_id, artifact_hash, effective_date, authority}`. Authority is `RETAINED_VERSIONED_RULE_CONTEXT_ONLY`. All bindings MUST resolve together through the original manifest/projection. |
| `claims[]` | At least one `{claim_id, context_id, alternative_id, role, subject_id, predicate, condition, value, basis, attribution, rule_context_refs, limitation_refs}`. Roles distinguish allowing/prohibiting effects, choices, state, characteristics and assumptions. Values are string, Boolean or explicit null; no arbitrary game-state object is admitted. |
| `attribution` | `{actor_id, statement_id}` retains the fictional speaker and statement. `basis` distinguishes authored fictional assumptions from attributed fictional assertions. Neither is rule authority. |
| `choices[]` | `{choice_id, context_id, alternative_id, claim_refs, description}` binds a possible alternative to its supporting claims. It generates/selects no choice. |
| `reasoning[]` | At least one `{step_id, context_id, alternative_id, condition, operation, claim_refs, rule_refs, depends_on_steps, limitation_refs, explanation}`. Operation is bounded authored reasoning or explicitly unsupported evaluation; dependency edges MUST be acyclic and local. |
| `limitations[]` | At least one `{limitation_id, kind, context_ids, claim_refs, step_refs, description}`. Kinds distinguish unknown input, unsupported computation, conflict, compatibility gap and scope. Each reference MUST resolve in its declared context. |
| `conclusion` | `{kind, stage, step_refs, assumption_refs, limitation_refs, text, unsupported_stronger_conclusions}`. It MUST identify all limitations relevant to its supporting steps/claims, its exact assumptions, and the complete fixed list of unsupported stronger conclusions. |
| `execution_authority` | Literal `BLOCKED`. No review or conclusion can override it. |
| `history` | `{supersedes_packet_ids, review_observations}`. Superseded packet IDs require an explicitly supplied, validated historical registry; absent history is a dangling-reference error. |
| `review_observations[]` | `{observation_id, authority, fictional, reviewer_id, claim_refs, step_refs, supersedes_observation_ids, text}`. Attributed human-review observations remain separate from assertions/reasoning; examples' observations are explicitly fictional. Supersession references MUST identify earlier preserved observations. No reviewer observation supplies actual PM/owner approval. |

`rule_context_refs` and `rule_refs` refer to local `evidence_id`s, not naked rule
numbers. Claims cannot cite rules as factual proof; their fictional attribution
remains required. Retained package names are finite validated owners, never
arbitrary paths. A legacy `anchor_id` field in this design can hold the existing
retained `anchor_identity` from PR #208's composite binding when the historical
source-anchor object has no standalone `anchor_id` (notably 601.2). This is a
reference to the already retained identity, not a newly minted anchor.

A null alternative denotes an assertion/step about its context generally; it MUST
NOT erase an alternative restriction on its inputs. An alternative-specific step
MUST consume only general or matching-alternative claims/dependencies in exactly
the same context/version. Different contexts or alternatives MUST NOT be silently
joined. A conclusion spanning independent alternatives MUST have kind
`INDEPENDENT_CONDITIONALS_ONLY`, keep each step separate and carry a compatibility
gap; it asserts no co-selection or incompatibility. No compatibility solver exists.
Different retained versions MUST NOT be substituted or blended for one rule binding.

## Conditions, conclusions and append-only review

| Condition | Claim/step obligation and effect on explanation |
|---|---|
| `PRESENT` | Attributed assertion/assumption value is supplied, or authored reasoning is supplied. This reports presence, not truth, sufficiency or performed computation. Claims MUST have nonnull values. |
| `UNKNOWN` | The required claim value is null, or a step identifies an unknown input. An `UNKNOWN` limitation names exactly what is missing and the affected scope. Unknown cannot become false, empty text, no prohibition, or default permission. |
| `UNSUPPORTED` | A claim's required interpretation/derived value is unavailable (null), or a step explicitly names an unimplemented operation. Inputs MAY all be present. An `UNSUPPORTED` limitation identifies the operation; the step MUST be `UNSUPPORTED_EVALUATION`. |
| `CONFLICTING` | Preserve nonnull attributed assertions about the same subject/predicate/context/alternative that disagree, and bind them in a `CONFLICT` limitation. The dependent step retains this condition. Never select a winner by time, confidence, ordering or an undeclared policy. |

Conditions are per claim/step and may coexist in one packet. Conclusion kinds
classify the **authored bounded explanation**, not an automated precedence or
truth aggregation algorithm: `CONDITIONAL_SUPPORT`, `INDETERMINATE_MISSING`,
`INDETERMINATE_UNSUPPORTED`, `INDETERMINATE_CONFLICT`, or
`INDEPENDENT_CONDITIONALS_ONLY`. Each kind MUST retain all applicable conditions
and limitations. Conditional support cannot depend on unknown, unsupported or
conflicting premises. Missing/unsupported/conflict kinds MUST trace their named
barrier. Populated effect lists establish no complete effect inventory. Absence
of a prohibiting assertion establishes no absence of prohibitions.

The explanation MUST link claims and rules through step IDs, identify assumptions
and context, state missing inputs/unsupported operations/conflicts/compatibility
gaps, and state what remains unsupported. The stronger-conclusion list always
contains overall permission, proposal legality, joint choice compatibility,
payment, casting completion and execution. `LEGAL`, `CASTABLE` and
`READY_TO_EXECUTE` are not permitted conclusion states. Prose MUST conform to
those limits; structural checks cannot prove arbitrary prose sound or truthful.
Reviewers must inspect it. No validator evaluates effects, timing, characteristics,
costs, payment, legality or choice compatibility.

Corrections MUST add a new packet with a new content identity, same lineage and
an increased revision, explicitly preserving and identifying its predecessor.
The new packet MUST NOT rewrite the predecessor or silently combine its facts.
The history registry MUST supply predecessor identities with compatible contract,
lineage and context identity/version; unresolved history and cycles fail. Changing
a context requires a new separately stated context, not reuse of evidence from an
incompatible instant. Review observations are append-only attributed records;
corrections refer to earlier observations while preserving them. Review approval
never mutates the historical packet's evidence condition or execution authority.
The examples use revision 1 and no superseded packets; fictional review observations
are included to demonstrate their separate authority.

## Five complete worked packets

Each linked JSON contains populated fields, complete actual retained rule bindings,
a reasoning trace, explicit limitations, a full expected explanation in
`conclusion.text`, and an attributed fictional reviewer observation. Their objects,
players, effects, qualities, states and choices are authored fiction.

| Packet | Bounded outcome and expected explanation |
|---|---|
| [A: conditional](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/packet-a-conditional.json) | Under `premise`, the possible `soften` choice could address `ban` alone under 601.3a. No inference of overall permission, compatible actual proposal or successful casting. |
| [B: missing](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/packet-b-missing.json) | The conditional-flash beacon fact is `UNKNOWN` at the exact context/version. 601.3d explains why it matters; neither lit nor unlit is invented. |
| [C: unsupported](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/packet-c-unsupported.json) | Assertions supply designated characteristics, a continuous-effect description and dial/threshold inputs. 601.3e/601.3b supply context; effect applicability, derived quality and timing computation remain `UNSUPPORTED`. |
| [D: conflict](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/packet-d-conflict.json) | Two attributed assertions give opposite beacon values in the same context. Both remain; conditional-flash satisfaction is disputed with no automatic winner. |
| [E: compatibility](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/packet-e-compatibility.json) | `soften` could address a prohibition under 601.3a; `brighten` could enable an allowance under 601.3b. Independent possibilities provide no single compatible proposal. |

All five cite retained 601.3 and relevant 601.2 parent, e and i context. The
parent/e/i entries are packet-wide procedural context supporting the scope
exclusions in every packet, rather than premises proving a scenario fact.
Rule citations explain conditions and procedural limits; they prove no scenario fact.

## Retained boundaries and design assessment

The individual 601.2 → 601.3 source reference remains resolved; complete 601.3
family coverage and **semantic closure OPEN** remain separate. 601.2e's semantic
relationship to the permission family is not a direct citation; e → 733 stays
unresolved. The single 602.2b b–i import excludes a and does not automatically
import 601.3. The separate 601.2f cost analogy stays separate. Prior-priority
and completion requirements remain conditional. Mana, controller, trigger,
loyalty, reveal, recovery and every other inherited unresolved boundary remain.
All ten activated-ability responsibilities stay **OPEN / EXECUTION_BLOCKED**.

No production builder, public runtime API, generic framework, inference engine,
Card/Oracle ingestion, target recognition, choice generation, effect/legality/
timing/cost/payment/allocation/characteristic/compatibility evaluator, trigger,
stack, priority, mana-production, reveal, recovery or simulation is implemented.
No real GameplayRulesSnapshot, execution profile, permission decision or action
is created. Query, catalog, admission, publication and workflow behavior remain
unchanged. No dependency, source selector, external AI call, source enrichment or
personal collection access is added. There are no changes under `src/`.

`source_policy_clearance=not_granted`. Private retention, redistribution, free
service, commercial service and AI export each remain **NOT_ESTABLISHED**.
Design approval changes none of these permissions and authorizes no future work.

The concise machine-readable
[design assessment](../reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/design-assessment.json)
records current authorization separately from PR #208's unchanged historical
recommendation. Structural checks can establish format and reference integrity;
humans must assess factual authority, sufficiency, soundness and completeness.
Remaining implementation questions concern author/reviewer authority for any
future real assertion policy, an honest offline presentation of conditions and
supersession, and any separately reviewed evidence-sufficiency or compatibility
contract. Missing knowledge remains a limitation here.

Exactly one subsequent recommendation: **Offline proposed-spell packet authoring
pilot**. Its concrete useful outcome would be a local fictional-only authoring
and structural-review tool demonstrating append-only corrections and separately
attributed reviewer observations over this contract. Empty source allowlist;
zero new source units/projections; no evaluator or runtime admission. This future
milestone is **unauthorized and unbegun**:

```text
future_milestone_authorized=false
future_source_projection_authorized=false
future_milestone_begun=false
```

## Preservation and validation

PR #208's package remains
`sha256:1cf5def840852e91dc157b654006ea48f74c9c12a766f56f4fae40eda3bf7e9e`,
projection `sha256:bd417ee1392485c378ac90e0c453e6410c9674b1e57ec988c8f0ac8149ef1b6f`,
and historical recommendation
`sha256:05ff5d7b7dae1db89973038363ec56aa84e2e970f275685790473bf3ad0be869`.
Historical acquisition remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
Previous packages retain their own domains, identities, manifests and self-bindings;
no historical self-reference is rebound to this design. PR #205/#206 performance
implementations, ledgers, inherited evidence/contracts/fixtures and every source
file remain unchanged. Exact finite adapters extend historical inventories without
removing their original assertions or introducing directory exemptions.

Independent canonical-Git audit compares all **2,863 inherited files / 89,499,907
original bytes and executable modes**, reversing only eight pinned document
appendices and two finite test adapters. It uses actual canonical Git blobs,
not a new whole-repository freeze fixture. The inherited PR #208 audit also
continues to reproduce its own original accounting.

Reproduction commands, with no source selector configured:

```sh
PYTHONPATH=src:tests python tests/proposed_spell_evidence_packet_validation.py
PYTHONPATH=src:tests python -m unittest test_proposed_spell_evidence_packet_design test_proposed_spell_evidence_packet_preservation -v
PYTHONPATH=src:tests python tests/proposed_spell_evidence_packet_preservation.py
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

Focused checks run before one successful complete local discovery on the stable
final changes. Baseline loader count is 2,560; the configured loader now finds **2,575**
(**12** data-driven design methods plus **3** preservation methods). Final counts, skips,
failures, durations and exact logs belong in the PR completion report. Existing
source-dependent skips keep their meaning: offline metadata validation is no
fresh source verification. No complete local publication cycle is duplicated.
Both unchanged final-head hosted runs must pass discovery and actual publication
validation with nested complete discovery, real 654-card writer, disposable bare
remote and matching published/readback heads. Literal checkouts and ordered merge
parents must be recorded. Final hosted evidence belongs in the PR description,
without a metadata-only commit after validation. Stop for independent PM review;
the owner retains final merge approval.
