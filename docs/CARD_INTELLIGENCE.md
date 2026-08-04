# Phase 138 observed-price explanation extension

`CardValueExplanationEngine.explain(..., include_observed_prices=True)` returns `card-value-explanation-v2`; omission of the flag preserves v1. The extension is limited to the existing ten-card pilot. It joins observations to Cards only by first selecting that Card's exact canonical Printing identities. Thus MB2 observations never value another Printing, and finish, language, provider, currency, and price type remain separate.

Evidence quality now separates known observed amounts and provenance, explicitly unavailable provider prices, incomplete one-acquisition/MB2-only history, and unsupported completed-sale velocity, inventory, usage, demand, buylist spread, fair value, and future direction. Printing count is not supply. No recommendation is produced.

# Phase 137 explainable Card Value evidence layer

`CardValueExplanationEngine` is a read-only presentation layer over three existing sources: the frozen
canonical snapshot, active asserted Card Intelligence facts, and retained immutable market
observations. It supports only the ten Phase 132/136 pilot Cards and emits
`card-value-explanation-v1`. A report identifies the Card and canonical snapshot, then separates:

* **Printing History:** retained printing/reprint counts, date bounds, distinct sets, finishes,
  treatments, promotional states, and bounded/incomplete coverage.
* **Market:** observation count and time span plus providers and currencies; observed price amounts are
  intentionally not exposed or interpreted.
* **Rules:** reviewed oracle text, mechanical roles, format legality, and product membership.
* **Evidence Quality:** sorted known and unknown predicates and explicit incomplete and unsupported
  categories.

The generation timestamp is the latest recording timestamp among selected retained inputs. This makes
repeated output byte-identical while accurately describing the evidence snapshot rather than the wall
clock. Provenance lists active knowledge fact IDs, knowledge evidence sources, market observation IDs,
and the canonical identity.

The engine explicitly states that this repository has no reviewed Commander usage, tournament results,
retained inventory, or demand evidence. It does not treat legality as usage, printing count as supply,
finish as collectibility, or an observation as a value explanation. It cannot infer demand, scarcity,
popularity, value, or price direction and produces no recommendation, score, ranking, or forecast.

Future categories may be displayed only after their evidence is separately retained, reviewed, and
asserted through the existing append-only knowledge boundary. Broader Card coverage requires an
explicitly approved scope phase. Explanation remains downstream and read-only; it must never acquire
data, promote canonical entities, append facts, or modify observations. Architecture v12 remains
frozen.

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

# Phase 135 printing evidence retention boundary

Phase 135 is evidence acquisition only. It creates no Card Intelligence fact and does not supersede the ten Phase 133 incomplete reprint-history facts. Its bounded MTGJSON projection preserves provider printing UUID, oracle ID when supplied, card/set coordinates, date, language, finishes, rarity, frame/treatment, promo/reprint/digital flags, source identity, and publication timestamp. Missing provider fields are the literal `unknown`; nothing is guessed. Production acquisition remains pending because the official endpoint was inaccessible from this environment.

# Phase 134 retained-evidence gap

Phase 134 did not append Card Intelligence facts. The retained reviewed MTGJSON payload boundary
contains the ten pilot MB2 Printings but no non-MB2 Printing identity for any pilot Card; its MSH
records do not match the pilot. Set-membership assertions cannot substitute for printing-level
records, and the unretained source bytes cannot be reconstructed from lineage or conversational
memory. Active queries therefore still return the incomplete Phase 133 aggregate, and full-history
queries still return only the Phase 132 unknown and Phase 133 bounded MB2 assertion.

Printing count remains `max(total distinct canonical printings - 1, 0)` for reprint-count purposes,
and does not measure supply. The retained evidence still cannot establish complete global history,
demand, deck usage, popularity, scarcity, catalysts, historical price movement, valuation, price
predictions, or recommendations. See `data/reviews/phase-134/evidence-gap-report.json`.

# Phase 133 verified printing-history intelligence

Phase 133 uses the same ten-card Phase 132 pilot and appends ten known
`printing.reprint_history` facts. Each aggregate cites the exact Phase 119 canonical Card and MB2
Printing IDs and the matching record in retained acquisition `scryfall-mb2-30754638264-1`. It
reports the canonical Printing count and IDs, canonical set codes, separately asserted historical
set memberships, earliest/latest retained canonical Printing dates, finishes, languages, explicit
treatment and promotional fields, and evidence coverage.

Reprint count means **`max(total distinct canonical printings - 1, 0)`**. The current canonical
snapshot contains one MB2 Printing for each pilot Card, so every bounded count is zero. This does
not contradict the retained source assertion that each MB2 record is a reprint: the canonical
repository does not contain the older Printing identities. Set membership codes are not fabricated
into Printings. Consequently all ten histories are known within their MB2 boundary but incomplete
globally, and confidence remains null because arithmetic success is not evidence completeness.

