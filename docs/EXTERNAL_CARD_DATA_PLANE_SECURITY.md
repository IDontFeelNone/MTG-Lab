# Data-plane security, privacy and permission model

**Status: Proposed threat model. No security service or runtime controls added.**

## Separate domains

| Domain | Authority/access boundary | Leakage surfaces and retention |
| --- | --- | --- |
| Public repository | Reviewed code/contracts/policies and demonstrably publishable artifacts | PRs, Git history, releases, public Actions logs/artifacts; public disclosure cannot be reversed by making a later repo private |
| Operator canonical plane | Approved game snapshot; authenticated operator deployment selects exact immutable root | Bundles, materializations, generated reports, copied source/unknown fields and AI contexts inherit data classification |
| Provider/source evidence | Independent protected access; exact source/projection manifest, terms/notice and provenance | Raw archives, URLs, receipts, parsed excerpts and acquisition logs may have different permissions from normalized records |
| Personal/user plane | User/tenant-controlled holdings, assessments/preferences/imports | Personal quantities, dates, positions, storage, crosswalks and reviews do not enter shared catalog bundles or public tests |
| Credentials/secrets | Scoped transport/review/deployment capability, outside logical content | No tokens, JWTs, cookies, session headers, signing/private keys or secret-bearing URLs in manifests, logs, PRs or uploaded artifacts |
| Temporary/staging | Bounded builder/transfer scope, never active authority | Extraction bombs, traversal, symlinks, executable hooks, leftover source bytes and interrupted builds |
| Caches/generated stores | Snapshot/config/materializer bound; read-only authority remains elsewhere | SQL dumps, indexes, embeddings, filesystem bytecode and query logs inherit sensitive classifications |
| Logs/CI artifacts | Explicit safe report projection with reviewed visibility | Names/IDs/counts/hashes can disclose information; no raw assertion/context dumps or private file contents by default |
| Backups | Separate scoped encrypted storage and retention/access policy | Backups are additional copies, not permission; user and card-source backups remain independently managed |

Two non-public domains are not one domain. Card-data transport credentials cannot
read collections. Collection processing cannot write/approve canonical releases.
Tests needing both receive separately scoped ephemeral inputs; reports bind each
revision without bundling the user's data into the shared snapshot.

## Permission gates, independent of technical access

For each field/source/component, retain evidence of permission for the intended
operation: processing; private retention of canonical values; retention of raw
source/projections; public redistribution; free/commercial service use; and export
to a specific AI/other destination. Required scope not established means blocked.
Optional excluded content has an explicit unavailable/not-retained disposition.

MTGJSON's controlled MIT layer, Scryfall's local-processing guidance, underlying
Wizards content and other upstream metrics remain distinct. Provider access,
private storage, a signed digest, an operator-provided file, an architecture merge
or a schema pass establishes none of the missing permissions. This review creates
no source-policy clearance and does not contact providers.

The existing trusted GitHub host authenticates admission under an explicit
operator/reviewer policy. Deployment/release activation requires a future,
separately reviewed host integration using those trust principles; no activation
authorization service is implemented by this review. Neither boundary accepts
the request's actor string or an `approved` flag as authority. A release signature
is trusted only if a separately configured
verified signer/host and decision scope are appropriate. Digest integrity and
authenticated authority are different. Inspection must remain read-only; admission,
release, activation and public export are separate authorized operations.

## Threats and required future controls

| Threat | Required design response |
| --- | --- |
| Altered/missing source, record or manifest | Independently expected digests, exact inventory and lineage validation; no refreshed expected hash to hide alteration |
| Malicious archive/path | Bounds before extraction; reject absolute/parent/platform paths, symlinks, duplicate normalized names, extra files and decompression bombs |
| Mutated staging/TOCTOU | Verified read-only attachment; recheck content/pre-state/authority immediately before activation or write; concurrent mismatch blocks |
| Fake approval/old receipt/rerun | Live trusted boundary checks exact operation, code, scope, plan/content/evidence/pre-state and authenticated reviewer; old receipt is not capability |
| Private data published through innocent filenames | Semantic whole-closure check of payload, source values, unknowns, provenance, checkpoints, audits, derived contexts and staged/untracked inventories |
| Fork/unreviewed CI exfiltration | No protected snapshots/credentials mounted into untrusted code; protected integration only from reviewed trusted revision/runner, including dependencies |
| Source prose/prompt injection | Parse as data; no executable hooks or instructions; context boundary excludes secrets/user fields and enforces destination policy; AI cannot authorize tool writes |
| Silent fallback/live refresh | Explicit snapshot required; no automatic provider fetch, “latest” selection, old cache/public fixture fallback or ambient-root merge |
| Cross-game/tenant contamination | Game/entity scoped references and explicit legacy profile; distinct user/catalog credentials, stores and accessors |
| Retention/use expiry | Recheck applicable use scope, revoke access/derived copies through authorized policy procedures, report replay unavailable when necessary |
| Service/provider outage | Existing permitted local attachment remains usable offline; blocked update must not replace current authority with incomplete evidence |
| Generated DB compromise | DB cannot approve facts; compare generation manifest/contract results and rebuild from retained authorized root in isolated staging |

Future activation should require expected-current identity compare-and-swap, honest
failure phase/status and preserved prior attachment. An incomplete build must not
leave a successful checkpoint or mutate the selected snapshot. Rollback plans and
operational services must be distinguished; neither is implemented here.

## CI and artifact policy

Public CI uses original fictional datasets and reviewed public-safe evidence, no
production secrets. Existing already-public historical fixtures remain interpreted
at their original versions; this review neither republishes new private content
nor declares blanket permission for legacy content. Any future restriction needs
an explicit authorized fixture/CI placement decision, preserving old assertions
and adding public synthetic equivalents, not silent skips or history repinning.

Protected integration mounts only the minimum selected snapshot/evidence scopes
to reviewed code. Disable general artifact/context dumps, scope caches to the run,
emit aggregate/redacted diagnostics and review even hashes/identities before public
export. Keep private logs/artifacts encrypted, access-controlled and retention-bound.
No raw OIDC/JWT credentials survive the execution boundary.

AI-context export is specifically gated. Size limits and provenance copying are
not permission filters. Model/provider telemetry, prompt logging and embedding
retention are distinct transfers; an operator's ability to read a dataset does
not permit those transfers. Conversation history never supplies missing canonical
facts, and model explanations cannot alter deterministic decisions or simulations.

Historical immutability describes content identity, not a promise to retain bytes
unlawfully forever. If future permission requires removing an operator copy, keep
only permissible audit metadata and accurately mark replay unavailable. No deletion,
Git purge, revocation action or legal conclusion is authorized by this review.
