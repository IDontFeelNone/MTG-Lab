# Next task

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
