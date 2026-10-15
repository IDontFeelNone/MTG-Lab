# Canonical authority options

**Status: Retained options analysis supporting accepted Decision 017.** Baseline:
`ec8fcbf97c84d24337503c81dd1c31a31e163d44`. Rankings are engineering judgments
under the project's stated open-code, provenance and conservative policy goals;
they are not legal permission verdicts or numerical performance measurements.
Option 8 is the approved v13 direction, initially using Option 3's single bundle.
The comparison describes alternatives against the original v12 audit baseline;
runtime implementation and all dataset/use permissions remain separately gated.

## Definitions and ranking

| Option | Rank | Authority model | v12 / Decision 004 | Decision 009 | Disposition |
| --- | ---: | --- | --- | --- | --- |
| O1 Public Git canonical | 6 | Current repository commit owns all production canonical bytes | Compatible today; 004 unchanged | Unchanged | Retain for historical/public-safe datasets; cannot solve unresolved public retention |
| O2 Private canonical Git | 3 | Public code commit + selected private data-repository commit | Git authority can remain, but split ownership/rebuild premises require an explicit decision clarification; not current zero-change support | Refine which repository owns approved data | Viable conservative backend where all private retention is permitted |
| O3 Immutable operator bundles | 2 | Selected validated content-addressed artifact owns production data | v13 for non-Git authority; supersede 004 dataset/rebuild clauses | Refine storage authority; preserve lifecycle | Smallest complete external-plane implementation target |
| O4 Runtime acquisition | 7 | Current providers/deployment-time reconstruction supplies data | Conflicts if live provider state replaces reviewed authority; explicit snapshot construction can reduce to O3 | Cannot bypass raw/processed approval/validation | Reject as startup/lookup authority; retain explicit upstream acquisition only |
| O5 DB/object-service authority | 8 | Editable database/service state is primary knowledge authority | v13 plus change to generated-database subordination for DB authority | Requires transactional approval/audit model | Reject editable SQL as primary truth; immutable object delivery is already O3, not this alternative |
| O6 Public core + live enrichment | 5 | Public canonical core plus separately attached richer layers | May fit v12 for genuinely optional noncanonical evidence; changing required authority needs a new decision | Layer approval and lifecycle ambiguous without effective snapshot | Reject implicit live overlays; compose permitted layers into O8 instead |
| O7 User/operator datasets | 4 | User supplies data for validated explicit local profile | Caller input is not canon; selected approved external authority needs v13/clarification | Must pass normal intake/approval | Useful input/deployment mode for O3/O8; not an authority or rights shortcut |
| O8 Effective snapshot hybrid | 1 | Public contracts + one immutable reviewed composition of permitted public/private/operator layers | v13 because final production authority need not be Git | Refine scope, retain lifecycle | Recommended target; start with O3's single bundle to minimize initial machinery |

Private Git can version source and authoring artifacts for O3/O8. An object store
can deliver immutable artifacts without becoming a mutable semantic authority.
Both are storage choices subordinate to the selected identity and approval rules.
O8 need not have a public production core: fictional fixtures can be the only
public dataset until required redistribution permissions are established.

## Complete comparison

Abbreviations: **pin** = explicit immutable revision, never “latest”; **gated** =
operation-specific permission and trusted review required. Every intelligence
column assesses future support, not current implementation or authorization.

