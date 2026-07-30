# Canonical Card, Printing, Evidence, and Uncertainty Contract (v3)

**Phase 80 · 2026-07-30 · Architecture v12 compatible additive extension**

## Pre-implementation assessment and decision

The Phase 79 review, v1 Card/Printing schemas and loaders, v2 composition contract,
typed models, source/evidence repositories, importer, mapping code, and schema
validator were reviewed before implementation. The gap is contractual rather than a
change to Architecture v12: immutable canonical JSON, source records, staged atomic
imports, and repository boundaries remain intact. An additive v3 contract and pure
compatibility projection solve the gap. No Tier 0 decision is required. No Mystery
Booster 2 population is included.

## Entity boundaries

A **Card** is rules identity: stable canonical/game IDs, names, layout and faces,
Oracle characteristics, legality references, and related-card relationships. A
**Printing** is one issued object: Card/set link, collector namespace, language,
rarity/classification, artist and flavor/printed text, physical presentation,
promotion/release data, provider IDs, and licensed image references. Printing text
is never filled from Oracle text. Set identity and collector number are Printing
facts. Face arrays retain multifaced and split semantics; applicable layouts require
at least two faces.

Fields omitted from a document are merely optional and absent from this record. They
do not claim that the real-world value is absent or unknown.

## Assertion evidence

Every v3 entity carries source assertions rather than duplicating the entity. An
assertion has a stable ID; subject and JSON-pointer-like field/relationship path;
value; source ID/type; evidence class; retrieval timestamp and optional publication
timestamp; confidence in `[0,1]`; verification and lifecycle statuses; notes; and
supersession/conflict links. Source IDs must resolve to retained Source Records.

Evidence classes, in descending default promotion priority, are: `official`,
`authoritative_structured`, `direct_observation`, `verified_community`, `derived`,
`inferred`, `unknown`, and `conflicting`. Classification describes the assertion,
not merely its source. Assertions are retained after rejection, supersession,
conflict resolution, or promotion.

## Uncertainty and partial knowledge

`KnowledgeValue` has six explicit states:

* `known`: a canonical value is present;
* `known_absent`: evidence establishes that no value exists;
* `unknown`: the value is not established;
* `provisional`: a supported value has not passed promotion;
* `conflicting`: supported claims disagree;
* `unresolved`: a relationship exists but its target/semantics are unresolved.

The `partial-collation` v3 schema applies these values to slot, sheet,
sheet-membership, and product-composition facts. It can therefore state that a slot
exists while replacement is unknown, a hypothesized sheet is incomplete, membership
is known while weight is unknown, or composition is partial—without manufacturing
simulation inputs. `simulation_required_paths` identifies semantics a consumer must
resolve. `require_simulation_facts` fails closed for omitted or non-`known` values.

## Promotion policy

Promotion is deterministic and auditable. Only verified/confirmed assertions not
rejected or superseded are eligible. Evidence class priority is applied first, then
confidence. Stable timestamp/source/assertion ordering removes input-order effects.
Equal-priority, equal-confidence disagreement has no winner and remains unresolved.
Unknown/conflicting assertions cannot be promoted. A rejected claim stays retained;
a superseding assertion links to what it replaces. The repository rejects two
promoted values on one path. Promotion never deletes source assertions.

## Validation

JSON Schema dispatches from `schema_version`. Closed v3 schemas reject misplaced
Oracle/printed fields, malformed face structures, invalid evidence classes/times,
missing assertion fields, and confidence outside `[0,1]`. Repository validation also
requires sources, complete field evidence, valid Printing→Card relationships,
unique collector numbers within set/language/declared namespace, and consistent
promoted facts. Existing graph validation continues checking entity references and
impossible concrete collation.

## Compatibility

Historical v1 Card/Printing and v1/v2 product files remain byte-for-byte untouched.
Pure `card_v3` and `printing_v3` adapters expose one immutable reconciled model.
Legacy names case-fold into `normalized_name`; absent layout becomes `normal`;
`set_code` projects to lowercase `set_id`; absent language becomes `und`; legacy
field provenance remains validated but does not invent v3 assertions. Unsupported
legacy metadata remains opaque and is not promoted into required semantics.

The importer accepts reviewed v1 or v3 local datasets. For v3 it preserves explicit
assertions, validates the prospective graph before atomic promotion, detects identity
and collector conflicts, remains hash-deterministic/idempotent, and reports per-kind
coverage plus assertion conflicts. It never performs network I/O.

## Examples

```json
{"status":"unknown","assertion_ids":["claim.slot.replacement"]}
```

This differs both from an omitted optional field and from:

```json
{"status":"known_absent","assertion_ids":["claim.no.flavor-text"]}
```

A simulation requiring `/replacement` must reject the first. Analytics may display
it as unresolved, while an importer may retain the supporting assertion without
promoting a Boolean guess.

## Downstream requirements

Consumers use the reconciled typed repository rather than reading version-specific
files. They must preserve Oracle/printing separation, inspect knowledge status, and
fail closed whenever required simulation semantics are absent, unknown, provisional,
conflicting, or unresolved. Inference may create an `inferred` assertion, but may not
silently turn it into canonical fact.
