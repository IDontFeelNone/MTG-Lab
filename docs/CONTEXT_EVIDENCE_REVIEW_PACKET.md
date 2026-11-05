# Coffers / Wastes context-evidence review packet v1

This read-only workflow organizes **owner-submitted, unverified contextual
claims for independent human review**. It does not authenticate sources, grant
permissions, analyze a deck, establish strategic advantage, or execute gameplay.
No reviewer event is assumed or automatically issued. There is no approval API.

Canonical base: `2ea55791a8267c4c6f178c921fa6f1ddebc27b9f`; tree
`d8d0f79430fc29f0321f313adc56be33c03566e1`. GitHub main and merged PR #226
were independently checked. Its ordered parents are
`a57ff99b68696a91eb5e33b26c9e66eb86de70d8` and reviewed head
`d63dd4c0d37be557852582efc619b59728fa6d6e`. The clean reviewed tree was
reconciled with the exact signed canonical commit before creating
`codex/context-evidence-review-packet`. Architecture v13 ACTIVE APPROVED,
Decision 017 ACCEPTED, and repository-first governance remain binding. No
AGENTS.md was present in the repository or its workspace/root ancestors.

The owning references remain unchanged:
[approved integration design](design/rules-card-intelligence-v1/README.md),
[six-land overlay](SIX_LAND_EVIDENCE_OVERLAY.md), and
[strategic requirements](STRATEGIC_CONTEXT_REQUIREMENTS.md).

## Exact scope and admission

Only `variable-output` is supported, with namespace
`magic:legacy-promoted:card` and the exact sorted Card pair:

| Card | Card ID | Accepted subject |
|---|---|---|
| Snow-Covered Wastes | `46a07b53-ff58-4bd6-80dd-ded2eb0e29a3` | `snow-wastes-mana` |
| Cabal Coffers | `7358e164-5704-4e78-9b21-6a9bf2a968ce` | `coffers-mana` |

`load_context_evidence_review(**explicit_evidence_arguments)` calls the existing
public `load_strategic_requirements` once. It calls the owning public exact-ID
`for_cards` and `validate_report` interfaces and verifies both subjects. The
admitted requirements report is privately owned as immutable bytes. No neighboring
private snapshot, copied example report, independent Card pipeline, source fetch,
or inferred name join is used. One batch shares the existing query, mechanical
reader and retained-rules context. Another public load revalidates current
evidence; a bound submission uses its admitted snapshot.

The original empty-context requirements identity remains
`sha256:47b134c21c5a54087ed29e6c70b06a5591e60958f38e2db4c759d1bafb71cedd`.
Owner decision:
`sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075`.
Accepted collection:
`sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`.
Only the two existing bounded retained-text subjects are displayed by this
consumer. The other seven accepted subjects and all four original question
families remain available through their unchanged original APIs.

## Input contract and identities

| Record | Domain / identity |
|---|---|
| Schema | `coffers-wastes-context-evidence-schema-v1` / `sha256:41b4039a87bb7bc7ac486ed07271f2a0e2e9d1dc630790db35e4e95b5b593d2c` |
| Candidate | `coffers-wastes-context-evidence-candidate-v1`, own `candidate_id` |
| Submitted packet | `coffers-wastes-context-evidence-packet-v1`, own `packet_id` |
| Review policy | `coffers-wastes-context-review-policy-v1` / `sha256:ffa32e2945bdb3e5555be2db88f210b3dba5fb2876cae93c36b897bc92f69318` |
| Computed report | `coffers-wastes-context-review-report-v1`, own `report_id` |

These are domain-separated content identities using the existing canonical JSON
contract. A content digest binds bytes, not truth, source authority or copyright
clearance. A new rehashed candidate is a different unverified submission, never
an authorized amendment to an existing immutable binding.

Each candidate contains these closed fields, plus its schema/version identity
and fixed unverified authority fields:

