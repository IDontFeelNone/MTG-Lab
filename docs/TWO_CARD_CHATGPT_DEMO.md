# Two-Card Evidence-to-ChatGPT Demonstration

## Scope and canonical baseline

Canonical main independently verified on 2026-10-12: `e5e11c41818b3a7e6bec85418a75a37e0ef638f0`, the merge of GitHub PR #164 including its Product field-provenance repair. Architecture v12 is frozen. GitHub PR numbers and project phase numbers are independent; this named milestone receives no new phase number.

This milestone demonstrates one read-only path from retained production evidence to bounded structured Card dossiers, existing-contract reasoning contexts, and human-readable explanation examples. The application performs the descriptive calculations; ChatGPT's downstream role is reasoning and explanation over those supplied results. No model execution or live ChatGPT connection is provided.

Exactly two production Cards are authorized:

| Card | Exact canonical production Card ID |
|---|---|
| Sol Ring | `6ad8011d-3471-4369-9d68-b264cc027487` |
| Counterspell | `cc187110-1148-4090-bbb8-e205694a39f5` |

The producer requires an exact production ID and matching canonical Card reference. It does not select by name or substitute a legacy seed Card. Target names and IDs are bound in the demonstration script, rather than embedded as product/card-specific rules in generic engines.

## Existing capabilities composed

The narrow query repair in `src/query/engine.py` projects the actual retained promotion-audit format and direct canonical-record provenance. It retains source identifiers, evidence references, promotion identity, and compact audit integrity references without embedding the complete promotion batch in a reasoning context. The existing package-shaped audit path remains supported. No audit, canonical record, or source snapshot is rewritten.

`scripts/card_dossier.py` is a manual demonstration composition helper over the existing public canonical semantic query, `ReasoningContextBuilder`, and `CardValueExplanationEngine`. The generic Reasoning Context Builder remains a semantic-only consumer; source-byte verification occurs at the script's composition boundary. The helper produces immutable `card-evidence-dossier-v1` review outputs and a manual handoff using `canonical-reasoning-context-v1` / `ReasoningContextResult`. The existing Card Intelligence and Decision Intelligence contracts remain unchanged. No AI provider is registered or executed, and no acquisition-decision policy is invoked.

The handoff retains the base canonical request and labels its supplemental payload `bounded_card_value_evidence_manual_handoff`. This supplied Card Value projection is not a semantic analytics query result; `analytics_snapshot_id` remains `null`. The manual composition is explicit rather than adding a new generic semantic operation or altering the Reasoning Context Builder's dependencies.

Each dossier binds the canonical query snapshot, retained canonical-state byte digest, source Card Value report content identity, base reasoning context, active knowledge-fact references, source references, and exact observation IDs. These identities have different scopes: a query snapshot or report content hash is not the raw canonical-state file digest. The retained evidence dates remain historical source/observation dates; replay does not invent a current observation timestamp.

## Retained evidence and its meaning

The dossiers expose supported Card identity and rules/mechanical facts, retained Printing coverage and exact sampled Printing identities, observed market history, provider-specific demand evidence, provenance, uncertainty, and unsupported dimensions.

| Evidence | Retained source boundary | Supported meaning and limits |
|---|---|---|
| Canonical Card and promoted lineage | `data/canonical/state.json`, retained Phase 119 audit and production review evidence | Exact admitted production identity and source lineage; seed identities are excluded. |
| Printing history | Retained Phase 135 MTGJSON projection and Phase 136 promoted Printings | Retained Printing coverage and dated identity/history evidence; counts do not establish total supply or scarcity. |
| Market history | Two retained MB2 Scryfall acquisitions, their manifests and immutable observations | Four observations per Card, grouped by compatible Printing/market/finish/language/currency/price-type dimensions. Historical provider price fields do not establish current offers, completed sales, liquidity, or future price direction. |
| Scryfall demand signal | `data/card_intelligence/demand/phase-142/scryfall-edhrec-rank.json` | Provider-supplied EDHREC ordinal at dataset timestamp `2026-08-04T21:10:15.879000Z`; not a deck count, demand score, or usage probability. |
| MTGJSON deck signal | `data/card_intelligence/demand/phase-143/mtgjson-decks.json` | Literal associations at dataset timestamp `2026-08-10T22:23:35Z`: Sol Ring appears in 241 and Counterspell in 63 of 3,004 represented provider deck files. This denominator is the retained provider corpus, not global decks, players, actual-play usage, or competitive performance. |
| Reviewed knowledge facts | Active retained facts under `data/knowledge/facts/magic/<Card ID>/` | Dated predicates, evidence source IDs, reference locations, and explicit unknown/unsupported states; no new knowledge admission. |

Scryfall and MTGJSON remain independent signals. They are not combined into a strategic, popularity, competitive, or investment score. Literal provider deck names/formats are associations rather than independently verified archetypes or competitive results.

Replay verifies retained projections and manifests against their recorded byte/record digests. Upstream bulk-source digests are preserved as acquisition assertions where the original bulk bytes are not retained; the dossiers explicitly distinguish that limitation from verification of available repository bytes. Source timestamps, retrieval timestamps, endpoints, recorded attribution/license considerations, and known missing original bytes remain separately represented. No external request occurs during generation or verification.

## Bounded output and deterministic replay

