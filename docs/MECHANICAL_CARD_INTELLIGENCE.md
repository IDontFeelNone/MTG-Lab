> **Merged status:** GitHub PR #166 is merged at `e4a99ae6ccffe3e7121337fe28d9127024be3743`. The mechanical v1 projection and all retained artifacts below remain unchanged. A separately bounded [functional-role review pilot](FUNCTIONAL_ROLE_CARD_INTELLIGENCE.md) adds pending interpretations for fifteen Cards; it does not turn this literal projection into a classifier or admit roles as facts. The original milestone specification and stop boundary below retain their historical context.

# Mechanical Card Intelligence — production cohort foundation

Canonical main verified on 2026-10-12: `c8941c568fb275a735ab6902e3663947f21760ee`, the merge of GitHub PR #165. Architecture v12 remains frozen. This is a named milestone, not a new numbered project phase. PR numbers and phase numbers remain independent.

## Implemented scope

`MechanicalCardIntelligence` in `src/card_intelligence/mechanics.py` composes existing public canonical queries with one retained, verified Scryfall acquisition. It produces read-only, immutable `mechanical-card-dossier-v1` outputs and a descriptive `mechanical-card-cohort-v1` report. It does not append knowledge facts, enrich canonical records, promote candidates, admit market observations, or implement a rules engine.

The current production cohort is independently verified as **384 Cards**. The query facade also exposes 15 typed seed Cards; these are excluded by the admitted `card_reference` identity binding. Dossier requests require an exact production Card ID. Names, seed IDs, and ambiguous source bindings never silently select a Card or provider record.

The existing Card Value v1–v4 reports remain separate, with their ten-Card pilot boundary. PR #165's seven Sol Ring/Counterspell artifacts are preserved byte-for-byte. No query, semantic, reasoning-context, canonical-schema, or Decision Intelligence contract is changed.

## Source and identity reconciliation

The sole input is the already retained acquisition `scryfall-mb2-30754638264-1`:

- Source file: `data/market/acquisitions/scryfall-mb2-30754638264-1/source-mb2.json`.
- Retained subset: 2,278,127 bytes; SHA-256 `c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47`.
- Provider dataset: `scryfall-default-cards`; recorded source locator `scryfall:default_cards`.
- Source timestamp: `2026-08-02T09:09:45.851000Z`; retrieval timestamp: `2026-08-02T15:34:06Z`.
- Upstream full-bulk digest: `03a2c4e4eace87db24fcab615def32445ef4c82129cae6fc5cda7edaf6cb688f`. Original bulk bytes are not retained; this is an acquisition assertion, distinct from verification of the retained subset.

The loader verifies the existing acquisition manifest's own serialization/digest, every retained file's byte count/digest, retained UTC timestamps, and agreement with its dry-run report. The acquisition's original canonical snapshot identity and normalized-source digest are preserved separately from the current canonical query snapshot. Each dossier also binds its provider Printing UUID, exact Oracle UUID, actual source-row index, entire-record content identity, canonical evidence references, and compact digest-bound promotion audit references. No source identity or observation timestamp is invented.

| Boundary | Verified count |
|---|---:|
| Retained source rows | 385 |
| Canonical production Cards | 384 |
| Uniquely mapped source rows / Cards | 384 / 384 |
| Missing or ambiguous Card mappings | 0 / 0 |
| Excluded source rows | 1 |
| Canonical source Printings matched | 379 |
| Mapped Cards without the retained source's canonical Printing | 5 |

Mapping is exact `oracle_id` → admitted canonical `card_reference`, with no name fallback. **Essence of Ajani**, provider UUID `7d5329a8-b3bd-498d-98c0-ba8b11ff7ddd`, Oracle UUID `115e3d3a-1625-4cb7-b988-6addcbac6713`, is an emblem-layout source record without a canonical production Card. It stays excluded; no identity is created.

The five Cards without a canonical source Printing are Liliana's Other Contract // Liliana's Undead Minion; Keeper of the Crown // Coronation of the Wilds; Plant a Sapling // Fully-Grown Treefolk; There // They're // Their; and Value Town // Take a Trip to.... Their Card mappings and source face relationships are supported; this does not establish Printing admission or complete MB2 membership.

## Fields and interpretation boundary

Dossiers retain source fields with `known`, `unknown`, or `unresolved` status, source JSON pointers, and exact values. Missing and explicit-null values have distinct reasons. Known empty strings/lists remain known; an empty mana-cost field is not called an unknown, a zero cost, or a free spell. Provider mana value (`cmc`) is encoded as an exact decimal string, without calculating it from symbols or face costs.

Oracle text is retained verbatim. Printed text and printed type line remain separate unknown fields when absent; Oracle text never substitutes for printed text. Provider colors, color identity, keywords, produced mana, power, toughness, loyalty, defense, and color indicators retain their distinct meanings. Symbolic characteristics such as `*` are not converted into numeric values.

Type labels are a deterministic split of the literal type line using an explicit type/supertype vocabulary and the provider's separators. Subtype tokens remain literal labels. **Summon Licid** and **Poly Artifact** stay unresolved: `Summon`/`Licid` and `Poly` are not silently converted into modern types. The literal `Artifact` label remains attributable. This token projection does not validate game legality, castability, functional roles, or rules interactions.

