# Phase 146 — competitive provider verification and bounded acquisition readiness

## Decision

**No production competitive acquisition is authorized.** Architecture v12 remains frozen and
`card-competitive-evidence-v1` remains unchanged. Phase 146 did not acquire provider data, retain a
competitive snapshot, create a competitive fact, add a network client, or enable a workflow.

Licensing and retention permission are hard gates. On 2026-08-12 the research environment could not
retrieve any provider-controlled document: the web research service returned HTTP 401 and direct
HTTPS requests through the environment proxy returned HTTP 403 before reaching every provider host.
A public page, an advertised API, or recollection of prior behavior is not a license. Consequently no
provider has verified permission for MTG Lab to automate retrieval, retain the bounded evidence, or
redistribute its Git projection. The Phase 145 conditional preference for TopDeck.gg is withdrawn;
it is not an approved provider.

## Frozen baseline independently rechecked

Repository validation confirms the same ten Cards: Brainstorm, Command Tower, Counterspell, Goblin
Charbelcher, Goblin King, Sol Ring, Swords to Plowshares, Treasure Cruise, Walking Ballista, and
Wishclaw Talisman. There are 140 retained Card Intelligence facts: ten active Phase 136
`printing.reprint_history`, ten Phase 142 Scryfall `value_driver.demand`, ten Phase 144 MTGJSON
`demand.deck_inclusion`, and ten Phase 144 MTGJSON `format.usage` facts. There are 956 immutable MB2
market observations across two Scryfall acquisitions. Phase 143's retained MTGJSON artifact and all
protected canonical, market, and knowledge bytes are unchanged.

There is no `data/card_intelligence/competitive/` production boundary and no fact predicate containing
`competitive` or `tournament`. Phase 145 added only the provider-neutral schema, validator, CLI, tests,
and gap documentation. Explanation v1/v2/v3/v4 behavior is unchanged.

## Current provider research and authoritative-source attempts

The following provider-controlled locations were selected because only the provider can establish an
official API contract and legal permission. Retrieval was attempted on 2026-08-12; none was available
to inspect in this environment. These URLs are research leads, not citations proving permission.

| Provider | Provider-controlled material attempted | Retrieval result | Licensing / retention conclusion |
|---|---|---|---|
| TopDeck.gg | `https://topdeck.gg/`, `https://topdeck.gg/api`, and the provider host's documentation/terms discovery paths | Proxy HTTP 403; web service HTTP 401 | Unverified; retention and redistribution not approved. |
| Wizards / Magic.gg | `https://www.magic.gg/` and linked Wizards legal/terms and event-publication material | Proxy HTTP 403; web service HTTP 401 | Unverified; first-party publication does not itself grant automated retention. |
| Melee | `https://melee.gg/` and provider-linked terms/API material | Proxy HTTP 403; web service HTTP 401 | Unverified; no supported automation or retention grant established. |
| MTGTop8 | `https://www.mtgtop8.com/` plus provider-hosted terms and `robots.txt` discovery | Proxy HTTP 403; web service HTTP 401 | Unverified; public HTML and robots policy would not alone establish retention rights. |
| MTGGoldfish | `https://www.mtggoldfish.com/` plus provider-linked terms/API material | Proxy HTTP 403; web service HTTP 401 | Unverified; no automation, retention, or redistribution grant established. |

No third-party summary was substituted for missing provider terms. Provider permission can change, so
an undated cached description would not satisfy this phase's current-verification requirement.

## Gate matrix

`U` means unknown because no current authoritative provider contract and response could be inspected.
Unknown fails a required gate; it does not mean the capability is absent.

