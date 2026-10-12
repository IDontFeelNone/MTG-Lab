# Collection-Aware Card Acquisition Pilot

Canonical main independently verified: `3cf6ad35fcb54ed5a4b640e36af6fa2ecf99a747`, the merge of GitHub PR #168. Architecture v12 is unchanged. This is a named milestone; PR identifiers are separate from project phase numbers.

## Bounded question and identities

“Which one missing copy should I acquire first, given my budget, ownership, declared objectives, and verified acquisition costs?”

| Card | Exact production Card | Exact production MB2 Printing |
|---|---|---|
| Ponder | `02090581-61aa-4348-ad57-451be8ee91c2` | `5c8d3bc4-32fc-5b26-84bf-9921e5884d43` |
| Faithless Looting | `3d6fa57a-aa53-4b5c-b8af-a7612c823117` | `72783a15-4847-5448-8f1d-0c40379594d3` |
| Greater Good | `dc0593c2-ccb4-4648-a592-c5bcd121dc72` | `46c0ae9f-b64a-528f-aab6-f1ceff9f0ade` |

The pilot requests English nonfoil copies with explicitly supplied physical-condition constraints. Greater Good's canonical Printing supports both foil and nonfoil; a foil offer cannot satisfy the nonfoil preference. Canonical treatment is absent and remains unknown; null in the pilot represents no supported treatment distinction, never an invented “regular” variant. A decision-critical unsupported treatment requirement fails closed.

The Card adapter contains no special cases for these identities. The isolated demonstration configuration selects them. They are not asserted to be interchangeable slots or legal in a particular sanctioned format.

## Existing systems and narrow repair

`CardAcquisitionAdapter` in `src/card_intelligence/acquisition.py` composes the existing canonical query, mechanical dossier and shared Decision Intelligence contracts. The shared numeric policy engine is unchanged. No provider, importer, canonical store, rules engine or strategic scoring system is added.

`CanonicalCollectionResolver` now reads the same canonical query projection. Its current view contains 384 production Cards and 913 production Printings plus 15 legacy seed Cards/Printings. Exact identities, physical-dimension conflicts, external-Identifier conflicts, explicit unknowns and compact provenance remain available. Collection snapshots bind the complete canonical query snapshot, including promoted state and lineage; previously retained snapshots are not rewritten.

The separate typed `CollectionService` path remains unchanged. The acquisition adapter reads source-bound, candidate-scoped ownership directly and does not call deck completion. The known mixed `any`/`exact` deck-allocation defect is explicitly excluded.

## Input and decision boundary

The immutable, content-identified `card-acquisition-input-v1` binds two or three distinct production Card/Printing candidates to retained source bytes. Whole-object JSON pointers must match those bytes, source metadata and mode must agree, and source paths cannot escape the declared source root. Real inputs require scoped human-reviewed source records; fixed-content Product READY attestations cannot authorize Card acquisition.

Required inputs include an explicit objective and objective identity, complete personal preference order, budget/currency and decimal precision, buyer destination/purchase/discount/order assumptions, hard constraints, desired quantities, acceptable Printings and dimensions, and complete ownership scope. Unknown ownership does not become zero. Duplicate lot identities are rejected; unacceptable copies do not satisfy a desired copy. Only one missing copy per candidate and independent complete orders are compared.

Offers must identify the exact Printing, seller, buyer-context content identity, condition, finish, language, currency, market, quantity and availability. Independent observation, retrieval and validity timestamps must satisfy the supplied freshness policy at the fixed evaluation time. Buyer identity alone cannot establish identical shipping or discount assumptions.

Unit price, shipping, taxes, fees and discounts require complete decimal-string amounts and an evidenced basis, including zeros. Integer monetary units preserve exact arithmetic: complete cost is the sum of charges less discounts; budget remainder is budget less complete cost. Unknown terms remain null and block a decision where critical. Negative totals, incompatible dimensions, missing evidence, contradictions, stale/future offers and unsupported constraints fail closed.

The versioned `collection-aware-card-acquisition` policy uses supplied personal priority followed by exact cost among known-eligible alternatives. Already-owned, unavailable, disallowed or unaffordable candidates remain in the full census with reasons. They do not become zero-cost alternatives. Personal priority is not a competitive-strength or suitability score. When objective eligibility is required, a source-bound scoped mechanical review must support it; pending functional-role proposals cannot supply approval.

