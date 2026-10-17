# Owner-Supplied Comprehensive Rules Artifact Verification

## Scope and Architecture v13 gate

This separately owner-authorized milestone verifies an explicitly supplied local
Comprehensive Rules TXT and closes the reviewed release's exact-byte evidence gap.
It starts from canonical main
`7342e20a2f38be43f517f4cfcca19e23da3c0e70`, after PR #184 merged. It fits
Architecture v13's existing independently governed Gameplay Rules evidence domain.
Decision 017 remains Accepted and unchanged; no Tier-0 change is required.

Implementation and the retained review are pending independent Project Manager
inspection. The evidence chain reaches **READY_FOR_RULE_PROJECTION**. This is
technical evidence readiness for a later, separately authorized projection
milestone. It does not authorize projection, admission, retention, redistribution,
service use or AI export. No real rules are executable.

## Three different provenance records

The original PR #183 Codex network attempt remains `ACCESS_UNAVAILABLE`. Its
eight-file source/version package is unchanged. No Wizards request was made to
verify the supplied artifact, and the failed attempt is not relabeled successful.

The separate PR #184 `PM_SUPPLIED_FIRST_PARTY_OBSERVATION` remains unchanged. It
records externally observed first-party designation of the September 25, 2026
Comprehensive Rules, as of **2026-10-16**. The designated formats were DOCX/PDF/TXT;
the observed TXT/PDF filename family contained `20260925`. That observation is
`VERIFIED_METADATA_ONLY`, not an artifact-byte verification or Codex network
receipt.

For this milestone the owner supplied one explicit local TXT and stated it was
downloaded directly from the official Wizards TXT link designated on the official
Magic Rules page, without intentional modification before supply. This is
owner/operator origin testimony. It is not Wizards cryptographic authentication,
independent Codex network verification, permission evidence or source-policy
clearance. The file remains external owner-controlled input; its absolute local
path and source body are not retained in the public package.

## Existing verifier, unchanged request

The operation uses the existing
`gameplay_rules.source_evidence.artifacts.verify_local_artifact` implementation
and its immutable profile `official-comprehensive-rules-txt-20260925-v1`.
Neither the verifier nor its required markers is changed to accept the input.
The existing CLI is `python -m gameplay_rules.source_evidence.verify`; it requires
an explicit artifact path, request, expected request/release/source identities,
game and optionally an explicit retained observation timestamp. There is no file
discovery or network fallback.

| Binding | Exact identity |
| --- | --- |
| Verification request | `sha256:c5c8746050b9d12bfce010c120e56d859301f6df07f2ca54c20f352e682997f5` |
| Existing release candidate | `sha256:9a6cabf4d5780f436669d2945341935bdf13fe35f8009f681aa6a0bf4be34d62` |
| Discovery source reference | `sha256:60d5449dc03af1e5b233eef9a5da6639ea23f5706afbf17fe3f0ebcf7d9a0f4f` |
| PM observation | `sha256:4452ad76e7902b183294d5c60b829e311e98da213511e6d51a4358a94efd005c` |

The request remains at
`reference-reviews/gameplay-rules-release-discovery-closure/artifact-verification-request.json`.
It requires game `magic`, UTF-8 TXT, maximum **5 MiB**, the `*20260925*.txt`
filename family and these four bounded markers:

- title: `Magic: The Gathering Comprehensive Rules`;
- effective date: `September 25, 2026`;
- rule reference: `701.71`;
- rule heading: `Empower Jace`.

Verification hashes exact bytes, counts their length and checks those markers.
It does not normalize the document, extract numbered rules, build an inventory,
copy source lines, parse a PDF, execute content or interpret rules. Unsafe paths,
symlinks, missing/oversized/non-TXT/invalid-encoding input and mismatched markers
fail closed under the existing contract. No `RawSnapshotStore` or evidence-registry
admission is used.

## Exact local verification result

The retained observation timestamp is the owner's explicit input
**`2026-10-16T22:15:00-04:00`**. No implicit clock enters deterministic identity.

| Result field | Verified value |
| --- | --- |
| Status | `VERIFIED_EXPECTED_ARTIFACT` |
| SHA-256, exact supplied bytes | `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca` |
| Byte length | `977752` |
| Effective date | `2026-09-25` |
| Encoding / artifact type | UTF-8 / TXT |
| Bounded markers | All four matched |
| Verification result identity | `sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3` |
| Local verification state | `ARTIFACT_BYTES_VERIFIED_LOCALLY` |
| `content_retained` / `source_body_copied` / `network_used` | `false` / `false` / `false` |

Identical bytes, request and explicit timestamp reproduce the same result.
Changed bytes yield a different hash/result; passing structural markers alone does
not authenticate their origin. The public result retains no source-body excerpts
or local path. The supplied attachment stays outside the repository.

## Explicit source-correspondence review