| Field | Meaning and bound |
|---|---|
| `category` | One of the four categories below. |
| `source` | Closed `type`, `claimed_origin`, `reference`, `source_date`, `observation_date`. Types: owner-declaration, owner-supplied-excerpt, reference-lead. Origin/reference are nullable printable strings, at most 120/160 characters. Explicit dates are nullable valid ISO calendar dates. No date is invented or treated as an authenticated observation. |
| `scope` | Closed `deck_id` (1..64 characters), `deck_version` (1..32), `kind=declared-hypothetical-deck`. These are unverified labels, not canonical deck identities. |
| `assertion` | Explicit uninterpreted factual claim, 1..240 printable characters. The program does not parse prose or infer Card subtypes. |
| `payload` | Exact category-specific typed declaration below. |
| `content` | Closed `mode`, `text`, `digest`. Declaration-only, reference-only, or supplied-utf8. Supplied text contains 1..1,024 exact UTF-8 bytes; no newline or Unicode normalization. Absent bytes remain absent, including when a digest is claimed. |
| `claimed_use_restrictions` | Nullable 1..160-character unverified use-restriction claim. It cannot grant permission. |
| `requirement_refs` | Zero to four unique sorted exact existing requirement IDs. Foreign/irrelevant references are quarantined as OUT_OF_SCOPE. Empty selects the category's finite relevance mapping. |
| `notes` | Zero to three distinct bounded provenance/verification notes, at most 120 characters each. Notes remain declarations. |

Packets contain at most **four** candidates in canonical candidate-ID order,
with unique IDs. Candidate and packet bounds are 8,192 and 32,768 canonical
bytes; total directly supplied content is at most 4,096 bytes. Four candidates
allow one per authorized category while keeping maximal contradictory packets
inside inherited report bounds. Duplicate keys, unknown fields, foreign scope,
noncanonical JSON, floats, booleans in integer fields, malformed dates and
unsupported source/content types reject. All decoded views are independent.

`reference-lead` has absent source content; an `owner-supplied-excerpt` requires
actual supplied bytes. Format/performance candidates default to reference-only
when no content is supplied. A source reference is an opaque evidence lead:
there is no URL opening, file reading, protocol authentication or lookup.
No entire decks, databases, articles or provider datasets are ingested.

## Four categories and exact requirement mapping

The finite registry selects **existing** admitted requirement rows by template
identity. It copies neither their policy nor their computed status. Every
mapping carries the original requirement ID, source support refs, unchanged
status, relevance rationale, unresolved information, future consumer and
independent validation method. Every candidate also maps to the existing
`evidence-authentication` requirement; supplying explicit refs cannot bypass it.

| Category | Strict payload | Existing requirements it may inform |
|---|---|---|
| `deck-composition` | `total_lands`, `claimed_swamps`: integer 0..1,000 or null; at least one present. Swamps mean a **claimed subset of the declared hypothetical deck's total lands**, not established Card subtypes or battlefield permanents. | `swamp-composition` |
| `objective-and-mana` | `objective` from the unchanged four-value investigation-intent vocabulary; nullable `mana_requirements` claim, at most 240 characters. | `deck-objective`, `resources-and-timing` |
| `format-legality-lead` | `format_label`, 1..80 characters; no format registry or legality assertion. | `format-label`, `format-legality` |
| `performance-lead` | Nullable `method`, `sample_scope`, `limitations`, each at most 160 characters. Any asserted outcome is an uninterpreted claim. | `strategic-performance` |

Deck composition is deliberately **not** routed into `hypothetical-swamps`.
A declared deck quantity is not a controlled Swamp count. The owning hypothetical
calculation stays UNSPECIFIED, with no output quantity. Coffers retains its
written `{2}, {T}` cost, and Wastes retains its fixed written output. No net
mana, break-even threshold, probability, actual payment or deck consistency is
calculated. The original hypothetical consumer remains available separately.

## Review states, conflicts and missing evidence

Every candidate retains `SUBMITTED_UNVERIFIED` and `REQUIRES_REVIEW`. Independent
additional triage states can coexist:

| State | Meaning |
|---|---|
| `CONFLICTING` | Two typed declarations disagree within the exact same claimed deck/version scope, or a claimed Swamp subset exceeds its declared total. |
| `INSUFFICIENT_SOURCE` | Missing claimed origin/reference/date, absent source bytes, incomplete composition, or missing performance method/sample/limitations. The precise codes and fields are retained. |
| `OUT_OF_SCOPE` | A requested requirement identity is foreign or irrelevant to this authorized category. Foreign packet Cards/families/namespaces instead reject the entire request. |

