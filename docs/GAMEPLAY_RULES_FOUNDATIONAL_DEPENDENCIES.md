# Direct Foundational Comprehensive Rules Dependency Projection

## Scope, result and Architecture v13

This separately owner-authorized milestone adds exactly **12** structured,
non-executable source units from the Comprehensive Rules release effective
**2026-09-25**. It starts from canonical main and branch base
`71652074fe5640d5b2cb4780c63f6b8bab5642d6`, after PR #187 merged. Its milestone
status is `DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED`; the new records remain
`PROJECTED_FOR_REVIEW`. Independent PM review is required. Projection is evidence,
not owner execution approval: `execution_authorized=false` remains fixed.

The append-only dependency projection fits **Architecture v13 — ACTIVE APPROVED**
and Accepted Decision 017. Neither Architecture v14 nor a Decision 017 revision
is required. The authority path remains:

```text
verified official source
  -> original foundational projection
  -> direct dependency projection
  -> review / closure analysis
  -> future execution design
```

There is no source-to-engine path. The target
`magic-comprehensive-rules-20260925-v1` remains **DESIGN_ONLY / NOT EXECUTABLE**.
The reassessment remains **BLOCKED / REAL_EXECUTION_PROFILE_NOT_READY**; no real
rule is executable.

## Exact twelve-rule allowlist

The five unresolved references retained by the original projection were
`104.3a`, `111.2`, `112.2`, `113.10` and section `407`. The selected children make
those direct references representable without expanding into the large deferred
exception families. A parent reference never implicitly selects its children.

| Selected reference | Project-authored semantic scope | Execution boundary |
| --- | --- | --- |
| `104.3a` | A player may choose concession at any time; that choice immediately entails leaving and losing. | No concession operation, multiplayer departure behavior, priority, SBA or complete game-ending policy. |
| `111.2` | The creator supplies a token's ownership and initial control relationship. | No token creation or complete token model; `111.1` and `111.3+` are unprojected. |
| `112.2` | Spell ownership follows the ordinary card relationship, with the rule's distinct copied-spell case; control defaults to the player responsible for putting the spell on the stack, and a spell always has a controller. | No casting, copying or stack execution. |
| `112.2a` | A card-copy made under an effect's instruction and casting permission belongs to the instructed player. | No copying/casting implementation or expansion into `707` or `601`. |
| `113.10` | Ability grants and removals are distinguished as effects with explicit ability-changing language. | No general effect evaluator. |
| `113.10a` | An added activated ability can carry activation instructions supplied by the granting effect. | No activation operation. |
| `113.10b` | Removing a specified ability covers all its instances on the affected object. | No characteristic or layer processing. |
| `113.10c` | Multiple grants/removals of the same ability require an ordering decision. | `613` is `UNRESOLVED`; no interpretation or projection of `613`. |
| `407.1` | Ante is an optional legacy variation, with tournament and legal-policy restrictions outside gameplay execution authority. | No tournament-policy ingestion or legal conclusion. |
| `407.2` | The variant describes setup selection and a game-end ownership consequence. | No Ante execution or random-selection operation. |
| `407.3` | Certain special cards have a restriction tied to using the variation. | No deck-legality engine; deck/tournament policy remains separate. |
| `407.4` | Anteing denotes the variant's object-moving action, restricted by ownership. | No real ante action. |

Exactly these references receive new structured source projections. No thirteenth
rule, deferred exception, dependency target or section heading is projected.
Each record retains a project-authored topic and concise paraphrase, semantic
category/tags, dependencies, unresolved dependencies, exception/subrule
boundaries, limitations, coverage/review states and a source anchor. No official
rule prose or examples are retained.

## Source identity and exact anchors

The external owner-controlled TXT must be present before construction. Its
identity is checked against the actual bytes, using the existing artifact
verification and anchoring infrastructure in `src/gameplay_rules/projection/`.
There is no fallback to a stored hash, reconstructed text or network source.

| Source binding | Required value |
| --- | --- |
| Artifact SHA-256 | `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca` |
| Byte length | `977752` |
| Effective date | `2026-09-25` |
| Existing verification result | `sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3` |
| Existing correspondence review | `sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def` |

