# Query snapshot and attachment verification performance

One owner-authorized bounded milestone. Architecture v13 remains ACTIVE APPROVED;
Decision 017 remains ACCEPTED. Owner retains final merge approval. Delivery stops
at one draft PR, with no merge or auto-merge.

## Canonical base and historical observations

Direct GitHub branch, PR and Git commit requests confirmed canonical main/base
`f66c912a2fbffe80c4c60241e555dfeeb4ba0c36`, tree
`d98d291da9a542f0396ce399043279fed88ec20d`. PR #205 is merged; its independently
reviewed head `c25b57a7a3e3a618f58b071f0e2d007b52a3e190` has that same tree and
is main's second parent. Local checkout was clean at that exact main. The single
implementation branch is `codex/query-attachment-performance`.

Completed historical logs were read directly from GitHub jobs 119662720413 and
119662999196. These are historical observations, not controlled runner pairs.

| PR #205 observation | Push 39730037126 | PR 39730124287 |
|---|---:|---:|
| Outer discovery, 2,459 tests / 11 skips | 3028.080s | 3040.191s |
| Preparation | 135.613104s | 139.746870s |
| Publication call, including nested discovery | 3658.214606s | 3647.958614s |
| Nested discovery, 2,459 tests / 11 skips | 3401.768s | 3390.966s |
| Total integration before cleanup | 3793.844454s | 3787.721701s |
| One-test publication regression including cleanup | 3794.173s | 3788.079s |

The overlapping hosted job envelope was approximately 115 minutes. Nested
discovery is inside the publication call; preparation and publication are inside
total integration. Concurrent jobs and enclosing/nested durations are never added
as owner elapsed time. Both historical logs show the actual 654-card writer,
successful complete nested validation, disposable local bare-remote publication,
and matching head readback. Only platform transport was simulated.

## Measurement design

Baseline code comes from a detached checkout of the exact required main.
`scripts/measure_query_attachment_performance.py` runs fresh subprocesses and
records repeated operations separately from construction, actual catalog counts,
implementation hashes, Python/platform, peak process RSS and canonical signatures.
OS page caches are uncontrolled. Fresh process does not mean cold storage.
Profiles are separate targeted runs and are not ordinary runtime observations.

Required consumers are the retained public role/comparison compatibility test and
the two named current-catalog query/collection and mechanical-coverage tests.
Current-class setup constructs the real query, resolver and mechanical reader;
its construction cost is reported separately. In the ordinary catalog the
mechanical missing-source loop is empty. In the expanded catalog it exercises
actual current missing-source dossiers. The old role profile must reject expanded
current bytes; fast rejection never represents full-parity work.

Expanded inputs come exclusively from the existing
`ExpandedPublicationValidationRegression.prepare_writer_expansion()` real-writer
disposable preparation path. It asserts 654 Cards and the original 810 selected
rows. The preparation stops at the existing smoke stage. Measurement does not
claim publication or create admission evidence.

## Unchanged authority and gameplay

No gameplay source units, source inspection, projections, rules knowledge,
capabilities, consumer implementations, catalog writers, admission/publication
code, workflow triggers/stages/checks/timeouts, schemas or historical evidence
are changed. Production external-data attachment remains unsupported.

Gameplay remains 91 projected real source units, 13 projections, 7/8 coverage of
the single 602.2b import, 601.2i unprojected, semantic closure OPEN, all ten
activation responsibilities OPEN / EXECUTION_BLOCKED, and real execution BLOCKED.
Historical acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
Source-policy clearance remains `not_granted`; private retention, redistribution,
free service, commercial service and AI export remain `NOT_ESTABLISHED`.

## Implementation and ownership

`src/query/engine.py` traverses dataclass fields directly instead of copying via
`asdict()` and then traversing the copied tree. String-key conversion, stable
ordering and collision behavior, Unicode, tuple/list output, numbers and nulls
retain their existing JSON representation.

