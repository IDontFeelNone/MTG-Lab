# Phase 146 — competitive provider verification failed closed

No evaluated provider has verified current automation and retained-evidence permission. Provider-controlled sources were unreachable (web service HTTP 401; direct proxy HTTP 403), so all legal, API, identity, completeness, and denominator gates remain unknown. No provider was selected, no production acquisition was executed, and competitive evidence/facts remain zero. The v1 contract and explanation v1/v2/v3/v4 are unchanged.

# Phase 145 — competitive evidence gap assessment complete

Phase 145 confirms zero retained tournament/actual-play evidence and introduces a non-production,
provider-neutral validation contract for a future bounded snapshot. Acquisition is blocked pending
human verification of TopDeck.gg licensing, retention, API stability, completeness, and denominator
semantics. It creates no competitive facts and does not change explanation v1/v2/v3/v4, canonical or
market data, historical facts, Phase 143 evidence, or frozen Architecture v12.

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

# Phase 142 — reviewed demand and usage evidence complete

Phase 142 retains a bounded ten-record projection of Scryfall `edhrec_rank` from the already retained `scryfall-default-cards` dataset timestamp `2026-08-04T21:10:15.879000Z`. Exact canonical Card/oracle and MB2 provider-Printing identities are retained with the provider-source digest. Ten known `value_driver.demand` facts supersede exactly the ten Phase 132 unknown demand facts; each reports the literal provider ordinal and explicitly remains incomplete for deck counts, methodology, archetypes, and competitive usage.

Opt-in `card-value-explanation-v3` exposes each provider-specific fact, exact value, timestamp, evidence-source ID, null confidence, completeness, and limitations. The default and v2 paths remain available. No score, provider combination, valuation, recommendation, prediction, popularity conclusion, scarcity inference, or price/reprint-driven demand inference was added. Canonical data, two retained market acquisitions, 956 immutable observations, imports, Phase 135 evidence, and ten Phase 136 histories remain unchanged; Architecture v12 remains frozen.

# Phase 141 — multi-snapshot historical card explanations complete

Phase 141 extends opt-in `card-value-explanation-v2` with authoritative `historical_price_evidence` for the ten-card pilot. It compares only canonical Printing/provider/finish/language/currency/price-type dimensions with known prices at two distinct source timestamps. Production remains two retained acquisitions, 956 observations (478 each), 379/379 MB2 coverage, 478 globally comparable dimensions, zero explicit-missing dimensions, and `multiple_snapshots_descriptive_only`.

The pilot contains 17 comparable MB2 dimensions: zero increased, nine decreased, and eight unchanged. JSON exposes exact Decimal change, first/latest provenance and digests, lineage, elapsed span, and a retained-MB2-only card summary. `--include-historical-movement` automatically enables observed prices; `--human-readable` derives text strictly from JSON. No protected data, facts, architecture, prediction, score, ranking, recommendation, or market inference changed.

# Phase 140 — second production MB2 market snapshot imported

