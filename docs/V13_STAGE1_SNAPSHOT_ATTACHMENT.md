Current status: Stage 1 is merged in PR #176. Its implementation and historical
scope below are preserved. The separately authorized Stage 2 review is in
[V13_STAGE2_LEGACY_PUBLIC_PROFILE_REVIEW.md](V13_STAGE2_LEGACY_PUBLIC_PROFILE_REVIEW.md);
its next prerequisite remains NOT AUTHORIZED. No real profile is activated.

# V13 Stage 1 — Fictional Canonical Snapshot Attachment

Status: separately owner-authorized implementation, pending independent PM review.
Decision 017 remains Accepted and Architecture v13 active. This implements only
local read-only attachment of original fictional data, not production admission.

## Public API and explicit selection

```python
from pathlib import Path
from repository.snapshots import attach_snapshot, attach_legacy_public
from query import CanonicalQueryEngine
from collection.intelligence import CanonicalCollectionResolver

# Obtain this exact expected identity from the reviewed fixture/release selection,
# independently of the directory being requested; never select "latest".
catalog = attach_snapshot(Path("/explicit/fictional-snapshot"),
                          game="lantern", expected_snapshot_id=reviewed_release_id)
query = CanonicalQueryEngine.from_attachment(catalog)
resolver = CanonicalCollectionResolver.from_attachment(catalog)

# A distinct explicit compatibility choice, never an error fallback:
legacy = attach_legacy_public(game="magic", data_root=Path("/explicit/repo/data"))
legacy_query = CanonicalQueryEngine.from_attachment(legacy)
```

`verify_snapshot` returns immutable verification metadata. `attach_snapshot`
returns a `SnapshotAttachment` only after successful verification. The handle
exposes game, read roots and fresh copies of identity/capability metadata; it is
not another query engine or a writer. Existing reader constructors retain their
legacy semantics. New `from_attachment` factories accept only these explicit
attachment types and check them before and after reader construction and reads.
Neither a failed verification nor a failed read tries another root, repository,
cache, historical fixture or provider. No network is used.

`LegacyPublicAttachment` is the existing filesystem profile, not a newly sealed
immutable release. Its roots are explicit; it asserts no new production authority
or permission. Existing historical tests continue to select their exact original
roots. This stage does not inventory or certify every legacy representation as a
v13 snapshot.

## Narrow runtime contract

`src/repository/snapshots.py` and the registered v1 `canonical-snapshot` schema
implement **canonical-snapshot-fictional-v1**, representation
**typed-card-printing-v1**. This is deliberately narrower than the accepted
long-term snapshot design. It supports one game, typed v1 Cards/Printings,
explicit game identity, internal original-fictional SourceRecords and bounded
local evidence. Identifier records, promoted state, knowledge/audit overlays,
products, treatments and arbitrary metadata extensions are unsupported here.

Both runtime fixtures under `tests/fixtures/canonical_snapshots/` are original:
`lantern` has two Cards and three Printings; `clockwork` has one Card and one
Printing. IDs and Printing→Card relationships are ordinary existing canonical
identities. Neither fixture contains production/provider or personal data.
They declare catalog identity available, mechanical evidence unavailable, rules
execution unsupported and identifier coverage unavailable. All artifacts retain
`production_eligible=false`, `approval_state=not_granted` and
`source_policy_clearance=not_granted`; production checks are explicitly unrun.

The complete release consists of four fixed control documents:

- `release-manifest.json`: release ID, game/profile, separate content/source/schema/
  policy/validation identities, exact control-byte bindings and compatibility.
- `content-manifest.json`: exact sorted payload inventory, SHA-256 and byte lengths,
  entity IDs/hashes/counts and explicit capability states.
- `source-manifest.json`: original source identity/version, exact SourceRecord and
  evidence correspondence, evidence byte binding and closed dependency inventory.
- `validation-report.json`: this content's fictional validation-input identity,
  exact passed technical checks and explicitly unrun production checks.

`policy.json` and `schema-bindings.json` are manifested payload dependencies.
The latter binds the exact packaged snapshot/Card/Printing/SourceRecord v1 schema
bytes. A release's validation input also binds the exact verifier implementation
SHA-256 and named check profile. Incompatible verifier or schema bytes block
attachment rather than silently blessing an old report. The report is not trusted
as proof: verification repeats every required technical check locally.

