# Strategic context requirements v1

This deterministic, read-only requirements engine answers **what evidence is
needed**, using the actual admitted six-land overlay. It evaluates neither Card
strength nor strategic relevance. Supplied information can inform a requirements
report while strategic validation remains unsupported. Completing every input
field never establishes a strategic conclusion.

Canonical base: `a57ff99b68696a91eb5e33b26c9e66eb86de70d8`, tree
`154f10442ac50f8fa7f08b3eb5a3008954a1abe4`. GitHub main and merged #225 were
verified with ordered parents `ff73976871a42264d060d2bf98d21d6e9d84acf8` and
reviewed head `db31a522f1eaff1b3b4096090230f2a535244ff4`. The clean local checkout
was reconciled hash-exact before creating `codex/strategic-context-requirements`.
Architecture v13 ACTIVE APPROVED, Decision 017 ACCEPTED and repository-first
governance remain binding. No AGENTS.md was found in the repository, workspace
parent or filesystem root.

The owning references are the unchanged
[approved design](design/rules-card-intelligence-v1/README.md) and
[public overlay contract](SIX_LAND_EVIDENCE_OVERLAY.md). This implementation does
not implement the design's six-layer proposal as a general platform.

## Contract, evidence and admission

- Public factory: `card_intelligence.strategic_requirements.load_strategic_requirements`.
- Policy domain: `six-land-strategic-requirements-policy-v1`.
- Policy identity:
  `sha256:9e74a8bbdc8daa94082cf9fa8a69754d70730169711abb837f75cbbde7e27c18`.
- Input contract domain: `six-land-strategic-context-input-contract-v1`.
- Input contract identity:
  `sha256:cad98af1ffae6321a4a41cffddfd9f2b4fa9b3968a1ea4be49a4b9954ed97c12`.
- Context input domain: `six-land-strategic-context-input-v1`, own `context_id`.
- Requirement domain: `six-land-strategic-requirement-v1`, own `requirement_id`.
- Report domain: `six-land-strategic-requirements-report-v1`, own `report_id`.

The factory calls the actual public overlay loader once with explicit selected
roots and independent expected profile/query/plan/decision identities. It uses
only public `card_ids`, `compare`, `validate_report`, `check` and `detailed`
interfaces. It verifies each exact registered pair and reuses the same admitted
batch. There is no neighboring private snapshot access, new Card-data pipeline,
copied example admission, cached authorization or imported-report constructor.
One factory invocation creates one query reader, one mechanical reader and one
retained-rules context through the overlay's existing owning contracts. Querying
additional requirements does not rebuild those catalogs or rule packages.

The source authority is unchanged: design
`sha256:fdd5e2362a36b906f3158977ced62aeb7f2f41e8a5acb111fbf1c01bbe6849a5`,
owner decision
`sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075`,
accepted interpretation collection
`sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`.
No pending interpretation is admitted as accepted by itself. All original
PENDING_NOT_ESTABLISHED records remain historical; the separate decision accepts
only their exact nine bounded retained-text interpretations. This establishes
neither current Oracle verification nor executable CardGameplaySemantics.

## Four finite question families

| Selector | Exact existing comparison | Requirements emphasized |
|---|---|---|
| `mana-and-utility` | Rishadan Port / Snow-Covered Wastes | Declared format/objective, mana needs, independent mana and utility abilities, opportunity cost, relevant/available targets, alternatives and independent impact validation |
| `variable-output` | Cabal Coffers / Snow-Covered Wastes | Written `{2}, {T}` cost, hypothetical versus observed controlled Swamps, composition/subtype/count provenance, resources/timing, alternatives and independent validation |
| `color-context` | Command Tower / City of Brass | Hypothetical commander identity versus declared deck colors, format/commander authority, written restrictions, separate damage trigger, alternatives and validation |
| `damage-ownership` | City of Brass / Tarnished Citadel | Separately triggered versus same-ability additional damage, missing general trigger procedure, life/prevention/resource context, objectives, alternatives and validated consequences |

The finite registry pins the exact Card UUID pairs from the approved identity
matrix; names are display data from admitted records. There are no extra Cards,
formats, archetypes or question families. Alternate labels and inferred UUID or
name matches are unsupported. Declared alternatives cannot expand the registered
comparison or introduce another Card's capabilities.