`QueryResult` now isolates constructor aliases. Its public fields remain mappings;
their private backing trees contain only mapping proxies, tuples and immutable
JSON scalars. Nested reads return ordinary detached dictionaries/lists. Mutating
those reads or an `as_dict()` export cannot change a result; assigning a top-level
mapping key raises `TypeError`. Generic `dataclasses.asdict()` exports remain
supported. This implements the existing detached/immutable-result contract
without consumer changes or a public schema migration. Unsupported non-JSON
mutable leaves cannot enter reusable canonical content.

Each engine hashes its owned immutable results once, lazily, and retains only the
identity. Snapshot exports remain fresh mutable copies. Every attached snapshot
still verifies current content and scope before and after access. Repeated IDs
therefore refer to the same privately immutable result content, while filesystem
drift still blocks access. There is no global engine/result identity cache.
The original attachment handle and read inventory are bound independently;
clearing/replacing the handle cannot bypass verification after warmup.

During construction only, the query materializes the actual selected audit
inventory once into immutable bytes and private immutable values. Entity lineage
and audit references derive from those exact bytes; obtaining a review package
does not repeatedly export the whole audit population. A `finally` block drops
the construction materialization. Subsequent public audit operations reread the
current inventory and bytes. Attached construction retains its full before/after
verification; no excluded audit is read.

`src/repository/legacy_profile.py` builds an immutable relative-path inspection
plan from strictly validated control bytes. It includes file indexes, scalar
identity/count metadata, namespace selections, absences and ancestor plans.
It contains no absolute root or verification result. Public bindings remain fresh
deep copies. Verification rereads the control and preserves strict canonical
equivalence for whitespace-different JSON; duplicate keys and nonfinite numbers
still fail.

After a complete successful verification, an attachment retains the exact selected
bytes whose JSON was strictly parsed. A later verification skips only that pure
parse when freshly read bytes equal the retained immutable bytes. Every selected
file is still opened/read, checked for path/symlink/regular-file/size/during-read
constraints, and checked against its existing exact hash and length. Roots,
game/selected namespaces, bound absences and casefold collisions are reinspected
on every verification. No path, inode, mtime, size, TTL or prior success substitutes
for a current check. Ordinary retained selected bytes total 4,994,619 bytes
(about 4.76 MiB) per attachment, plus small indexes; this is an explicit memory
tradeoff. Identical controls at separate roots share no filesystem result.

The separate targeted baseline profile took 27.075s and 69,081,047 calls; this is
profiled runtime, not an unprofiled sample. Across two constructors it observed
99,775 file reads, 116,128 JSON parses and 3,068 `_audit_records()` calls. Repeated
audit reads/conversion and snapshot materialization motivated the chosen query
changes. Cumulative profile durations overlap and are not suite percentages.

## Finite implementation successors

Historical fixture rows and evidence remain immutable. The new
`tests/query_attachment_performance_implementation_changes.json` ledger records
the exact base/tree, original Git blobs/hashes/lengths, current replacement
hashes/lengths, the finite measurement-tool addition, seven original fixture
bindings and PR #205's unchanged implementation ledger.

`tests/query_attachment_performance_preservation.py` handles hash-only rows and
hash-plus-length rows explicitly. Only an exact authorized original row selects
its pinned replacement; actual current replacement bytes must match. Old
implementations fail current mode. Unrelated rows keep their original checks,
including PR #205's gameplay successors. Relative path and regular-file checks
remain. The shared 82-row historical implementation/tool inventory is reconstructed
only after exact current successor/tool verification. Unknown additions remain
visible. All operational-document bodies and prior appendices remain unchanged.

## Controlled ordinary-catalog measurements

Same managed environment for both versions: CPython 3.12.14 / Clang 22.1.3,
Debian 13.6, Linux 6.18.55 x86_64 / glibc 2.41, five visible CPUs with a four-CPU
cgroup quota, 16 GiB memory limit, `PYTHONHASHSEED=0`. No MTGLAB source selectors
are configured; no rules source was inspected. Heavy tests did not overlap timed
consumer runs. Small fictional regression checks took under three seconds each.