Every selected reference must match exactly once. The anchor binds the exact
artifact, effective date, external rule reference, deterministic byte offsets and
line number, and SHA-256 of the source span. Missing or duplicate selected rules
block construction. Only the twelve selected source units are located; this is
not a general Comprehensive Rules parser or recursive dependency explorer.

Source-aware verification recomputes spans from the exact external artifact.
Offline package-integrity verification checks retained authored records and
anchor metadata; it does not claim fresh access to the source bytes. The TXT,
official prose, examples, source excerpts and absolute local source path are
absent from the repository and package. No Wizards fetch, Oracle/Gatherer/Scryfall
ingestion or RawSnapshotStore use is involved. The prior current-designation
observation remains as of 2026-10-16; no new currentness or full bulletin-diff
claim is made.

## Append-only package and composite coverage

The new deterministic package is
`reference-reviews/gameplay-rules-foundational-dependencies/`:

| File | Role |
| --- | --- |
| `projection.json` | Twelve authored dependency projections and exact source anchors |
| `closure-review.json` | Direct-reference findings with semantic/execution closure kept separate |
| `composite-coverage.json` | Read-only coverage view over the original twenty and new twelve source units |
| `execution-readiness-reassessment.json` | Append-only reassessment of the merged PR #187 design |
| `manifest.json` | Exact inventory, content hashes/lengths and package identity |

The generated JSON records and manifest hold the authoritative new identities:

| New binding | Identity |
| --- | --- |
| Dependency projection | `sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1` |
| Dependency package | `sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a` |
| Direct closure review | `sha256:0a0536019dce76146e31698562bcb549c130ea8d26b578416594fa181bb57aec` |
| Composite coverage | `sha256:3f39dac3844a02da32d2ceb2bcdad470e1f29ae86511c50d832adae3109b981b` |
| Execution-readiness reassessment | `sha256:1d5cff65c03b88d2d46d550d684b5e93e70013b2c4e1eec9bb84603dfe9c0fc0` |

The new projection has its own scope/contract and identity. It reuses the existing
projection infrastructure rather than replacing the original projection or
introducing a source-to-runtime converter.

The original package at
`reference-reviews/gameplay-rules-foundational-projection/` remains byte-identical:

| Preserved binding | Identity |
| --- | --- |
| Original projection | `sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7` |
| Original projection package | `sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea` |
| PR #187 execution-design package | `sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687` |
| PR #187 projection execution-design review | `sha256:f1b57c6465e5a9dfcb96ec241e5e83d12cbbdd1d5b47546090c4d8ac44a2b104` |

The composite binds both distinct projection/package identities and reports
**20 + 12 = 32 real projected source units**. It reports projected references,
direct dependencies resolved, remaining unresolved rules, open exception
families, new boundaries, affected capabilities and execution status. It is a
read-only derived view, not a replacement projection, merged executable rule set
or mutation of the old projection ID. The original status and all historical
review/permission values remain unchanged.

## Read-only reproduction

From the repository root, the following verifies the exact five-file package,
its prior evidence lineage and deterministic reports without source TXT or
network access. To also reproduce from actual source bytes and verify all twelve
span hashes, set `MTG_RULES_SOURCE_TXT` to the external owner-controlled TXT
before running the same command. The source-aware branch rebuilds only in memory;
it does not write source content or replace retained evidence.

