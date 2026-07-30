# Phase 66 Evidence Acquisition Packet

> **Status: Reference** — retained intake contract for future externally acquired MB2
> evidence. Its original PR #18/Phase 66 status narrative is historical: Phase 67 later
> delivered one mechanically reviewed product-title artifact, but it did not satisfy
> any unresolved outcome-affecting rule need. Current authorization is defined only by
> `ROADMAP.md`, `SESSION_STATE.md`, and `NEXT_TASK.md`.

**Original status:** Evidence-waiting. The PR #18 raw research handoff contained no
acquired external evidence artifacts, and Phase 66 processing had not begun.

**Purpose:** Define a controlled external-evidence handoff for Mystery Booster 2
pack topology and selection semantics when the Codex environment cannot reliably
retrieve live Wizards, Scryfall, archive, or community sources.

The packet is an intake contract, not evidence. A filled manifest without the
declared artifact bytes supports no claim. Codex must not fabricate a capture,
substitute remembered web content, or treat an inaccessible URL as evidence.

The current raw handoff under
`data/raw/magic/mystery_booster_2/phase_66/handoffs/` contains an
empty-artifact manifest, an empty artifact directory, and a research summary of
failed acquisition attempts and source leads. It does not satisfy the entry
gate. Phase 66 evidence verification is authorized only after a future handoff
is artifact-bearing, content-complete, and independently reviewed as specified
below. That authorization is limited to verification and research reconciliation;
canonical population and all downstream implementation remain unauthorized.

## 1. Required evidence questions

The external researcher should seek explicit evidence for each question and
record “not found” rather than infer an answer.

1. How many cards are in one booster for each documented product version?
2. How many selection events or logical Slots compose that booster, and how is
   each event identified?
3. What is the purpose of each event (for example, a defined pool, treatment,
   frame class, or other product-defined role)?
4. How many draws occur in each event?
5. Which Cards or Printings are eligible for each event?
6. What establishes each pool boundary and its completeness?
7. What weights, ratios, rarity bands, or documented frequency classes apply?
8. Are multiple draws made with or without replacement, and at what scope?
9. How are treatments and frames selected and represented in eligible outcomes?
10. Are any selections conditional, mutually exclusive, optional, or replacements
    for another selection?
11. Are selections correlated or sequenced, including dependencies within a pack
    or across packs in a box, display, or case?
12. Do rules differ by product version, release, region, language, channel,
    packaging, or production run?

## 2. Source priority and claim limits

Use the highest available category and retain lower-priority corroboration or
conflict evidence. Authority classification does not expand what an artifact
actually says.

| Priority | Source category | Claims it may support | Claims it may not support without explicit content |
| ---: | --- | --- | --- |
| 1 | Official Wizards product pages | Product identity/version, advertised card count, described pack components, named treatments, explicitly stated frequencies | Complete pools, exact weights, replacement, independence, or manufacturing collation merely because a product is described |
| 2 | Official Wizards announcements and articles | Dated product/version statements, component explanations, treatment or slot descriptions, corrections | Unstated pool completeness, exact odds, or continued applicability to later versions |
| 3 | Official card galleries or checklists | Printing identity, enumerated membership, treatment/frame attributes, and complete pool boundaries only when the source expressly declares completeness and scope | Pack topology, weights, replacement, or assignment to a Slot from mere gallery membership |
| 4 | Official packaging or instruction materials | Version-specific pack count, selection roles, advertised odds/frequency classes, warnings, and regional/language distinctions visible on the artifact | Rules hidden from the supplied panels/pages; extrapolation to different packaging or production runs |
| 5 | Archived first-party material | The first-party claims visible in the preserved capture at its archived time, with archive provenance | Authenticity beyond the archive record, live-current status, omitted linked content, or facts not visible in the capture |
| 6 | Well-documented community research | Reproducible hypotheses, reconstructed pools, documented frequency models, conflict discovery, and leads to primary evidence | Official intent or exact/comprehensive collation unless methods, sample, uncertainty, and independent corroboration justify the bounded claim |
| 7 | Observed opening datasets | Empirical outcomes for the documented sample, observed co-occurrence, falsification of impossible-outcome claims, and statistical estimates with uncertainty | Exact weights, full support, independence, replacement, or universal production behavior from finite observations alone |

