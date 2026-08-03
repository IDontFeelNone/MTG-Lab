# Phase 133 handoff

Pilot `phase-133-mb2-printing-history-v1` retains the Phase 132 ten-card scope and adds one known,
evidence-bound reprint-history aggregate per Card. Active queries return the Phase 133 fact; full
history returns it alongside the unchanged Phase 132 unknown. Counts cover canonical MB2 Printing
records only, while the separate set-code list is reported as an asserted membership list and never
converted into fabricated Printing identities. All ten coverage states are incomplete. Review
`data/reviews/phase-133/pilot-review.json`; do not interpret the zero bounded reprint count as no
historical reprints or as a supply statement. Architecture v12 and protected data remain frozen.

# Phase 132 handoff — first reviewed Card Intelligence facts

Phase 131 is merged at `0e2b89c`. The Phase 132 pilot adds exactly 90 append-only production facts
for ten alphabetically ordered MB2 Cards, with 70 known values and 20 explicit unknowns. Use the
existing `CardKnowledgeQuery` projections to inspect all/active, value-driver, legality, archetype,
catalyst, evidence-source, and confidence results. Archetype and catalyst results are intentionally
empty. The deterministic review is `data/reviews/phase-132/pilot-review.json`. Canonical data,
acquisitions, imports, and all 478 observations are unchanged; inference and promotion are false.

# Phase 130 historical-query handoff

Baseline `73fb1de` contains Phase 129 and the unchanged Phase 128 production corpus: 478 immutable
Scryfall observations, one retained acquisition, and 379/379 MB2 Printing coverage. Phase 130 adds
only `market-history-report-v1` read paths. Use `PYTHONPATH=src:. python -m market.cli --help` for
the inventory and `--data-root` for an alternate retained tree. Listing is chronological, defaults
to 100, and rejects limits outside 1..500. First/latest never synthesize an observation; count is
exact; time ranges and as-of are inclusive source-observation timestamps; snapshot chooses the last
observation per Printing/provider/finish/language/currency/price-type dimension without collapsing
dimensions. Coverage is promoted canonical MB2 coverage. Acquisition summary binds its observation
census to retained manifest timestamps, canonical identity, and source/normalized digests.

All successful responses contain schema version, report type, normalized filters, canonical
snapshot identity when applicable, result count, truncation, ordering, explicit empty state, and
retained observation provenance. Invalid filters return `market-history-error-v1` and exit 2.
No command has an acquisition, append, import, canonical-write, or promotion path.

# Phase 128 handoff

Phase 128 imported exactly `scryfall-mb2-30754638264-1`. Evidence remains the unchanged three-file acquisition directory. Production now contains 478 append-only `market-observation-v1` files and one deterministic import report: 379 matched printings, six unmatched finish mappings, zero ambiguous/rejected/duplicate/unsupported mappings, 478 known prices, and zero missing prices. Replay accepts only identical report and observation bytes; conflict fails closed. Complete validation precedes staging, and injected partial-write failure removes staging without publication. Coverage is 379/379 from 0/379. Canonical data and promotion state are unchanged.

# Phase 127L handoff

Review and merge the explicit required-check registration repair. The existing successful
`scryfall-mb2-30730690426-1` evidence branch and PR must be preserved: dispatch Python validation
on that exact head, wait for GitHub to register at least one required check, require all required
checks to succeed, and let repository rules govern auto-merge. Do not reacquire, import market
observations, change canonical data, or promote.

# Phase 127K handoff

Review and merge the removal of the unsupported branch-protection REST read. The successful
`scryfall-mb2-30730690426-1` evidence branch and PR already exist; rerun or safely reuse them,
wait for a nonempty all-green required-check set, and let repository rules govern auto-merge.
Do not import observations, write canonical data, promote, or reacquire under a different run ID.

# Phase 127G handoff

Phase 127F is merged (`d64b1b2`). Its real dry run proved the official metadata, `jsonl_download_uri`, URI validation, and data-host connection path, then received HTTP 200 `application/gzip` and correctly retained nothing because that media type was unsupported. Phase 127G streams and validates the gzip JSONL response without changing metadata selection or URI policy. Merge, run one dry-run-only dispatch, inspect diagnostics and the bounded MB2 artifact, and stop before persistence. Production observations remain empty, canonical state remains Phase 119 only, no promotion occurred, and MB2 market coverage is 0/379.

