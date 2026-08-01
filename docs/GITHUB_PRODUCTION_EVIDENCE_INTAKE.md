# Phase 114A intake revision

The workflow redownloads and authenticates the same artifact, runs adapter `mtgjson-workflow-artifact-v2`, and intakes derived evidence identity `30663562841-review-payload-v2`; it never replaces `data/production_runs/30663562841/`. Its dedicated default branch is `production-evidence/run-30663562841-review-payload-v2`. Reports now include retained payload count and bounded serialized payload bytes as well as `canonical_write: false` and `promotion_performed: false`.

Exact rerun inputs: `run_id: 30663562841`, `artifact_name: mtgjson-ingestion-30663562841`, `archive_sha256: 2887ea307f07b58ddcf4f0179e99e54e79e072949542869e7c01b4275a1ee3ba`, `destination_branch: production-evidence/run-30663562841-review-payload-v2`, `base_branch: main`, and initially `dry_run: true`; after that run and this implementation are green, dispatch `dry_run: false` to create the evidence-revision PR. Merge remains withheld until all GitHub Actions checks are green.

# Phase 112B persistence reconciliation

The two reported dispatches authenticated and verified run `30663562841`, but neither established durable repository evidence. The first was intentionally dry-run. In the second, the workflow's effective `inputs.dry_run` still caused both conditional persistence steps to be skipped. Thus write-boundary validation was the last executed durability-related stage: Git configuration, branch creation, staging, commit, push, and PR creation did **not** run; they produced no command output and no exit status. Because skipped steps are not failures, the job exited zero. This is the exact workflow control-flow defect; it is not an intake-path, ignored-file, or Phase 111 verification defect.

Phase 112B always invokes `scripts/production_evidence_persistence.py` and passes the displayed dry-run value as an explicit `true`/`false` argument. A false value must complete every named persistence stage and independently query the GitHub Pull Requests API. It confirms an open PR, requested head and base, exact head SHA, retained run path, and evidence-only changed-file boundary. Existing branches and PRs are reused only when the retained tree is byte-identical; conflicts, missing permissions, empty staging, push failures, missing PRs, and unverifiable PRs fail nonzero. The report exposes `intake_status`, `run_id`, `evidence_path`, `destination_branch`, `evidence_commit_sha`, `pull_request_number`, `pull_request_url`, `retained_file_count`, `retained_tree_digest`, `canonical_write: false`, and `promotion_performed: false`.

## Exact rerun

Dispatch **Production evidence intake** from merged Phase 112B with: run ID `30663562841`; artifact `mtgjson-ingestion-30663562841`; archive SHA-256 `2887ea307f07b58ddcf4f0179e99e54e79e072949542869e7c01b4275a1ee3ba`; destination `production-evidence/run-30663562841`; base `main`; and `dry_run: false`. Confirm the persistence artifact and workflow outputs contain a commit SHA and PR URL/number. Do not review, approve, promote, or merge evidence until all Actions checks are green.

# GitHub production evidence intake

> **Phase 112A — implemented 2026-07-31. Architecture v12 unchanged.**

## Baseline and incident

Merged Phase 112 is confirmed at merge commit `188101b` (implementation commit `3660657`).
The GitHub-native intake authenticated run `30663562841`, downloaded artifact
`mtgjson-ingestion-30663562841`, and verified archive SHA-256
`2887ea307f07b58ddcf4f0179e99e54e79e072949542869e7c01b4275a1ee3ba`. Phase 111 then
correctly rejected it because `manifest.json` was absent at archive root. This was a contract/layout
mismatch, not corrupt production evidence.

## Native artifact inventory

The upload declaration in `.github/workflows/mtgjson-production-ingestion.yml` produces these
top-level families (GitHub may remove their common runner-temporary prefix):

```text
reports/mtgjson-delivery/                         # checksum, acquisition, provider,
                                                  # dataset, validation, batch, performance reports
evidence/mtgjson/production-batches/...           # legacy bounded globs, when present
evidence/mtgjson/imports/.../identifier_quarantine.json
streaming/<source-sha256>/
  manifest.json                                   # streaming run/plan manifest
  completed-sets.json                             # completed-set ledger
  batch-index.json
  candidate-shards/<unit>.json                    # MB2 000334-mb2; MSH 000373-msh
  finding-shards/<finding>.json                   # finding payloads
  review-indexes/<batch-id>/review-package.json   # retained compatibility index
  review-batches/<set-code>/<batch-id>/
    manifest.json
    candidate-ids.json
    dependency-closure.json
    review-package.json
  quarantine/*.json
  performance-checkpoints/*.json
run-result.json
mtg-lab-diagnostics/                              # initialization, stderr, resource/exit diagnostics
```

The full `AllPrintings.json[.gz]` and the streaming SQLite working index are deliberately not
uploaded. The adapter inventories every ZIP member rather than assuming that optional globs
matched files.

## Exact mismatch and normalized contract

The native `streaming/<sha256>/manifest.json` describes streaming delivery and points to nested,
target-specific files using runner paths. Phase 111 instead requires a repository-intake
`manifest.json` at ZIP root, plus root `metadata.json`, `batch_index.json`,
`lineage/source.json`, and compact `review_batches/...` bundle documents. Native evidence has all
facts needed to derive that envelope, but it does not natively use that envelope.

`mtg-lab evidence normalize-workflow-artifact` is the deterministic pre-intake adapter. It checks
safe unique paths, authenticated run/artifact naming, commit and repository lineage, the successful
dry-run result, all no-write/no-promotion flags, source lineage, ledger, exact target identity,
candidate shard resolution and hashes, candidate-ID and closure digests, pending review packages,
and target isolation. It rejects the full dataset. It then constructs only the Phase 111 envelope
and compact bundles, retains permitted bounded reports/findings/lineage/diagnostics, records source
paths, sizes, hashes, and transformations, and emits a fixed-metadata deterministic ZIP. Its
`normalized_archive_sha256` is the digest of the canonical normalized member inventory excluding
the self-describing root manifest; `normalized_zip_sha256` authenticates the emitted ZIP bytes.
The unchanged Phase 111 `evidence intake` API consumes that ZIP next.

```bash
PYTHONPATH=src python -m mtglab evidence normalize-workflow-artifact ARTIFACT.zip \
  --sha256 ARCHIVE_SHA256 --run-id RUN_ID --artifact-name NAME \
  --repository OWNER/REPOSITORY --commit-sha WORKFLOW_COMMIT \
  --output NORMALIZED --format json
```

## Operational dry-run rerun

Dispatch **Production evidence intake** with exactly:

```text
run_id: 30663562841
artifact_name: mtgjson-ingestion-30663562841
archive_sha256: 2887ea307f07b58ddcf4f0179e99e54e79e072949542869e7c01b4275a1ee3ba
destination_branch: production-evidence/run-30663562841
base_branch: main
dry_run: true
```

The job authenticates and downloads the original ZIP, normalizes it, performs unchanged Phase 111
intake and verification, enforces the evidence-only write boundary, and uploads the adapter report,
generated manifest, normalized inventory, intake/verification results, and any available errors.
With `dry_run: true`, it creates no branch, commit, push, or PR. Do not use `dry_run: false` until
this normalized dry run and all GitHub Actions checks are green. Intake is still neither review nor
approval nor promotion.