Scryfall or another database is classified by the actual artifact and publisher,
normally community research/data rather than an official Wizards source. A URL,
search-result excerpt, paraphrase, or screenshot without sufficient context does
not inherit the authority of the underlying page.

## 3. Required intake metadata

For every externally supplied artifact, the intake manifest must contain:

- proposed stable Source Record ID;
- source title;
- publisher;
- original URL;
- access date in `YYYY-MM-DD` form;
- artifact filename;
- media type;
- exact file size in bytes;
- lowercase SHA-256 digest of the supplied bytes;
- authority classification using the priority categories above;
- exact claims supported, stated narrowly rather than as a topic label;
- precise locators such as page, heading, paragraph, table row, image panel, JSON
  Pointer, timestamp range, or dataset columns and row range;
- known limitations, including missing context and version scope; and
- conflict notes naming any contradictory artifact or stating that none is known.

Each artifact must also declare acquisition method, product-version scope, and
whether it contains personal data or redistribution restrictions. These safety
fields do not replace the required claim metadata.

## 4. Artifact directory plan

External evidence must first be handed off under a non-canonical raw intake path:

```text
data/raw/magic/mystery_booster_2/phase_66/handoffs/<handoff_id>/intake-manifest.json
data/raw/magic/mystery_booster_2/phase_66/handoffs/<handoff_id>/artifacts/<artifact_filename>
```

`<handoff_id>` and filenames must be lowercase stable path segments containing
only ASCII letters, digits, dots, underscores, and hyphens. The handoff directory
is quarantined input: its presence does not register a Source Record, verify a
claim, or authorize processing.

After Phase 66 begins, Codex may verify the declared bytes and prepare reviewed
Evidence Repository bundles at:

```text
data/sources/magic/<bundle_id>/manifest.json
data/sources/magic/<bundle_id>/files/<archived_filename>
```

Only subsequently derived research artifacts belong at:

```text
data/intermediate/research/mystery_booster_2/phase_66/rule-claim-matrix.json
data/intermediate/research/mystery_booster_2/phase_66/evidence-sufficiency-report.json
```

Canonical domain paths under `data/canonical/` are forbidden during Phase 66.
Raw intake must never be moved or copied into canonical paths, and processed
research must never be presented as archived source bytes.

## 5. Intake manifest template

The complete machine-readable fill-in template is retained at:

```text
docs/templates/phase_66_external_evidence_intake.template.json
```

Place a completed copy at the handoff path. Replace every angle-bracket
placeholder, preserve one artifact entry per supplied file, and do not delete a
required field. `claims_supported` may be empty only when the artifact is supplied
solely to document a conflict or failed lead; explain that purpose in limitations.

## 6. Claim-to-evidence checklist

| Current Rule Claim Matrix entry | Current state | Evidence needed to improve classification | Improvement gate |
| --- | --- | --- | --- |
| `mb2.rule.card-pool.membership.partial` | Incomplete | Version-scoped official gallery/checklist or rigorously documented complete enumeration; Printing identifiers and treatment/frame attributes; explicit pool-to-event assignment | Every eligible Printing and exclusion boundary is evidenced for each pool; isolated membership examples do not qualify |
| `mb2.rule.collation.dependencies` | Unsupported | Explicit first-party collation statement or sufficiently documented opening data capable of testing conditionality, correlation, mutual exclusion, and sequence, including sampling unit and product version | Supported behavior and uncertainty are stated; absence of observed correlation is not proof of independence |
| `mb2.rule.pack.structure` | Unsupported | Version-specific first-party page, article, packaging, or instructions stating total card count and complete component/event composition | Total draws reconcile exactly with the described booster and version scope |
| `mb2.rule.print-sheet.entries-and-weights` | Unsupported | Complete event-specific entry lists plus explicit relative weights, ratios, odds, frequency classes, or a documented inference methodology with uncertainty | Completeness and weight meaning are evidenced separately; equal weights are never assumed |
| `mb2.rule.probability.distribution` | Unsupported | All topology, pools, weights, replacement, treatments, and dependency claims required to derive a distribution | Remains unsupported until every outcome-affecting upstream claim is adequate and normalized probabilities can be validated |
| `mb2.rule.replacement.behavior` | Unsupported | Explicit draw-with/without-replacement statement or evidence strong enough to establish the rule at each multi-draw scope | Must cover every multi-draw event; “duplicates observed/not observed” alone is insufficient |
| `mb2.rule.slot.definitions` | Unsupported | Complete selection-event names/roles, draw counts, pool mappings, and version scope | Every event maps to an evidenced pool and the event draw counts reconcile to pack size |
| `mb2.rule.treatment.selection` | Unsupported | Official descriptions/checklists or documented research mapping frame/treatment classes to events and frequencies, including replacements or exclusivity | Printing attributes are distinguished from pack-selection rules and all treatment paths are accounted for |

