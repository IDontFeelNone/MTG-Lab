# Real-Mana Activation-Window Applicability V1

This is a deterministic, read-only assessment of retained propositions under
explicit hypothetical assumptions. It never establishes a legal activation,
performs a game action, or approves executable real-Card semantics.

## Admission and evidence scope

`card_intelligence.mana_window.load_mana_window(**closure_arguments)` calls the
actual public Semantic Closure V1 factory once. It uses that consumer's public,
integrity-checked historical route. It does not access neighboring private
snapshots, admit copied example reports, open the external CR TXT, or load a
second catalog. Every new public load revalidates current source roots.

The existing admitted 24-rule context actually contains all four selected units:

| Unit | Retained rule identity | Supported proposition |
|---|---|---|
|605.3a|`sha256:b996ad86f817a1d69ed179f5b299c6efe56591ff363d162dba64318c98f4c562`|Ordinary-priority and explicitly supplied mana-payment opportunity categories.|
|605.3b|`sha256:64c8d9dffd2a31ad715d214fda4fb650c217f5bd803b72dcb65663cc03a73e04`|Activated-mana no-stack exception and immediate resolution after activation.|
|605.3c|`sha256:c00f9b451db7dcce795fcfb2b1c53a192610feb2c3112a0d73bf155f4709039c`|Restriction on repeating the same ability before that activation resolves.|
|405.6c|`sha256:014c5bf6eb8a3b751961d28ea1e612ade7509763ecd9886fb66dd68010294941`|Conditional return to the pre-activation priority holder after resolution.|

These bind the existing September 25, 2026 artifact
`sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
The first three use package `sha256:010ab048c504b4da4327dbda4a666a6754f2d41e93b73ea34bc595b39c929990`,
projection `sha256:c9432ee880d150d92b88096092cb999dc88fd423c1228bc04bbd284b2b2e1832`.
405.6c uses package `sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1`,
projection `sha256:7ff68d920bd2b846e3fb1616743c48d99e2935b007ccb6943057c47ce74cf87a`.

Reports preserve exact source anchors and span digests. The detailed evidence
route returns the four selected structured records and four exact existing
dependency-review references, with an integrity-checked route to the original
full report. Those reviews establish only their bounded source/dependency scope.
Original `PROJECTED_FOR_REVIEW` states are preserved. They do not constitute
executable semantic approval or fresh verification of source bytes.

## Explicit hypothetical input

`real-mana-window-context-v1` requires exactly its version and seven closed fields.
The helper `hypothetical_context(**assumptions)` supplies UNKNOWN for omitted
information; the file/API contract itself requires every field. No null, boolean,
arbitrary Card name, extra field, permission assertion or free-form rules text is
accepted. Missing payment is UNKNOWN, distinct from explicitly ABSENT.

- `classification`: ACTIVATED_MANA, ACTIVATED_NONMANA, TRIGGERED_MANA, UNKNOWN,
  UNSUPPORTED. These are hypothetical declarations, never computed Card approval.
- `stack_use`, `priority_opportunity`, `same_ability_unresolved`,
  `held_priority_before_activation`, `activation_resolved`: YES, NO, UNKNOWN.
- `payment_opportunity`: ABSENT, UNKNOWN, UNSUPPORTED, or exactly one of
  SPELL_CASTING_MANA_PAYMENT, ABILITY_ACTIVATION_MANA_PAYMENT,
  RULE_REQUESTED_MANA_PAYMENT, EFFECT_REQUESTED_MANA_PAYMENT.

The context describes one activation and its same-ability progress. It is not a
game-state model. A present payment category is never inferred from output.
Priority need not be declared present for the separate hypothetical payment
category to apply. The existence of a real request is never authenticated.

## Findings and generic policy

Five finite proposition findings retain each condition and its supplied value:
ordinary-priority opportunity, payment opportunity, no-stack/immediate resolution,
same-ability repeat restriction, and post-resolution priority return.
The finite adapter obtains category and exception descriptors from the admitted
structured rule records. It does not infer semantics from numbers or Card names.
The bounded pure conjunction evaluator is independently exercised with explicitly
synthetic descriptors; it is never a source-admission endpoint.

APPLICABLE means the conditional proposition follows under these assumptions.
INAPPLICABLE means a necessary condition was explicitly false, with no opposite
permission implied. UNKNOWN means a necessary condition remains unknown.
UNSUPPORTED covers out-of-scope classifications or payment context. Triggered
mana procedures are unsupported in this assessment. CONFLICTING preserves an
activated-mana/stack-use contradiction or a single activation simultaneously
declared unresolved and resolved. No preferred assertion is selected.

A known-false conjunct determines INAPPLICABLE before unsupported/unknown terms;
explicit unsupported classification or a conflict takes precedence. Each local
condition remains visible. Conflicting findings establish no consequence.
The readable renderer prints conditional consequences only for APPLICABLE rows.

## Public use and integrity

```python
from card_intelligence.mana_window import load_mana_window, hypothetical_context
consumer = load_mana_window(**existing_explicit_closure_arguments)
report = consumer.assess(hypothetical_context(
    classification='ACTIVATED_MANA', priority_opportunity='YES'))
