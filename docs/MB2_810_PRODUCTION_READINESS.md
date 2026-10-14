# MB2 810 production admission readiness

Status: **MINIMUM-DATA ADMISSION NOT CURRENTLY SAFE**. This is a pending
readiness review, not an admission decision or source-policy clearance.

Reviewed canonical main: `32032706f22207fdd310cdca9850e388fc97ebcd`.
PR #173 is merged into that revision. The canonical pre-state is
`881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077`,
matching the existing pending configuration. Production records are unchanged.

## Exact scope and evidence

The retained selection is 810 pending candidates: 270 Cards, 270 Printings and
270 Scryfall identifier records. Its ordered-ID digest is
`f63585f4a023e2b81656a4cca0c6811a7d598e45f065633c3a11d9a9a2b5d500`:
SHA-256 of UTF-8 JSON with sorted object keys, compact separators,
`ensure_ascii=False`, and no trailing LF. There are no duplicate IDs or overlap
with the nine held multiface candidates. The field matrix records the exact
held IDs; they remain unselected. Japanese Gigantosaurus remains Japanese.
Unconfirmed owner spellings remain unapplied; Essence of Ajani remains outside
the ordinary Card cohort with emblem semantics. No physical identity is inferred.

The original reference packets, raw projections, source receipts and candidates
remain byte-identical. The 34 policy-evidence files under
`reference-reviews/mb2-810-source-policy/2026-10-14/` are also preserved
byte-for-byte. Their manifest SHA-256 is
`f686a1792303adbdcfa0dc15359f4614bc2076cc8896dae7273752f98cf9e8d7`.
Those files contain policy citations, bounded quotations, internal summaries,
the complete MTGJSON MIT notice, and receipts. They contain no private collection
information, full Wizards/Scryfall pages, cookies, credentials or session material.

Receipts distinguish the retained projection hash, exact HTTP entity hash, and
web-reader rendered-text hash. Unavailable origin hashes are null. Auxiliary
field-definition URLs are explanatory citations, not hash-pinned origin policy
captures. Full policy captures remain private. The public-retention audit does
not establish permission for any additional card-content redistribution.

## Required-field and dependency blockers

1. `AutomaticCanonicalUpdate._canonical_record` derives Card identity from the
   exact Scryfall Oracle ID and requires a name. The mapper embeds the same
   Oracle ID in Printing relationships. The alias records require the exact
   Scryfall Printing ID. Retained policy evidence does not establish public
   retention permission for these identifiers or the underlying Card names.
2. Both v1 and v3 Card contracts require a nonempty name. V3 additionally
   requires normalized name and layout. Production projection validates the
   name; the collection resolver indexes Card names while constructing its
   Printing index, even before an identifier-based lookup. A withheld object
   cannot replace the required string. A made-up placeholder would assert a
   false name; changing or hashing the Oracle ID would change the selected
   identity. Printings/aliases cannot be admitted without their Card targets.
3. The writer copies mapped fields into both `values` and `source_values`, and
   unknown fields into both `unknown_fields` and `unknown_values`. It preserves
   parsed context, field provenance and acquisition lineage. There is no
   reviewed field-exclusion policy in the current adapter.
4. `admission_publication_inventory` includes the actual canonical delta,
   bound candidate payload, source/receipt dependencies, admission audit and
   acceptance checkpoints. A filtered `state.json` with an unchanged full-content
   payload or receipt closure would still redistribute the excluded material.

Relevant existing entry points:

- `src/providers/mtgjson/mapper.py:map_dataset`
- `src/production_evidence/automatic_updates.py:AutomaticCanonicalUpdate._canonical_record`
- `src/production_evidence/automatic_updates.py:AutomaticCanonicalUpdate.admission_bindings`
- `src/production_evidence/automatic_updates.py:admission_publication_inventory`
- `src/schemas/v1/card.schema.json` and `src/schemas/v3/card.schema.json`
- `src/projection/engine.py:TypedCanonicalProjectionEngine.validate`
- `src/collection/intelligence.py:CanonicalCollectionResolver`

## Exact field review

`reference-reviews/mb2-810-production-readiness/2026-10-14/field-admission-matrix.json`
enumerates every container and leaf of the pure existing adapter output for all
810 selected candidates, including all nested source/unknown values, provenance,
relationships and lineage. Array positions use `/[]`; `/$canonical_identity`
is an explicitly identified inspection pseudo-path for the returned identity.
Each field has a canonical role, permission-evidence status, occurrence count,
origin/rationale and proposed disposition. Per-candidate hashes bind the adapted
inspection without retaining source-controlled values in this new packet.

