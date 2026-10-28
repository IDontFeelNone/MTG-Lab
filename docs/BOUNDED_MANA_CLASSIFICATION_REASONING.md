# Bounded mana-classification evidence reasoning

This read-only capability computes conditional consequences of the seven unchanged
PR #216 authored readings. It shows satisfied substantive premises, negative
witnesses, unresolved inputs, separate method gaps, the conditional conclusion,
and its relationship to the original proposal. It supplies no official Card
ruling or independently approved semantics.

The exact base is `d6b649bfe82c88012d8b51bc6412e012fc6eddde`, tree
`8f51c376cb61acfc2dda018587e48b457c567602`. PR #216 is merged; its reviewed
head `ada76667709cac5be03326b3764df26f6579a4fb` has the same tree.
Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

## Closed policy

The policy version `card-rules-mana-reasoning-policy-v1` belongs to Card–Rules
review. Its identity is `sha256:5694ec96c5edcbe61895684c6885e556578b738f27a29154d95283542b1ed745`. It uses proposed
kind, the exact criterion IDs and states, and retained rule bindings. Card names,
subject IDs, mana symbols, source substrings, provider `produced_mana`, free-text
rationales and proposed-classification labels never determine the calculation.
The original proposed classification is compared only after calculation.

- Activated substantive conjunction: `activated_kind`, `no_target`,
  `potential_mana`, `not_loyalty`, `no_library_cost_movement`,
  `no_library_effect_movement`.
- Activated method obligations: `self_replacement_considered` and
  `other_replacements_disregarded`. These govern assessment, not Card properties.
- Triggered substantive conjunction: `triggered_kind`, `trigger_no_target`,
  `trigger_potential_mana`, `qualifying_trigger_relationship`. Activated method
  obligations and priority-return context do not transfer to this branch.
- Spell exclusion: the actual pending `proposed_spell_instruction` kind reading,
  retained type line and retained 605.5b. An empty or inapplicable ability matrix
  cannot succeed by vacuous conjunction.

All substantive requirements proposed satisfied yield
`SATISFIED_UNDER_AUTHORED_READINGS`. A proposed-not-satisfied requirement yields
`NOT_SATISFIED_UNDER_AUTHORED_READINGS`, preserving every negative witness and
any other unresolved input. Otherwise unresolved required input yields
`INDETERMINATE_UNDER_AUTHORED_READINGS`. Unknown, unsupported and conflicting
states remain distinct. Required inapplicable rows remain unresolved and never
count as satisfied. Malformed or inconsistent branch layouts reject before
calculation.

Method status is separate: proposed satisfied, incomplete, unmet or conflicting;
branches without these obligations report not applicable. Only proposed-satisfied
applicable obligations permit conditional eligibility or exclusion. An unknown
self-replacement assessment or failure to disregard other replacements leaves the
assessment incomplete or unmet; neither independently establishes exclusion.
Structural validity of a method annotation is not semantic approval.

## Actual unchanged baseline

| Subject | Substantive result | Method | Overall explanation |
|---|---|---|---|
| `sol-ring-tap` | Satisfied | Incomplete | Unknown self-replacement assessment prevents completed conditional classification. |
| `basalt-monolith-tap` | Satisfied | Incomplete | Same gap, with this subject's separate evidence and context. |
| `basalt-monolith-untap` | Not satisfied | Incomplete | Negative `potential_mana` premise remains visible; paying mana differs from producing it. |
| `deathrite-shaman-first` | Not satisfied | Incomplete | Negative `no_target` premise concerns a target requirement, independently of chosen-target count. |
| `dark-ritual-spell` | Conditional spell exclusion | Not applicable | Separately bound pending spell-kind reading, retained type line and 605.5b. |
| `mana-flare-trigger` | Indeterminate | Not applicable | `qualifying_trigger_relationship` remains unknown. |
| `pitiless-plunderer-host-trigger` | Not satisfied | Not applicable | Both negative host potential-mana and qualifying-trigger premises remain visible; the Treasure activation has a different owner. |

Review questions preserve independent subject/candidate provenance. The substantive
gap is Mana Flare's qualifying-trigger relationship. The methodological gaps are
self-replacement assessment on each of the four activated subjects. Basalt untap
and Deathrite already have negative substantive witnesses; completing their
method assessment does not remove those witnesses. Original counterevidence,
selected passages, full-field context and authored missing requirements remain
inspectable in the report's bound candidate context.

## Exactly ten hypothetical cases

For each of the five currently unknown rows, exactly two cases assume
`proposed_satisfied` or `proposed_not_satisfied`, holding every other authored
reading unchanged. No combinations or general scenario language are exposed.

| Subject / unknown row | Assume satisfied | Assume not satisfied |
|---|---|---|
| Sol Ring / self replacement | Conditional activated eligibility | Method unmet; no category exclusion follows |
| Basalt tap / self replacement | Conditional activated eligibility | Method unmet; no category exclusion follows |
| Basalt untap / self replacement | Conditional exclusion; negative potential-mana witness retained | Method unmet; negative witness retained |
| Deathrite / self replacement | Conditional exclusion; negative no-target witness retained | Method unmet; negative witness retained |
| Mana Flare / qualifying relationship | Conditional triggered eligibility | Conditional exclusion |

