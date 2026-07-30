# MTG Lab Constitution

> **Tier: Tier 0 (Project Constitution)**  
> **Status: Approved** — Phase 83, 2026-07-30  
> **Architecture:** v12 (unchanged)

## Purpose and authority

This Constitution records the enduring laws behind MTG Lab. It governs architecture,
data, research, implementation, and AI-assisted work. It is read with
[`ARCHITECTURE.md`](ARCHITECTURE.md), [`DECISIONS.md`](DECISIONS.md),
[`DATA_MODEL.md`](DATA_MODEL.md), and [`DATA_REPOSITORY.md`](DATA_REPOSITORY.md).
Those documents explain the approved structure and contracts; this document states the
principles that future structures and contracts must preserve.

If guidance conflicts, contributors must preserve these laws, stop rather than invent a
resolution, and seek an explicit constitutional or architectural decision. Current-state
documents report progress but cannot override Tier 0 guidance.

## Foundational laws

### 1. The canonical repository is the single source of truth

Version-controlled, reviewed canonical records are authoritative. Databases, indexes,
caches, APIs, reports, simulations, and model context are projections or consumers.
They may improve access, never establish competing authority. Chat history and external
providers are not project state.

### 2. Unknown is preferable to incorrect

Absence, uncertainty, disagreement, and incomplete coverage must be represented honestly.
No feature deadline, user expectation, or plausible inference justifies presenting an
unsupported value as fact. Consumers must distinguish known, partial, conflicting, and
unknown information.

### 3. Every canonical fact must be evidence-backed

A canonical assertion requires identifiable evidence, an explicit transformation path,
applicable validation, and reviewed promotion. Schema validity alone is insufficient.
Confidence or provider reputation cannot substitute for evidence.

### 4. Raw provider data is immutable

Acquired bytes and their content identity are preserved without revision. Corrections
produce new snapshots and lineage; they do not rewrite history. Licensing and access
constraints may restrict storage or redistribution but never justify silent mutation.

### 5. Normalization does not create truth

Normalization maps syntax, identifiers, and shapes. It may expose omissions or conflicts,
but it cannot resolve them by convenience, infer canonical authority, or erase unmapped
source values. Normalized records remain evidence-derived candidates until reviewed.

### 6. AI reasons over the repository; it is not the repository

AI may retrieve, compare, explain, and propose conclusions from repository facts. Model
memory, generated text, embeddings, and prompts are not canonical evidence. AI output must
identify its inputs, uncertainty, and reasoning boundary, and must never self-promote a
claim.

### 7. Simulation must fail closed

Simulation is permitted only when every outcome-affecting input required by its declared
model is validated and eligible. Missing topology, pools, weights, replacement semantics,
conditional rules, or correlations must stop the simulation or explicitly narrow its
claim; they must never receive convenient defaults.

### 8. Every promoted fact must be traceable to evidence

Lineage must connect a promoted field or assertion to immutable evidence, source identity,
transformation, review decision, and promotion audit. Traceability must survive contract
migration and persistence changes.

### 9. Architectural changes must preserve explainability

New storage, automation, intelligence, and scale mechanisms must retain deterministic
inputs, explicit decisions, versioned contracts, audit history, and understandable failure
states. Performance and convenience do not justify opaque authority or irreproducible
results.

### 10. Product-specific logic belongs in data, not code

Generic engines interpret versioned product definitions. A product name, release, set,
treatment, or game must not introduce special-case engine branches. When the current data
model cannot express a supported fact, propose a product-agnostic contract change rather
than embedding an exception.

### 11. Derived knowledge never silently becomes source fact

Analytics, decisions, probabilities, market summaries, research synthesis, and AI
conclusions are derived artifacts. They record versions and input lineage and remain
separate from observed or canonical facts unless an explicit evidence-backed promotion
process authorizes a suitable assertion.

### 12. Validation and promotion are explicit boundaries

Acquisition, parsing, normalization, review, promotion, consumption, and derivation are
separate stages. Success at one stage does not imply success at the next. Boundary failures
must be visible, deterministic where practicable, and safe to retry.

### 13. History is preserved

Raw evidence, audits, accepted decisions, superseded contracts, and dated research remain
available according to retention policy. Corrections supersede; they do not conceal. The
project must be able to explain what it knew, why it acted, and which version governed.

### 14. Human accountability remains final

Automation may enforce gates and prepare proposals. Maintainers approve architectural
change, canonical promotion, releases, and merges. Tools and passing tests provide evidence
of quality but do not grant authority by themselves.

## Applying the Constitution

Every milestone should state which constitutional laws it relies on, whether it changes a
Tier 0 contract, and how evidence, uncertainty, lineage, and failure are handled. Design
reviews should reject solutions that introduce parallel truth, implicit promotion, opaque
reasoning, or product-specific engine behavior. When laws appear in tension, choose the
more conservative truth claim and document the unresolved question.

## Constitutional amendments

An amendment is exceptional and must not be smuggled into a feature or refactor. A proposal
must:

1. identify the law and exact wording to add, change, or supersede;
2. describe the problem using repository evidence and concrete scenarios;
3. explain effects on Architecture v12, authority, provenance, uncertainty, compatibility,
   and existing canonical data;
4. list alternatives, migration needs, risks, and irreversible consequences;
5. update or add an accepted decision record and all affected Tier 0 cross-references;
6. receive explicit maintainer approval in a dedicated, reviewable milestone; and
7. preserve the former text or amendment history rather than silently rewriting rationale.

The amendment record must include date, approval, motivation, affected laws and documents,
compatibility disposition, and validation performed. Until approval and merge, the existing
Constitution remains controlling. Phase 83 creates institutional memory only and does not
amend Architecture v12 or any canonical schema.
