# Offline missing-input sensitivity analysis

This owner-authorized bounded milestone answers: **If the missing assertions for
one selected fact were supplied as Boolean true or Boolean false, how would this
same named fictional condition change, and what would remain unresolved?**

A hypothesis is an assumed value used to examine a consequence. It is neither a
verified fact, corrected record, reviewer decision nor executed game event.
The actual packet, ordinary evaluation and hypothetical cases stay separate.
Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

GitHub confirms PR #212 merged with reviewed head
`241f98fd89ba2008a4cd51cbf8c732165b26d1b1`. The required canonical main/base is
`e114c70b01a0a28c77278efb9c2c058d1a73d660`, with tree
`270d207462862429a8570f867a68c1dafecea98f`. The initially clean older checkout was
reconciled to this exact base before implementation on
`codex/offline-missing-input-sensitivity`. No alternative base was substituted.

## Operator workflow

Use the existing offline authoring workflow to admit one exact retained A–E root,
or a valid explicitly parented fictional descendant. Author its exact separate
condition-model file according to the existing
[model contract](OFFLINE_FICTIONAL_CONDITIONAL_REASONING.md). This command accepts
packet/model inputs; imported result bytes are not an admission interface.

```sh
export PYTHONPATH=src
python -m proposed_spell_packets --workspace "$workspace" sensitivity "$packet_id" \
  --model "$workspace/model.json"
python -m proposed_spell_packets --workspace "$workspace" sensitivity "$packet_id" \
  --model "$workspace/model.json" --json
```

Readable explanations and canonical JSON go to stdout. Errors produce a nonzero
exit and REJECTED diagnostic with execution authority BLOCKED. Malformed inputs,
stale identities, edited roots, invalid actual history, retained-source or
context/alternative bindings remain hard validation errors; they are never
converted into hypothetical evidence gaps.

Each invocation owns its model, freshly validates the actual packet/history and
retained boundary once through corrected `Workspace.read()`, then calculates the
ordinary PR #212 baseline and all cases from that privately owned snapshot.
There is no repeated repository-wide validation for individual cases. The actual
baseline's complete canonical content and result identity are unchanged. Its
ordinary result is visible before the sensitivity section in readable output.

Analysis performs no write: no packet revision, record/model rewrite, review
observation, report store or automatic persistence. The operator may explicitly
redirect stdout, but the command does not persist reports. Later mutation of
caller objects, input files or decoded report views cannot change an already
produced report or leave a stale identity attached to changed content. No network,
service, UI or AI transport is involved.

## Exact sensitivity policy v1

Only the existing flat nonempty ALL_OF of Boolean assertion comparisons is
supported. The existing v1 packet/model acceptance, strict Boolean/scalar handling,
32-operand limit, complete eligible assertion groups and scope rules remain in
force. A fact uses the exact context, subject and opaque predicate key, with the
model binding its context version. The predicate and all authored prose are
uninterpreted. General assertions and matching-alternative assertions remain
eligible under named scope; foreign alternatives are excluded. General scope
admits general assertions only. An omitted eligible assertion is an error.

Walk operands in their existing model order. For every selected operand whose
complete eligible group contains at least one actual UNKNOWN claim, generate
exactly these two independent cases, in this order:

1. Assume every currently UNKNOWN claim in that group has Boolean true.
2. Assume every currently UNKNOWN claim in that group has Boolean false.

Each case begins from the same original validated baseline. No assumption carries
to another group or case. Every assumed claim is explicitly identified, in model
claim-reference order. With at most 32 operands, the maximum is 64 cases. These
uniform group assignments do not enumerate mixed assignments among multiple
UNKNOWN claims and do not establish every possible real-world outcome. No
cross-group combinations, exhaustive assignment search, solver, optimizer,
probability or ranking policy is added. No operators, nesting, natural-language
interpretation, automatic model construction, or packet/source admission is added.

Only actual UNKNOWN claims receive private effective Boolean values for these
calculations. The actual original condition, value, basis, attribution, assumptions
and limitations remain preserved. PRESENT, UNSUPPORTED, CONFLICTING and valid
non-Boolean inputs retain their actual meaning. The original model's expected
values, operator, references, scope and alternative remain fixed. Authored
reasoning, conclusions and limitations are never rewritten or adopted as computed
semantics. Transient effective values are calculation inputs only: they are not
admitted packets, recorded assertions or execution evidence.

