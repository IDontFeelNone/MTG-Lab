# Functional comparison — pending human review

These are engineer-authored proposals tied to retained evidence. No human approval or canonical role admission has occurred.

Shared directly evidenced proposed roles: card_draw.

Compare proposed outcomes and explicit restrictions. No ranking, substitute verdict, net advantage, or verified interaction is computed.

## Ponder

Exact Card: `02090581-61aa-4348-ad57-451be8ee91c2`.

### card_draw — known; requires_review

Draw one card after the look/reorder/optional-shuffle instructions.

- costs: Card mana cost {U}.
- restrictions: Drawing one card is not a proven positive net-card-advantage claim.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:8ec840cb35c583e8678b1f2af81b606530c6f0c30252825c5ca23a930968ffb9`; `sha256:520679507ff35d784234c1c746e3daa09a04e460c48c33c6f39b40397374102b`.

Retained Oracle passage:

> Look at the top three cards of your library, then put them back in any order. You may shuffle.
> Draw a card.

### card_selection — known; requires_review

Look at the top three cards, reorder them, and optionally shuffle.

- costs: Card mana cost {U}.
- restrictions: Selection is limited to the top three before the optional shuffle.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:84d90ff35c540a13d477e9bb84a6b667feec72a2f999166c5880d447521a8f24`; `sha256:520679507ff35d784234c1c746e3daa09a04e460c48c33c6f39b40397374102b`.

Retained Oracle passage:

> Look at the top three cards of your library, then put them back in any order. You may shuffle.
> Draw a card.

## Faithless Looting

Exact Card: `3d6fa57a-aa53-4b5c-b8af-a7612c823117`.

### card_draw — known; requires_review

Draw two cards, then discard two cards.

- costs: Card mana cost {R}.
- restrictions: The discard-two instruction accompanies the draw-two instruction.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:49fd74b5770efe97a0478db980cd5373729749b3e492472975f2e0f0daa863f6`; `sha256:c2c032ccc36ec75de853c094a88b8fac46393036685626f78423f74f3c9f2833`.

Retained Oracle passage:

> Draw two cards, then discard two cards.
> Flashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

### card_selection — incomplete; requires_review

Draw/discard may support filtering the hand or placing useful cards in the graveyard.

The draw/discard outcome is literal; the value of filtering or graveyard placement depends on separately supplied cards and objectives.

- costs: Card mana cost {R}.
- restrictions: Two cards must be discarded.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- context dependency: Current hand, draw outcomes, graveyard utility and deck objective are not retained.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:d4a16a92b31055f4d50d8d1b32708ab8ab8ec299beae42023848eb52d150ddac`; `sha256:c2c032ccc36ec75de853c094a88b8fac46393036685626f78423f74f3c9f2833`.

Retained Oracle passage:

> Draw two cards, then discard two cards.
> Flashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

### recursion — known; requires_review

The retained flashback reminder permits casting this card from the graveyard for its flashback cost, then exiling it.

- costs: Flashback cost {2}{R}.
- restrictions: This permission concerns this card, not arbitrary graveyard cards.
- restrictions: The supplied reminder says to exile it afterward.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:1d6e9bbfc52ef02366c00b53c0bf2b3f90d90559fc309c8d1c2adc4e9a926513`; `sha256:c2c032ccc36ec75de853c094a88b8fac46393036685626f78423f74f3c9f2833`.

Retained Oracle passage:

> Draw two cards, then discard two cards.
> Flashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

## Greater Good

Exact Card: `dc0593c2-ccb4-4648-a592-c5bcd121dc72`.

### card_draw — known; requires_review

Draw cards equal to the sacrificed creature's power, then discard three cards.

- costs: Activation cost: Sacrifice a creature.
- conditions: The draw count depends on the sacrificed creature's power.
- restrictions: The discard-three instruction follows the draw.
- restrictions: A positive net-card-advantage result is not assumed.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:a0a97a3faae7eee971347619a5af874bc370ee6d0fdce7da6e26765bc079547e`; `sha256:dfee1e71560daf6c7971c453582a34f0d5af936405d050a2965b8f2dbebd7967`.

Retained Oracle passage:

> Sacrifice a creature: Draw cards equal to the sacrificed creature's power, then discard three cards.

### card_selection — incomplete; requires_review

The draw/discard sequence may support filtering or graveyard preparation.

The variable draw and discard-three sequence is direct; its selection value is a strategic interpretation.

- costs: Activation cost: Sacrifice a creature.
- restrictions: Three cards are discarded after the variable draw.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- context dependency: Creature power, hand contents, draw outcomes and the deck objective are absent.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:924fa9b36f24a9bc6bb2b00c62d72f6e3f4b7bd5c3bd32e0d4042311d34f1c32`; `sha256:dfee1e71560daf6c7971c453582a34f0d5af936405d050a2965b8f2dbebd7967`.

Retained Oracle passage:

> Sacrifice a creature: Draw cards equal to the sacrificed creature's power, then discard three cards.

### sacrifice_outlet — known; requires_review

Pay the sacrifice-a-creature activation cost to obtain the stated draw/discard effect.

- costs: Card mana cost {2}{G}{G}.
- costs: Activation cost: Sacrifice a creature.
- conditions: A creature is required to pay the activation cost.
- restrictions: The cost is a creature, not an arbitrary permanent.
- timing: No specific legal activation/casting window is established by this annotation; card type is supplied separately.
- limitation: Functional capability is not efficiency, net advantage, competitive strength, or verified rules interaction.

Evidence: `sha256:21cc8853dc94fd62f015c710dc2d9c31ce80f5288f419418caa8777611f025fd`; `sha256:dfee1e71560daf6c7971c453582a34f0d5af936405d050a2965b8f2dbebd7967`.

Retained Oracle passage:

> Sacrifice a creature: Draw cards equal to the sacrificed creature's power, then discard three cards.
