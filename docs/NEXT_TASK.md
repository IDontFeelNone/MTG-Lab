# Next task after Phase 113A

Rerun PR #86 only after Phase 113A merges. Require its merge-result checks to validate retained
run `30663562841` as non-canonical, target-isolated, and pending review. After #86 is green and
merged, authorize a separate independent review of exactly one indexed MB2 batch; do not review
MSH, approve, promote, or write canonical state during the intake transition.

# Next task after Phase 112B

Merge Phase 112B only after GitHub Actions are green, then perform the documented `dry_run: false` intake rerun for run `30663562841`. Verify the resulting branch, evidence-only commit, open PR, and persistence report. Merge remains withheld until checks are green. Do not restart Phase 113 review, approve candidates, promote, or write canonical state in Phase 112B.

# Next task after Phase 113

Retain run `30663562841` through the verified Production Evidence Repository intake and merge its
evidence-only pull request. Only then rerun the independent first-MB2-batch review and create a
candidate-complete immutable decision. Do not review Marvel or promote canonical data.

## Prior Phase 112A operation

Run the GitHub **Production evidence intake** workflow for `30663562841` using the exact documented
inputs and `dry_run: true`. Inspect the uploaded adapter report, generated root manifest,
normalized inventory, and Phase 111 verification result. Keep merge and `dry_run: false` withheld
until all GitHub Actions checks are green. Do not review candidates or promote data.

Manually dispatch `Production evidence intake` with the independently obtained SHA-256 for
artifact `mtgjson-ingestion-30663562841` from successful run `30663562841`, then review and merge
the workflow-created evidence-only pull request. Only after the retained run verifies on the
default branch may a separately authorized phase restart the blocked independent Phase 110B
review. Intake must not review, approve, or promote candidates.
