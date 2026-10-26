# Offline requirement evaluation across named alternatives

This capability answers: **Among these explicitly named alternatives, which—if
any—meets every requirement in this shared, explicitly authored requirement set
under its supplied fictional assertions?** It extends `proposed_spell_packets`.
Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

The essential boundary is per alternative: requirement A met by one alternative
and requirement B met by another do not establish one alternative meeting both.
The evaluator neither forms combinations nor ranks or selects a preferred option.
A witness means only one declared alternative meeting this particular requirement
set under supplied fictional assertions. The list is finite and not established
exhaustive. Negative results say nothing about omitted or future alternatives.

## Exact base and operator workflow

GitHub PR #213 is merged with reviewed head
`efbdb2aa1b91b91a99691ee8fd90761b6b5e1930`. Fetched Git objects independently
confirm canonical main `def003e8591c5bb15a1fa31bd960713f80bb7841` and tree
`d2ec912a7cef936c2c8bb1580c9aa7626fbefc48`, identical to the reviewed head's
tree. The stale clean checkout at `e114c70b01a0a28c77278efb9c2c058d1a73d660`
was reconciled by creating `codex/offline-requirement-alternatives` from exact main.
No unrelated work was present and no alternative base was substituted.

Use an explicit disposable workspace outside the repository. Admit the unchanged
retained E root with the existing authoring CLI, then use `draft --base` and
`record --draft` for every fictional descendant. See the
[authoring boundary](OFFLINE_PROPOSED_SPELL_AUTHORING.md) and existing
[condition evaluator](OFFLINE_FICTIONAL_CONDITIONAL_REASONING.md).
Author and seal an explicit comparison definition using `seal_definition` in
`proposed_spell_packets.alternatives`; it supplies requirements and bindings,
never claims or inferred consequences.

```sh
export PYTHONPATH=src
python -m proposed_spell_packets --workspace "$workspace" evaluate-alternatives \
  "$packet_id" --requirements "$workspace/requirements.json"
python -m proposed_spell_packets --workspace "$workspace" evaluate-alternatives \
  "$packet_id" --requirements "$workspace/requirements.json" --json
```

Readable output and canonical JSON go to stdout. Contract/integrity errors emit a
nonzero exit with REJECTED and execution authority BLOCKED. No report store,
revision, observation, model rewrite or automatic persistence occurs. Imported
condition, sensitivity and comparison results are not proof inputs.

## Closed definition contract v1

All fields below are required, with unknown fields rejected at every level:

```python
from proposed_spell_packets.alternatives import seal_definition
value = seal_definition({
    "definition_version": "fictional-alternative-requirements-v1",
    "authority": "AUTHORED_FICTIONAL_REQUIREMENTS",
    "packet": {
        "packet_id": packet_id, "contract_id": contract_id,
        "schema_version": "proposed-spell-evidence-packet-v1",
        "lineage_id": "fictional:e:lineage", "revision": revision,
    },
    "scope": {"context_id": "ctx", "context_version": 1},
    "requirements": [
        {"requirement_id": "a", "subject_id": "fictional:e:object",
         "predicate": "Explicit opaque requirement A", "expected": True},
        {"requirement_id": "b", "subject_id": "fictional:e:object",
         "predicate": "Explicit opaque requirement B", "expected": True},
    ],
    "candidates": [
        {"alternative_id": "soften", "bindings": [
            {"requirement_id": "a", "claim_refs": ["soften-a"]},
            {"requirement_id": "b", "claim_refs": ["soften-b"]},
        ]},
        {"alternative_id": "brighten", "bindings": [
            {"requirement_id": "a", "claim_refs": ["brighten-a"]},
            {"requirement_id": "b", "claim_refs": ["brighten-b"]},
        ]},
    ],
})
```

Replace every binding with the exact admitted packet and actual claim keys.
`seal_definition` adds the own `definition_id` and returns an independent dict;
`AlternativesDefinition` validates an already sealed dict; `read_definition`
uses the established bounded no-symlink/no-hardlink local reader. JSON duplicate
keys, nonfinite values, malformed scalars and stale identities fail without
coercion. Positive integer versions reject Booleans and floats; expectations are
exact Booleans, rejecting integers, floats, strings and null.

Bounds are 1–16 distinct named candidates, 1–32 distinct shared requirements and
1–64 claim references per requirement/candidate binding. Each candidate must
bind every shared requirement exactly once. Duplicate IDs, fact keys, candidates,
references, empty groups, dangling references and unsupported versions fail.
Local IDs use `[a-z][a-z0-9-]{0,63}`; subject IDs use the packet fictional entity
namespace. Predicates are exact nonempty opaque strings. The definition owns a
maximum 1,024,000 canonical bytes, depth 8, 65,536 structural nodes, keys of at
most 128 characters and strings of at most 4,096 characters. Strict ownership
rejects tuples, custom objects, non-string keys and non-JSON scalar types before
canonicalization. Each composed candidate also retains the existing v1 model limits: 64,000 bytes
and 8,192 nodes at depth 8. Long references can therefore exhaust a candidate
byte budget before its count limits. These limits do not broaden packet admission.

