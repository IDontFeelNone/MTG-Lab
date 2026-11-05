# Six-land exact-ID evidence overlay v1

This read-only, non-production overlay connects exact attached Card identities,
mechanical dossiers, the nine accepted retained-text subjects, original concise
explanations and optional hypothetical mana calculations. It implements only the
first-ranked option in the approved
[design](design/rules-card-intelligence-v1/README.md). It is not a general
orchestrator, strategic evaluator or executable CardGameplaySemantics provider.

Canonical base: `ff73976871a42264d060d2bf98d21d6e9d84acf8`; tree
`0ae896429fb74912ca76671a8a55340a8b3ddc92`. GitHub main, merged #224,
ordered parents `9d89156cd14eedfb7b2c87cb89ac46fd1803b28d` and
`3ef579b5434d56917ed8afe87e9e354af328b734`, and the clean checkout were verified
before creating `codex/six-land-evidence-overlay`. Architecture v13 ACTIVE
APPROVED and Decision 017 ACCEPTED remain binding. No AGENTS.md was present in
the repository, workspace parent or filesystem root.

## Public contract and admission

API: `card_intelligence.land_overlay.load_land_overlay`. All evidence roots and
independent expected profile, query, plan and owner-decision IDs are required.
`design_root` optionally selects another copy of the exact frozen approved package.
There is no imported-report, pending-candidate or caller-supplied approval route.

- Report version/domain: `six-land-exact-id-evidence-overlay-v1`.
- Policy domain: `six-land-evidence-overlay-policy-v1`.
- Policy identity:
  `sha256:72cc8f621290a785d138fafdfb218b6cce9803ae9a0cc536b7ea306eb8059a5b`.
- Approved design:
  `sha256:fdd5e2362a36b906f3158977ced62aeb7f2f41e8a5acb111fbf1c01bbe6849a5`.
- Exact owner decision:
  `sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075`.
- Accepted collection:
  `sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`.

The factory verifies the immutable design package; actually attaches the current
catalog; creates one public query/mechanical reader; passes that verified reader
through the existing land/decision admission; and composes the admitted decision
into the existing explanation and scenario consumers. No original reasoning,
explanation, effect or hypothetical policy is rewritten. The small public seams
are `mechanical_reader=` on the original land readers,
`land_explanation.from_decision` and `mana_scenario.from_explanations`. They accept
actual owning reader types, revalidate bindings, and independently own their outputs.
The new `verify_evidence()` accessors reproduce the exact owner decision/original
evidence and recompute the explanation batch before cross-consumer composition;
a matching reader type or a coherently rehashed copied report is insufficient.
Old constructors and report bytes retain their behavior.

`projection.historical_evidence.load_historical_admission` is the narrowly scoped
public route to the owning historical promotion verifier. It independently pins
the original audit and payload bytes, checks original candidate membership,
preflight, review and lineage through the original verifier, and exposes only
the six authorized Printing records as independent decoded views. The overlay
uses the existing public query APIs to verify Card/Printing membership and current
identifier edges. It recomputes the six mechanical dossiers through their owner
and compares them with the actual accepted retained-source bindings and fixed
design identities. Hashes supplement owning validation; they do not replace it.

One batch creates one query, one mechanical reader and one retained-rules context.
No catalog or rule package is rebuilt per subject or per comparison. The readers'
existing unchanged-input verification still runs at their public boundaries.
No neighboring `_snapshot`, `_overview` or other private state is accessed.
After admission, the overlay retains immutable owned bytes and its privately
created immutable explanation/scenario consumers. Callers receive independent
decoded documents. `check()` checks the admitted snapshot; a **new public load**
revalidates current selected filesystem evidence. A previous snapshot never
silently switches to changed disk evidence or a historical fallback fixture.

## Exact identities and abstentions

Every Card request requires namespace **`magic:legacy-promoted:card`** and one
exact Card UUID from the approved matrix. Display names come from admitted Card
records and never select identity, semantics or conclusions.

| Display label | Exact Card UUID | Current promoted Scryfall edge |
|---|---|---|
| Snow-Covered Wastes | `46a07b53-ff58-4bd6-80dd-ded2eb0e29a3` | ESTABLISHED |
| Rishadan Port | `f3e8dc56-2810-474e-a6a7-9c3555f94ae9` | IDENTITY_NOT_ESTABLISHED |
| City of Brass | `f25351e3-539b-4bbc-b92d-6480acf4d722` | IDENTITY_NOT_ESTABLISHED |
| Tarnished Citadel | `66ae2562-68e9-4c77-ba0a-57f8ff37f656` | IDENTITY_NOT_ESTABLISHED |
| Cabal Coffers | `7358e164-5704-4e78-9b21-6a9bf2a968ce` | IDENTITY_NOT_ESTABLISHED |
| Command Tower | `0895c9b7-ae7d-4bb3-af17-3b75deb50a25` | IDENTITY_NOT_ESTABLISHED |