The matrix permits only review of independently established MTGJSON-controlled
UUID material and internally generated metadata. It does not approve any record.
Required Scryfall identities, names and relationship facts remain blocked.
Rules/flavor/printed/foreign prose, rulings, mechanical descriptions, EDHREC
metrics and unresolved provider metadata are withheld from any proposed public
profile. Artwork/price values are not present; illustration/back identifiers
are treated as identifiers rather than a license for imagery.

The selected 270 source records contain 268 rules-text fields, 163 flavor-text
fields and 500 ruling entries. These occur on multiple output surfaces; omission
from just one surface is insufficient. Short names, factual descriptions,
identifiers, prose, metrics and images are not assigned one presumed rights status.

## Generic minimum-data design, not implemented

Optional-field omission can fit the existing data-driven Architecture v12 adapter
and evidence boundaries. A future reviewed generic extension would:

1. Bind a deterministic field-policy identity to configuration, planning,
   authorization, replay and publication, including canonical pre-state.
2. Evaluate every nested canonical, payload, context, receipt, audit and
   checkpoint surface. Default to withholding an unreviewed field; fail closed
   if a required identity/relationship field cannot be retained.
3. Represent optional content as unavailable/not-retained with a reason,
   source locator/hash and policy reference. This is a retention disposition,
   not a claim of factual absence or a fabricated mechanical value.
4. Preserve existing identities, relationship/dependency validation and
   historical evidence. Compute new payload/source-projection hashes honestly;
   do not reuse hashes of removed content.
5. Require a lawful, reproducible retained input closure. A URL/hash cannot
   stand in for source bytes when an existing validator requires those bytes.
   External/private-only dependencies need explicit contract review if they
   cannot satisfy the existing publication/replay boundary.
6. Permit later evidenced enrichment without changing identity. Missing content
   must retain safe incomplete/ABSTAIN behavior in consumers; no new mechanical
   source is activated and typed materialization is not claimed complete.

This optional-field design introduces no second store, importer or approval
service. It cannot supply missing permission for required fields. Supporting
nameless Cards would instead require an explicit canonical-contract and consumer
change proposal; it is not implemented or assumed to fit frozen requirements.

No generic field-filtering implementation is justified for this cohort until
required-field permission and the replay dependency closure are resolved.

## Pending configuration, planning and rehearsal

`config/automatic_updates/mb2-ordinary-810-pending.json` is unchanged:
`launch_state=pending`; real payload/source-artifact paths are absent. All
human-decision, reviewed-configuration and source-policy gates remain unresolved.
`SOURCE_POLICY_CLEARED_PLANS` remains empty.

No production-format execution input is materialized. The recorded plan attempt
is read-only and blocked. There is no `plan_id`, no verified execution plan, no
AdmissionDecision and no writer rehearsal for a filtered profile. Approval is
not granted; execution is unauthorized; admission is not ready.

The CLI currently rejects the pending marker before inspecting inputs. This is
not the sole blocker here: factual artifacts are absent and the required public
profile is unsafe. A narrow future integration repair may allow a pending plan
to inspect complete inputs while `admit`/`execute`/`publish` remain blocked. It
must not create inputs, grant approval, clear policy or bypass failed integrity.
No CLI or workflow change is made in this readiness PR.

The in-memory adapter inspection is method-level evidence only. It is neither
whole-workflow acceptance, a successful writer rehearsal, nor an expanded
collection census. Arithmetic projected counts are not a current catalog.

## Review and next decision

See `MB2_810_SOURCE_PERMISSION_FOLLOW_UP.md` for exact permission questions.
The bounded readiness PR contains evidence, the field matrix, this generic
design, blocker analysis and focused read-only regressions. It contains no
canonical delta, actual admission decision, owner audit or private capture.

Before artifact construction: establish the operation-specific rights chain for
required names/identifiers and relationships, plus a publishable replay closure;
or independently review a different canonical contract. Any later optional-field
implementation must have fictional and real-writer isolated tests, complete
leak checks and current/historical validation separated. Real admission remains
subject to a new explicit owner decision and the existing trusted boundary.