## Minimal supplied context

`strategic_context.make_context(declarations=None, hypothetical=None, leads=None)`
returns an immutable versioned input. `validate_context` and `parse_context`
reproduce its exact expected contract. Missing context contains empty declaration,
hypothetical-assumption and lead lists; it never defaults a count to zero or an
identity to an empty palette.

| Input | Bound and meaning |
|---|---|
| `format_label` declaration | Printable opaque label, 1–80 characters. Explicit user declaration only; no format registry, date/legality validation or metagame lookup. |
| `deck_objective` declaration | One of `mana-flexibility`, `resource-output`, `interaction-utility`, `effect-tradeoffs`. Investigation intent only; not an archetype or functional-role classification. |
| `deck_color_requirements` declaration | Canonical unique W,U,B,R,G subset, including explicit empty. Unverified declared needs; never used as commander identity or proof of legality/payment. |
| `alternatives` declaration | Up to six unique `{namespace, card_id}` objects in exact Card ID order. Only the six supported legacy Card UUIDs; explicit empty is recorded without claiming exhaustive search or viability. |
| `hypothetical` | The original `card-rules-hypothetical-mana-input-v1` record. Exact integer Swamp count 0..1,000,000 only for `variable-output`; canonical hypothetical WUBRG identity only for `color-context`. Missing/zero/empty/conflicting states retain their original meaning. |
| `leads` | Up to four distinct `{category, reference}` entries. Category: `deck-context`, `format-legality`, `rule-procedure`, `strategic-performance`. Reference: 1–160 printable characters. Opaque leads only; no dereferencing, filesystem reading, network lookup or authentication. |

Declarations are `{dimension, value}` entries. Up to eight entries and at most two
different values per dimension are allowed. Identical duplicates reject; two
different values for a single declared field conflict, with neither preferred.
Lead references are not contradictory factual claims and are never promoted into
authenticated evidence. Hypothetical contradictions use the existing scenario
consumer. A conflict in one dimension does not erase other independently supplied
inputs or accepted source evidence. For example, conflicting format labels do
not change the conditional arithmetic under a separately supplied count of five.
Differing deck colors and hypothetical commander colors are not automatically
classified as illegal or contradictory.

Context is bounded at 8,192 bytes. New records require exact JSON types, finite
fields, canonical UTF-8 JSON with LF and domain-separated identities. Unknown
fields, duplicate keys, floats, boolean counts, malformed palettes, foreign
identities and unsupported observed-state/role/verified-format assertions reject.
No arbitrary decklist, observed game-state object or general query language exists.

## Independent requirement statuses

Every requirement includes a category, needed information, rationale, exact
support references, originating question or structured capability, context
pointers, independently represented statuses, a future consumer and validation
method. A sealed requirement identity binds that complete record.

| Dimension | States and limits |
|---|---|
| Information | `ABSENT`, `HYPOTHETICAL_SUPPLIED`, `DECLARED_UNVERIFIED`, `ADMITTED_EXISTING_EVIDENCE`, `CONFLICTING` |
| Bounded satisfaction | `SATISFIED_WITHIN_RETAINED_SCOPE`, `SATISFIED_FOR_HYPOTHETICAL_TEXT_ONLY`, `DECLARATION_RECORDED_ONLY`, `BOUNDARY_DISCLOSED_ONLY`, `UNRESOLVED` |
| Validation | `EXISTING_EVIDENCE_ONLY`, `HYPOTHETICAL_TEXT_ONLY`, `UNIMPLEMENTED_OR_UNAUTHORIZED` |

Categories separate universal context, capability context, procedure/ownership,
independent strategic validation, and identity/permissions. Generic templates are
selected by admitted output patterns, dependencies, effect ownership, procedure
and relationships between abilities. Card names and subject labels never select
requirements. The finite question registry declares legitimate questions; it
does not supply prepared strategic answers.

Examples of independent statuses:

- A declared objective records intent; target relevance and opportunity cost
  remain unresolved. It produces no role classification or strategic advantage.
