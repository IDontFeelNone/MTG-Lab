# Phase 108B delivery evidence

The manual workflow uploads deterministic identifier-quarantine artifacts in addition to provider, batch, and review reports. Run **Actions → MTGJSON production ingestion → Run workflow** using the same approved URL and reviewed SHA-256, a positive maximum batch size, `mode=dry-run`, and blank batch/reviewer/reference fields. Download the `mtgjson-ingestion-<run-id>` artifact and inspect `provider-validation.json`, `dataset-summary.json`, `batch-plan.json`, every manifest/review package, and `identifier_quarantine.json`. Merge and promotion remain withheld until CI is green and this gate validates the real records.

---

# MTGJSON Dataset Delivery and Production Run

> **Phase 108A:** the first real workflow reached provider validation after official download and
> checksum verification, then safely stopped on `deckboxId:2676`. The scope-policy fix preserves
> all such third-party references and reports their collisions for review. Rerun the same dry-run
> inputs; do not select a batch or promotion mode. Full-corpus planning is not yet claimed.

> **Phase 107 — implemented 2026-07-31. Architecture v12 unchanged.**

## Assessment and authority

The merged Phase 106 commit `456f2df` is the verified baseline. Architecture v12 and the
canonical Card/Printing contracts remain unchanged. The Canonical Repository is the sole source
of truth; MTGJSON AllPrintings is licensed, attributed, non-canonical reference evidence. Phase
106 already supplies production preparation, dependency-closed batching, governed promotion,
typed projection, rollback, and downstream verification. Phase 107 adds operational delivery,
not another ingestion framework. No architectural defect or Project Architect approval need was
found.

## Why the hosted run received HTTP 403

The approved `https://mtgjson.com/api/v5/AllPrintings.json` request returned HTTP 403 from the
hosted Codex execution environment in both Phase 106 and this phase. This is an upstream/network
access decision for that execution context, not JSON validation or an MTG Lab architecture
failure. The repository does not evade it with mirrors, browser impersonation, or unverified
bytes. A GitHub-hosted runner or an operator-delivered local artifact is the supported boundary.

## Supported delivery paths

The manual **MTGJSON production ingestion** workflow downloads only to `$RUNNER_TEMP`, validates
the request, requires the caller's checksum, installs `requirements.txt`, and calls the local
command. Inputs are `source_url`, `expected_sha256`, `maximum_batch_size`, `selected_batch`,
`mode`, `reviewer`, and `review_reference`. `dry-run` is the default. `reviewed-promotion`
requires one exact deterministic batch plus both reviewer fields. The workflow has read-only
repository permission, a 90-minute timeout, a safe pip cache, and no commit, PR, merge, or
full-corpus promotion step.

The local `scripts/mtgjson_delivery.py` command accepts an existing regular non-symlink file and
calls `MTGJSONDatasetDelivery`, which in turn composes the public Phase 106 API. It never copies
source bytes into reports and never prints them.

## Checksum, storage, licensing, and retention policy

An explicit 64-character SHA-256 is mandatory; missing, malformed, or mismatched values fail
before provider execution or canonical writing. Provider validation then rejects malformed JSON,
unsupported AllPrintings shapes, and unsupported schemas. Reports retain byte length, digest,
MTGJSON attribution, and the CC BY 4.0 licensing assessment, but not source URLs containing
credentials or environment secrets. Do not put secrets in workflow inputs.

Local source corpora belong outside Git or below ignored `data/local/`. Workflow source bytes and
state remain in runner-temporary storage and are destroyed with the runner. Only machine-readable
reports, manifests, review-package summaries, validation results, and performance observations
are uploaded for 30 days. `.gitignore` excludes `data/local/`; operators must inspect `git status`
before committing.

## Commands

Set shell variables first:

```bash
export PYTHONPATH=src
SOURCE=/absolute/path/AllPrintings.json
SHA256=<reviewed-64-character-sha256>
ROOT=data/local/phase-107
```

Verify existing bytes without ingestion:

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" verify --source "$SOURCE" --sha256 "$SHA256"
```

Parse and plan the complete corpus, stopping before promotion (the default safe operation):

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" --batch-size 1000 plan --source "$SOURCE" --sha256 "$SHA256"
```

List deterministic dependency-closed batches:

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" --batch-size 1000 list --source "$SOURCE" --sha256 "$SHA256"
```

After an independent reviewer examines one `review-package.json`, promote that exact batch only:

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" --batch-size 1000 promote \
  --source "$SOURCE" --sha256 "$SHA256" --batch batch-NNNNNN-DIGEST \
  --reviewer REVIEWER_ID --review-reference REVIEW_TICKET_OR_AUDIT_ID
```

Verify Query, Analytics, Semantic, Reasoning, and replay state:

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" verify-downstream
```

Roll back the selected promotion using its reported promotion ID:

```bash
python scripts/mtgjson_delivery.py --data-root "$ROOT" rollback \
  --promotion-id PROMOTION_ID --actor ROLLBACK_APPROVER \
  --timestamp 2026-07-31T12:00:00+00:00
```

Rollback is compensating history: evidence, review, versions, and audits remain retained.

## Reports and determinism

Reports are written under `ROOT/reports/mtgjson-delivery`: acquisition, checksum verification,
provider validation, corpus summary, deterministic batch plan and digest, selected review batch,
promotion, typed projection, downstream verification, performance/memory observations, and
rollback instructions/results. Stable inputs produce stable identities, batch ordering, plan
digests, and ingestion manifests. Timing and peak-memory fields are observations and therefore
are not represented as stable content digests.

## Triggering the first real run

1. Obtain the reviewed official SHA-256 through the project's independent source-review process.
2. In GitHub, choose **Actions → MTGJSON production ingestion → Run workflow**.
3. Keep `mode=dry-run`; enter the approved URL, digest, and a positive maximum batch size.
4. Download the workflow artifact. Review `checksum-verification.json`,
   `provider-validation.json`, `dataset-summary.json`, `batch-plan.json`, and the selected
   dependency-closed review package.
5. Have an independent reviewer record a durable review reference.
6. Re-run the same workflow with the same URL, checksum, and batch size; select
   `reviewed-promotion`, paste exactly one batch ID, reviewer identity, and review reference.
7. Require a green workflow and inspect promotion, projection, downstream, performance, and
   rollback reports. Do not merge or authorize another batch until that review is complete.

The hosted Codex attempt remained HTTP 403, so no real corpus counts or production promotion are
claimed here. Fixture execution validates both paths; the exact workflow steps above are the
remaining operational action.