The ordinary and hypothetical calculations share the same operand/aggregate
semantics. Every selected comparison and applicable finding is computed. An
existing PRESENT true assertion stays fixed when another assertion of the same
fact is UNKNOWN: assuming true can agree, while assuming false exposes opposing
Boolean assertions. The implementation cannot discard the original assertion to
make a hypothesis succeed. Declared conflict and unsupported inputs remain
unresolved under every hypothesis; assumed values cannot implement an unsupported
operation or decide which observer is correct.

| Effective selected inputs | Hypothetical aggregate |
|---|---|
| Any unresolved selected input remains | INDETERMINATE_UNDER_HYPOTHESIS |
| All comparisons evaluable and matching | SATISFIED_UNDER_HYPOTHESIS |
| All comparisons evaluable and at least one mismatch | NOT_SATISFIED_UNDER_HYPOTHESIS |

Known mismatches remain visible even when uncertainty keeps the aggregate
indeterminate. Explanations report both the affected operand's change and why
the aggregate changed or stayed the same. If both cases remain indeterminate,
the report identifies remaining barriers and still describes the affected
operand; it does not label the fact irrelevant. If neither tested case satisfies
the condition, it names remaining unresolved/unmet requirements without claiming
that no broader combination of future evidence could matter.

If no selected group contains UNKNOWN, sensitivity has status
`NOT_APPLICABLE_NO_SELECTED_UNKNOWN_CLAIMS`, zero cases and the unchanged actual
baseline. That status establishes neither complete knowledge, sufficient evidence
nor execution readiness. Unselected unknowns and packet-level limitations may
still exist; unsupported/conflicting selected inputs may still make the baseline
indeterminate.

## Derived report contract v1

The report version/domain is `fictional-condition-sensitivity-report-v1`; its
sensitivity policy is `fictional-condition-sensitivity-policy-v1`. Its authority
is exactly **HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY** and execution authority is
always BLOCKED. This is a distinct derived-report contract: hypothetical content
is never emitted as an ordinary factual `ConditionResult`.

`report_id` is `sha256:` plus the established
`sha256_identity({"domain": REPORT_VERSION, "content": body_without_report_id})`.
Canonical UTF-8 JSON uses sorted keys, compact separators, Unicode preserved and
one trailing LF. No path, timestamp, random value or mutable reference contributes
to identity. Identical explicit inputs and policy versions reproduce identical
canonical output after workspace relocation.

The report binds the actual packet/contract/schema/lineage/revision, exact model,
ordinary baseline identity, report/model/evaluator/sensitivity versions, named
condition, exact context/version and alternative. `baseline` contains the ordinary
result unchanged, including the full model, selected original assertions and
provenance, authored packet limitations/conclusion/reasoning/history, and retained
rule context. Original evidence appears once in this baseline; cases reference
the corresponding baseline operand rather than embedding the packet repeatedly.

`sensitivity` records applicability, finite case count and ordered `cases`. Each
case binds its sequence, selected operand, exact `unknown_claim_ids`, uniform
`assumed_value` and one explicit `{claim_id, value}` assumption per claim. Case
operands report original-evidence references, fixed expected values and claim
references, effective comparisons, findings, status and mismatch references.
Each case reports its unmistakable `hypothetical_result`, remaining unresolved
operand IDs, actual `known_mismatches`, all `computed_mismatches`, the affected
operand's before/after findings/status with an explanation, and an aggregate
explanation. The precise original assertion identifies subject, opaque predicate,
context/version and fictional attribution through its baseline evidence reference.

The report owns immutable canonical bytes and exposes fresh decoded copies. The
entry point accepts actual packet/model inputs only. A decoded output or wrapper
is not an external result-admission or trust mechanism.

## Reproducible CLI demonstration

Run the actual CLI authoring, ordinary evaluation and sensitivity commands in an
existing empty disposable workspace outside the repository:

