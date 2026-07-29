# Print Sheet and Slot Repository

**Status:** Implemented foundation

## Scope

This foundation implements the existing Tier 0 Print Sheet and Slot model. It
does not introduce new rule behavior, populate Mystery Booster 2 rules, or
implement probability, collation, or simulation.

## Canonical Layout

Canonical records are game-scoped and use stable identifiers:

```text
data/canonical/games/<game>/print_sheets/<print_sheet_id>/print-sheet.json
data/canonical/games/<game>/slots/<slot_id>/slot.json
```

Print Sheets contain positive integer weights for canonical Printing
references. Slots identify their game, reference one Print Sheet, declare a
positive draw count, and record replacement behavior. Every non-container
field is covered by provenance referencing a schema-valid canonical Source
Record.

## Validation

The repository validates structure, path identity, stable and duplicate
identifiers, source references, provenance coverage, and the complete
Card-to-Printing-to-Print-Sheet-to-Slot-to-Product graph. Cross-game references
fail because every relationship is resolved within the record's canonical game
repository. Duplicate Printing entries on one Print Sheet are rejected; their
multiplicity is represented by the existing positive `weight` field.

Empty Print Sheet and Slot collections are valid. Deterministic snapshots sort
canonical paths and serialize object keys consistently. They are derived
validation output rather than canonical source data.

## Promotion and Rollback

The generic candidate-review service enables `print_sheet` and `slot` through
explicit entity definitions. Promotion requires a schema-valid candidate
marked valid, complete candidate-field provenance, explicit approval, and a
valid canonical dependency graph. Decisions use immutable promotion audits and
retain idempotency, conflict protection, and write compensation.

Repository validation enforces dependency-safe rollback. A Printing cannot be
removed while a Print Sheet references it, a Print Sheet cannot be removed
while a Slot references it, and a Slot cannot be removed while a Product
references it.

## Population Boundary

Tests use temporary synthetic repositories and internal source records. No
synthetic Print Sheet or Slot is canonical project data, and this foundation
does not claim that the existing Mystery Booster 2 title fixture supports card
pool, weight, slot, replacement, probability, or collation facts.
