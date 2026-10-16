# V13 Functional-Role and Contextual-Comparison Attachment Integration

Status: separately owner-authorized implementation, pending independent Project
Manager inspection. Architecture v13 is ACTIVE APPROVED; Decision 017 is Accepted.
Reviewed canonical main: `bea66e1b52eae0c20dc82a6959b2ecbd7c9698e6`.
The Tier A Mechanical Card Intelligence/Acquisition integration is merged in PR #180.

This milestone extends the existing explanatory path through its remaining two
Card Intelligence consumers. It changes construction and live integrity checks,
not authored role interpretations, comparison arithmetic, Decision policy or
retained content-addressed formats. It supplies no approval or production authority.

## Explicit dependency-injection API

```python
from pathlib import Path

from card_intelligence.comparison import ContextualCardComparisonPilot
from card_intelligence.mechanics import MechanicalCardIntelligence
from card_intelligence.roles import FunctionalRolePilot
from repository.legacy_profile import attach_legacy_compatibility

attachment = attach_legacy_compatibility(
    Path("/explicit/existing-checkout"),
    control_path="config/catalog_profiles/legacy-public-tier-a.json",
    game="magic",
    expected_profile_id=(
        "sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e"
    ),
)
mechanical = MechanicalCardIntelligence.from_attachment(
    attachment,
    data_root=Path("/explicit/mechanical-evidence-root/data"),
    expected_query_snapshot_id=(
        "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"
    ),
)
roles = FunctionalRolePilot.from_mechanical(mechanical)
comparison = ContextualCardComparisonPilot.from_roles(roles)
assert roles.mechanical is mechanical
assert comparison.roles is roles
catalog_binding = comparison.catalog_binding
```

The explicit paths illustrate independently selected retained input roots. They
are not discovery locations or an instruction to acquire provider data. Existing
optional `plan_path` and `vocabulary_path` arguments select the exact authored role
inputs; comparison's `plan_path` selects its exact authored contextual plan.

`FunctionalRolePilot.from_mechanical(mechanical, *, plan_path=None,
vocabulary_path=None)` requires an actual attachment-backed
`MechanicalCardIntelligence`. `ContextualCardComparisonPilot.from_roles(roles, *,
plan_path=None)` requires an actual attachment-backed `FunctionalRolePilot`.
Neither accepts a path, dictionary or arbitrary namespace as verified evidence.
Neither constructs another MCI, query, semantic reader or context builder. An
invalid input remains blocked rather than selecting the legacy constructor.

The original `FunctionalRolePilot(data_root, ...)` and
`ContextualCardComparisonPilot(data_root, ...)` retain their historical direct-root
behavior. Legacy MCI/acquisition constructors, Stage 1 fictional attachment,
Stage 3 Tier A profile and bare query constructor remain unchanged.

## One query and separate authorities

```text
verified catalog attachment
  -> CanonicalQueryEngine.from_attachment(...)
     -> one MechanicalCardIntelligence
        -> CanonicalSemanticQueryEngine(the same query)
           -> the same ReasoningContextBuilder
        -> FunctionalRolePilot.from_mechanical(the same MCI)
           -> ContextualCardComparisonPilot.from_roles(the same roles)
```

Roles build their existing manual reasoning supplements through that MCI. The
contextual comparison uses `self.roles.mechanical.context_builder`; its generic
contexts retain the same `canonical_snapshot_id`. There is no independent
reasoning catalog and no model call. Conversation memory is never an authority.

| Binding | Scope; identity stays separate |
| --- | --- |
| Catalog profile/control and closure | Stage 3's authored Tier A contract and exact 40 in-place file bindings |
| Canonical query snapshot | Existing query serialization/hash semantics, unchanged |
| Mechanical acquisition/source | Independently verified source manifest, retained bytes, acquisition run and exact Oracle-ID correspondence; outside Tier A |
| Mechanical dossier | Existing `mechanical-card-dossier-v1` content identity |
| Role plan and vocabulary | Exact retained authored bytes and their existing content identities |
| Role candidates and dossiers | Existing `functional-role-candidate-v1` and `functional-role-dossier-v1` identities; proposals, not canonical facts |
| Context and comparison | Existing hypothetical-context, plan and comparison identities |
| Decision and handoff | Existing request/policy/analyses/recommendation and structured reasoning-context identities |

Live `catalog_binding` properties return defensive metadata separately from these
domain artifacts. Profile IDs are not inserted into old dossiers, candidate
payloads, Decision recommendations or handoffs. Equivalent canonical, mechanical,
plan and context inputs must therefore retain their original artifact bytes/IDs.

Attached `verify_inputs()` checks preserve the exact MCI/roles objects, catalog
integrity, canonical query identity, game, separately retained mechanical evidence,
role plan/vocabulary and contextual-plan bindings. Retargeting a reader, changing
selected bytes, mutating cached evidence or crossing snapshots blocks subsequent
reads. Missing or ambiguous mechanical coverage stays explicit. No automatic
refresh, fallback, rewritten expected hash or name-based selection is provided.

