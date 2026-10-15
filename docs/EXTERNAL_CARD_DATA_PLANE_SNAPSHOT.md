# Immutable canonical snapshot contract — accepted design direction

**Status: Accepted v13 architectural requirements; constrained fictional Stage 1 implemented.**
Decision 017 is Accepted. A later separate owner instruction authorized the local
fictional-only `canonical-snapshot-fictional-v1` contract and read-only attachment,
now pending PM review. See [its implemented scope and API](V13_STAGE1_SNAPSHOT_ATTACHMENT.md).
The broader production snapshot design below remains future work. No production
manifest authority, activation or dataset permission is installed. Examples under
`docs/examples/external-card-data-plane/` retain their original `design-v1` domain
and bytes; they are documentation fixtures, not runtime production authority.
Runtime fictional fixtures live separately under `tests/fixtures/canonical_snapshots/`.

## Scope and identities

A snapshot is one explicitly game-scoped, immutable effective dataset and its
reviewed dependency closure. Its release may be stored locally, in private Git,
object storage or a private release service. Runtime authority is the selected
verified release identity, not its mutable location or a provider's current API.
Multiple games use separate handles; composition pins exact member roots.

Keep four identities distinct:

1. **Content ID:** domain-separated SHA-256 of the canonical content manifest. This manifest lists
   exact canonical files, source-manifest ID, provenance dependencies, game,
   representation profile, schema/policy/transform versions, entity inventories,
   capability/completeness declarations and optional member/parent content roots.
2. **Validation-input ID:** domain-separated SHA-256 of content ID plus exact validator code,
   schema/policy/configuration identities and required check profile. It is
   calculated before the validation report and contains no report digest.
3. **Snapshot/release ID:** domain-separated SHA-256 of the release manifest containing content ID,
   validation-input ID, exact validation report digest, release/parent/migration
   metadata and operation-scoped decision references. Exclude only its own ID,
   transport locators and external signatures. Those exclusions are specified,
   never an arbitrary ignore list.
4. **Query snapshot ID:** existing digest of query entities/envelopes. It is not
   redefined or overwritten by the outer production authority ID.

The validation report binds content and validation-input IDs, **not the final
snapshot ID**. Thus report digest → release ID does not create a digest cycle.
Signatures/attestations bind the final release ID through a separately trusted
operator host/signing policy; signatures are not included in the ID they sign.
Source and policy documents retain their own exact-byte hashes and semantic IDs.

## Canonical serialization and manifests

Design version `canonical-data-snapshot-design-v1` uses UTF-8 JSON, sorted object
keys, compact separators, `ensure_ascii=False`, no trailing LF for semantic IDs;
reject duplicate keys, nonfinite numbers and unsupported numeric representations.
Record byte hashes hash the exact retained bytes, including any LF. For new
decimal domain values use explicit reviewed string/precision rules rather than
platform-dependent binary floats. Historical source bytes are never reformatted
to make them match new serialization rules.

For each semantic ID, hash exactly the canonical JSON object
`{"identity_domain":"mtg-lab:<kind>:design-v1","document":<body>}`. Kinds are
`source-manifest`, `content-manifest`, `validation-input`, `release-manifest`,
`schema-set` and `policy`. Each body's own ID is excluded; the validation-input
body is the explicit object of content ID, validator/schema/policy identities and
check profile. This recipe applies only to the documented outer design; existing
entity IDs and query/evidence hash recipes are unchanged. The fictional example
and its tests specify the exact object shapes. Timestamps/locators are never
removed through a caller-selected exclusion list.

Repeated game, schema, policy, representation, source and inventory metadata in
content/release manifests must agree. Individually correct hashes cannot make
contradictory declarations valid. Transport locators and external signatures live
outside the release identity document.