Internally inconsistent and out-of-scope candidates are quarantined. Cross-record
conflicts preserve both original assertions, source metadata, exact candidate IDs
and incompatible values. No preferred source, correction, average or winner is
selected. Matching deck labels disclose a possible conflict; they do not prove
that the sources refer to the same real deck. Different declared versions do
not automatically conflict. Prose contradictions, differing methods or multiple
compatible resource needs require human interpretation and are not inferred by
text searches.

All original strategic requirement statuses remain unchanged, including absent
context and unresolved independent validation. Candidate presence supplies no
authenticated source fact. `review_event`, reviewer and approval remain null;
source authentication and permissions remain NOT_ESTABLISHED. A normal CLI exit
indicates a computable review view, never approval or readiness for recommendation.
There is no status toggle that promotes evidence. An authorized review-record
and reviewer-identity/promotion process requires additional governance and remains
unimplemented; tests issue no synthetic approvals.

## Public API and CLI

```python
from card_intelligence.context_review import load_context_evidence_review
from card_intelligence.context_review_input import make_candidate, make_packet

owner = load_context_evidence_review(**explicit_overlay_evidence_arguments)
candidate = make_candidate(
    category="deck-composition",
    source={"type": "owner-declaration", "claimed_origin": "Owner claim",
            "reference": None, "source_date": None, "observation_date": None},
    scope={"deck_id": "hypothetical-example", "deck_version": "v1",
           "kind": "declared-hypothetical-deck"},
    assertion="Hypothetical deck declaration, not observed game state.",
    payload={"total_lands": 36, "claimed_swamps": 20})
packet = make_packet([candidate.to_dict()])
bound = owner.submit(packet.to_dict())
report = bound.report()
bound.packet()                         # independent full submitted packet
bound.candidate(candidate.to_dict()["candidate_id"])
bound.candidates(); bound.provenance(); bound.conflicts(); bound.missing()
bound.check()                          # snapshot integrity, not source refresh
bound.validate_report(report.to_dict())
bound.parse_report(report.to_json().encode())
owner.validate_report(report.to_dict(), packet.to_dict())
requirements = bound.detailed(report.to_dict()["requirements_reference"])
historical = bound.detailed(report.to_dict()["full_evidence_reference"])
```

The bound API privately owns the **complete** submitted packet. Validation
recomputes expected reports against that packet and the admitted requirements;
it never trusts self-contained report hashes. Coherently rehashing a changed
assertion at every level creates a different submission and cannot validate an
old report. Altered owner decisions fail fresh public admission even if rehashed.
Detailed requirements references check exact report identity, canonical byte
count and digest, reproduce through public owning APIs, then validate. Existing
overlay/rule/explanation/scenario routes delegate to their owning public reader.
The full original report is retained separately, not embedded in every packet.

Run `PYTHONPATH=src python -m card_intelligence.context_review_cli` with the same
explicit five root and four expected-ID options as the existing overlay:
`--catalog-root`, `--mechanical-root`, `--review-root`, `--cohort-root`,
`--decision-root`, `--expected-profile-id`, `--expected-query-snapshot-id`,
`--expected-plan-id`, `--expected-decision-id`. Put `--json` before the subcommand.

```text
create candidate-inputs.json
validate-packet packet.json
review packet.json
candidates packet.json
candidate packet.json EXACT_CANDIDATE_ID
provenance packet.json
conflicts packet.json
missing packet.json
check packet.json
validate packet.json report.json
detail reference.json
```

`create` accepts a canonical bounded list of `make_candidate` keyword records,
computes their exact candidate identities, and emits a packet to stdout. It
writes no canonical data. All commands perform actual evidence admission.
Exit 0 means successful construction/inspection; exit 2 is rejection; exit 3
means conflicting or out-of-scope triage. Insufficiency remains visible even
when the operation returns 0. There is no approval command. Readable review mode
summarizes source/claim/content digest/findings and uncertainty without appending
raw JSON. Explicit detail mode emits the separately requested full JSON evidence.

## Actual demonstrations, sizes and timing