- Hypothetical count five satisfies only written-output substitution. Deck Swamp
  composition, actual count, timing, available resources and independent strategic
  validation remain unresolved. Net mana, break-even and payment are not computed.
- Hypothetical W/B satisfies only the original written-choice calculation. It
  proves no commander, legal deck, current available mana or superior fixing.
- A format label remains DECLARED_UNVERIFIED; format legality remains unresolved.
  A reference claiming to prove legality is still an unauthenticated lead.
- Ownership evidence is admitted within retained scope. General triggered
  procedure, actual events, life/prevention context and consequences remain
  outside currently authorized validation. Damage is never executed.
- Current-source/version review, production identity and each source/use permission
  remain independent unresolved requirements, regardless of declaration completeness.

`request_state` is `ANSWERABLE_REQUIREMENTS_ONLY` with no context,
`PARTIALLY_INFORMED` with supplied declarations/assumptions/leads, or `CONFLICTING`
with inconsistent premises. Unsupported requests raise structured errors.
`answerability.requirements_query=ANSWERABLE` means only that this engine can list
requirements; `strategic_evaluation=UNSUPPORTED` and
`strategic_validation=UNIMPLEMENTED_OR_UNAUTHORIZED` always remain separate. There
is no confidence score, recommendation readiness flag or automatic elevation.

## API, CLI and detailed inspection

```python
from card_intelligence.strategic_requirements import load_strategic_requirements
from card_intelligence.strategic_context import make_context
from card_rules_pilot.mana_scenario_policy import make_scenario

engine = load_strategic_requirements(**explicit_overlay_evidence_arguments)
supplied = make_context(
    [{"dimension": "format_label", "value": "owner-declared format"}],
    hypothetical=make_scenario([
        {"dimension": "controlled_swamp_count", "value": 5}
    ]).to_dict()).to_dict()
report = engine.requirements("variable-output", supplied)
engine.missing("variable-output", supplied)
engine.provenance("variable-output", supplied)
engine.requirement("variable-output", exact_requirement_id, supplied)
engine.for_cards(explicit_namespace, exact_sorted_registered_pair, "variable-output", supplied)
engine.check()
engine.validate_report(report.to_dict())
engine.parse_report(report.to_json().encode())
full_overlay = engine.detailed(report.to_dict()["overlay_reference"])
historical = engine.detailed(report.to_dict()["full_evidence_reference"])
```

`policy_document()` and `contract_document()` expose independent decoded policy
and input-contract views from their owning modules. Policies, contexts and reports
privately own their data. New public loads revalidate current evidence; queries
reuse an immutable admitted snapshot. `check()` explicitly describes this snapshot
scope and never claims to have refreshed current disk evidence.

Run `PYTHONPATH=src python -m card_intelligence.strategic_requirements_cli` with
the same explicit root and expected-ID options documented for the overlay. Use
`--json` before the subcommand for canonical output. Structured subcommands:

```text
requirements mana-and-utility
requirements mana-and-utility --objective interaction-utility
requirements variable-output --swamp-count 5
requirements color-context --commander-colors WB
requirements damage-ownership
requirements mana-and-utility --format-label "owner-declared format"
requirements color-context --deck-colors WB --lead format-legality "unverified-review-lead"
requirements variable-output --swamp-count 0 --swamp-count 5
missing variable-output
provenance color-context
requirement color-context EXACT_REQUIREMENT_ID
check
validate canonical-requirements-report.json
detail canonical-evidence-reference.json
```

Options also include repeated `--format-label`, `--objective`, `--deck-colors`,
`--alternative NAMESPACE CARD_UUID`, `--lead CATEGORY OPAQUE_REFERENCE`, optional
`--namespace` / repeated `--card-id` for exact registered-pair verification, or a
strict canonical `--context FILE` instead of context options. `--commander-colors ''`
is explicitly empty. Exit 0 means supported requirements inspection, **never**
strategic readiness; exit 2 is rejection; exit 3 preserves a conflicting report.
There are no mutation, recommendation, simulation or natural-language commands.

