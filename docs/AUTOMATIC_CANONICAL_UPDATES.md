# Phase 123 trusted refresh attempt

Phase 123 added an immutable, checksum-first MTGJSON snapshot registration boundary. Registration requires a caller-supplied trusted SHA-256, complete provider publication metadata, and exact retained bytes; replay is idempotent and any identity collision fails closed. The approved MTGJSON metadata, checksum, and dataset endpoints all returned HTTP 403 from this execution environment, so no refreshed bytes or evidence identity could honestly be registered and the Phase 122 gate was not run against untrusted or stale input. No descriptor, candidates, plan, execution, or canonical write was created. A future provider refresh remains the next task.

# Automatic Canonical Updates

The [implementation-only compatibility repair](CATALOG_ADMISSION_COMPATIBILITY_REPAIR.md)
supersedes the routine-approval/write descriptions below. New admission requires a
live authenticated trusted-host review decision bound to exact inputs and pre-state;
validated candidates, configuration labels and saved checkpoints cannot authorize
it. Ordinary CLI calls install no authenticator and fail closed for new writes.
The explicit GitHub entry below requires signed platform identity and live operation
bindings. Historical receipts and results below remain historical evidence,
not reusable approval. Production admission and source activation remain on hold.

## Phase 122 first-real-target availability result

The requested target was **The Hobbit**, with its code intentionally unknown until provider evidence established it. Inspection of retained trusted MTGJSON snapshot `mtgjson-allprintings-5.3.0+20260731-b47cc8360034` found exactly two set partitions, `MB2` and `MSH`, and zero set-level Hobbit matches. The immutable availability report is `data/automatic_updates/phase-122-hobbit-availability.json`. It classifies this provider snapshot as `not_yet_published_by_provider`; the repository-retained source summary and bounded payload inventory prove the snapshot's two-set scope, while the operator-managed source bytes are deliberately not retained.

The gate stopped before target selection. No set code, evidence identity, batch, candidate membership digest, production descriptor, plan, verify, execution, audit, rollback, target branch, target PR, or auto-merge request exists. Candidate counts and classifications are zero, dependency closure was not run, and both `canonical_write` and `promotion_performed` are false. Supplying a newer checksum-verified trusted MTGJSON dataset is the only intervention that can establish whether the target has become uniquely available. MB2, MSH/Marvel, other Lord-of-the-Rings products, and every unrelated set remain excluded.

> **Phase 120 · Architecture v12 compatible.** This orchestration composes existing evidence, review, promotion, query, and analytics boundaries. It changes no canonical contract or Tier 0 architecture.

## Standard lifecycle and safety

`AutomaticCanonicalUpdate` runs sixteen fixed, fail-closed stages: source acquisition verification; evidence normalization; permanent intake; exact target partitioning; bounded payload retention; complete review; policy-approved identifier/conflict resolution; dependency closure; readiness planning; deterministic preflight; atomic bounded promotion; immutable audit; post-state verification; query/analytics smoke tests; branch/PR persistence; and merge-eligibility verification. Every successful stage has a canonical-JSON digest and durable checkpoint. A failure stops later stages and retains `data/automatic_updates/<batch>/blocked-report.json`. Valid checkpoints resume; tampered checkpoints fail closed.

Promotion requires a configured trusted provider, verified hashes/inventories, exact isolation, only permitted final classifications, no unresolved/rejected/quarantined/fatal candidate, no unresolved identity conflict, valid closure and no orphan Printing, exact canonical pre-state, deterministic identities, and atomic state/audit/post-state success. Identical completed replay is idempotent; changed membership, audit, or state conflicts. Failed audit or verification restores original canonical bytes.

## Configuration and commands

Schema `automatic-canonical-update-v1` requires `game`, `target_code`, `target_name`, `trusted_provider`, `source_dataset_identity`, `source_artifact_or_workflow_run`, `evidence_identity`, `batch_identifier`, `candidate_digest`, `expected_target_isolation`, `promotion_policy`, `destination_branch`, and `base_branch`. Artifact paths, integrity expectations, trusted providers, classifications, and optional identity fields are data. A future set needs retained bounded evidence and a configuration—not engine changes.

`config/automatic_updates/mb2-first-batch.json` references completed Phase 119. Its audit makes execution an idempotent verification; it does not duplicate promotion. No second MB2 batch or MSH candidate is configured.

```bash
PYTHONPATH=src python scripts/automatic_canonical_update.py --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py plan --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py verify --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py execute --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py status --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py replay --config CONFIG
PYTHONPATH=src python scripts/automatic_canonical_update.py rollback-plan --config CONFIG
```

