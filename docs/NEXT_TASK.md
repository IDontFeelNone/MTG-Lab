# Next task after Phase 112A

Run the GitHub **Production evidence intake** workflow for `30663562841` using the exact documented
inputs and `dry_run: true`. Inspect the uploaded adapter report, generated root manifest,
normalized inventory, and Phase 111 verification result. Keep merge and `dry_run: false` withheld
until all GitHub Actions checks are green. Do not review candidates or promote data.

Manually dispatch `Production evidence intake` with the independently obtained SHA-256 for
artifact `mtgjson-ingestion-30663562841` from successful run `30663562841`, then review and merge
the workflow-created evidence-only pull request. Only after the retained run verifies on the
default branch may a separately authorized phase restart the blocked independent Phase 110B
review. Intake must not review, approve, or promote candidates.