Ordinary catalog: 384 promoted Cards, 913 Printings, 235 Identifiers, two Finishes;
the full query adds typed records for 1,566 entities. Three fresh processes each
run construction once and operations once plus two repeats. Table entries are
medians. Role/comparison uses one fresh process with first and repeat full-parity
cycles; an earlier independent unprofiled baseline was 219.936465s.

| Actual operation | Baseline | Candidate | Seconds saved | Change |
|---|---:|---:|---:|---:|
| Full role/comparison parity, first | 227.244239 | 48.603656 | 178.640583 | -78.61% |
| Full role/comparison parity, repeat | 220.803422 | 47.763431 | 173.039991 | -78.37% |
| Current consumer class construction | 15.576938 | 8.165169 | 7.411769 | -47.58% |
| Query/collection test, first | 0.274625 | 0.333977 | -0.059352 | +21.61% |
| Query/collection test, repeat | 0.135914 | 0.152067 | -0.016153 | +11.88% |
| Bare query construction | 4.919517 | 2.301209 | 2.618308 | -53.22% |
| First bare snapshot | 0.265335 | 0.167661 | 0.097674 | -36.81% |
| Repeated bare snapshot | 0.237449 | 0.000002934 | 0.237446 | -99.9988% |
| Attachment construction | 0.100212 | 0.135353 | -0.035140 | +35.07% |
| Repeated attachment verification | 0.108674 | 0.020197 | 0.088476 | -81.41% |
| First verification after attachment creation | 0.083443 | 0.020848 | 0.062595 | -75.02% |
| Attached query construction | 6.284945 | 2.572780 | 3.712165 | -59.06% |
| First measured attached snapshot (constructor already validates one) | 0.500836 | 0.044786 | 0.456049 | -91.06% |
| Repeated attached snapshot | 0.488808 | 0.044806 | 0.444002 | -90.83% |

Times are seconds. Positive change denotes a regression. The small collection
loop and initial attachment cost increased; these are not hidden by selecting a
serialization-only result. The real dominant full role/comparison workload is
more than halved. The ordinary mechanical coverage test has an empty missing-source
loop and takes approximately 0.0001s first / 0.00003s repeat; it supplies correctness,
not a performance claim.

