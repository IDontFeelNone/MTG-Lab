# Official Gameplay Rules Release Discovery Closure

## Scope and Architecture v13 gate

This separately owner-authorized milestone reconciles supplied review evidence
and adds an offline, metadata-only artifact verification handoff. It is implemented
pending independent Project Manager inspection, from canonical main
`988ac4bc384da8e4b62f89790727c2e79373eea2`, following merged PR #183.
It fits Architecture v13's independently governed Gameplay Rules evidence domain.
Decision 017 remains Accepted and unchanged; no Tier-0 change or Architecture v14
is required.

The existing fictional gameplay kernel and PRODUCT RULES modules are unchanged.
No real Comprehensive Rules are executable, no real Card semantics or Oracle
parser exists, and `src/simulation/` remains unimplemented. The public metadata
and verifier establish evidence bindings, never rules projection authorization,
source-policy clearance or production authority.

## Two observations with different provenance

The previous [source/versioning review](GAMEPLAY_RULES_SOURCE_VERSIONING.md)
recorded one Codex network attempt at the official Magic rules page on
2026-10-16. It returned `ACCESS_UNAVAILABLE` under the environment's network
policy. No origin HTTP status, artifact URL, source body, effective version,
SHA-256 or byte length was established. That observation and its original
eight-file review package remain byte-identical at
`reference-reviews/gameplay-rules-source-versioning/`.

The owner supplied a separate Project Manager observation dated **2026-10-16**,
made through first-party Wizards web review outside Codex's blocked environment.
Its provenance is `PM_SUPPLIED_FIRST_PARTY_OBSERVATION`; its acquisition method is
`EXTERNALLY_OBSERVED_FIRST_PARTY`. Codex did not independently fetch Wizards in
this milestone. No HTTP status, response headers or network receipt are invented
for the PM review.

The PM label describes supplied review provenance. It is neither cryptographic
observer authentication nor legal authority. The retained record has
`VERIFIED_METADATA_ONLY` evidence and `NOT_INDEPENDENTLY_REPRODUCED` status;
it does not claim `VERIFIED_ARTIFACT` or locally verified bytes.

`ExternalSourceObservation` in `gameplay_rules.source_evidence.observations`
uses the existing immutable metadata contract conventions: `.create`,
`.from_dict`/`.from_json`, `.verify`, defensive `.to_dict` and `.identity`.
Its exact source-reference anchor is verified without upgrading the original
source's access outcome. `ObservedReleaseCandidate`, `DiscoverySourceReview`
and `DiscoverySelection` keep the supplied observation, release and explicit
review/selection distinct in `gameplay_rules.source_evidence.closure`.

## Exact supported designation and incorporation claims

The supplied observation supports these bounded facts:

| Item | Supplied first-party observation |
| --- | --- |
| Designating source | Official Magic rules landing page, under Comprehensive Rules |
| Designated formats | DOCX, PDF and TXT |
| Designated TXT/PDF filename family | Contains `20260925` |
| TXT title marker | Magic: The Gathering Comprehensive Rules |
| Explicit effective date | September 25, 2026 (`2026-09-25`) |
| Observed rule marker | `701.71`, Empower Jace |
| Related bulletin | Official Reality Fracture Update Bulletin, published September 21, 2026 |
| Bulletin relationship | Identifies `701.71` as the new Empower Jace rule and defers to the official rules page on conflict |
| Currentness scope | Designation observed **as of 2026-10-16** |
| Artifact SHA-256 / byte length | Unknown / unknown |

The exact TXT basename and resolved artifact URL were not supplied. They remain
unknown. The filename family/date token is a bounded supplied observation, not
an invented URL, complete filename or source-provided semantic version.

The narrow update conclusion is
`at_least_identified_update_incorporated=true`: the observed September 25 TXT
contains the specific rule marker that the September 21 bulletin identified.
`full_bulletin_diff_verified=false`. There is no exhaustive comparison of every
Reality Fracture change, numbered-rule extraction or rule-level diff.

Currentness is a dated designation claim, not a timeless “current” alias. Future
observations may supersede this review without changing its historical identity.
The Comprehensive Rules remain the primary general gameplay authority; the
bulletin is supporting change evidence and cannot replace a selected rules
artifact.

