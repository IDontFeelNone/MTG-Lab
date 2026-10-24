# Proposed-spell evidence-gap analysis pilot

This owner-authorized, read-only pilot traces **declared** evidence dependencies
in validated fictional proposed-spell packets. It answers what the author cited,
which declared conditions and limitations affect those relationships, and what
changed between two explicitly selected related revisions. Architecture v13
remains ACTIVE APPROVED; Decision 017 remains ACCEPTED.

PR #210 is merged at the required canonical base
`99813ea7b98c1fc1a2deda31479464ef83a47c31`, tree
`12aea934a43be4a13cb27fc33129dabf4238b5d8`. That tree equals corrected reviewed head
`97fa5889003fe98ca3db9bb8d2c52b77a0cb13c4`. The original
[v1 packet design](GAMEPLAY_RULES_PROPOSED_SPELL_EVIDENCE_PACKET_DESIGN.md) and
[corrected root workflow](OFFLINE_PROPOSED_SPELL_AUTHORING.md#pr-210-correction-roots-review-provenance-and-draft-bounds)
remain authoritative for input validation. Their contract/schema are unchanged;
`authoring.py` and `validation.py` retain their exact original bytes.

## Commands and demonstration

Run from the repository with existing dependencies. Each command selects an
existing local pilot workspace outside the repository and exact recorded identity.
There is no implicit latest revision, path-based selection, report store or writer.

```sh
export PYTHONPATH=src
demo_workspace=$(mktemp -d)
python tools/proposed_spell_packet_demo.py --workspace "$demo_workspace"
original_id=sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b
correction_id=sha256:5c6bd95825dadef42beb389ba67b18111593de26311ba88eaed94ff1cf118345
review_id=sha256:06e437c42ce77e5f10a8aa9ead9fb8a9b2c9c6929b9481c64c4d66563b98cf13
python -m proposed_spell_packets --workspace "$demo_workspace" analyze "$original_id"
python -m proposed_spell_packets --workspace "$demo_workspace" analyze "$original_id" --json
python -m proposed_spell_packets --workspace "$demo_workspace" compare "$original_id" "$correction_id"
python -m proposed_spell_packets --workspace "$demo_workspace" compare "$correction_id" "$review_id" --json
```

The existing demonstration records all five unchanged retained examples and the
explicitly authored B correction/review chain. Its output supplies every identity;
use any emitted A–E identity with `analyze`. Analysis and comparison freshly call
`Workspace.read()` for actual canonical packet bytes, retained bindings, exact
permitted retained roots and required reachable ancestors. Bad bytes, invalid
bindings, missing ancestors, unrelated lineages and incompatible contracts are
errors, never UNKNOWN analysis results. Commands emit stdout only and do not
create, repair, reseal, revise, publish or modify packet/history files.

For one compact acceptance demonstration, including all A–E reports, both B
comparisons and an explicitly authored valid transitive descendant, use a fresh
empty workspace:

```sh
analysis_workspace=$(mktemp -d)
PYTHONPATH=src python tools/proposed_spell_analysis_demo.py --workspace "$analysis_workspace"
```

This script reuses the existing authoring demonstration. Its extra packet is
explicit authored input recorded through the separate authoring commands; analysis
remains read-only. The final output checks original packet/history bytes unchanged.

Comparison is directional: the first exact identity must be an ancestor of the
second in its validated linear history, or identical to it. Revision numbers,
filenames, timestamps and directory order cannot establish this relationship.

## Derived report contract v1

The derived report is separate from the v1 packet schema and is **not another
authoritative evidence packet**. The report is a deterministic JSON object; its
readable rendering expresses the same bounded authority.

| Field | Meaning |
| --- | --- |
| `analysis_version` | `proposed-spell-dependency-report-v1`; versioned traversal and reporting policy. |
| `report_id` | Domain-separated SHA-256 content identity described below. |
| `report_kind` | `ANALYSIS` or `COMPARISON`. |
| `authority` | Always `DECLARED_DEPENDENCIES_ONLY`. |
| `execution_authority` | Always `BLOCKED`. |
| `inputs` | Ordered exact packet bindings: `packet_id`, `contract_id`, `schema_version`, `lineage_id`, `revision`; one input for analysis, ancestor then descendant for comparison. |
| `analyses` | One dependency view per input, in the same order. |

Each dependency view contains `input`, `authored_question`, the clearly labeled
`authored_conclusion`, `retained_rule_context`, `contexts`, `branches`, typed `nodes` and `edges`, `condition_findings`,
`declared_limitations`, separately identified `uncited_packet_content`, and
`review_observations` with historical origins. Branch records bind exact
`context_id`, `context_version` and nullable `alternative_id`, plus direct and
transitive step references, claim references, explicit assumption references and
contextual choice references. Nodes use typed IDs such as `step:condition` and
`claim:beacon`; they retain their authored fields, including attribution, values,
conditions, limitation text and actual retained rule/version evidence. Edges bind
`source`, `target`, `relationship` and authored reference `position`.

Condition findings and declared limitations remain separate collections. Each
binds its affected branch(es) and bounded witness paths to the authored conclusion.
For limitations, `conclusion_declared_branches` records the context-matching
conclusion citation scope separately from target-scoped `branches`; a direct
`conclusion_witness_path` remains even when no selected branch matches the targets.
The typed edge listing supplies reproducible relationships without enumerating
exponentially many equivalent paths. Comparison additionally reports observed
material changes, structural effects on dependent steps/branches, and reviewer
observation changes/origins. Its `changes` object separates `claims`, `reasoning`,
`choices`, `limitations`, `contexts`, `rule_evidence`, `assumptions`,
`authored_conclusion`, `other_authored_fields`, `collection_order`,
`condition_findings`, `declared_limitations` and
`review_observations`. Material records retain before/after values, changed fields
and structural impact for each endpoint. Impact separates logical dependent steps
and branches from typed `reference_associations` and `associated_branches`;
context/rule/choice/limitation associations do not become additional premises.
`collection_order` retains observed record-order changes. Top-level `reviewed_material_changed`,
`review_only_change` and `no_change` distinguish review additions from authored
material changes. It retains each endpoint analysis so conditions,
limitations, authored conclusions and exact rule/version bindings remain inspectable.

Identity uses the established packet convention:

```text
report_id = "sha256:" + sha256_identity({
  "domain": "proposed-spell-dependency-report-v1",
  "content": report with only report_id omitted
})
```

Serialization reuses the established canonical JSON implementation, including its
trailing newline. Object keys are canonical; collection traversal and output
ordering are deterministic. Authored array order, including reasoning dependency
positions and historical observation order, is preserved where meaningful.
No ambient time, random value or local path participates. Identical explicit
inputs/version produce identical bytes and identity after local relocation;
changing either input identity changes the bound content/identity. The immutable
report owns canonical bytes; `.to_dict()` returns a new copy. Later mutation of
caller-held input objects or decoded reports cannot change a produced result.

## Traversal and interpretation

Traversal starts only from the authored conclusion's `step_refs`,
`assumption_refs` and `limitation_refs`. It follows explicit reasoning dependencies
including transitive `depends_on_steps`, claim references and the distinct typed
contextual, choice, limitation and retained-rule relationships. Contextual links
are displayed as context; they do not silently become logical premises. General
inputs can support an alternative under the validated contract, while an
alternative-specific premise stays within its alternative. No joint proposal is
constructed from separate branches.

`UNKNOWN`, `UNSUPPORTED` and `CONFLICTING` claim/step conditions are reported
simultaneously; declared `UNKNOWN`, `UNSUPPORTED`, `CONFLICT`,
`COMPATIBILITY_GAP` and `SCOPE` limitations keep their actual authored kind.
A conclusion-level limitation remains visible without a matching claim condition.
All relevant attributed conflict values are preserved without a winner. An
uncited unknown claim can appear only as uncited packet content, not as a direct
conclusion dependency. No invented barrier precedence policy selects one finding.

`PRESENT` means content is supplied. It establishes neither truth, sufficient
evidence, successful computation, complete effect coverage nor permission.
Explicit assumptions remain assumptions; attributed assertions remain attributed
assertions. Retained rule bindings retain authority
`RETAINED_VERSIONED_RULE_CONTEXT_ONLY`; they explain versioned context and do not
verify fictional assertions or activate real CR semantics. The authored conclusion
is copied and labeled, never selected or rewritten by analysis.

A comparison reports that an author supplied a formerly UNKNOWN value, removed a
declared limitation, changed reasoning or changed the authored conclusion. It
does not verify a new assertion or the soundness of reasoning. An observation
absent from the successor remains in its ancestor; reported origins identify the
original packet/revision. A fresh fictional review is distinguishable from changes
to reviewed material and cannot change evidence conditions or execution authority.

## Acceptance matrix and limits

| Retained input | Required value of the derived view |
| --- | --- |
| A — conditional | Named assumption and possible choice connect to the limited authored explanation; scope survives PRESENT inputs. |
| B — missing | UNKNOWN beacon connects to its dependent step and authored explanation. |
| C — unsupported | Present named assertions coexist with explicitly unsupported evaluation. |
| D — conflict | Both attributed beacon values remain visible along the dependent explanation. |
| E — compatibility | Soften and brighten stay separate; the declared compatibility gap remains visible. |
| B revision 1 → 2 | Supplied beacon assertion, conditions, attribution, reasoning/conclusion changes and removed missing-input limitation are observed; scope/stronger restrictions remain. |
| B revision 2 → 3 | Fresh separately attributed review appears; corrected material and blocked authority stay unchanged. |

Focused command tests also construct a valid parented descendant with a transitive
dependency and mutate structured references to demonstrate graph-derived findings.
Compact controls cover mixed barriers, uncited unknowns, alternative scope,
tampering, unrelated inputs, immutable ownership, relocation, deterministic identity
and unchanged packet/history bytes. Historical root and review-material protections
remain enforced by the unchanged validation boundary. Exact counts, command results,
failed attempts and final-head hosted publication/readback evidence belong in the
single draft PR report, avoiding duplicate milestone reports in state appendices.

Declared dependencies may be incomplete. Absence of a listed unknown, prohibition,
choice or barrier does not prove its absence in the underlying game. Reports with
no declared unknown still preserve unverified assumptions, authored scope,
unsupported stronger conclusions and BLOCKED execution. Predicates/explanations
remain prose; no arbitrary-prose interpretation, effect evaluation, compatibility
solving, legality determination, payment, casting completion or gameplay execution
is implemented. No server, database, GUI, network request, external AI call,
generic graph framework or catalog/query/runtime integration is added.

This milestone adds zero real source units, projections, source anchors or rule
dependency admissions. Coverage remains **100 real projected source units / 15
projections**, casting stages **9/9**, parent proposal range **4/4**, the single
activated b–i import **8/8** with a excluded, and completion's preceding a–h range
**8/8**. Counts do not establish semantic completeness. Semantic closure remains
OPEN; all ten activated-ability responsibilities remain OPEN / EXECUTION_BLOCKED.
Real execution remains BLOCKED; no real GameplayRulesSnapshot or execution profile
is created or activated. No Card/Oracle ingestion, personal collection access or
AI export is authorized. Original retained design records, projected source/evidence,
historical authorization flags and PR #205/#206 performance behavior are preserved.

`source_policy_clearance=not_granted`; private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED. Stop for
independent PM review; the owner retains final merge approval. No subsequent
recommendation is authorized or begun.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false
