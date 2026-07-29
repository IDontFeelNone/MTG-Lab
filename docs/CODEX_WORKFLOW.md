# Codex Workflow

## Purpose

Define the standard operating procedure for every Codex development session. The repository is the only source of truth; previous chat history is never an implementation dependency.

## 1. Establish Repository State

At the start of every session, read:

1. `PROJECT_INVENTORY.md`
2. `docs/AI_CONTRIBUTING.md`
3. `docs/HANDOFF.md`
4. `docs/DEVELOPMENT_PLAYBOOK.md`
5. `docs/SESSION_STATE.md`
6. `docs/NEXT_TASK.md`
7. `docs/ARCHITECTURE.md`
8. `docs/DECISIONS.md`
9. `docs/ROADMAP.md`
10. `CHANGELOG.md`

Then verify the current branch, recent commits, remotes, and working-tree status. Resolve discrepancies using repository content and current Git state, not conversational memory.

## 2. Confirm Scope

- Apply the governance, document priority, and collaboration rules in `docs/AI_CONTRIBUTING.md` before implementation begins.
- Consult `docs/DEVELOPMENT_PLAYBOOK.md` for the approved implementation pattern relevant to the task.
- Before major implementation work, consult `docs/LESSONS_LEARNED.md` for relevant historical engineering context.
- Treat the repository as the only source of truth.
- Never rely on previous chat history.
- Never redesign approved architecture without explicit approval.
- Work on one approved milestone at a time.
- Confirm the objective, acceptance criteria, constraints, and expected files in `docs/NEXT_TASK.md`.
- Stop and request clarification when repository instructions conflict or the milestone is not sufficiently defined.

## 3. Implement

- Keep changes small, focused, and reviewable.
- Follow `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and engineering standards.
- Avoid unrelated refactoring, formatting, or documentation churn.
- Add focused unit, integration, and regression coverage as appropriate.
- Update documentation whenever implementation changes project behavior or status.

## 4. Validate

- Run the complete test suite.
- Run all milestone-specific schema, data, lint, or documentation validation.
- Run `git diff --check`.
- Review the complete diff and confirm that it contains only milestone-related changes.

## 5. Record State

- Update `PROJECT_INVENTORY.md` with completed and remaining work.
- Update `docs/SESSION_STATE.md` with the new repository state.
- Update `docs/NEXT_TASK.md` to the next approved milestone or mark it as awaiting approval.
- Replace stale session-specific content in `docs/HANDOFF.md` with a concise account of the work just completed, validation, repository state, and immediate next action.
- Update `docs/ROADMAP.md` and `CHANGELOG.md` when their status changes.
- Ensure these documents agree before committing.

## 6. Deliver

- Commit the focused change with an accurate message.
- Confirm `docs/HANDOFF.md` is current before opening or updating the PR.
- Open a new PR or update the existing PR for the milestone.
- Include scope, rationale, and exact validation commands in the PR description.
- Stop after the PR is ready for review. Do not begin another milestone, merge the PR, or make post-PR changes without a new instruction.