```bash
PYTHONPATH=src python - <<'PYCODE'
import os
from pathlib import Path
from gameplay_rules.projection.dependency_package import (
    build_dependency_package, load_dependency_package,
)
from gameplay_rules.projection.dependency_source import (
    verify_dependency_projection_source,
)

base = Path("reference-reviews")
roots = {
    "projection_root": base / "gameplay-rules-foundational-projection",
    "design_root": base / "gameplay-rules-execution-profile-design",
    "artifact_review_root": base / "gameplay-rules-artifact-verification",
    "source_root": base / "gameplay-rules-source-versioning",
    "discovery_root": base / "gameplay-rules-release-discovery-closure",
}
records = load_dependency_package(
    base / "gameplay-rules-foundational-dependencies", **roots,
)
print("VERIFIED_DEPENDENCY_PACKAGE_INTEGRITY", records["projection.json"].identity)
artifact = os.environ.get("MTG_RULES_SOURCE_TXT")
if artifact:
    rebuilt = build_dependency_package(artifact, **roots)
    assert set(rebuilt) == set(records)
    assert all(rebuilt[name].to_dict() == records[name].to_dict() for name in records)
    source_roots = {name: roots[name] for name in (
        "artifact_review_root", "source_root", "discovery_root",
    )}
    print(verify_dependency_projection_source(
        records["projection.json"], artifact, **source_roots,
    ))
PYCODE
```

The source-aware result is `VERIFIED_EXACT_SOURCE_SPANS`, with exactly twelve
anchors, the required source hash/length/effective date,
`source_body_retained=false`, `execution_authorized=false` and
`real_rules_executable=false`. Offline integrity alone makes no fresh-span claim.
A source mismatch, missing/duplicate selected rule, changed retained record,
wrong prior package or extra source file blocks verification. Relocation does
not change identities because source paths and package-root paths are not
identity inputs.

## Direct resolution and execution-readiness reassessment

`DIRECT_REFERENCE_RESOLVED` means that selected, anchored projection evidence now
represents the named target. It does not mean
`SEMANTICALLY_CLOSED_FOR_EXECUTION`. The closure records keep
`SEMANTIC_CLOSURE_OPEN` and `EXECUTION_BLOCKED` explicit.

| Original direct reference | New evidence | Finding |
| --- | --- | --- |
| `104.3a` | `104.3a` | `DIRECT_REFERENCE_RESOLVED` |
| `111.2` | `111.2` | `DIRECT_REFERENCE_RESOLVED` |
| `112.2` | `112.2`, with `112.2a` represented separately | `DIRECT_REFERENCE_RESOLVED` |
| `113.10` | `113.10`, `113.10a`, `113.10b`, `113.10c` | `DIRECT_REFERENCE_RESOLVED` |
| `407` | `407.1`, `407.2`, `407.3`, `407.4` | `DIRECT_REFERENCE_RESOLVED`; section represented by four units |

All **five** original direct unresolved references are represented by the new
projection evidence. The append-only reassessment binds the unchanged PR #187
design package and records the narrower effect on its blockers:

| Original rule/capability | Direct dependency change | Execution finding |
| --- | --- | --- |
| `101.1` | The concession exception target `104.3a` is represented. | Conflict/Card-effect semantics and concession/game-end execution remain absent. |
| `101.2` / `101.2a` | The `113.10` family is represented. | `113.10c` exposes unresolved `613`; executable ability/effect semantics remain absent. |
| `108.3` | The `407` family is represented. | Ante remains unsupported; complete ownership semantics are not established. |
| `108.4` | The `112.2` spell relationship and `112.2a` case are represented. | Spell/control/casting/copy primitives remain absent; complete control closure is not established. |
| `110.2` | The `111.2` token-ownership target is represented. | Token-creation and ownership runtime primitives remain absent. |

These are dependency findings, not claims that ownership, control, precedence or
game-ending behavior is executable. Remaining result-affecting exception
families, incomplete semantic closure, absent real primitives, absent
Card/effect semantics, absent deterministic real-runtime vectors and absent owner
activation continue to block execution. Structural and fictional regression
results cannot substitute for real-profile execution vectors.

## Newly exposed boundaries and Ante policy

Rule `113.10c` explicitly exposes `613` as an `UNRESOLVED_RULE`. The dependency is
recorded without reading, projecting or interpreting `613`; ability-modification
execution remains blocked. The authored requirements are explicit:

