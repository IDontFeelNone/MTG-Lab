# Decision Intelligence Contract Foundation handoff

The checked baseline was `19b69c2` / PR #156, with Phase 147 still the highest merged project phase.
The foundation is an additive Architecture-v12 implementation: five versioned contracts and schemas,
a deterministic ordered-criteria policy, stateless orchestration, first-class abstention,
reproducible identities, and a complete recommendation projection for downstream explanation. All
validation is synthetic-only and production repositories were not modified. Continue with
`DECISION_INTELLIGENCE.md`; stop before Product Intelligence unless separately authorized.
Competitive Intelligence remains parked.

# Historical Decision Intelligence assessment handoff (implemented)

The checked-out baseline is merge commit `1574f7778cc0748b14544ead631b4c906eedcd41`
(GitHub PR #155); Phase 147 remains the highest merged project phase. Phase numbers and PR numbers are
independent. The assessment in `DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md` found no Architecture
v12 defect. Product and Deck Intelligence should share a generic Decision Intelligence contract, with
a thin acquisition orchestrator over domain analytics and the existing Decision Engine.

The assessment's synthetic-only Decision Intelligence Contract Foundation is now implemented.
Neither domain, live provider integration, nor ChatGPT provider was implemented. Competitive
Intelligence remains parked.

# Roadmap reconciliation handoff (historical)

The inspected mainline baseline was `bf2976c0c42153f11756bd362767356f23671cfc`: project Phase 147
is merged through GitHub PR #154 and is the highest project phase present. Competitive Intelligence
is now **PARKED / KNOWN GAP / NOT ON CURRENT CRITICAL PATH**, with tournament evidence allowed to
remain unknown and no further acquisition authorized. Existing provider-neutral validation,
fail-closed gates, legal unknowns, and transport-free adapter are sufficient preparation.

Wait for the separate Product Intelligence requirement. The next recommended major capability is a
generic, collection-aware, provenance-rich acquisition-decision vertical—not another evidence source.
No implementation, provider contact, secrets, evidence, facts, protected production data, or
Architecture v12 changes belong to this reconciliation. See
`ROADMAP_RECONCILIATION_2026_08_12.md` for the exact competitive resumption chain and capability gaps.

# Phase 146 handoff — no competitive acquisition authorized

All five candidates remain unverified because provider-controlled sources were unreachable (research service HTTP 401; HTTPS proxy HTTP 403). Licensing and retention are hard gates, so TopDeck.gg is no longer a conditional selection: no provider is approved. No production competitive evidence, facts, client, or workflow exists; the schema and explanation v1/v2/v3/v4 remain unchanged. See `PHASE_146_PROVIDER_VERIFICATION.md` for the source-attempt and gate matrices and the invariant bounded design.

# Phase 145 handoff — competitive evidence acquisition remains blocked

The retained-data census found no actual-play tournament evidence. Phase 145 adds only the
provider-neutral evidence envelope, fail-closed local validator, tests, and acquisition-design report.
TopDeck.gg is the single conditional pilot candidate, but the environment could not verify its API or
retention terms; no acquisition may run until human approval of those gates. No production evidence,
facts, explanation behavior, protected data, or Architecture v12 changed. See
`PHASE_145_COMPETITIVE_EVIDENCE_GAP.md` for metrics, denominators, rollback, and post-merge operation.

# Phase 144 — reviewed MTGJSON deck usage admitted

Phase 144 strictly reviewed `data/card_intelligence/demand/phase-143/mtgjson-decks.json` and admitted its literal ten-Card projection. The artifact is `card-deck-usage-evidence-v1`, provider `mtgjson`, dataset `AllDeckFiles.zip`, source SHA-256 `41b5c64a0a5797518cfb0d0584c5b2cba320ec955f775c40b4bbecfd66a298b1`, 259,140,526 source bytes, dataset/retrieval timestamp `2026-08-10T22:23:35Z`, and records SHA-256 `6f1dfb55554b145062b958a0655e5f43385d0d2a8fbfa9377e254b3928b14248`. Its denominator is exactly 3,004 distinct decoded provider deck files, not global decks, players, or the Magic population.

| Card | represented decks | denominator | represented % | literal formats | associations |
|---|---:|---:|---:|---|---:|
| Brainstorm | 23 | 3004 | 0.765646% | box set; commander deck; dandan deck; duel deck; jumpstart; secret lair drop; theme deck; world championship deck | 23 |
| Command Tower | 205 | 3004 | 6.824234% | box set; brawl deck; commander deck; historic brawl precon deck; secret lair drop | 205 |
| Counterspell | 63 | 3004 | 2.097204% | advanced deck; advanced pack; box set; commander deck; duel deck; enhanced deck; game night deck; mtgo redemption; pro tour deck; secret lair drop; shandalar enemy deck; starter deck; theme deck; world championship deck | 63 |
| Goblin Charbelcher | 4 | 3004 | 0.133156% | duel deck; mtgo redemption; world championship deck | 4 |
| Goblin King | 17 | 3004 | 0.565912% | box set; mtgo redemption; secret lair drop; shandalar enemy deck; theme deck | 17 |
| Sol Ring | 241 | 3004 | 8.022636% | box set; commander deck; secret lair drop; shandalar enemy deck | 241 |
| Swords to Plowshares | 78 | 3004 | 2.596538% | box set; commander deck; duel deck; game night deck; mtgo commander deck; mtgo theme deck; pro tour deck; secret lair drop; shandalar enemy deck; theme deck; world championship deck | 78 |
| Treasure Cruise | 15 | 3004 | 0.499334% | clash pack; commander deck; intro pack; mtgo redemption; pioneer challenger deck | 15 |
| Walking Ballista | 8 | 3004 | 0.266312% | challenger deck; commander deck; jumpstart; mtgo redemption; secret lair drop | 8 |
| Wishclaw Talisman | 3 | 3004 | 0.099867% | box set; mtgo redemption | 3 |

Admission appended 10 known `demand.deck_inclusion` and 10 known `format.usage` facts. No exact-predicate unknown existed, so zero facts were superseded and all 120 earlier facts were unchanged. Both predicates have known=10, unknown=0, incomplete=10, unsupported=0; inferred archetype remains unsupported for all ten Cards. Source ZIP-member path—not nullable or repeated provider deck code—is record identity. Literal deck names/formats remain associations only.

Opt-in `card-value-explanation-v4` now exposes Printing history, both retained MB2 price snapshots and descriptive history, independent Scryfall EDHREC rank, independent MTGJSON represented-deck evidence, literal associations, quality, provenance, and limitations. It adds no scores, valuation, prediction, popularity/scarcity conclusion, or recommendation. The ten Phase 142 facts, ten Phase 136 histories, Phase 135 evidence, canonical data, two MB2 acquisitions/imports, and 956 observations are unchanged. Architecture v12 remains frozen.

# Phase 142 handoff — reviewed demand evidence

The exact ten pilot Cards now have one reviewed provider observation each: Scryfall `edhrec_rank` from the retained default-cards snapshot observed at `2026-08-04T21:10:15.879000Z`. The bounded evidence is `data/card_intelligence/demand/phase-142/scryfall-edhrec-rank.json`; its ten records are digest-bound and deterministically mapped by canonical Card/Scryfall oracle ID and exact MB2 Scryfall Printing ID.

Ten Phase 142 `value_driver.demand` facts supersede only their corresponding Phase 132 unknowns. Known=10; unknown=0 for this predicate; all ten remain incomplete beyond the exact ordinal; competitive usage and archetype/deck inclusion are unsupported (20 card-dimensions). No pilot Card lacks the retained rank. Run `PYTHONPATH=src:. python -m card_intelligence.cli explain "Sol Ring" --include-demand-evidence` for opt-in v3 output. The rank is evidence, not a high/low-demand judgment or valuation input.

Protected boundaries are unchanged: 913 canonical Printings, 956 market observations across two retained snapshots, ten active Phase 136 histories, immutable Phase 132 history, retained Phase 135 evidence, and Architecture v12. Next, consider a separately reviewed deck-count provider acquisition without expanding the pilot.

# Phase 141 — historical explanation handoff

Run `PYTHONPATH=src:. python -m card_intelligence.cli explain "Sol Ring" --include-observed-prices --include-historical-movement` for authoritative JSON. The historical flag automatically enables observed-price evidence. Add `--human-readable` only for a rendering derived from that contract. Comparisons never cross Printing, provider, finish, language, currency, or price type. The output describes two retained MB2 snapshots only and is not completed-sales evidence, fair value, prediction, trend strength, score, ranking, or recommendation. The 956 observations, both three-file acquisitions, both import reports, canonical state, and knowledge facts are unchanged.

# Phase 140 — second production MB2 market snapshot imported

Phase 140 imported retained acquisition `scryfall-mb2-30959813191-1` from `data/market/acquisitions/scryfall-mb2-30959813191-1/` without provider contact or reacquisition. The retained boundary remains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`; verification binds manifest identities, source and normalized digests, byte counts, timestamps, canonical snapshot identity, MB2-only scope, and false write/promotion flags.

The import appended 478 immutable Scryfall/USD/market observations under `data/market/observations/printing/<printing-id>/scryfall/` and published `data/market/imports/scryfall-mb2-30959813191-1/import-report.json` last. Historical observations grew from 478 to 956; retained acquisition count grew from one to two; MB2 coverage remained 379/379. Mapping census is 385 retained source records, 379 matched canonical Printings, 478 matched observation dimensions, six unmatched finish mappings, and zero ambiguous, rejected, duplicate, unsupported, or explicit-missing price observations.

History readiness moved from `single_snapshot_only` to `multiple_snapshots_descriptive_only`: distinct source timestamps grew from one to two, all 478 exact Printing/provider/finish/language/currency/price-type dimensions are comparable multi-snapshot dimensions, and zero dimensions contain explicit missing prices. Descriptive historical movement is available only inside those exact dimensions and is not a prediction, reliable trend, momentum signal, valuation, ranking, recommendation, or expected return.

Replay is byte-identical and idempotent; conflicting report or observation bytes fail closed. Atomic rollback removes only files created by the current attempt before report publication. The first acquisition's observation bytes are preserved, canonical data and Card Intelligence facts are unchanged, `canonical_write` is false, `promotion_performed` is false, and Architecture v12 remains frozen.

# Phase 138 handoff

Use `PYTHONPATH=src:. python -m card_intelligence.cli explain "Sol Ring"` for unchanged v1 coverage output. Add `--include-observed-prices` to opt into v2 actual retained prices. V2 reads only immutable market observations and resolves them through canonical Printing IDs; it never substitutes Card identity or carries MB2 prices to historical Printings.

All numeric amounts are decimal strings. Observation and dimension ordering is explicit. A one-observation dimension is labeled `single_observation_no_trend`. Future snapshots should enter only through the existing separately authorized Market acquisition and import process; the explanation layer requires no writer.

# Phase 137 — explainable Card Value evidence engine handoff

The ten-card pilot now has deterministic `card-value-explanation-v1` reports generated directly from
read-only canonical, active knowledge, and market-observation repositories. Run with `PYTHONPATH=src:.`
and either `python -m card_intelligence.cli explain Sol Ring` or
`python -m card_intelligence.cli explain --card-id 6ad8011d-3471-4369-9d68-b264cc027487`.
The command emits stable, schema-valid JSON and fails closed outside the pilot.

Supported presentation categories are retained Printing History, market coverage (not price
interpretation), reviewed Rules/mechanical roles/legalities/product membership, and Evidence Quality.
Commander usage, tournament results, inventory, demand, global printing completeness, scarcity,
popularity, value conclusions, scores, rankings, forecasts, and recommendations are unsupported and
explicitly disclosed. Future work must first retain and review new evidence; the explanation engine
must remain a consumer and must never create facts. The 913 Printings, 534 promoted pilot Printings,
478 observations, ten Phase 136 histories, and Architecture v12 remain protected.

# Phase 137 — pilot Printing-history audit complete

Phase 137 performed a deterministic, read-only audit of the Phase 136 pilot history. The baseline is
merged and reconciled: canonical digest `881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077`,
913 canonical Printings, exactly 534 promoted non-MB2 Printings, ten pilot Cards, ten active Phase 136
facts, the Phase 132 → Phase 133 → Phase 136 historical chain for every Card, and 478 unchanged market
observations. Retained Phase 135 evidence and all prior fact bytes remain unchanged.

The exact promoted counts are Brainstorm 47, Command Tower 110, Counterspell 83, Goblin Charbelcher 8,
Goblin King 26, Sol Ring 135, Swords to Plowshares 96, Treasure Cruise 14, Walking Ballista 10, and
Wishclaw Talisman 5. All 534 canonical identities, Card links, provider UUIDs, set codes/names,
collector numbers, dates, languages, finishes, rarities, frames/treatments, acquisition runs, and source
record identities reconcile. The provider projection has 487 unknown promotional states (47 known
true), 500 unknown paper/digital states (34 known digital), and 11 unknown reprint states (523 known
true). Border indicators and field-level provenance are provider-unsupported for all 534 records; no
unknown was converted to false. There are 154 deterministic promoted set-code/name pairs. Finish,
language, treatment, promotion, reprint, and paper/digital inventories are normalized and sorted in the
audit report.

All ten Phase 136 facts match canonical Printing IDs, totals, derived reprint counts, distinct sets,
set inventories, date bounds, and elapsed spans. No defects, conflicts, malformed values, or
missing-required values were detected, so no correction, canonical write, or superseding fact was
created. Coverage is `bounded_complete_for_retained_phase_135_projection` and
`incomplete_global_printing_history`; provider omission states are `provider_field_unknown` and
`provider_field_unsupported`. Printing count is not supply quantity, global completeness is not proven,
and no demand, popularity, scarcity, supply, value, recommendation, or market-trend conclusion follows.
No acquisition, promotion, or inference occurred. The deterministic artifact is
`data/reviews/phase-137/printing-history-audit.json`; the read-only builder and operator script can
regenerate it and fail closed on canonical or fact drift. Architecture v12 remains frozen.

# Phase 136 — verified pilot Printings promoted

Phase 136 consumed only merged retained run `mtgjson-pilot-30786023976-1`. Its exact regular-file
inventory is `acquisition-report.json`, `manifest.json`, and `source-pilot-printings.json`; the
normalized projection is 371,126 bytes with SHA-256
`493df83312c8d9271e84a143ed288767d7fbf53d7b4a23bfc2f72af514bc67e6`, and records source
SHA-256 `2a10a52e9d82c3140c0be67f77a2ab0f5c2c491e53f06dccb4a9b224a96f53ae` over 177,237,377
source bytes. The evidence directory remains unchanged.

All 534 retained supported non-MB2 rows became deterministic Printing candidates and were reviewed:
534 accepted; zero existing-canonical duplicates, retained duplicates, ambiguous, conflicting,
incomplete, unsupported, or rejected. The ten existing Cards and the existing `foil` and `nonfoil`
finishes were reused; no supporting entity was promoted. Exactly 534 provider-UUID-keyed Printings
were promoted, taking the canonical repository from 379 to 913 Printings. The canonical digest moved
from `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f` to
`881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077`.

Immutable audit and promotion identity is `phase-136-mtgjson-pilot-30786023976-1` (audit digest
`94284fef8024bb3abc2c785d82fc6f79e7adcc8303e69f06c8152959193e1e5b`); rollback identity is
`phase-136-mtgjson-pilot-30786023976-1-rollback`. Byte-identical replay is idempotent, conflicts and
canonical drift fail closed, and rollback removes only the audited 534 Printings and verifies the
pre-state digest.

Printing totals (including the existing MB2 Printing) are: Brainstorm 48, Command Tower 111,
Counterspell 84, Goblin Charbelcher 9, Goblin King 27, Sol Ring 136, Swords to Plowshares 97,
Treasure Cruise 15, Walking Ballista 11, and Wishclaw Talisman 6. Exactly ten append-only Phase 136
`printing.reprint_history` facts supersede their Phase 133 facts. Active queries return Phase 136;
historical queries return Phase 132, Phase 133, then Phase 136 in recording order. Coverage remains
explicitly incomplete: this is the retained ten-card projection, not proof of global history, and
Printing counts are not supply. All 90 Phase 132 facts, all ten Phase 133 fact files, and all 478
market observations remain byte-identical. No provider contact, reacquisition, market write,
demand/value inference, or Architecture v12 change occurred.

The deterministic census, per-card Printing IDs, dates, set coverage, fact IDs, supersession IDs,
and limitations are recorded in `data/reviews/phase-136/pilot-review.json`.

---

# Phase 135C handoff

The Phase 135B attempt reached the official checksum endpoint with HTTP 200 and observed a bare
64-hex digest. The old two-field parser rejected it and correctly stopped at
`checksum_requests: 1`, `source_requests: 0`; no evidence or protected data changed. Phase 135C
accepts digest-only, standard GNU text/binary-marker, and BSD SHA256 records. Filename-bearing
records must use exactly `AllPrintings.json.gz`; URLs, credentials, absolute/relative paths,
traversal, and alternate basenames remain forbidden.

Sidecars are strict UTF-8, at most 1,024 bytes, single-line with at most one final newline, and must
contain exactly one digest. Diagnostics add byte count, sidecar SHA-256, bounded escaped text,
syntax, filename candidate, and exact reason without corpus bytes. A valid parse only permits the
one source request; its streamed bytes must still match the digest. After merge, rerun **Pilot
printing acquisition** exactly once and review its three-file evidence PR. Do not promote,
supersede Card Intelligence facts, or write market data.

# Phase 135B handoff

The Phase 135A production run received HTTP 403 and also passed an empty acquisition timestamp.
The repaired transport uses an explicit MTG Lab GitHub Actions User-Agent, explicit Accept and
Accept-Encoding headers, HTTPS-only approved-host redirects, final-response validation, and the
official SHA-256 sidecar. Diagnostics contain only safe descriptors and response/failure metadata,
never corpus bytes. The workflow generates and validates one UTC timestamp. No acquisition was
executed while implementing this repair. After merge, manually rerun **Pilot printing
acquisition** exactly once and review the resulting evidence PR.

# Phase 135 handoff

The bounded retention implementation is complete and tested, but production acquisition is blocked by the environment's HTTP 403 proxy response. MTGJSON AllPrintings v5 gzip is the approved source; CC BY 4.0 permits retaining the attributed bounded projection. The source is downloaded once to staging, verified as HTTP 200 with gzip media/magic, hashed, incrementally scanned one set at a time, projected to the exact pilot excluding MB2, and atomically renamed. A byte-identical run is accepted; an identity conflict fails closed; staging is removed after every result.

No production evidence directory exists yet. Never substitute fixture data or reconstruct printings from the Phase 134 MB2/MSH payloads. Execute the command in `docs/MTGJSON_PROVIDER.md`, then verify the exact three-file inventory before recommending the Phase 134 retry.

# Phase 134 evidence-gap handoff

The requested baseline passed, but the mandatory source gate did not. Review
`data/reviews/phase-134/evidence-gap-report.json`: all twelve retained reviewed MTGJSON payloads
are checksum-bound and limited to MB2/MSH. Across 10,940 candidates they supply zero non-MB2
Printing records for the ten pilot Cards. The source AllPrintings bytes named by lineage are not
retained, so no safe reconstruction is possible. Phase 134 correctly performed no promotion and
created no facts; Phase 132 and Phase 133 remain the full three-layer-intelligence history available
only through the first two layers (unknown, then bounded MB2). Acquire nothing implicitly and do
not resume until an approved printing-level artifact is actually retained.

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

# Phase 135A handoff

The production acquisition is deliberately delegated to a manually dispatched GitHub-hosted job
with approved network access. It checks out the triggering SHA, runs the full suite before its
single `retain_pilot_printings.py` invocation, and keeps the complete provider gzip only in the
retention component's temporary directory. That staging directory is deleted; diagnostics contain
only logs, source/normalized digest summaries, boundary reports, run/branch identity, PR identity,
and a failure marker. The durable boundary is exactly three JSON files in one new run directory.

The job rejects incomplete ten-name coverage, zero retained rows, MB2/unrelated rows, invalid
provider Printing UUIDs, missing/ambiguous/conflicting/malformed/unsupported records, or any
canonical write, promotion, or fact creation. It creates or byte-verifies the deterministic
`pilot-printing-acquisition/<run-id>` branch without force, creates or reuses at most one exact open
PR, and verifies base, head, title, and SHA. An operator must review and merge it manually, then stop
before canonical promotion. Codex Cloud network availability is not an implementation prerequisite.

## Phase 139 — multi-snapshot readiness

Phase 139 preserves the Architecture v12 acquisition/import boundary while making later MB2 snapshots operationally safe. A repository owner manually dispatches `market-acquisition.yml`; the GitHub run ID and attempt produce a unique `scryfall-mb2-<run>-<attempt>` identity. The job makes the existing single provider-corpus request, projects MB2 only, retains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`, and creates or reuses one deterministic evidence branch and at most one exactly verified PR. It neither schedules runs nor merges PRs.

After human review and manual evidence-PR merge, an owner imports that run with `PYTHONPATH=src:. python scripts/import_market_observations.py <acquisition-run-id>`. Verification binds source/normalized digests, byte counts, timestamps, provider, canonical snapshot, scope, census, and non-write flags. Import is append-only, publishes its report last, rolls back partial publication, accepts byte-identical replay, rejects conflicts, preserves acquisition lineage, and records a deterministic observation inventory digest. Previous observations are never overwritten.

Readiness compares only the exact tuple canonical Printing ID, provider, finish, language, currency, and price type. States are `no_observations`, `single_snapshot_only`, `insufficient_comparable_dimensions`, and `multiple_snapshots_descriptive_only`. Missing prices remain explicit. Two priced source timestamps in the same exact dimension may yield Decimal first/latest amounts, absolute/percentage change, elapsed seconds, and count labelled **descriptive historical movement**. This is not statistical trend reliability, momentum, prediction, valuation, ranking, or recommendation.

Production still contains only acquisition `scryfall-mb2-30754638264-1` and therefore remains `single_snapshot_only`: one snapshot is not a trend and no descriptive movement can be established. The hard stop remains in force before prediction or recommendation work. To acquire the next real snapshot after merge: open GitHub Actions, choose **Market acquisition**, click **Run workflow** once, review the three-file evidence PR and checks, merge it manually, then separately run the importer for the displayed run identity and review that import change before merge.
# Phase 143 handoff — acquisition required before production facts

The implementation selects MTGJSON `https://mtgjson.com/api/v5/AllDeckFiles.zip` (CC BY-SA 4.0
project-data terms; underlying Wizards data remains owned by its respective owners). The workflow is
manual and retains only the exact pilot projection, not the ZIP. Numerator means distinct provider deck
files containing the exact Card name on commander, main, or side board; denominator means all distinct
decoded deck files in the snapshot. Deck type is case-folded, board identity is preserved, and deck
names are not converted into inferred archetypes. Completeness is bounded to MTGJSON's curated deck
products and is not global played-deck coverage.

No acquisition artifact exists in this checkout because provider network access was unavailable.
Consequently there are no Phase 143 production usage records, facts, or supersessions. Run the manual
workflow, review the artifact, and only then admit evidence/facts. Phase 142 and all protected data are unchanged.

## Phase 143 repaired acquisition handoff

The hosted failure was a projection identity defect, not acquisition failure: a repeated non-empty Deck
`code` was preferred over the decoder's filename coordinate and rejected as though MTGJSON promised
global uniqueness. The corrected projection treats `code` as optional provider identity and the complete
ZIP member path as exact source-record identity. Run **Bounded deck usage acquisition** on `main`
exactly once after this repair merges, then review its ten-record PR. Do not run it from this checkout and
do not create usage facts during the acquisition.
# Phase 143 publication-boundary repair handoff

The first hosted acquisition reached publication and wrote the expected evidence file, but the old
tracked-diff-only check missed that untracked file and stopped before branch creation, commit, push, or
PR creation. The workflow now uses a NUL-delimited Git porcelain parser before and after staging. Its
only pre-commit state is `?? data/card_intelligence/demand/phase-143/mtgjson-decks.json`; its only
staged state is `A  data/card_intelligence/demand/phase-143/mtgjson-decks.json`. The strict loader runs
before publication. After merge, manually rerun **Bounded deck usage acquisition** exactly once and
manually review the resulting evidence PR. No production evidence PR exists from this repair.
# Phase 147 handoff — TopDeck probe infrastructure only

Phase 147 added a transport-free TopDeck tournament projector and synthetic regression coverage. It
cannot make network or repository writes. No live probe occurred: official documents were blocked and
`TOPDECK_API_KEY` was absent. Permanent retention, historical storage, redistribution, and attribution
for stored/derived output require human/provider clarification. Keep production acquisition, Phase 148,
and fact creation blocked until both API and retention authorization are verified.