Historical Card/Printing/provider correspondence is ESTABLISHED for all six.
Printing namespace `magic:mtgjson:printing` and provider observation namespace
`scryfall:historical:printing-observation` remain separate. Their UUIDs are not
interchangeable. The [exact matrix](design/rules-card-intelligence-v1/identity-joins.json)
and each report retain those distinct IDs and proof pointers.

Typed-seed and operator-production identities remain IDENTITY_NOT_ESTABLISHED
for all six. Functional-role and contextual-comparison pilot membership are
independently NOT_IN_SUPPORTED_COHORT. These statuses neither suppress authorized
historical evidence nor grant new authority. Tower retains 111 historical Printing
memberships, but only its single accepted observation supplies the reviewed text.

## Report shape and methods

The finite contract contains `schema_version`, `kind`, `namespace`, `selector`,
`join`, `identity_status`, policy/design/decision/collection identities, accepted
scope, exact versioned `scenario`, state, `cards`, optional original `comparison`,
catalog binding, full historical reference, authority, limitations and `report_id`.
Each Card contains exact identity/observation/Printing/joins, mechanical dossier
and literal source fields, and its relevant accepted subjects. Each subject keeps
historical versus current status, original classification and ownership,
the original concise explanation, original hypothetical calculation, provenance,
and verified detailed references. No general A–F strategic platform is registered.

```python
from card_intelligence.land_overlay import load_land_overlay, CARD_NAMESPACE
from card_rules_pilot.mana_scenario_policy import make_scenario

overlay = load_land_overlay(**explicit_evidence_arguments)
assumptions = make_scenario([
    {"dimension": "controlled_swamp_count", "value": 5}
]).to_dict()
card = overlay.card(CARD_NAMESPACE,
    "7358e164-5704-4e78-9b21-6a9bf2a968ce", assumptions)
comparison = overlay.compare("variable-output", assumptions)
overlay.provenance(CARD_NAMESPACE, "7358e164-5704-4e78-9b21-6a9bf2a968ce")
overlay.identity(CARD_NAMESPACE, "7358e164-5704-4e78-9b21-6a9bf2a968ce",
                 "operator_production")  # IDENTITY_NOT_ESTABLISHED
overlay.check()
overlay.validate_report(card.to_dict())  # recomputes the expected complete report
overlay.parse_report(card.to_json().encode())  # strict canonical JSON
full = overlay.detailed(card.to_dict()["full_evidence_reference"])
```

`policy_document()` returns the independent deterministic policy view.
`to_json()` emits canonical UTF-8 JSON with LF. `render_overlay(document)` emits
readable findings, IDs, assumptions, unknowns and authority without appending raw
historical JSON. Canonical provenance includes exact premise/source-field pointers;
readable mode identifies the same report and every explanation finding.

All fields and strict JSON types are validated by exact expected-report
reproduction, including nested evidence and authority. Unknown fields, duplicate
keys, floats in new reports, noncanonical bytes, foreign selectors and coherently
rehashed substitutions reject. Counts are exact integers 0..1,000,000; color sets
are unique canonical W,U,B,R,G subsequences. Missing, explicit zero, explicit empty,
conflicting and unsupported contexts remain distinct. Only the relevant accepted
subject receives an assumption. Mechanical detailed documents retain their
**original owning numeric representation**; no numeric coercion changes dossier IDs.

## CLI and actual demonstrations

Run from the repository with `PYTHONPATH=src`. The following options are required
before the subcommand; use the actual selected roots and independent IDs:

```bash
python -m card_intelligence.land_overlay_cli \
  --catalog-root . --mechanical-root . --review-root reference-reviews \
  --cohort-root data/review/land-mana-utility \
  --decision-root data/review/land-semantic-decisions \
  --expected-profile-id sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e \
  --expected-query-snapshot-id sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7 \
  --expected-plan-id sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5 \
  --expected-decision-id sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075 \
  --json card --namespace magic:legacy-promoted:card \
  --card-id 7358e164-5704-4e78-9b21-6a9bf2a968ce --swamp-count 5
```

With the same root/identity options, supported subcommands include:

```text
compare variable-output --swamp-count 5
compare color-context --colors WB
compare damage-ownership
compare mana-and-utility
card --namespace magic:legacy-promoted:card --card-id 0895c9b7-ae7d-4bb3-af17-3b75deb50a25 --colors WB
provenance --namespace magic:legacy-promoted:card --card-id f3e8dc56-2810-474e-a6a7-9c3555f94ae9
identity --namespace magic:legacy-promoted:card --card-id f3e8dc56-2810-474e-a6a7-9c3555f94ae9 --join current_identifier_edge
check
validate canonical-overlay-report.json
detail canonical-reference.json
```

Omit `--json` for readable mode. `detail` explicitly requests full canonical
owning evidence; it is never automatically appended. Exit codes: 0 supported;
2 structured rejection; 3 conflicting assumptions; 4 explicit identity/cohort
abstention. Repeated count/color options preserve valid contradictory premises.
`--colors ''` explicitly supplies an empty identity. There is no name selector,
game-state JSON, mutation command, natural-language parser or network access.