| Classification | Newly recorded boundary |
| --- | --- |
| `UNRESOLVED_RULE` | `613` |
| `EXTERNAL_POLICY` | `tournament_policy`, `applicable_law`, `deck_policy` |
| `UNSUPPORTED_VARIANT` | `ante_variant` |
| `FUTURE_SEMANTIC_PRIMITIVE` | `concession_transition`, `token_creation`, `spell_copy_and_casting`, `card_effect_interpretation`, `ability_activation`, `ability_modification`, `ante_state_and_ownership`, `zone_inspection` |

These names record closure questions, not implemented contracts or primitives.
Non-rule requirements remain `OUT_OF_SCOPE` for this milestone. Dependency
recording never authorizes recursive projection or expands the twelve-rule
allowlist.

Ante is an `UNSUPPORTED_VARIANT` for execution. Tournament rules and deck-policy
authority are separate `EXTERNAL_POLICY` boundaries. This package ingests no
tournament rules, implements no deck-legality decision and gives no legal
conclusion. Its descriptive setup, ownership and action relationships do not
provide an Ante implementation. Random choice, game-end ownership changes and
anteing require separately reviewed future semantics if ever authorized.

## Deferred exception families

The following **19** exception references remain individually `UNPROJECTED`:

- `109.4a`, `109.4b`, `109.4c`, `109.4d`, `109.4e`, `109.4f`, `109.4g`.
- `400.7a`, `400.7b`, `400.7c`, `400.7d`, `400.7e`, `400.7f`, `400.7g`,
  `400.7h`, `400.7i`, `400.7j`, `400.7k`, `400.7m`.

The `109.4` exceptions branch into mana abilities, triggered abilities, emblems
and casual variants. The `400.7` exceptions branch into continuous effects,
prevention, triggered abilities, casting, state-based actions, madness and
stickers. Those areas require their own coherent future projections. This
milestone preserves the already-known family boundaries without inspecting or
projecting their dependencies. Their parent rules remain limited baseline
semantics, not complete control or zone-change identity policies.

## Runtime, permissions and protected state

`GameplayRulesEngine`, `GameplayRulesSnapshot`, `GameState`, `GameAction`,
`LegalityResult`, `GameTransition`, `CardGameplaySemantics`,
`ENGINE_CONTRACT_VERSION` and `EXECUTION_PROFILE` remain unchanged. The only
executable profile is still `fictional-two-player-v1` under `gameplay-kernel-v1`.
No real snapshot, profile activation, projection-to-engine path,
`to_rules_snapshot()` or ownership, spell-control, token, concession,
ability-modification or Ante runtime primitive is introduced.

No Oracle ingestion or real Card semantics, mana, priority, casting, layers,
SBA implementation or simulation is added. Rules `106`, `117`, `118`, `601`,
`603`, `605`, `613` and `704` are not implemented; `src/simulation/` is unchanged.
Source policy remains `source_policy_clearance=not_granted`. Source-content
private retention, redistribution, free service, commercial service and AI
export remain `NOT_ESTABLISHED`.

All prior gameplay evidence packages, source/versioning, discovery, artifact
verification, original projection and execution-design evidence remain
byte-identical. Protected Card Acquisition identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`
is preserved. Product Rules, canonical catalog, Tier A, Card Intelligence, MB2,
`SOURCE_POLICY_CLEARED_PLANS` and writer/admission remain unchanged.

## Limitations and next milestone

Twelve source-anchored records close five direct reference gaps, not complete
Magic semantics. The complete dependency graph and semantic closure remain
unknown. Policy boundaries and unsupported variants are explicit; no permission,
owner approval or executable behavior follows from projection.

The one recommended next candidate is **Object-Control Exception Family
Projection — NOT AUTHORIZED**. This follows the retained capability matrix and
known exception inventories: the seven `109.4` exceptions still block control,
and form a smaller known coherent family than the twelve `400.7` exceptions.
The newly unresolved `613` has no reviewed bounded dependency scope, while
complete semantic closure remains insufficient to justify state-primitive
contracts. The comparison uses retained evidence, without inspecting any
deferred rule's source or projecting its dependencies.

A later milestone requires its own exact scope and source-use boundary. No next
milestone is implemented here. This milestone ends with one draft PR for
independent PM review; do not merge or activate real rules.