Each serialized dossier and handoff context has a 65,536-byte maximum. This byte cap is a repository output bound, not a claim about a particular ChatGPT model's token capacity. The projection retains all four market observations, 11 active knowledge-fact references, and seven evidence sources for each Card. It includes at most five Printing identities, five retained-set identities, and five literal deck associations; every priced Printing is included in the identity selection. Totals and omitted counts preserve the difference between retained coverage and the bounded samples.

Printing selection prioritizes observed Printing UUIDs, then other UUIDs, and renders the selected sample in UUID order. Set samples use set-code order and deck samples use exact source-record identity order. The full source Card Value report is referenced by its content identity; the legacy v1-style `evidence_quality` section and duplicate observed-price history-readiness section are omitted with explicit accounting. The retained v4 historical evidence and limitations govern the supplied projection. Supplemental omission counts and sampling policy are also present in the context's truncation metadata and warnings.

Stable canonical JSON, explicit ordering, recursively immutable payloads, and content identities make identical retained inputs replay to identical bytes. The producer fails if the exact identity, source integrity, required lineage, or byte limit cannot be satisfied. It does not silently drop source references or invent evidence to fit the demonstration.

The isolated directory is [`data/review/two-card-chatgpt-demo/`](../data/review/two-card-chatgpt-demo/). It contains seven derived review artifacts:

| Artifact | Purpose |
|---|---|
| [`sol-ring.dossier.json`](../data/review/two-card-chatgpt-demo/sol-ring.dossier.json) | Sol Ring bounded evidence dossier. |
| [`counterspell.dossier.json`](../data/review/two-card-chatgpt-demo/counterspell.dossier.json) | Counterspell bounded evidence dossier. |
| [`sol-ring.reasoning-context.json`](../data/review/two-card-chatgpt-demo/sol-ring.reasoning-context.json) | Sol Ring manual handoff in the existing reasoning-context contract. |
| [`counterspell.reasoning-context.json`](../data/review/two-card-chatgpt-demo/counterspell.reasoning-context.json) | Counterspell manual handoff in the existing reasoning-context contract. |
| [`sol-ring.explanation.md`](../data/review/two-card-chatgpt-demo/sol-ring.explanation.md) | Evidence-constrained human-readable Sol Ring explanation example. |
| [`counterspell.explanation.md`](../data/review/two-card-chatgpt-demo/counterspell.explanation.md) | Evidence-constrained human-readable Counterspell explanation example. |
| [`manifest.json`](../data/review/two-card-chatgpt-demo/manifest.json) | Exact target IDs, dossier/context identities, baseline, and artifact byte counts/digests. |

From the repository root, verify retained outputs without writing:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/build_two_card_demo.py --check
```

The same command without `--check` prepares the isolated directory when it is empty or confirms identical existing artifacts. It rejects conflicting retained output rather than overwriting it. It performs no production mutation, promotion, or market admission.

## Manual reasoning handoff

Review a Card's dossier, then supply that Card's `reasoning-context.json` manually to ChatGPT. A suitable instruction is:

> Explain only the supplied Card evidence. Separate verified facts, deterministic descriptive calculations, supported interpretations, and unknown or unsupported conclusions. Preserve source identifiers, dates, market dimensions, provider-specific meanings, and omission counts. Use the supplied calculations; do not add external facts, claim current prices, merge provider signals into a score, or produce competitive, investment, or acquisition recommendations. If a claim lacks evidence, state the gap.

The retained explanation examples illustrate that boundary without executing a model. Their statements derive from the corresponding dossier and distinguish facts from calculations and interpretations. They do not claim best-in-slot status, competitive ranking, forecasts, investment value, or an acquisition decision. Unsupported rules interactions, synergy/combo judgments, inferred archetypes, global usage, and current transaction costs remain explicit gaps where evidence is absent.

## Validation and production protection

Focused regressions cover actual production-shaped promotion audits, exact Card selection, compact lineage, deterministic serialization/replay, source and snapshot bindings, source-integrity failures, omission accounting, context bounds, explanation fidelity, immutability, and compatibility with existing reasoning/Card Intelligence/Decision Intelligence boundaries. Complete hosted-style suite and CI results are recorded in this milestone's PR and final handoff report.

All existing canonical datasets, historical market observations/acquisition bytes, knowledge facts, other retained evidence, schemas, dependencies, GitHub Actions workflows, Architecture v12, and approved decisions remain protected. The seven demo artifacts are derived review outputs; they are not a parallel canonical store or newly admitted production evidence.

The Commander Collection: Black bundle merged in PR #164 remains separate and `NOT_READY_FOR_EVALUATION`. Its Product candidate is `requires_review`; six missing ordinary Card/Printing pairs remain unresolved, the token remains incomplete, and the existing Sol Ring/Command Tower CC2 Printings remain reused references. This demonstration cannot authorize candidate promotion, human READY attestation, product evaluation, or an acquisition recommendation.

No new provider, credential, acquisition, model execution, live transport, hosting, GUI, product pilot expansion, tournament evidence, deck optimization, strategic scoring, or architecture change is authorized. Competitive Intelligence remains parked; Competitive Card Intelligence and Deck Intelligence remain planned and unauthorized. Stop after this demonstration's single PR handoff for Project Manager review.