# Phase 127E handoff

Phase 127D is merged at `7cfe964`. Its real dry run stopped at the combined `blank_uri`
classification before URI security validation and made no writes. Phase 127E retains the exact
selected provider descriptor for transport, separates value-free diagnostic projection, and
reports exact field extraction reasons. Run exactly one post-merge `persist=false` dispatch and
stop before persistence regardless of outcome. Coverage remains 0/379; canonical state and
promotion are unchanged.

# Phase 127D handoff

Phase 127C is merged at `a837210`. Its real dry run established that the remaining failure
was the exact-host URI policy after successful direct metadata selection and timestamp
validation. Phase 127D admits only label-aware official static subdomains beneath
`scryfall.io` with the remaining secure URL constraints and sanitized diagnostics. Coverage
is still 0/379. Run one post-merge `persist=false` workflow dispatch, inspect it, and stop;
do not persist observations or alter canonical state in this phase.

# Phase 126 handoff

Start with `docs/MARKET_INTELLIGENCE.md`, `src/market/intelligence.py`, and `src/market/query.py`. Observations are append-only and separate from canonical facts; queries preserve unknowns. Phase 125 is merged, Architecture v12 is unchanged, and Phase 119 remains the sole production promotion. No live feed, recommendation engine, portfolio analysis, or AI reasoning was added.

# Phase 123 handoff

Phase 123 stopped fail-closed at trusted acquisition. Retry the approved MTGJSON acquisition path in an environment that can reach the provider and supplies its trusted SHA-256; pass those bytes and digest to `register_trusted_snapshot`, then run the unchanged exact-one set-metadata gate. Never reuse the Phase 122 identity, infer a Hobbit code, inspect card text, or substitute LTR/Commander/scene/Secret Lair products. If zero matches remain, retain the new result and stop; only one complete match may enter the generic automatic-update pipeline.

# Phase 127J handoff

Review and merge the changed-file verification repair, then rerun Market acquisition once. The
pre-branch status must contain exactly three durable evidence paths plus four workflow diagnostic
paths; only the three evidence files may be staged and committed. Allow protected checks and
auto-merge to govern the evidence PR, then stop before observation import or canonical changes.

# Phase 122 handoff

Phase 122 stopped correctly at availability. Trusted retained MTGJSON evidence identity `mtgjson-allprintings-5.3.0+20260731-b47cc8360034` (source SHA-256 `b47cc83600341e18663bdb48fe9d1337730976844465a35e75bcde5ac6f00d09`) inventories only MB2 and MSH. It has no Hobbit match, so no exact code, new evidence/batch identity, candidates, descriptor, canonical run, rollback, or target PR exists. The next attempt requires a newer trusted checksum-verified MTGJSON snapshot; it must repeat the exact-one availability gate and must not substitute another product. Production remains unchanged and protected merges still require green checks.

# Phase 121 handoff

Review the synthetic-only validation and withhold merge until required GitHub Actions checks are green. `SYN` proved the standard engine without an MB2 branch: sixteen stages, interruption recovery, immutable audit, idempotent replay, conflicting-replay rejection, and non-executing rollback plan all passed in temporary roots. Before a live new set, retain licensed trusted-provider evidence, independently review its complete candidates and provenance, approve its bounded descriptor, confirm repository settings/required checks, and run through the protected workflow. Do not copy the synthetic fixture into production data.

# Phase 120 handoff

Review the Phase 120 PR and allow protected auto-merge only after required Actions checks are green. Future routine trusted sets use retained evidence plus a descriptor, not engine edits or recurring signatures. Human action remains required for conflicts, ambiguity, validation failure, drift, contract change, destructive action, or rollback.

# Phase 119 handoff


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

Review and merge Phase 118 only after GitHub Actions are green. The active architecture no longer
uses operator signatures or authorization-only pull requests. Normal PR review and CI are sufficient
human oversight for a trusted-source batch that passes every fail-closed validation gate.

