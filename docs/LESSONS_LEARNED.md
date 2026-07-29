# Lessons Learned

## Purpose

This document captures reusable engineering knowledge discovered while developing MTG Lab. It is neither a changelog nor a bug tracker. Each lesson records what was learned, why it matters, how it changed the project, and how future contributors should apply it.

## Lesson 1 — Repository as the Source of Truth

### Context

Development may move between conversations, AI agents, tools, and human contributors.

### What Happened

Important project state initially depended on temporary conversational context that was not guaranteed to be available to the next contributor.

### Root Cause

Chat history is temporary and tool-specific, while repository documentation is durable, versioned, and reviewable.

### Resolution

MTG Lab established `PROJECT_INVENTORY.md`, `docs/SESSION_STATE.md`, `docs/NEXT_TASK.md`, `docs/HANDOFF.md`, and `docs/AI_CONTRIBUTING.md` as repository-owned sources for capability, status, approved work, immediate transfer, and governance.

### Engineering Principle

**Repository state should always outlive conversations.**

### Guidance for Future Contributors

Read and reconcile repository documents at the start of every session. Never use previous conversations as authoritative project state, and update the appropriate state documents before handing work to another contributor.

## Lesson 2 — Architecture Before Implementation

### Context

MTG Lab requires several interoperating layers and must support multiple products without embedding product assumptions in generic systems.

### What Happened

Freezing Architecture v12 before expanding implementation clarified system boundaries and made incremental development substantially simpler.

### Root Cause

Implementation started from stable responsibilities and data flows instead of redefining structure during every feature. Architectural drift would have multiplied coupling and rework.

### Resolution

Approved architecture and decisions take precedence over implementation convenience. Work is divided into small milestones that fit the established layers.

### Engineering Principle

**Stabilize architecture before scaling implementation.**

### Guidance for Future Contributors

Place new work within approved Architecture v12. Prefer a focused implementation change over redesign, and obtain explicit approval before changing architectural boundaries.

## Lesson 3 — Explicit Serialization Boundaries

### Context

Candidate artifacts use frozen dataclasses and tuple-backed collections internally but must produce JSON- and schema-compatible documents externally.

### What Happened

Generic dataclass serialization preserved tuples where JSON-style lists were expected. A later review also found that shallow mapping copies allowed serialized nested dictionaries and lists to alias data retained by frozen models.

### Root Cause

Internal domain representation and external JSON representation have different contracts. Treating serialization as a mechanical reflection of the model obscured required type conversion, ownership, enum, and optional-field rules.

### Resolution

Candidate artifacts gained explicit serializers that convert tuple collections to lists, invoke nested serializers, deep-copy arbitrary mutable JSON-like values, emit enum values, and omit optional fields when required by schema.

### Engineering Principle

**Serialization is a translation boundary, not the domain model.**

### Guidance for Future Contributors

Keep immutable tuple-backed models immutable. At JSON boundaries, intentionally translate types, prevent mutable aliasing, and follow the schema's required, optional, and nullability rules. Add schema and non-aliasing regression tests.

## Lesson 4 — Evidence Preservation

### Context

External collectible-card data may be incomplete, contradictory, revised, or inferred from observed products.

### What Happened

The project separated acquisition, parsing, normalization, validation, canonical promotion, and persistence so each transformation remains inspectable.

### Root Cause

Combining these responsibilities would overwrite source context, obscure transformations, and make canonical facts difficult to audit or correct.

### Resolution

Raw evidence remains immutable; parsed records retain source context; normalized candidates retain field provenance; validation precedes controlled promotion; persistence does not become the canonical authority.

### Engineering Principle

**Never lose provenance.**

### Guidance for Future Contributors

Preserve original bytes, hashes, source metadata, locations, excerpts, transformation identifiers, and approval history. Do not collapse pipeline stages or promote data that cannot be traced to evidence.

## Lesson 5 — Small Pull Requests

### Context

Repository changes must be understandable to maintainers and reversible when assumptions prove incorrect.

### What Happened

Focused milestone work produced easier reviews, more targeted testing, faster debugging, and safer rollback than broad feature branches.

### Root Cause

Large changes mix decisions and failure modes, making it difficult to identify which behavior caused a regression or whether unrelated edits are safe.

### Resolution

