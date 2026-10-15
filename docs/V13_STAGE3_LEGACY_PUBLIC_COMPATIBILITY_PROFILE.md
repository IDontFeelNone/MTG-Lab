# V13 Stage 3 — Legacy/Public Compatibility Snapshot Profile

Status: separately owner-authorized implementation, pending independent Project
Manager inspection. Architecture v13 remains ACTIVE APPROVED; Decision 017 is
Accepted. This stage implements only the non-production Tier A scope authorized
by the [permission and closure contract](V13_LEGACY_PUBLIC_PERMISSION_CLOSURE.md),
merged in PR #178. It establishes no data-processing or use permission.

Reviewed implementation base: `e63b5ca54d6cef0425c39fe8cc05c79720dc9c03`.
The Stage 2 review, its historical baseline and the permission matrix remain
unchanged. No provider corpus is copied, reformatted, exported or newly bundled.

## Explicit public API

```python
from pathlib import Path

from collection.intelligence import CanonicalCollectionResolver
from query import CanonicalQueryEngine
from repository.legacy_profile import attach_legacy_compatibility

# Select the expected identity from reviewed configuration, independently of the
# requested file. There is no "latest", root discovery or permission upgrade.
catalog = attach_legacy_compatibility(
    Path("/explicit/existing-checkout"),
    control_path="config/catalog_profiles/legacy-public-tier-a.json",
    game="magic",
    expected_profile_id=(
        "sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e"
    ),
)
query = CanonicalQueryEngine.from_attachment(catalog)
resolver = CanonicalCollectionResolver.from_attachment(catalog)
snapshot = query.snapshot()
outer_binding = query.catalog_binding
```

The handle exposes read roots and fresh copies of authored control metadata. It
does not import, write, admit, activate, publish or acquire anything. Existing
query/repository loaders and Collection resolution implement the reads; no second
query engine or temporary catalog tree is constructed. Collection imports remain
separate caller inputs. Resolution retains its existing priority and uncertainty;
an alias or name match is not new physical-Printing evidence or ownership.

`repository.legacy_profile` implements the separate
**legacy-public-compatibility-v1** contract. Stage 1's
**canonical-snapshot-fictional-v1** remains unchanged and does not accept the
mixed representation. Existing direct constructors and the explicit unrestricted
`attach_legacy_public` profile retain their original behavior.

## Control metadata and distinct identities

`config/catalog_profiles/legacy-public-tier-a.json` contains authored metadata:
relative paths, exact SHA-256/byte-length bindings, placement, namespace and
absence inventories, counts, capabilities and fixed authority limits. It contains
no copied entity values, source assertions or provider payload. The explicit
roots are `data` and `data/canonical/games`, relative to the selected checkout.

| Identity | Reviewed value and scope |
| --- | --- |
| `profile_id` | `sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e`; complete authored control document, excluding only its own fixed ID field |
| `closure_id` | `sha256:2d5241a2c03a07bb435a60ae0a9457b6795fa6bee511a38721bcce250c4950c7`; sorted selected file bindings and placement |
| `query_snapshot_id` | `sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`; the existing query result serialization/hash, unchanged |
| Historical whole-canonical pre-state | `881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077`; informational reference to all 52 historical canonical files, not a Tier A certification |
| Bare legacy query snapshot | `sha256:e580c987f4e7cae0c0a69e22dc025e468ceacef078a4ff907935c1d54998fa6e`; unchanged 32-entity default-root behavior |

Profile and closure IDs use SHA-256 over compact, sorted-key UTF-8 JSON,
`ensure_ascii=False`, no trailing newline. Their domain wrapper is
`{"domain":"mtg-lab:legacy-public-compatibility-v1:<domain>","value":...}`,
where the domains are respectively `control` and `closure`. File hashes bind
exact retained bytes, including newlines. Root location is not an identity input.
There are no arbitrary caller-selected exclusions. These IDs neither redefine
the query snapshot nor claim Stage 1 release/content/source/validation identities.

Attached query readers expose `catalog_binding` separately. Attached Collection
results expose `catalog_attachment`; their existing `canonical_snapshot_id` and
canonical references continue to bind the query snapshot.

