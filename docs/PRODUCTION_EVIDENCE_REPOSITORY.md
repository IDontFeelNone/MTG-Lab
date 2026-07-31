# Production Evidence Repository

> **Phase 111 — implemented 2026-07-31. Architecture v12 unchanged.**

> **Phase 112A adapter:** Native MTGJSON Actions artifacts use a nested streaming layout rather
> than this repository's root intake envelope. The deterministic adapter documented in
> `GITHUB_PRODUCTION_EVIDENCE_INTAKE.md` verifies and normalizes that retained evidence before
> invoking this Phase 111 API unchanged. The observed missing-root-manifest failure was a layout
> mismatch, not evidence corruption; no verification, review, or promotion boundary was weakened.

## Baseline confirmation

The implementation baseline is merged Phase 110B at merge commit `f7989ba` (implementation
commit `07bcccf`). Its failed-closed result is preserved: run `30663562841` and expected batch
`mb2-batch-000001-e32022126c07` are not present, no candidate was reviewed, and no canonical
write or promotion occurred. Phase 111 supplies the missing permanent intake mechanism but does
not fabricate or retrieve that production evidence.

## Authority and scope

The Production Evidence Repository permanently retains verified evidence from successful
production workflows so later sessions do not depend on expiring GitHub artifact downloads.
It is non-canonical: the Canonical Repository remains the sole source of truth, intake never
reviews candidates, approves a package, promotes a fact, or writes canonical state.

## Layout

Repository-owned evidence lives below `data/production_runs/`:

```text
data/production_runs/
  index.json
  RUN_ID/
    manifest.json
    metadata.json
    batch_index.json
    review_batches/       # compact immutable JSON bundles
    findings/             # referenced findings, when retained
    dependency_reports/   # bounded closure evidence
    lineage/              # source and transformation lineage
    summaries/            # bounded run reports
```

A run directory is immutable after intake. The repository excludes the full MTGJSON dataset,
nested archives, databases, transient workspaces, checkpoints that are not evidence, and
unrelated temporary files. Large candidate payloads are not copied into every bundle: bundles
retain content-addressed payload references and only bounded material needed for review.

## Archive contract and intake

A ZIP contains a root `manifest.json`, `metadata.json`, `batch_index.json`, and every file
listed by the manifest. The manifest schema is `1.0.0`; it records the GitHub run ID, workflow
name, repository, commit SHA, source dataset identity and SHA-256, plus exact path, byte length,
and SHA-256 for every other member. `metadata.json` repeats run and source lineage at the
operational boundary. The batch index identifies the target product, candidate-ID digest,
bundle path, and bundle digest for every retained batch.

Run intake with:

```bash
mtg-lab --data-root data evidence intake ARTIFACT.zip \
  --sha256 ARCHIVE_SHA256 --run-id RUN_ID --format json
```

Intake verifies the supplied archive digest before parsing; rejects unsafe or duplicate ZIP
members; matches the requested run to both workflow manifest and metadata; requires complete
workflow and source lineage; checks the inventory is exact; recomputes every internal size and
digest; validates each indexed bundle; and only then atomically installs the run. Existing run
IDs are rejected, including byte-identical duplicates, making accidental re-intake visible.
A failed intake leaves no run directory.

## Immutable review bundles

Each indexed bundle contains the review package, candidate IDs, dependency closure, payload
references, provenance, findings, lineage, and deterministic digests. Bundle bytes have their
own digest in `batch_index.json`, which itself is covered by the run manifest. Payload references
are content-addressed so the package can preserve identity without multiplying large payloads.
Approval fields retain their actual workflow state; intake does not turn `pending` into approval.

## Indexing and lookup

`index.json` is a deterministic, sorted projection rebuilt from retained run manifests and batch
indexes. It lists production runs and indexes exact source hashes, target products, batch IDs,
and workflow identities (`repository:workflow:commit`). It is disposable and reproducible; the
immutable run records, not the index, are evidence. Commands emit sorted JSON:

```bash
mtg-lab --data-root data evidence runs --format json
mtg-lab --data-root data evidence inspect RUN_ID --format json
mtg-lab --data-root data evidence batches RUN_ID --format json
mtg-lab --data-root data evidence verify RUN_ID --format json
```

`verify` recomputes the retained inventory, byte sizes, file hashes, and deterministic tree
digest and fails closed on additions, deletion, or modification.

## Retention and lifecycle

1. A successful workflow creates a bounded artifact and publishes its archive SHA-256 out of band.
2. An operator obtains the immutable ZIP and verified digest and runs intake with the expected ID.
3. The resulting run is committed and reviewed like code. Failed and incomplete workflow output
   is not represented as a successful retained run.
4. Review consumes a verified batch bundle and records a separate immutable decision. Evidence
   intake alone grants no approval.
5. Bounded promotion may consume only a genuinely approved, dependency-closed package through the
   existing promotion gate. Promotion remains a separate operation and sole canonical writer.
6. Superseded evidence remains for history. Corrections arrive as a new workflow run; retained
   run bytes are never edited. Removal requires an explicit documented retention decision.

This lifecycle implements permanent availability without creating parallel truth or weakening
source, review, and promotion boundaries.