The repository workflow now limits work to one approved milestone and requires focused diffs and reviewable commits.

### Engineering Principle

**Prefer many small PRs over large feature branches.**

### Guidance for Future Contributors

Keep each PR aligned with one objective and its acceptance criteria. Exclude unrelated refactors, formatting, dependencies, or follow-on milestones.

## Lesson 6 — Documentation Is Part of the Product

### Context

MTG Lab's architecture, data provenance, workflow, and milestone state cannot be inferred reliably from code alone.

### What Happened

Documentation-first development reduced ambiguity, but documentation that lagged implementation created stale instructions and uncertain handoffs.

### Root Cause

Treating documentation as an afterthought separates design intent and current state from the implementation contributors actually encounter.

### Resolution

Documentation updates are included in the same task as relevant implementation and are checked before a PR is ready for review.

### Engineering Principle

**Code and documentation should remain synchronized.**

### Guidance for Future Contributors

Use the documentation update matrix in the development playbook. Update technical contracts, inventory, session state, handoff, next task, roadmap, decisions, and changelog wherever the scope requires.

## Lesson 7 — AI Works Best With Structured Knowledge

### Context

MTG Lab aims to provide explainable AI-assisted decision intelligence over collectible-card data.

### What Happened

The architecture intentionally separated the repository, generated database or persistence layer, deterministic analytics, and AI reasoning.

### Root Cause

Language-model memory and free-form responses are not suitable canonical stores for versioned facts or reproducible calculations.

### Resolution

AI capabilities retrieve grounded repository knowledge and consume validated analytical outputs. Deterministic calculations remain outside the language model, and facts and inferences remain distinguishable.

### Engineering Principle

**Ground AI in structured knowledge.**

### Guidance for Future Contributors

Use validated repository data, explicit provenance, and reproducible analytics as AI inputs. Do not treat conversational memory as data, and evaluate outputs for grounding and unsupported claims.

## Lesson 8 — Regression Tests Preserve Progress

### Context

Correct behavior can regress when implementation details change, even if the original fix appeared small.

### What Happened

Candidate-artifact serialization bugs revealed both JSON type mismatches and nested mutable aliasing. Focused regression tests made the intended boundary behavior executable and durable.

### Root Cause

A fix without a test leaves the failure mode undocumented in executable form and permits later changes to reintroduce it unnoticed.

### Resolution

The project requires meaningful bug fixes to include focused regression tests when practical, alongside the complete existing suite.

### Engineering Principle

**Prevent recurring bugs rather than repeatedly fixing them.**

### Guidance for Future Contributors

First reproduce the defect in a test, then implement the smallest correction. Test the root cause, boundary conditions, and relevant contract rather than only the observed symptom.

## Lesson 9 — Separate Engineering Knowledge from Domain Knowledge

### Context

MTG Lab must preserve both knowledge about building the platform and knowledge discovered through collectible-card research.

### What Happened

Repository governance introduced engineering lessons at the same time the platform recognized domain research as a first-class architectural subsystem.

### Root Cause

Engineering practices and domain findings have different evidence, review, versioning, search, and lifecycle requirements. Combining them would turn engineering documentation into a research notebook and make domain conclusions difficult to query or reproduce.

### Resolution

`docs/LESSONS_LEARNED.md` records reusable architectural, implementation, testing, and debugging insight. The Research Log defined by `docs/RESEARCH_LOG_ARCHITECTURE.md` records domain questions, hypotheses, experiments, datasets, observations, conclusions, findings, and evidence.

### Engineering Principle

**Separate knowledge about building the system from knowledge discovered by the system.**

### Guidance for Future Contributors

Record engineering reasoning here only when it improves future technical decisions. Record collectible-card research in the Research Log with reproducible methods and traceable evidence. Cross-reference the two when an engineering constraint affects research, but do not collapse their distinct governance or lifecycles.

## Future Lessons

Append a lesson when a significant architectural, implementation, testing, or debugging insight would improve future engineering decisions. Use the same context, event, root cause, resolution, principle, and guidance structure.

Do not record routine bug fixes, task summaries, release notes, or unresolved work here. Use `CHANGELOG.md` for notable historical changes, issue tracking for defects, and repository state documents for current work. A lesson belongs here only when it captures reusable reasoning that helps future contributors avoid mistakes or choose better patterns.