All five multi-faced Cards retain the provider's face order: four have two faces and There // They're // Their has three. There are **11 explicit face objects**. Face IDs, mana values, colors, color identities, and keywords are never invented or inherited from the parent. Root metadata and face fields remain separate, including apparently different root mana cost/value representations on adventure and split Cards. The report also records 44 Cards with canonical/provider field differences; independent provider values remain visible and canonical records stay unchanged.

| Field coverage | Card-root denominator: 384 | Explicit-face denominator: 11 |
|---|---:|---:|
| Oracle text | 379 known, 5 absent | 11 known |
| Mana cost | 382 known, 2 absent; 42 known empty | 11 known |
| Mana value | 384 known | 0 known, 11 absent |
| Colors | 382 known, 2 absent | 4 known, 7 absent |
| Color identity | 384 known | 0 known, 11 absent |
| Keywords | 384 known; 259 known empty | 0 known, 11 absent |
| Type line | 384 known | 11 known |
| Printed text / printed type line | 0 known | 0 known |

Every Card has Oracle text for all its represented source components. That is source coverage, not current official-rules verification. Absent power/toughness/loyalty/defense fields are unknown rather than inferred to be inapplicable. Nonmechanical provider fields are omitted with explicit field counts; the whole source record remains digest-bound. No artwork or full provider corpus is copied into the derived outputs.

## Cohort descriptive findings

Card distributions use **384 canonical Cards**, not 385 source rows or 390 represented source components. Type/supertype memberships union represented faces and count each Card once per label; overlapping categories need not sum to 384. This is literal represented-face membership, not a rules claim about which face's characteristics apply. Mana-value, color-identity, and keyword distributions use root provider metadata; missing values are counted separately and face keywords are not inferred.

- Type memberships: Creature 147; Artifact 53; Instant 52; Enchantment 48; Sorcery 48; Land 41; Planeswalker 13; Conspiracy 2; Kindred 1. Fully classified type labels: 382 Cards; unresolved: 2.
- Mana values 0–10 have counts 56, 65, 80, 71, 56, 29, 17, 5, 3, 1, 1 respectively, totaling 384. These are provider metadata, not cast-cost or power estimates.
- Color identity: 68 colorless, 261 monocolor, 55 multicolor; the complete literal combinations are retained in the report.
- Keyword presence includes Flying on 15 Cards; Enchant and Flash on 8 each; Trample on 7. Counts are once per Card per provider label, not ability prevalence, roles, or competitive strength.

This is **canonical-cohort analysis**, never complete-set analysis. A retained `set=mb2` subset and a bounded canonical promotion do not establish complete official set membership.

## Read-only use and replay

```bash
PYTHONPATH=src python -m card_intelligence.cli mechanical --card-id 6ad8011d-3471-4369-9d68-b264cc027487
PYTHONPATH=src python -m card_intelligence.cli mechanical-cohort
PYTHONPATH=src python -m card_intelligence.cli mechanical --card-id 150be0e9-a65f-4209-bdea-8cf4c691d217 --reasoning-context
PYTHONDONTWRITEBYTECODE=1 python scripts/build_mechanical_cohort.py --check
```

[`data/review/mechanical-card-cohort/`](../data/review/mechanical-card-cohort/) contains all 384 dossiers in canonical-ID-ordered `dossiers.jsonl`, `cohort-report.json`, four standalone examples, four existing-contract manual reasoning contexts, and a digest/identity manifest: **11 derived artifacts**. Examples cover Sol Ring, Counterspell, Liliana's Other Contract, and the three-faced There // They're // Their. The generation script writes only this isolated directory and rejects conflicting existing artifacts. `--check` performs no writes.

Each dossier and individual handoff context has a 65,536-byte bound. Handoffs use the existing `ReasoningContextResult` contract with an explicitly labeled supplemental mechanical projection and `analytics_snapshot_id=null`; the generic semantic-only Reasoning Context Builder is unchanged. Canonical and source references, content identities, limits, and omissions remain in the handoff. A manual consumer may explain these supplied facts/calculations while preserving unknowns. No model, live ChatGPT transport, or application is executed.

## Unsupported dimensions and stop boundary

Functional-role classification, structured ability classification, verified rules interactions, combo/synergy correctness, best-in-slot or substitute rankings, competitive power, deck optimization, complete-set membership, and price/acquisition decisions remain explicitly unsupported. Keywords and superficial Oracle-text matches do not authorize these conclusions. The existing ten-Card pilot's knowledge facts and provider demand/market evidence remain separate and unchanged.

Tests cover production identity/source reconciliation, literal field pointers, face-aware missing values, nonstandard labels, correct denominators, deterministic serialization/replay, source integrity failures, ambiguous/missing mappings, immutable payloads, existing Card Intelligence/two-Card compatibility, and protected-data non-mutation. Complete suite and hosted checks are recorded in the milestone PR. All existing canonical, market, knowledge, historical evidence, schemas, dependencies, workflows, Architecture v12 and approved decisions remain protected.

Stop for Project Manager review of this PR and its evidence. No promotion, provider acquisition, human READY attestation, functional-role milestone, Deck Intelligence, Competitive Intelligence, or follow-on implementation is automatic.
