# Multi-Source Evidence Acquisition Framework v1

**Status:** Phase 98 framework; no live acquisition or dataset population  
**Architecture:** v12, unchanged

## Provider architecture

`evidence` defines immutable provider, source, dataset, artifact, request, result, capture,
license, and review contracts. An `EvidenceProviderAdapter` reports metadata and capabilities,
plans acquisition without performing networking, and validates artifacts and datasets. The
explicit provider registry rejects duplicate identifiers and unsupported licensing.

The abstraction supports official sources, structured reference datasets, and MTG Lab curated
research. Pricing, tournament, inventory, and collection-import adapters may implement the same
interface later; none is implemented by this milestone. Provider-specific parsing and transport
remain at the edge and must not introduce product-specific engine behavior.

## Reference dataset policy

Reference datasets are evidence, not canonical facts. The deterministic filesystem registry
records dataset/provider identity, schema and dataset versions, acquisition time, license and
source metadata, supported entity types, artifacts, and review state. Registrations serialize as
sorted compact UTF-8 JSON. Identical replay is idempotent; reuse of an identifier for different
content fails. Artifact bytes are identified by lowercase SHA-256.

The registry deliberately exposes no canonical write or promotion method. Registration never
implies validation, review, acceptance, or canonical authority.

## Acquisition lifecycle and promotion boundaries

```text
Evidence Provider -> Artifact Registration -> Dataset Registration -> Validation
 -> Independent Review -> Promotion Candidate -> Existing Canonical Promotion Engine
```

Every arrow is an explicit boundary. Validation reports eligibility, not truth. Independent
review must be recorded before a candidate can enter the existing promotion workflow. Only that
workflow may update the Canonical Repository, which remains the sole source of truth. Query,
analytics, semantic, reasoning, and AI contracts are unchanged.

## Licensing model

Providers, sources, datasets, and artifacts carry source identity as applicable. Provider,
dataset, and artifact registrations declare attribution requirements, redistribution policy,
licensing assessment, assessor, and assessment time. Artifacts additionally retain acquisition
and capture metadata plus content hash. Empty, `unknown`, `unassessed`, or `unsupported`
redistribution/assessment states fail closed. A successful assessment does not grant canonical
authority and does not override external terms.

## Extension strategy and roadmap

Adapters should remain independently testable, deterministic, and network-free at the contract
boundary. Future work may add separately approved official-source captures, an MTGJSON adapter
over supplied immutable bytes, or curated-research registrations. Later pricing, tournament,
inventory, and collection-import providers must use their existing domain boundaries and this
evidence lifecycle where applicable. Live downloads, credentials, schedulers, automatic review,
automatic promotion, and provider-specific canonical mappings require separate milestones.

## CLI

`mtg-lab evidence providers`, `datasets`, `artifacts`, and `validate` return deterministic JSON;
`--format json` is explicit and is currently the only format. Empty registries are valid. The
commands inspect or validate non-canonical registrations and never acquire or promote data.
