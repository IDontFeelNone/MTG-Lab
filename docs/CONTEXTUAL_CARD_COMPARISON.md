# Contextual Card Comparison — bounded pending-evidence pilot

Canonical main independently verified on 2026-10-12: `4d15582d6ed364f012e853c1fdb2312e54ea7c60`, the merge of GitHub PR #167. Architecture v12 remains frozen. GitHub PR numbers and project phases are independent; no new phase number is assigned.

## Scenario and exact selection

The hypothetical objective is to compare resource requirements and card-access trade-offs for a blue/red/green casual testing shell. This is neither a submitted decklist nor evidence of sanctioned format legality, metagame relevance or competitive performance. The Cards are alternatives for inspection, not proven interchangeable slots.

| Card | Exact production Card ID | Retained casting cost | Provider mana value | Other relevant route |
|---|---|---|---|---|
| Ponder | `02090581-61aa-4348-ad57-451be8ee91c2` | `{U}` | 1 | Top-three ordering / optional shuffle followed by one draw. |
| Faithless Looting | `3d6fa57a-aa53-4b5c-b8af-a7612c823117` | `{R}` | 1 | Draw two, discard two; this Card's flashback `{2}{R}`, followed by exile, is supplied in the retained reminder. |
| Greater Good | `dc0593c2-ccb4-4648-a592-c5bcd121dc72` | `{2}{G}{G}` | 4 | Enchantment setup and a separate sacrifice-a-creature activation cost; power-based draw followed by discard three. |

All are exact production identities, normal-layout Cards with sufficient root mechanical evidence. No seed or name fallback is allowed. The bounded selection is not a cohort classification or complete-set analysis.

Three assumptions are explicit supplied inputs, never provider facts: the hypothetical shell, an illustration in which the relevant instructions resolve and can be followed, and a creature of power four for the Greater Good illustration. That last assumption does not verify creature availability, expendability or the applicable power-determination rule. Actual hands, libraries, graveyards, mana access and legal game state are absent.

## Evidence and interpretation boundaries

`contextual-card-comparison-v1` is an immutable, versioned, game-neutral envelope. The shared schema does not enumerate MTG Cards, colors, roles or resource rules. The MTG adapter binds the configured three Cards and the complete retained root Oracle fields. It separates:

1. Source-verified provider assertions: exact identity, five selected root mechanical fields, source record and snapshot hashes, provider timestamp, retrieval time and compact canonical lineage.
2. Pending functional interpretations: all eight selected original role candidates, unchanged and still `requires_review`.
3. Supplied deck-context assumptions: versioned inputs with explicit state, value, description and content identity.
4. Deterministic descriptions: exact mana-value subtraction and conditional instruction-count subtraction, with their dependencies and limitations.
5. Unverified strategic hypotheses: one per Card, explicit evidence/assumption references and counterarguments, without a suitability score or claimed selection.

The original role vocabulary remains provisional. Six selected role proposals have directly evidenced known functionality; Faithless Looting's and Greater Good's selection proposals remain incomplete. Known functionality does not mean role approval or canonical authority. The fifteen-Card pilot still contains 30 pending assignments with the original 20/4/2/4 state census. No role is rewritten, superseded, approved or admitted here.

Initial casting, later flashback and permanent activation remain separate. Full Oracle passages, all role costs/conditions/restrictions, and unknown legal timing are preserved. An enchantment's mana value is not its activation payment. A lower mana value is not universal efficiency. Repetition, free setup, instant-speed permission, positive net advantage and profitable sacrifice are not assumed.

## Comparisons and abstention

Five explicit criteria cover casting requirements, instruction counts, selection/multiple roles, costs/restrictions/dependencies, and unknown timing/opportunity cost. All selection weights are null. They describe inspection dimensions, not a weighted power score.

Mana values show Ponder and Faithless Looting equal on this single scalar, and three less than Greater Good. Their colored requirements differ, and Greater Good's activation requires a creature independently of its initial casting cost. These observations cannot establish castability or a preferred choice.

| Conditional instruction arithmetic | Draw count | Mandatory discard instruction count | Difference |
|---|---|---|---|
| Ponder | 1 | 0 | +1 |
| Faithless Looting | 2 | 2 | 0 |
| Greater Good, supplied power-four illustration | 4 | 3 | +1 |

These counts come from pending, source-bound engineer-authored literal-instruction annotations; the validator is not a rules/semantic entailment engine. Arithmetic is deterministic conditional on those readings and the supplied illustration. Zero for Ponder represents no discard instruction in its complete retained passage, not an unknown cost replaced by zero. Missing counts remain unknown/null. No result is a net card-advantage claim: casting expenditure, sacrificed creature, hand/library sufficiency, setup, resolution and opportunity cost are excluded. There is no draw-per-mana or total-resource-efficiency score.

The contextual hypotheses are that ordering could help an immediate access objective; draw/discard plus flashback could suit a graveyard-tolerant plan; and creature-supported draw/discard could suit a plan able to afford the sacrifice. Actual outcomes, utility and deck suitability remain unverified. Each hypothesis carries its own counterargument.

