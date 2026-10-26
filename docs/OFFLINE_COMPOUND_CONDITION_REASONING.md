# Offline compound condition reasoning

This versioned extension answers explicitly authored fictional questions such as
`ALL_OF(gate, ANY_OF(route-a, route-b))`. Ordinary evaluation, missing-input
sensitivity and evaluation across explicitly named alternatives use one shared v2
expression evaluator. No Card text, rule text or predicate prose becomes a fact.
Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

## Exact base and compatibility

GitHub main is authoritative. PR #214 is merged at
`a79fdd22aeb1c68be0cd11a207b6c102ea3e53b8`, with ordered parents
`def003e8591c5bb15a1fa31bd960713f80bb7841` and reviewed head
`a4a73bb589124ca97f4c028f2f0011c46a27ef39`. Main and that head have identical
tree `981a76c693d7bc84fb9b0ce2f4028a314a24cbd4`. The initially clean stale
checkout at `def003e8591c5bb15a1fa31bd960713f80bb7841` was reconciled by
creating `codex/offline-compound-condition-reasoning` from exact canonical main.

Version dispatch is explicit through `model_version` or `definition_version`.
Unknown versions reject. There is no fallback, implicit migration, substitution
or reinterpretation of v1 payloads. Existing v1 model/definition classes remain
strict. V1 accepted/rejected inputs, flat ALL_OF policy, canonical outputs and
ordinary/sensitivity/alternative identities remain unchanged. Packet v1 and its
admission and authoring contracts remain unchanged. Narrow dispatch changes have
exact finite reversible preservation adapters; historical bodies and pins stay
intact. Reports remain computed outputs, never imported proof inputs.

## Versions, identities and authority

| Contract | Exact version / identity domain | Own identity field | Authority |
|---|---|---|---|
| Compound model | `fictional-condition-model-v2` | `model_id` | `AUTHORED_FICTIONAL_CONDITION` |
| Evaluator policy | `fictional-condition-evaluator-policy-v2` | `policy_id`, embedded as `evaluator_policy_id` | `BOUNDED_FICTIONAL_EXPRESSION_COMPOSITION_POLICY_ONLY` |
| Ordinary result | `fictional-condition-result-v2` | `result_id` | `NAMED_FICTIONAL_CONDITION_UNDER_ASSERTIONS_ONLY` |
| Sensitivity report | `fictional-condition-sensitivity-report-v2` | `report_id` | `HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY` |
| Sensitivity policy | `fictional-condition-sensitivity-policy-v2` | `policy_id`, embedded as `sensitivity_policy_id` | `REPOSITORY_DEFINED_FICTIONAL_SENSITIVITY_POLICY` |
| Alternative definition | `fictional-alternative-requirements-v2` | `definition_id` | `AUTHORED_FICTIONAL_REQUIREMENTS` |
| Alternative report | `fictional-alternative-requirements-report-v2` | `report_id` | `LISTED_FICTIONAL_ALTERNATIVES_UNDER_ASSERTIONS_ONLY` |
| Alternative policy | `fictional-alternative-requirements-policy-v2` | `policy_id`, embedded as `comparison_policy_id` | `REPOSITORY_DEFINED_FICTIONAL_ALTERNATIVE_COMPARISON_POLICY` |

Each policy is a finite repository-owned content object with its own `policy_id`,
`policy_version`, authority and explicit algorithm description. It is embedded
with its identity in the corresponding output; it is never an imported policy or
plugin. Policy identities use their own version domains. Content identities use the established
canonical JSON and `v.identity(version, value, own_field)`: hash the domain and
content excluding only its own identity field, prefixed `sha256:`. No v1 result
domain or policy label identifies the new semantics. All execution authority is
`BLOCKED`; retained rule context authority is
`RETAINED_VERSIONED_RULE_CONTEXT_ONLY`.

Models and definitions own private immutable canonical bytes and return independent
decoded views. Reports are produced only by their evaluators and likewise own
immutable bytes. Caller mutation of input mappings, decoded views or files cannot
attach an existing identity to changed report content. Identical inputs reproduce
identical bytes; paths, clocks and randomness do not enter these identities.

## Closed model and expression contract