The Phase 132 unknown remains byte-unchanged and is named in `supersedes`; active printing-history
queries return only the later known fact, while full-history queries return both. Invalid subject,
predicate, reference, or recording chronology fails closed through the Phase 131 repository.
Printing count is not supply quantity. Reprint history alone does not establish scarcity,
collectibility, popularity, demand, deck usage, catalysts, historical price movement, price
direction, investment quality, or value. Unsupported archetype and catalyst queries remain
explicitly empty. The deterministic review is `data/reviews/phase-133/pilot-review.json`.

# Card Intelligence

## Phase 132 reviewed pilot

Pilot `phase-132-mb2-reviewed-pilot-v1` contains 90 asserted facts for ten deterministically
selected Mystery Booster 2 Cards: Brainstorm, Command Tower, Counterspell, Goblin Charbelcher,
Goblin King, Sol Ring, Swords to Plowshares, Treasure Cruise, Walking Ballista, and Wishclaw
Talisman. Names are stored in ascending order. Each card was selected before examining price to
exercise a distinct rules-text-supported role where possible: card selection, mana fixing, stack
interaction, damage, tribal synergy, mana acceleration, creature removal, card draw, repeatable
damage, and tutoring.

The supported predicates record retained oracle text, format legalities, MB2 membership, finishes,
USD market-price dimension availability, immutable observation coverage, and one bounded mechanical
role. The Phase 131 contract was extended with narrowly descriptive kinds for product membership,
treatment availability, market-price availability, observation coverage, and evidence gaps; using
an unrelated kind for those assertions would have misrepresented their meaning. Facts preserve
references to the Phase 119 canonical state, the retained Phase 128 Scryfall MB2 projection, or the
Phase 128 observation repository. Confidence remains unknown (`null`), because no separate retained
confidence assessment exists.

Demand and reprint history are explicitly unknown for every pilot card. Empty archetype and market
catalyst queries remain empty rather than producing conclusions. Competitive/Commander staple
status, popularity, supply, scarcity, collectibility, tournament usage, Commander demand, combo
participation, archetype placement, market catalysts, valuation, ranking, and recommendations are
excluded. A format legality is not evidence of play or popularity, a finish is not evidence of
collectibility, and a price observation is not an explanation of value.

Consequently this pilot is not a complete explanation of card value. Future separately retained
and reviewed datasets may append facts about competitive event usage, Commander usage, supply,
printing/reprint history, or dated market catalysts. Those additions must cite their exact retained
evidence, preserve unknowns, and must not be inferred by this repository or an AI consumer.

The deterministic review artifact is
`data/reviews/phase-132/pilot-review.json`. Production facts remain append-only beneath
`data/knowledge/facts/magic/<card-id>/<fact-id>.json`; neither the review artifact nor querying
promotes facts into canonical or market data.

# Phase 135A operational boundary

The manual Pilot printing acquisition workflow can retain evidence but cannot create or supersede
Card Intelligence facts. Its census requires all ten approved names, at least one supported non-MB2
Printing UUID per name, and zero missing, ambiguous, malformed, conflicting, or unsupported records.
The evidence PR must be manually reviewed and merged. Processing stops there: a later phase must
separately review retained evidence before any bounded Printing promotion or Phase 133 supersession.
No history, demand, scarcity, value, popularity, supply, or recommendation is inferred.

## Phase 139 — multi-snapshot readiness

Phase 139 preserves the Architecture v12 acquisition/import boundary while making later MB2 snapshots operationally safe. A repository owner manually dispatches `market-acquisition.yml`; the GitHub run ID and attempt produce a unique `scryfall-mb2-<run>-<attempt>` identity. The job makes the existing single provider-corpus request, projects MB2 only, retains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`, and creates or reuses one deterministic evidence branch and at most one exactly verified PR. It neither schedules runs nor merges PRs.

After human review and manual evidence-PR merge, an owner imports that run with `PYTHONPATH=src:. python scripts/import_market_observations.py <acquisition-run-id>`. Verification binds source/normalized digests, byte counts, timestamps, provider, canonical snapshot, scope, census, and non-write flags. Import is append-only, publishes its report last, rolls back partial publication, accepts byte-identical replay, rejects conflicts, preserves acquisition lineage, and records a deterministic observation inventory digest. Previous observations are never overwritten.

Readiness compares only the exact tuple canonical Printing ID, provider, finish, language, currency, and price type. States are `no_observations`, `single_snapshot_only`, `insufficient_comparable_dimensions`, and `multiple_snapshots_descriptive_only`. Missing prices remain explicit. Two priced source timestamps in the same exact dimension may yield Decimal first/latest amounts, absolute/percentage change, elapsed seconds, and count labelled **descriptive historical movement**. This is not statistical trend reliability, momentum, prediction, valuation, ranking, or recommendation.

Production still contains only acquisition `scryfall-mb2-30754638264-1` and therefore remains `single_snapshot_only`: one snapshot is not a trend and no descriptive movement can be established. The hard stop remains in force before prediction or recommendation work. To acquire the next real snapshot after merge: open GitHub Actions, choose **Market acquisition**, click **Run workflow** once, review the three-file evidence PR and checks, merge it manually, then separately run the importer for the displayed run identity and review that import change before merge.