All 74 captured role/mechanical/dossier/reasoning/comparison/Decision/handoff
artifact digests match exactly across revisions and repeats, combined digest
`5e24185d1b8b8db24453fc767a6999378949ca0800487d5d14c1c311586699b4`.
The ordinary query ID remains
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`;
snapshot export SHA-256 remains
`4ebc484f49af8dc36f465a49d5c1a141e15896d756ceba622b32794d37d17be6`.
The profile and closure IDs retain their fixture-specific existing pins.

## Expanded comparison qualification

The real writer produces identical `state.json` bytes in independent preparations,
but its authorization binding includes the actual disposable `repository_root`.
That binding is retained in the promotion audit and its digest; query provenance
binds the exact audit bytes. Independent disposable roots therefore have different
query IDs despite identical entity-state bytes. No writer, audit or identity input
is normalized or repinned to hide this difference.

For an exact-input paired expanded comparison, the bounded tool prepares one real
writer catalog, runs fresh baseline consumer processes, overlays only the two
authorized reader implementations, and runs fresh candidate processes. It checks
the entire canonical/audit input inventory before and after. Separate preparations
remain labeled observations and supply preparation-cost measurements; their query
IDs are not treated as unchanged-input pairs.

The controlled expanded pair binds 83 canonical/audit files / 24,548,560 bytes,
inventory SHA-256
`6ca45e2fb950268dfb9f3b6ea7ddd9431a3dd621cdd21240736fb84a6adba999`.
The tool proves that inventory is identical before and after both versions.
Expanded counts are 654 promoted Cards / 1,183 Printings / 505 Identifiers /
two Finishes; including typed records the query has 2,376 entities. The actual
mechanical coverage loop visits 270 missing-source Cards.

| Actual operation on this same expanded input | Baseline | Candidate | Seconds saved | Change |
|---|---:|---:|---:|---:|
| Current consumer class construction | 67.651205 | 13.043971 | 54.607234 | -80.72% |
| Query/collection test, first | 5.744723 | 3.451414 | 2.293308 | -39.92% |
| Query/collection test, repeat | 5.946343 | 3.302657 | 2.643686 | -44.46% |
| Missing-source mechanical coverage, first | 0.094207 | 0.128018 | -0.033811 | +35.89% |
| Missing-source mechanical coverage, repeat | 0.098381 | 0.153368 | -0.054987 | +55.89% |
| Bare query construction | 21.865674 | 3.856260 | 18.009414 | -82.36% |
| First bare snapshot | 0.346658 | 0.160635 | 0.186022 | -53.66% |
| Repeated bare snapshot | 0.293792 | 0.000003495 | 0.293789 | -99.9988% |
| Old-profile attachment rejection, first | 0.038653 | 0.030489 | 0.008164 | -21.12% |
| Old-profile attachment rejection, repeat | 0.036230 | 0.028125 | 0.008104 | -22.37% |
| Retained role test's rejection branch, first | 0.072251 | 0.055553 | 0.016698 | -23.11% |
| Retained role test's rejection branch, repeat | 0.065031 | 0.052323 | 0.012708 | -19.54% |

The missing-source loop is modestly slower in absolute terms. Its unknown fields,
source-binding-missing reasons and acquisition abstention behavior remain checked;
no claim of universal consumer acceleration is made. The expensive actual current
construction and collection work continue executing on the expanded catalog and
improve materially. Historical-profile rejection is preserved separately.

The controlled expanded query ID is identical across implementations:
`sha256:27017cca98170d324b4cbb8d8e859ea86085c13d3d502cfd458d4ca3eb7d65fb`.
This is this prepared input's identity, not a new universal fixture pin. Independent
earlier preparations had query IDs beginning `bfb9fcff` and `ec03d539`, respectively;
they remain labeled observations, not unchanged-input output comparisons.
The full expanded snapshot export SHA-256 remains
`83b6d1413f1c0ab402bba12815cf99e564a1aee2d49f940adebe60c61263adc7`;
mechanical reconciliation SHA-256 remains
`1c0192e0ba898676ba8f8d77df3a114752a1865dc238c2c272273f48a89fbf1b`.

Ordinary preparation is zero. Independent baseline real-writer preparation
observations were 112.591497s, 115.462721s and 119.764278s; candidate preparation
was 36.896783s (82.867495s / 69.19% below the controlled pair's baseline
preparation). These preparations use separate disposable roots and seed code;
they are separately qualified observations, not unchanged-query-input identity
pairs. They do not invoke publication.

Ordinary process peak RSS medians (KiB), baseline → candidate: current consumers
134,292 → 123,428; snapshot/attachment 99,924 → 93,688; the two-cycle role process
139,536 → 113,240. These include imports, transient values and all sample operations;
they do not isolate cache allocation. Expanded worker `ru_maxrss` may inherit the
pre-exec parent image/high-water, so it cannot establish a consumer memory change.
The attachment's approximately 4.76 MiB retained-byte tradeoff remains regardless
of observed process peaks. OS caches and allocator history are uncontrolled.

The separate candidate profile took 19.931s / 90,455,486 calls. JSON parses fell
116,128 → 306; attachment binding parses 16,377 → two; attachment `_read()` calls
6,627 → 429; constructor `_audit_records()` calls 3,068 → zero. Both profiles
execute eight attachment verifications. Current selected reads are retained;
removed reads were repeated construction/metadata work. Candidate profiling adds
heavy overhead to 8.5 million recursive private-view conversions (`_thaw`), so
neither profile duration nor overlapping cumulative times estimate ordinary cost
or a whole-suite share. Actual unprofiled consumers establish the improvement.

The reproducible measurement bundle is `/tmp/query-measurement-summary.json`,
SHA-256 `0016859d00827451c845da69e0b9488615c777408b196f087239070d96fdc118`.
It records exact command argument arrays and raw-report checksums. Principal raw
report SHA-256 values are:

| Report | SHA-256 |
|---|---|
| Baseline ordinary | `048532a4c6353f715e9b3315f80820812e5bc239470451dc09317d602b3a4c44` |
| Candidate ordinary | `6062d71c145672ddb184a057dc0c83f9148194a29ce8f6fa985276ec201f3dcd` |
| Baseline role | `9766b8df4af8d34d3b7d9c79d7f8594fa4ad22e6389191e1f1f9d4e3592a338c` |
| Candidate role | `2c1712d74745aa644078e820cb242b5068e124d11265272e9f85d99723765d62` |
| Controlled expanded pair | `c0d8169a740a68726c84f0d786adf6ecfd6ae3366bc9e786b65c80e48f5dcf65` |

Measured candidate implementation hashes match the final finite ledger:
engine `e14b686b0c7db19e9ead9067b168ad91aba25c0ea51f31228635adb19a51abe0`;
legacy profile `3f4ab75d9d11fba60ac70cb1a377170c43294cfd6cf6deb61880482518dddea3`.
The bounded tool's final SHA-256 is
`9fa6e860d2021780b13fbfeb83c77b93dc2767248a54e41330fc53e6108e5781`;
ledger SHA-256 is `47c5389f24b8b28a8c7faa825619e2c6ddc0ce2534ea0321e780e25139be6a3d`.

Final complete-discovery and hosted observations, the exact tested head/tree,
literal checkouts and end-to-end comparison are maintained in the associated
draft PR's final evidence section. No success is inferred from a pending check.

## Correctness, preservation and attempt history

Initial broad focused selection: 289 tests / 166.360s / zero skips, failures or errors,
exit 0; monotonic process total 167.171810s. It includes all eleven requested
query/attachment/compatibility/current-catalog modules, the three new regression
modules, relevant historical preservation modules/methods and the aggregate
implementation/tool inventory. Exact argument array is retained in
`/tmp/query-attachment-focused-final.json`; verbose log SHA-256 is
`fc285680b89c244df644b7e498b8870efa9804d614944c946d93120b62ac206a`.

Additional aggregate-adapter selection: 76 tests / 1.638s / zero skips, failures
or errors, exit 0. This covers all nine additional historical preservation classes
and the eight new guard methods. Log SHA-256:
`f4309ba29cc51ebb22818a2737cebe97dad14d8ef6915084dbfe3f3a10b90b1c`.
An AST comparison verifies that original assertion bodies, counts, digests,
enumeration and file checks remain; only imports, checked per-row adaptation and
accurate method names change. Eighteen existing preservation test files need
adapters because both runtime implementations occur in these historical families.

Inventory increases from 2,459 to 2,485 tests: eleven new query isolation/audit/
reuse tests, seven attachment verification tests and eight finite preservation
tests. Existing meaningful assertions remain; changed historical test names
distinguish preserved original rows from exact current replacements. No extra
skip, reduced input, disabled check or timing threshold is introduced.

Direct Git-base reproduction verified both original implementation blobs,
SHA-256 hashes and lengths. Independent blob/mode/inventory checks found all
53 retained fixture files / 29 directories, 160 gameplay evidence files /
23 directories, 137 gameplay source files / 12 directories, seven workflows,
52 canonical-data files, and 105 other review files unchanged. PR #205's
implementation ledger, helper and profiling tool remain byte-identical. Prior
operational documents and appendices remain byte-identical. The final immutable
audit log is `/tmp/query-attachment-immutable-audit-final-tool.log`, SHA-256
`1de22837e54eb5a73b2351fea04700c1453e68059255f0e2f574f0945cbb7279`.

Retained attempt history:

- The first two added audit tests errored during fixture authoring because an
  integer-only snapshot helper was given fractional confidence. Integer fixture
  confidence corrected that setup; numeric conversion coverage remains elsewhere.
- Initial preservation selection: 71 tests / 2.213s / three failures. The new
  exact measurement tool appeared in the old aggregate inventory; a finite
  checked adaptation was missing. The ninth selected test adapter fixes it.
  `/tmp/query-attachment-preservation-attempt-1.json` retains labeled metadata,
  not a reconstructed raw log. Subsequent 72-test selections passed; their logs
  remain labeled superseded after later source-pin corrections. The final
  289-test selection checks final runtime pins; wider aggregate adapters below
  receive a separate focused pass and a new complete discovery.
- First complete-discovery attempt was intentionally interrupted after 563.740500s
  with 1,247 completed result lines, seven observed skips and six aggregate
  preservation failures.
  No runtime-output failure had appeared. The initial pin scan missed historical
  aggregate source inventories that include the two implementations implicitly.
  Nine further test-only adapters preserve their original counts/digests and
  verify exact current successors. The incomplete failed attempt is retained as
  `/tmp/query-attachment-discovery-attempt-1-interrupted.log` and `.json`, exit -2
  from the intentional SIGINT, log SHA-256
  `347248cf06c9d4e3498b5af98b402d6f2490511a7af9c9e338d93c2b575a7240`.
  It is not a complete-discovery result and no hosted run used it.
- Initial default-sandbox Git fetch could not reach the session proxy; the
  explicitly network-enabled read succeeded and confirmed the exact base.
- Earlier independently prepared expanded measurements retain their own distinct
  audit-derived query IDs. They were superseded only for cross-revision identity
  comparison by the exact-input paired run, not discarded or repinned.

Complete discovery command is `PYTHONPATH=src python -m unittest discover -s tests
-p 'test_*.py' -v`. The unchanged hosted workflow additionally executes
`PYTHONPATH=src:tests python tests/publication_validation_regression.py`, including
the real 654-card writer, expanded complete nested discovery, disposable local
bare-remote publication and matching readback. A duplicate local complete
publication is not an extra gate. Final-head run links, literal checkouts,
ordered merge parents, actual publication diagnostics and the complete-cycle
comparison are recorded in the associated draft PR's final evidence section;
they cannot be inferred from a run's nominal `head_sha` or a pending status.

## Reproduction commands

From the candidate checkout (outputs are measurements, not admission evidence):

```sh
git worktree add --detach /tmp/mtglab-query-perf-base f66c912a2fbffe80c4c60241e555dfeeb4ba0c36
python scripts/measure_query_attachment_performance.py --repo /tmp/mtglab-query-perf-base --state ordinary --workload current_consumers --workload snapshot_attachment --repetitions 3 --warm 2 --output /tmp/query-baseline-ordinary.json
python scripts/measure_query_attachment_performance.py --repo . --state ordinary --workload current_consumers --workload snapshot_attachment --repetitions 3 --warm 2 --output /tmp/query-candidate-ordinary.json
python scripts/measure_query_attachment_performance.py --repo /tmp/mtglab-query-perf-base --state ordinary --workload role_comparison --repetitions 1 --warm 1 --output /tmp/query-baseline-role-formal.json
python scripts/measure_query_attachment_performance.py --repo . --state ordinary --workload role_comparison --repetitions 1 --warm 1 --output /tmp/query-candidate-role-formal.json
python scripts/measure_query_attachment_performance.py --repo /tmp/mtglab-query-perf-base --state expanded --comparison-repo . --repetitions 1 --warm 1 --output /tmp/query-expanded-controlled-pair.json
python scripts/measure_query_attachment_performance.py --repo /tmp/mtglab-query-perf-base --state ordinary --workload snapshot_attachment --repetitions 1 --warm 0 --profile /tmp/query-baseline-targeted.prof --output /tmp/query-baseline-profile.json
```

Stage new selected files before preparing the candidate's disposable writer root:
the existing fixture deliberately copies `git ls-files`. A separate candidate
preparation observation uses `--repo . --state expanded --workload role_comparison
--repetitions 1 --warm 0`; that workload confirms rejection, and is not parity.
Baseline and candidate measurements identify actual implementation bytes even
while the report is uncommitted; final ledger pins must match those bytes.

## Complete changed-path ledger

| Filename | Purpose |
|---|---|
| `src/query/engine.py` | Conversion, defensive ownership, snapshot identity reuse, construction-only audits, attachment binding. |
| `src/repository/legacy_profile.py` | Immutable relative plans and pure parsing reuse with current verification. |
| `scripts/measure_query_attachment_performance.py` | Actual consumer measurements and controlled expanded pairing. |
| `docs/QUERY_ATTACHMENT_PERFORMANCE.md` | Detailed evidence, commands, qualifications and operational status. |
| `tests/query_attachment_performance_implementation_changes.json` | Exact original/replacement/tool and retained-fixture pins. |
| `tests/query_attachment_performance_preservation.py` | Strict finite successor and current-byte adapters. |
| `tests/test_query_attachment_performance.py` | Conversion/mutation/snapshot/audit/retarget regressions. |
| `tests/test_legacy_profile_performance.py` | Warm reads, parsing reuse, unchanged-stat attacks, roots, metadata and equivalent controls. |
| `tests/test_query_attachment_performance_preservation.py` | Successor schemas, tampering, old-current rejection and unknown additions. |
| `tests/test_activated_ability_procedure_design.py` | Historical verifier rejection plus exact current successor checks. |
| `tests/test_gameplay_rules_bounded_activated_ability_preservation.py` | Exact hash-plus-length row successors. |
| `tests/test_gameplay_rules_bounded_mana_classification_projection.py` | Exact hash-only row successors. |
| `tests/test_mana_stack_exception_preservation.py` | Exact successors and original source inventory. |
| `tests/test_real_rules_execution_design_boundaries.py` | Checked adaptation of historical aggregate implementation/tool inventory. |
| `tests/test_shared_casting_stage_preservation.py` | Exact successors to retained rows. |
| `tests/test_shared_target_declaration_preservation.py` | Exact successors, original declaration evidence and appendices. |
| `tests/test_shared_target_allocation_preservation.py` | Compose these successors with PR #205's accounting. |
| `tests/test_shared_proposal_legality_preservation.py` | Compose these successors with PR #205's accounting. |
| `tests/test_gameplay_rules_bounded_casting_projection.py` | Checked successor adaptation of the original 292-source aggregate. |
| `tests/test_gameplay_rules_bounded_mana_ability_projection.py` | Checked successor adaptation of the original 308-source aggregate. |
| `tests/test_mana_ability_dependency_design.py` | Checked successor adaptation of the original 297-source aggregate. |
| `tests/test_mana_ability_direct_dependency_design.py` | Checked successor adaptation of the original 313-source aggregate. |
| `tests/test_madness_casting_dependency_design.py` | Checked successor adaptation of the original 282-source aggregate. |
| `tests/test_gameplay_rules_foundational_dependencies.py` | Checked successor adaptation of the original 256-source aggregate. |
| `tests/test_gameplay_rules_zone_change_direct_dependencies.py` | Checked successor adaptation of the original 256-source aggregate. |
| `tests/test_gameplay_rules_object_control_exceptions.py` | Checked successor adaptation of the original 256-source aggregate. |
| `tests/test_gameplay_rules_zone_change_exceptions.py` | Checked successor adaptation of the original 256-source aggregate. |