## Reconciled metadata package

The new package is
`reference-reviews/gameplay-rules-release-discovery-closure/`. It explicitly binds
the original PR #183 package and its files, then adds the PM observation, the
September 25 release candidate, dated designation/incorporation claims, an
artifact verification request, permission state and narrowed readiness result.
It retains project-authored control metadata, identities and bounded summaries.
It contains no official TXT, PDF, DOCX, full rule passages, numbered-rule corpus
or source-body capture.

The original unavailable observation is not converted to a successful fetch.
The PM observation and later local verification have distinct identities from
the source reference, release candidate, artifact byte hash, review and selection.
Deterministic immutable contracts and package bindings reject altered metadata
rather than refreshing its hashes or silently rebinding a historical review.
The seven new files are `pm-observation.json`, `release-candidate.json`,
`artifact-verification-request.json`, `source-review.json`,
`current-selection.json`, `readiness.json` and `manifest.json`.

## Offline artifact verification handoff

The preferred next input is the exact officially designated **TXT** artifact in
the `20260925` family, supplied locally by the owner/operator. No such real
artifact was supplied for this milestone. The verifier never discovers or
downloads it.

The request pins the game, selected release identity, expected effective date,
TXT verification profile and bounded markers:

- title: `Magic: The Gathering Comprehensive Rules`;
- effective date: `September 25, 2026`;
- rule reference: `701.71`;
- rule heading: `Empower Jace`.

The caller supplies an explicit file path and exact request. Verification reads
the existing file under bounded size and encoding rules, computes SHA-256 over
the exact bytes and their exact length, and checks only these bounded structural
markers. It does not normalize the full text, extract numbered rules, parse a
PDF or interpret an executable rule.

The metadata-only result binds the release candidate, request, verification
profile, effective date, checked markers, byte length and SHA-256 where obtained.
It always carries `content_retained=false` and
`projection_authorized=false`. It contains no source body, copied lines or
sensitive absolute input path. There is no `RawSnapshotStore` call, registry
admission, network request, hidden temporary copy or output-body file.

Malformed or mismatched contracts fail closed. A valid request that cannot
verify its input returns a structured outcome such as `HASH_MISMATCH`,
`WRONG_EFFECTIVE_DATE`, `MISSING_EXPECTED_MARKER`, `WRONG_MEDIA_TYPE`,
`ARTIFACT_TOO_LARGE`, `MALFORMED_TEXT` or `UNSUPPORTED_ARTIFACT_TYPE`.
Symlinks, non-file inputs, path ambiguities, invalid encoding, stale/altered
requests, wrong game or retargeted release/profile are rejected. Exact-byte
identity is independent of file location; identical retained inputs produce
identical verification identities.

The authored request at
`reference-reviews/gameplay-rules-release-discovery-closure/artifact-verification-request.json`
defines the exact API/CLI handoff and result contract. Verification does not
delete or change the operator's input file; it simply does not copy or retain the
source body in MTG Lab.

### Local API and CLI

`ArtifactVerificationRequest` and `ArtifactVerificationResult` are immutable
metadata contracts in `gameplay_rules.source_evidence.artifacts`.
`build_artifact_verification_request(...)` authors the explicit release/source/
observation binding under the fixed
`official-comprehensive-rules-txt-20260925-v1` profile. That profile permits only
UTF-8 TXT, at most 5 MiB, with the `*20260925*.txt` reference pattern and the four
bounded markers above. The pattern is not a claimed exact official basename.

The API is:

```python
verify_local_artifact(
    explicit_local_txt_path,
    verified_request,
    expected_request_id=reviewed_request_id,
    expected_release_candidate_id=reviewed_release_candidate_id,
    expected_discovery_source_reference_id=reviewed_source_reference_id,
    game_id="magic",
    observed_at=explicit_optional_observation_time,
)
```

The independent expected identities must come from the reviewed handoff; a
caller must not silently refresh them from altered input metadata. Observation
time is optional and explicit. There is no implicit wall clock in an otherwise
identical verification result.