All output is JSON. A new write additionally requires the live trusted-host review
boundary; ordinary CLI commands do not install it. Read-only inspection/replay of exact retained
historical evidence grants no new authority. `rollback-plan` never executes
destructive work. Digests bind content and do not authenticate a reviewer.

Omitting the command runs the existing read-only `plan` operation. Explicit commands
remain supported. Configuration-loading and engine errors return a structured
`status=blocked` result with exit code 1. Approval labels in configuration and actor
names in environment variables do not install a trusted boundary. The existing plan
is an inspection result. The manual workflow now separates planning from explicit
owner authorization; exact-delta publication follows only after required validation.

Read-only planning reuses `admission_bindings()` and the existing source, payload
and target-integrity checks. `decision_inputs` records the operation/target, exact
ordered IDs and digest, counts by type, actual retained source/receipt and payload
hashes, expected integrity values, policy/construction bindings and observed
canonical pre-state. New admission previews require explicit expected source,
payload and configured receipt hash pins and a matching pre-state; planning never
fills in or rewrites those expectations. Final rereads reject changes during
verification.

`plan_id` is `sha256:` followed by the existing `digest(decision_inputs)` recipe:
UTF-8 JSON with sorted keys, separators `(',', ':')`, `ensure_ascii=False`, and no
trailing newline. It includes the configuration's actual byte hash and excludes
checkpoint progress and timestamps. Recheck a saved identity with
`plan --config CONFIG --expected-plan-id sha256:...`; changed decision-relevant
inputs block that check. This option supplies no execution authority.

Every preview reports `approval_state=not_granted`, `execution_authorized=false`
and `admission_ready=false`. Source-policy permissions and admission/readiness
review remain unresolved or unassessed; retained license receipts and provider
trust do not authenticate an approver or establish a rights decision.

Completed batches are labeled `historical_inspection` only after their existing
retained admission verification succeeds. Their original pre-state is displayed
alongside the current catalog, which may include later admissions. Historical
descriptors lacking raw-byte hash pins report `integrity_verified=false`, expose
the missing pins, and retain their separately verified source-to-record evidence.
They never become a new admission preview or refresh historical expectations.
Planning calls no execution/authorization path and writes no checkpoints or data.

## Owner-controlled manual entry and trusted boundary

This integration repairs implementation against Architecture v12; it changes no
canonical, importer or admission-decision contract. The entry points remain
`.github/workflows/automatic-canonical-update.yml` and
`scripts/automatic_canonical_update.py`. The workflow defaults to `operation=plan`.
Its separate plan job calls only the existing read-only planner; it installs no
review boundary, cannot execute the writer, and has only `contents: read`.

A later action must explicitly choose `operation=admit` and supply the exact
previously reviewed `expected_plan_id`, `reviewed_revision` (the plan's
`reviewed_code_revision`), and reviewed `config`. Recomputing with
`plan(expected_plan_id=...)` checks that old identity; it never silently substitutes
a newly generated plan. Selecting admission is the owner's explicit decision to
admit and propose that exact catalog delta as a draft data PR, subject to all gates. Neither a plan, tests,
PR merge, configuration approval field nor a saved receipt supplies that decision.

The reviewed script's policy allows only repository `IDontFeelNone/MTG-Lab`
(immutable repository ID `1314720822`), its personal owner `IDontFeelNone`
(account ID `310046194`), `refs/heads/main`, and this specific workflow.
Those IDs were read independently through the GitHub repository API on 2026-10-13.
Admission is not delegated to arbitrary collaborators or a request-supplied list.
A future delegation requires reviewed policy, not a dispatch input.

GitHub authenticates the account performing `workflow_dispatch` and supplies the
runner/event context. Its OIDC issuer signs the actor/owner/repository IDs, workflow
ref and SHA, code SHA, run ID/attempt and runner claims. The reviewed GitHub action
requests audience `mtg-lab:canonical-admission`, masks the token, and passes it
directly to the child process environment; it is never saved to a file or report.
`PyJWT[crypto]` verifies RS256 signatures using only GitHub's fixed JWKS endpoint,
issuer, audience, required claims and validity times. Environment variables are
transport and consistency checks, not reviewer authentication.

The application checks the fixed policy, branch subject (both official legacy and
immutable forms), GitHub-hosted runner, manual event, actor equals owner, exact
reviewed revision equals the signed workflow/code SHA and checkout HEAD, unchanged
tracked checkout, matching run/event/workspace and triggering actor. All reruns
(`run_attempt != 1`) are rejected: GitHub documents that reruns retain the original
actor's privileges. A new explicit dispatch is required, with fresh review if inputs
or pre-state changed. The authenticated context, plan identity, operation, code
revision and run identity are retained in `AdmissionDecision.review_reference`;
decision time is the live boundary's UTC observation of that explicit action.