[Actual demonstration receipt](examples/six-land-overlay-v1.json) contains all six
Card views, four comparisons, exact report/calculation/candidate identities,
sizes, measured timings, assumptions, missing/zero/empty/conflicting outputs,
abstentions, actual CLI results and rejection codes. Tests reproduce its report
identities and byte sizes through the actual admitted API.

- Wastes retains `{T}` and fixed one colorless written output, with its historical
  and current identifier correspondences established.
- Port exposes its missing promoted identifier edge while retaining independent
  `{T}` mana and `{1}, {T}` targeted utility subjects. No mana/target borrowing.
- City retains a separate triggered damage subject; general triggered procedure
  remains unresolved. No event is detected or damage executed.
- Citadel's color-choice activation owns its additional damage clause; its
  colorless activation does not inherit that clause.
- Coffers with assumed five Swamps has conditional written quantity 5 B; full
  `{2}, {T}` cost stays separate. No payment, actual/net output or value follows.
- Tower with hypothetical W/B supplies exactly those written color choices,
  without inventing a commander or actual available mana.
- Coffers/Wastes compares the conditional quantity to fixed one C with separate
  costs/dependencies. Tower/City compares restricted W/B to unrestricted written
  any-color choice while also retaining City's separate trigger evidence.
- Foreign Card/namespace queries reject with UNSUPPORTED_CARD_ID /
  UNSUPPORTED_NAMESPACE. Current-edge and production requests abstain separately.
- A coherently rehashed actual changed owner decision rejects with
  EVIDENCE_ADMISSION_REJECTED. A rehashed report claiming production eligibility
  rejects with REPORT_INTEGRITY_REJECTED. Changed detailed references reject with
  REFERENCE_INTEGRITY_REJECTED.
- The verified full historical route reproduces exactly 689,253 bytes,
  SHA-256 `0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515`,
  and original pending report `sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd`.

## Size, performance and preservation

Canonical reports are bounded at 65,536 bytes and readable views at 32,768 bytes.
Neither bound nor any inherited timeout is increased. One actual load measured
5,343.177 ms; subsequent view plus readable rendering measured 9.629–44.069 ms.
Receipt timings are observations (integer microseconds), not report identity inputs
or guaranteed performance. Tests allow 30 s for admission and 5 s per view and
verify every actual Card/comparison against the fixed byte bounds.

| Actual view | Canonical bytes | Readable bytes |
|---|---:|---:|
| Wastes | 16,340 | 5,515 |
| Port | 26,405 | 7,648 |
| City | 27,340 | 7,891 |
| Citadel | 26,982 | 7,845 |
| Coffers, count five | 17,634 | 5,851 |
| Tower, W/B | 17,559 | 5,917 |
| mana-and-utility | 43,122 | 12,508 |
| damage-ownership | 55,132 | 15,539 |
| variable-output, count five | 34,137 | 10,428 |
| color-context, W/B | 45,011 | 12,809 |

Existing data, design package, policies, dossiers, decisions, candidate records,
source projections, identity/market records, reports, workflows and validation
timeouts are unchanged. Five owning reader modules receive only the small public
composition seams. Historical tests retain their original pin constants; finite
byte-exact reversible adapters reconstruct those five original source files and
the three-path source-inventory extension plus four exact historical test adapters,
rejecting every other edit. The older
Card-intelligence census separately checks exact hashes for the three additions.
The original historical overview and existing explanation/scenario documents are
reproduced byte-for-byte. No old pending record becomes accepted by relabeling.

Focused regression coverage includes all identities/subjects/comparisons, distinct
join abstentions, source ownership, explicit context edge cases and leakage,
mechanical/decision/report tampering, public batch reuse, independent ownership,
actual read-only CLI, historical source/report parity, size/timing bounds and
rejection of the **actual incompatible 654-card writer-expanded catalog**. The
nested publication path cannot substitute a historical positive fixture or skip.
One stable full local discovery and both final-head hosted complete outer/nested
discovery, real 654-card writer/publication/readback gates remain required; their
exact final-head receipts are recorded in the draft PR.

## Boundaries and stop

Coverage remains 104 CR units / 16 projections / 24 land-context units. Zero new
Cards, Printings, sources, interpretations, role classifications, semantic approvals
or executable semantics. canonical_admission=false; execution_authority=BLOCKED;
semantic closure OPEN; all ten activation responsibilities OPEN / EXECUTION_BLOCKED.
Source-policy clearance not_granted; private retention, redistribution, free service,
commercial service and AI export NOT_ESTABLISHED. Tier A remains non-production.
Integrity is neither semantic truth nor legal permission.

One proposed next milestone is a finite **strategic-context requirements view** for
the four existing comparison questions: make missing deck/format/objective and
validation evidence actionable while keeping every strategic implication a
hypothesis. It would exclude rankings, new role/semantic interpretations, source
acquisition, production promotion, interaction generation and simulation. It is
recommended only and has not been authorized or begun.

Stop for independent Senior PM review and final owner approval. No merge or
auto-merge. Future implementation milestone authorized: false. Future source
projection authorized: false. Future milestone begun: false.
