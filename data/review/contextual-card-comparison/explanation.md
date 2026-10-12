# Contextual Card comparison — manual explanation example

Comparison: `sha256:ec7bdc86116d2e6f6a0467ef60e19b962c51ccf41b57fc40895aa25ed707241b`. Human review is pending; no canonical admission or live ChatGPT integration.

## Declared hypothetical context

A blue/red/green casual test shell is exploring card access and optional hand/graveyard preparation. These are comparison alternatives, not equivalent slots or a real competitive list. Initial casting, later recasting and permanent activation are separate routes.

Objective: Compare resource requirements and card-access trade-offs for a hypothetical casual test shell; abstain from choosing a Card while suitability and human role review remain unverified.

- Supplied assumption: Hypothetical blue/red/green casual testing shell; no submitted decklist or sanctioned format is represented.
- Supplied assumption: For instruction-count arithmetic only, suppose the described effect resolves and the stated draw/discard instructions can be followed; this does not verify a legal game state.
- Supplied assumption: For the Greater Good illustration only, suppose an available creature has power four at the relevant determination; availability, expendability and rules timing are unverified.

## Ponder

Exact production Card: `02090581-61aa-4348-ad57-451be8ee91c2`.

Source-verified provider assertions: mana cost `{U}`, mana value `1`, type `Sorcery`.
Source observation: `2026-08-02T09:09:45.851000Z`; retrieval: `2026-08-02T15:34:06Z`.

Retained Oracle text:

> Look at the top three cards of your library, then put them back in any order. You may shuffle.
> Draw a card.

Pending functional interpretations:

- card_draw (known; requires_review): Draw one card after the look/reorder/optional-shuffle instructions.
  - costs: Card mana cost {U}.
  - restrictions: Drawing one card is not a proven positive net-card-advantage claim.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- card_selection (known; requires_review): Look at the top three cards, reorder them, and optionally shuffle.
  - costs: Card mana cost {U}.
  - restrictions: Selection is limited to the top three before the optional shuffle.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.

Unverified strategic hypothesis: Top-three ordering may help an immediate card-access objective if the revealed options matter.

Counterargument: The actual library, draw outcome and desired options are unknown; ordering is not a guaranteed favorable result.

Evidence: `sha256:520679507ff35d784234c1c746e3daa09a04e460c48c33c6f39b40397374102b`; pending dossier `sha256:24efbe75670d139ca3463afb240415db35930c293dba97be9b92aa6cbc9647a4`.

## Faithless Looting

Exact production Card: `3d6fa57a-aa53-4b5c-b8af-a7612c823117`.

Source-verified provider assertions: mana cost `{R}`, mana value `1`, type `Sorcery`.
Source observation: `2026-08-02T09:09:45.851000Z`; retrieval: `2026-08-02T15:34:06Z`.

Retained Oracle text:

> Draw two cards, then discard two cards.
> Flashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

Pending functional interpretations:

- card_draw (known; requires_review): Draw two cards, then discard two cards.
  - costs: Card mana cost {R}.
  - restrictions: The discard-two instruction accompanies the draw-two instruction.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- card_selection (incomplete; requires_review): Draw/discard may support filtering the hand or placing useful cards in the graveyard.
  - costs: Card mana cost {R}.
  - restrictions: Two cards must be discarded.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- recursion (known; requires_review): The retained flashback reminder permits casting this card from the graveyard for its flashback cost, then exiling it.
  - costs: Flashback cost {2}{R}.
  - restrictions: This permission concerns this card, not arbitrary graveyard cards.
  - restrictions: The supplied reminder says to exile it afterward.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.

Unverified strategic hypothesis: The draw/discard sequence and later flashback access may suit a graveyard-tolerant hand-filtering plan.

Counterargument: Card selection is a pending incomplete role; the actual hand, discarded cards, graveyard utility and recasting opportunity are unknown.

Evidence: `sha256:c2c032ccc36ec75de853c094a88b8fac46393036685626f78423f74f3c9f2833`; pending dossier `sha256:c75770179c25379acfa6babda8c20843a30cbb5ae049a2d062fb9cbb0bc3c91e`.

## Greater Good

Exact production Card: `dc0593c2-ccb4-4648-a592-c5bcd121dc72`.