The first MB2 batch has 1,000 approved candidates, zero unresolved/quarantined/conflicting
candidates, valid dependency closure, MB2-only isolation, verified evidence, and an exact canonical
pre-state. It is technically ready, not promoted. The next phase is an explicitly invoked bounded
canonical promotion of this one batch with deterministic audit and rollback support. No canonical
write or promotion occurred in Phase 118.
# Phase 124 handoff

Review and merge the Collection Intelligence Foundation. It is downstream-only and needs no
authorization form. Do not begin pricing or market intelligence before review. The next useful
boundary is collection/deck contract hardening and richer canonical attribute coverage.
# Phase 125 handoff

Phase 125 adds the first high-level `canonical-query-v1` service and JSON CLI over existing
canonical and collection facts. Review `docs/CANONICAL_QUERY_LAYER.md` for operations and
limitations. Phase 124 baseline `de12a6b` is merged; production remains solely Phase 119 at
digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`.
Canonical data/contracts and Architecture v12 were not modified. Stop after Phase 125.
# Phase 127 handoff

Review and merge the Scryfall acquisition boundary. Then manually dispatch **Market
acquisition** with `persist=false` in an environment that can reach `api.scryfall.com`.
Inspect diagnostics before a separate `persist=true` dispatch. Current production market
coverage is 0/379 due to the documented outbound-proxy HTTP 403. Do not claim prices,
collection value, or full coverage until the Action retains and verifies them. No secret
is required; enable Actions PR creation and optional repository auto-merge.

# Phase 127A handoff

Resume workflow-first: inspect the retained `market-acquisition-*` artifact for the first
Phase 127 Actions run before dispatching anything else. If its dry run is valid, persist the
exact retained payload once; if persistence already exists, reuse it idempotently. This
checkout has zero production observations and cannot supply price, history, or collection
value proof. Do not replace missing access with fixtures or zero prices.
# Phase 129 multi-acquisition handoff

Phase 128 is merged at `7f5ce36`, and the production retained MB2 import is complete: 478
immutable observations cover 379/379 MB2 Printings. Phase 129 removes the former empty-store
restriction. Every run is independently revalidated from its retained three-file evidence,
normalized with acquisition provenance, staged, then appended under content-derived observation
identities. Existing files are never replaced. The import report is the run commit marker.

Replay reloads and verifies the immutable report plus every expected observation byte. An
identical replay returns the retained report; altered reports, altered observations, reused run
identity with different lineage, or destination collisions fail closed. Before the commit marker
is installed, any publication failure unlinks only paths published by that attempt, preserving
all earlier runs. Repository queries support acquisition, UTC observation date, as-of instant,
ordered printing history, first/latest observation, and counts.

Run `PYTHONPATH=src:. python -m unittest tests.test_phase_129_market_history` before importing
another retained run. No test performs acquisition. Canonical state is read only and guarded by
its snapshot digest; reports continue to state `canonical_write: false` and
`promotion_performed: false`. Architecture v12 is unchanged. Phase 130 should expose these
history/report capabilities through a read-only operator CLI, without trend inference.
# Phase 131 handoff — deterministic Card Intelligence foundation

Baseline `4e34eaf` contains merged Phase 130. The new `src/card_intelligence/` package contains
immutable contracts, strict parsing, canonical serialization, an append-only repository loader,
cross-record supersession validation, and read-only query projections. Canonical JSON schemas are
`src/schemas/v1/card-knowledge-fact.schema.json` and
`src/schemas/v1/card-knowledge-query.schema.json`. A future populated repository uses
`data/knowledge/facts/<game-id>/<card-id>/<fact-id>.json`; Phase 131 intentionally adds no facts.

Safety boundary: all records require evidence, provenance, effective time, and an explicit known or
unknown value. Confidence may itself be unknown. Corrections append a later record naming the prior
fact in `supersedes`; bytes are never replaced, and replay/load verifies canonical bytes, paths,
identities, references, chronological direction, and cycles. Query results deterministically expose
all facts, active facts, value drivers, competitive formats, archetypes, catalysts, sources, and
confidence values. The engine performs no inference. Future AI may retrieve these reports but may
not write facts or treat them as generated conclusions.

Canonical data, acquisitions, the 478 retained observations and import report are unchanged. Phase
119 remains the sole promotion, market and knowledge promotion are false, and Architecture v12 is
still frozen.