[The retained receipt](examples/context-evidence-review-v1.json) contains ten
complete submitted packets and four rejection operations covering **all twelve**
requested demonstration categories. They are explicitly hypothetical
owner-submission examples, never authenticated observations or approved new
interpretations. Report identities, exact packet/candidate/requirement IDs,
unchanged statuses, conflicts and actual CLI receipts are retained and
recomputed in tests. No example JSON is used as source admission.

| Demonstration | Canonical / readable bytes | Result |
|---|---|---|
| Empty packet | 28,971 / 8,484 | Unresolved review/strategic prerequisites remain. |
| Consistent hypothetical 36 lands / 20 claimed Swamps | 31,691 / 10,124 | Submitted declaration only; controlled Swamps stay UNSPECIFIED. |
| Second 40 / 25 declaration, same claimed version | 35,216 / 12,693 | Separate total-land and claimed-Swamp conflicts; preserve both. |
| Internally inconsistent 20 / 30 | 31,888 / 10,280 | Quarantined; no correction. |
| Owner-declared objective/mana need | 32,511 / 10,580 | May inform objective/resources review; proves no achieved goal or payment. |
| Dated format/reference-only lead | 32,492 / 10,555 | Referenced bytes absent; no legality/currency verification. |
| Performance/reference-only lead | 32,180 / 10,541 | Missing sample metadata and content remain explicit. |
| Exact supplied CRLF/LF content and digest | 31,854 / 10,220 | Exact bytes retained; no source authentication. |
| Missing claimed source/method/scope metadata | 32,653 / 10,812 | Precise insufficiency findings. |
| Four categories supplied together | 41,876 / 16,261 | All original requirement statuses remain unchanged; strategy unresolved. |
| Forged authentication and permission assertions | Rejected | INVALID_SUPPLIED_EVIDENCE, including after recomputing candidate IDs. |
| Coherently rehashed report/evidence substitution | Rejected | REPORT_INTEGRITY_REJECTED against the full original bound submission. |

Actual batch admission measured 5,824.684 ms. Actual view plus readable rendering
measured 2.033–4.129 ms; timings are software observations, not guarantees or game
observations, and are outside deterministic report identities. Tests also cover
maximal content/provenance and all pairwise contradictions. Canonical/readable
bounds remain **65,536 / 32,768 bytes**; no inherited limit is increased.

## Preservation and review stop

All inherited runtime, Card/Printing data, dossiers, policies, owner decisions,
pending/accepted interpretations, reports, market evidence, identity records,
source projections and workflows remain unchanged. Two test-only helper
successors reconstruct their canonical predecessors exactly. Three exact new
runtime paths are pinned; existing finite path sets and original source pins
remain intact. Unknown paths, changed pins and nonexact helper edits still fail.

Only Wastes has the existing current promoted identifier edge. Coffers retains
IDENTITY_NOT_ESTABLISHED for that edge; both retain missing operator-production
identity. Neither acquires functional-role/contextual-pilot membership.
Historical matching never promotes current authority or production eligibility.

Coverage remains 104 CR units / 16 projections / 24 retained land-context units.
No new Cards, Printings, acquisitions, interpretations, approvals, roles, rules,
identity promotions, market observations or strategic rankings are created.
`canonical_admission=false`; `execution_authority=BLOCKED`; semantic closure
OPEN; all ten activation responsibilities OPEN / EXECUTION_BLOCKED.
Source-policy clearance remains not granted. Private retention, redistribution,
free/commercial service and AI export remain NOT_ESTABLISHED; Tier A remains
non-production. Supplied content is unverified non-production review material,
not a permission grant or production-data admission.

One proposed next milestone, **not authorized or begun**: a design-only reviewer
authorization and append-only review-record contract for this one packet family.
This is needed before an independently authored review decision can carry
defined authority. Exclude automatic approval, evidence promotion, new source
acquisition, rules projections, strategic scoring, recommendation and simulation.

Final exact head/tree/test-merge, preservation audit, focused/local/hosted checks
and real publication/readback receipts belong in the single draft PR. Stop for
independent Senior PM review and final owner approval. No merge or auto-merge.

Future implementation milestone authorized: false  
Future source projection authorized: false  
Future milestone begun: false