```sh
export PYTHONPATH=src
sensitivity_workspace=$(mktemp -d)
python tools/proposed_spell_sensitivity_demo.py --workspace "$sensitivity_workspace"
packet_id=sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b
python -m proposed_spell_packets --workspace "$sensitivity_workspace" sensitivity \
  "$packet_id" --model "$sensitivity_workspace/models/A-original-b.json"
python -m proposed_spell_packets --workspace "$sensitivity_workspace" sensitivity \
  "$packet_id" --model "$sensitivity_workspace/models/A-original-b.json" --json
```

The script explicitly authors fixture records through `draft --base` followed by
`record --draft`. Every descendant is revision 2 with original retained B as its
parent; these siblings are fictional authored inputs, not simulated state
transitions. Existing review observations remain in the original historical
record and are omitted from changed-material descendants. The original beacon
remains UNKNOWN in every fixture; D also contains another UNKNOWN about that same
exact fact. The explicit premise is already PRESENT true in retained B. No prose
is converted to a Boolean premise.

The demonstration exercises both readable and JSON sensitivity output, compares
each embedded baseline with actual ordinary CLI output, checks expected outcomes,
and compares all workspace input/history/model bytes before and after analysis.
Actual final demonstration completed with exit 0. Selected stdout lines:

```text
Scenario A-original-b: actual baseline INDETERMINATE
Hypothesis lit-beacon=true claims=["beacon"] -> SATISFIED_UNDER_HYPOTHESIS
Remaining unresolved: []; actual known mismatches: []
Hypothesis lit-beacon=false claims=["beacon"] -> NOT_SATISFIED_UNDER_HYPOTHESIS
Remaining unresolved: []; actual known mismatches: []
Scenario B-second-unknown: actual baseline INDETERMINATE
Hypothesis lit-beacon=true claims=["beacon"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["other-input"]; actual known mismatches: []
Hypothesis lit-beacon=false claims=["beacon"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["other-input"]; actual known mismatches: []
Hypothesis other-input=true claims=["other-input"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["lit-beacon"]; actual known mismatches: []
Hypothesis other-input=false claims=["other-input"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["lit-beacon"]; actual known mismatches: []
Scenario C-known-mismatch: actual baseline INDETERMINATE
Hypothesis lit-beacon=true claims=["beacon"] -> NOT_SATISFIED_UNDER_HYPOTHESIS
Remaining unresolved: []; actual known mismatches: [{"claim_refs": ["other-required"], "operand_id": "other-required"}]
Hypothesis lit-beacon=false claims=["beacon"] -> NOT_SATISFIED_UNDER_HYPOTHESIS
Remaining unresolved: []; actual known mismatches: [{"claim_refs": ["other-required"], "operand_id": "other-required"}]
Scenario D-mixed-group: actual baseline INDETERMINATE
Hypothesis lit-beacon=true claims=["beacon", "beacon-second-unknown"] -> SATISFIED_UNDER_HYPOTHESIS
Remaining unresolved: []; actual known mismatches: []
Hypothesis lit-beacon=false claims=["beacon", "beacon-second-unknown"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["lit-beacon"]; actual known mismatches: []
Scenario E-unsupported-conflict: actual baseline INDETERMINATE
Hypothesis lit-beacon=true claims=["beacon"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["unsupported-input", "declared-dispute"]; actual known mismatches: []
Hypothesis lit-beacon=false claims=["beacon"] -> INDETERMINATE_UNDER_HYPOTHESIS
Remaining unresolved: ["unsupported-input", "declared-dispute"]; actual known mismatches: []
```

For B, the two cases for `other-input` start again from the actual UNKNOWN beacon;
there is no carryover from either beacon case. C retains the PRESENT false
`other-required` assertion against its fixed true expectation under both beacon
hypotheses. The false beacon case adds another unmet comparison. D retains
`beacon-known=true`: the true hypothesis agrees; the false hypothesis reports
`OPPOSING_BOOLEAN_ASSERTIONS (beacon, beacon-known, beacon-second-unknown)`.
Both UNKNOWN IDs are included in each uniform assignment. E retains the selected
unsupported input and both distinctly attributed declared-conflict assertions.
Its true case resolves the beacon operand while those other barriers remain;
its false case also retains the computed beacon mismatch. These observations
establish neither irrelevance nor impossibility of broader future evidence.