Manifest file entries are sorted by normalized relative POSIX path, not arrival
or filesystem order. Paths must be unambiguous, bounded and relative: reject
absolute paths, `..`, platform-drive/UNC paths, backslashes, symlinks, duplicate
normalized names and case/Unicode collisions relevant to the target platform.
Declare maximum file counts, payload sizes and decompressed size/ratio before
extracting a bundle. Reject extra/missing files rather than accepting unknown
archive members. Canonical/source manifests have no executable hook or pickle.

Archive compression, encryption, timestamps and packaging have a separate
transport digest. A differently compressed archive can contain the same logical
snapshot; its transfer integrity still must be verified. Ciphertext and plaintext
hashes are distinct and access-controlled. Secret-bearing URLs or credentials
never enter logical identity or public metadata.

## Required release metadata

| Field | Semantics and verification |
| --- | --- |
| `snapshot_id`, `contract_version` | Recomputed semantic identity and exact manifest-contract version |
| `game` | Explicit game scope; legacy unscoped state is allowed only through a reviewed single-game representation profile |
| `content_id`, `content_manifest_sha256` | Logical content root and exact retained content-manifest bytes |
| `schema_set_id`, `schema_versions` | Hash-pinned schema definitions, not just a version label |
| `policy_id`, `policy_version` | Exact validation/conflict/identity/construction/field-use policy content |
| `source_manifest_id`, `source_manifest_sha256` | Immutable provider/source inventory and exact source-manifest bytes |
| `providers`, `transformations` | Provider namespace/version/dataset identities, acquisition versions and exact transformation code/config |
| `entity_inventory` | Counts plus sorted per-kind `(game, id, record_hash)` inventory digest; complete dependency graph checked |
| `representation_profile` | Typed/state/knowledge/evidence components and pinned duplicate/precedence rules; no ambient-root merging |
| `capabilities` | Known available/incomplete/unavailable/unsupported source/derived capability states; not a claim of comprehensive rules/simulation support |
| `validation_input_id`, `validation_report` | Check profile, validator revision and report ID/hash, executed checks, errors and explicit unrun checks |
| `created_at` | Supplied release event time; never inferred provider publication or market observation time |
| `compatibility` | Supported code/API/representation/materializer versions and exact schema/policy needs, validated against actual consumers |
| `migration_id` | Identity of an actual applicable migration, or explicit no-migration state; no speculative migration silently applied |
| `parents`, `supersedes`, `members` | Optional immutable prior/root/member IDs; acyclic relationships; composition/conflict policy and effective root fixed |
| `decision_references`, `permission_profile` | Scope-bound authenticated admission/use decisions and authoritative evidence references; request-authored booleans are insufficient |
| `visibility`, `retention_profile` | Canonical/evidence/derived/log/export scopes and availability/expiry obligations; not proof that the specified permission exists |

Schema validity and a passing technical report are necessary but insufficient:
production must independently verify authenticated release/admission authority
and actual use permission through the trusted boundary. A signed content claim
does not establish rights beyond the referenced decision/evidence scope.

## Source closure and provenance

Source manifests inventory retained bytes or exact bounded projections with
content type/encoding, provider IDs/versions, source URLs, retrieval times,
publication/observation times only when evidenced, checksum evidence and notices.
Projection recipes bind original pointers/record hashes and distinguish retained
projection bytes from unretained full upstream bytes. Hash-only upstream metadata
must never claim those unavailable full bytes are archived or replayable.

Each canonical assertion/record links source IDs, field paths, retained evidence
hashes, parsed-row references, transformations, confidence, unknown/conflict
state and real admission evidence. Full record-level historical evidence cannot
be relabeled as v3 field assertions. Source lookup is an explicit authorized
accessor against pinned evidence roots; it has no implicit network fallback.

Large source archives can be independently permissioned from runtime canonical
files. Full rebuild/revalidation requires all necessary authorized evidence and
code. Ordinary consumers may use a verified canonical attachment without receiving
every raw byte when the approved access/check profile permits it, but the system
must disclose whether full replay is presently available. If the required evidence
cannot legally be retained, a reproducibility-required production profile blocks;
a checksum or provider URL is not substitute evidence.

