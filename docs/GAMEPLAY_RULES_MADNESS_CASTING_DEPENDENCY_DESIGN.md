# Madness Casting Dependency Design

## Scope, provenance and current coverage

This milestone defines immutable **DESIGN_ONLY / NON_EXECUTABLE** contracts and
review evidence for the casting dependencies exposed by existing Madness rule
`702.35b`. Canonical main and branch base are
`ccf408904f682d9b2e49ba6d25ade335d80d61fb`, after PR #191 merged. The branch is
`codex/madness-casting-dependency-design`. The intended result is
`MADNESS_CASTING_DEPENDENCY_DESIGN_COMPLETE`.

The design fits **Architecture v13 — ACTIVE APPROVED** and Accepted Decision
017. It adds no Tier-0 authority or runtime contract change. The future profile
`magic-comprehensive-rules-20260925-v1` remains **DESIGN_ONLY / NOT EXECUTABLE**
and `REAL_EXECUTION_PROFILE_NOT_READY`.

The five existing projections still cover **63 real source units**:
20 foundational + 12 direct foundational dependencies + 7 object-control
exceptions + 12 zone-change exceptions + 12 zone-change direct dependencies.
This milestone projects **0** new units. Existing projection, anchor, review
and package identities remain immutable. In particular, `601.2b`, `601.2f`,
`601.2g`, `601.2h` and every candidate dependency below remain unprojected.

The design reproduces from retained repository evidence. The external
Comprehensive Rules TXT is **not required**; no source artifact is read or
fetched, and no real source anchor is created. Release `2026-09-25` is a
conceptual design pin, not a new source-verification claim. The Project
Manager's observations about the four casting stages are explicitly
**DESIGN INPUT**. They do not acquire the authority of the already projected
`702.35a–c` evidence.

## Why design precedes projection

The four current casting references are parts of a larger procedure. Projecting
their source units in a later milestone could supply bounded structured
knowledge. It would leave many casting permissions, legality checks and
runtime operations unresolved. The present design makes those limits explicit
before another projection is scoped.

Two separate conceptual capabilities prevent a partial model from implying
general casting support:

| Capability | Intended scope | Current readiness |
| --- | --- | --- |
| `alternative_cost_casting_subprocedure` | Choice, cost determination, mana-ability opportunity and payment design relevant to a candidate alternative cost. | DESIGN_ONLY / EXECUTION_BLOCKED |
| `complete_spell_casting` | Complete proposal, permissions, targets, legality, stack, completion and consequences. | UNSUPPORTED / EXECUTION_BLOCKED |

The first capability does not satisfy the second. No design sequence has a
runtime transition function, and no contract produces a legally cast spell.

## Four conceptual stages

| Order | Stage | Future source reference | Design purpose |
| --- | --- | --- | --- |
| 1 | `CASTING_CHOICES` | `601.2b` | Record declared casting choices and unresolved choice families. |
| 2 | `TOTAL_COST_DETERMINATION` | `601.2f` | Describe components and the identity of a prospective locked cost. |
| 3 | `MANA_ABILITY_WINDOW` | `601.2g` | Describe a conditional prepayment opportunity, with real `605` unresolved. |
| 4 | `TOTAL_COST_PAYMENT` | `601.2h` | Describe ordered payment groups and a non-executable result contract. |

The ordering is deterministic design data. These references are the exactly
four current frontier references exposed by retained Madness evidence. The
rows do not verify their source text or implement a casting state machine.

### Casting choices and alternative costs

Choice declarations can describe an opaque spell/reference placeholder, chosen
casting method, normal or alternative cost basis, selected additional costs,
variables, modal and splice declarations, hybrid and Phyrexian payment choices,
prior-choice restrictions, knowledge state and unsupported choice families.
These declarations do not select real modes, evaluate X, inspect Card text or
establish legality.

