# Functional-Role Card Intelligence — bounded review pilot

Canonical main independently verified on 2026-10-12: `e4a99ae6ccffe3e7121337fe28d9127024be3743`, the successful merge of GitHub PR #166. Architecture v12 remains frozen. This named milestone does not assign a phase number; project phases and GitHub PR numbers remain independent.

## Implemented boundary

Exactly **15 production Cards** receive **30 pending role candidates**: 20 directly evidenced proposed functions, four incomplete contextual interpretations, two unknown proposals, and four explicitly unsupported assignments. All remain `requires_review`, with no human attestation and no canonical admission. The provisional vocabulary also requires review.

`src/card_intelligence/roles.py` validates engineer-authored proposals against exact production Card IDs, immutable mechanical dossier identities, the canonical snapshot, and complete retained Oracle passages. It does not infer roles from keywords, search phrases to assign labels, run a model, or classify the cohort automatically. Semantic correctness of the authored interpretation remains a human-review responsibility. The validator checks evidence bindings and structural boundaries; it is not a rules or natural-language entailment engine.

The existing cohort is still 384 production Cards mapped to 385 retained Scryfall rows, with Essence of Ajani excluded, 15 typed seed Cards outside the cohort, and five missing canonical source Printings. Every selected Card has a uniquely bound root Oracle field; this pilot does not interpret multi-faced Cards. The original 384 mechanical dossiers and the earlier Sol Ring/Counterspell demonstration remain byte-identical. No canonical, market, knowledge, or historical evidence is admitted or rewritten.

## Exact pilot and proposed role census

A known state means that the proposed outcome is directly evidenced with its qualifications. It does **not** mean human approval, canonical admission, positive net advantage, or strategic superiority.

| Card | Exact production identity | Directly evidenced proposed functions | Other proposed/unsupported assignments |
|---|---|---|---|
| Veil of Summer | `002965be-a36f-4a09-9ce0-c6535bca1703` | card_draw, protection | — |
| Ponder | `02090581-61aa-4348-ad57-451be8ee91c2` | card_draw, card_selection | — |
| Underworld Breach | `27e0948b-9916-473b-8d8c-a51bdfbc7457` | recursion | combo_enabling (incomplete), sacrifice_outlet (unsupported) |
| Faithless Looting | `3d6fa57a-aa53-4b5c-b8af-a7612c823117` | card_draw, recursion | card_selection (incomplete) |
| Giver of Runes | `4ec85850-f274-4c0c-9a03-0488267caa14` | protection | — |
| Treasure Cruise | `5b6bdf5a-2742-4851-92cd-a857a3852836` | card_draw | — |
| Sol Ring | `6ad8011d-3471-4369-9d68-b264cc027487` | mana_acceleration | — |
| Basalt Monolith | `6b8cf2a0-b045-4d91-9d91-c602d40c6237` | mana_acceleration | combo_enabling (unknown) |
| Wishclaw Talisman | `81c70ae7-3c18-4c9b-8505-e4db9e0e6518` | tutoring | — |
| Noxious Revival | `97cabeda-9fe3-490d-99b4-4c8d87c17157` | recursion | card_draw (unsupported) |
| Pitiless Plunderer | `a784481f-eccb-4112-bb38-04a659319660` | event_payoff, mana_acceleration | combo_enabling (unknown), sacrifice_outlet (unsupported) |
| Swords to Plowshares | `b1544f21-7e98-461b-aed5-e748b0168c52` | removal | — |
| Counterspell | `cc187110-1148-4090-bbb8-e205694a39f5` | stack_interaction | protection (incomplete) |
| Greater Good | `dc0593c2-ccb4-4648-a592-c5bcd121dc72` | card_draw, sacrifice_outlet | card_selection (incomplete) |
| Standstill | `fea4cb32-0329-4199-9abe-bff0cc45882a` | card_draw | sacrifice_outlet (unsupported) |