## Timestamp, completeness and deterministic behavior

Content/validation identities exclude ambient wall clock. Recorded source times
remain decision inputs; actual release `created_at` is an explicit input to release
identity. Releasing identical content at a new time may yield a new release ID
with the same content ID. Byte-identical fixed inputs yield identical IDs and
domain results. Do not fabricate a historical timestamp to force identity equality.

An unavailable optional module is an explicit capability gap, not `known_absent`
facts. Corrupt evidence is invalid; unsupported format differs from missing
coverage. Required identity fields still satisfy current canonical contracts.
New snapshots cannot silently convert unresolved Printings, languages, finishes,
faces, rules semantics or ownership spelling into known facts.

## Attach and activation protocol

1. An authenticated deployment/operator selects an exact snapshot reference and
   expected prior active identity; a request cannot supply its own trust roots.
2. Explicit transport stages it into a bounded isolated directory and verifies
   transfer identity. Loader/consumer discovery never fetches live providers.
3. Verify manifests/paths/bytes, schema and graph closure, sources, validation
   inputs/report, actual permissions, trusted release authority and compatibility.
4. Attach a read-only capability rooted in the verified immutable tree. Detect
   mutation/replacement/TOCTOU before publication/activation; do not expose mutable
   staging paths as production attachments.
5. Run required real query, collection, projection and domain consumer checks on
   this attachment before atomic activation. “Valid” and “materializable” remain
   different states where current projection is incomplete.
6. Compare-and-swap the expected active root. A concurrent/stale update blocks.
   Existing requests retain their old handle; new requests use the new one.
7. Retain truthful safe failure diagnostics and intact previous attachment. Failed
   activation leaves no successful acceptance marker. Proposed recovery steps
   are not an already implemented rollback service.

Missing/incompatible/untrusted/corrupt snapshot: structured blocked response before
consumption. Optional missing source: source-status/incomplete or ABSTAIN according
to the domain contract. Explicit historic replay can select a known old compatible
root. Current operations never silently select old/public seed data to pass tests.

## Generated SQL, projections, embeddings and caches

Cache key includes snapshot ID, code/schema/policy, materializer/migration version,
backend/dialect and exact indexing/configuration identity. Store a generation
manifest and logical row/index counts/digests; stable domain ordering and Decimal
semantics must not depend on SQL query order. Database bytes need not be identical
across engines, but observable contract results must be deterministic.

Materialize into staging, validate query results and dependency/count equivalence,
then select the generated cache. Do not mutate the authoritative snapshot through
ORM writes. Cache loss/corruption rebuilds from the exact authorized snapshot;
without that snapshot the operation blocks. SQLAlchemy/SQLite production generation
is future work under Decision 010, not demonstrated runtime support today.

Derived stores inherit source/personal classifications. Encrypted backup transport
does not grant export permission. Embeddings/vector indexes must additionally bind
model/tokenizer/index versions; they cannot become a second canonical knowledge
authority or survive a source-retention decision unnoticed.

## Historical compatibility and rollback

Keep old public canonical bytes, audit receipts, source projections and expected
query hashes unchanged. The legacy adapter inventories existing typed, promoted
and knowledge generations, and records original audit scope as history, not a
reusable live authorization. Do not alter an old absolute-root decision binding
and claim it authorized a new operator root or update.

Store outer snapshot and legacy query IDs side-by-side. Every historical dossier,
collection audit, market record and calculation selects its original input scope;
a changed current catalog requires a new calculation. If an old input is unavailable
or no longer permitted, report replay unavailable rather than repinning evidence.

Rollback means authorized activation of an intact compatible still-permitted prior
root and matching generated cache/rebuild. It does not reverse private ownership
events, rewrite old outputs or guarantee that every schema/code migration is
reversible. Required code compatibility and retained inputs are explicit limits.
