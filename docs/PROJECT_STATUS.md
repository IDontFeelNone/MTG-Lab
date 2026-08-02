# Phase 127H status — deterministic workflow dependency installation

Main contains merged Phase 127G at `32b6ad4`. The latest real Market acquisition run
successfully passed the focused gzip/JSONL tests but the repository-wide suite stopped with
53 `jsonschema` import errors because that workflow did not install the repository's declared
dependencies. Phase 127H restores the same `requirements.txt` installation boundary used by
the standard Python validation workflow before acquisition or validation executes. Provider,
parser, persistence, canonical, promotion, and production-coverage behavior are unchanged.

# Phase 127G status — official gzip JSONL streaming

Phase 127F is merged at `d64b1b2`. Its real dry run successfully completed the official metadata and secure JSONL URI path, but rejected the HTTP 200 `application/gzip` payload before reading bytes. Phase 127G repairs only that defect: gzip media requires independently valid framing and successful streaming decompression; decompressed UTF-8 JSONL is validated one record per nonblank line, while compressed/decompressed counts and deterministic digests are accumulated. The workflow remains dry-run-only. Observations and canonical bytes are unchanged, promotion is false, and coverage remains 0/379.

# Phase 126 status

Market Intelligence Foundation is implemented. Phase 125 is merged at `b71f961`; Phase 119 remains the sole production promotion at digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Architecture v12, canonical facts/contracts, Canonical Query Layer, Collection Intelligence, and generic automatic updates remain unchanged. Canonical facts still have no pricing. No recommendation engine, portfolio analysis, advice, or AI reasoning exists.

# Phase 123 status — provider acquisition blocked

Main contains merged Phase 122. Phase 119 remains the sole production canonical promotion and canonical digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f` is unchanged. The newest trusted provider version could not be determined because all approved MTGJSON endpoints returned HTTP 403. Consequently no refreshed checksum, evidence identity, target result, candidate, batch, descriptor, promotion, branch, PR, checks, or auto-merge state exists. Architecture v12 and canonical contracts remain unchanged.

# Phase 122 — requested real target unavailable in retained provider snapshot

The retained checksum-identified MTGJSON snapshot contains exactly MB2 and MSH and zero set-level matches for The Hobbit. Availability stopped fail-closed before a code or target could be selected. Counts are zero for every candidate entity and classification; dependency closure, descriptor creation, plan, verify, execution, promotion, audit, rollback, target branch, target PR, checks, and auto-merge are not applicable. Production digest remains `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`, with Phase 119 the sole promotion. Required green checks continue to protect merges. No MB2/MSH/Marvel/unrelated data, Architecture v12, or canonical contract changed.

# Phase 121 — synthetic validation complete

All sixteen automatic-update stages succeeded for isolated synthetic target `SYN`; the resulting fixture-only state contained 1 Set, 2 Cards, 2 Printings, 1 Identifier, and 2 Finishes and digest `47abe0658ad434f6485148592559a973a6f8f14694455a89cb0cb29b5b8e9327`. Recovery resumed eight authenticated checkpoints, replay was byte-idempotent, conflicting replay failed closed, and rollback planning was non-executing and human-gated. All requested negative and mocked GitHub persistence cases pass. The real production digest remains `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`; Phase 119 is still the sole promotion, with no second MB2 batch or MSH/Marvel data. Architecture v12/contracts remain unchanged.

# Phase 120 — implementation complete

The reusable pipeline, JSON CLI, MB2 completed-promotion reference, protected PR/auto-merge workflow, recovery rules, documentation, and tests are implemented. Phase 119 remains the only MB2 promotion: 1,000 candidates (384 Cards, 379 Printings, 235 Identifiers, 2 Finishes), post-state `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. No MSH or second MB2 batch was promoted. Architecture v12/contracts are unchanged. Merge awaits green required Actions checks.

# Project status after Phase 119


## Phase 119 — first verified MB2 bounded canonical promotion (2026-08-01)

Promotion **succeeded** for exactly evidence `30663562841-review-payload-v2`, batch
`mb2-batch-000001-e32022126c07`, and target MB2 / Mystery Booster 2. The immutable
Phase 115/116 review chain and every Phase 118 readiness gate were independently reverified
immediately before the write. Exact membership is 1,000 approved candidates: 384 Cards,
379 Printings, 235 Identifiers, and 2 Finishes. Candidate digest is
`e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e`. There are zero
unresolved, excluded, quarantined, fatal-conflict, or orphaned candidates. MSH/Marvel, every
other MB2 batch, and every unrelated candidate were excluded.

Canonical pre-state digest was
`0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba`; post-state digest is
`793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Immutable audit
`phase-119-mb2-batch-000001-e32022126c07` records exact membership, source/review lineage,
preflight digest `d0ea6939c6c282647e24f8873f3021430b451173477013ccaca2fff60d6e1aab`,
pre/post-state digests, deterministic dependency order, replay, and rollback metadata.

Replay with `promote(data_root)`; a byte-identical completed promotion returns idempotent
success without another write or audit. Conflicting replay fails closed. Roll back with
`rollback(data_root)`; it verifies the audited post-state, removes only this bounded canonical
state, verifies restoration of the pre-state digest, and retains immutable audit history.
Architecture v12 and canonical contracts are unchanged. Stop after Phase 119; merge remains
withheld until normal pull-request review and GitHub Actions are green.

## Historical state before Phase 119

Phase 118 removes the active Phase 117/117A operator-authorization subsystem. Operator signatures,
human identity fields, signature requests, authorization-only branches, and authorization artifacts
are not promotion prerequisites. Trusted-source validation plus normal pull-request review and green
GitHub Actions provide the active gate; Architecture v12 and canonical contracts are unchanged.

Evidence `30663562841-review-payload-v2`, exact batch
`mb2-batch-000001-e32022126c07`, is checksum-verified and MB2-only. All 1,000 candidates are approved
(384 Cards, 379 Printings, 235 Identifiers, 2 Finishes), with zero unresolved, quarantined, rejected,
or fatal-conflict candidates and valid dependency closure. Canonical pre-state remains
`0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba`.

The batch is technically ready for a separately invoked bounded canonical promotion. Promotion is
still explicit, exactly-one-batch, target-isolated, canonical-pre-state guarded, deterministic,
audited, and rollback capable. Phase 118 performed no canonical write or promotion and includes no
MSH/Marvel candidate.
# Phase 124 status

Collection Intelligence v1 is implemented: deterministic JSON/CSV collection import,
canonical resolution with retained uncertainty, immutable snapshots, summaries, deck
completion, and explainable price-independent priorities. Architecture v12 and production
canonical digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`
are unchanged; Phase 119 remains the only production promotion.
# Phase 125 status

