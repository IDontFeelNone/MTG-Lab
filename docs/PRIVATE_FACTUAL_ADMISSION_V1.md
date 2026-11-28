# Private factual canonical admission V1

This additive profile implements reviewed normal-layout Card/Printing groups in
the existing canonical architecture. It reads verified factual derivatives, not
the original archive. Public tests use original project-authored source fixtures.
No real cohort is approved or admitted by implementing this pathway.

## Ownership and contracts

`canonical_import.mtgjson_factual.assess_factual_publication` verifies the existing
limited-retention publication with its original `PrivateResearchProfile`, an
independently retained report ID and publication ID. It streams the existing
`assertions.jsonl`, checks its exact artifact hash and partition/row census, and
builds a disposable SQLite eligibility index. It never changes the importer,
mapper, source-use policy, source archive, historical publication or checkpoint.

The selected `CanonicalQueryEngine` supplies the exact canonical pre-state.
Typed and promoted entities, inline identifiers, historical Identifier entities
and an attached factual snapshot's reviewed crosswalk participate in matching.
Promoted top-level assertion paths such as `/name` use the existing projection
convention for the pre-state view. Incompatible plain/path representations refuse;
known absence remains distinct from unknown. Existing Printing rarity, finish
availability and overlapping external-identifier disagreements hold the group.
An external alias requires unique identity and factual corroboration. Names alone
never establish identity. Provider candidate IDs are not canonical IDs. New
identities use the existing Card-reference/Printing-UUID identity rule.
Duplicate prevention applies to this explicitly selected canonical pre-state;
an operator must not claim universal collision detection against an unselected
catalog. Aliases with unresolved targets and ambiguous matches are held.
The importer's contradictory Oracle-alias refusal remains authoritative; the
adapter does not reinterpret unresolved records. Different unmatched Card keys
sharing a normalized name are held for identity review, never merged by name.
Independently corroborated existing canonical Cards may retain distinct identities
even when their names coincide.

Existing evidence dispositions `ELIGIBLE` and `QUARANTINED` are reused. Card
assertion conflicts, strict Scryfall identifier collisions, disputed matches and
exceptional/face relationships hold the affected Card and all dependent
Printings. A Printing defect holds its entire Card group, including siblings.
Unrelated groups remain eligible. Exceptional records are not declared defective.
Eligibility JSONL supplies exact reasons, source references and dependency scope.
Assessment covers the complete supported publication, not a hardcoded cohort.

`prepare_cohort(assessment, selected_card_ids, expected_assessment_id=...)` selects
whole eligible groups. Its immutable manifest binds the source release,
publication/report/profile/artifacts, exact pre-state, crosswalk, assertions,
transformations, dependency closure, policy, implementation and capabilities.
The caller independently reviews and retains its ID. No field called approved,
serialized review, checksum or schema-valid directory confers admission authority.

`repository.factual_snapshot.admit_factual_cohort` requires a live existing
`AdmissionReviewBoundary`, returning an exact existing `AdmissionDecision` for
the manifest bindings and operator root. The existing isolated test capability
is accepted only within its original temporary-root/lifetime scope. Its receipts
remain classified as isolated-test and cannot become production admissions.
Production requires the trusted host's authenticated reviewer. The host must
approve the whole exact cohort; there is no per-card manual approval requirement.

The adapter maps source assertions to explicit pending derived canonical
assertions and uses existing `build_review_package`, `CanonicalPromotionEngine`,
`TypedCanonicalProjectionEngine` and `CanonicalRepository.apply_import` staging,
prospective validation and transaction machinery. Confidence 1 means verified
derivative correspondence; it is not a probability of factual truth or semantic
verification. These are version-bound factual observations, not current Oracle.

## Factual mapping and evidence limits

Supported Card fields are name, layout, colors, color identity, mana cost, mana
value, literal type line, power, toughness and loyalty. Normalized name is an
explicit existing normalization. Missing optional fields remain unknown; empty
mana cost becomes unknown, never known_absent. No type-line decomposition,
defense, abilities, format legality or strategic classifications are admitted.
The existing v3 schemas must accept each proposed value.
Publisher characteristics must also have their literal provider types. An internal
knowledge-status object in a source field cannot assert known absence or verified
knowledge merely by fitting a canonical knowledge-value schema.

Printing mappings preserve Card association, set, collector number, language,
rarity when supported, literal finish availability and existing permitted external
identifiers. Set-code casing and supported language-code normalization have
explicit provenance. UUID identity remains in the reviewed crosswalk. Finishes
describe source availability, never ownership, artwork, border or treatment facts.
Missing required schema evidence holds the group; no collector namespace or
missing characteristic is invented.

Every assertion binds the exact derivative row and field pointer, original
record integrity reference, source partition and row, publication, transformation
and source release. The original importer can normalize/default some fields
(including language). This adapter verifies the retained mapper assertion; it
does not reestablish whether the original raw field was present. Provenance marks
original-field presence `NOT_REESTABLISHED_FROM_ARCHIVE`. Cohort reviewers must
consider these transformations; a derivative assertion must not be described as
a newly independently observed raw-source value. No archive inspection is added
to fill this evidence gap.

## Private snapshots, attachment and recovery