The cost basis is explicitly one of `NORMAL_MANA_COST` and
`SELECTED_ALTERNATIVE_COST`. A Madness declaration can name
`alternative_cost_source=madness`; the Madness cost is a candidate replacement
for the normal base cost. It is not represented as a discount subtracted from
that mana cost. Additional costs, increases, reductions and direct total-cost
modifiers belong to later design components.

Selected alternatives, other candidate alternatives, mutual exclusion,
unknown interactions and unsupported branches have distinct representations.
The contracts preserve conflicts without choosing an alternative or claiming
complete interaction semantics.

### Total-cost expression and lock-in

The expression describes a selected base-cost basis followed by additional
costs, increases, reductions and direct total-cost modifiers. It can identify a
resulting total cost without calculating real costs or applying effects.
`UNDETERMINED`, `DETERMINED` and `LOCKED` are distinct design states. A payment
description binds the exact locked-cost identity, rather than silently
substituting a newly computed cost.

Cost components include mana, tapping, sacrificing, discarding, life, generic
nonmana, unknown and unsupported categories. These are labels in a data
taxonomy; none authorizes an object, permanent, life total or mana-pool change.
No layer or cost evaluator is supplied.

### Mana-ability opportunity

Where the described total cost includes mana payment, the design records the
required opportunity before payment. `605` remains an unresolved real-rule
dependency. Mana abilities, activation, mana pools, mana generation, priority
and payment are unsupported. The fictional engine's simplified mana support
does not establish real `605` authority or semantic closure, and fictional
behavior remains unchanged.

### Payment inventory, ordering and result

A payment design binds a locked total-cost identity, component inventory,
ordered groups and paid/unpaid/unknown/unsupported declarations. Partial
payment is forbidden in the design, and an unpayable cost has an explicit
representation. A declaration of payment status is not a performed payment.

Ordinary components belong to an earlier group. Components involving random
elements or moving a library object to a public zone belong to a later group.
The design represents that distinction without randomization, library access,
card movement, cost execution or legality adjudication.

## Madness evidence binding and readiness

The new package binds existing projected `702.35a`, `702.35b`, `702.35c` and
existing zone-change exception `400.7k` by their retained identities. It does
not change or re-project them. The conceptual dependency path is:

```text
Madness discard replacement / exile
  → Madness trigger
  → owner's optional casting decision
  → Madness alternative-cost declaration
  → casting choices
  → total-cost determination
  → mana-ability opportunity when needed
  → total-cost payment
  → later casting stages outside this design
```

Every arrow describes a requirement, not an executable transition. The
reassessment separately tracks discard replacement, exile, trigger behavior,
casting permission, alternative-cost selection, total-cost determination,
mana-ability opportunity, payment, complete casting legality, public-zone
fallback when the card is not cast, and zone-change lookup. Existing lookup
relationships provide review evidence; they do not provide object-history
execution. Madness remains **EXECUTION_BLOCKED**.

Full casting still lacks proposal/placement, applicable modes and targets,
legality checks, permissions and prohibitions, completion, illegal-action
rollback, stack semantics, priority and trigger consequences. These missing
areas are classified as subsystem boundaries without inventing a new exact
source allowlist for them.

## Conditional branches and fail-closed synthetic proofs

Alternative-cost selection, total-cost determination and payment are central
to the narrow Madness path. A mana-ability opportunity is conditional on mana
payment. Modal, splice, variable, hybrid and Phyrexian branches can depend on
the spell or declaration; they are not required by every synthetic Madness
case. Their absence from one case does not establish general support.

Fictional fixtures exercise known declarations, alternative conflicts,
conditional branch relevance, cost identity binding and unsupported branches.
If an unmodeled branch could affect the answer, the design records
`INDETERMINATE` or `UNSUPPORTED`. It never infers a confident executable
outcome. There are no real Card examples or Oracle-derived fixtures.

## Future source-unit anchor design

Historical projections use `EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR` where
one physical line contains the selected unit. All historical contracts and
anchor identities are preserved. PM **DESIGN INPUT** identifies the future
`601.2b` and `601.2f` units as requiring complete multi-line treatment; a hash
of only the first line would not represent their full units.