Semantic identities use SHA-256 over compact UTF-8 JSON with sorted keys,
`ensure_ascii=False`, no trailing newline and a domain wrapper:
`{"identity_domain":"mtg-lab:<kind>:fictional-v1","document":<document>}`.
The release/content/source document excludes only its own fixed self-ID field;
there are no caller-selected exclusions. File bindings hash exact bytes including
newlines. Creation time is a fixed authoring input, not regenerated at attachment.
Duplicate keys, non-finite values and all floats are rejected by this integer/
string profile. Domain-separated content, source, schema, policy, validation-input
and release identities are not interchangeable.

The outer release ID is **not** `CanonicalQueryEngine.snapshot.snapshot_id`.
The existing query hash/envelope calculation is unchanged. Attached readers expose
`catalog_binding` separately; attached collection resolution additionally emits
`catalog_attachment`. Its `canonical_snapshot_id` remains the original query ID.
Personal persisted collection snapshots are not migrated by Stage 1.

## Integrity and read-only boundary

Verification requires an independently selected expected release ID and game. It
checks exact inventory, file size/checksum, source/schema/policy correspondence,
repeated metadata consistency, validation inputs/report, entity schemas and
relationships through the existing canonical repository validation. Every declared
SourceRecord is checked even when no entity references it. Unsupported dependency
files are rejected even if correctly rehashed into a manifest.

Paths must be normalized relative POSIX paths with the supported ASCII alphabet;
absolute paths, backslashes, traversal, trailing dots and case-fold collisions are
rejected. Symlinks in the root or descendants and nonregular files fail closed.
This small profile is bounded to 256 files, 2 MiB/file, 16 MiB total and at most
128 records per entity kind. It performs no archive extraction, executable hooks,
pickle loading, network acquisition or implicit discovery.

A final byte inventory confirms that graph validation did not observe a persisted
change. Attached readers reverify before and after access, so ordinary directory
mutation invalidates the selected attachment. These controls do not claim an OS
sandbox, authentication, filesystem lock or protection against a malicious
concurrent writer performing an undetectable change-and-restore race. Deployments
must supply immutable/read-only storage; protected production deployment remains
future work. A caller can copy returned data without mutating canonical bytes.

`SnapshotError.as_dict()` returns `status=blocked`, a typed code and a bounded
message/relative path, without source contents or sensitive absolute paths.
Missing, corrupt, unsupported/incompatible and wrong-game inputs remain distinct.
Unknown mechanical coverage is not corruption or a fabricated mechanical fact.

## Reproducibility and preservation

`PYTHONPATH=src python tests/snapshot_fixture_builder.py` checks deterministic
fixture bytes without changing them. Its explicit `--write` mode authors only
these new fictional runtime fixtures. Test-only `rebind` helpers support attacks
with internally consistent hashes; they cannot create real authorization.
Documentation examples remain separate historical design fixtures and are not
loaded as runtime production authority.

Tests exercise both fictional games, exact query/collection relationships,
relocation, immutable metadata, failure/no-fallback cases, adversarial dependency
closure and unchanged legacy behavior. Public tests require neither network nor
private production data. Original canonical data, MB2 pending inputs,
`SOURCE_POLICY_CLEARED_PLANS`, writer/admission authority and historical replay
fixtures remain unchanged. Card Acquisition continues binding its own original
Architecture-v12 bytes and protected identity
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

## Remaining boundary

Attachment is not admission; a hash is not approval; a private path is not
permission; technical validation is not owner authorization or policy clearance.
There is no production eligibility, real-data activation, protected transport,
signature service, composition, SQL materialization, writer destination change,
new mechanical loader, Rules/Deck/Competitive expansion, simulation or AI transport.

Candidate next milestone: **V13 Stage 2 — Legacy/Public Snapshot Profile Review**,
**NOT AUTHORIZED**. Review existing generations and their evidence/consumer
contracts before implementing or selecting any further profile. Stage 1 does not
authorize that work or the still-blocked MB2 cohort.