The v2 model requires exactly `model_id`, `model_version`, `authority`,
`condition_id`, `condition_name`, `packet`, `scope`, `leaves` and `expression`.
`seal_model` in `proposed_spell_packets.conditions_v2` accepts the same fields
without `model_id`, derives it, and returns an independent validated dict.
`ConditionModel` validates an already sealed definition.

```python
from proposed_spell_packets import conditions_v2 as c

model = c.seal_model({
    "model_version": "fictional-condition-model-v2",
    "authority": "AUTHORED_FICTIONAL_CONDITION",
    "condition_id": "gate-and-route",
    "condition_name": "Explicit fictional gate and either route",
    "packet": {
        "packet_id": packet_id, "contract_id": contract_id,
        "schema_version": "proposed-spell-evidence-packet-v1",
        "lineage_id": "fictional:e:lineage", "revision": revision,
    },
    "scope": {"context_id": "ctx", "context_version": 1,
              "alternative_id": alternative_id},
    "leaves": [
        {"leaf_id": "gate", "claim_refs": gate_refs, "expected": True},
        {"leaf_id": "route-a", "claim_refs": route_a_refs, "expected": True},
        {"leaf_id": "route-b", "claim_refs": route_b_refs, "expected": True},
    ],
    "expression": {"operator": "ALL_OF", "children": [
        {"leaf_id": "gate"},
        {"operator": "ANY_OF", "children": [
            {"leaf_id": "route-a"}, {"leaf_id": "route-b"}]}]},
})
```

Replace every packet field and reference with an exact admitted binding. Each
leaf supplies one complete eligible assertion group for one exact
`(context_id, subject_id, predicate)` and one exact Boolean expectation. General
claims plus matching-alternative claims are included. Reusing the fact group under
another leaf ID rejects, even with a different expectation. Claim order remains
authored identity content. Original values, conditions, attribution, basis and
limitations remain in results. Predicate strings remain opaque. Expected false is
an explicit Boolean comparison; no general NOT exists.

Only two closed node shapes exist: `{"leaf_id": token}` and
`{"operator": "ALL_OF" | "ANY_OF", "children": [node, ...]}`. Nodes cannot
override packet, context, alternative, evidence or expectation. The embedded tree
has no expression-node references, graph, recursive macro or general expression
language. Repeated references to one leaf are allowed and correlated. Every
declared leaf must be referenced and every reference must resolve. A leaf-only
root is supported.

| Bound | Ordinary v2 model | V2 comparison definition |
|---|---|---|
| Distinct leaves / shared requirements | 1–32 | 1–32, shared by every candidate |
| Claim references | 1–64 per leaf, no duplicate reference | 1–64 per requirement/candidate binding; complete groups required |
| Named candidates | One alternative scope or null | 1–16 distinct explicitly named alternatives |
| Expression nodes | At most 128, including every leaf-reference occurrence | One common tree, same limit; also applies to every composed model |
| Expression depth | At most eight, root depth one | Same common tree limit |
| Compound children | 1–32 per operator; empty rejects | Same |
| Canonical bytes | At most 64,000 | At most 1,024,000, cumulative with every candidate model's 64,000 |
| Raw JSON depth | At most 20, root depth zero | At most 20, root depth zero; candidate model limit also applies |
| Raw structural nodes | At most 8,192 | At most 65,536, cumulative with candidate model limit |
| Key / string length | At most 128 / 4,096 characters | Same |
| Sensitivity cases | At most 64: two per selected UNKNOWN group | Aggregate sensitivity is outside scope; each emitted model supports ordinary sensitivity |

Expression depth and raw JSON structure are distinct limits. The raw allowance
accommodates eight expression levels including intervening child arrays. Existing
v1 raw JSON depth eight is unchanged. Collection maxima are cumulative with byte
and structural budgets; sufficiently long references can hit a byte budget first.
Packet admission retains its existing independent limits.

All schemas are closed. Exact scalar types reject Boolean integer substitutes,
floats, tuples, non-string keys, null expectations and custom objects without
coercion. Local IDs match `[a-z][a-z0-9-]{0,63}`. Revision/context versions are
exact integers from 1 through 2,147,483,647. Duplicate JSON keys, nonfinite values,
unknown fields, malformed types, stale identities and unsupported versions reject.
Bounded local readers retain the existing no-symlink/no-hardlink protections.

## Normative composition and full validation

