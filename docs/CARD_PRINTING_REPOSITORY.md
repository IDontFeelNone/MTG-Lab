# Card and Printing Repository

**Status:** Implemented foundation

## Canonical Layout

Canonical Card and Printing records are game-scoped and stored at:

```text
data/canonical/games/<game>/cards/<card_id>/card.json
data/canonical/games/<game>/printings/<printing_id>/printing.json
data/canonical/games/<game>/sources/<source_id>.json
```

Each record is validated against its versioned JSON Schema. Every Printing must
reference a Card present in the same game repository. Every non-container
canonical field must be covered by field-level provenance that references a
schema-valid canonical Source Record.

## Stable Identifier Rules

Foundation identifiers are deterministic, lowercase, and repository-owned:

- Card: `<game>.<normalized-card-name>`
- Printing: `<game>.<normalized-set-code>.<normalized-collector-number>.<language>`

Normalization lowercases text, replaces runs of non-ASCII-alphanumeric
characters with one hyphen, and removes leading or trailing hyphens. Once a
canonical ID is reviewed and committed it remains stable even if a display name
or external provider identifier changes. Identifier collisions must be resolved
through explicit review rather than silently overwritten.

## Validation and Output

The repository loader performs structural validation, verifies identities
against canonical paths, validates source references and field coverage,
rejects duplicate identifiers, and rejects orphaned Printings. A deterministic
snapshot sorts entity paths and serializes JSON with sorted object keys and
fixed separators; it is derived output and does not replace canonical files.

## Review Boundary

The seed dataset remains deliberately small and backed by an official Source
Record. Card and Printing normalized candidates may now enter the generic
candidate-review service. The service enables entity types through explicit
repository definitions, while the shared workflow owns eligibility, approval,
rejection, conflict detection, audit storage, and rollback.

Card and Printing definitions were enabled through the generic service in
Phase 57, followed by Print Sheet and Slot definitions in Phase 60. Each
definition supplies its schema, canonical path, record validator,
and repository validator, allowing future entity types to reuse the workflow
without embedding their rules in its control flow. The existing Product facade
uses the same framework and remains backward compatible.

Promotion requires a schema-valid candidate marked `valid`, complete
candidate-field provenance, and an explicit approval. Canonical Card and
Printing validation additionally verifies canonical Source Records and field
coverage. A Printing can be promoted only after its Card exists. Rollback runs
repository validation and therefore refuses to remove a Card while a Printing
still references it.

## Mystery Booster 2 Wave 1

Phase 61 validates the complete bounded Card and Printing ingestion workflow
with three evidence-supported Mystery Booster 2 pairs. A content-identified
controlled evidence bundle combines separately attributed official Card
identity, community Printing identity, and official product-membership sources.
The deterministic pipeline retains parsed and candidate artifacts, promotes
Cards before Printings, and preserves six immutable approval audits. This wave
does not define a complete card pool or authorize Print Sheet or Slot data.

## Mystery Booster 2 Wave 2

Phase 63 requires the population workflow to enter through the Evidence
Repository. The application bridge loads and verifies the archived bundle,
selects one JSON artifact, checks every embedded Card, Printing, and membership
source against artifact provenance, and only then invokes the bounded
deterministic normalizer.

Review identifies Card candidates whose stable IDs already exist canonically;
those Cards are not promoted again, while a new Printing may still reference
the existing Card. The retained Wave 2 run adds one new Card and its Mystery
Booster 2 Printing in dependency order with two immutable approval audits. It
does not define a complete card pool or authorize product-rule data.
