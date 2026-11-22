# Real-Card Rules Reasoning V1

This read-only consumer answers one question: **under explicit declared ability
characteristics, does the activated-mana payment timing exception apply, and does
the same-ability unresolved-activation restriction prohibit reactivation?**

It derives classification rather than asking the caller to assert ACTIVATED_MANA.
It applies retained real Magic rules descriptors to original scenarios; it does
not identify or execute a real Card. An affirmative answer establishes this
conditional timing conclusion, not complete activation legality, actual mana
production, casting feasibility, deck strength or strategic usefulness.

## Evidence and authority

The existing metadata-only `card_rules_pilot.land_context.read_context` validates
the fixed six projection packages, their review records and artifact lineage.
Only the established 24-rule context enters admission; seven selected units
support this question. Neither Card/Printing records, historical Oracle text,
the blocked whole Scryfall acquisition nor the external CR TXT is read.

The exact context is
`sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478`,
bound to the retained September 25, 2026 release and artifact
`sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`.
Every assessment revalidates it. This is retained-metadata integrity verification,
not fresh source verification or a claim about current rules.

| Unit | Bounded contribution |
|---|---|
|605.1a|Conjunction of declared activated-mana criteria, considering self-replacements and disregarding other replacement effects for classification.|
|605.2|Current inability to produce mana alone does not remove classification.|
|605.3a|The four explicitly declared mana-payment opportunity categories.|
|605.3c|The same ability cannot be reactivated before that activation resolves.|
|606.2|Loyalty is determined by loyalty symbols in an activated ability's cost, rather than source type.|
|115.6|Zero chosen targets alone does not establish absent target requirements.|
|614.15|Self-replacement dependency; recognizing/applying one is outside V1.|

Reports bind each unit's exact rule, package, projection and source-anchor
identities. Original `PROJECTED_FOR_REVIEW` states remain unchanged; where a unit
has no review-state or execution-readiness field, the report preserves that
absence as null. Existing bounded, non-executing descriptor admission is not
human approval of arbitrary Card semantics or executable semantic closure.
Source-policy clearance remains `not_granted`, upstream permission observations
remain `NOT_ESTABLISHED`, and real-card execution remains `BLOCKED`.

## Inputs and inference

`real-card-rules-reasoning-input-v1` is a closed contract. See the original
[scenario](../tests/fixtures/rules_reasoning_v1/payment.json) and
[schema](../src/schemas/v1/real-card-rules-reasoning-input.schema.json).
All characteristics and state fields are required; UNKNOWN is explicit.

- Ability kind: ACTIVATED or UNKNOWN; TRIGGERED and SPELL are refused.
- Target requirement: NONE, PRESENT or UNKNOWN; chosen count: 0–16 or UNKNOWN.
- Potential mana, loyalty symbol in cost, source-is-planeswalker, cost/effect
  library movement: YES, NO or UNKNOWN.
- Self/other replacement presence: ABSENT, PRESENT or UNKNOWN.
- Payment request: ABSENT, UNKNOWN, SPELL_CASTING_MANA_PAYMENT,
  ABILITY_ACTIVATION_MANA_PAYMENT, RULE_REQUESTED_MANA_PAYMENT or
  EFFECT_REQUESTED_MANA_PAYMENT.
- Priority and same-ability-unresolved: YES, NO or UNKNOWN.
- Current output: ZERO, NONZERO or UNKNOWN.

The sample describes a targetless, potentially mana-producing, nonloyalty
activated ability with no library movement or self-replacement, a declared
spell-casting payment request, no priority, and no same-ability unresolved
activation. The result is `PAYMENT_TIMING_EXCEPTION_APPLIES`, even with ZERO
current output. The request's actual existence is not authenticated.

Changing chosen targets to 1 and target requirement to PRESENT excludes the
mana-specific exception. A declared loyalty symbol or library movement also
excludes it. Changing same-ability-unresolved to YES yields
`SAME_ABILITY_REACTIVATION_PROHIBITED`. Neither negative conclusion decides
unrelated permissions. ABSENT payment yields no payment-specific opportunity,
even when ordinary priority is available.

Unknown prerequisites yield `NEEDS_FACTS` with explicit gaps. PRESENT target
requirements with zero chosen targets remain unresolved: V1 cannot recognize
optional/conditional target procedures. A positive chosen count is a negative
witness; NONE plus a positive count is contradictory and refused. A present
self-replacement is refused; unknown self-replacement prevents classification.
Other replacements are disregarded only for classification and may affect actual
output. Source type is not a proxy for loyalty. Current output is not a proxy
for intrinsic potential.

The finite classifier feeds the existing pure
`mana_window.evaluate_propositions` conjunction evaluator for opportunity and
repeat findings. No existing Card-dependent admission factory is bypassed or
reused with fabricated Card evidence. Findings are conditional on caller facts.

## Python, CLI and replay

```python
import json
from pathlib import Path
from card_intelligence.rules_reasoning import load_rules_reasoner, CONTEXT_ID

consumer = load_rules_reasoner(review_root=Path('reference-reviews'),
                               expected_context_id=CONTEXT_ID)
request = json.loads(Path('tests/fixtures/rules_reasoning_v1/payment.json').read_bytes())
report = consumer.assess(request)
consumer.replay(report.to_json().encode())
```

```sh
PYTHONPATH=src python -m card_intelligence.rules_reasoning \
  --review-root reference-reviews \
  --expected-context-id sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478 \
  --json assess tests/fixtures/rules_reasoning_v1/payment.json
```

Omit `--json` for readable output; use `validate REPORT.json` for deterministic
reproduction. CLI files use canonical UTF-8 JSON with sorted keys, compact
separators and one trailing LF, following the existing contract utilities.
Input is limited to 8 KiB, reports to 64 KiB and target counts to 16; the fixed
metadata packages and finite rules bound work independently of catalog size.
No general text interpretation, recursive rule traversal or source acquisition
occurs. Invalid types, extra fields, unsupported versions/questions, mismatched
context identities and changed metadata fail closed. `RulesReasoningError`
contains a structured code and `as_dict()` refusal; CLI refusals use stderr and
exit 2. Valid positive, negative and missing-facts findings use exit 0.

Reports use `real-card-rules-reasoning-report-v1`, immutable owned bytes and an
exact domain/content report hash. Reopening/replay recomputes every field against
current retained metadata, rejecting stale inputs and altered results even if
rehash-consistent. It proves reproduction of the embedded declarations, not their
authenticity. API decoded views are independent and input objects are unchanged.

A future deck investigation could attach this conditional timing finding beside
a separate exact draw-access calculation. Combining them into a casting or
strategy probability would require additional verified mechanics, game-state
evidence, costs, procedures and explicit authorization. This milestone adds no
research integration, gameplay profile, source permission or canonical authority.