Reviewed v1 leaf-group semantics are reused unchanged. A complete group containing
UNKNOWN, unsupported, conflicting or unsupported non-Boolean evidence remains
`UNRESOLVED`. A known mismatch inside that group stays visible independently and
does not turn the unresolved group into a determinate false leaf. Missing eligible
groups remain binding errors; no UNKNOWN assertion is synthesized and no empty
group succeeds.

V2 applies the following only between expression children:

| Operator | Child outcomes | Node outcome |
|---|---|---|
| ALL_OF | Any determinate MISMATCH | MISMATCH |
| ALL_OF | No MISMATCH, at least one UNRESOLVED | UNRESOLVED |
| ALL_OF | Every child MATCH | MATCH |
| ANY_OF | Any determinate MATCH | MATCH |
| ANY_OF | No MATCH, at least one UNRESOLVED | UNRESOLVED |
| ANY_OF | Every child MISMATCH | MISMATCH |

The root maps MATCH to `SATISFIED_UNDER_ASSERTIONS`, MISMATCH to
`NOT_SATISFIED_UNDER_ASSERTIONS`, and UNRESOLVED to `INDETERMINATE`.

| Explicit policy contrast | Result |
|---|---|
| V1 flat ALL_OF(MISMATCH, UNRESOLVED) | INDETERMINATE, unchanged |
| V2 ALL_OF(MISMATCH, UNRESOLVED) | NOT_SATISFIED_UNDER_ASSERTIONS |
| V2 ANY_OF(MATCH, UNRESOLVED) | SATISFIED_UNDER_ASSERTIONS, unresolved findings retained |

The entire model, all branches/references and complete groups validate before any
result is calculated. An invalid branch rejects the whole request even alongside
a decisive branch. Every leaf and expression node is evaluated; success or failure
does not discard evidence. Explanation traces identify stable paths, parent/child
relationships, operator/policy, child outcomes and determining outcomes or the
unresolved reason. Full leaf findings preserve missing, unsupported and conflicting
inputs and independent known mismatches. Root and authority limits remain explicit.
A determinate root establishes the answer only to this authored formula; unresolved
facts remain unresolved and may matter to other questions.

The ordinary output fields are `result_id`, `result_version`,
`evaluator_policy_version`, `evaluator_policy_id`, `evaluator_policy`,
`model_version`, `authority`, `execution_authority`, `packet`, `model_id`,
`condition_model`, `condition_id`, `condition_name`, `scope`, `context`, `leaves`,
`expression_nodes`, `selected_input_findings`, `computed_result`,
`explanation_trace`, `limitations`, `retained_rule_context_authority`,
`retained_rule_context` and `packet_context`.
Every leaf outcome contains `leaf_id`, `leaf_kind=BOOLEAN_ASSERTIONS_EQUAL`,
`expected`, `claim_refs`, original `assertions`, `assertion_evaluations`,
`findings`, `status` and `known_mismatch_claim_refs`. Actual assertion evaluations
retain `claim_id`, `original_value`, `original_condition` and `boolean_match`.
Findings retain their `kind` and `claim_refs`; selected findings also identify
`leaf_id`. The packet context separately retains authored conclusion, limitations,
unselected claims, reasoning, choices, history, validated ancestor IDs and the
unapproved-model review authority.

Expression nodes are emitted in deterministic preorder. Each has `path`,
`parent_path`, `policy_version`, `children`, `child_outcomes`, `status`,
`determining_child_paths` and `explanation`; leaf-reference nodes also have
`leaf_id`, while compound nodes have `operator`. Paths are `root`, `root/0`, etc.
Each child outcome identifies its path and status. The ordinary explanation trace
contains these same nodes; original evidence remains in the leaf outcomes.

## Sensitivity and named alternatives

Sensitivity preserves the exact ordinary v2 baseline bytes and identity separately.
In leaf-definition order, each group with actual UNKNOWN claims receives two
independent cases: uniformly true, then false, starting from the actual baseline.
PRESENT, UNSUPPORTED, CONFLICTING and non-Boolean evidence remain fixed. There are
no cross-group combinations or solver. One reused leaf is calculated once per case;
its changed value applies to every expression occurrence. Repetition creates
neither independent unknowns nor extra cases. The whole expression is recomputed.

