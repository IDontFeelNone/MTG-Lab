# Local Deck Consistency Workbench V1

A local browser application for exact **card access**, using the unchanged
[Supplied Deck Consistency V1](SUPPLIED_DECK_CONSISTENCY_V1.md) Python API.
It does not estimate casting, combo success, strategic superiority or win rates.
No card catalog, external provider, collection or Comprehensive Rules source is needed.

## Start and stop

Use Python 3.12 and the repository's existing Python environment. From the checkout:

```console
python -m pip install -r requirements.txt
PYTHONPATH=src python -B -m workbench
```

The terminal prints an address such as `http://127.0.0.1:54321/`. Open that exact
address in a browser. An unused local port is selected by default; optionally use
`--port 8765`. The host cannot be changed. Stop with **Ctrl+C** in the terminal.
There is no installer, public deployment, automatic browser launch or background service.

## Analyze a deck

1. Add card rows, enter readable labels, quantities and explicit sections.
   A card receives a stable caller-local identity; its label never resolves a
   canonical Card, alias, Oracle text or external source. Use “Add existing card
   row” to repeat an identity unambiguously in another row or section.
2. Select the exact draw section. The displayed size is derived from those rows.
   Sideboard, commander, companion and other sections are excluded unless explicitly
   selected. `other:NAME` is a supported named experimental section, not a game rule.
3. Confirm that the selected population is complete. This is your declaration,
   not independent verification of a physical deck or format legality.
4. Define one to three groups by selecting entered cards, and choose each minimum.
   All minima must hold jointly. Groups must be disjoint. You declare the cards'
   interchangeability; the application infers no synergy or strategic roles.
5. Enter cumulative, nondecreasing cards-seen observations. “Turn 4” is a caller
   label, not an implemented draw schedule. No mulligans or additional draws are inferred.
6. Calculate. Read exact fractions, percentages, derived counts and limitations.
   A valid requirement exceeding the available group copies is an impossible
   event with exact zero probability, not a malformed deck.

Bounds remain 1–120 selected cards, 1–3 groups and 0–20 cards seen (never more
than the selected size), with at most 21 observations and 512 rows per configuration.
Invalid or incomplete inputs produce a visible refusal without authoritative partial results.

## Compare alternatives

“Duplicate as alternative” preserves caller-local card identities, group membership
and observations. Change quantities in the duplicate. Shared identity labels remain
shared display labels; adding a new card creates a different local identity.

The unchanged analytical owner supplies differences only when exact members,
minima, selected sections and full observation schedules match. Different labels
alone cannot establish equivalence. Otherwise both results remain visible with
comparison abstention reasons. No “better deck” ranking follows.

The explicitly loaded fictional example has 3 target copies and 57 other cards.
Seven-card access is `5397/17110` (31.542957334892%). Duplicating and changing the
target to 4 and remainder to 56 gives `38962/97527` (39.949962574467%). The exact
difference is `81991/975270`, presented as 8.407005239575 percentage points.
These are mathematical examples, not evidence of real card behavior.

## Freshness, download and privacy

Every analytical edit invalidates visible results and disables downloading until
recalculation. An old in-flight response cannot become current after an edit.
“Download current report” is an explicit action and exports the calculated wrapper,
labels, normalized input, original analytical report and deterministic identities.
It contains your deck labels and quantities; handle it as private if appropriate.

Nothing is automatically persisted, exported, sent to an AI provider or stored in
browser local storage. Reloading loses the workspace. Browser history, explicitly
downloaded files, extensions and the host operating system are outside this application's
memory-only guarantee. No private collection or source is discovered.

## Developer boundary

`workbench.adapter.assess_workbench(request)` accepts the closed
`deck-workbench-input-v1` envelope: exactly `schema_version`, `labels` and `analysis`.
`analysis` uses the existing supplied-deck input contract. `labels` is an exact list
of `{card_id, label}` bindings for every declared identity, with no extra identities.
Both strings are trimmed printable text, 1–128 characters; identities are unique.
Labels may coincide, but that never merges identities. Raw requests are at most
196,608 bytes. Duplicate JSON keys, nonfinite numbers and unknown fields refuse.

The adapter delegates normalization, probabilities, comparison equivalence and
refusals to `assess_supplied_decks`. It does no combinatorial calculation. It embeds
the original owner report unchanged, adds exact-rational percentage presentation
(12 places, half-even), and hashes normalized input and report with versioned
SHA-256 domains. Output is capped at 393,216 bytes. Presentation is not used to
calculate deltas, classify impossible events or establish comparison equivalence.

`deck-workbench-report-v1` contains `schema_version`, `status`, `input`, `input_id`,
`analysis`, `presentation`, `authority`, `real_gameplay_authorized` and `report_id`.
The report ID excludes only itself. Refusals contain exactly `schema_version`,
`status: REFUSED` and `reason`. UI labels and report values are rendered as text,
not HTML. Browser state is detached from request/report identities.

The standard-library HTTP adapter serves only three fixed bundled assets and
`POST /assess`; it exposes no general REST, file, collection, database or shell API.
It binds to IPv4 loopback, uses an ephemeral launch token, exact Host and Origin
checks, JSON-only bounded requests, socket timeouts, no CORS and no-store/CSP headers.
The launcher has no public-host option. It does not defend against malicious local
processes, browser extensions or a compromised machine; no authentication service
or remote multiuser access is claimed.

Existing probability APIs/CLI/contracts, collection integration, gameplay, historical
evidence, Architecture v13, Decision 017 and source permissions remain unchanged.
The full-corpus CR HOLD remains. Future application modules require separate owner
authorization; no AI, pack interface, collection workspace or follow-on is enabled here.
