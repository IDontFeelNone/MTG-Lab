# Incremental migration and CI/deployment model

**Status: Proposed sequence; each implementation scope needs approval.** No phase
number is assigned and no step is executed by this documentation PR. Architecture
v12 remains active until the owner accepts the prospective v13 authority decision.

## Stages with acceptance and rollback

| Stage | Scope | Compatibility boundary | Required tests | Rollback | Acceptance |
| --- | --- | --- | --- | --- | --- |
| 1 Architecture decision | Accept/revise/reject Decision 017 and implementation scope | Preserve historical 004/009; explicitly authorize future authority model | Decision/document consistency and Tier-0 rationale | Leave v12 active if not accepted | Owner decision recorded separately from any dataset permission/admission |
| 2 Snapshot contract | Review manifest, identity, provenance, permission/authority and capability contracts; fictional fixtures only | No production schema/identity changes; distinguish content/report/release/query IDs | Canonical hash determinism, tampering, path escapes, extra/missing files, scope, dependency/cycle failures | Keep docs/fixtures; no production effect | Independent inspection and production-ineligible fixture validation agree |
| 3 Minimal attachment seam | Read-only verified handle through current injected-root readers; explicit fixture selection | Existing query envelope unchanged; no runtime acquisition, importer or second store | Fictional game, absent/corrupt/unsupported snapshot, root relocation, no ambient fallback | Retain legacy reader route explicitly | All required authority/compatibility gates precede consumer construction; no hidden default catalog |
| 4 Legacy public snapshot profile | Inventory current typed/promoted/knowledge/audit generations; attach in place where permitted, without copying/reformatting historical bytes | Preserve old IDs, query hashes, source projections and audit scope; source-policy review remains separate | Original historical replay unchanged; old/current calculations distinct; missing source disclosed | Existing public checkout remains interpretable | Old dossiers/audits still reject wrong snapshot; exact graph and source bindings survive |
| 5 Query/projection/collection consumers | Pass explicit attachment/evidence accessors; separate catalog and personal stores | No physical-copy upgrade, name placeholder, Identifier loss or fabricated v3 lifecycle | Actual relationships/aliases, game scope, name requirements, consumer output and historical Finish/materialization gaps | Select original compatible reader/handle explicitly | Writer/consumer validity distinguished from typed materializability and content coverage |
| 6 Intelligence/context adapters | Bind Card/Product/Market/Decision/reasoning input versions | Preserve existing mechanical source format initially; domain ownership and deterministic policy unchanged | Missing/unsupported/corrupt evidence, ABSTAIN, cross-snapshot/as-of conflict, export omission and non-leaking context | Prior explicit profile/attachment retained | No consumer invents prices/rules or fills from memory/network; contexts respect destination scope |
| 7 Existing writer release destination | Separately reviewed protected staging and immutable snapshot release/activation adapter using existing writer/review boundary | Do not bypass repository-root checks or repurpose public publisher; old approvals not portable live authority | Fictional actual-writer end-to-end: pending/rejected/forged/stale decisions, evidence/prestate changes, exact delta, closure, failure restore, concurrency, idempotency | Failed pre-activation build retains previous active root and recovery bytes | Required consumers validate actual writer output; no successful checkpoint/activation for incomplete operation; no public private-data PR |
| 8 Protected integration/deployment | Optional real snapshot only after processing/private-retention/evidence/use permissions and owner admission approval | Code+snapshot+policy selected atomically; no fork/unreviewed code receives credentials | Trusted-code protected suite, offline operation, invalid/missing/expired scope, backup/rollback drill and leak checks | Explicit intact compatible still-permitted prior snapshot | Real authority and permission evidence verified; safe diagnostic/report boundaries operational |
| 9 Generated SQL persistence | Implement approved Decision 010 direction only when performance/use requires it | Snapshot remains authoritative; DB/index output subordinate | Logical row/query/dependency parity, dialect/ordering/Decimal behavior, cache-key mismatch, rebuild and corruption | Use read-only snapshot reader or rebuild approved older generation | DB can be discarded/rebuilt from retained authorized inputs; no ORM fact authority |
| 10 Optional composition and future domains | Pin permitted core/enrichment modules into one effective root; separately authorize Rules/Deck/Competitive/Simulation/AI work | No live overlay authority, implicit precedence or expanded capability claim | Member conflict/identity/dependency and permission intersection, feature-specific deterministic tests | Previous complete effective root | New domain semantics/evidence independently approved, pinned and complete enough for requested operation |
| 11 MB2 readiness revisit | Reuse exact retained 810 recommendation and nine holds under actual established permission scopes | No changed identities, Japanese replacement, owner spelling confirmation or physical assignment inferred | Real production-format artifact checks, actual isolated writer, private audit new calculation, source/closure/privacy checks | Leave existing catalog and completed personal audit untouched | New owner-reviewed plan and later explicit admission decision; architecture acceptance alone never clears MB2 |

