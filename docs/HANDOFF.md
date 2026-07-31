# Phase 112B handoff

Merged Phase 113 (`b9941a6`) was the baseline. The successful verification did not prove persistence: both conditional Git/PR steps were skipped, so they emitted no output and no exit code and the job remained green. After Phase 112B is green and merged, rerun the exact non-dry-run dispatch documented in `GITHUB_PRODUCTION_EVIDENCE_INTAKE.md`; require populated commit and PR outputs plus the uploaded persistence report. Withhold evidence merge and all review/promotion until Actions are green.

# Phase 112A handoff

Phase 112 is merged at `188101b`. Run `30663562841`'s artifact was authenticated but correctly
failed Phase 111 because the native workflow layout has no root intake `manifest.json`; this is not
evidence corruption. Phase 112A adds deterministic normalization and dry-run reporting, then uses
the unchanged intake/verify boundary. Dispatch the exact dry-run inputs in
`GITHUB_PRODUCTION_EVIDENCE_INTAKE.md`. Do not use non-dry-run mode, review, approve, or promote
until normalization and all GitHub Actions checks are green.

The manually dispatched `Production evidence intake` workflow now performs the Phase 111 intake
without transferring the ZIP to Codex. It validates the selected successful workflow and exact
artifact, authenticates the download with an independently supplied SHA-256, runs intake and
verification, enforces that only `data/production_runs/` changed, and opens a dedicated-branch PR.
Dispatch it for run `30663562841` and artifact `mtgjson-ingestion-30663562841`; no artifact has
been fabricated or committed by Phase 112. Intake is not review, approval, or promotion.