The shared requirement stores the exact subject, predicate and Boolean once.
All candidate groups must match that same fact key in the one exact context and
version. Matching requirement labels cannot substitute a different fact or
expectation. Predicates, choice descriptions, Card/rule text, reasoning and
conclusions are uninterpreted. No prose-to-Boolean inference exists.

## Complete assertion groups and evaluation

For each requirement and candidate, explicitly bind **all** eligible claims for
its exact `(context_id, subject_id, predicate)`: general claims plus claims for
that exact alternative. Claims from another context, alternative, revision or
history record cannot transfer. General claims may appear in several candidate
groups. Every original value, condition, basis, attribution and limitation stays
in the v1 candidate result. No dissent can be omitted or overridden.

An explicitly represented UNKNOWN claim is valid incomplete evidence and yields
an unresolved requirement. A missing eligible group is an insufficient binding
error before any semantic comparison report; the underlying packet is not
thereby invalid. It never becomes false, a vacuous match or a fabricated UNKNOWN
claim. When intended, the operator must explicitly author an attributed UNKNOWN
through the parented authoring workflow.

The existing v1 comparison and conservative ALL_OF policy apply independently:

| Candidate evidence | Candidate result |
|---|---|
| Any selected missing, unsupported or conflicting input | INDETERMINATE |
| All requirements match | SATISFIED_UNDER_ASSERTIONS |
| Otherwise, at least one mismatch | NOT_SATISFIED_UNDER_ASSERTIONS |

Expected false compares with explicitly supplied false, never unknown. Independent
known mismatches remain visible even when another requirement is unresolved.
General versus matching-alternative disagreement remains conflict. Declared
CONFLICTING, UNSUPPORTED and valid non-Boolean inputs retain v1 treatment.
Every candidate and every finding is computed, including when a witness exists.

| Aggregate | Meaning |
|---|---|
| LISTED_WITNESS_FOUND_UNDER_ASSERTIONS | At least one listed candidate satisfies every requirement; return all matching IDs in authored order, without ranking. |
| INDETERMINATE_NO_LISTED_WITNESS_ESTABLISHED | No satisfied candidate and at least one indeterminate candidate. |
| NO_LISTED_WITNESS_UNDER_ASSERTIONS | Every listed candidate is determinately not satisfied. |

## Immutable derived report and authority

The definition identity uses domain `fictional-alternative-requirements-v1` and
own field `definition_id`. Identity follows existing canonical serialization and
`v.identity`: `sha256_identity({"domain": VERSION, "content": body_without_own_id})`,
prefixed `sha256:`. The derived report domain/version is
`fictional-alternative-requirements-report-v1`, policy
`fictional-alternative-requirements-policy-v1`, own field `report_id`, and authority
`LISTED_FICTIONAL_ALTERNATIVES_UNDER_ASSERTIONS_ONLY`. It is a computed output, neither admitted
evidence nor a trusted imported result. Execution authority is always BLOCKED.

The report fields are `report_id`, `report_version`, `comparison_policy_version`,
`definition_version`, `definition_id`, `definition`, `authority`,
`execution_authority`, `condition_model_version`, `condition_result_version`,
`evaluator_policy_version`, `packet`, `scope`, `context`, `requirements`,
`candidates`, `computed_result`, `satisfying_alternative_ids`,
`aggregate_explanation`, `limitations` and `retained_rule_context_authority`.
Each candidate has `alternative_id`, `scope`, `condition_model`, `model_id`,
`condition_result`, `result_id`, `computed_result`, `requirement_outcomes`,
`selected_input_findings` and `known_mismatches`. Requirement outcomes preserve
the requirement fields plus `status`, `claim_refs` and
`known_mismatch_claim_refs`; mismatch entries identify `requirement_id` and
`claim_refs`. The full v1 result contract is unchanged. The report constructor
rejects imported content; only evaluation produces this output type.

The report binds the complete definition, exact packet/contract/schema/lineage/
revision and context/version, candidate scopes, relevant model/evaluator/result
versions and every calculation. Each candidate retains its actual composed v1
model, actual v1 result identity and full result, including assertion references,
provenance, findings, known mismatches, authored packet context and retained rule
context. The candidate result is byte-identical to standalone v1 evaluation of
that exact model. No old identity is attached to changed content. Readable output
shows shared expectations and a row per candidate with requirement outcomes,
all findings and mismatches, all witnesses, aggregate explanation, separately
labeled authored conclusion/limitations and execution authority.

