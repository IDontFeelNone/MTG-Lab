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

The Phase 56 seed dataset is a deliberately small, maintainer-approved canonical
foundation backed by an official Source Record. The existing automated
candidate-promotion service remains limited to Product candidates. Adding Card
or Printing promotion requires a separately approved lifecycle increment; this
milestone does not bypass or broaden that service.
