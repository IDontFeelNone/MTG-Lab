# Official Reference Dataset Acquisition

> **Status:** Phase 105 implemented — acquisition only. Architecture v12 is unchanged.

## Scope and architecture assessment

Official Reference Dataset Acquisition retrieves approved upstream artifacts into local,
Git-ignored storage. It is an operational extension of the Multi-Source Evidence Framework,
not a new truth authority. The Canonical Repository remains the sole source of truth.
Downloaded files and their registrations are non-canonical evidence and cannot become canonical
without the existing provider validation, independent review, promotion, and typed-projection
boundaries. Acquisition exposes no call to those later stages.

The merged Phase 104 baseline was confirmed at merge commit `62d61cb` before implementation.
No architectural defect or Architecture v12 change was required.

## Supported datasets and configuration

The initial approved definition is `mtgjson`: MTGJSON `AllPrintings.json`, provider `mtgjson`,
official URL `https://mtgjson.com/api/v5/AllPrintings.json`, uncompressed JSON, local path
`data/local/reference-datasets/mtgjson/all-printings/AllPrintings.json`, and supported schema
family `5.x`. Definitions also carry an expected filename, compression, optional checksum URL,
and schema version. The immutable configuration contract and registry permit additional reviewed
official datasets without adding game- or product-specific acquisition logic.

## Acquisition lifecycle

```text
approved official URL -> streamed download -> resumable .part file -> integrity gates
  -> SHA-256 identity -> artifact registration -> reference-dataset registration
  -> ready for explicit provider import
```

HTTP range requests resume interrupted transfers. If a server ignores a range and returns `200`,
the partial is safely replaced rather than appended. The completed artifact is atomically renamed
only after every download-time gate succeeds. An existing verified artifact is idempotently
reported as `already_downloaded`; it is never fetched or silently replaced.

## Verification and checksum policy

Verification fails closed on a missing or empty file, malformed JSON, unsupported/missing MTGJSON
schema metadata, SHA-256 mismatch, registration mismatch, invalid registration, or configured
official-checksum failure. SHA-256 is always computed and recorded. When a dataset definition has
an official checksum URL, acquisition must retrieve and match its SHA-256; an unavailable or
malformed checksum response fails the operation. MTGJSON does not currently publish a configured
checksum endpoint in the approved definition, so its locally computed SHA-256 is bound into both
artifact identity and registration and is rechecked by `verify`.

Failed downloads retain only the `.part` file for safe resume. Files that fail checksum, JSON, or
schema verification are never renamed or registered. Acquisition success means only “ready for
provider import”; it says nothing about canonical eligibility.

## Storage layout

```text
data/local/reference-datasets/
  mtgjson/all-printings/
    AllPrintings.json       # downloaded artifact
    AllPrintings.json.part  # interrupted transfer only
    acquisition.json        # definition plus artifact/dataset registration
  registry/
    artifacts/              # immutable content-addressed evidence registrations
    datasets/               # immutable content-addressed dataset registrations
```

The entire `data/local/` tree remains ignored by Git. Downloaded artifacts and local
registrations must never be committed or redistributed from this repository.

## CLI

All commands emit deterministic JSON envelopes:

- `mtg-lab dataset download mtgjson`
- `mtg-lab dataset verify mtgjson`
- `mtg-lab dataset status mtgjson`
- `mtg-lab dataset list`

Failures return exit status `2` with a JSON error and `canonical_write: false`. These commands do
not invoke provider import, candidate review, promotion, projection, or any canonical writer.

## Updates and licensing

Updates are explicit operator actions. A verified existing logical artifact is not overwritten;
the operator must archive/remove the local copy before acquiring a newly published version.
Registrations use content-derived identifiers, so distinct upstream bytes cannot collide or
masquerade as the previous acquisition. Provider import must be separately invoked afterward.

MTGJSON attribution and CC BY 4.0 assessment metadata are retained in each local registration.
Operators remain responsible for reviewing current upstream terms, attribution, and redistribution
constraints before enabling new definitions or distributing derived materials. Local acquisition
does not grant permission to commit or redistribute the source corpus.

## Evidence Framework integration

The subsystem creates the existing `EvidenceArtifact` and `EvidenceDataset` contracts through the
existing `ReferenceDatasetRegistry`. This preserves acquisition time, official source identity,
byte length, SHA-256, licensing, schema version, and pending review state. The MTGJSON provider may
then consume the local artifact through its unchanged import workflow. Registration is evidence
inventory, not validation approval, human review, promotion authorization, or typed projection.