Phase 140 imported retained acquisition `scryfall-mb2-30959813191-1` from `data/market/acquisitions/scryfall-mb2-30959813191-1/` without provider contact or reacquisition. The retained boundary remains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`; verification binds manifest identities, source and normalized digests, byte counts, timestamps, canonical snapshot identity, MB2-only scope, and false write/promotion flags.

The import appended 478 immutable Scryfall/USD/market observations under `data/market/observations/printing/<printing-id>/scryfall/` and published `data/market/imports/scryfall-mb2-30959813191-1/import-report.json` last. Historical observations grew from 478 to 956; retained acquisition count grew from one to two; MB2 coverage remained 379/379. Mapping census is 385 retained source records, 379 matched canonical Printings, 478 matched observation dimensions, six unmatched finish mappings, and zero ambiguous, rejected, duplicate, unsupported, or explicit-missing price observations.

History readiness moved from `single_snapshot_only` to `multiple_snapshots_descriptive_only`: distinct source timestamps grew from one to two, all 478 exact Printing/provider/finish/language/currency/price-type dimensions are comparable multi-snapshot dimensions, and zero dimensions contain explicit missing prices. Descriptive historical movement is available only inside those exact dimensions and is not a prediction, reliable trend, momentum signal, valuation, ranking, recommendation, or expected return.

Replay is byte-identical and idempotent; conflicting report or observation bytes fail closed. Atomic rollback removes only files created by the current attempt before report publication. The first acquisition's observation bytes are preserved, canonical data and Card Intelligence facts are unchanged, `canonical_write` is false, `promotion_performed` is false, and Architecture v12 remains frozen.

# Phase 138 — observed price evidence explanations complete

Phase 138 adds opt-in `card-value-explanation-v2` output for the same ten reviewed pilot Cards. The read-only engine now exposes the actual 478-file repository observations that resolve through each Card's exact canonical MB2 Printing. Every value retains Printing, finish, language, provider, currency, price type, timestamps, acquisition, provider-record, observation, and digest provenance. The default remains byte-compatible v1.

The deterministic summary distinguishes known and explicitly unavailable prices, counts exact coverage, identifies latest observations per exact dimension, and computes minimum, maximum, and median only within compatible dimensions. The retained data is one Scryfall snapshot, not completed sales or a trend; it does not price the other retained historical Printings. No acquisition, promotion, scoring, prediction, ranking, recommendation, demand, inventory, or sales-velocity inference occurred. Canonical identity and Architecture v12 remain frozen.

# Phase 137 — explainable Card Value evidence engine complete

Phase 137 adds the first deterministic, read-only explanation layer for exactly the ten reviewed pilot
Cards. `card-value-explanation-v1` combines the canonical snapshot, active reviewed Card Intelligence
facts, and retained market-observation coverage into Printing History, Market, Rules, and Evidence
Quality sections. It reports counts, dates, dimensions, explicit unknown/incomplete/unsupported states,
limitations, and exact input provenance. Its generation timestamp is the latest retained input recording
time, so identical repositories produce byte-identical JSON.

The CLI supports `python -m card_intelligence.cli explain Sol Ring` and `explain --card-id <id>`.
It rejects non-pilot Cards and ambiguous input. It never reports observed price amounts, calculates a
numeric value or score, ranks Cards, predicts prices, infers demand/popularity/scarcity, or recommends
an action. There is no writer or network path.

Baseline protection is confirmed: 913 canonical Printings, 534 promoted non-MB2 pilot Printings, 478
market observations, and ten complete active Phase 136 printing-history facts. Canonical identity
`881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077` and Architecture v12
remain frozen. Canonical, knowledge, market, and retained evidence inputs are unchanged.

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

# Phase 135C status — genuine checksum syntax repaired

The Phase 135B hosted run observed MTGJSON's digest-only 64-hex sidecar and stopped because the old
parser required a filename field. It made zero large-source requests and no production writes.
Phase 135C accepts the genuine form plus standard GNU text/binary and BSD forms, while requiring
the exact `AllPrintings.json.gz` basename whenever a filename is present. Unsafe paths and unrelated
names fail before download. Corpus-free diagnostics bind the sidecar by byte count and SHA-256 and
report escaped bounded text, syntax, filename candidate, and exact reason. Streamed source bytes
remain SHA-256 verified. Canonical, market, evidence, and knowledge data are unchanged; no
production acquisition or promotion ran in this task.

# Phase 135B status — production transport repair ready

Phase 135A's GitHub-hosted run failed because the minimal urllib request was rejected with HTTP
403 and the workflow expanded an unavailable `github.run_started_at` expression to an empty
`--acquired-at` value. Phase 135B adds an identified, explicitly negotiated HTTPS request, safe
redirect/final-URL enforcement, one published SHA-256 sidecar request, checksum and response
validation, and bounded failure diagnostics. The workflow now creates and validates one UTC RFC
3339 shell timestamp and passes that exact value to acquisition and diagnostics. It has not run an
acquisition; production evidence, canonical, market, and knowledge bytes remain unchanged.

# Phase 135 status — implementation ready; acquisition transport blocked

Phase 134 is merged at `7453469`. Its retained-evidence report confirms zero supported non-MB2 pilot Printings. The 90 Phase 132 facts, ten Phase 133 superseding facts, ten incomplete active histories, one MB2 Printing per pilot Card, and 478 Phase 128 observations remain unchanged. Architecture v12 remains frozen.

Phase 135 adds a fail-closed MTGJSON AllPrintings gzip acquisition and bounded-retention implementation. The official provider request was attempted on 2026-08-03 but the execution proxy returned HTTP 403 before a source response. Consequently no acquisition run identity or retained production directory was fabricated, and canonical, knowledge, and market data were not changed. Re-run the documented command where the approved endpoint is reachable.

# Phase 134 status — stopped at retained-evidence gap

Phase 133 is merged at `ca5756c`. Baseline verification found the ten-card Phase 132/133
pilot, 90 Phase 132 facts, ten active incomplete Phase 133 histories, one canonical MB2 Printing
per pilot Card, 478 market observations, and frozen Architecture v12 intact. The only retained,
reviewed MTGJSON candidate boundary is dataset
`mtgjson-allprintings-5.3.0+20260731-b47cc8360034` (source SHA-256
`b47cc83600341e18663bdb48fe9d1337730976844465a35e75bcde5ac6f00d09`). Its twelve retained
payloads contain only MB2 and MSH candidates: 10,940 entities, including 813 Printings. They
contain the ten existing pilot MB2 Printings and zero non-MB2 Printing records for the pilot.
The original AllPrintings bytes are not retained.

Phase 134 therefore stopped before candidate creation, review, canonical promotion, audit,
rollback, or fact supersession. Canonical digest remains
`793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`; all pilot counts remain
one Printing and zero bounded reprints with incomplete coverage. No external acquisition,
inference, market/acquisition mutation, or prior-fact mutation occurred. The deterministic
evidence-gap report is `data/reviews/phase-134/evidence-gap-report.json`.

# Phase 133 status — verified bounded printing history

Phase 132 is merged at `ef2606c` with exactly ten pilot Cards and 90 reviewed facts. Phase 133
appends ten known `printing.reprint_history` facts that supersede, but do not alter, the ten Phase
132 unknown assertions. The retained Phase 119 canonical snapshot contains exactly one MB2
Printing per pilot Card; therefore the bounded reprint count is zero under `max(total distinct
canonical printings - 1, 0)`. Retained Card assertions list additional historical set memberships,
so all ten histories are explicitly incomplete rather than globally complete. The retained Phase 128
MB2 projection supplies the 2024-08-02 date, English language, finishes, treatment fields, and
promo/reprint flags. Printing count is not supply quantity, and history alone does not determine
scarcity, demand, price direction, or value. Canonical data, retained evidence, 478 market
observations, Architecture v12, and all 90 Phase 132 fact bytes remain unchanged. No acquisition,
inference, promotion, or canonical write occurred.

# Phase 132 status — first reviewed Card Intelligence facts

Phase 131 is merged at `0e2b89c`. Pilot `phase-132-mb2-reviewed-pilot-v1` adds 90 reviewed,
evidence-bound facts for ten deterministic MB2 Cards: 70 known assertions and 20 explicit
unknowns. The facts cover retained rules text and mechanical roles, legalities, product membership,
finishes, market dimension availability, and observation coverage; demand and reprint history remain
unknown. No staple, popularity, scarcity, collectibility, combo, archetype, catalyst, valuation, or
recommendation claim is made. Canonical data and the 478 market observations are unchanged, no
inference or promotion occurred, and Architecture v12 remains frozen.

# Phase 131 status — Card Intelligence Knowledge Layer foundation

Phase 130 is merged at `4e34eaf`. Card Intelligence v1 adds a game-agnostic, deterministic
repository of immutable asserted facts. Versioned JSON contracts represent the subject, knowledge
kind and predicate, known or explicitly unknown value, confidence, effective/recording dates,
multiple evidence sources, and supersession lineage. Strict loading, canonical serialization,
append-only persistence, repository replay validation, and read-only card queries are implemented.

The layer stores supplied knowledge and never infers, scores, recommends, predicts, calculates card
value or EV, or invokes AI. No production knowledge facts were added. The 478 Phase 128 market
observations, Phase 129 history, Phase 130 reporting, acquisitions, canonical data, sole Phase 119
promotion, and frozen Architecture v12 remain unchanged.

# Phase 130 status — read-only historical market query CLI and reporting

Phase 129 is merged at `73fb1de`. The versioned `market-history-report-v1` reporting facade and
`python -m market.cli` now expose deterministic observation list/latest/first/count, printing
history, MB2 coverage, acquisition summary, and exact-dimension as-of snapshot reports. Filters
cover canonical Printing ID, provider, acquisition, finish, language, currency, price type,
inclusive source-time range, and inclusive as-of cutoff. Listing defaults to 100 results and is
bounded at 500 with explicit truncation; complete printing history remains chronologically ordered.
Unknown Printing IDs and unsupported dimensions fail closed, while valid empty queries are explicit.

The commands only read the existing 478 immutable observations from retained acquisition
`scryfall-mb2-30754638264-1`, covering 379/379 MB2 Printings. No acquisition, import, observation
write, canonical write, promotion, EV calculation, recommendation, or workflow was performed.
Architecture v12 remains frozen.

# Phase 129 status — multi-acquisition market history

Phase 128 is merged at `7f5ce36`; the retained production MB2 acquisition completed and its
478 observations cover 379/379 canonical MB2 Printings. The observation store now accepts
independent retained acquisitions into one append-only history. Imports stage completely,
publish only new immutable observation identities, verify published bytes, and remove only
the new run's files on failure. Byte-identical replay succeeds, report or observation conflicts
fail closed, and acquisition/date/as-of/first/latest/count queries are deterministic. Import
reports include observation and coverage growth, historical count, append/replay verification,
and lineage. Canonical bytes remain unchanged, `canonical_write` and `promotion_performed`
remain false, and Architecture v12 remains frozen.

# Phase 128 status — first production MB2 market snapshot imported

Retained acquisition `scryfall-mb2-30754638264-1` was verified and imported without reacquisition. Its 385 MB2 source records produced 478 immutable Scryfall/USD/market observations covering all 379 production MB2 printings; 478 prices are known, zero are explicitly missing, six finish mappings are unmatched, and zero are ambiguous, rejected, duplicate, conflicting, or unsupported. Observations use `market-observation-v1` under `data/market/observations/`; the deterministic census is `data/market/imports/scryfall-mb2-30754638264-1/import-report.json`. Canonical coverage moved from 0/379 to 379/379. Canonical bytes remain unchanged, `canonical_write` and `promotion_performed` are false, and Architecture v12 remains frozen.

# Phase 127M status — manual evidence-PR completion

Main contains merged Phase 127L at `4d07036`. The latest real Market acquisition reached Scryfall, downloaded and validated the official gzip JSONL payload, produced the bounded MB2-only dry-run census, retained exactly three durable evidence files, passed all 415 repository tests, committed and pushed deterministic branch `market-acquisition/scryfall-mb2-30730690426-1` at `a94288b`, and created its evidence pull request. It stopped only while waiting for required checks that are not configured: the repository has no branch ruleset and no required status-check set. No production observation or canonical data changed, no promotion occurred, and MB2 market coverage remains 0/379.

Phase 127M removes required-workflow dispatch, required-check polling, branch-protection inspection, and auto-merge orchestration. After acquisition and validation, the workflow safely creates or byte-identically reuses the deterministic branch, commits exactly the unchanged three-file evidence boundary, pushes without force, creates or safely reuses exactly one PR, verifies its base, head, head SHA, and title, records its identifier and URL, and exits successfully. The open evidence PR is now intentionally reviewed and merged by a user. Observation import remains a separately authorized later phase.

# Phase 127L status — evidence PR check registration repaired

Main contains merged Phase 127K at `eb09a13`. The latest real Market acquisition successfully
validated the official Scryfall payload, retained exactly three durable evidence files, pushed
the deterministic branch, and created or reused its exact pull request without writing canonical
data or observations or performing promotion. Finalization then found no checks on the evidence
head because GitHub-token-created pushes and pull requests do not recursively start workflows.
Phase 127L explicitly dispatches the required Python validation on the exact evidence branch,
waits for a nonempty registered required-check set, revalidates the immutable head SHA, and only
then enters the existing all-success gate and repository-governed auto-merge request.

# Phase 127K status — unsupported branch-protection API dependency removed

Main contains merged Phase 127J at `b76110f`. The latest real Market acquisition completed the
official payload acquisition and validation, retained exactly three durable files, passed the
commit boundary and all 415 tests, committed as `a94288b`, pushed branch
`market-acquisition/scryfall-mb2-30730690426-1`, and created the evidence PR. No observations or
canonical data were written and no promotion occurred. Its sole failure was an unavailable,
redundant branch-protection REST read. Phase 127K relies on the existing PR-specific nonempty
required-check success assertion before requesting repository-governed auto-merge.

# Phase 127J status — evidence changed-file verification repaired

Main contains merged Phase 127I at `dd84f94`. The first real Phase 127I acquisition completed
the official download, evidence generation, and all 404 repository tests, then stopped at the
working-tree assertion because its four intentional untracked workflow diagnostics were absent
from the expected path list. Phase 127J adds a reusable NUL-delimited porcelain parser and
structured JSON verifier for the exact seven-path pre-commit boundary and three-path commit
boundary, including file placement, symlink, run/manifest identity, status, rename/deletion,
canonical, and observation isolation checks.
No acquisition, evidence fabrication, observation import, canonical write, or promotion occurs
in this repair; production market coverage remains 0/379.

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

# Phase 135A status — production execution path ready

Phase 135 is merged at `a8a21a8`. Phase 135A adds a manual-only GitHub Actions path for the
existing bounded retention component. A dispatch validates the complete repository, derives
`mtgjson-pilot-<github-run-id>-<attempt>`, downloads once, enforces the ten-card non-MB2 census,
and offers exactly the three Phase 135 evidence files on a deterministic branch and open PR.
Codex Cloud need not reach MTGJSON or GitHub: provider access belongs to the post-merge hosted
workflow, so local network failure cannot invalidate this implementation. No acquisition was run
here. Canonical data, 478 market observations, Phase 132/133 facts, and Architecture v12 remain
unchanged. Manual review and merge of the evidence PR is mandatory; canonical promotion is a hard stop.

## Phase 139 — multi-snapshot readiness

Phase 139 preserves the Architecture v12 acquisition/import boundary while making later MB2 snapshots operationally safe. A repository owner manually dispatches `market-acquisition.yml`; the GitHub run ID and attempt produce a unique `scryfall-mb2-<run>-<attempt>` identity. The job makes the existing single provider-corpus request, projects MB2 only, retains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`, and creates or reuses one deterministic evidence branch and at most one exactly verified PR. It neither schedules runs nor merges PRs.

