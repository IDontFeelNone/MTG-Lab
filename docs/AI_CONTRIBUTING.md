# AI Contributing Guide

## Purpose

MTG Lab is intentionally developed through repository-driven collaboration. Repository documentation—not chat history—defines the project state, approved architecture, current milestone, and next action. This guide is the authoritative operating and governance guide for AI agents and human contributors working together on the project.

For reusable implementation patterns within this governance model, consult `docs/DEVELOPMENT_PLAYBOOK.md`. The playbook is subordinate to the document priority below and does not authorize architectural changes.

## Document Priority

If repository documents appear to conflict, use this order of authority:

1. `docs/ARCHITECTURE.md`
2. `docs/DECISIONS.md`
3. `docs/AI_CONTRIBUTING.md`
4. `PROJECT_INVENTORY.md`
5. `docs/SESSION_STATE.md`
6. `docs/NEXT_TASK.md`
7. `docs/HANDOFF.md`
8. `CHANGELOG.md`
9. `README.md`

Higher-priority documents always take precedence. A lower-priority document may summarize or operationalize a higher-priority document, but it must not override it. Contributors should stop and request maintainer clarification when a conflict cannot be resolved from this order.

## Project Philosophy

- The repository is the canonical source of truth.
- Documentation is part of the product and changes with the implementation.
- Architecture stability is more important than implementation speed.
- Every change and result should be reproducible.
- AI augments engineering discipline; it does not replace review, evidence, or accountability.
- Small, reviewable changes are preferred over large rewrites.
- Validated evidence is preferred over assumptions.
- Generic systems remain independent of individual game products.

## Contributor Roles

| Contributor | Responsibility |
| --- | --- |
| Human Maintainer | Owns vision, approvals, architecture decisions, release decisions, and final merges. |
| ChatGPT | Supports architecture, planning, project management, design review, and technical review. |
| Codex | Implements approved work, adds tests, updates documentation, validates changes, commits, and prepares pull requests. |
| GitHub | Provides source control, review history, issue and pull-request collaboration, and the canonical shared repository. |
| GitHub Actions | Runs continuous integration and automated validation for proposed changes. |

Tools do not grant approval by themselves. Human maintainers retain final authority over architecture and merges.

## Standard Development Workflow

Every contributor should:

1. Read, in the priority order above where applicable:
   - `PROJECT_INVENTORY.md`
   - `docs/SESSION_STATE.md`
   - `docs/HANDOFF.md`
   - `docs/NEXT_TASK.md`
   - `docs/ARCHITECTURE.md`
   - `docs/DECISIONS.md`
   - `docs/ROADMAP.md`
   - `CHANGELOG.md`
2. Understand the current milestone, its acceptance criteria, and its constraints.
3. Implement one approved milestone.
4. Keep changes focused and reviewable.
5. Update affected documentation and repository state documents.
6. Run the complete test suite and all milestone-specific validation.
7. Commit the reviewed changes with an accurate message.
8. Update the milestone's existing PR or create one when none exists.
9. Stop and wait for review; do not begin the next milestone.

## Engineering Rules

- Never rely on previous conversations as project state.
- Never redesign approved architecture without explicit maintainer approval.
- Never bypass validation or consume unvalidated canonical data.
- Never merge directly to `main`.
- Never skip tests required by the repository or milestone.
- Never silently change schemas; document, validate, and review schema changes explicitly.
- Never introduce product-specific logic into generic systems.
- Keep commits small, coherent, and reviewable.
- Prefer deterministic, reproducible implementations.
- Preserve evidence, provenance, and auditability.
- Update documentation whenever implementation behavior or project state changes.
- Record significant reusable architectural, implementation, testing, or debugging insights in `docs/LESSONS_LEARNED.md`; do not use it for routine fixes or release notes.
- Keep engineering knowledge in `docs/LESSONS_LEARNED.md` and domain research in the Research Log defined by `docs/RESEARCH_LOG_ARCHITECTURE.md`; do not mix their purposes.
- Avoid unrelated refactoring, formatting, or dependency changes.
- Before implementing a milestone that introduces a new subsystem, verify that
  a corresponding approved Tier 0 architecture document exists. If none
  exists, stop and recommend an architecture/documentation milestone before
  implementation.

## Documentation Responsibilities

| Document | Role | Update responsibility |
| --- | --- | --- |
| `README.md` | Public project purpose, capabilities, and contributor entry points. | Update when the project-level description or workflow entry points change. |
| `PROJECT_INVENTORY.md` | Canonical inventory of implemented and remaining capabilities. | Update when milestone completion changes repository capability. |
| `docs/SESSION_STATE.md` | Ongoing version, phase, focus, risks, debt, and milestone state. | Update at the end of work that changes ongoing project state. |
| `docs/NEXT_TASK.md` | Single approved next milestone, constraints, tests, and definition of done. | Update when a milestone completes or maintainer approval changes the next task. |
| `docs/HANDOFF.md` | Concise immediate transfer from the most recent session. | Replace stale session details at the end of every implementation or documentation task. |
| `CHANGELOG.md` | Historical record of notable user- or project-visible changes. | Add entries when notable changes are prepared; never use it as live session state. |
| `docs/ARCHITECTURE.md` | Approved structural design and system boundaries. | Change only through explicit architectural approval. |
| `docs/DECISIONS.md` | Accepted architectural and engineering decisions with rationale. | Add or supersede decisions through explicit approval; do not silently rewrite history. |

## Pull Request Requirements

Every pull request should include:

- Motivation.
- Summary of the focused change.
- Exact testing and validation performed, including results.
- Files changed.
- Documentation updates, or an explanation of why none were required.

The PR title and description must accurately describe the reviewed diff. Update an existing milestone PR rather than opening a duplicate.

## Quality Gates

Before a pull request is ready for review:

- The complete test suite passes.
- Milestone-specific validation passes.
- Documentation is accurate and updated.
- Repository state documents are current and mutually consistent.
- No unrelated files are modified.
- The full diff has been reviewed.
- Approved architecture is unchanged unless explicit approval accompanies the change.
- The branch is committed and the working tree is clean.

## Long-Term Vision

MTG Lab is intended to become a self-documenting software project in which repository documentation enables any future AI agent or human contributor to understand the system, continue approved development, reproduce results, and prepare reviewable work without relying on chat history.