Selection is deliberate, not representative sampling for population prevalence. It covers resource output, paid untap, conditional and variable draw, selection, countering, targeted exile, constrained tutoring, protection scope, graveyard return/casting, voluntary sacrifice, death payoffs, and contextual combo-enabling questions. It excludes face-aware role interpretation, arbitrary mechanics, formal rules interactions, legal casting windows and deck-specific priority.

## Versioned contract and provisional vocabulary

`functional-role-candidate-v1` has a game-neutral subject/role/evidence envelope, content identity, source-field binding, qualifiers, contextual dependencies, review status and supersession. The shared schema has no MTG-only game enum or mandatory mana/rules fields. `mechanical_binding.context_metadata` carries game-specific fields. The MTG adapter uses the existing mechanical projection and existing `Evidence` contract; it does not create another knowledge repository.

`config/card_intelligence/functional-role-vocabulary-v1.json` supplies eleven MTG-specific provisional definitions and evidence requirements. These are not an exhaustive or universally approved taxonomy:

| Role | Required interpretation boundary |
|---|---|
| mana_acceleration | Actual resource production/access, with costs, recipients and restrictions; an untap or resource word is insufficient. |
| card_draw | Explicit draw quantity and beneficiary, including conditions and accompanying discard/return; no net-advantage inference. |
| card_selection | Explicit look/choice/order evidence; filtering from draw/discard remains contextual. |
| removal | Exact action, target, destination, compensation and restrictions. |
| stack_interaction | Exact pending action affected; countering a spell does not imply countering an ability. |
| tutoring | Search location, permitted selection, destination, costs, timing and downside. |
| protection | Protected subjects, scope and duration; describing ordinary interaction as protection needs threat/objective context. |
| recursion | Source, destination or casting permission, owner, costs and exclusions; library-top return is not draw. |
| sacrifice_outlet | Voluntary activation with an explicit sacrifice cost; forced sacrifice or a death payoff is insufficient. |
| event_payoff | Exact triggering event, recipient, controller and self/other distinction; death need not be sacrifice. |
| combo_enabling | Contextual review proposal only; direct components plus missing partner/cost/sequence dependencies, never a verified loop. |

Value states are `known`, `incomplete`, `unknown`, and `unsupported`. Direct mechanical proposals require known support; contextual interpretations must remain incomplete or unknown; unknown/unsupported values are null. Unsupported entries record a particular rejected assignment and do not prove absence of every possible contextual use. Unlisted roles are unassessed, not known absent.

The contract supports primary/secondary designations only with explicit context evidence. Every current candidate's prominence is unknown: no deck objective or human priority assessment is retained. Oracle order is not used to rank roles. Supersession validation requires an existing candidate with the same subject and role definition and a later preparation timestamp; this pilot supersedes nothing and stores or promotes no facts.

The pending envelope requires `review.status=requires_review`, a null human attestation and `canonical_admission=false`. Changing a status or recomputing an identity cannot make it an approved fact. `KnowledgeRepository.append` rejects these candidate objects. Future knowledge admission requires separate authorization and the existing knowledge/evidence governance; this milestone supplies no admission function or approval API.

## Source and deterministic provenance

The sole provider input remains the already retained `scryfall-mb2-30754638264-1` acquisition, source file `data/market/acquisitions/scryfall-mb2-30754638264-1/source-mb2.json`, SHA-256 `c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47`. The source timestamp is `2026-08-02T09:09:45.851000Z`, retrieval `2026-08-02T15:34:06Z`. No new source download, rules acquisition, image or provider integration occurs. Existing provider/source governance remains unchanged.

The annotation preparation timestamp `2026-10-12T16:08:11Z` was captured from the session clock; it is distinct from historical observation/retrieval times. It is fixed input to replay, not a fabricated provider timestamp or a timestamp generated on every execution.