After human review and manual evidence-PR merge, an owner imports that run with `PYTHONPATH=src:. python scripts/import_market_observations.py <acquisition-run-id>`. Verification binds source/normalized digests, byte counts, timestamps, provider, canonical snapshot, scope, census, and non-write flags. Import is append-only, publishes its report last, rolls back partial publication, accepts byte-identical replay, rejects conflicts, preserves acquisition lineage, and records a deterministic observation inventory digest. Previous observations are never overwritten.

Readiness compares only the exact tuple canonical Printing ID, provider, finish, language, currency, and price type. States are `no_observations`, `single_snapshot_only`, `insufficient_comparable_dimensions`, and `multiple_snapshots_descriptive_only`. Missing prices remain explicit. Two priced source timestamps in the same exact dimension may yield Decimal first/latest amounts, absolute/percentage change, elapsed seconds, and count labelled **descriptive historical movement**. This is not statistical trend reliability, momentum, prediction, valuation, ranking, or recommendation.

Production still contains only acquisition `scryfall-mb2-30754638264-1` and therefore remains `single_snapshot_only`: one snapshot is not a trend and no descriptive movement can be established. The hard stop remains in force before prediction or recommendation work. To acquire the next real snapshot after merge: open GitHub Actions, choose **Market acquisition**, click **Run workflow** once, review the three-file evidence PR and checks, merge it manually, then separately run the importer for the displayed run identity and review that import change before merge.
# Phase 143 — bounded deck-usage acquisition path ready; production evidence pending

