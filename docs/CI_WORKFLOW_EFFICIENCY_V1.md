# CI Workflow Efficiency V1

The `Python validation` workflow retains its single `test` check and both full
commands. This changes CI routing only; no analytical engine, canonical data,
source-use permission, activation, architecture or merge authority changes.

## Distinct guarantees and redundant runs

Full discovery validates the checked-out repository. The publication integration
then builds an actual disposable 654-Card writer-expanded catalog and runs the
complete suite **again in that different state**, before publishing to a local
bare remote and verifying readback. This nested suite remains necessary and is
unchanged. Its simulated platform grants no live GitHub or production authority.

Previously every branch push, PR merge-ref update and main push ran both commands.
Only a successful PR merge-tree run can now substitute for an ordinary main
repeat. A branch-head pass alone never qualifies.

| Event | Before | Now |
| --- | --- | --- |
| Ordinary branch push | Full discovery + writer/nested gate | No automatic run; opening/updating a PR runs the full gate |
| Any PR | Full discovery + writer/nested gate | Both commands, unchanged, on GitHub's proposed merge checkout |
| Ordinary single main merge with exact prior evidence | Both commands again | Read-only tree/ancestry/evidence verification |
| Direct, batched, squash/rebase or unexpected main history | Both commands | Both commands |
| Missing, expired, failed, pending, inaccessible or inconsistent evidence | Both commands | Both commands |
| High-risk main changes | Both commands | Both commands even when tree-equivalent |
| Tag push or manual dispatch | Both commands | Both commands |

## Evidence required to reuse a PR result

`scripts/ci_merge_tree.py` starts with `full=true`. Only a push of a single
two-parent merge to main can select reuse. Its first parent must equal the push
event's `before`; the checked-out commit must equal the event's `after` and
`GITHUB_SHA`. The associated merged PR must bind that merge, base and head.

The verifier reads the latest PR-triggered run of this exact workflow for the
head. It requires successful completion, all workflow jobs successful, the
original `test` job, and successful execution (not skipping) of both discovery
and publication steps **before the PR merged**. It reads that job's GitHub-hosted
log and validates the original discovery summary, real writer receipt, nested
count/log-hash consistency and matching publication/readback identities.

The log must contain one actual checkout identity. GitHub's commit object for
that checkout must have the current main tree and the exact ordered base/head
parents. The current PR merge ref, a caller receipt, a branch push, a rounded
metric, a successful older run masking a newer failure, and an arbitrary cache
cannot substitute. Comparing the complete tree also binds workflow, helper,
dependency requirements, tests and source bytes. This trusts reviewed repository
code and GitHub's authenticated run/job/log records, as existing CI does; it is
not protection against a maintainer deliberately rewriting the test commands.

The finite API reader permits at most six requests and 4 MiB per response, with
20-second socket timeouts and a three-minute scope-step limit. Storage redirects
must use approved HTTPS host families and receive no API Authorization header.
Failures select full validation; unexpected verifier termination fails the job
rather than silently skipping validation. Logs retained beyond GitHub's retention
period may require full validation. A versioned decision and its evidence appear
in the job log and step summary; reused counts are explicitly historical evidence,
not a claim that tests ran again on main.

## High-risk and deliberate full validation

Existing CI/scripts, canonical data/reviews, canonical import, ingestion,
production-evidence, repository persistence, acquisition, canonical schema and retained
source-evidence path boundaries conservatively force full post-merge validation.
Permission, authorization, policy, admission, migration, recovery, rollback,
persistence, snapshot, publication and release path names do likewise. Approved
architecture, decisions and governance documents are explicitly included. This
is a small CI safeguard, not a new semantic or admission classification.
Adding a portable analytical-file schema alone is not a canonical migration.

All PRs receive full validation regardless of paths. For release preparation or
any risk not represented by a filename, deliberately run **Python validation →
Run workflow → main** (or `gh workflow run python-validation.yml --ref main`).
Manual dispatch always runs both full commands; it has no skip option. Tags also
retain full validation. Direct pushes cannot borrow another commit's success.
No publication, recovery or rollback implementation/gate is weakened.

## Protection, deployment and owner decisions

At the verified base `59ccc66952e6683eb8558651e6c949b583112060`, GitHub's branch
endpoint reported `protected=false`, enforcement off and no required contexts;
the ruleset list was empty. The dedicated protection endpoint was inaccessible
(403), so its detailed settings could not be independently inspected. The
workflow's existing `test` check name remains unchanged. **Passing CI does not
enforce review or prevent an owner from merging early.**

No branch settings are changed. The Owner should independently inspect settings
and, if desired, separately authorize requiring the existing `test` check and
an up-to-date reviewed base. That is an Owner configuration action, not an
assumed prerequisite silently completed by this PR. Missing pre-merge evidence
still forces the main workflow's complete fallback, even without protection.

All other workflows remain byte-identical. The six acquisition/intake/automatic
update workflows are manually dispatched; none depends on `workflow_run` or a
branch-push validation event. Their publication/admission gates remain unchanged.
There is no new deployment, release, approval or automatic merge path. Merge
queues are not configured; adding one would require reviewing its event needs.

Historical workflow bytes and their original pins are retained through one exact
reversible successor adapter. Unknown edits, changed ledgers, modes and symlinks
remain rejected; no historical baseline or evidence hash is rebaselined.