# priority opportunity APPLICABLE; payment opportunity UNKNOWN; legality unknown.
consumer.validate_report(report.to_dict(), expected_context=hypothetical_context(
    classification='ACTIVATED_MANA', priority_opportunity='YES'))
consumer.detailed(report.to_dict()['detailed_reference'])
```

`check`, `parse_report`, `render_window` and independently decoded views are also
public. Report validation recomputes every field from admitted owned evidence and
the complete submitted context. An optional expected context binds an external
request; without it validation proves calculation integrity for the explicitly
embedded hypothesis, not authenticity of that hypothesis. A different valid
hypothesis is a different report, not a verified game observation.

CLI: `PYTHONPATH=src python -B -m card_intelligence.mana_window`, with the same
nine explicit root/expected-identity options as Semantic Closure V1, then optional
`--json` and `check`, `assess CONTEXT.json`, `validate REPORT.json`, or
`detail REFERENCE.json`. Input files use the existing canonical strict JSON
codec, including duplicate-key rejection. Exit 0 means assessment succeeded,
never legal activation; invalid input/evidence returns structured stderr and 2.

Context input is bounded to 4,096 bytes, pure proposition input to 16,384 bytes,
16 propositions / 8 conditions each, reports and selected detail to 32,768 bytes,
and readable output to 16,384 bytes. Tests measure actual output sizes without
raising inherited limits. The full historical report is referenced, not embedded.

## Semantic Closure V1 and authority

`mana-window-closure-reference-v1` binds the unchanged original closure report,
accepted candidate and owner decision as provenance only. The existing 23-row
closure report and its identities do not change. Its authority-level evaluator
cannot receive these applicability findings as completed reviewed real procedures.
A stronger composition is deferred until explicitly versioned admission and the
necessary independent review exist. No automatic promotion route is provided.

General priority, actual requests, complete activation/payment procedures,
tap-cost semantics, mana-pool updates, checkpoints and illegal-action recovery
remain unresolved. No missing rule body, new CR citation or executable procedure
is manufactured. Fictional gameplay is not a real-rules authority and is never
called. Targeting, triggers, additional-effect sequencing and real execution are
outside scope.

Architecture v13 and Accepted Decision 017 remain unchanged. Coverage remains
104 CR units / 16 projections / 24 land-context units. Semantic closure OPEN;
canonical_admission=false; execution BLOCKED; all ten activation responsibilities
OPEN / EXECUTION_BLOCKED. Source-policy clearance is not_granted; private
retention, redistribution, free/commercial service and AI export remain
NOT_ESTABLISHED. Existing non-production review admission is not a new use license.

The only inherited modification is a four-line test-helper delegation to a finite
byte-pinned successor adapter. It reconstructs the exact canonical predecessor
and pins only the one new runtime module. Historical ledgers, expectations,
reports, source evidence, fictional profiles and workflows remain unchanged.
