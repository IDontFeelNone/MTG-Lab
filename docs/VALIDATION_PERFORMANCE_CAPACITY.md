# Validation performance and delivery capacity

This milestone changes validation implementation only. It adds no gameplay source
units or capabilities. Architecture v13 remains ACTIVE APPROVED and Decision 017
ACCEPTED. The owner retains merge approval; stop at one draft PR for independent
PM review, with auto-merge disabled.

## Authority and controlled comparison

Direct GitHub branch, PR, Git data and local Git checks established main/base
`bdccc4e9be2f6ff2aec7b5764baa022e15f51cfe`, tree
`6afe49701cd99b7b6f124a979fbe332c91bb4c71`. PR #204 is merged; reviewed head
`faf6f6d10d5fbdea92132088ffe59c188efd210f` has that same tree and is main's
second parent. The clean local `work` checkout was stale at
`a21cda0c22092a77ec07097d7b155e7a71bd8de2`. A fetch and new branch
`codex/validation-performance-capacity` reconciled it without removing work.
The isolated baseline worktree uses the exact required main. No external source
TXT or source selector was used; offline validation is not fresh reproduction.

Historical Actions observations were verified from actual run/job logs:

| PR #204 run | Checkout | Discovery | Publication integration |
|---|---|---|---|
| [Push 39703281020](https://github.com/IDontFeelNone/MTG-Lab/actions/runs/39703281020) | `faf6f6d10d5fbdea92132088ffe59c188efd210f` | 2,436 tests, 11 skips, 2,840.063s | 3,578.850s |
| [PR 39703287358](https://github.com/IDontFeelNone/MTG-Lab/actions/runs/39703287358) | `00d049f523d17413f39341663d625ccadc43db2c` | 2,436 tests, 11 skips, 1,996.100s | 2,508.675s |

The PR merge ref had ordered parents `a21cda0c22092a77ec07097d7b155e7a71bd8de2`
and the reviewed head. Both actual publication runs used the real 654-card writer,
2,436 nested tests, disposable bare-remote publication and matching readback.
Their nested validation log hashes were respectively
`647505e60a39bdc7e3430678cf8f2da8455de2dc79ddd05fb086dd0afe921cde` and
`6becc1c34b98843e00b3e2c175c318996f47661181de2cda0b99c9d29957e9ee`.
Historical nested duration/skips were unavailable from success summaries.
Publication integration includes preparation, writer work, nested discovery,
publication and readback. The workflows overlapped; their durations are not added
as owner elapsed time. Hosted hardware variability is separate from paired code
measurements. Historical hosted Python was CPython 3.12.15.

## Measured implementation boundary

The initial declaration load-plus-manifest profile made 11.37 million calls in
3.631s of cProfile internal time. Three historical validations recursively
regenerated older packages/manifests; declaration historical validation consumed
3.059s cumulatively. Profiling overhead is separate from the unprofiled elapsed
samples below.

Before editing, the selected implementation paths were enumerated:

- `src/gameplay_rules/shared_target_declaration/package.py` and
  `src/gameplay_rules/shared_target_allocation/package.py`: replace repeated
  historical reconstruction with pinned-manifest/current-byte validation, cache
  immutable contract bytes, avoid redundant manifest validation and consume private
  validated snapshots.
- `src/gameplay_rules/retained_stage_validation.py`: one bounded lower-level helper
  for canonical retained bytes, schema-specific own identities/domains and enclosing
  manifest bindings. Older packages do not import proposal-legality.
- `src/gameplay_rules/shared_proposal_legality/package.py`: integrate that same
  validator while preserving PR #204's caller-mutation corrections.

Actual disk verification remains fresh at public historical-validation boundaries.
Cached bytes contain immutable contract-derived metadata; cached success, paths,
mtimes and caller-owned dictionaries never authorize later operations. A supplied
review root must stand on its own. Invalid inputs fail before output creation.

## Reproduction and observations

Each measured cycle calls `load_package` on the actual retained package, then
`manifest` on its result. Both checkouts use the same retained inputs, Python
3.12.14 (Clang 22.1.3), Linux 6.18.55 x86_64/glibc 2.41, five reported CPUs,
`PYTHONHASHSEED=0`, bytecode writing enabled with no custom cache prefix, and no
configured source selectors. No heavy tests overlapped
the timing samples. Three fresh subprocesses per package each execute a first
cycle and two warm cycles. Gameplay imports and metadata initialization are in
the first-cycle timer. Whole-process timing additionally includes interpreter
startup, benchmark standard-library imports, both warm cycles and teardown.
OS page cache is uncontrolled: fresh process does not mean cold storage.
Profiles are separate from unprofiled elapsed measurements.

The baseline revision is the exact required main. The candidate was uncommitted
during measurement; its four exact implementation SHA-256 values match the
final ledger. Thus the measured implementation is identified independently of
later report/commit metadata.

Reproduce from the candidate checkout, with a detached baseline at required main:

```sh
git worktree add --detach ../MTG-Lab-baseline bdccc4e9be2f6ff2aec7b5764baa022e15f51cfe
python scripts/profile_validation_capacity.py --repo ../MTG-Lab-baseline --repetitions 3 --warm 2 --profile-dir /tmp/mtglab-baseline-profiles --output /tmp/mtglab-baseline.json
python scripts/profile_validation_capacity.py --repo . --repetitions 3 --warm 2 --profile-dir /tmp/mtglab-candidate-profiles --output /tmp/mtglab-candidate.json
```

| Package | First cycle/import median, baseline → candidate | Warm median, baseline → candidate | Whole process first + 2 warm, baseline → candidate |
|---|---:|---:|---:|
| shared_target_declaration | 1.638366s → 0.403125s | 1.531626s → 0.282055s | 4.796029s → 1.016172s |
| shared_target_allocation | 12.682119s → 0.405716s | 12.537494s → 0.277366s | 37.572077s → 1.020020s |
| shared_proposal_legality | 1.590748s → 0.403879s | 0.256119s → 0.269320s | 2.162395s → 1.006567s |

Warm reductions are **81.6% declaration** and **97.8% allocation**. Proposal
legality warm increased **5.15% / 13.2ms**; no warm improvement is claimed for it.
First-use reductions are respectively 75.4%, 96.8% and 74.6%.

Raw elapsed samples (seconds; each warm list contains two cycles per process):

| Package / state | Baseline | Candidate |
|---|---|---|
| shared_target_declaration / first/import | 1.694771, 1.638366, 1.627570 | 0.403125, 0.404376, 0.378757 |
| shared_target_declaration / warm | 1.547832, 1.702451, 1.514294, 1.577057, 1.513229, 1.515420 | 0.274676, 0.275265, 0.264352, 0.288844, 0.305917, 0.300436 |
| shared_target_declaration / whole process | 5.036300, 4.796029, 4.714379 | 1.007418, 1.016172, 1.043536 |
| shared_target_allocation / first/import | 12.682119, 13.041936, 11.923084 | 0.403988, 0.405716, 0.427025 |
| shared_target_allocation / warm | 12.073665, 12.116655, 12.519425, 13.153245, 13.031577, 12.555563 | 0.279144, 0.275588, 0.268559, 0.273434, 0.301728, 0.302584 |
| shared_target_allocation / whole process | 36.932642, 38.775842, 37.572077 | 1.020020, 1.007045, 1.093724 |
| shared_proposal_legality / first/import | 1.591268, 1.590748, 1.574714 | 0.403879, 0.419120, 0.403846 |
| shared_proposal_legality / warm | 0.257901, 0.254337, 0.252797, 0.267010, 0.250390, 0.257989 | 0.267818, 0.275120, 0.269091, 0.274860, 0.267505, 0.269549 |
| shared_proposal_legality / whole process | 2.162395, 2.170169, 2.142559 | 1.006567, 1.023354, 0.995524 |

| Profile call count per load + manifest | Declaration before → after | Allocation before → after | Proposal before → after |
|---|---:|---:|---:|
| Actual `_read` calls | 2,700 → 761 | 19,898 → 781 | 2,948 → 802 |
| Activated prior-package verification | 6 → 2 | 44 → 2 | 7 → 2 |
| Activated expected-record construction | 30 → 3 | 281 → 3 | 28 → 4 |
| Activated manifest construction | 19 → 2 | 180 → 2 | 18 → 2 |

Calls to declaration historical validation fall 22 → 0 inside the allocation
cycle; its required history is checked directly through the shared validator.
Declaration itself performs two public historical checks per cycle instead of
three. Validation of the older 115-file baseline and schema bindings remains
the dominant targeted cost (about 0.53s of the 0.80s allocation profile).
Repeated file reads within inherited validators remain; no one-read-per-file
claim is made. Untouched catalog/writer/test preparation also remains.

Canonical combined records/manifest digest is identical before/after:

| Package | SHA-256 |
|---|---|
| shared_target_declaration | `5b30b4aaec9c23311789be10df670f1a71256f909c05a36607fe58ddab8498cf` |
| shared_target_allocation | `222280eabff9703b3df7b750fb0d81182f511dbb33e46cc412f0596d8a268095` |
| shared_proposal_legality | `9e79bbc823a53d6cd91c5a9a48802cfb7f88beb8df8c5998668884f690f6c2d8` |

## Regression and gate record

The inventory is **2,436 → 2,459 tests**, with 23 new focused methods: six shared
stage boundary tests, seven diagnostic tests and ten finite preservation tests.
No existing method was removed. Two allocation/proposal preservation methods
were renamed from `test_every_inherited_source_and_evidence_file_remains_byte_identical`
to `test_historical_rows_and_authorized_current_implementation_match_exact_pins`.
They still enforce every original fixture row, requiring the exact original row
before a named successor check. Separate fixture-integrity tests retain their
original hashes/counts/rows. Changed implementation files are not byte-preserved.

Focused commands and observed results:

```sh
PYTHONPATH=src:tests python -m unittest test_shared_stage_validation test_shared_target_declaration_package test_shared_target_allocation_package test_shared_proposal_legality_package -v
# 50 tests, 28.715s, OK, zero skips/failures
PYTHONPATH=src:tests python -m unittest test_shared_stage_validation.SharedStageValidationTests.test_selected_review_root_is_honored_with_cold_and_warm_metadata -v
# strengthened all-predecessor-caches-cold/default-roots-absent case: 1 test, 0.739s, OK
PYTHONPATH=src:tests python -m unittest test_publication_validation_diagnostics -v
# 7 tests, 0.002s, OK
PYTHONPATH=src:tests python -m unittest test_validation_performance_preservation test_shared_target_allocation_preservation test_shared_proposal_legality_preservation test_shared_target_declaration_preservation test_shared_casting_stage_preservation test_gameplay_rules_bounded_activated_ability_preservation test_mana_stack_exception_preservation test_real_rules_execution_design_boundaries test_activated_ability_procedure_design.CanonicalPreservationTests -v
# 86 tests, 1.859s, OK, zero skips/failures
```

Complete local discovery passed **2,459 tests in 1,994.405s**, **11 explicit
source-dependent skips**, **zero failures/errors**, exit 0. Monotonic parent
elapsed time, including interpreter startup/teardown, was **1,997.248s**.
The unchanged standard runner command was:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

Local combined-log SHA-256:
`0581af910c11588418ef26a3c38e9454b85642ff3b6d1d6567f7df307cd28cbc`.
The eleven skips require absent owner-controlled source artifacts; they confer no
fresh source reproduction. All offline checks and existing meaningful coverage
ran. Local Python differs from historical hosted Python, so this local total is
not a controlled before/after full-suite comparison.

Full discovery still takes about 33 minutes locally. Minutes-long compatibility
and real-writer setup/repeat checks remain outside this optimization. These
observations do not establish that the owner's delivery-time problem is solved.

Final-head hosted push and PR discovery/publication gates are pending at this
committed checkpoint. Their exact checkout, count/skip/timing, publication,
readback, final commit/tree and draft PR URL belong in the PR completion record
once observed. Hosted publication uses the unchanged command:

```sh
PYTHONPATH=src:tests python tests/publication_validation_regression.py
```

The checkout's 384-card catalog and the writer-expanded 654-card catalog remain
distinct required states. No separate local full-publication run was launched;
both final-head hosted actual-publication gates must demonstrate the real path.
No earlier head pass may substitute for them.

An initial local timing launch exited 127 because `/usr/bin/time` was absent,
before launching discovery. The standard unittest command was then launched
under a monotonic subprocess timer. This is a launch failure, not a suite pass.

The diagnostic parser reads the unchanged actual `.git/catalog-admission-validation.log`
after publication, checks count/hash/status against the real result and counts
explicit skips. Test-only JSON distinguishes preparation, observed nested-suite
duration, publication call time and total integration time, and exposes actual
matching published/readback heads. Unavailable/ambiguous values fail diagnostic
consistency checks; nothing enters canonical identity or admission decisions.

## Changed file ledger

| Filename | Purpose |
|---|---|
| `docs/NEXT_TASK.md` | Append one exact operational status/policy suffix; preserve all historical bytes. |
| `docs/VALIDATION_PERFORMANCE_CAPACITY.md` | Single detailed measurement, preservation and validation report. |
| `scripts/profile_validation_capacity.py` | Reproducible subprocess timing and separate call profiling. |
| `src/gameplay_rules/retained_stage_validation.py` | Small shared retained-byte/manifest/own-domain validator. |
| `src/gameplay_rules/shared_proposal_legality/package.py` | Integrate shared validator; remove cold default-root dependency. |
| `src/gameplay_rules/shared_target_allocation/package.py` | Remove recursive declaration reconstruction; validate current history and private snapshots. |
| `src/gameplay_rules/shared_target_declaration/package.py` | Direct fresh historical validation, immutable contract bytes and private snapshots. |
| `tests/activated_ability_preservation.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/publication_validation_regression.py` | Actual-log consistency diagnostics, monotonic timing and readback heads. |
| `tests/shared_proposal_legality_preservation.py` | Compose the exact NEXT_TASK suffix with historical document adapters. |
| `tests/test_activated_ability_procedure_design.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/test_gameplay_rules_bounded_activated_ability_preservation.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/test_publication_validation_diagnostics.py` | Seven focused parser/hash/count/skip/ambiguity regression methods. |
| `tests/test_real_rules_execution_design_boundaries.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/test_shared_casting_stage_preservation.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/test_shared_proposal_legality_preservation.py` | Same distinction, exact current helper inventory and preserved document prefix. |
| `tests/test_shared_stage_validation.py` | Six focused cache/root/content/mutation/roundtrip boundary methods. |
| `tests/test_shared_target_allocation_preservation.py` | Separate original fixture rows from exact authorized successor checks; exact helper inventory. |
| `tests/test_shared_target_declaration_preservation.py` | Adapt historical inventory only for the explicitly enumerated helper/tool; unknown additions remain visible. |
| `tests/test_validation_performance_preservation.py` | Ten tamper, original-row/blob, path and finite-ledger methods. |
| `tests/validation_performance_implementation_changes.json` | Finite exact original Git and successor byte pins. |
| `tests/validation_performance_preservation.py` | Explicit successor checks, regular paths, exact additions and document suffix. |

## Preservation and unchanged scope

The finite implementation replacement ledger is
[`tests/validation_performance_implementation_changes.json`](../tests/validation_performance_implementation_changes.json).
It records exact canonical-base Git blob, SHA-256 and length plus exact replacement
SHA-256 and length, separately from unchanged historical evidence and fixture rows.
Historical fixture-integrity checks remain distinct from successor implementation
checks. The protected historical design script stays unchanged.

Authorized implementation replacements (these source bytes changed):

| Exact path | Original canonical Git blob | Original bytes / SHA-256 | Replacement bytes / SHA-256 |
|---|---|---|---|
| `src/gameplay_rules/shared_target_declaration/package.py` | `2d2b28a53dce6698c5d647ecf4dedd8db4c3b940` | 13710 / `2df44207f65ca7a31ca9bbf8c8d49e8f108396a460dc7969bf2c0930fe696b10` | 16299 / `5546e59226f0f4e37f69758ed317630024c1129d38de35f46ee111b30298f44a` |
| `src/gameplay_rules/shared_target_allocation/package.py` | `77a47ed30dd03ab40701f53a192bdea91018115d` | 15827 / `570497fe40b1bac70126ae6f4476321b6eaf21411c61b5d15907b6852dcc3310` | 17779 / `5f004be0b7079d0ec443289a62375e8b52ea77611abbbb9beee1092d6e4545dd` |
| `src/gameplay_rules/shared_proposal_legality/package.py` | `2fb9d02bd56b73560a27ca589b454b320e10d4ec` | 24363 / `637cecce22c99008618af4b963fc63f0712be63e9e241f60298e38a177e461dd` | 18983 / `5d4398147d5ce69aaab57a096cd6be1f042bc0be85fd5d82c4b214aad58811b2` |

All 160 existing gameplay evidence files across 23 directories, all 53 fixture
files (including seven historical protected-state fixtures), and the pinned
design tool independently match canonical Git bytes, blobs and modes. Fixture
contents/rows/counts/hashes did not change. Existing unrelated source files
continue requiring original bytes; only the named replacements use successor pins.
The ledger is pinned by SHA-256
`89fd37eb6f94182a118420ecdc8ed4aa52fd66d3f83c75fa1abb2a2c2e167322`.
Original values were reproduced locally from `git show bdccc4e9be2f6ff2aec7b5764baa022e15f51cfe:<path>`
and verified against each original Git blob, SHA-256 and length. The checks do
not require base Git objects in shallow hosted or disposable publication repos.


Current gameplay remains **91 distinct real source units / 13 projections / 7 of
8** members of the single 602.2b import. **601.2i remains missing**. No projected
rule, source anchor, dependency resolution, permission or execution capability is
added. Semantic closure remains OPEN; all ten activation responsibilities remain
OPEN / EXECUTION_BLOCKED; real execution remains BLOCKED.

Historical acquisition identity remains
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.
PR #204 package/projection identities remain respectively
`sha256:dc2e8b6ee1c79b8c6696f768317d7fa140e6130725ad4993cc0a5547517a3589`
and `sha256:cfe4da820b091ab63c9e8764003bdb689becc7af125fec712e386260f7b0f2a8`.
`source_policy_clearance=not_granted`; private retention, redistribution, free
service, commercial service and AI export remain NOT_ESTABLISHED.

No production admission/publication implementation, workflow trigger, validation
stage, timeout, source verifier, projection contract, identity domain, retained
schema, authored gameplay finding, catalog/product behavior, Card/Oracle semantics,
runtime, simulation or permission behavior changes.

Next rules planning uses coherent batches organized around useful reasoning
outcomes. Exact per-rule provenance does not require one PR per rule. This records
the policy only: no next milestone, source inspection or projection has begun.