Phase 143 reviewed structured provider options and selected the MTGJSON `AllDeckFiles.zip` snapshot as
the smallest reliable single-provider source for auditable represented-deck, board, deck-name, and
provider deck-type evidence. Direct provider acquisition was unavailable in the Codex Cloud task
environment, so no production values or facts were fabricated. A manually dispatched GitHub Actions
workflow now downloads the corpus transiently and retains only ten digest-bound Card aggregates plus
the matching provider deck identities needed to reproduce each numerator. The denominator is every
distinct decoded deck file in that exact snapshot; a Card is counted at most once per deck even if it
appears on multiple boards. Provider deck `type` is normalized by case-folding and is presented as a
provider format label; deck names are literal associations, not inferred archetypes.

Until a resulting artifact is reviewed and merged, the retained production census is zero usage
records, zero new facts, zero supersessions, and all ten Cards remain unknown for deck inclusion.
Phase 142's ten Scryfall ranks and exactly ten known demand facts remain intact. Canonical data, 956
market observations, Phase 135 evidence, Phase 136 histories, and Architecture v12 are unchanged.

## Phase 143 repair — source-record identity separated from provider code

The first hosted acquisition reached the real ZIP and proved the transport path, but projection rejected
legitimate repeated MTGJSON `code` values. The decoder had populated a filename fallback, yet
`project_decks()` preferred any non-empty `code` and incorrectly treated that provider field as a
mandatory globally unique deck-file key. MTGJSON's Deck model documents `code` as deck-associated
provider data; it does not state that `code` is present and globally unique across every member of
`AllDeckFiles.zip`. The downloadable member path, rather than name, type, or code, is the retained
coordinate for the exact provider file.

