# Canonical import recovery

The repair is limited to `CanonicalRepository.apply_import` and its missing-root
read guard. Architecture v13, Decision 017, canonical record schemas, import
provenance, source permissions and owner-controlled admission are unchanged.
Recovery directories are operational material, never a second canonical authority.

## Why the transaction changed

The preceding implementation renamed the original to a backup, promoted staging,
deleted the backup, then reloaded the live repository. An abrupt process exit
between renames left current absent. A retry treated it as a new empty game,
deleted the original backup and published only incremental records. A separate
final-load failure returned an error after the original backup had been deleted.
Both regressions failed against canonical base
`ae1c8d2a8880f4fc5d5174650e5fe5f258b4e913` before this repair.

## Transaction and public outcomes

For game `G` under the explicitly selected `games_root`:

* `G/` is the live canonical tree.
* `.G.import-backup/` retains the original until live verification succeeds.
* `.G.import-staging/G/` contains the candidate. Creating the fixed staging
  directory exclusively serializes cooperating calls for that game.

An existing backup, staging path, or legacy `tmp*/G` candidate blocks an import
before copying or writing. Nothing in these pre-existing paths is automatically
cleaned. A missing live directory with such recovery material raises
`CanonicalRepositoryError` instead of constructing a successful empty catalog.
A genuinely new empty game without recovery material remains supported.

The importer copies existing records, writes sorted relative paths, validates the
complete staged graph, and fingerprints the candidate. It renames the original
into the backup, promotes the candidate, and verifies the **live** repository
while the original backup still exists. Successful live verification is the
publication boundary. A successful return is still a `CanonicalRepository`; the
existing importer reports `applied=true` and keeps its existing report schema.

Before that boundary, compensation preserves a rejected candidate in staging and
restores the original when safe. Device/inode identity plus the complete candidate
file/directory fingerprint must match before moving a promoted candidate back.
A changed candidate, conflicting live directory, or failed compensation is left
in place with an explicit recovery-required error. Do not assume an error always
means the filesystem was untouched: inspect the described recovery paths.

Early copy/write/staged-validation failures clean only this call's own staging
when it has not begun committing. If that cleanup fails, the primary exception
keeps a recovery note and staging remains. Once commit begins, failure preserves
staging for inspection and blocks blind retries even after original restoration.

After successful live verification, cleanup removes the old backup and then the
**empty** staging directory. An ordinary cleanup exception does not roll back the
verified publication. The method returns the verified reader with
`import_cleanup_pending`, a tuple of remaining recovery-directory names, and
emits `CanonicalImportCleanupWarning` naming the committed outcome and operator
action. Its default value is `()`. Warnings-as-errors cannot turn this verified
commit into an abort. Existing importer callers retain `applied=true`; the
warning and a subsequent blocked retry expose unfinished cleanup.

A cleanup `KeyboardInterrupt`/other non-ordinary termination is not swallowed;
Python exceptions receive an explicit **COMMITTED and verified** note. An abrupt
process exit cannot return a result; leftover recovery paths require inspection.
No previous backup is removed automatically on the next call.

## Recovery-state matrix

| Failure/window | Active tree | Recovery material | Read/retry result |
|---|---|---|---|
| Copy, partial candidate write, staged validation | Original unchanged | Own staging cleaned, or retained if cleanup fails | Original reads; retry only after any retained state is resolved |
| Pre-existing backup/staging/legacy orphan | Unchanged | All existing bytes preserved | New import blocked; missing active tree never loads as empty |
| Original rename failure | Original retained/restored if safe | Candidate retained | Explicit not-committed/recovery error; retry blocked |
| Candidate promotion failure | Original restored if safe | Candidate retained | Same; compensation failure preserves both paths |
| Abrupt exit between renames | Absent | Full original backup and candidate staging | Read and all ordinary retries blocked; no empty success |
| Final live initialization failure | Original restored if ownership proven | Rejected candidate retained | Not committed; retry blocked |
| Changed/foreign candidate or destination | Preserved as found | Original backup and available staging retained | No overwrite; explicit compensation-incomplete error |
| Successful publication/normal cleanup | Verified candidate | None | Normal reads and deterministic incremental retry |
| Backup cleanup failure, including partial deletion | Verified candidate | Remaining backup/staging preserved | Committed return plus warning/pending tuple; retry blocked |
| Staging cleanup failure/unexpected content | Verified candidate | Staging retained; unexpected content never recursively deleted | Same committed outcome; retry blocked |
| Abrupt exit after promotion or during cleanup | Candidate may be live | Available generations preserved | No automatic rollback or cleanup; retry blocked by remaining staging/backup |

## Safe operator procedure

There is deliberately no automatic recovery or approval command.

1. Stop writers for this game. Preserve the live tree, backup, staging and legacy
   orphans in permitted storage; do not delete them or infer precedence from names
   or timestamps. Keep the original error and requested input identity.
2. Copy the potential original and candidate into **separate disposable games
   roots**. Validate each with the normal `CanonicalRepository` loader. Compare
   complete bytes, record identities/dependencies and the intended input against
   the known original/expected result. A valid schema or checksum does not select
   the authorized generation or grant source-use permission.
3. An owner/operator must explicitly choose restoration or acceptance. Never
   overwrite a conflicting valid live tree without inspecting and preserving it.
   Restore only a verified complete original; do not restore a partially deleted
   backup. For a verified committed candidate, repair cleanup rather than blindly
   rolling back to an older generation.
4. Archive recovery material **outside `games_root`**, retaining provenance and
   permissions. Verify the chosen live tree before retrying. Do not remove a
   guard just to make an import pass. The tests demonstrate repeated blocked
   attempts, verification on a separate copy, archival and a safe subsequent
   incremental import preserving unrelated records.

## Evidence and limits

`tests/test_canonical_import_recovery.py` calls the real owning API with fictional
Game/Rarity records in disposable roots. It injects ordinary filesystem/loader
exceptions, partial writes/deletion, changed destinations, compensation failure
and actual subprocess `os._exit(86)` interruptions. Tests preserve an untouched
canonical record, distinguish committed cleanup from aborted publication and
verify deterministic successful import and repeated rejection/recovery.

The exact historical source adapter only reverses enumerated base-to-successor
bytes; it does not repin historical evidence, waive gates or grant runtime power.
All prior record/fixture identities and pack/gameplay semantics remain unchanged.

This is process-exception/interruption recovery, **not demonstrated power-loss
durability**: no fsync, journal, general persistent transaction service or
multi-filesystem atomic exchange is introduced. Cooperating imports serialize via
exclusive staging; direct readers are not a transactional snapshot across the
rename gap and will fail closed when the live root is absent. Non-cooperating
external writers are unsupported; detectable candidate/destination conflicts are
preserved, not overwritten. Keep production admission and permission gates intact.