## Exact in-place Tier A closure

The selected capability is **CATALOG_QUERY_COLLECTION**. Its 40 files are taken
exactly from `tiers.A.files` in the merged permission/closure packet:

| Placement | Count | Meaning |
| --- | ---: | --- |
| `CORE_CATALOG_CONTENT` | 33 | 32 typed Game/Card/Printing/Product files and promoted `data/canonical/state.json` |
| `SOURCE_EVIDENCE_REFERENCE` | 5 | Selected global SourceRecords referenced by the typed catalog; references, not upstream provider archives |
| `AUDIT_CONTEXT` | 2 | Existing bounded-promotion context required for current entity-local provenance |

Only these two audits are available to the attached reader:

- `data/audit/bounded_promotions/phase-119-mb2-batch-000001-e32022126c07.json`
- `data/audit/bounded_promotions/phase-136-mtgjson-pilot-30786023976-1.json`

They are audit context, not canonical entities, admission authority, an owner
decision or source-policy clearance. The other 28 audit files may remain present
but are not read by this attachment. Of eight SourceRecords in the broader census, only the five
selected bindings may be opened. Seven SourceRecords are global and the eighth
is product-local: two unselected global names are bound in the source namespace
inventory solely to detect scope expansion; the product-local SourceRecord and
its acquisition sidecars are outside the reader surface. None of these excluded
bytes is read, verified or promoted into the closure.

The bounded inventory is injected into the existing canonical repository, Card
and Product loaders and query reader. It filters both discovery and direct reads.
Selected bytes are hash-checked; an unselected direct read is rejected. Ordinary
unrestricted constructors retain their original scanning behavior.

## Namespace, integrity and failure boundary

The control document binds one game namespace and every currently scanned entity
namespace, including empty ones: Cards, Printings, Products, identifiers, Finishes,
treatments, rarities, product versions, packs, slots and both sheet layouts.
It pins `data/canonical/knowledge/state.json` **ABSENT**. Derived
`data/knowledge/facts/` is not a substitute or an included domain.

Attachment verifies the selected closure before reader construction. Attached
operations reverify control identity, selected bytes, namespace membership and
bound absences. Reader roots and read inventory cannot be retargeted silently.
Query construction also checks the expected query identity and entity census.

Missing/changed dependencies, new selected-namespace files, an additional game,
new optional knowledge state, changed audit/SourceRecord bindings and altered
control identities block. Duplicate JSON keys, non-finite values, malformed scope,
unsupported versions, absolute/traversal/backslash paths, ambiguous/case-fold
collisions and selected symlinks are rejected. Metadata contains only the
supported integer/string/boolean values; finite fractional values in existing
catalog bytes retain their existing query semantics.

`SnapshotError.as_dict()` provides a structured `status=blocked`, error code and
safe relative path/message. Loader errors in the bounded path are sanitized;
source values and sensitive absolute roots are not included in diagnostics.
There is no network access, provider lookup, archive extraction or fallback to
current, historical, cache or unrestricted legacy data. A failed selected
attachment remains failed.

These checks are read-side integrity controls, not an OS sandbox, authentication
service or filesystem transaction. They do not claim protection against a
malicious concurrent writer changing and restoring bytes between observations.
The caller must preserve the selected read-only files for the operation.

## Capabilities and failure before excluded I/O

Tier A supports entity lookup/listing/search/snapshot, ordinary catalog
relationships, aliases, selected entity provenance, entity-local
unknown/conflicting/unresolved/superseded states, Collection identity resolution
and corresponding entity-local semantic queries.

The following require **FULL_QUERY_AUDIT**, which this profile cannot grant:

- `related(..., "promotion_audits")` and full promotion-history inspection;
- `validation("rejected")` and `validation("validation_failure")`;
- aggregate validation analytics and semantic `validation_statistics`;
- semantic `list_validation` for rejected or validation-failure history.

The query/semantic/analytics boundary checks these capabilities before snapshot
verification or audit I/O. It raises `unsupported_capability`; it does not return
an empty result that implies complete rejected-history coverage. Historical
admission validation/source replay is also unsupported. Explicit
`catalog.require_capability("historical_admission_replay")` fails before any
historical dependency is opened. No Tier B or Tier C implementation is added.