Each invocation freshly calls actual `Workspace.read()` once, validating current
packet bytes, exact retained bindings, permitted root and reachable history.
The packet/history and definition are privately owned before calculation. No
repository-wide validation occurs in candidate or requirement loops, and no cache
bypasses filesystem integrity. Models are mechanically composed from explicit
bindings; all v1 semantics and identities remain unchanged. Immutable canonical
bytes and fresh dictionary views prevent caller, input-file or decoded-output
mutation from altering an existing report. Identical inputs reproduce identical
bytes after relocation; no clock, random value or workspace path enters identity.

## Demonstration and regressions

```sh
export PYTHONPATH=src
alternatives_workspace=$(mktemp -d)
python tools/proposed_spell_alternatives_demo.py --workspace "$alternatives_workspace"
```

The demonstration starts from exact retained E and preserves its root/history.
New Boolean assertions are explicitly authored fictional statements; original E
prose and string assertions are preserved without interpreting consequences.
Actual commands, outputs, identities and validation evidence are recorded below
and in the draft PR description.

Actual demonstration exit 0, using `/tmp/mtg-alternatives-demo.lVncYM`:

```sh
python -m proposed_spell_packets --workspace "$workspace" draft --example packet-e-compatibility.json --output "$workspace/drafts/retained-e.json"
python -m proposed_spell_packets --workspace "$workspace" record --draft "$workspace/drafts/retained-e.json"
python -m proposed_spell_packets --workspace "$workspace" draft --base "$root_id" --output "$workspace/drafts/explicit-assertions.json"
# The demo explicitly edits this draft with author_assertions; no interpretation.
python -m proposed_spell_packets --workspace "$workspace" record --draft "$workspace/drafts/explicit-assertions.json"
packet_id=sha256:a4b6e48c3ec35744ea8f2257f4bbcdfa735ad5c676796efc574fbbf854683a71
python -m proposed_spell_packets --workspace "$workspace" evaluate-alternatives "$packet_id" --requirements "$workspace/requirements/A-separate.json"
python -m proposed_spell_packets --workspace "$workspace" evaluate-alternatives "$packet_id" --requirements "$workspace/requirements/A-separate.json" --json
```

Retained root: `sha256:67e162ef5700746bf161850a4e11b2470c93ef4db96d3b96a6010f2e60ff868e`.
The child is revision 2 and explicitly parents that root. All added assertions
are attributed to `fictional:e:requirements-demo-author`. New A/B values are
soften=(true,false), brighten=(false,true), steady=(true,true), and
missing=(UNKNOWN,false), with predicates `Opaque requirement A/B`. Both are
expected true. No original E assertion is converted. Separately authored integrity
assertions supply D's general true, steady true, disputed false, unsupported null,
text-only string "true", and two distinct opposing declared-conflict statements.
D selects `Opaque integrity requirement` plus B; it is a separately sealed question.

| Scenario | Candidate requirement statuses | Aggregate / witnesses |
|---|---|---|
| A separate favorable alternatives | soften MATCH/MISMATCH; brighten MISMATCH/MATCH | NO_LISTED_WITNESS_UNDER_ASSERTIONS / [] |
| B separately authored all-requirement candidate | above two plus steady MATCH/MATCH | LISTED_WITNESS_FOUND_UNDER_ASSERTIONS / [steady] |
| C explicit missing evidence | steady MATCH/MATCH; missing UNRESOLVED/MISMATCH | LISTED_WITNESS_FOUND_UNDER_ASSERTIONS / [steady] |
| D conflict and unsupported input | steady MATCH/MATCH; disputed, unsupported, text-only, declared each UNRESOLVED/MATCH | LISTED_WITNESS_FOUND_UNDER_ASSERTIONS / [steady] |
| E complete negative (same inputs as A) | soften MATCH/MISMATCH; brighten MISMATCH/MATCH | NO_LISTED_WITNESS_UNDER_ASSERTIONS / [] |

A/E prove there is no cross-alternative union. C retains `MISSING_ASSERTION` and
the independent known mismatch `missing-b`. D retains
`OPPOSING_BOOLEAN_ASSERTIONS` for general true versus disputed false,
`UNSUPPORTED_ASSERTION`, `UNSUPPORTED_BOOLEAN_INPUT`, and `DECLARED_CONFLICT`
(with opposing Booleans), despite steady's success. Actual v1 model/result IDs
repeat unchanged when a candidate's exact model is reused in another definition.