Reports contain the exact question/Card identities, source-bound capability and
cost/ownership summaries, admitted dossier/candidate/decision/source references,
declared context and authority, grouped requirements, missing inputs, conflicts,
unresolved validation, unsupported conclusions and unchanged authority boundaries.
Per-requirement support keys resolve to the local Card/capability evidence table;
its exact provenance and owning detailed references permit full inspection. The
complete overlay is referenced by report identity, bytes and SHA-256, not copied
into every report. Existing detailed references are verified through the public
overlay route. The original 689,253-byte historical report retains its exact
identity and raw SHA-256, with pending history intact.

Report validation regenerates the expected complete report, including all nested
statuses, provenance and supplied inputs. Self-consistent rehashing cannot admit
changed requirements or source substitutions. Readable rendering displays each
needed input, rationale, independent statuses and future method without appending
full historical JSON.

## Actual demonstrations, sizes and tests

[Actual demonstration receipt](examples/strategic-context-requirements-v1.json)
records twelve real admitted requests: all four question families, missing and
declared objective, missing/five/zero Swamps, missing/WB/empty commander identity,
damage ownership, unverified format, every declared field plus unverified leads,
and conflicting counts. It includes exact input/report/requirement/calculation
identities, changing statuses, unchanged strategic abstentions, measured bytes and
timings, actual CLI results, unsupported requests and actual coherently rehashed
owner-decision/report rejection. Tests reproduce its outputs through the API.

No existing size limit is raised: reports are capped at 65,536 canonical bytes,
readable output at 32,768 bytes. The receipt contains actual per-request sizes and
observed integer-microsecond timings, outside deterministic report identities.
Tests exercise each family, maximal bounded contradictory contexts, admission
within 30 seconds and view/rendering within 5 seconds. Exact final measurements
and test receipts are included in the draft PR.

Meaningful regressions cover the complete six-Card/nine-subject cohort, four-family
routing, generic template behavior under renamed labels, input/authority separation,
conflicts and leakage, costs/ownership/procedure, no automatic strategic validation,
all identity/pilot/permission abstentions, read-only public composition and CLI,
tampering and strict JSON, private ownership, historical output parity and actual
incompatible writer-expanded catalog rejection. The nested writer path tests real
rejection without substituting a positive historical catalog or adding skips.

All existing runtime/data/policy/design/report/workflow files are unchanged.
Two test-only helper successors add exactly four pinned source paths to inherited
censuses and reconstruct their predecessor bytes exactly. All earlier pin constants,
negative checks, report identities, source inventories, workflow gates and timeouts
remain binding. Full local and both final-head hosted outer/actual nested discovery,
real 654-card writer, bare-remote publication and matching readback remain required.
Their exact final-head evidence is recorded in the draft PR.

## Remaining boundaries and next recommendation

Historical Card/Printing correspondence remains established for all six. Only
Snow-Covered Wastes has the current promoted Scryfall identifier edge; the other
five remain IDENTITY_NOT_ESTABLISHED. All operator-production/typed-seed joins
remain IDENTITY_NOT_ESTABLISHED; all land functional-role/contextual-pilot coverage
remains NOT_IN_SUPPORTED_COHORT. These distinct abstentions remain visible.
Tower's 111 Printing memberships inherit no general interpretation approval.

Coverage remains 104 CR units / 16 projections / 24 retained land-context units.
No new Card, Printing, source acquisition, rule unit/projection, semantic approval,
role classification, identity promotion, market observation or strategic ranking.
canonical_admission=false; execution_authority=BLOCKED; semantic_closure=OPEN;
all ten activation responsibilities OPEN / EXECUTION_BLOCKED. Source-policy
clearance not_granted; private retention, redistribution, free/commercial service
and AI export NOT_ESTABLISHED. Tier A remains non-production.

Exactly one next recommendation, not authorization: a **finite read-only context
evidence review packet** for one existing question family. Bind owner-supplied
context evidence to exact content/source/scope/permission and independent review
references while retaining unsupported strategic evaluation. This addresses the
current opaque-lead gap and reuses the admission/identity infrastructure. Exclude
new acquisition, deck parsing, source projection, role/semantic promotion,
strategic scoring/recommendations, interaction generation and simulation.

Stop for independent Senior PM review and final owner approval. No merge or
auto-merge. Future implementation milestone authorized: false. Future source
projection authorized: false. Future milestone begun: false.