The trusted computing boundary includes GitHub's issuer and event delivery, runner
isolation and credential secrecy, reviewed main code/policy, Actions and Python
dependencies. The signature proves execution context, not that arbitrary code is
safe; main review/protection and trusted dependencies remain host responsibilities.
An operator able to replace trusted code or steal its live bearer capability is
inside that boundary. This is a GitHub client integration, not an authentication
service. Ordinary `execute`/`admit` calls, forged environment claims, request JSON
and copied decisions cannot install production authority. There is no simulated
authorization switch in the CLI or workflow.

Before installing authority, and on every writer authorization callback including
the final pre-write check, the entry verifies the original plan, source/payload and
receipt checksums, policy, exact candidate order and canonical pre-state. It also
rechecks signed execution identity and reviewed configuration. Configuration names
are restricted to regular, tracked `config/automatic_updates/*.json` files with
exact reviewed bytes; absolute paths, traversal and symlinks fail closed. Workflow
inputs travel through quoted environment variables or argument arrays with
`shell: false`, never shell expressions.

Operation-specific source-policy clearance is a separate trusted-code gate:
`SOURCE_POLICY_CLEARED_PLANS` is empty. No real proposal, including the pending
810-record recommendation, is cleared or approved by this change. Adding a future
clearance requires an independently reviewed, operation-specific policy decision
backed by retained authoritative evidence; its exact plan binds that evidence.
Provider trust and receipt hashes alone never provide redistribution permission.

The admission entry calls the existing repaired writer only through
`query_and_analytics_smoke_tests`, including its actual query, collection and
projection acceptance checks. The fixed workflow then requests
`--publish-admission-pr`, using the existing `GitHubPersistence` helper. That helper
requires the live decision object from this operation; the read-only boundary CLI
and copied audit metadata cannot install it. No merge or PR approval is requested.

`admission_publication_inventory()` in `automatic_updates.py` compares the reviewed
Git base with the original canonical pre-state and reconstructs the exact selected
delta through the existing `_canonical_record()` adapter. Every existing record and
other canonical byte must be preserved. Current state, the original planning inputs,
receipt and live decision must agree; a permitted state filename cannot conceal an
unrelated edit. The explicit inventory binds raw hashes/Git blobs for state, audit,
all fourteen successful writer checkpoints, configuration, payload and every
configured source/receipt dependency. Existing dependencies remain bound to the
base; newly required dependencies are staged with the actual catalog delta.

Tracked, staged, untracked and ignored files are inspected before staging. Extra
files, symlinks, path escapes, incompatible index modes and staged alternate bytes
block publication. The sole known recovery backup is checked against original base
bytes and remains local and unstaged; all other temporary/private artifacts are
rejected. Credential/JWT/private-field checks apply to retained publication bytes
and diagnostics. Raw tokens, headers and signing keys are never artifacts. Safe
actor/run/decision metadata records history; it is not a reusable authenticator.

Before committing, the helper runs the actual required unittest suite, strips the
OIDC and GitHub credentials from its child environment, retains safe validation
diagnostics under `.git`, and rechecks the entire inventory and remote refs. A moved
main, unexpected branch or unrelated local head blocks. Only explicitly inventoried
files are staged; a dedicated `canonical-update/` branch has one parent equal to the
reviewed base. No reset, direct main push or force-push is used. Push status is
captured and independently read back, even after an ambiguous response. A draft PR
is created or an exact matching open draft reused. Git refs, PR head/base/draft,
commit parent/tree and complete remote changed-file list must match. Readback cannot
claim completeness at the GitHub compare API's 300-file limit. Failures report their
phase and preserve local work; this is not a new rollback service.

Planning retains `contents: read`. The admission job's `contents: write` and
`pull-requests: write` are used only for its branch and draft PR; `id-token: write`
requests identity, not repository-write access. No new token, external service or
Actions permission was added to manufacture CI success. Under current GitHub
documentation, GITHUB_TOKEN-created pushes do not trigger push workflows; PR opened,
synchronize and reopened events can create approval-required workflow runs. A user
with write access can select **Approve workflows to run** if that banner appears.
This is distinct from admission approval or merge permission. Hosted CI may be
pending, approval-required, successful or failed; publication success implies none
of those outcomes. A repository setting that disallows Actions-created PRs will
block creation, not silently trigger a broader credential or automatic setting change.