`mb2.rule.product.identity` is already confirmed. New artifacts may narrow its
version scope or reveal distinctions, but identity evidence alone does not improve
any selection claim.

## 7. Minimum viable evidence threshold

The smallest meaningful package is not a minimum file count. It is the smallest
set of mutually consistent, version-scoped artifacts that collectively provides:

1. **Pack topology:** total card count, the complete set of logical selection
   events, each event's purpose and draw count, and reconciliation of event draws
   to the total.
2. **Pool mapping:** an evidenced definition of which pool serves every event and
   whether each boundary is complete, even if exhaustive Printing population is
   delegated to a later milestone.
3. **Replacement semantics:** explicit replacement behavior for every event with
   more than one draw, plus the scope of any cross-event restriction.
4. **Architectural behavior:** explicit disclosure of any conditional, mutually
   exclusive, correlated, or sequenced selection; alternatively, enough source
   language to state only the independent behavior it actually guarantees.
5. **Treatments and versions:** treatment/frame paths and the exact product version
   to which all statements apply.

This threshold permits Phase 66 to determine pack topology, replacement
semantics, and Tier 0 fit. Canonical Slot and Print Sheet population may begin
only if every Slot role, draw count, pool boundary, pool mapping, weight or
frequency semantics, replacement rule, treatment path, and outcome-affecting
dependency is sufficiently supported. If topology is known but weights or
complete pool entries are not, Slot/Print Sheet population remains blocked even
though the architectural-fit determination may be meaningful.

## 8. Mandatory stop conditions

Phase 66 must stop at the affected claim boundary, record the unresolved or
conflicting state, and request a new evidence handoff when:

- required evidence is absent;
- a cited source or supplied artifact is inaccessible;
- evidence proves Printing membership but not pack eligibility or collation;
- observations cannot establish exact weights or documented frequency classes;
- sources conflict and scope, version, or authority does not resolve the conflict;
- behavior cannot be represented by the current Tier 0 model;
- a file's size or SHA-256 differs from its manifest;
- a locator cannot be independently resolved in the supplied bytes; or
- product-version distinctions cannot be reconciled.

Stopping does not authorize an inference. In particular, Phase 66 must not infer
equal weights, independent draws, replacement, complete pools, or applicability
across product versions.

## 9. Recommended external research handoff procedure

1. The repository owner assigns a stable `<handoff_id>` and gives the external
   researcher this packet and the JSON template.
2. The researcher works outside Codex, follows source priority, downloads original
   bytes rather than supplying paraphrases, and records inaccessible or dead links
   as failed leads rather than reconstructed captures.
3. The researcher computes byte size and SHA-256 locally, fills all metadata and
   narrow claim/locator fields, and records contradictions and version scope.
4. A second human reviewer opens each artifact, checks every locator, verifies the
   digest, and confirms that the stated claim does not exceed the visible content.
5. The completed manifest and exact files are placed under the raw handoff paths;
   no files are placed in `data/sources/`, `data/intermediate/`, or `data/canonical/`.
6. After explicit Phase 66 approval, Codex verifies paths, bytes, digests, metadata,
   and locators before registering sources or constructing Evidence Repository
   bundles. Verification failure triggers a stop and a corrected handoff request.
7. Codex reconciles only verified claims into new processed research artifacts,
   reports whether the minimum threshold is met, decides evidenced Tier 0 fit,
   and stops without canonical population or engine implementation.