| Criterion | O1 | O2 | O3 | O4 | O5 | O6 | O7 | O8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reproducibility | Git commit, existing fixtures | Two pinned commits | Exact retained bundle | Poor without captured/frozen outputs | Requires consistent export/transaction identity | Weak with live overlays | Varies until sealed | One effective root plus pinned members |
| Deterministic identity | Existing IDs | Preserve IDs across repos | Preserve IDs across storage | Provider drift/mapping risk | DB surrogate-key drift risk | Alias/conflict risk across layers | Validate submitted IDs | Stable IDs plus explicit scoped mappings |
| Provenance | Git evidence closure | Private history/evidence links | Immutable manifests + authorized evidence | Must capture each source/transform | Requires independent immutable audit | Cross-layer lineage required | Submission needs real source lineage | Unified complete lineage with classified evidence access |
| Replay | Public checkout for retained scope | Both authorized repositories | Code + bundle + evidence | Not from live API alone | Full consistent export plus audit | All exact layers required | Exact original submission required | Explicit code/effective root/evidence set |
| Auditability | Familiar PRs | Private PR/reviewer access | Reviewable manifests, receipts and release attestations | Network receipts do not approve data | Complex write/change audit | Ambiguous unless composition frozen | Operator history varies | Exact change set and trusted release boundary |
| Historical snapshots | Git objects/archives | Private immutable refs + retention | Retained roots and evidence | Upstream may remove history | Backups/export retention needed | Keep every old composition | User must retain originals | Immutable old roots; truthful availability status |
| CI/testing | Easy for public-safe data | Public CI cannot mount private repo | Fictional public fixtures + protected integration | Network-flaky CI | DB service/test isolation burden | Public core coverage differs from rich deployment | Fixture quality varies | Same contracts, independent safe/public and protected tiers |
| Developer experience | One clone | Optional second authorized clone | Explicit local fixture/bundle attachment | Convenient until outage/drift | Service setup/migrations | Hidden layer differences confusing | Easy local import, hard quality control | Default explicit fictional profile; optional authorized attachment |
| Deployment | Checkout is data release | Fetch both exact refs | Prevalidated immutable artifact | Startup networking/latency | Service/version coordination | Multiple layer/version coordination | Operator provisioning required | Code + root pin, explicit stage/verify/activate |
| Security | Public disclosure permanent | Scoped Git access/history copies | Bounded extraction, scoped evidence, attestations | API/SSRF/credentials at runtime | Broad writable service and backup surface | Multiple scopes/confused-deputy risk | Untrusted file input | Read-only attachment, separated builder/consumer/evidence/user scopes |
| Data leakage | Public data by design | Clones, PRs, logs, backups | Bundles, caches, logs and contexts need classification | Responses/logs/diagnostics leak | SQL dumps/query/logs leak | Rich overlay can leak through public outputs | Accidental uploads/local logs | Whole closure and export gates; hashes also reviewed |
| Provider outages | Offline retained data unaffected | Retained private data unaffected | Attached retained data unaffected | Blocks startup or changes inputs | Acquisition separated; DB service outage still blocks | Live enrichment unavailable | Retained submission unaffected | No provider dependency during consumption; update may block |
| Source-policy flexibility | Requires public retention | Supports permitted private retention | Per-component/per-operation gates | Access alone grants nothing | Storage choice grants nothing | Required core may still be uncleared | Possession grants nothing | Distinct processing/retention/export/service gates |
| Multi-game support | Existing scoped schemas | Preserve game scopes across repos | Per-game handles | Multiple provider assumptions | Must avoid global ID collisions | Per-game layer conflict rules | Validate format/game explicitly | Per-game authority handles, no rekeying |
| Rules Intelligence | Only publicly permitted rules facts | Rich permitted rules versions | Pin rules/evidence/interpretation module | Live text is not reviewed executable semantics | SQL rows do not define rules semantics | Could combine incompatible rules versions | Reject incomplete source/format | Exact rules/capability module; fail closed on missing semantics |
| Simulation | Needs validated product/slot/sheet facts | Same pinned facts privately | Snapshot/config/algorithm/seed | Live collation drift destroys replay | Transactions must pin all inputs | Mixed product/card layers risky | Caller definitions require validation | Full effective graph and collation evidence, deterministic seed |
| Collection Intelligence | Current names/exact IDs | Same IDs, private user data separate | Catalog root bound to personal snapshot | Provider drift changes resolution | Catalog/user tables must not become shared authority | Name/identity mismatches across layers | No implied physical-copy evidence | Stable IDs, explicit new audits, preserved historical bindings |
| Deck/Competitive Intelligence | Public format/usage gaps remain | Protected evidence still independently needed | Separate pinned legality/usage/context | Live rankings not canonical strategy | DB storage does not solve evidence validity | Core/enrichment assumptions may conflict | Operator metrics need evidence | Catalog + independent domain evidence/policy; not universal rankings |
| Market Intelligence | Separate temporal observations | Same separate price history | Independently pinned market observation set | Fetch explicitly, never manufacture freshness | Must separate prices from stable entities | Live price layer needs explicit as-of | Submitted offers need provenance | Catalog/mappings + time-indexed evidence and explicit as-of |
| AI reasoning | Structured permitted public contexts | Private values require export gate | Authorized projection from selected root | Never network-fill missing canonical facts | Query results need provenance/permission | Overlay text may inject/leak | Untrusted supplied text | Structured snapshot-grounded contexts; memory is never authority |
| Offline use | Good for retained scope | Good after authorized checkout | Good after explicit transfer | Poor unless complete capture retained | Depends on local export/DB | Poor if overlay remains remote | Good after validated local supply | Good with full permitted attachment and evidence closure |
| Migration complexity | Low code; unsolved rights blocker | Medium root/version-link changes | Medium-high snapshot/writer scope work | High deterministic acquisition/review redesign | Highest authority/write architecture change | High conflict/coverage accounting | Medium validation/attachment work | Staged O3 first, composition deferred until justified |
| Operational cost | Low hosting; Git corpus/history growth | Git access/storage/retention management | Artifact retention, verification and scoped access | Quotas, repeated bandwidth, outage handling | DB operations/backups/HA | Multiple feeds/caches/debugging | Support burden on operators | Artifact-based baseline; pay for optional protected modules only |
| Failure recovery | Revert/select old Git revision | Select old data + code pair | Select intact compatible allowed root | Cannot recover unavailable provider history | Restore exact export/transaction plus receipts | Restore every matching layer | Restore original retained submission | Atomic selection rollback; DB rebuild, personal audits untouched |

