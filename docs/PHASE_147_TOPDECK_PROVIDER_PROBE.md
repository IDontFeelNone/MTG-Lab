# Phase 147 — TopDeck.gg competitive-evidence provider probe

## Decision

The bounded, transport-free TopDeck adapter is compatible with the ten-Card competitive evidence
design, but **production retention remains blocked**. API request authorization and dataset retention
authorization are separate gates. No TopDeck key was available, no live request occurred, and no raw
or projected provider record was retained; human/provider clarification is required before long-term
storage or redistribution.

Architecture v12 and `card-competitive-evidence-v1` remain unchanged. This phase creates no
competitive fact, canonical record, market observation, score, valuation, prediction, ranking, or
recommendation.

## Baseline confirmation

The repository was checked before implementation: the exact pilot is Brainstorm, Command Tower,
Counterspell, Goblin Charbelcher, Goblin King, Sol Ring, Swords to Plowshares, Treasure Cruise,
Walking Ballista, and Wishclaw Talisman. It contains 140 knowledge facts, including ten active Phase
136 printing histories, ten Phase 142 Scryfall demand facts, and twenty Phase 144 MTGJSON usage facts.
It contains 956 immutable MB2 market observations. Retained competitive evidence and competitive or
tournament facts are both zero. The protected canonical and market tree digests remain respectively
`e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19` and
`34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9`.

## Official-document research record

On 2026-08-12, the official-source browser request returned HTTP 401. Direct identified HTTPS
requests returned proxy HTTP 403 before reaching the provider. The following provider-controlled
locations/descriptors were attempted: `https://topdeck.gg/` (provider home),
`https://topdeck.gg/docs` (documentation discovery), `https://topdeck.gg/api` (API discovery),
`https://docs.topdeck.gg/` (documentation host discovery), `https://topdeck.gg/api/docs` (API docs
discovery), and `https://topdeck.gg/terms` (terms discovery). None supplied inspectable content.

Consequently, the prompt's statements about free use, attribution, authentication, limits, fields,
filters, and analytics/export use cases are useful investigation leads but are not treated as proof.
No third-party summary, cached recollection, guessed endpoint, or webpage scrape substitutes for a
current provider-controlled document. The adapter's provisional endpoint constant is
`POST https://topdeck.gg/api/v2/tournaments`; it must be reconciled against reachable official docs
before any live probe. **No provider endpoint is recorded as verified in this environment.**

## Contract and rights matrix

The required legal classification vocabulary is literal: `verified_allowed`, `verified_prohibited`,
`unverified`, and `not_applicable`. Silence never means permission.

| Dimension | Classification | Finding |
|---|---|---|
| API availability | `unverified` | Current official documentation could not be inspected. |
| API authentication | `unverified` | Provisional design uses `Authorization`; its exact scheme must be verified. |
| API request authorization | `unverified` | No terms or live authenticated response was available. |
| Rate limits | `unverified` | The reported ~100 requests/minute and lower bulk limits were not independently verified. |
| Visible attribution/link | `unverified` | Reported requirement must be captured verbatim enough to implement, without excessive quotation. |
| Tournament date/participant filters | `unverified` | Provisional contract lead only. |
| TID tournament identity | `unverified` | Adapter requires non-empty `TID`; stability/collision scope is not proven. |
| Decklist and `deckObj` availability | `unverified` | Parser supports documented-shape leads and missing decklists. |
| Standings and W/L/D | `unverified` | Parser preserves literal standing, wins, draws, and losses. |
| Participant count | `unverified` | Parser preserves it; whether it is entrants, registrations, or standings count is unknown. |
| Rounds/matches | `unverified` | Presence is diagnosed; completeness and identity are unknown. |
| Pagination/bulk behavior | `unverified` | Terminal-page proof cannot yet be designed. |
| Response version/stability | `unverified` | No inspected versioning or stability commitment. |
| Retention rights | `unverified` | Production retention fails closed. |
| Redistribution rights | `unverified` | No Git/publication grant established. |
| Historical-storage rights | `unverified` | No permanent historical corpus grant established. |
| Attribution for stored/derived data | `unverified` | Applicability and required placement are unknown. |

There are no `verified_prohibited` findings: lack of proof is classified `unverified`, not prohibited.
There are no `not_applicable` rights dimensions. The API-access decision is therefore “not approved,”
and the storage/redistribution decision is independently “not approved.”

## Bounded adapter and privacy boundary

`topdeck_provider.py` has no HTTP client, filesystem writer, knowledge repository, canonical writer,
or market writer. It accepts already decoded transient input and projects only matches for the exact
ten canonical Cards. It preserves tournament TID, event date, provider format, participant count,
standing, W/L/D, mainboard and sideboard copy counts, deck-level identity, and whether rounds were
present. A provider-native deck ID is preferred; absent one, a deterministic content identity is
derived from TID, standing, and normalized deck contents. Duplicate identities and conflicting replay
fail closed.

Player names, emails, usernames, Discord identities, account IDs, and contact information are never
copied. Transient player identifiers may only help resolve a response in memory and must be discarded
before projection. This is a permanent competitive-evidence privacy boundary unless Architecture v12
is explicitly revised.

The source/retrieval timestamp, raw response digest, byte count, and source-record digest belong in a
future licensed v1 snapshot envelope, not this non-retaining probe. No fabricated values are emitted.
`Authorization` is built separately, never included in the URL or safe request descriptor, and the
environment variable name is `TOPDECK_API_KEY`.

## Literal metrics and denominator rules

The only implemented summaries are retained tournament deck count, retained tournament count,
retained main-deck copies, retained sideboard copies, Top 8 count, Top 16 count, first-place count,
aggregate wins, aggregate losses, and aggregate draws. A Card is counted once per unique
tournament/deck for deck count while all literal copies are preserved. Metrics require one exact
provider format; format populations are not combined.

No fraction is calculated. A future fraction requires a complete, reproducible filtered population
and successful terminal pagination. Participant count is retained event-size evidence, not by itself
a deck denominator. TopDeck coverage is not all competitive Magic; deck count is not global
popularity; placement is not card strength; represented decks are not supply; price is not demand;
EDHREC rank is not competitive use; and MTGJSON preconstructed inclusion is not tournament use.

## Probe outcome and exact next action

No live non-retaining metadata/API probe occurred because `TOPDECK_API_KEY` was absent and official
documentation was unreachable. Synthetic records exercise the provisional documented shape; they are
test inputs, not fabricated provider observations, and are not under `data/`.

Next, a human operator must (1) capture the current provider-controlled API and terms URLs, including
endpoint, authentication scheme, limits, attribution language, pagination, and versioning; (2) obtain
written provider clarification explicitly covering permanent bounded storage, historical storage,
redistribution, and attribution for stored/derived data; (3) inject `TOPDECK_API_KEY` only as a secret
environment variable; and (4) run one bounded, non-retaining Magic tournament metadata request while
recording only redacted structural diagnostics. Do not begin Phase 148 until both the API and retention
gates are verified allowed.
