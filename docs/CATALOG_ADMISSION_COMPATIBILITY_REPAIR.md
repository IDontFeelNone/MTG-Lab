# Catalog admission compatibility repair

This is an implementation-only repair. It admits no production records, records no
real admission decision, and changes no Architecture v12 contract. The retained
819-candidate reference packet stays pending and byte-identical; the nine held
multiface candidates are not corrected or selected. The new factual packet is not
activated as a Mechanical Card Intelligence source.

## Admission authority and trust

`AutomaticCanonicalUpdate` no longer derives approval from successful validation
or caller-authored classifications. A new write requires an `AdmissionDecision`
from a live `AdmissionReviewBoundary` supplied by **trusted host code**. The host
must authenticate the reviewer and authorize the canonical-admission operation
before installing that capability. Request/configuration JSON, arbitrary actor
strings, `approved=true`, provider reputation and digests cannot authenticate a
reviewer. Python/code/OS operators able to replace the host are inside this trust
boundary; untrusted request callers must never choose the capability.

The standalone CLI has no authenticated host integration and therefore cannot
authorize new admission. This repair does not claim to implement an authentication
service. A later production caller integration and actual owner/Project Manager
admission decision remain gates. A retained audit is evidence of a previous
operation, not a new authorization capability.

The decision binds ordered candidate IDs and digest, exact payload and row hashes,
retained source/receipt paths, lengths and hashes, target/evidence/dataset identity,
construction policy, canonical pre-state, operation, authenticated reviewer,
decision time and review reference. Authorization and live integrity are checked
again at readiness/write boundaries and on checkpoint resume; a checkpoint is an
observation, not cached authority. Changed inputs cannot reuse an old decision.
Previous completion requires a contiguous, scope-valid checkpoint prefix with
matching admission/post-state and consumer results; merely placing a success file
does not establish completion. Resumed acceptance executes the real consumer checks
again and rejects cached claims that differ. These checks bind protected local
artifact content and progress, not reviewer authentication; filesystem/code
operators remain inside the documented host trust boundary.

`IsolatedAdmissionTestBoundary` is nonserialized authority bound to one live
`TemporaryDirectory` capability, exact root, lifetime and initially authorized
inputs. It produces explicitly simulated receipts and cannot target a different
root, survive cleanup, or become a reusable production approval. No configuration
flag enables it.

## Record construction and consumer acceptance

The existing writer preserves Oracle Card identities, MTGJSON UUIDs, deterministic
Scryfall aliases, source values/original labels, candidate/parsed-row references,
field provenance, acquisition lineage, confidence, opaque unmapped fields and
uncertainty. Printing relationships use `card_id`, `set_id` and `finish_ids`;
English/en and Japanese/ja agree, while contradictory evidence remains rejected.
Closure is checked over existing records plus the proposed delta, including
Printing-to-Card/Finish and Identifier-to-Printing links.

The proposed state is read through actual canonical queries, collection resolution
and the projection read bridge in disposable staging before accepting the update.
Each admitted Printing must traverse both Card relationships and its set namespace;
each alias must resolve to its exact Printing. Dictionary/count checks alone do not
establish acceptance.

The projection bridge validates the flat production representation against real
retained admission audits and payloads without adding lifecycle/approval fields or
discarding aliases. `validation_scope=production-read-and-admission-integrity`
explicitly differs from typed materialization. All aliases count in completeness.
Thirty unchanged historical Phase 136 Printings have provider finish labels absent
from canonical taxonomy: 21 `signed`, nine `etched`. Their exact evidence is
reported; `fully_dependency_closed=false` and `typed_materialization_ready=false`.
New deltas have no such exception and require real Finish dependencies. Typed
materialization remains blocked where whole-row evidence/alias representation is
not supported by existing typed contracts. No new taxonomy or Identifier model is
manufactured; any further contract decision remains outside this repair.

## Incomplete mechanics and preserved history

A valid canonical Card missing a mechanical source binding retains explicit
incomplete/unknown fields. Acquisition returns a structured abstention with
`mechanical_source:<Card ID>:source_binding_missing` or ambiguous-source blockers,
without fabricating a provider row, source identity, price or complete cost.
Invalid canonical identities, corrupt evidence and false unique bindings remain
errors. Existing supported original-cohort behavior stays covered by regression
tests. Supporting the new factual source format is deferred.

Historical packet/pilot replay uses the original fixture and snapshot explicitly.
Changed-current catalogs must still reject those historical bindings; no current
operation silently substitutes historical data. The full suite runs updated code
against unchanged retained production data and separately constructs expanded
current catalogs through the repaired writer in temporary fixtures. New snapshots
and audits are new calculations, never replacements or repinned historical outputs.

The original eight-row Phase 121 fictional fixture stays unchanged. Its standalone
Set candidate is explicitly rejected under the frozen virtual-set contract. A
separately identified seven-row disposable derivative demonstrates the unrelated
writer workflow; set namespace facts remain on Printings.

## Rehearsal and failure recovery

`tests/fixtures/catalog_admission/mb2-recommended-candidate-ids.json` contains exactly
the ordered 810-ID recommendation. Its UTF-8 canonical JSON bytes have no trailing
newline and SHA-256
`f63585f4a023e2b81656a4cca0c6811a7d598e45f065633c3a11d9a9a2b5d500`.
`tests/catalog_admission_helpers.py` independently verifies that list and the
unchanged packet digest before copying evidence into isolated storage. It supplies
native pending rows unchanged and separate retained parsed-field context. The
workflow tests use the supported writer, not `build_prospective_fixture.py`.

Pre-completion failure restores only authenticated original bytes for a write owned
by this operation. Tampered backups or unrelated current-state drift are not
overwritten; diagnostics explain why recovery was refused. Incomplete operations
leave no successful write/acceptance checkpoint. A failed write creates no new
accepted-admission receipt. If a partial-write receipt already exists before a
later validation/recovery failure, its immutable bytes are retained as prior write
evidence and the blocked report identifies it explicitly; it does not establish
completed admission. Historical audits remain immutable. The interface still offers a rollback **plan**, not an
executable rollback service; no rollback framework is added.

Focused tests cover missing/pending/rejected/simulated/mismatched/out-of-scope
decisions; payload/source/receipt/pre-state tampering; checkpoint resumes and final
authorization races; dependency/collision failures; actual query/collection
acceptance; incomplete acquisition; original-byte recovery; backup/drift refusal;
historical/current separation; exact 810-record writer integration; and the
unrelated fictional workflow. The full required command remains:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

The private collection rehearsal uses the retained original import, declaration and
clarification against writer-produced disposable data. Its measured result is
reported separately from the earlier hand-shaped observation. No personal
source, positions, spelling proposals, audits or authorization fixtures enter Git.
Source-policy questions remain operation-specific gates for real admission; a
failed Scryfall terms-page read is an access failure, not a rights decision.
