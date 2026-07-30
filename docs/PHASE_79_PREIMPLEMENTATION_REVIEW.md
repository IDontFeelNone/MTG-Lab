# Phase 79 — Mystery Booster 2 Canonical Dataset Pre-Implementation Review

> **Status: Blocked** — completed 2026-07-30 before any dataset or importer
> implementation. Architecture v12 is unchanged.

## Decision

Phase 79 must stop at the pre-implementation gate. The existing canonical contract
cannot faithfully express several required card/printing facts or an explicitly
unknown collation state, and the canonical importer cannot write Canonical Contract
v2 product graphs. Proceeding would require either arbitrary metadata, loss of
provenance distinctions, or unsupported concrete collation values. Each is prohibited
by the milestone.

No source fixture was acquired, no canonical record was promoted, and no MB2
collation claim was added. Resolving these limitations requires a separately approved
contract/importer change; that would conflict with the instruction that Architecture
v12 remain frozen unless the change is first reviewed as compatible.

## Repository inventory

### Canonical MB2 data already present

| Area | Present state | Review finding |
| --- | --- | --- |
| Product | One `mystery_booster_2` v1 foundation Product | Valid retained identity; empty composition is intentional |
| Cards | Four MB2-associated identities: Abzan Falconer, Academy Manufactor, Ad Nauseam, and Adarkar Windform | Names only; requested rules/card metadata is absent |
| Printings | Four MB2 Printings, collector numbers 1–4 | Set code, collector number, rarity, language, and product-membership metadata present |
| ProductVersions | None | Missing for Phase 79 composition |
| PackDefinitions | None | Missing; retained product-local `packs.json` is an empty legacy placeholder/index |
| PackSlots | None | Missing; retained product-local `slots.json` is an empty legacy placeholder/index |
| PrintSheets / SheetEntries | None | Correctly absent because retained evidence does not establish them |
| Sources | Seven game-level Source Records, including official Wizards, Scryfall, Gatherer, and retained MB2 bundle records | Existing sources cover only the bounded assertions already promoted |
| Observations | README/infrastructure only; no canonical promotion source | Correctly isolated from canonical truth |

The canonical repository totals 15 Cards and 15 Printings, of which four Printings
are MB2. No duplicate MB2 canonical IDs or collector numbers exist in the populated
four-record subset. The requested complete expected count is not encoded anywhere as
a reviewed canonical invariant.

### Duplicate, conflict, placeholder, and completeness findings

* The four MB2 Printings and their four Cards are unique and internally linked.
* Their source split is deliberate, not a conflict: card identity/name uses the
  retained Gatherer source; exact printing fields use the retained Scryfall source;
  product membership uses a retained official-gallery Source Record.
* `products/mystery_booster_2/packs.json` and `slots.json` contain empty arrays but are
  not loaded as canonical v2 entity records. They are legacy placeholders and must not
  be mistaken for known empty real-world composition.
* The Product is explicitly a `foundation` v1 record with no slots. Its note says that
  card list, sheets, slots, collation, and probabilities are intentionally absent.
* Existing MB2 Cards lack mana cost, color identity, type line, Oracle/printed text,
  and external identifiers. Existing MB2 Printings lack finish and artist, and have
  no first-class treatment or external-mapping fields.
* Historical raw, candidate, review, and promotion artifacts intentionally duplicate
  assertions across lifecycle stages; they are not competing canonical records.

## Architectural fit assessment

### Blocking contract limitations

1. **Card and Printing fields are not representable.** The closed v1 Card schema has
   no mana cost, color identity, type line, Oracle text, or printing-specific text.
   The closed v1 Printing schema has no finish, artist, external identifiers, or
   printing-specific text. `metadata` is technically open, but Phase 79 explicitly
   forbids using arbitrary metadata when the model cannot express an important
   distinction. Canonical Contract v2 only upgraded Product/composition entities; it
   did not provide Card or Printing v2 schemas.
2. **Unknown collation cannot be represented as a canonical partial instruction.** A
   v2 PackSlot requires a concrete Sheet reference, positive draw count, and Boolean
   replacement value. A v2 Sheet requires at least one positively weighted Printing.
   Consequently, “slot known but pool/replacement unknown” and “membership known but
   weights unknown” cannot be serialized without inventing an authoritative value.
3. **Assertion class and confidence are under-specified.** Source Records classify an
   entire source as official, community, inferred, or internal and give it one
   verification status. Field provenance identifies a source and claim, but cannot
   independently label each assertion as official fact, reliably derived fact,
   community claim, inferred hypothesis, or unknown, nor attach assertion-level
   confidence. Mixing claim classes from one source would lose the milestone's
   required distinction.

### Blocking importer limitations

1. The importer accepts only dataset `schema_version: v1`; Phase 79 must produce new
   product/composition entities using Canonical Contract v2.
2. Its ProductVersion input contract requires legacy `pack_definition_ids`, whereas
   v2 requires typed `components`; it also does not construct all required v2 `game`
   and field-provenance values.
3. For Cards and Printings it replaces source-level field provenance with one generic
   dataset source, so it cannot retain multiple assertion sources/classes from a
   normalized MB2 fixture.
4. Validation rejects duplicate IDs but does not validate uniqueness of collector
   numbers within a set/language/treatment namespace, external mapping uniqueness,
   complete expected MB2 count, metadata coverage, or unsupported collation claims.
5. The import report contains aggregate create/update/unchanged counts only; it is not
   the required MB2 coverage and unresolved-data report.

The repository's staged prospective-graph validation, atomic application, stable JSON
serialization, local-only adapters, dataset fingerprint, dry-run, and validation-only
behavior are reusable. They are insufficient without changing the contracts above.

## Required resolution before implementation

A reviewed follow-up must decide, without embedding MB2-specific behavior:

* first-class, versioned Card and Printing fields (including the distinction between
  Oracle and printing-specific text) and external identifiers;
* an assertion-level provenance vocabulary that represents official, derived,
  community, inferred, and unknown claims plus supported confidence/evidence;
* a canonical way to preserve partial/unknown composition without fabricating Sheet,
  weight, replacement, or probability values; and
* a v2-capable deterministic importer and validators for collector namespaces,
  external mappings, coverage, and unsupported-claim rejection.

After those decisions are approved, Phase 79 must repeat this inventory against the
then-current tree before acquiring checked-in normalized inputs. No merge of a later
dataset should be recommended until its GitHub Actions run is green.
