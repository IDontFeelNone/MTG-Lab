# Next task: Phase 108B official-corpus evidence gate

After this PR is green (without merging it first if the branch workflow can be dispatched), rerun **MTGJSON production ingestion** with the same official URL, reviewed SHA-256, positive batch size, `mode=dry-run`, and blank promotion inputs. Record the complete colliding-record inventory and determine whether the rows are physical-printing duplicates, faces/components, aliases, supersession, source defects, or remain ambiguous. Success means provider validation completes and deterministic unaffected batches plus narrow quarantine are reported, or the next fatal issue is exposed. Do not promote and do not begin Phase 108C.

---

# Next task

Rerun **Actions → MTGJSON production ingestion → Run workflow** with the same official source URL,
reviewed SHA-256, positive maximum batch size, blank selected batch/reviewer/reference, and
`mode=dry-run`. Confirm provider validation and deterministic planning complete; inspect all
identifier findings. Do not promote until an independent reviewer approves exactly one batch.

## Prior Phase 107 direction (superseded)

After Phase 107 merges with green GitHub Actions, trigger the manual MTGJSON production ingestion
workflow in dry-run mode with the independently reviewed official SHA-256. Review its full-corpus
counts and deterministic batches, then authorize at most one dependency-closed batch with named
reviewer metadata. Verify projection, downstream checks, and rollback before considering any
later incremental batch. Never commit the source corpus or temporary canonical state.

## Prior Phase 105 direction (superseded)

After Phase 105 merges with green GitHub Actions, run an operator-controlled local MTGJSON
acquisition rehearsal and record its SHA-256 without committing `data/local/`. Provider import,
target discovery, review, promotion, and projection remain separate work and require explicit
authorization. Do not infer set codes or treat acquisition registration as canonical eligibility.
# Immediate gate after Phase 108C

Run the official compressed-artifact targeted dry run for `Mystery Booster 2,Marvel Super Heroes`
using the reviewed checksum, inspect uploaded streaming ledgers/manifests and resource diagnostics,
and require green checks. Only then run a blank-target full-corpus dry-run plan. Do not promote or
claim the resource issue resolved before one official run completes.
