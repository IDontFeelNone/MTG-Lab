# Offline proposed-spell packet authoring pilot

This separately owner-authorized pilot authors fictional packets under the unchanged
[v1 design](GAMEPLAY_RULES_PROPOSED_SPELL_EVIDENCE_PACKET_DESIGN.md). It renders the
author's explanation and validates structure, identities and retained references.
It does not verify fictional assertions, generate reasoning, supply a conclusion
or grant gameplay permission. Execution authority is always **BLOCKED**.

Run from the repository with its existing Python dependencies installed. Select a
local pilot workspace outside the repository explicitly; use a temporary directory
for the examples:

The workspace must already exist. Draft outputs must also be outside the
repository and separate from the sealed `packets/` directory.

```sh
export PYTHONPATH=src
workspace=$(mktemp -d)
python -m proposed_spell_packets --workspace "$workspace" draft \
  --example packet-b-missing.json --output "$workspace/missing-draft.json"
${EDITOR:-vi} "$workspace/missing-draft.json"
python -m proposed_spell_packets --workspace "$workspace" record \
  --draft "$workspace/missing-draft.json"
```

The record command prints its `packet_id`. Copy that exact identity for subsequent
commands; there is no timestamp-based "latest" selection:

```sh
packet_id=sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b
python -m proposed_spell_packets --workspace "$workspace" inspect "$packet_id"
cat "$workspace/packets/${packet_id#sha256:}.json"
python -m proposed_spell_packets --workspace "$workspace" draft \
  --base "$packet_id" --output "$workspace/correction-draft.json"
${EDITOR:-vi} "$workspace/correction-draft.json"
python -m proposed_spell_packets --workspace "$workspace" record \
  --draft "$workspace/correction-draft.json"
```

The example identity above applies when the initial draft is unchanged. Use the
actual emitted identity after any edits. A correction selects its parent by exact
identity and starts the next revision in the same lineage. Supply changed
assertions, attribution, explanation, limitations and conclusion explicitly.
The tool rejects inconsistent references instead of repairing authored material.
This pilot supports linear histories only: each root has revision 1, and every
correction names one parent. Sealed imports and their reachable history must obey
the same pilot boundary; the retained v1 schema and shared checker are unchanged.

For a separately attributed review, create another draft from the correction's
emitted identity, append an explicitly fictional observation in
`packet.history.review_observations`, record it, then inspect its history:

```sh
correction_id=sha256:REPLACE_WITH_EMITTED_CORRECTION_ID
python -m proposed_spell_packets --workspace "$workspace" draft \
  --base "$correction_id" --output "$workspace/review-draft.json"
${EDITOR:-vi} "$workspace/review-draft.json"
python -m proposed_spell_packets --workspace "$workspace" record \
  --draft "$workspace/review-draft.json"
review_id=sha256:REPLACE_WITH_EMITTED_REVIEW_ID
python -m proposed_spell_packets --workspace "$workspace" history "$review_id"
```

For the demonstrated B correction, a complete fresh observation has this shape;
the reviewer supplies the fictional identity, fresh ID and observation text:

```json
{
  "authority": "HUMAN_REVIEW_OBSERVATION",
  "fictional": true,
  "observation_id": "review-correction",
  "reviewer_id": "fictional:b:second-reviewer",
  "claim_refs": ["beacon", "premise"],
  "step_refs": ["condition"],
  "supersedes_observation_ids": [],
  "text": "Fictional reviewer observation of this correction only; no factual verification, actual PM/owner approval or gameplay authority."
}
```

A draft is an editable JSON envelope with exactly `draft_version`,
`base_packet_id` and `packet`. Its packet body omits `packet_id`. A supplied
identity or unknown field is an error. Readable formatting is accepted only in
draft mode. Explicit recording derives the v1 content identity from the owned,
validated body and writes canonical bytes to `packets/<sha256 hex>.json`.
No time, random identifier or local path enters packet content.

A sealed record includes its own `packet_id` and must already contain exact v1
canonical bytes. Import one explicitly with `record --sealed PATH`; a tampered
identity or reformatted record fails. Recording never reseals a sealed input,
overwrites a record or repairs corruption. An identical existing record is
reported only after byte verification. Each operation freshly validates the
actual retained contract/package bindings and required reachable history.
The pilot refuses writes into retained evidence directories.

Direct conclusion assumptions must fit every cited branch, including transitive
dependencies. Alternative-specific premises cannot become general premises.
An observation ID binds its original material closure across all reachable
ancestors, including after intermediate omission. If material changes, leave the
old observation in its original historical packet, omit it from the successor,
then add a fresh observation with a fresh ID and explicit fictional reviewer.
For a review-only correction with unchanged material, carry the original
observation and append another whose `supersedes_observation_ids` names it.
Those links are local to the current packet; an ancestor-only observation cannot
be named there. History shows observations in their originating packet/revision.

The complete reproducible demonstration uses actual CLI commands on all five
retained examples, rejects a changed-material correction carrying `review-1`,
records the proper correction and adds a fresh fictional review:

```sh
demo_workspace=$(mktemp -d)
PYTHONPATH=src python tools/proposed_spell_packet_demo.py \
  --workspace "$demo_workspace"
```

The script contains explicit fictional author/reviewer inputs rather than copies
of prior evidence packages. Its final JSON reports the reproducible packet IDs.
The original B packet has `INDETERMINATE_MISSING`; revision 2 supplies a fictional
beacon assertion and an authored `CONDITIONAL_SUPPORT` explanation; revision 3
adds `fictional:b:second-reviewer`'s fresh observation. The old review remains in
revision 1. Unsupported C, conflicting D and independent-alternatives E retain
their limitations even though their structures validate.

The demonstrated deterministic chain is:

| Revision | Packet identity | Authored change / observation origin |
|---|---|---|
| 1 | `sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b` | Original missing beacon input; `review-1` originates here. |
| 2 | `sha256:5c6bd95825dadef42beb389ba67b18111593de26311ba88eaed94ff1cf118345` | `fictional:b:correction-author` supplies beacon=true and revised explanation/conclusion; original review stays only in revision 1. |
| 3 | `sha256:06e437c42ce77e5f10a8aa9ead9fb8a9b2c9c6929b9481c64c4d66563b98cf13` | Unchanged corrected material; fresh `review-correction` by `fictional:b:second-reviewer` originates here. |

Inspection keeps structural validity, authored per-claim/per-step evidence
conditions, authored explanation and execution authority distinct. Rule/version
references supply contextual evidence only. Reviews remain fictional and confer
no actual PM/owner approval, factual verification or gameplay authority. No real
Card data, source body, attachment, gameplay evaluator, runtime admission,
network service, database, AI call or automatic publication is involved.

Architecture v13 remains ACTIVE APPROVED; Decision 017 remains ACCEPTED. The eight
retained design JSON files and historical authorization flags remain byte-for-byte
unchanged. Coverage remains 100 real source units / 15 projections, casting stages
9/9, parent range 4/4, the single activated b–i import 8/8 with a excluded, and
completion's preceding a–h range 8/8. This adds zero units, projections, anchors or
dependency admissions and establishes no semantic completeness. Semantic closure
remains OPEN; all ten activated-ability responsibilities remain OPEN /
EXECUTION_BLOCKED. No real snapshot or execution profile is created or activated.

`source_policy_clearance=not_granted`; private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED. This pilot
awaits independent PM review and final owner merge approval; no subsequent
milestone or source projection is authorized or begun.
