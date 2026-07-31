# Phase 102 — Representative Corpus Validation

> **Status:** Complete — 2026-07-31  
> **Architecture:** v12 unchanged  
> **Change class:** validation corpus, integration tests, and documentation only

## 1. Pre-implementation architecture assessment

The merged Phase 101 baseline (`d7b1ef3`) is present. Phase 101 concluded that MTG Lab is
a pre-alpha reference platform with a beta-ready architectural shape, strong fail-closed
governance and deterministic contracts, but unproven large-corpus behavior and overlapping
generations of acquisition, repository, and persistence abstractions. It identified no
critical architectural defect and recommended representative-corpus validation before
large-scale population.

Architecture v12 remains unchanged. The Canonical Repository remains the sole source of
truth; the Multi-Source Evidence Acquisition Framework remains the only acquisition path;
acquisition never promotes; and canonical promotion still requires completed validation
and an explicit decision by an independent reviewer. Phase 102 adds no provider, network,
schema, canonical contract, simulation, model execution, or product-specific behavior.

## 2. Deterministic corpus design

The test-only JSON corpus contains two Cards and three Printings across `set-one` and
`set-two`. It includes common and mythic rarity, English and Japanese language, foil and
nonfoil finishes, one Card with multiple Printings, and a deliberately null artist. The
test derives a contradictory assertion, a malformed review package, and a revised Card
version rather than storing ambiguous duplicate fixtures. This keeps the positive corpus
small while exercising conflict, validation-failure, supersession, and rollback paths.

| Concern | Corpus/test representation |
| --- | --- |
| Multiple sets/cards/printings | Two sets, two Cards, three Printings |
| Rarity/finish/language | common/mythic; foil/nonfoil; en/ja |
| Unknown value | null artist, explicitly reviewed before promotion |
| Conflicting evidence | deterministic contradictory assertion; promotion fails closed |
| Validation failure | duplicate assertion in a tampered review package |
| Review required | package initially reports `hold`; explicit independent decision required |
| Supersession | revised Card name creates a second promotion and replacement link |
| Rollback | second promotion is rolled back and state replay is verified |

The fixture is immutable test evidence, not canonical data and not a sample claimed to be
representative of MTG card frequency.

## 3. Validation methodology and exercised subsystems

The integration test executes the governed path: offline reference fixture provider →
content-addressed raw evidence → deterministic normalization and assertions → validation
and review package → explicit independent review decision → promotion candidate →
Canonical Promotion Engine → canonical state → Query → Canonical Analytics → Semantic
Query → Reasoning Context → a serialized `AIModelRequest`. No AI provider is registered
or invoked.

Assertions at the transitions cover snapshot and normalized identifiers, byte preservation,
dataset identity, raw and assertion provenance, validation and conflict state, confidence,
unknown lifecycle state, review-package identity, promotion idempotence, query snapshot
identity, analytics snapshot linkage, semantic identity, reasoning-context identity, and
AI request serialization. Two independent acquisitions preserve byte-identical raw payloads
and identical content-derived record identifiers. Repeated promotion, query, analytics,
semantic, reasoning, and request operations are deterministic.

Negative-path validation proves that conflicting or malformed candidates cannot mutate
canonical state. Supersession and rollback prove current-state replacement, immutable
history, replay, and compensation safety under the documented single-writer assumption.

## 4. Results and limitations

The representative path succeeds end to end and all repository unittest tests pass. The
corpus demonstrates subsystem composition without importing a complete MTGJSON dataset.

Known limitations remain:

- this is five entities, not a performance, concurrency, interruption, or memory benchmark;
- raw acquisition manifests intentionally contain storage paths, so byte identity applies
  to retained source payloads and content identities, not relocatable manifests;
- Phase 85 generic promotion stores assertion paths such as `/name`; identifier lookup and
  downstream envelopes work, but name/set filters and field-specific analytics expect the
  typed canonical projection. This confirms Phase 101's provider-to-canonical handoff and
  repository-boundary gap; the test does not disguise it by changing contracts;
- conflict evidence is synthesized deterministically from the corpus rather than acquired
  from a second real provider;
- rollback is validated for the filesystem single-writer model, not concurrent processes;
- no model, SDK, networking, simulation, or product-specific runtime is exercised.

## 5. Readiness assessment

The platform is **ready for a bounded, local MTGJSON import rehearsal through pending
review and for small, explicitly mapped, independently reviewed promotion batches**. It is
**not yet ready for an unattended full MTGJSON canonical import**. Before that step, the
project should approve the provider-candidate-to-typed-canonical mapping boundary, retain
compatibility fixtures for the `/field` projection, measure complete-corpus time/memory and
storage, test interruption/resume and quarantine behavior, and define generation/concurrency
guards. Full import must remain non-promoting until each batch passes validation and
independent review.

No defect found by this milestone requires an Architecture v12 amendment or Project
Architect approval. The observed handoff limitation is the already-recorded implementation
gap, and the safe response is a separately authorized mapping/scale milestone rather than
architectural redesign.
