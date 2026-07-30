# Canonical Contract v2

**Status:** Approved Phase 78 reconciliation  
**Architecture:** Architecture v12 (unchanged)

## Authority and compatibility

The JSON schemas in `src/schemas/v2/` and the immutable values in
`canonical.models` jointly express the single downstream canonical contract.
`CanonicalRepository` is its read-only boundary. New records use `schema_version:
"v2"`; validation selects the declared version. Retained v1 files are never
rewritten. A pure compatibility adapter projects them into v2 values, so consumers
see one model and cannot distinguish storage generations except through metadata.

Every entity has a stable lowercase identifier, a game-scoped relationship path,
field provenance in serialized form, and optional metadata. Foundation or draft
records may be incomplete where stated. Validated graphs fail closed before use.

## Product

**Purpose.** Stable marketing identity for a sealed product across configurations.

**Required:** `schema_version`, `id`, `game`, `name`, `product_type`,
`lifecycle_status`, `version_ids`, `provenance`. **Optional:** `metadata`.
`lifecycle_status` is `foundation`, `draft`, `validated`, or `deprecated`.
`version_ids` is a unique set of ProductVersion references. A validated Product has
at least one version; foundation and draft records may have none. A Product does not
directly own slots in v2.

## ProductVersion and ProductComponent

**Purpose.** A concrete, composable configuration of a Product. It requires
`schema_version`, `id`, `game`, `product_id`, `name`, `components`, and `provenance`;
`metadata` is optional. `product_id` references exactly one same-game Product.

A ProductComponent is an immutable value inside `components`, not an independent
entity. It requires `component_type`, `component_id`, and a positive integer
`quantity`. Type `pack_definition` references a PackDefinition; type
`product_version` references another ProductVersion. This recursive relationship
models pack, box, case, bundle, and future sealed composition without naming those
concepts in engine logic. The complete ProductVersion graph must be acyclic. A
validated version has at least one component; foundation and draft graphs may be
incomplete. Component array order is canonical output order, not selection order.

## PackDefinition

**Purpose.** Defines one generated pack as an ordered sequence of slot instructions.
It requires `schema_version`, `id`, `game`, `product_version_id`, `name`, `slot_ids`,
and `provenance`; `metadata` is optional. `product_version_id` references its owning
ProductVersion. `slot_ids` is a non-empty, duplicate-free ordered array of PackSlot
references. Reusing a PackSlot across definitions is permitted.

## PackSlot

**Purpose.** Defines repeated draws from one weighted Sheet. It requires
`schema_version`, `id`, `game`, `name`, `print_sheet_id`, positive integer
`draw_count`, boolean `replacement`, and `provenance`; `metadata` is optional.

`replacement: true` means every draw uses the full weighted Sheet. `false` means the
selected physical weighted entry is unavailable for later draws in the same slot
execution. Thus weights are multiplicities for no-replacement draws, and
`draw_count` may not exceed total Sheet weight. Replacement state resets for each
new slot execution. Slots contain no product-specific conditions.

## Sheet and SheetEntry

**Purpose.** A Sheet is a named, game-scoped weighted population. It requires
`schema_version`, `id`, `game`, `name`, a non-empty `entries` array, and
`provenance`; `metadata` is optional. Each SheetEntry requires `printing_id` and a
positive integer `weight`. `printing_id` references one same-game canonical Printing.
Printing IDs are unique within a Sheet; weights express relative multiplicity, not an
inferred probability or reconstructed physical print sheet.

## Relationship and composition validation

```text
Product -> ProductVersion -> ProductComponent --+-> PackDefinition -> PackSlot
                                                 |                       -> Sheet
                                                 +-> ProductVersion          -> SheetEntry -> Printing
```

Loading rejects missing or duplicate IDs, cross-game references, unknown component
types, non-positive quantities/weights/counts, empty validated compositions, empty
packs or sheets, impossible no-replacement draws, and ProductVersion cycles. All
validation completes before the repository is exposed.

## Versioning and v1 migration

Versions identify serialized contracts, not simulator versions. Writers must emit v2
for these six entities. Readers dispatch from `schema_version`; an explicit version
remains available for controlled validation. The compatibility projection is:

* v1 `print_sheet_id`, `draw_count`, and `replacement` map directly to v2 PackSlot.
* Older typed `sheet_id` and `count` map to those same fields; absent replacement is
  treated as `true`, preserving its historical draw behavior.
* A v1 Product with `slot_ids` becomes a deterministic synthetic ProductVersion and
  one PackDefinition, each marked `compatibility_source: v1`; no source file changes.
* A foundation v1 Product with no slots and no versions remains an incomplete v2
  Product with no versions.
* Existing explicit typed ProductVersion pack references become quantity-one
  `pack_definition` components.
* Nested schema-backed `print_sheets`/`slots` and retained flat typed directories are
  both read, then normalized into the same immutable values.

The adapter is a transitional read boundary. Downstream code must use
`CanonicalRepository`, never v1 document shapes. Migration of retained bytes is not
required and must occur only through a separately reviewed canonical promotion.

## Scope

This contract supplies canonical composition and selection instructions only. It does
not implement simulation, probability inference, print-sheet reconstruction,
analytics, observations, market pricing, or product-specific rules.