A local hash alone cannot close readiness. A new immutable review explicitly binds
the successful result to the existing release, exact request, PM observation and
discovery source reference. It evaluates the exact byte identity, expected
20260925 family, September 25 effective date, title and 701.71/Empower Jace markers,
the owner's direct-download origin statement and that testimony's limitations.

The review is dated **2026-10-17**; this is explicit review metadata, distinct from
the owner's retained artifact-verification timestamp. `ArtifactCorrespondenceReview`
in `gameplay_rules.source_evidence.artifact_review` binds the origin statement,
six reviewed correspondence checks and an unchanged-contract `DiscoverySourceReview`.
Its immutable metadata identity changes if those reviewed inputs change.

The review supports `local_artifact_identity` and
`local_artifact_source_correspondence` alongside the existing designation,
effective-date, as-of-currentness and identified-update claims. The
`select_reviewed_artifact` handoff verifies the explicit correspondence review,
then the existing `select_discovered_release` machinery reproduces the selection
with its bound discovery review and verification. It still rejects missing review, mismatched identities,
cross-game inputs, stale or conflicting bindings and a different currentness
scope. No new logical rules release is invented merely because its bytes are now
known; the previously metadata-only candidate remains immutable and the new
selection binds the exact artifact separately.

The selected currentness claim remains **designation observed as of 2026-10-16**.
It does not establish currentness on a later date. The narrow Reality Fracture
conclusion is unchanged: the identified `701.71` / Empower Jace update is
incorporated. `full_bulletin_diff_verified=false`; hashing the full TXT is not an
exhaustive bulletin diff.

## Append-only metadata package

The new package is
`reference-reviews/gameplay-rules-artifact-verification/`:

- `artifact-verification-result.json`;
- `artifact-correspondence-review.json`;
- `current-selection.json`;
- `readiness.json`;
- `manifest.json`.

`verify_artifact_review_package(root, *, source_root, discovery_root)` verifies
the package and requires explicit roots for its prior evidence dependencies.
It contains only bounded metadata/control JSON and binds prior source/discovery
evidence without modifying either package. Integrity verification reproduces the
selection and checks exact file inventory, content bindings and fixed authority
flags. The supplied TXT, PDF/DOCX bytes, full rules text, extracted corpus and
large quotations are excluded. Public tests use authored fictional local input
and retained metadata, never the owner's external file or live Wizards access.

## Readiness, authority and permission

The reviewed chain is:

PM first-party designation observation → existing September 25 release candidate
→ existing TXT verification request → owner-supplied local artifact → successful
exact-byte verification → explicit source-correspondence review →
**READY_FOR_RULE_PROJECTION**.

`projection_authorized=false`, `admission_eligible=false` and
`source_policy_clearance=not_granted` remain fixed. Source-content private raw
retention, public redistribution, free service, commercial service and AI/model
export permissions remain **NOT_ESTABLISHED**. Metadata verification does not
upgrade them. Existing generic licensing gates are unchanged.

No real `GameplayRulesSnapshot`, structured Comprehensive Rules projection,
Oracle parser, real Card semantics, gameplay simulation, format/deck legality or
strategic recommendation is created. The fictional Gameplay Rules kernel,
Product Rules, Tier A profile, canonical catalog, intelligence artifacts, MB2
pending state and writer/admission/OIDC behavior remain unchanged. Card Acquisition
historical protected identity stays
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

## Validation and limitations

Focused tests cover the exact retained identities, deterministic fictional TXT
verification, explicit review and mismatch rejection, readiness/permission
separation, metadata-only package safety, prior package preservation and protected
state. Existing gameplay, Product Rules, evidence/acquisition, Tier A and
intelligence/historical regressions remain required. Publication validation runs
the complete committed suite in its disposable writer environment; final counts
and exact-head hosted status belong to the PR validation record.

The local verifier establishes byte identity and bounded structure, not official
cryptographic origin or a complete content audit. Only the reviewed October 16
designation scope is established. This milestone performs no independent Codex
Wizards fetch and no complete Reality Fracture review. It does not clear source
permissions or begin implementation of real rules.

## Recommended next candidate — NOT AUTHORIZED

**Core Comprehensive Rules Projection — Foundational Rules Subset** is the next
candidate, subject to separate owner authorization and an explicit source-use
boundary. Start with a manually reviewed, small subset of **Magic Golden Rules
and players/game/object/zone concepts**: rule precedence and unknown-exception
boundaries, player/object identity, ownership/control and zone identity. State the
exact included rule references and unsupported dimensions before executable
projection; do not ingest entire numbered-rule families.

This creates the semantic base for later bounded mana/payment, timing/priority,
casting/stack-resolution and SBA projections without pretending that those systems
already understand real Magic. No source body retention or redistribution is
authorized by this recommendation. No next milestone begins automatically.