SQL generation comes after reader/consumer parity, not before, because there is
no current SQLAlchemy production runtime to migrate. Composition and rich rules
modules are deferred beyond the first single-snapshot attachment scope.

## Public CI tier

- Run schemas, transformations, identity/relationship, query, projection, decision,
  domain-completeness and deterministic tests with original fictional datasets.
  Keep variable cohort sizes and a second fictional game to expose hardcoding.
- Verify snapshots/examples without network or private production data. Include
  tampering, scope/authorization failures, absent optional evidence, path attacks,
  incompatible code/schema/policy and no-fallback cases.
- Retain historical public fixtures and their exact assertions at their original
  snapshot scope; do not apply their census to an expanded current catalog.
  Their continued permitted distribution needs its own policy assessment, not a
  blanket inference from prior publication. This review changes no existing fixture.
- Public contributors need no production credentials. CI output publishes only
  safe fictional data/contract results; no rich source corpus, protected contexts,
  personal audit, signing secrets or auth headers.
- Deterministic fixture generation pins template/generator/version/configuration;
  publication of a fixture never declares any real provider dataset approved.

If a future policy decision requires restricting an old fixture, retain its hashes,
expected behavior and lawful authorized replay placement; add public fictional
equivalent contract coverage. Do not silently remove failures, repin old expected
hashes or expose private production data to restore a public test.

## Protected production-integration CI tier

- Run only reviewed trusted code/dependencies on scoped protected runners. No
  fork PR or arbitrary caller script receives production mounts or credentials.
- Select exact approved snapshot, source evidence and permitted operations.
  Personal integration inputs are separately scoped synthetic or expressly
  authorized private fixtures; the catalog secret is not the collection secret.
- Run complete relevant schema/graph/provenance/admission/query/collection/
  intelligence integration and actual writer/activation recovery checks.
  An unsupported domain/source remains unsupported; never fabricate fixture facts.
- Keep data, logs, DBs, contexts and caches private/retention-bound. Emit only
  reviewed contentless/aggregate conclusions publicly, tied to reviewed code
  and permitted identity metadata. No general public artifact upload.
- Report tested code/snapshot/check-profile identities, exit status, failures,
  setup errors and unrun checks separately. Protected success does not license
  redistribution or authenticate an owner decision by itself.

## Deployment flows

| Mode | Explicit flow | Failure behavior |
| --- | --- | --- |
| Public developer checkout | Install public code, choose fictional fixture profile, verify and attach, run query/domain tests; original dataset not required for meaningful core coverage | Missing fixture is a blocked requested operation, not silent production selection |
| Optional operator dataset | Supply manifest/bytes through supported explicit acquisition/intake, establish permission/scope, validate dependencies and trusted admission, seal and select | Caller-supplied or incomplete material stays noncanonical; untrusted/forbidden required fields block |
| Production | Pin reviewed code/configuration; transfer exact authorized release; verify authority/permissions/compatibility; run consumer acceptance; stage DB if required; atomically activate | Preserve active allowed snapshot on failed update; no public seed/live provider fallback |
| Offline operation | Attach locally retained permitted complete snapshot/evidence with exact requested as-of/config/seed | Missing required bytes or invalid use scope returns blocked/replay-unavailable; no network demand hidden in queries |
| Snapshot update | Explicit acquisition → candidates → review/permission → actual writer → validate → seal → compare-and-swap expected current root | Concurrent/stale bindings or unsupported new scope block; no automatic reassessment/physical assignment |
| Rollback | Explicitly select intact, compatible, still-permitted old root and matching cache/rebuild; bind new operations to chosen root | Incompatible code/schema/expired permission means rollback unavailable; old personal audits remain unchanged |

Production result identity includes code revision, snapshot/query IDs, schema/
policy/transform/engine versions, configuration and source manifests, independent
market/user/rules inputs, and PRNG algorithm/version/seed when applicable. A fresh
render timestamp is display metadata, not silently a new analytical input.

## First bounded implementation proposal

After owner approval of Decision 017: implement only manifest verification and
explicit read-only attachment of a fictional snapshot through existing query/
collection roots, plus absent/corrupt/incompatible/no-fallback regressions. Preserve
all canonical bytes and existing public behavior with an explicit legacy profile.
No SQL, real provider acquisition, new writer destination, AI transport, actual
MB2 artifact construction or private production admission is included in that
first proposed implementation scope. It is not authorized by this design PR.