| Fixture | Exact admitted packet identity | Exact hypothetical report identity |
|---|---|---|
| A-original-b | `sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b` | `sha256:5c0810f82cb9724078d399e969c1b6c8d37dd9b01d16b3b311ddb61607331d9f` |
| B-second-unknown | `sha256:fc8df3f8de8821426d19e894c274776fbece60e194e9db8f3a3fa588177ab058` | `sha256:bfe93ef3fd36b9717bba4fe864ddc5b9c977565eadafafab86673d6aaa471d1c` |
| C-known-mismatch | `sha256:25004d7661af856351af01c2a7db58a7096d449bd3e36ce6cee522ad7b41a12e` | `sha256:37f2a145134592451a6c768af186059a3d66cbaf196998f401bd0725df16458d` |
| D-mixed-group | `sha256:d9e314d84bbbfebc72ba7a9d7fef2f9af9189b8e9ef80dffe6498be33c935134` | `sha256:6ef2817b0475925885c77c827948c50b8fc2f66c33b72a31bcc1ce4de8defd1b` |
| E-unsupported-conflict | `sha256:a92e9defb6ab6b1442d2ad3dcb9a4997e331a13b822c81c56daae630802802ca` | `sha256:34b24b87fd4454739c80d4db8a7d545a3e1451f435da9b2a403e64e4baebedc3` |

Original B's unchanged model is `sha256:4809a76b53441a81183cb6d7d7e44681cbba4ef05fc28fe45b9971d91e0cd689`; its unchanged ordinary
result remains `sha256:9c775f4945a4ed58fcd620d8231e96c6570ccc695dca4d5d1c951a37f915ad11`. The full final stdout JSON also
reports each fixture's model and ordinary result identities. All five embedded
baselines equal the actual ordinary CLI evaluations. Actual final flags are
`actual_beacon_condition=UNKNOWN`, `baseline_parity=true`,
`all_input_and_history_bytes_unchanged=true`, `sensitivity_read_only=true`,
`no_assertions_recorded_by_sensitivity=true`,
`authority=HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY` and
`execution_authority=BLOCKED`. No beacon fact is established or recorded by this
analysis. The final run has 12 independent cases across five separate inputs;
those inputs are never combined.

## Authority, preservation and remaining limits

This capability explains consequences of assumed missing inputs only. It does
not advise altering a record to obtain a desired result or collecting only
favorable evidence. Neither a hypothesis nor satisfaction establishes factual
truth, observer correctness, soundness of arbitrary authored prose, complete
dependencies/effects, absence of prohibitions, evidence sufficiency, overall
permission, proposal legality, choice compatibility, payment, casting completion,
a legal game action or state transition. Retained CR references are versioned
context only; actual assertions remain fictional inputs under the existing
admission contract. Real gameplay execution remains BLOCKED.

The eight PR #209 retained JSON files and identities, exact A–E root admission,
parented histories, PR #210 authoring/review provenance, PR #211 analysis/comparison
semantics and PR #212 ordinary model/evaluation behavior remain preserved.
Historical documentation bodies and authorization flags remain historical facts.
PR #205/#206 performance improvements, gameplay/product/collation behavior,
publication behavior, workflows, required checks and timeouts are unchanged.
Inventory adaptations are exact finite successors, with historical assertions
retained; no new retained-package hierarchy or whole-repository fixture exists.

Real-source allowlist is empty; new source units, projections, admissions and
source-body inspections are zero. Coverage remains 100 real CR units and 15
projections, casting 9/9, parent proposal range 4/4, activated b–i 8/8 with a
excluded, and completion's separate preceding a–h 8/8. These counts confer no
semantic closure. Historical acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
`source_policy_clearance=not_granted`; private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED. No TXT, Card or
Oracle ingestion, real-rule activation, gameplay-engine change, real snapshot,
simulation, or collection/acquisition integration is authorized.

Focused regressions precede stable complete local discovery. Actual final-head
push and PR merge-ref discovery/publication evidence belongs in the single draft
PR description, with observed counts, skips, statuses and timings. No new
source-dependent skip is introduced. Stop at that draft for independent PM review;
the owner retains final merge approval. No merge or auto-merge. Future milestone
authorized=false; future source projection authorized=false; future milestone
begun=false.