Source-verified provider assertions: mana cost `{2}{G}{G}`, mana value `4`, type `Enchantment`.
Source observation: `2026-08-02T09:09:45.851000Z`; retrieval: `2026-08-02T15:34:06Z`.

Retained Oracle text:

> Sacrifice a creature: Draw cards equal to the sacrificed creature's power, then discard three cards.

Pending functional interpretations:

- card_draw (known; requires_review): Draw cards equal to the sacrificed creature's power, then discard three cards.
  - costs: Activation cost: Sacrifice a creature.
  - conditions: The draw count depends on the sacrificed creature's power.
  - restrictions: The discard-three instruction follows the draw.
  - restrictions: A positive net-card-advantage result is not assumed.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- card_selection (incomplete; requires_review): The draw/discard sequence may support filtering or graveyard preparation.
  - costs: Activation cost: Sacrifice a creature.
  - restrictions: Three cards are discarded after the variable draw.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- sacrifice_outlet (known; requires_review): Pay the sacrifice-a-creature activation cost to obtain the stated draw/discard effect.
  - costs: Card mana cost {2}{G}{G}.
  - costs: Activation cost: Sacrifice a creature.
  - conditions: A creature is required to pay the activation cost.
  - restrictions: The cost is a creature, not an arbitrary permanent.
  - timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.

Unverified strategic hypothesis: A creature-supported draw/discard option may suit a plan that can afford its setup and creature sacrifice.

Counterargument: Creature availability and opportunity cost are unknown; a power-four illustration does not prove net card advantage, repeatability or favorable deck suitability.

Evidence: `sha256:dfee1e71560daf6c7971c453582a34f0d5af936405d050a2965b8f2dbebd7967`; pending dossier `sha256:4bfd0b3e1d7dac0a21774d8faa5cc38c3b3b37aa24aef14b80dd8f19962497c0`.

## Deterministic descriptions and conditional arithmetic

- Ponder / Faithless Looting: `left_minus_right_mana_value` = `0` (known, mana_value). Mana value is not actual payment, castability, total resource cost, or universal efficiency.
- Ponder / Greater Good: `left_minus_right_mana_value` = `-3` (known, mana_value). Mana value is not actual payment, castability, total resource cost, or universal efficiency.
- Faithless Looting / Greater Good: `left_minus_right_mana_value` = `-3` (known, mana_value). Mana value is not actual payment, castability, total resource cost, or universal efficiency.
- Ponder: `draw_count_minus_mandatory_discard_count` = `1` (known, instruction_count_difference). Conditional on the pending literal annotation and supplied illustration. Not net card advantage: casting-card expenditure, creature sacrifice, setup, resolution, hand/library availability and opportunity cost are excluded.
- Faithless Looting: `draw_count_minus_mandatory_discard_count` = `0` (known, instruction_count_difference). Conditional on the pending literal annotation and supplied illustration. Not net card advantage: casting-card expenditure, creature sacrifice, setup, resolution, hand/library availability and opportunity cost are excluded.
- Greater Good: `draw_count_minus_mandatory_discard_count` = `1` (known, instruction_count_difference). Conditional on the pending literal annotation and supplied illustration. Not net card advantage: casting-card expenditure, creature sacrifice, setup, resolution, hand/library availability and opportunity cost are excluded.

## Unknowns and abstention

- Human approval of role definitions and all eight selected role candidates.
- Actual hand, library contents, creature availability, power determination and graveyard utility.
- Colored mana access, casting opportunity, setup expenditure and legal activation/casting windows.
- Opportunity cost of losing a creature or a Card, repeatability, interaction and net card advantage.
- Format legality, real deck suitability, competitive results, combo strength and substitute equivalence.

Existing Decision Intelligence outcome: **ABSTAIN**. No Card is selected.

- required_metric_unknown:02090581-61aa-4348-ad57-451be8ee91c2:human_reviewed_context_match
- required_metric_unknown:3d6fa57a-aa53-4b5c-b8af-a7612c823117:human_reviewed_context_match
- required_metric_unknown:dc0593c2-ccb4-4648-a592-c5bcd121dc72:human_reviewed_context_match

This example preserves the mechanical / pending-interpretation / supplied-assumption boundary. It cannot establish net card advantage, format legality, a superior choice or a verified interaction.