Cases report explicit hypothetical assignments, affected leaf outcomes, all node
outcomes and changes, root changes or stability, remaining findings and known
mismatches. Hypothetical states are `SATISFIED_UNDER_HYPOTHESIS`,
`NOT_SATISFIED_UNDER_HYPOTHESIS` or `INDETERMINATE_UNDER_HYPOTHESIS`, with distinct
hypothetical authority. They never become assertions, ordinary factual results,
reviews or gameplay events.

Sensitivity output fields are `report_id`, `report_version`,
`sensitivity_policy_version`, `sensitivity_policy_id`, `sensitivity_policy`,
`authority`, `execution_authority`, `model_version`, `evaluator_policy_version`,
`evaluator_policy_id`, `baseline_result_version`, `packet`, `model_id`,
`baseline_result_id`, `condition_id`, `condition_name`, `scope`, `baseline`,
`sensitivity` and `limitations`. The sensitivity object has `status`, `case_count`
and `cases`. Every case has `sequence`, `selected_leaf_id`, `unknown_claim_ids`,
`assumed_value`, explicit `assumptions`, `evidence_ref`, `leaves`,
`expression_nodes`, `expression_node_changes`, `hypothetical_result`,
`root_change`, `remaining_unresolved_leaves`, `remaining_input_findings`,
`known_mismatches`, `computed_mismatches`, `affected_leaf_change` and
`aggregate_explanation`. Case leaves refer to actual baseline evidence and retain
effective values, hypothesis flags, comparisons, findings and statuses; each node
change identifies its path, baseline/hypothetical statuses and whether they changed.
Root change uses the ordinary baseline result separately from its hypothetical
result label. `known_mismatches` preserves actual mismatches, while
`computed_mismatches` describes effective hypothetical comparisons.

The v2 alternative definition extends the existing closed definition with one
`expression`. Its required fields are `definition_id`, `definition_version`,
`authority`, `packet`, `scope`, `requirements`, `expression` and `candidates`.
Each shared requirement is exactly `{requirement_id, subject_id, predicate,
expected}`; expression `leaf_id` references use these requirement IDs. Each
candidate is exactly `{alternative_id, bindings}`, each binding exactly
`{requirement_id, claim_refs}`. Every candidate binds every shared requirement once.
Only alternative scope and complete eligible bindings differ; expression, fact
keys and expectations are shared. Nodes never select alternatives or borrow
another candidate's evidence. `seal_definition` and `AlternativesDefinition` in
`proposed_spell_packets.alternatives_v2` author/validate this explicit input.

Each composed candidate has `condition_id=shared-requirements` and
`condition_name=Shared fictional requirements`. Leaf order is common requirement
order; IDs map exactly from requirement IDs. Comparison output fields are
`report_id`, `report_version`, `comparison_policy_version`,
`comparison_policy_id`, `comparison_policy`, `definition_version`, `definition_id`,
`definition`, `authority`, `execution_authority`, `condition_model_version`,
`condition_result_version`, `evaluator_policy_version`, `evaluator_policy_id`,
`packet`, `scope`, `context`, `requirements`, `expression`, `candidates`,
`computed_result`, `satisfying_alternative_ids`, `aggregate_explanation`,
`limitations` and `retained_rule_context_authority`. Every candidate retains
`alternative_id`, `scope`, its complete `condition_model`, `model_id`, complete
`condition_result`, `result_id`, `computed_result`, `requirement_outcomes`,
`selected_input_findings` and `known_mismatches`. Requirement outcomes retain the
common requirement plus `status`, actual `claim_refs` and
`known_mismatch_claim_refs`; mismatch entries identify requirement and claims.

Every emitted candidate model and ordinary result matches standalone v2 evaluation
of that exact model, including canonical bytes and identities. All candidates and
findings remain visible. The existing finite aggregate is unchanged:

| Listed candidates | Aggregate |
|---|---|
| At least one satisfied | `LISTED_WITNESS_FOUND_UNDER_ASSERTIONS`, with all listed witnesses in authored order |
| None satisfied, at least one indeterminate | `INDETERMINATE_NO_LISTED_WITNESS_ESTABLISHED` |
| Every candidate determinately not satisfied | `NO_LISTED_WITNESS_UNDER_ASSERTIONS` |

