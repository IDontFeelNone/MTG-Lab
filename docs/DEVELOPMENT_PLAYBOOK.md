# Development Playbook

## Purpose

This playbook provides repeatable implementation patterns for common MTG Lab development tasks. It complements the system structure in `ARCHITECTURE.md`, accepted decisions in `DECISIONS.md`, governance in `AI_CONTRIBUTING.md`, session procedure in `CODEX_WORKFLOW.md`, and general rules in `ENGINEERING_STANDARDS.md` without replacing them.

Consult `docs/LESSONS_LEARNED.md` for the historical engineering context behind patterns that emerged from significant implementation and debugging experience.

Domain hypotheses, experiments, observations, and conclusions belong in the Research Log defined by `docs/RESEARCH_LOG_ARCHITECTURE.md`, not in engineering lessons or session-state documents.

Contributors must follow higher-priority architecture, decision, governance, and engineering documents when guidance conflicts. Stop and request explicit approval rather than improvising an architectural change.

## Core Implementation Principles

- Keep generic systems product-agnostic.
- Represent product behavior through structured data.
- Preserve evidence and provenance.
- Prefer deterministic behavior.
- Validate at system boundaries.
- Keep domain models explicit.
- Separate acquisition, parsing, normalization, validation, promotion, persistence, simulation, analytics, and presentation.
- Keep changes focused and reviewable.
- Add tests with every behavior change.
- Update repository state documents when implementation changes project status.

## Adding a New Module

1. Confirm its architectural layer, placement, owner, and single responsibility.
2. Define small public interfaces before internal implementation.
3. Direct dependencies toward stable lower layers and avoid circular imports.
4. Add configuration only when behavior genuinely varies; provide explicit defaults.
5. Define domain-specific errors that callers can handle without parsing messages.
6. Add focused unit tests and integration tests at module boundaries.
7. Update relevant technical documentation and `PROJECT_INVENTORY.md`.
8. Run the complete test suite and milestone-specific validation.

A typical module contains an explicit public entry point, focused domain or service code, domain-specific errors, and colocated test coverage under `tests/`. Do not create placeholder layers or duplicate an existing module's responsibility.

## Adding or Changing a Domain Model

- Define the model's purpose, owning layer, lifecycle, and authoritative source.
- Prefer typed, explicit fields over unstructured containers when the contract is known.
- Preserve immutability where it protects evidence or intermediate results.
- Define stable identifiers and ID-based relationships.
- Establish construction, structural, referential, and domain validation rules.
- Keep serialization explicit at JSON boundaries.
- Do not leak ORM, database-session, or transport details into domain logic.
- Add equality, serialization, validation, round-trip where applicable, and edge-case tests.
- Treat schema changes as intentional contract changes requiring documentation and review.

Immutable tuple-backed collections may serialize to JSON lists. Serialized output must not alias nested mutable dictionaries or lists held by frozen models. Optional fields must be included, omitted, or represented as `null` consistently with their schema.

## Adding or Changing a Database Model

- Confirm alignment with the raw, processed, canonical, and validated data lifecycle.
- Define primary keys, foreign keys, uniqueness and check constraints, and query-driven indexes.
- Keep SQLAlchemy persistence models separate from domain concerns where layer boundaries require it.
- Add or update migrations and make them reversible when feasible.
- Test fresh database creation and supported upgrade paths.
- Avoid product-specific columns in generic tables; represent product behavior through related data.
- Update schema and architecture documentation when persistence contracts change.

## Adding a Schema or Data Contract

- Version schemas explicitly.
- Define required and optional fields precisely.
- Define enums, formats, collection constraints, and numeric bounds.
- Reject unknown fields or invalid states where appropriate.
- Add representative valid fixtures and focused invalid fixtures.
- Validate documents produced by application code against the schema.
- Preserve backward compatibility unless a breaking change is explicitly approved.
- Document migration and compatibility expectations.

## Adding an Acquisition Source

- Register the source through the source registry.
- Define acquisition targets through structured data or manifests.
- Preserve acquired raw evidence exactly.
- Record source metadata, acquisition timestamps, content types, and cryptographic hashes.
- Keep network access separate from parsing.
- Support deterministic, fixture-based tests without live network dependencies.
- Never silently overwrite or mutate stored evidence.
- Document licensing, provenance, reliability, and known source limitations.

## Adding a Parser

- Convert raw evidence into parsed-record artifacts only.
- Do not normalize entities or perform canonical promotion.
- Preserve source locations and excerpts needed to audit extracted fields.
- Emit structured, actionable errors and warnings.
- Keep parsing deterministic and free of network access.
- Test malformed, partial, duplicate, empty, and unexpected input.
- Validate every produced parsed artifact against its versioned schema.

## Adding a Normalizer

- Convert parsed records into normalized candidates only.
- Never silently discard provenance.
- Record field-level source provenance and named transformation versions.
- Preserve confidence and candidate validation state.
- Leave canonical data unchanged.
- Test alternate source representations, missing fields, conflicts, and partial results.
- Validate every normalized-candidate artifact against its versioned schema.

## Adding Validation Rules

- Make validation explicit, composable, and independently testable.
- Separate structural, referential, domain, and statistical validation.
- Return actionable errors and warnings with relevant identifiers or paths.
- Do not silently correct data unless an approved, documented normalization rule owns that behavior.
- Add positive, negative, and boundary tests.
- Ensure validation runs before canonical promotion or analytical consumption.

## Adding Canonical Promotion

Canonical promotion is controlled and intentionally unavailable unless current repository state explicitly says otherwise. When approved and implemented, it requires:

- An explicit human or approved automated approval workflow.
- Complete provenance preservation.
- Documented conflict-resolution rules.
- Idempotent repeated operation.
- An auditable decision history.
- Rejection and rollback paths.
- Tests proving invalid or unreviewed candidates cannot bypass validation.

## Adding a Product Definition

- Represent product behavior in structured data.
- Reuse generic product, pack, slot, sheet, and probability abstractions.
- Never add product-name conditionals to generic engines.
- Define source metadata and validation evidence.
- Add product-specific fixtures for generic behavior.
- Update product inventory and relevant documentation.
- Validate the complete definition before simulation or analytics use.

## Adding a Pack Slot or Print Sheet

- Define the slot's purpose and selection behavior.
- Reference sheet or pool identifiers through data.
- Document rarity, treatment, finish, replacement, and dependency rules.
- Keep probabilities normalized and explicitly explain approved exceptions.
- Preserve evidence for inferred collation rules.
- Add deterministic tests and statistically justified validation where appropriate.
- Clearly distinguish confirmed source data from inferred models.

## Adding Simulation Behavior

- Accept or record a random seed.
- Keep random-number generation injectable or otherwise controlled.
- Avoid product-specific branches; interpret validated product data.
- Validate input product definitions before execution.
- Produce reproducible outputs for identical inputs and versions.
- Add deterministic unit tests.
- Add statistical tests only with justified sample sizes and tolerances.
- Record product, repository or data version, simulator version, seed, timestamp, and configuration needed for reproduction.

## Adding Analytics

- Operate only on validated inputs.
- Separate raw facts from derived metrics.
- Document formulas, assumptions, units, and rounding.
- Make time windows and price or observation sources explicit.
- Preserve reproducibility through versioned inputs and configuration.
- Test known examples and boundary cases.
- Never present inferred values as confirmed facts.

## Adding Market or Price Data

- Record source, timestamp, currency, condition, finish, and marketplace context.
- Preserve historical observations rather than overwriting them.
- Normalize only through explicit, versioned rules.
- Keep vendor-specific acquisition logic outside generic analytics.
- Document stale-data handling and freshness expectations.
- Test missing, conflicting, duplicate, and outlier observations.

## Adding an API Endpoint

- Keep transport logic thin.
- Call application or domain services rather than embedding business rules.
- Validate inputs and serialize outputs explicitly.
- Use stable, documented error contracts.
- Do not expose internal persistence representations.
- Add request, response, authorization where applicable, and failure-path tests.
- Update API documentation and examples.

## Adding an AI Capability

- Retrieve or operate on grounded, validated repository data.
- Distinguish facts, calculations, assumptions, and inference in output.
- Never use conversational memory as canonical data.
- Preserve citations or provenance references where applicable.
- Keep deterministic calculations and analytics outside the language model.
- Add evaluation cases for correctness, grounding, and unsupported claims.

## Testing Patterns

- **Unit tests:** Isolate domain rules, transformations, errors, and boundary behavior.
- **Schema validation tests:** Exercise valid output plus invalid types, states, bounds, and references.
- **Integration tests:** Verify contracts between repository layers and external boundaries.
- **Migration tests:** Verify fresh creation, upgrades, data preservation, and feasible rollback.
- **Deterministic simulation tests:** Assert identical seeded inputs produce identical results.
- **Statistical validation tests:** Use justified samples, tolerances, and failure thresholds.
- **Regression tests:** Reproduce a reported defect and prevent recurrence.
- **Fixture-based acquisition and parsing tests:** Preserve representative bytes and avoid live network dependence.

Every bug fix should include a regression test when practical. Tests must prove behavior rather than merely execute code.

## Documentation Update Matrix

| Change Type | Documents to Review |
| --- | --- |
| Architecture change | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `PROJECT_INVENTORY.md` |
| New milestone | `docs/ROADMAP.md`, `docs/SESSION_STATE.md`, `docs/NEXT_TASK.md`, `docs/HANDOFF.md` |
| New module | `PROJECT_INVENTORY.md`, `README.md`, relevant technical documentation |
| Schema change | Schema documentation, `docs/DECISIONS.md` if architectural, `CHANGELOG.md` |
| Completed task | `docs/SESSION_STATE.md`, `docs/HANDOFF.md`, `PROJECT_INVENTORY.md`, `CHANGELOG.md` |
| Workflow change | `docs/AI_CONTRIBUTING.md`, `docs/CODEX_WORKFLOW.md`, `docs/DEVELOPMENT_PLAYBOOK.md` |

## Pull Request Checklist

- [ ] Scope matches the approved task.
- [ ] Architecture and accepted decisions were followed.
- [ ] No unrelated files changed.
- [ ] Tests were added or updated for behavior changes.
- [ ] The complete test suite passes.
- [ ] Schemas and fixtures validate.
- [ ] Documentation is current.
- [ ] `docs/SESSION_STATE.md` is current.
- [ ] `docs/HANDOFF.md` is refreshed.
- [ ] `docs/NEXT_TASK.md` still reflects the approved next objective or was updated with approval.
- [ ] The PR description explains motivation, changes, testing, and risks.

## Anti-Patterns

- Product-specific conditionals in generic engines.
- Parsing and network acquisition in the same component.
- Promoting unvalidated candidates.
- Losing or weakening provenance.
- Silent schema changes.
- Hidden nondeterminism.
- Mutable shared serialization output.
- Business logic inside API handlers.
- Using chat history as project state.
- Large unrelated rewrites.
- Skipping documentation because a change appears small.

## Definition of Done

A task is complete only when:

- The implementation satisfies its acceptance criteria.
- All required tests and validation pass.
- Documentation is updated.
- Repository state documents are current.
- The focused change is committed.
- The PR is ready for review.
- The contributor stops and waits for approval.