The CLI is `PYTHONPATH=src python -m gameplay_rules.source_evidence.verify`.
It requires the local artifact as its positional argument and these flags:
`--request`, `--expected-request-id`, `--release-candidate-id`,
`--discovery-source-reference-id` and `--game-id`. `--observed-at` is optional.
The retained handoff supplies the request path and identity bindings; the owner
supplies only the existing local TXT path and any explicit observation time.
JSON is written to stdout, never the source body. Exit status is 0 for
`VERIFIED_EXPECTED_ARTIFACT`, 1 for a structured unsuccessful verification, or 2
for a malformed/unavailable contract. Error output excludes source snippets and
absolute local paths.

## Readiness and future review

**Current result: `NOT_READY_FOR_RULE_PROJECTION`.**

The remaining artifact gate is `OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED`. SHA-256 and
byte length remain unknown because no owner/operator artifact was supplied.
The stronger metadata/currentness observation does not weaken the exact-byte
gate or fabricate an artifact-verification receipt.

The supported future evidence chain is:

```text
preserved unavailable Codex observation
    + separately attributed PM first-party metadata observation
    + exact selected release/designation/effective-date bindings
    + successful offline artifact verification
    + explicit source review
    -> scoped readiness assessment
    -> later separately authorized structured projection
```

A successful local verification alone does not authorize projection. The future
review must still bind the same release, dated designation, effective date,
markers and exact artifact identity. It must explicitly review both
`local_artifact_identity` and `local_artifact_source_correspondence`: the latter
confirms the supplied bytes correspond to the observed official designation.
Structural marker checks alone cannot establish official origin. This review
claim records provenance judgment, never cryptographic authentication or source
permission. When every required gate is genuinely
satisfied, readiness may become `READY_FOR_RULE_PROJECTION`; it remains a
technical evidence condition. A real `GameplayRulesSnapshot` additionally needs
separately reviewed structured projection, capability coverage, compatibility
and owner authorization.
`select_discovered_release(...)` accepts the exact observation, release,
verification request, optional local result and explicitly selected review. Its
readiness model does not promote the original inaccessible network reference to
a successful acquisition and cannot use metadata-only observation as a substitute
for the missing artifact identity.

## Permission and retention boundaries

The PM observation and local integrity verification do not establish any source
content-use permission. These states remain independently `NOT_ESTABLISHED`:

| Source-content operation | State |
| --- | --- |
| Private raw retention | `NOT_ESTABLISHED` |
| Public source-content redistribution | `NOT_ESTABLISHED` |
| Free service use | `NOT_ESTABLISHED` |
| Commercial service use | `NOT_ESTABLISHED` |
| AI/model export | `NOT_ESTABLISHED` |

Discovery/metadata processing and transient inspection remain separately
classified; an implemented verifier does not grant permission to use it on any
specific source. Public retention of this project's authored control metadata
does not stand in for a provider-content grant. No legal conclusion, notice
upgrade or source-policy plan clearance is made. Existing
`ReferenceDatasetRegistry` and generic evidence licensing gates remain unchanged.

## Tests, preservation and next candidate

Public tests use original fictional TXT content and supplied fictional metadata.
They prove deterministic observation/request/result identities; scoped
currentness; the artifact-hash gate; title/date/rule-marker checks; exact byte
hashing; rejection of malformed, oversized, wrong-type, symlinked, missing-marker
and retargeted inputs; no network/RawSnapshotStore/source-body output; and future
explicit-review readiness without projection authorization. Existing gameplay,
Product Rules, evidence/acquisition, Tier A, Card Intelligence, role/comparison,
historical replay and publication/writer regressions remain required validation.

Canonical data, the Tier A profile, selected audits, SourceRecords, mechanical
evidence, role/context artifacts, market/collection data, MB2's 810 selected
candidates and nine holds, spelling/physical Printing state,
`SOURCE_POLICY_CLEARED_PLANS` and writer/admission/OIDC are unchanged. The Card
Acquisition historical protected identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`,
including its original Architecture-v12 auxiliary dependency.

The next candidate is **Owner-Supplied Comprehensive Rules Artifact Verification
— NOT AUTHORIZED**. It supplies the missing exact officially designated TXT for
the offline handoff and an explicit review. It does not project real rules,
parse Oracle text, integrate real Cards or implement simulation. No next
milestone begins automatically.