The existing mechanical loader verifies retained acquisition manifests, file byte counts/digests and report agreement. Each role proposal binds the full mechanical dossier identity, canonical snapshot, provider record identity/hash, retained-source digest, original field pointer, complete Oracle text, and complete selected lines. Evidence references use the actual retained array index and JSON pointer. The full field remains available even when a particular ability is selected. Exact expected dossier identity/name and complete field equality fail closed after source or snapshot changes.

The annotation plan and vocabulary have deterministic content identities and retained file digests. Candidates, dossiers, review report, comparison and contexts use sorted-key compact UTF-8 JSON with explicit versions. Individual dossiers and contexts have a 65,536-byte cap; oversize outputs fail rather than silently dropping roles. Comparison handoffs currently use fewer than 32,000 bytes each. Original upstream bulk bytes remain unretained, as disclosed by the mechanical source contract; upstream digests remain acquisition assertions.

## Practical comparison and ChatGPT boundary

The bounded comparison uses **Ponder, Faithless Looting and Greater Good**. All have a directly evidenced draw proposal, with materially different restrictions:

- Ponder supplies explicit top-three ordering/optional shuffle and draws one card.
- Faithless Looting draws two then discards two; its retained flashback reminder permits later casting of this card for `{2}{R}` and subsequent exile. Strategic filtering remains incomplete.
- Greater Good requires sacrificing a creature, draws according to its power, then discards three. The voluntary outlet and draw are direct proposals; filtering value depends on missing hand, creature and deck context.

These differences could help a later deck analysis ask about selection, graveyard access, sacrifice resources and conditions. They do not establish interchangeability, a superior choice, positive net advantage, a verified combo or a ranking. The machine comparison and [human-readable comparison](../data/review/functional-role-pilot/comparison.md) retain all relevant candidates, qualifiers and exact passages.

Three individual manual handoffs reuse `canonical-reasoning-context-v1` and the existing mechanical handoff. They retain the original mechanical supplement and add a labeled `functional_role_review_pilot_manual_handoff` supplement. `analytics_snapshot_id` remains null; the normalized request describes the base semantic retrieval. This is an explicit manual supplement, not a new semantic/analytics operation. Candidate omissions are zero, byte limits and generic omissions are reported, and source/canonical references remain present. No model, transport, hosting or live ChatGPT integration runs.

## Review material, use and replay

Eight isolated derived artifacts live in `data/review/functional-role-pilot/`: 15 dossiers in `dossiers.jsonl`, `review-report.json`, `comparison.json`, `comparison.md`, three Card-ID-named reasoning contexts, and `manifest.json`. Input plans live in `config/card_intelligence/`. Neither directory is a canonical fact store or an admission input to the existing knowledge repository.

```bash
PYTHONPATH=src python -m card_intelligence.cli roles --card-id dc0593c2-ccb4-4648-a592-c5bcd121dc72
PYTHONPATH=src python -m card_intelligence.cli roles-pilot
PYTHONPATH=src python -m card_intelligence.cli roles-comparison
PYTHONPATH=src python -m card_intelligence.cli roles --card-id 02090581-61aa-4348-ad57-451be8ee91c2 --reasoning-context
PYTHONDONTWRITEBYTECODE=1 python scripts/build_functional_role_pilot.py --check
```

The generator writes only the isolated review directory, rejects conflicting existing artifacts and supports byte-identical read-only checking. Tests cover exact identities, multi-role semantics, restrictions, false positives, evidence pointers, state distinctions, source/snapshot mismatch, deep immutability, deterministic identities/replay, prominence context, supersession, schema/review enforcement, existing mechanical/context compatibility and protected-data non-mutation. Full-suite and hosted results are recorded in the milestone PR.

The one next action is Project Manager review of the provisional definitions, all 30 exact source-bound proposals, restrictions, unknowns and comparison. All candidates remain pending. No role admission, full-cohort classification, formal rules/combos, synergy scoring, universal best-in-slot, deck optimization, tournament/metagame acquisition, price forecasting, acquisition recommendation or Architecture v12 change is authorized. Stop after the single PR handoff; no follow-on implementation is automatic.