## Current-public compatibility result

The already-tracked current catalog was inspected **in place**, using the
explicit both-root target, without creating a new real-data snapshot or bundle:

| Entity type | Promoted | Typed | Total |
| --- | ---: | ---: | ---: |
| Card | 384 | 15 | 399 |
| Printing | 913 | 15 | 928 |
| Identifier | 235 | 0 | 235 |
| Finish | 2 | 0 | 2 |
| Game | 0 | 1 | 1 |
| Product | 0 | 1 | 1 |
| **Total** | **1,534** | **32** | **1,566** |

Observed query identity equals the expected `sha256:7cee417d...bb437a7` value
listed above. Typed-first precedence remains exact on `(entity_type, ID)`;
current typed/promoted Card and Printing overlap is zero. Existing aliases,
relationships, languages, uncertainty and entity provenance remain unchanged.

The bare constructor's 32 entities and separate identity remain legacy
path-inference behavior. Stage 3 does not fix or redirect its roots. A deliberately
expanded writer output invalidates this fixed baseline profile; tests characterize
that rejection rather than relabeling an old catalog as current or repinning IDs.

## Explicit limitations and permission state

The profile cannot be switched to production mode. Its fixed authority metadata
is:

- `production_eligible=false`
- `approval_state=not_granted`
- `source_policy_clearance=not_granted`
- `data_processing_permission_established=false`

All seven complete mixed-content operation statuses remain **NOT_ESTABLISHED**:
local private processing, private operator retention, existing-public-Git
compatibility permission, new redistribution, free public service, commercial
service and AI/model export. Integrity, public availability, existing Git history,
notices or private storage do not establish those permissions. This implementation
does not update the permission matrix, notices or `SOURCE_POLICY_CLEARED_PLANS`.

Known incompleteness is preserved: 21 signed and nine etched unresolved Finish
references; incomplete typed materialization; Product identity with zero slots
and unsupported contents/collation; unsupported gameplay rules; mechanical
evidence outside Tier A; absent optional canonical knowledge state. No missing
Finish, slot, rule, mechanical fact or physical-copy verification is invented.

Market evidence, derived Card/Product/Decision Intelligence, reasoning contexts,
personal collection data, pending candidates, provider archives and credentials
are outside the profile. The MB2 810 recommendation and nine multiface holds stay
pending and unadmitted; owner spelling proposals remain unapplied. No writer,
admission/OIDC, publication, rollback or projection authority is changed.

## Public tests and preservation

New generic tests use original fictional mixed catalogs: typed plus promoted
records, selected source references/audits, an excluded audit, aliases,
relationships, empty namespaces and separate fictional Collection input.
Relocation of identical fictional bytes preserves profile/closure/query identities
and results; selected-byte changes block. Excluded audit/source sentinels and
pre-I/O capability tests exercise the negative read boundary. Public tests need
no credentials, private mount, protected dataset or network.

Focused and full-suite results, exact tested revision, the separate real
expanded-writer publication regression and hosted CI state are reported in this
milestone's PR. Test execution is not source permission or admission approval.
The established `data/test-evidence/` rehearsal namespace retains its explicit
test/replay classification; arbitrary new inspection families remain fail-closed.

Original public canonical bytes, selected audits, SourceRecords, Stage 2 and
permission/closure packets, MB2 pending inputs and historical fixtures remain
unchanged. Card Acquisition replay continues binding its original Architecture-v12
auxiliary dependency and protected identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

## Next candidate — NOT AUTHORIZED

**Tier B Audit-Context Capability Design Review** is the smallest next candidate.
It would determine whether additional audit consumers need a separately scoped,
integrity-bound context and explicit permission/authority limits. It is a review
candidate, not authorization to implement Tier B, expand this closure or select a
production snapshot. Production remains blocked on operation-complete permission
evidence and a future explicit owner decision. SQL, composition, Rules, Deck,
simulation and AI transport remain separately authorized future work.