## Pending-role and abstention boundaries

The retained pilot remains exactly 15 selected Cards and 30 authored role
candidates: 20 known directly supported proposals, four incomplete interpretations,
two unknown proposals and four unsupported assignments. Every candidate and the
provisional vocabulary still require review. Direct mechanical support does not
approve an interpretation. Costs, conditions, timing, restrictions, context
dependencies, complete Oracle-field evidence and selected ability lines remain
unchanged. No classifier, new role, prominence ranking, supersession or
`KnowledgeFact` write is introduced.

The retained contextual comparison remains its three exact Cards in the same
hypothetical scenario, with its eight unchanged pending candidates. Supplied
assumptions, literal-instruction annotations, deterministic arithmetic, unverified
strategic hypotheses, counterarguments and source references are unchanged.
`human_reviewed_context_match` remains unknown. The same Decision policy therefore
returns **ABSTAIN**, null selection and the original abstention reasons. No winner,
power/suitability score, legal timing, deck suitability or interaction correctness
is inferred.

Unsupported dimensions remain net card advantage, format legality, verified rules
timing, competitive superiority, universal best-in-slot, combo strength, synergy
correctness, automatic deck optimization and market/acquisition recommendation.
Oracle text is retained provider evidence; role annotations are authored proposals,
not a Gameplay Rules Intelligence engine.

## Tier A and permission limits

The vertical requires only Tier A entity lookup, exact relationships and selected
provenance, plus separately bound mechanical and authored proposal/context inputs.
It adds no audit or SourceRecord to the catalog. Full promotion audits, rejected
history, validation-failure history, `validation_statistics` and historical
admission replay remain unsupported before excluded I/O.

Tier B Audit-Context Capability Design Review is deliberately **DEFERRED** because
this consumer path needs no Tier B/C operation. Unexpected future audit needs must
be reviewed rather than silently upgrading the profile.

Stage 3's fixed flags remain `production_eligible=false`,
`approval_state=not_granted`, `source_policy_clearance=not_granted` and
`data_processing_permission_established=false`. All seven mixed-content operation
states remain **NOT_ESTABLISHED**: private processing, private operator retention,
existing-public-Git compatibility permission, new public redistribution, free
public service, commercial service and AI/model export. Integrity or successful
explanation supplies no source permission, admission authority or role approval.

No provider acquisition, corpus copy, production snapshot, MB2 admission,
KnowledgeRepository migration, new Decision algorithm, purchase execution, SQL,
AI/model transport, Rules, Deck or simulation implementation is included.

## Compatibility characterization and validation

New tests reuse the existing fictional Tier A/MCI machinery and synthetic authored
role/context inputs under the existing contracts. They prove exact object reuse,
snapshot consistency, pending proposals, abstention, independent catalog/source/
plan/vocabulary/context drift, capability rejection and no network fallback.
The existing source loader's Scryfall-shaped retained-acquisition format is
preserved; fictional evidence does not assert actual provider facts or permission.

A narrow current-public check reads already-tracked bytes **in place**. It compares
legacy and attached role candidates/dossiers/reports/contexts and contextual
comparison/Decision/handoff/explanation for exact parity at query identity
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`.
This is compatibility characterization only. If the expanded writer has changed
the current catalog, the fixed reviewed profile must reject that drift; a test
must not substitute old data or repin the profile.

Historical role/context/mechanical/acquisition artifacts and reasoning handoffs
remain unchanged. Card Acquisition replay keeps its own Architecture-v12 auxiliary
fixture and protected identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
Production canonical bytes, selected audits, SourceRecords, mechanical evidence,
MB2's 810 pending candidates/nine holds and `SOURCE_POLICY_CLEARED_PLANS` are not
modified. Writer/admission/OIDC behavior is outside this read-side milestone.

The milestone PR records actual focused tests, full-suite and expanded-publication
commands, tested revision, counts and terminal exit statuses. The real expanded
publication gate may cover complete discovery once; a duplicate standalone full
run is unnecessary. Hosted results remain separate from local validation.

## Product-value reassessment — next candidate NOT AUTHORIZED

Recommended next milestone: **Gameplay Rules & Interaction Intelligence Foundation
— bounded design, contracts and fictional proof**. This should define a structured,
provenance-bound rules/action model, evidence/version/completeness boundaries and
honest unsupported interaction outcomes before attempting rich real-card support.
It requires separate owner authorization and its own source-permission assessment;
this document authorizes neither acquisition nor rules implementation.

The two remaining existing Card Intelligence consumers now have explicit attachment
paths, so another small migration is not the default next task. Serious gameplay
simulation needs legal actions, payment, timing, zones and state-based actions;
a rules/interaction foundation should precede claims about such simulation.
Deck Intelligence also needs legality, context and reviewed semantics. A generic
simulation foundation can be valuable later, but must not invent interaction
correctness. Tier B should return only when a concrete consumer needs audit
history. None of those domains begins automatically.