The list is explicitly non-exhaustive. No ranking, preferred candidate, combined
alternative, feasibility or co-selection is inferred. Candidate A meeting the gate
and candidate B meeting a route do not create one witness. Sensitivity of this
aggregate is outside scope; each emitted v2 candidate model works with the ordinary
sensitivity command.

## CLI, demonstration and validation evidence

The existing workflow dispatches on the explicitly authored input version:

```sh
export PYTHONPATH=src
python -m proposed_spell_packets --workspace "$workspace" evaluate \
  "$packet_id" --model "$workspace/model-v2.json" --json
python -m proposed_spell_packets --workspace "$workspace" sensitivity \
  "$packet_id" --model "$workspace/model-v2.json" --json
python -m proposed_spell_packets --workspace "$workspace" evaluate-alternatives \
  "$packet_id" --requirements "$workspace/alternatives-v2.json" --json
compound_workspace=$(mktemp -d)
python tools/proposed_spell_compound_demo.py --workspace "$compound_workspace"
```

Omit `--json` for deterministic readable explanations. JSON writes immutable
canonical report bytes to stdout. Contract/integrity errors exit nonzero with
REJECTED and execution authority BLOCKED. The actual demonstration uses authoring,
admission and these CLI entry points in a disposable workspace outside the
repository. It admits an exact retained root, authors attributed Boolean assertions
in explicitly parented descendants and preserves original retained bytes and
reachable history. No existing prose or string value becomes a Boolean fact.

The demonstration and regressions cover the shared gate-and-either-route formula:
a satisfied gate/route; satisfied route beside UNKNOWN; mismatch beside UNKNOWN;
determinate gate mismatch beside unresolved routes; both routes mismatching;
conflict or unsupported route beside an independently satisfied route; invalid or
incomplete hidden branches; repeated leaf sensitivity correlation; split successes
across alternatives versus a separately declared full witness; and exact candidate
standalone/embedded parity. Operator truth tables, nesting, complete-group semantics,
strict versions/types, cumulative limits, ownership, read-only behavior, deterministic
replay and unchanged v1 identities are separately tested. Actual commands, outputs,
identities, counts, timings and final-head local/hosted evidence belong in the draft
PR description; no report-only commit is needed after hosted gates complete.

Each invocation validates the actual workspace once, then calculates from privately
owned packet/history/model snapshots. No repository-wide validation occurs inside
expression, candidate or hypothesis loops. No cache bypasses current integrity
checks. Evaluation creates no packet edits, derived assertion admission, review,
report store or automatic persistence. No network service or external AI call exists.

## Preservation and authority limits

The source allowlist is empty: zero real source units and zero projections; no TXT
is required or inspected. Retained CR/source evidence, manifests, anchors, identities,
all eight original PR #209 JSON files, packet roots/histories/reviews, existing
admission/authoring/analysis, historical bodies/appendices and PR #205/#206 performance
improvements remain intact. Catalog, acquisition, collection, runtime, publication,
workflows, timeouts and required gates are unchanged. Exact finite adapters extend
existing preservation controls; no new whole-repository freeze inventory exists.

Real coverage remains 100 CR units / 15 projections; casting 9/9, parent range 4/4,
single activated b–i import 8/8 with a excluded, and completion's preceding a–h range
8/8 remain unchanged. Semantic closure remains OPEN. All ten activation
responsibilities remain OPEN / EXECUTION_BLOCKED. Real gameplay execution remains
BLOCKED. No real GameplayRulesSnapshot, real execution profile, Card/Oracle parser,
gameplay engine or simulation is introduced.

A satisfied fictional expression establishes no real Card semantics, actual effect
consequence, complete applicable-effect inventory, feasible choice, compatibility,
casting permission, legality, payment or completion. Retained CR references remain
RETAINED_VERSIONED_RULE_CONTEXT_ONLY. Permission states remain:

```text
source_policy_clearance=not_granted
Private retention: NOT_ESTABLISHED
Redistribution: NOT_ESTABLISHED
Free service: NOT_ESTABLISHED
Commercial service: NOT_ESTABLISHED
AI export: NOT_ESTABLISHED
```

Historical acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
Stop at one draft PR for independent PM review. The owner retains final merge
approval. Do not merge or enable auto-merge.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