The proposed future anchor convention is
`EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR`. A future
projection must explicitly select an anchor type: historical
`SINGLE_LINE_RULE_ANCHOR` or future `MULTI_LINE_RULE_BLOCK_ANCHOR`. No historical
anchor is converted.

The future block contract includes exact numbered rule reference, full-artifact
identity, effective date, starting and ending physical lines, inclusive
`byte_start`, exclusive `byte_end`, `line_count` and SHA-256 of the complete
selected raw-byte block. Internal source line terminators are hashed exactly
as supplied. Only the final source-line terminator is excluded. The retained
anchor contains metadata and hashes, with no source prose.

The conceptual locator begins at an exact numbered marker and includes its
continuation lines. It stops before the next numbered rule/subrule at the same
structural level or the next source unit. It must not consume a following
rule's examples. Parent-unit selection must stop before a child unit instead
of swallowing its body. The future verifier must reject missing or duplicate
starts, ambiguous endings, malformed numbering and overlapping selected spans.
An unresolved ownership/boundary ambiguity fails closed.

Only a design contract and fictional proofs are supplied here. Synthetic
byte fixtures demonstrate internal LF/CRLF preservation, final-terminator
exclusion, deterministic offsets and ambiguity rejection without accessing
real CR bytes. This is not a general CR parser or a new source-verification
result.

## Candidate direct-reference frontier

All entries below have status
`CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_PROJECTION`. They come from PM
**DESIGN INPUT**, remain unprojected and must be verified from the exact
artifact in a separately authorized projection.

| Future origin | Candidate references | Design boundary |
| --- | --- | --- |
| `601.2b` | `700.2`, `702.47`, `118.8`, `118.9`, `601.2f`, `107.3` | Modes, splice, costs, cost-stage relationship and variables. |
| `601.2f` | `601.2b` | Link back to casting declarations. |
| `601.2g` | `605` | Mana-ability subsystem. |

No additional numbered dependency is inferred for `601.2h`. The existing
unprojected blockers `613`, `605`, `603`, `603.7d`, `603.7e`, `603.7f`, `114`,
`901.6`, `902.6`, `904.7` and `905.5` remain unresolved. The new design does
not close any of these frontiers.

## Exactly one future projection recommendation

Recommend **Bounded Casting Rules Projection**, with the exact candidate
allowlist **`601.2`, `601.2b`, `601.2f`, `601.2g`, `601.2h`**: **5** source
units, taking the composite from 63 to 68 only if separately authorized and
successfully verified. This recommendation is **NOT AUTHORIZED** and has not
begun.

| Proposed source unit | Why include it in the coherent projection candidate |
| --- | --- |
| `601.2` | Immediate procedural-parent context frames the selected noncontiguous stages as part of a broader casting procedure. This is a design judgment derived from numbering hierarchy; its body is not a supplied observation or independently verified source evidence. |
| `601.2b` | The retained Madness frontier requires choice and alternative-cost declarations. |
| `601.2f` | The retained frontier requires total-cost determination and lock-in context. |
| `601.2g` | The retained frontier requires the conditional mana-ability opportunity boundary. |
| `601.2h` | The retained frontier requires payment completeness and ordering context. |

The candidate is the smallest coherent scope identified by this design review,
rather than four disconnected stages. The future exact source artifact must
confirm the parent context and all unit boundaries. If it reveals insufficient
context or ambiguous source units, the future work must fail closed for scope
review instead of silently adding rules. Other `601.2*` stages are excluded;
the candidate is not complete casting.

The verified external TXT **will be required** for that future projection.
Use `MULTI_LINE_RULE_BLOCK_ANCHOR` uniformly for all five candidate units under
`EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR`. A future unit
verified to occupy one physical line is a degenerate block with `line_count=1`.
Historical `SINGLE_LINE_RULE_ANCHOR` contracts remain unchanged. No present byte
spans or source hashes are claimed for those five units.