The existing `DecisionRequest`, `DomainAnalysisEnvelope`, `DecisionPolicy`, recommendation and decision-reasoning-context contracts preserve provenance, blockers, supporting factors, counterarguments, uncertainty and change conditions. An unknown decision-critical input yields ABSTAIN. No purchase is executed and no role, fact, price or canonical entity is admitted.

## Reconstruction integrity repair

Reconstructing an acquisition dossier now requires its versioned `card-acquisition-reconstruction-v1` proof. This retains the original immutable input packet, exact acquisition-source UTF-8 bytes (or an explicit unavailable-source reason), original Decision request and analyses, and the minimal read-only canonical projections used by the adapter. Identical analysis fields are shared losslessly; each original Decision analysis is recovered by combining `analysis_shared` with its individual fields. No metrics or evidence are discarded.

The constructor verifies source digests and bindings, repeats the existing adapter's eligibility and exact monetary calculations, and replays the existing Decision orchestrator. It requires exact agreement with the retained request, analyses, recommendation and dossier projection. Recomputing the outer dossier hash cannot authorize a synthetic-to-real change, contradictory owned/desired/missing quantities, altered cost terms or units, an inconsistent budget remainder, or a different selected action. Real purchase-advice status still requires complete governed real inputs; the retained real assessment remains ABSTAIN.

These canonical projections reference the existing query snapshot and mechanical dossiers; they are not a separate canonical store or independent authentication of imported canonical facts. Source review remains the established human-review boundary. Pre-repair dossiers lacking the reconstruction proof are rejected and must be regenerated from their original retained inputs. The combined review dossier omits the duplicate proofs after validating each complete scenario output and records their identities and omission accounting. Its manual handoff and explanation builders also compare the supplied projection against a replay from the original retained pilot inputs before rendering.

## Demonstrations and retained review materials

The complete scenario is a fictional fixture. It supplies a 10.00 USD budget, one already-owned acceptable Ponder, and personal priority Ponder, Greater Good, Faithless Looting. Greater Good's fictional complete cost is 8.00 USD, leaving 2.00 USD. Faithless Looting's fictional complete cost is 2.00 USD. The synthetic result selects Greater Good because the supplied priority precedes price after excluding the owned Ponder. The cheaper alternative remains a counterargument. These amounts are not Scryfall observations or real seller offers.

The real-input assessment ABSTAINS. Actual buyer context, budget/currency, desired quantities, ownership, objectives, current offers, availability, transaction costs and necessary eligibility review are absent. The historical Scryfall prices remain unchanged and are never substituted for executable offers.

The [isolated review directory](../data/review/card-acquisition-pilot/) contains source/plan inputs, both packets, full validated scenario outputs, one combined acquisition dossier, a bounded manual reasoning-context handoff, a human-readable explanation and an integrity manifest. The combined dossier avoids repeating source and Printing payloads, accounts for omitted details and references the complete outputs. Existing mechanical and role dossier identities remain bound. All eight selected role candidates remain pending; the original fifteen-Card / thirty-candidate pilot is unchanged.

Canonical compact UTF-8 JSON and fixed input timestamps produce deterministic content identities and replay. JSON files and structured CLI output append exactly one LF. Complete structured delivery, including that LF, must fit 65,536 bytes; oversize output fails before writing, with no truncation. Full source bytes and original role payloads remain available through digest-bound references rather than repeated in the manual context.

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/build_card_acquisition_pilot.py --check
PYTHONPATH=src python -m card_intelligence.cli acquisition --input data/review/card-acquisition-pilot/packet-synthetic.json --source-root .
PYTHONPATH=src python -m card_intelligence.cli acquisition --input data/review/card-acquisition-pilot/packet-real.json --source-root . --reasoning-context
```

This is a manual ChatGPT handoff, without model execution or live integration. Explanations preserve the synthetic notice, real abstention, evidence states and policy. No competitive ranking, format-legality conclusion, net card-advantage claim, verified synergy, forecast or actual purchase advice is established.

## Protection and stop boundary

Canonical records, historical market observations/acquisitions, knowledge facts, previous demonstration artifacts and Architecture v12 remain protected. CC2 stays NOT_READY_FOR_EVALUATION; tournament acquisition remains parked. Full inventory management, mixed-policy deck allocation, deck optimization, provider acquisition/authentication, strategic scoring and purchase execution are excluded.

The next action is Project Manager review of this single pilot and its PR. No automatic merge, real-world evaluation, production admission or follow-on implementation occurs.
