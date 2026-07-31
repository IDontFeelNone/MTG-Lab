# Phase 112 handoff

The manually dispatched `Production evidence intake` workflow now performs the Phase 111 intake
without transferring the ZIP to Codex. It validates the selected successful workflow and exact
artifact, authenticates the download with an independently supplied SHA-256, runs intake and
verification, enforces that only `data/production_runs/` changed, and opens a dedicated-branch PR.
Dispatch it for run `30663562841` and artifact `mtgjson-ingestion-30663562841`; no artifact has
been fabricated or committed by Phase 112. Intake is not review, approval, or promotion.