| Scenario | Definition identity | Report identity |
|---|---|---|
| A-separate | `sha256:c0f662fbfd2056406d314bc91192d6c5a79abca7c15c118557ac72d05ae6f383` | `sha256:876eed912bc5c8271e200ea77374955ef16428e1f9c1de3b9caacfdf6205c92d` |
| B-witness | `sha256:1afa91313692f077dea2cd4bb262f7ab12ea8e5cd7181d6a23104c78bf5bdcb3` | `sha256:09d9534e9d8e7ce4eb759da99483bc8657eb0834e912e42e9d87edaa67fd2576` |
| C-unknown | `sha256:de9ac7912ba0283ba9c79c6120e3e2bd4bc4873c677315000192633b1d977f4c` | `sha256:7cb80e8075b5dae1108286969578fb353e22e63e843389b6c18cd55bea86a43b` |
| D-findings | `sha256:dc35f47699a8aa97b8103639b3e89c7ed7ec96986cb918f18abf2df6145df7b4` | `sha256:0098b5857a49d863d12cffae04bc4c65deaf4cbe99f4517bb5cebcd7c9170391` |
| E-negative | `sha256:c0f662fbfd2056406d314bc91192d6c5a79abca7c15c118557ac72d05ae6f383` | `sha256:876eed912bc5c8271e200ea77374955ef16428e1f9c1de3b9caacfdf6205c92d` |

Actual selected candidate identities for A/B/C:

| Candidate | Model identity | Ordinary result identity |
|---|---|---|
| soften | `sha256:009bfa55a0044db21e5eeed8af37d568cf5e3814078b3eafbb2d5e88c82a24c7` | `sha256:c2b3393cd717c9182dd6662383f7b223f0d8ec9f64e5739a79a075010d03a0de` |
| brighten | `sha256:ab2be2e7d02b45b48fa865812559128142c29cc2f0d6a932ddaa941202882f5e` | `sha256:919039c948e380dc4e31479dd5b95dcbf004e0d4a76824cffff8ee3ca6a2903d` |
| steady | `sha256:f0460c171df31565b5673a48def98328a78c4896cd678c0d5dc150d3ed4cf05a` | `sha256:e6f316fad016f94e4b9c778640a883befca157beecfc01d35e50cf10f5465da9` |
| missing | `sha256:37c686fde47ca4df776bf9813d64f667d4267cac9f0a301aa201599f69094c93` | `sha256:a668c5902ea99c31ab92aa9a3ba42dfb2101469c7c731a917f4106c547912946` |

The command against retained E with these absent required groups exits 1:

```text
REJECTED: ALTERNATIVES_INSUFFICIENT_BINDING_MISSING_REQUIRED_GROUP
execution_authority=BLOCKED
```

It creates no synthetic evidence. Actual final flags are
`all_input_and_history_bytes_unchanged=true`, `retained_e_prose_preserved=true`,
`missing_group_rejected_without_synthetic_evidence=true`, execution BLOCKED.
The evaluation itself performs no file writes; only explicit authoring and
operator-managed definition-file writes precede the read-only comparison phase.

The data-driven regressions cover separate favorable candidates, all-requirement
witnesses, UNKNOWN evidence with and without a witness, complete negatives,
conflict/unsupported/non-Boolean inputs, expected false, binding and scalar errors,
missing groups, omitted dissent, mixed scopes, stale identities, actual root/
history/retained tampering, immutable ownership, read-only behavior, standalone
v1 parity and maximum structural bounds. Original condition and PR #213
sensitivity identities remain unchanged.

## Preservation and real gameplay boundary

`conditions.py`, `sensitivity.py`, `authoring.py`, `validation.py` and `analysis.py`
remain unchanged. All retained evidence, manifests, identities, anchors, eight
original PR #209 JSON records, authored histories/reviews, historical document
bodies, catalog/acquisition/collection/runtime/publication behavior, workflows,
timeouts and required gates are preserved. Only exact finite successor adapters
extend existing preservation checks; no new freeze inventory or framework.
PR #205/#206 performance improvements remain intact.

The real source allowlist is empty. No TXT or new source body, official example,
Oracle/Card interpretation or external AI service/export is part of this work.
Coverage remains 100 real CR source units / 15 projections; casting 9/9; parent
range 4/4; single activated b–i import 8/8 with a excluded; completion's preceding
a–h range 8/8. Counts establish no semantic completeness. Semantic closure remains
OPEN, all ten activation responsibilities OPEN / EXECUTION_BLOCKED, and real
gameplay execution BLOCKED. Retained CR references remain
RETAINED_VERSIONED_RULE_CONTEXT_ONLY. No real GameplayRulesSnapshot, execution
profile, compatibility/target/choice solver, stack/priority/payment engine or
simulation is introduced.

A positive fictional result establishes no actual effect consequences, feasible
or co-selectable choice, compatibility, absence of prohibitions, permission to
cast, proposal legality, payment, completion or execution. Source policy remains
`source_policy_clearance=not_granted`; private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED. Historical
acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

Stop at one draft PR for independent PM review; owner retains final merge approval.
No merge or auto-merge. Future milestone authorized: false. Future source projection
authorized: false. Future milestone begun: false.