The adapter reuses `DecisionAlternative`, `EvidenceReference`, `DecisionRequest`, `DomainAnalysisEnvelope`, `AnalysisMetric`, `DecisionPolicy` and the existing `AcquisitionDecisionOrchestrator`. Despite that historical class name, no acquisition objective or action is passed. No engine or policy algorithm is duplicated or modified.

The bounded policy requires `human_reviewed_context_match`; every alternative's metric is unknown. It has no numeric suitability or power value and cannot infer one. The existing engine therefore emits `recommendation-v1` with **ABSTAIN**, null selection and three exact unknown-metric blockers. The comparison contract also refuses selection and review/admission mutations. It exposes no approval API. Human review and a separately authorized, evidence-supported policy would be necessary for any later selection capability; hypothetical assumptions alone cannot approve roles.

## Provenance, replay and manual ChatGPT boundary

The sole provider input remains retained Scryfall acquisition `scryfall-mb2-30754638264-1`: source SHA-256 `c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47`, observation `2026-08-02T09:09:45.851000Z`, retrieval `2026-08-02T15:34:06Z`. Existing manifest verification, source licensing/attribution and mechanical source limitations remain unchanged. Original upstream bulk bytes remain unretained; upstream digests remain acquisition assertions. No source download or new provider occurs.

Preparation time `2026-10-12T17:44:40Z` was captured from the session clock and retained as a fixed annotation input. It is not a provider observation time or a new timestamp generated during replay. The configured plan binds exact mechanical and role dossier identities, complete Oracle passages and canonical snapshot. Canonical, source, dossier or role drift fails closed. Semantic correctness of the authored instruction readings and strategic hypotheses remains a human-review responsibility.

Five isolated derived artifacts reside in `data/review/contextual-card-comparison/`:

- [comparison.json](../data/review/contextual-card-comparison/comparison.json): the complete 55,794-byte compact JSON dossier (55,795 retained file bytes), including eight unchanged pending role candidates and the existing deterministic abstention.
- [decision-inputs.json](../data/review/contextual-card-comparison/decision-inputs.json): complete existing request/policy/analysis contracts, independently content-addressed from the dossier rather than repeated in the handoff.
- [reasoning-context.json](../data/review/contextual-card-comparison/reasoning-context.json): one 61,430-byte compact JSON manual wrapper (61,431 retained file and CLI output bytes) composing three unmodified `canonical-reasoning-context-v1` retrieval contracts, the full dossier and its `decision-reasoning-context-v1` result.
- [explanation.md](../data/review/contextual-card-comparison/explanation.md): deterministic human-readable example, strictly rendering the dossier's facts, pending roles, assumptions, arithmetic, hypotheses, counterarguments and abstention.
- [manifest.json](../data/review/contextual-card-comparison/manifest.json): input file byte counts/hashes, content identities and exact output integrity inventory.

The generic retrieval contexts deliberately set entity/evidence limits to zero to avoid duplicating large audit projections already represented by compact lineage and source bindings in the comparison. Each reports one omitted generic entity and one omitted generic evidence item; no selected Card or role is omitted from the dossier. Their normalized exact-identity requests, snapshot IDs, original context identities, truncation limits and warnings remain intact. No new semantic operation, altered generic request or false analytics snapshot is introduced.

Dossiers and manual wrappers have a 65,536-byte compact UTF-8 JSON payload bound and fail on oversize; they never silently discard selected roles. Retained JSON files and contextual-comparison CLI JSON output append exactly one final LF. Content identities and the canonical payload guard exclude that framing byte. The CLI checks its complete UTF-8 output, including the LF, before writing and rejects output above 65,536 bytes; its compact payload therefore has a 65,535-byte budget. Sorted-key compact UTF-8 JSON, immutable payloads and SHA-256 identities make replay deterministic. The manual wrapper is explicitly supplemental evidence, not live ChatGPT transport or model execution. ChatGPT may explain the supplied result while preserving abstention and evidence states.

```bash
PYTHONPATH=src python -m card_intelligence.cli contextual-comparison
PYTHONPATH=src python -m card_intelligence.cli contextual-comparison --human-readable
PYTHONPATH=src python -m card_intelligence.cli contextual-comparison --reasoning-context
PYTHONDONTWRITEBYTECODE=1 python scripts/build_contextual_card_comparison.py --check
```

The generator writes only the isolated review directory, rejects conflicting retained bytes and supports read-only exact replay. Focused tests cover production IDs, context states, source/role binding, qualifications, instruction assumptions/missing values, existing-engine contradiction/abstention, human-review rejection, immutable serialization, byte caps, example claims, CLI compatibility, previous demonstration replay and production non-mutation. Complete-suite and hosted results are recorded in the milestone PR.

## Stop boundary

The 384-Card mechanical cohort, earlier Sol Ring/Counterspell handoffs, original functional-role bundle, canonical production data, market observations, knowledge facts, historical evidence and Architecture v12 remain unchanged. CC2 remains `NOT_READY_FOR_EVALUATION`. Competitive Intelligence stays parked; Competitive Card Intelligence and Deck Intelligence remain planned and unauthorized.

The one next action is Project Manager review of this declared scenario, source-bound readings, pending roles, trade-offs, omissions and abstention. No automatic approval, knowledge admission, Card selection, deck optimization, full-cohort classification, rankings, combo/synergy discovery, tournament acquisition, provider acquisition, pricing decision or follow-on milestone is authorized.