`private-factual-canonical-snapshot-v1` is a governed instance of the existing
canonical architecture. Git owns implementation, schemas and original fixtures;
owner-only operator storage outside Git owns private evidence and admitted data.
No Architecture v13, Decision 017, compatibility-profile permission or default
catalog is changed. Each generation contains only its exact approved cohort.

Publication uses an exclusive `.factual-admission-staging` workspace, validates
the prospective canonical repository and factual assertion correspondence, fsyncs
files/directories, then atomically renames into `snapshots/<manifest-digest>`.
The operator must provision the private 0700 operator root beforehand. Publication
fsyncs both the snapshots directory and operator root; a failed durability step
preserves the isolated generation and independent recovery pin.
The receipt binds every file, source, manifest, pre-state and authority scope.
The existing snapshot reader enforces its closed inventory and byte ceilings.
Live approval and pre-state are rechecked before publication. Attachment remains
a separate explicit operation; publication never changes a global pointer.

Idempotent replay verifies the existing generation instead of promoting again;
it requires `expected_existing_snapshot_id` from the independently retained
receipt. It never takes that trust pin from the generation's own marker.
Failures preserve staging or the new isolated generation for operator inspection;
they do not modify the previously attached authoritative view. Pending staging
refuses subsequent admission with `RECOVERY_REQUIRED`. There is no automatic
deletion or novel backup framework. A generation published before a parent-fsync
failure can be verified and durably reestablished without a second promotion.
If a later step fails after native snapshot verification, the exception's
`verified_snapshot_id` preserves that trusted invocation's already verified pin
for explicit recovery. It does not authorize attachment or bypass live review.
Rollback explicitly selects an older independently pinned, authenticated snapshot;
history is retained.

`attach_factual_snapshot(publication, expected_snapshot_id=...)` requires the live
publication capability. `reopen_factual_snapshot` requires independently retained
snapshot and manifest pins plus live host authentication after restart. Integrity
verification compares every projected assertion (including provenance) with the
exact approved manifest; integrity alone does not authorize attachment. Query reads recheck authority
scope and immutable inventory. Construct the query with
`CanonicalQueryEngine.from_attachment(attachment)`.

`MechanicalCardIntelligence.inspect_canonical_facts` is a minimal read-only
consumer of that explicitly attached profile. It returns the admitted identity,
associated Printings, facts, explicit unknowns, assertions, source and snapshot
context. It does not initialize historical source readers or mechanical dossiers.
No Oracle, semantic, legality, resource-production or gameplay authority follows
from factual inspection. Rules-level inputs still need their independent evidence.

## Bounds and validation

Whole-publication preparation streams at most 1,000,000 occurrence rows of 64 KiB
each, with a 2 GiB workspace/disk guard and an 8 MiB SQLite page cache; SQLite
temporary sorting stays in the private workspace. Single-writer trusted-host
execution is required because the existing SQLite temporary-directory convention
is process-scoped. Existing importer/worker limits are unchanged.

Cohort preparation is bounded to 25 Printings (the existing bounded review
envelope), a 2 MiB manifest and existing snapshot inventory ceilings: 256 files,
2 MiB per file and 16 MiB total. Large Card groups are held for a later separately
reviewed capacity change; the assessment still covers the whole publication.
Resource refusal must not trigger automatic retries or ceiling increases.
The 160-row/80-Card original fixture demonstrates population assessment and
independent cohort selection, not real-release throughput or memory guarantees.

Synthetic tests exercise actual importer/publication verification, promotion,
projection, transactional failure, immutable snapshot verification, query and Card
Intelligence interfaces. Finite successor preservation tests reconstruct exact
historical bytes and reject arbitrary edits; historical ledgers remain unchanged.

## Post-merge private procedure and additional decisions

After independent PM review and Owner merge approval, separately authorize
derivative-only private preflight against the actual pinned factual publication.
Supply its original trusted profile and independent report/publication IDs, the
selected canonical pre-state and a new private empty eligibility workspace. Review
whole-publication eligibility/reasons and transformation limitations, then select
a dependency-closed normal-layout cohort within the existing bounds. No real
individual record is inspected by this implementation milestone.

Separately approve the exact resulting manifest, intended canonical pre-state,
operator root and trusted production admission boundary. Only that later approval
can authorize actual real admission. Independently retain manifest, review,
snapshot and publication identities before explicit attachment. Verify privately
with the existing query and factual inspection APIs. Retain previous generations
for rollback. Original archive custody, historical limited-retention receipts and
source-use dispositions remain unchanged throughout.

No new acquisition, archive processing, Oracle extraction, external AI export,
public redistribution, semantic promotion or real-card execution is authorized.

## Future population-scale expansion and authorization usability

The current 25-Printing cohort ceiling, 2 MiB manifest ceiling and immutable
snapshot limits (256 files, 2 MiB per file, 16 MiB total) remain enforced. Every
generation represents only its exact selected cohort; cumulative private canonical
catalog expansion is not implemented. Future population-scale work must preserve
previous admitted knowledge and history efficiently rather than requiring hundreds
of separately approved small cohorts.

Owner authorization must eventually be iPhone-first, with machine-generated
bindings and audit metadata handled automatically. Authentication is deferred and
actual real admission remains HOLD. Bounded standing authorization is future
product direction, not permission to use this interface without its current live
exact-operation boundary. Future execution must independently verify the current
pre-state and bound implementation; changed bindings require deterministic
reassessment and a new manifest. Existing historical pins must not be rewritten.