The repair therefore keeps optional `code` as `provider_deck_identity` (null when unavailable), uses the
full ZIP member path as `source_record_identity`, derives `retained_record_id` from that path, and binds
the record to its member-byte SHA-256. Code/name/type collisions never collapse files. Duplicate member
paths fail closed; the diagnostic distinguishes identical duplicate entries from the same path carrying
conflicting bytes. Byte-identical content at different paths remains two explicit aliases with equal
content digests. Numerator and denominator remain counts of distinct member paths, and no production
artifact was created by this repair.
# Phase 143 — publication boundary repair ready

The hosted bounded deck-usage acquisition created the exact evidence path as an ordinary untracked
file, but the publication step used `git diff --name-only`, which inventories tracked diffs and
therefore returned no path. A deterministic porcelain-v1 `-z` verifier now inventories staged,
unstaged, untracked, deleted, renamed, and copied paths. Before staging it permits exactly one `??`
regular non-symlink file; after staging it permits exactly one `A ` file, always at
`data/card_intelligence/demand/phase-143/mtgjson-decks.json`. Every other Git state fails closed.

The strict evidence loader additionally binds both UTC timestamps, source digest and byte count, the
ten-record digest and exact pilot, and path-derived retained record identities. Provider deck identity
remains nullable and non-unique; ZIP member paths remain unique source identities and denominator
units. No provider acquisition was run during this repair, and no canonical, market, knowledge, Phase
135 evidence, or other production data changed.
