# Canonical Product Repository v1

## Purpose and boundary

`data/canonical/games/<game>/` is the authoritative, version-controlled source of
official game and product facts. It is deliberately separate from raw observations,
market snapshots, derived analytics, and simulations. Those systems may retain stable
canonical identifiers, but none may create, edit, or promote canonical records.

The Python boundary is `repository.canonical.CanonicalRepository`. Loading constructs
immutable domain values from `canonical.models`, validates every record, and validates
relationships before returning data. Consumers retrieve cards, printings, products,
and pack definitions through repository methods rather than opening JSON files.

## Layout

Each game owns a `game.json` and data directories for `cards`, `printings`, `products`,
`product_versions`, `treatments`, `finishes`, `rarities`, `packs`, `slots`, and `sheets`.
Existing evidence-backed card, printing, and product records retain their nested paths.
Small catalog and rule records are individual JSON objects in their named directory.
Product folders may include human/audit metadata plus pack and slot indexes; these
indexes are descriptive and are not observation data.

Relationships form this directed graph:

```text
Game -> Product -> ProductVersion -> PackDefinition -> PackSlot -> Sheet
                                                               -> SheetEntry -> Printing -> Card
Printing -> Rarity / Treatment / Finish
```

Identifiers are stable lowercase values. Repository construction rejects duplicate
identifiers, missing fields, malformed product definitions, and broken references in
sorted file order, producing repeatable failures. Loading is read-only.

## Observations and analytics

The observation importer asks the canonical repository for its card and printing
index. Verification writes a separate derived result containing canonical IDs; it does
not annotate canonical records. An unmatched observation remains unmatched rather
than manufacturing canonical data. Analytics may join those IDs to repository values,
but analytics outputs remain under derived-data storage and never feed back into this
repository.

## Canonical import pipeline

The explicitly reviewed pipeline stages source candidates outside `data/canonical`,
validates schemas and references, produces a deterministic report and provenance
audit, and promotes accepted records through the repository in one transaction. See
`CANONICAL_IMPORT_PIPELINE.md`. It does not consume user observations as official facts.

## v2 reconciliation

[`CANONICAL_CONTRACT_v2.md`](CANONICAL_CONTRACT_v2.md) supersedes the entity field
and layout details in this v1 implementation guide. Retained v1 records remain
immutable and are projected by the repository compatibility boundary.