The external candidate references `700.2`, `702.47`, `118.8`, `118.9`, `107.3`
and `605` should remain unresolved after that bounded projection. Candidate
links between selected `601.2b` and `601.2f` would become represented only if
the future artifact verifies them. Any parent-origin direct references remain
unknown until source verification and must be recorded without automatic
expansion. General costs, mana abilities, broader abilities/control,
continuous effects and complete casting require separately bounded milestones.

## Review package, identities and preservation

The append-only package is
`reference-reviews/gameplay-rules-madness-casting-design/`:

- `source-anchor-design.json`: compatibility and future raw-byte block policy.
- `casting-subprocedure-design.json`: ordered design stages and capability boundary.
- `cost-design.json`: cost basis, components, lock-in and payment contracts.
- `madness-readiness.json`: retained evidence binding and blocked readiness.
- `projection-frontier.json`: design-input candidates and the one future recommendation.
- `manifest.json`: canonical file inventory and retained package identity.

| Retained identity | SHA-256 identity |
| --- | --- |
| Source-anchor design | `sha256:c42c8dd774a263f182c08e66135aca4e5668d4f5f70af480a6c0d281b187ee19` |
| Casting subprocedure | `sha256:ca2acabb2fbca0e958165ef4cc4d48d3736885458053219507cddd58c5eb611a` |
| Cost model | `sha256:6980770de834b9a2c29a2bfbdfdb7d2f12f676a2c760c216849d20a180980937` |
| Madness readiness | `sha256:8c3accfaec25c1ffb53efbafa49fa8f9fab395ce382474653da179b029e274ac` |
| Projection frontier | `sha256:a843e39ef3d1350c5e45a0a31bc8c4cf137e52671c1b7b7d6304cc9e18631c82` |
| Package | `sha256:06cd012d08d204f10337d834f312bcf19b060a3569ef3cf879c46714d30944c8` |

Canonical serialization derives deterministic identities for the anchor design,
casting design, cost model, Madness reassessment and package. Meaningful design
input changes change identities; no mutable latest identity is introduced.
Package verification rejects tampering, extra files and noncanonical package
forms. Relocation and reconstruction use repository evidence rather than an
external source path. No official prose, excerpts, examples, TXT or external
path is retained.

The six prior rules/design packages remain byte-identical, including the
foundational package, execution-profile design, foundational dependencies,
object-control exceptions, zone-change exceptions and zone-change direct
dependencies. Historical acquisition replay identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

## Runtime, permissions and review boundary

`GameplayRulesEngine`, `GameplayRulesSnapshot`, `GameState`, `GameAction`,
`LegalityResult`, `GameTransition`, `CardGameplaySemantics`,
`ENGINE_CONTRACT_VERSION` and `EXECUTION_PROFILE` remain unchanged. No real
snapshot, runtime conversion or profile activation is supplied. Fictional
gameplay retains its separate authority and unchanged behavior.

Casting, Madness, cost calculation, cost payment, mana abilities, Card
semantics and simulation remain unsupported. No Oracle, Gatherer, Scryfall
substitute or real Madness Card text is ingested. No continuous effects,
layers, SBAs, attachment legality, triggers, replacement-effect execution,
zone movement, stickers, meld or merge runtime is introduced.

`source_policy_clearance=not_granted`. Private retention, redistribution,
free service, commercial service and AI export remain `NOT_ESTABLISHED`.
Product Rules, Tier A, Card Intelligence, canonical catalog, MB2,
`SOURCE_POLICY_CLEARED_PLANS` and writer/admission are unchanged.

Focused tests and regressions must validate the immutable design, fictional
anchor proofs, provenance labels, unchanged 63-unit coverage, prior-package
preservation and runtime boundaries. Complete discovery, publication regression
and `git diff --check` provide publication validation. The recorded results
belong in the PR and final execution report; this document makes no unrun-test
claim. Stop at one draft PR for independent PM review; do not merge or begin
the recommended projection.