The first canonical intelligence query API is complete. It deterministically exposes
existing Card, Printing, Product, collection, and deck-comparison facts through JSON without
inference. Phase 124 is merged at `de12a6b`; Phase 119 remains the sole production promotion.
Architecture v12, canonical contracts/data, generic automatic updates, and completed
Collection Intelligence are unchanged. No pricing or AI-provider integration exists.
# Phase 127 — acquisition boundary implemented; live access blocked

Phase 126 is merged at `30db5d4`. Scryfall default-card bulk data is the sole selected
production market source. Its adapter, deterministic exact identifier resolver, bounded
append-only persistence, workflow, query envelope completeness, and tests are implemented.
The execution environment's proxy returned HTTP 403 before the official API responded;
no provider payload, production observation, or collection valuation was retained.
Coverage is exactly 0/379 promoted MB2 Printings. Architecture v12/contracts and Phase
119 canonical state remain unchanged; there is no recommendation engine or AI provider.

# Phase 127A status — operationally blocked

Phase 127 is merged (`ad0797e`). The repository has no retained production market
observations and therefore 0/379 queryable MB2 coverage. The existing GitHub Actions path is
still the required next operation. Its first run could not be audited from this execution
environment because outbound GitHub and Scryfall CONNECT requests returned proxy HTTP 403.
Architecture v12, canonical contracts/data, and Phase 119-only promotion remain unchanged.

# Phase 127B status — acquisition diagnostics repaired

Phase 127A is merged at `fc9a041`. The failed GitHub-hosted dry run exposed an
implementation error: the metadata request used `default-cards`, while Scryfall's official
bulk-data type/path is `default_cards`; Scryfall therefore returned permanent HTTP 404.
The official endpoint, descriptive request headers, bounded transient-only retries, response
validation, sanitized stage diagnostics, always-retained workflow artifact, and original
exit-status propagation are now implemented. A provider failure stops before persistence.
No market observation or canonical data was written; coverage remains 0/379.

# Phase 127C status — Scryfall metadata parser repaired

Phase 127B is merged at `21f9b6e`, and its official endpoint repair succeeded: GitHub Actions reached Scryfall and received JSON metadata. The authoritative diagnostics stopped at `download_uri_extraction` before any payload download because the parser did not handle the official list envelope. Phase 127C defensively supports both official metadata shapes and validates the exact secure Scryfall data-host boundary. No live payload or price was retained, coverage remains 0/379, and no canonical write or promotion occurred. The next operation is one post-merge `persist=false` workflow dispatch.

# Phase 127F status — official JSONL transport supported

Baseline `ba8f8c3` contains merged Phase 127E. Its real dry run preserved the exact official
descriptor but proved that Scryfall supplies `jsonl_download_uri`, not the assumed
`download_uri`. Phase 127F implements fail-closed transport selection, bounded streaming
JSONL/gzip validation, duplicate rejection, MB2-only retention, safe format diagnostics,
and deterministic source/normalized digests. Persistence is prohibited. No production market
or canonical data changed, no promotion occurred, and MB2 market coverage remains 0/379.

# Phase 127I status — automatic durable acquisition evidence

Phase 127H is merged at `8cf298f`. Its post-merge Market acquisition workflow completed
successfully: the official bounded Scryfall acquisition passed, retained an MB2-only provider
projection and dry-run report as a 14-day Actions artifact, and performed no canonical write,
promotion, or market-observation persistence. Consequently production MB2 market coverage is
still 0/379. The successful evidence is not copied into this implementation branch and no data
was reacquired or fabricated.

Phase 127I makes the repository the durable handoff boundary. Every subsequent successful run
validates the dry-run report and MB2 projection, then creates
`data/market/acquisitions/<acquisition-run-id>/manifest.json`, `dry-run-report.json`, and
`source-mb2.json`. The manifest records run/timestamp/provenance, provider and normalized
digests, mapping and price censuses, the mapping canonical snapshot identity, explicit false
write flags, and SHA-256/byte length bindings for both retained payload files. The complete
Scryfall bulk dataset and normalized observations are never retained.

Automation uses deterministic branch `market-acquisition/<acquisition-run-id>`, commits exactly
those three files, pushes without force, creates or safely reuses the exact Phase 127I PR,
independently verifies base/head/SHA and the changed-file boundary, requires actual base-branch
protection and all required checks to succeed, and only then requests squash auto-merge. Replay
is byte-idempotent; branch collisions, conflicting evidence, absent protection, changed-file
boundary violations, or failed checks stop closed. The always-uploaded diagnostic artifact
remains available for failures.