| Required property | TopDeck.gg | Wizards / Magic.gg | Melee | MTGTop8 | MTGGoldfish |
|---|:---:|:---:|:---:|:---:|:---:|
| Structured API or machine-readable dataset | U | U | U | U | U |
| Authentication model | U | U | U | U | U |
| Automated retrieval permitted | U | U | U | U | U |
| Retention permitted | U | U | U | U | U |
| Redistribution restrictions known | U | U | U | U | U |
| Stable event identity | U | U | U | U | U |
| Stable deck identity | U | U | U | U | U |
| Stable Card identity or sufficient mapping coordinates | U | U | U | U | U |
| Event date and format | U | U | U | U | U |
| Placement/result | U | U | U | U | U |
| Decklist and mainboard/sideboard counts | U | U | U | U | U |
| Event size | U | U | U | U | U |
| Pagination and terminal-page proof | U | U | U | U | U |
| Rate limits | U | U | U | U | U |
| Historical coverage | U | U | U | U | U |
| Literal provider archetype labels | U | U | U | U | U |
| Complete reproducible denominator | U | U | U | U | U |
| Deterministically replayable snapshot | U | U | U | U | U |

All five candidates therefore fail the legal, technical, identity, denominator, and reproducibility
approval gates. There is no fallback to page scraping.

## Contract comparison

The existing v1 envelope is not weakened. A future source must populate provider/source identity,
endpoint, source byte digest/count, timestamps, licensing review, retention boundary, population and
completeness declarations, provenance, explicit unknowns, and digest-bound records. Records preserve
source-record and nullable event identity, canonical Card identity, literal provider labels,
mainboard/sideboard counts, placement/result, event size, and per-record lineage. Null remains unknown
and must be named; zero remains observed zero. Player identity stays forbidden and archetypes must not
be inferred.

A provider cannot pass merely by returning fields that fit the schema. It must also prove current
permission to automate and retain, stable identities, complete pagination, and the exact population
behind any denominator. No schema revision is justified while every provider contract is unavailable.

## Exact bounded design status

There is deliberately **no provider-specific acquisition design** to execute. Endpoint, authentication,
request count, page order, retry/rate-limit behavior, snapshot identity, deck/event/source identities,
Card mapping coordinates, denominator, and replay rules depend on a verified provider contract and
must not be invented.

The invariant design, if a later phase verifies exactly one provider, remains:

1. Scope exactly the ten frozen canonical Card UUIDs, one closed date interval, and explicitly
   supported format filters; never retain an unbounded corpus.
2. Stage responses outside the publication boundary; allowlist HTTPS host and endpoint, reject every
   redirect, never place credentials in URLs/output, and redact authorization values.
3. Require successful terminal pagination and recorded rate-limit behavior before projection. Reject
   malformed JSON, schema drift, duplicate required event/deck identities, conflicting records,
   ambiguous Card mappings, missing provenance, and incomplete pages.
4. Canonicalize and digest the exact source bytes and a deterministic projection sorted by provider
   event identity, deck identity, canonical Card UUID, and board. Retain only the minimum licensed raw
   material (outside Git when redistribution disallows it), request manifest, digests/byte counts,
   bounded evidence, validation diagnostics, and licensing record.
5. Treat absent fields as explicit unknowns. A denominator is only all provider records under the
   captured filters when completeness can be proven; otherwise it is null and no population fraction
   is supported. Event size is never a denominator.
6. Exact snapshot/digest replay is idempotent; same identity with different bytes is a conflict.
   Publish atomically only after all checks. On failure remove staging only; rollback removes the new
   proposal without modifying canonical data or earlier retained evidence.
7. Require manual PR review before the dedicated evidence boundary is admitted. A later, separately
   authorized phase—not Phase 146—would decide whether any fact can be created.

Because no provider passed, production acquisition was not executed, the retained competitive-evidence
census remains zero, and no post-merge workflow operation exists.

## Phase 147 recommendation

Phase 147 should remain a verification-only legal/API review performed where current provider-controlled
documentation and terms are reachable. Capture dated terms and API documentation, obtain explicit
written retention/redistribution permission when terms are silent, and run a non-retaining metadata
probe for identity, pagination, limits, coverage, and denominator semantics. Approve at most one
provider. If any hard gate remains unknown, fail closed again. Do not acquire decklists or create facts.