Every self-replacement case states: “Completing this assessment may require
revising other criterion readings. This hypothetical holds those readings
unchanged.” These are bounded review outcomes under assumptions, not corrected
interpretations, new evidence or replacement candidates. Dark Ritual and Plunderer
have no invented missing-row cases. All cases bind original plan/candidate,
subject, criterion, original and hypothetical state, policy identity, unchanged
input assumption, computed dimensions and explanatory trace.

## API, CLI and reproducible demonstration

Run from the repository root with the actual intact catalog. The publication
writer expands that catalog; an incompatible expanded live catalog must reject.
No historical fixture is substituted for a positive demonstration.

```sh
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
args=(--catalog-root . --mechanical-root . --review-root reference-reviews
  --plan data/review/card-rules-mana-pilot/plan.json
  --expected-profile-id sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e
  --expected-query-snapshot-id sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7
  --expected-plan-id sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83)
python -m card_rules_pilot "${args[@]}" analyze sol-ring-tap
python -m card_rules_pilot "${args[@]}" analyze-all --json
python -m card_rules_pilot "${args[@]}" review-impact
python tools/card_rules_reasoning_demo.py "${args[@]}"
```

```python
from pathlib import Path
from card_rules_pilot import load_reasoning, render_reasoning

reasoning = load_reasoning(
    catalog_root=Path('.'), mechanical_root=Path('.'),
    review_root=Path('reference-reviews'),
    plan_path=Path('data/review/card-rules-mana-pilot/plan.json'),
    expected_profile_id='sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e',
    expected_query_snapshot_id='sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7',
    expected_plan_id='sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83')
print(render_reasoning(reasoning.subject('sol-ring-tap')))
comparison = reasoning.comparison()
impact = reasoning.review_impact()
print(comparison.to_json())
```

Each invocation freshly verifies the actual catalog, mechanical evidence, rules
and plan once, then computes all subject and hypothetical results from that
privately owned snapshot. Read commands create no files or records; callers may
explicitly redirect stdout. Existing `subject`, `compare` and `check` commands
retain their original canonical outputs. Immutable reports return independent
decoded views. Imported or rehashed report content cannot replace fresh public
computation or upgrade authority. Strict closed reproduction checks, exact scalar
types, canonical-byte identities and explicit resource budgets reject alterations.

## Evidence and authority preservation

The unchanged input plan is
`sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83`,
manifest
`sha256:7243ed93272b488b3dd50eb6ea712ca0dda4d6ea2fec6567259455f61b5d8762`,
and original comparison
`sha256:a2b0dedc3ef68b779b5b3a36ec20f97afc348b1ce52ad79c9e4a3cd2a281da0c`.
Derived identity domains are `card-rules-mana-evidence-analysis-v1`,
`card-rules-mana-evidence-comparison-v1`, `card-rules-mana-review-impact-v1`
and `card-rules-mana-hypothetical-case-v1`. None changes the seven candidate
identities. Canonical UTF-8 JSON uses sorted compact keys and one trailing LF.
Identities hash the domain/content wrapper without that LF and exclude only the
own identity field. The original PR #216 bounds remain unchanged; derived reports
have a separate 1,048,576-byte maximum each hypothetical case has a 65,536-byte maximum, and the policy has a
16,384-byte maximum.
Shared immutable original comparison context avoids multiplying full provenance
across the ten cases. Exact provenance remains in the
structured context: source observation/retrieval dates, CR release, dossiers,
rule identities/anchors, retained package bindings and later dependency reviews.
The rule boundary stays exactly 17 units: the complete 13-unit 605 family,
115.6, 606.1, 606.2 and 405.6c. Later reviews do not expand that allowlist.

Every report and hypothetical retains pending authored input authority,
`semantic_review_status=PENDING_NOT_ESTABLISHED`, `requires_review`, null human
attestation, canonical admission false and execution authority BLOCKED. Successful
calculation, code review, PM approval or owner merge approves no Card semantics.
The results establish no activation eligibility, actual mana output, event
causality, legal action, response window or official ruling. Real candidates stay
outside fictional packets/evaluators, KnowledgeFact admission, executable
CardGameplaySemantics and real gameplay snapshots or execution profiles.

Historical acquisition remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
Coverage stays 100 real CR units / 15 projections; semantic closure remains OPEN,
all ten activation responsibilities remain OPEN / EXECUTION_BLOCKED and real
execution remains BLOCKED. Source policy clearance remains not_granted; private
retention, redistribution, free service, commercial service and AI export remain
NOT_ESTABLISHED. Tier A remains non-production with unapproved processing and
operation. No source inspection/acquisition, new interpretation, parser,
projection, engine, external service, model call, embedding or AI export is added.

One draft PR is the review artifact. Stop for independent PM review; the owner
retains final merge approval. No merge, auto-merge or subsequent milestone.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
