# Phase 111 handoff

The permanent Production Evidence Repository and intake CLI are implemented. Obtain the immutable
ZIP and independently published SHA-256 for successful workflow run `30663562841`, then run
`mtg-lab --data-root data evidence intake ZIP --sha256 SHA256 --run-id 30663562841 --format json`.
Commit the resulting bounded evidence only after `evidence verify` succeeds. Then restart Phase
110B from candidate inspection. Intake is not review, approval, or promotion; do not promote.
