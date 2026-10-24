# Offline fictional conditional-reasoning pilot

This one owner-authorized milestone computes one named condition under explicit
fictional assertions. It extends the existing offline proposed-spell tooling; it
neither invokes nor changes the fictional gameplay engine. Architecture v13 and
Decision 017 remain unchanged. Stop at one draft PR for independent PM review;
the owner retains final merge approval. No later milestone is authorized or begun.

GitHub confirms PR #211 merged, with reviewed head
`fd181b6e9a6e09d3738a8d33f0cefae69dc10e34`. Required canonical main/base is
`514386f418b05643b839a246089c0080dfc2d4e3`, tree
`fefe0285f28491402113e52d7835a1b093e1e032`. GitHub Git data and fetched local
objects agree. The initially clean checkout at PR #210's main was reconciled to
this exact base before implementation on
`codex/offline-fictional-conditional-reasoning`.

## Operator workflow

Use existing dependencies and an explicit local workspace outside the repository.
First record an unchanged retained A–E example through the existing authoring
workflow. All edits require `draft --base EXACT_PACKET_ID` and `record --draft`;
see the [corrected authoring boundary](OFFLINE_PROPOSED_SPELL_AUTHORING.md#pr-210-correction-roots-review-provenance-and-draft-bounds).
Only those exact retained roots and valid parented descendants are admitted.
A manually constructed packet body cannot bypass root/history admission.

Author a separate model JSON file; bind the actual emitted packet identity,
contract, schema, lineage, revision and exact context/version. Explicitly select
one alternative or null for general scope. Supply the complete claim reference
group for each fact, and the expected Boolean. The model defines the test; it
supplies no missing assertion. Seal its content identity with the helper below,
then invoke the read-only evaluator:

```sh
export PYTHONPATH=src
python -m proposed_spell_packets --workspace "$workspace" evaluate "$packet_id" \
  --model "$workspace/model.json"
python -m proposed_spell_packets --workspace "$workspace" evaluate "$packet_id" \
  --model "$workspace/model.json" --json
```

Readable output and canonical JSON go to stdout. Contract errors produce nonzero
exit status and a REJECTED diagnostic with execution authority BLOCKED. Evaluation
creates no report store, files, review observations or packet revisions. Every
invocation freshly uses corrected `Workspace.read()` once to validate actual
packet bytes, actual retained contract/rule bindings, exact roots and reachable
history. No validation cache bypasses current integrity checks. Repository-wide
validation is outside operand loops. Model files use the existing safe local-file
reader; readable JSON formatting is allowed, duplicate keys and nonfinite values
are rejected. Models and results own immutable canonical bytes; dictionary views
are independent copies. Later mutation of input files, caller data or decoded
output cannot change an already produced report.

## Closed model contract v1

Every field below is required; unknown fields at any level fail. No automatic
model construction from predicate, explanation, Card text or conclusion exists.
The explicit example definition used by the demonstration has this body before
adding its own identity (replace binding placeholders with exact actual values):

```python
from proposed_spell_packets.conditions import seal_model
model = seal_model({
    "model_version": "fictional-condition-model-v1",
    "authority": "AUTHORED_FICTIONAL_CONDITION",
    "condition_id": "premise-and-beacon",
    "condition_name": "Fictional premise and lit beacon",
    "packet": {
        "packet_id": packet_id, "contract_id": contract_id,
        "schema_version": "proposed-spell-evidence-packet-v1",
        "lineage_id": "fictional:b:lineage", "revision": revision,
    },
    "scope": {"context_id": "ctx", "context_version": 1, "alternative_id": None},
    "operator": "ALL_OF",
    "operands": [
        {"operand_id": "premise", "claim_refs": ["premise"], "expected": True},
        {"operand_id": "beacon", "claim_refs": ["beacon"], "expected": True},
    ],
})
```

Models are bounded to 64,000 bytes, 32 operands and 64 references per leaf.
Local tokens match `[a-z][a-z0-9-]{0,63}`; condition names have 1–256 characters.
Revision/context versions are exact integers from 1 through 2,147,483,647.
A pre-canonicalization structural budget rejects depth over 8, over 8,192 nodes,
keys over 128 characters, strings over 4,096 characters and non-JSON container
or scalar types. These model bounds do not broaden packet v1 acceptance.

`seal_model` is an explicit authoring convenience: it returns a new sealed model,
validating the closed shape; it never infers requirements or facts. Input JSON
must supply and validate its `model_id`. A changed revision requires a separately
bound model with a new identity. Duplicated binding fields must equal the selected
validated packet; no silent rebinding, version substitution or migration occurs.

The only leaf operation compares bound Boolean assertions with an explicit exact
Boolean expectation, true **or false**. The sole combination is a nonempty flat
ALL_OF of at most 32 leaves. No nesting, ANY_OF, general NOT, implication,
quantifiers, arithmetic, characteristic/effect interpretation, DSL, registry or
plugin exists. Strict scalar types reject 0, 1, floats and string Boolean
substitutions for expectations. Claim values remain governed by unchanged v1:
only valid PRESENT Booleans are evaluable; valid strings remain unsupported
Boolean inputs. Integers/floats in packets still fail v1 validation.

## Complete assertion groups and conservative evidence policy

A fact is identified only by exact `(context_id, subject_id, predicate)` fields.
The context version is separately bound through the selected packet context.
Predicate strings remain opaque. General scope admits only general claims;
a named alternative admits general claims and that exact alternative's claims.
Foreign-alternative claims cannot be combined. Every selected leaf must explicitly
bind the complete eligible group, so an operator cannot omit dissent to obtain a
favorable answer. Mixed fact keys, duplicate references/operand IDs/groups,
dangling references and incompatible contexts/versions/scopes fail as contract
errors. Array order is preserved and deterministic; it selects no assertion winner.

Each original claim retains scope, value, condition, basis and attribution. PRESENT
means supplied content, not verified truth. UNKNOWN yields a missing finding;
UNSUPPORTED remains unsupported; CONFLICTING remains conflicting even when a
narrower eligible selection appears consistent. Opposing eligible Boolean values
are conflicting, including general versus matching-alternative disagreement.
There is no inferred override or preference by order, recency, confidence or
reviewer. Every selected assertion is evaluated and every applicable finding is
retained. Independently evaluable Boolean mismatches remain visible alongside
unresolved inputs.

| Selected operands | Computed result |
|---|---|
| Any missing, unsupported or conflicting input | INDETERMINATE |
| All evaluable, every expectation matched | SATISFIED_UNDER_ASSERTIONS |
| All evaluable, one or more expectations mismatched | NOT_SATISFIED_UNDER_ASSERTIONS |

This is the pilot's conservative evidence policy, not a general Boolean or
multivalued logic system. Expected false tests an explicitly supplied false;
it never fills an unknown with false. A malformed model, unsupported operator,
invalid packet/model identity or integrity failure is an error, not indeterminate
evidence.

## Result contract and authority

Model, evaluator policy and result versions are respectively
`fictional-condition-model-v1`, `fictional-condition-evaluator-policy-v1` and
`fictional-condition-result-v1`. Model/result identity reuses established canonical
serialization and `v.identity`: `sha256_identity({"domain": VERSION, "content":
body_without_own_identity})`, prefixed `sha256:`. Each artifact has its own domain;
no paths, clock, random values or mutable references enter result identity.
Identical explicit inputs and versions reproduce identical canonical bytes and
identities. The result binds the exact packet and model plus policy/result
versions, explicit condition/scope, every selected claim and original value,
assumption/assertion provenance, each expectation and Boolean match/mismatch,
all selected findings and a deterministic explanation trace.

The packet's authored conclusion is separately labeled and copied unchanged.
Selected-input limitations remain visible alongside all packet-level limitations
and unselected authored findings. Unselected content is context, never an inferred
model premise. Existing reviews do not approve the condition definition and are
not rewritten. Retained references keep authority
`RETAINED_VERSIONED_RULE_CONTEXT_ONLY`. Execution authority is always BLOCKED.

A satisfied condition or empty selected-finding list establishes none of: truth
of fictional assertions; soundness of prose; complete dependencies/effects;
absence of prohibitions; evidence sufficiency; overall casting permission;
proposal legality; joint choice compatibility; payment; completion; gameplay
execution. No LEGAL, CASTABLE or READY_TO_EXECUTE result state exists. This checks
only assertions represented in the selected packet under exact keys, not a
complete fact/effect inventory or semantic equivalence of differently worded
predicates. The original packet contract, authored classifications, retained CR
context and PR #211 dependency-analysis semantics are unchanged.

## Reproducible demonstration and regression evidence

Run the actual authoring and evaluation entry points in a fresh disposable
workspace:

```sh
export PYTHONPATH=src
condition_workspace=$(mktemp -d)
python tools/proposed_spell_conditions_demo.py --workspace "$condition_workspace"
```

The demonstration's condition is explicitly authored as `premise && beacon`.
Retained B already supplies premise=true as an AUTHORED_FICTIONAL_ASSUMPTION;
it is used as supplied without interpreting its predicate. The original beacon
is UNKNOWN. Properly parented descendants explicitly supply true and false with
fictional attribution. These are authored alternatives/corrections, not game-state
transitions. The script prints actual IDs, commands and results, and verifies
that evaluation leaves packet/history bytes unchanged.

Actual demonstration outputs (selected stdout lines):

```text
Computed condition result: INDETERMINATE
Operand explicit-premise: expected true -> MATCH
Operand lit-beacon: expected true -> UNRESOLVED
Computed condition result: SATISFIED_UNDER_ASSERTIONS
Operand explicit-premise: expected true -> MATCH
Operand lit-beacon: expected true -> MATCH
Computed condition result: NOT_SATISFIED_UNDER_ASSERTIONS
Operand explicit-premise: expected true -> MATCH
Operand lit-beacon: expected true -> MISMATCH
```

| Beacon input | Exact packet identity | Exact computed result identity |
|---|---|---|
| Missing | `sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b` | `sha256:9c775f4945a4ed58fcd620d8231e96c6570ccc695dca4d5d1c951a37f915ad11` |
| True | `sha256:9aeeb8b24f1c7d88a832acb9c0e85232541ec7cb8286ee2c5c0ac0f47eef4a4b` | `sha256:05932b1f8bebd7ab2b8363815374dd8ff4f3e779c6ac9132196e81199128d99b` |
| False | `sha256:a030fba396262eb47d307654219fe64de030be498b2f2c0b8ab2c00f029b4cd2` | `sha256:8dc041459c0715995d3cd98bf810a733b2843f8e92bf7552a07edc0e6b65233c` |

Both revision-2 descendants explicitly name retained B as their parent; they are
alternative authored assertions, not an inferred sequence of state changes.
All three packet authored conclusions remain INDETERMINATE_MISSING, clearly
separate from the computed condition. Final demo output reports
`all_input_and_history_bytes_unchanged=true`, `evaluation_read_only=true` and
`execution_authority=BLOCKED`.

Focused tests exercise multi-operand conjunction, expected false, all barriers
and mismatch together, declared and discovered conflicts, general/alternative
scope, omitted dissent, cross-branch rejection, strict shape/types/identities,
tampered ancestors/retained evidence, ownership, deterministic bytes, fresh reads
and read-only behavior. Exact commands, actual output and final validation totals
are recorded in the draft PR description. No source-dependent skip is added.

## Preservation and delivery boundary

The historical document prefixes, eight retained PR #209 JSON files, packet
history/reviews, retained CR projections/anchors/packages/identities, PR #210
validation/authoring and PR #211 analysis remain preserved. `authoring.py`,
`validation.py` and `analysis.py` are byte-identical. Existing finite preservation
checks are adapted only for the named source addition, narrow CLI successor and
eight exact documentation suffixes; no new repository fixture/manifest framework.
No publication/workflow/timeout/check change occurs. Focused tests precede stable
complete local discovery; final-head push and PR workflows provide the mandatory
real publication runs, nested discovery, 654-card writer, disposable bare remote
and matching published/readback heads. Evidence belongs in the PR description so
no report-only commit invalidates checks.

Real source allowlist remains empty; new source units/projections/anchors/admissions
are all zero. Coverage stays 100 real CR units / 15 projections, casting 9/9,
parent range 4/4, activated b–i 8/8 with a excluded, and completion's preceding
a–h 8/8. These counts establish no semantic or execution closure. No fresh CR/TXT
inspection, Oracle/Card ingestion, gameplay-engine change, real rule evaluation,
state transition, simulation, execution-profile activation, service, UI, network
or AI integration is introduced.

Historical acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
`source_policy_clearance=not_granted`. Private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED. Real gameplay
execution stays BLOCKED. No merge or auto-merge; future milestone authorized:
false; future source projection authorized: false; future milestone begun: false.