## Reasons for the recommendation

O8 separates code openness from data distribution without changing stable domain
identity or deterministic consumers. Composition occurs before activation and has
one effective graph, avoiding O6's two-authority problem. O3 supplies the initial
single bundle so the first milestone does not build a module marketplace, server
or generalized importer. Existing data-root injection and content-addressed raw
storage provide implementation seams; writer publication must be migrated safely.

O2 is practical where a small trusted team can lawfully retain full history and
operators can fetch a pinned private repo. It adds access/version coupling and
does not make private datasets available to public CI. Releasing an immutable
validated artifact from that repo yields the recommended runtime contract.

O7 maximizes distribution flexibility but transfers quality/retention obligations
to operators. Supported validation and explicit authority selection remain needed.
An arbitrary supplied ZIP or “approved” JSON is neither permission nor approval.

O1 remains appropriate for demonstrably public-safe fixtures or data. Existing
public history is not erased; its presence does not clear new admissions. O4 is
appropriate only as explicit controlled acquisition feeding candidates and future
sealed releases, not as automatic canonical reconstruction. O5 changes a second
Tier-0 invariant (DB subordination) with no demonstrated need. O6 is acceptable
for optional independent evidence under v12 only when it does not silently
replace required canonical facts; full rich canonical composition should use O8.

## Tradeoffs and remaining gates

- Public Git alone cannot replay protected production calculations. Public
  algorithms remain auditable; full replay requires authorized retained inputs.
- A signed digest authenticates a trusted attestation only with a configured
  verified signer/host boundary. Neither a hash nor a supplied actor string
  authenticates a reviewer or licenses data.
- Public manifests, counts and stable IDs can leak private information; publication
  needs an explicit permitted metadata projection too.
- Snapshot availability/retention and permission expiry are operational duties;
  unavailable/deleted bytes mean unavailable replay, not permission to substitute.
- Optional enrichment must not create implicit order-dependent shadowing. A new
  effective snapshot and its reviewed conflict/mapping policy are required.
- MB2 private processing/retention and source-policy questions remain blockers.
  The architecture enables a future permitted dataset; it does not supply one.
