# Portable Deck Research Investigations V1

This implemented local workflow preserves a supplied-deck question, exploratory
notes, immutable experiment versions and independent alternatives. It implements
a small portable artifact subset of the [Research Log](RESEARCH_LOG_ARCHITECTURE.md),
not a general research platform, reviewed finding store or live ChatGPT connection.
Architecture v13, Decision 017 and all source/admission boundaries are unchanged.

## Start, investigate and save

Use the existing Python environment and dependencies:

```sh
python -m pip install -r requirements.txt
PYTHONPATH=src python -B -m workbench.research
```

Open the printed `http://127.0.0.1:PORT/research` URL on the same computer.
The original workbench and its command remain unchanged. Stop with Ctrl+C.
This is not hosted deployment or direct iPhone access to a desktop loopback port.

1. Enter an original question and choose **Start question**. A hypothesis or deck
   is optional. Add notes and record a **notes-only** revision to begin exploring.
2. Enter the deck in the existing [editor](LOCAL_DECK_WORKBENCH_V1.md), explicitly
   select its complete draw population, groups and cumulative observations, and
   calculate. Clear **notes-only** and record the verified experiment.
3. To fork, load a saved revision and enter a new branch identity. Change quantities,
   assumptions or notes and record another revision. Existing branch identities
   must extend their own latest saved version; siblings remain independent.
4. Record counterexamples, rejected alternatives and unresolved questions. Outcomes
   are user claims, including `supported_under_declared_assumptions`; they establish
   no strategic superiority or approval. References are unverified `user:KEY` or
   content-hash identities, not automatically fetched citations.
5. Choose **Save investigation JSON**. Keep the downloaded file: all server/browser
   state is otherwise volatile. Reloading or stopping loses unsaved work. Names
   contain an artifact identity prefix; keep older files for their exact versions.
6. **Reopen saved investigation** explicitly selects a file in your browser. It is
   strictly checked and all saved calculations are reproduced before presentation.
   **Verify saved calculations** verifies the saved history, not an edited draft.
7. Select exact revisions and explicitly download the handoff text. Review its
   private contents and source-use/AI-export permissions before sharing manually.
   Saving JSON includes **all** history; selection limits only the text handoff.

Editing analytical inputs clears the editor's current result. Unsaved changes
disable investigation save and handoff export. Recalculate and record, or explicitly
record a notes-only revision; an old result is never attached to changed inputs.
Partially invalid deck drafts are not saved as experiments: record notes-only or
finish and calculate the deck first. Loading an old revision restores that exact
experiment; extending a non-head version requires a new branch identity.

## Contract and public API

The [machine schema](../src/schemas/v1/portable-deck-investigation.schema.json) is
`portable-deck-investigation-v1`, with `deck-research-revision-v1` records.
Its closed header binds a caller-local key, original question, UTC creation time,
stable investigation identity, analytical engine and exact ordered revision list.
Each revision binds its branch, exact parent, metadata, normalized analytical
request and optional complete owning result. Empty investigations are valid.

```python
from workbench.investigations import (
    create_investigation, append_revision, save_investigation,
    open_investigation, replay_investigation, export_handoff,
)

record = create_investigation(key="my-question", question="Can four copies help access?",
                              created_at="2026-11-20T12:00:00Z")
# append_revision accepts explicit metadata and the existing workbench input.
# calculate=False retains validated inputs WITHOUT a current result.
raw = save_investigation(record)  # bytes only; the caller explicitly saves them
restored = open_investigation(raw, expected_artifact_id=record["artifact_id"])
receipt = replay_investigation(restored)
# export_handoff(restored, revision_ids=[...]) requires an explicit nonempty selection.
```

`append_revision` never mutates an earlier dictionary or inherits a result from a
parent. All annotation lists and nested objects are privately owned. Parent links
must refer backwards to exact revisions; cycles, second roots, orphan links,
duplicate revisions and ambiguous same-branch forks refuse. Original question
changes require a new investigation identity.

Serialization is canonical sorted-key compact UTF-8 JSON without a trailing LF.
Identities use SHA-256 of `domain + NUL + canonical_json(body)`, excluding only
their fixed self-identity field. Full artifact identity covers all history.
Revisions bind both the workbench report and unchanged native supplied-deck report.
Engine compatibility binds exact packaged bytes of the workbench adapter,
supplied-deck consumer and draw-access engine. Missing/incompatible code refuses;
code-file drift under an imported process also refuses. There is no migration,
fallback, dynamic import or substitution with a new engine. Future compatibility
requires separately reviewed work; retain compatible code to reproduce old files.

Hashes and caller-supplied timestamps do not authenticate authorship or approval.
An attacker can author a different, coherently rehashed annotation history; it
remains unverified. Independently pin `expected_artifact_id` when checking a known
handoff. Altered results, even after rehashing, fail the native recomputation check.

## Bounds and refusals

Maximum artifact size is 2 MiB, with 16 revisions, eight branches, and at most 16
4,000-character entries per annotation list. Evidence references are capped at 16.
The transport caps requests at twice the artifact budget plus 8 KiB, allowing
escaped file JSON and a new analytical request. The owning engine's 1–120 deck,
0–20 cards-seen, one–three disjoint groups and input/report budgets remain intact.
Worst-case replay performs bounded owning analyses for at most 16 revisions.

Errors distinguish invalid artifacts, budgets, schema/engine incompatibility,
lineage failure, integrity mismatch, unavailable dependencies and analytical
refusal. No partial replay success, approximation or zero probability replaces a
failed calculation. A valid impossible access event remains an exact zero.
Embedded analytical structures are checked by the owning API, in addition to the
published structural schema; a schema-valid JSON object alone is not admission.

## Original example and handoff

**Load original research example** demonstrates exploratory notes, a three-copy
baseline and two independent branches: four copies and a rejected two-copy access
hypothesis. The exact owning comparison is:

- Three copies, seven seen from 60: `5397/17110`.
- Four copies: `38962/97527`.
- Candidate minus baseline: `81991/975270`.

These are joint card-access probabilities under caller assumptions, not casting,
combo execution, win rates or a recommendation to replace a card. Read the retained
[machine example](../tests/fixtures/portable_research_v1/example-investigation.json)
and [text handoff](../tests/fixtures/portable_research_v1/example-handoff.txt).
The example is original and contains no real Card source content.

## Security, privacy and composition

The additive same-process page uses the unchanged deck editor and
`workbench.adapter.assess_workbench`, which delegates to `assess_supplied_decks`.
It is not a new probability controller or general tool dispatcher. Its finite
request operations are create, append, open, replay, export and original example.
The original `/assess` route and all historical assets remain byte-identical.

Loopback binding, Host/Origin checks, per-launch capability, CSP, request limits
and suppressed access logging are inherited/preserved. New paths are fixed assets
or bounded JSON operations. File selection happens in the browser; no caller path
is accepted by the server. There is no database, arbitrary file endpoint, automatic
save/export, external asset, collection access, canonical write or outbound model
request. Notes are rendered with textContent and quoted in plain-text handoffs;
executable-looking text is data. A handoff is not a trusted instruction prompt.

Initial scope is user-authored research and declared deck experiments. Private
location, a download or a pasted label grants no source rights. Do not use this
workflow to import source datasets or bypass export restrictions. Real-card
understanding, ingestion, markets, visual identification, hosted/mobile apps,
autonomous research and full-corpus CR processing remain outside scope. Existing
full-corpus CR HOLD and real-card execution restrictions remain unchanged.