Offline tests use fictional retained inputs, the actual writer and required
consumer/suite validation, local bare Git, and explicitly simulated platform
responses. Simulated decisions can publish only to the disposable capability's
local bare remote using a transport double. They cannot publish to GitHub. These
tests do not establish live authorization or publication of a real catalog update.

`config/automatic_updates/mb2-ordinary-810-pending.json` binds the retained ordered
810-ID digest, 270 records of each type, nine held IDs and all 32 retained packet
files. It is explicitly pending and the CLI blocks it. The reviewed data-root
candidate payload with parsed contexts, and source/receipt retention paths, have not
been materialized as production inputs. Their missing paths/hashes are explicit;
the rehearsal's simulated payload is not relabeled for real admission. Private
processing, public redistribution, future application-use policy and an actual
human decision remain separate gates. No held record, spelling proposal, Japanese
language evidence, emblem semantics or physical-copy identity changes here.

`requirements.txt` adds only `PyJWT[crypto]>=2.10,<3`: PyJWT verifies GitHub JWT
claims and its cryptography extra verifies RS256 signatures. No unrelated dependency
upgrade, custom signing implementation or authentication service is introduced.
The combined implementation still requires the full final local suite, exact-head
hosted validation and independent Project Manager review before owner merge approval.

Current official GitHub references (read 2026-10-13):

- [OIDC claims, token-request permission and immutable subjects](https://docs.github.com/en/actions/reference/security/oidc)
- [Manual workflow dispatch and access](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Rerun actor privileges](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
- [Safe workflow input handling](https://docs.github.com/en/actions/reference/security/secure-use)
- [Current workflow-token event behavior](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)

Failure before authorization writes no engine checkpoint. Later failures retain
truthful engine diagnostics and evidence; the repaired writer's bounded compensation
remains authoritative. `rollback-plan` is a nonexecuting plan, not a rollback service.

## Phase 121 synthetic production-readiness result

The retained fixture `tests/fixtures/phase_121_synthetic/` describes synthetic Magic set
`SYN` under the same `automatic-canonical-update-v1` contract and engine used by the MB2
reference. Its deterministic eight-candidate order is: one Set identity, two Cards, two
Printings, one Identifier, and foil/nonfoil Finishes. Every candidate has an exact synthetic
source locator; null release date and oracle text are paired with explicit unknown-state
fields. Both Printings close over retained Cards. The trusted provider, evidence and dataset
identities, source/payload hashes, exact inventory, identity fields, policy, and deterministic
branch are configuration data. Tests copy the fixture to a temporary root; synthetic bytes,
audits, checkpoints, and promoted state never enter production `data/`.

All stages returned `succeeded`, in registry order: (1) source authenticated and trusted;
(2) eight ordered candidates and payload checksum verified; (3) evidence retained; (4) exact
`SYN` partition confirmed; (5) bounded payload authenticated; (6) eight of eight reviewed and
approved; (7) deterministic identifier policy found zero unresolved conflicts; (8) zero
orphan Printings; (9) readiness true; (10) empty isolated pre-state matched; (11) eight
entities promoted atomically; (12) audit digest verified; (13) post-state digest
`47abe0658ad434f6485148592559a973a6f8f14694455a89cb0cb29b5b8e9327` verified; (14) isolated
entity counts were 2 Cards, 2 Printings, 1 Identifier, 2 Finishes, and 1 Set; (15) deterministic
branch/PR plan emitted; and (16) protected auto-merge policy emitted.

An interruption after stage eight resumed without changing completed checkpoint bytes. A
completed replay made no canonical change; altered batch/audit/state replay failed closed.
The rollback command emitted a non-executing, human-decision-required plan retaining the
audit. `plan`, `verify`, `execute`, `status`, `replay`, and `rollback-plan` all returned stable
JSON identities. Deterministic tests reject untrusted provider, contamination, missing or
duplicate inventory, unresolved/quarantined review, conflicting identity, orphan Printing,
payload checksum mismatch, pre-state drift, checkpoint/audit alteration, interrupted and
conflicting replay, mismatched PRs, non-green checks, and any force/admin path.

The engine source contains neither `MB2` nor `MSH`; no target-code/name condition was added.
The former Phase 121 workflow's publication and auto-merge behavior is historical;
the owner-controlled integration above supersedes it. Original retained evidence and
historical hashes remain unchanged. Real admission still requires source-policy
clearance, exact owner authorization, completed publication safeguards and independent
review; this implementation task grants none of those production decisions.
