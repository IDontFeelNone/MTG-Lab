# Phase 66 Mystery Booster 2 external-evidence research handoff

**Handoff ID:** `phase_66_external_research_20260730`
**Prepared:** 2026-07-30
**Status:** Controlled research package; no external artifact bytes acquired
**Decision:** Evidence acquisition is incomplete and every outcome-affecting rule remains blocked.

## 1. Scope and evidence boundary

This handoff applies only to the English-language Mystery Booster 2 product as
sold through the 2024 MagicCon: Las Vegas / Festival in a Box channel unless a
future artifact explicitly establishes a broader scope. It does not silently
extend a statement to another language, region, channel, packaging format, or
production run.

The repository evidence-acquisition contract requires exact bytes, size,
SHA-256, narrow claims, and resolvable locators. The current execution
environment returned HTTP 403 for direct requests to Wizards and GitHub, and the
web research service returned HTTP 401. Accordingly:

* no external page, gallery, dataset, image, video, or packaging artifact was
  directly acquired in this handoff;
* no search snippet, remembered page content, URL, or existing paraphrase is
  promoted as evidence;
* `intake-manifest.json` intentionally contains an empty `artifacts` array; and
* the `artifacts/` directory is intentionally empty pending manual acquisition.

This is a completed **draft intake**, not a verified evidence bundle. A URL in
this report is a lead, not evidence that the linked content says anything.

## 2. Research summary

### Directly acquired evidence

None. The access failures prevent content verification and exact-file
preservation. The repository's pre-existing title-only capture was reviewed as
context but is not duplicated into this raw handoff. It proves product identity
only and cannot support topology or selection semantics.

### Evidence located but not preserved

The following high-priority targets were identified from repository Source
Records and bounded URL discovery. Their content was not accessible in this
session, so titles other than existing repository titles are descriptive rather
than asserted verbatim.

| Proposed Source Record ID | Source title | Publisher | Original URL | Access date | Authority | Acquisition method | Version scope | Exact claims currently supported | Target locators | Limitations / conflict notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `wizards-mb2-product-page-phase-66` | Mystery Booster 2 product page | Wizards of the Coast | https://magic.wizards.com/en/products/mystery-booster | 2026-07-30 | Official Wizards product page | Manual browser save plus full-page PDF | To be established from page and capture | **None until preserved.** Candidate lead for advertised pack count, named components, product/channel distinctions, and treatments. | Product overview; booster-contents section; product-details section; legal/footer date | HTTP 403 here. Existing repository capture contains title only. Page description cannot prove pools, weighting, replacement, or dependencies unless explicit. No conflict assessed. |
| `wizards-mb2-card-gallery-phase-66` | Mystery Booster 2 Card Image Gallery | Wizards of the Coast | https://magic.wizards.com/en/products/mystery-booster/card-image-gallery | 2026-07-30 | Official card gallery/checklist | Save rendered HTML, export PDF, and export any page JSON/API payload | Gallery version/date to be recorded | **None until preserved.** Candidate lead for enumerated Printing identities and visible frame/treatment attributes. | Gallery heading and filters; every card tile; collector numbers; pagination/lazy-load boundary; embedded data | HTTP 403 here. Gallery membership alone does not prove slot eligibility, pool completeness, weights, replacement, topology, or collation. No conflict assessed. |
| `wizards-mb2-collecting-article-phase-66` | Official Mystery Booster 2 collecting/product article (exact title pending) | Wizards of the Coast | https://magic.wizards.com/en/news | 2026-07-30 | Official Wizards announcement or article | Locate through official news search; save rendered HTML and PDF | Article publication date and named release | **None until located and preserved.** Candidate lead for rarity/frequency classes, treatments, foil/replacement language, and product version. | Exact article URL; publication/update date; headings discussing booster contents, treatments, and odds | No exact article URL was content-verified. Do not reconstruct the article from memory. Potential conflict with packaging or later corrections must be retained. |
| `wizards-mb2-packaging-phase-66` | Mystery Booster 2 sealed booster/display packaging | Wizards of the Coast / contracted printer | Physical package; product page image URL to be recorded | 2026-07-30 | Official packaging or instructions | Photograph every panel at readable resolution; preserve original camera files | Exact SKU, region, language, channel, lot/production marks | **None until supplied.** Candidate lead for card count, contents, odds, legal version, and SKU distinctions. | Booster front/back/seam; display bottom/back/sides; barcode/SKU; lot code; contents and odds panels | Physical sample unavailable. Packaging may advertise categories without defining logical events or exact odds. Differences among lots must not be silently merged. |
| `wayback-wizards-mb2-product-phase-66` | Archived Wizards Mystery Booster 2 product page | Wizards of the Coast via Internet Archive | https://web.archive.org/web/*/https://magic.wizards.com/en/products/mystery-booster | 2026-07-30 | Archived first-party material | Download WARC or replay HTML plus archive metadata | Each archived timestamp separately | **None until preserved.** Candidate corroboration for dated first-party wording and revisions. | Replay timestamp; archived URL; page headings; missing-resource list | Archive and network inaccessible here. Archive capture does not prove live-current status and may omit scripts/images. |
| `scryfall-mb2-set-export-phase-66` | Mystery Booster 2 set records | Scryfall | https://scryfall.com/sets/mb2 | 2026-07-30 | Well-documented community data | Export API JSON with response headers and pagination | Scryfall dataset timestamp; MB2 set code | **None until preserved.** Candidate support for a community enumeration of Printing records and recorded rarity/frame/finish fields. | Set metadata; `/cards/search` query; every page; `total_cards`; collector number, rarity, frame, finishes | HTTP 403 here. Database membership is not official slot eligibility or completeness and does not establish weights, replacement, topology, or dependencies. |
| `community-mb2-collation-study-phase-66` | Reproducible Mystery Booster 2 collation study (not yet identified) | Pending | Pending | 2026-07-30 | Well-documented community research | Preserve article/notebook/source data and methodology | Exact sampled product version/lots | **None.** A qualifying source could support bounded hypotheses or frequency estimates with uncertainty. | Method, sample unit, raw observations, exclusion rules, analysis code, confidence intervals | No qualifying study was found or acquired. Commentary without raw data is insufficient. |
| `observed-mb2-openings-phase-66` | Mystery Booster 2 pack-opening dataset (not yet identified) | Pending | Pending | 2026-07-30 | Observed opening dataset | Export structured rows and preserve source videos/photos with timestamps | Exact boxes, packs, lots, channel, region, language | **None.** A qualifying dataset could prove only outcomes in its documented sample and estimate frequencies. | One row per pack/card; box/pack order; timestamps; collector number/treatment; missing/ambiguous observations | No dataset was acquired. Finite openings cannot prove complete support, universal collation, exact weights, independence, or replacement. |

### Conclusions supported by evidence

Only the repository's already-retained conclusion remains available: Mystery
Booster 2 product identity is confirmed, while four bounded Printing-membership
examples are partial. This handoff adds no verified external factual claim about
pack contents or selection semantics.

## 3. Claim-by-claim assessment

The classifications below reflect **preserved evidence**, not likely product
behavior and not unverified descriptions encountered elsewhere.

| Rule Claim Matrix category | Classification | Assessment |
| --- | --- | --- |
| Pack structure | **unsupported** | No newly preserved version-specific artifact states a total card count and complete event composition. No draw-total reconciliation is possible. |
| Slot definitions | **unsupported** | Event names, roles, draw counts, and pool mappings have not been preserved. Physical positions must not be assumed to equal logical Slots. |
| Card-pool membership | **incomplete** | The pre-existing repository supports four bounded membership examples. No complete, event-specific eligible Printing pool or exclusion boundary is established. Gallery membership must not be treated as slot eligibility. |
| Print Sheet entries and weights | **unsupported** | No complete event-specific entry list, relative weight, rarity band, odds statement, or documented inference methodology was acquired. Equal weighting and literal physical sheets are not inferred. |
| Replacement behavior | **unsupported** | No artifact states with- or without-replacement behavior within an event or across events. Duplicate observations, if later acquired, would not alone settle the rule. |
| Treatment selection | **unsupported** | No acquired artifact maps frames, finishes, borders, playtest status, or other treatments to selection events or frequencies. Printing attributes are not selection rules. |
| Collation dependencies | **unsupported** | Conditionality, mutual exclusion, correlation, ordering, and within-box sequencing are all unknown. Independence is not inferred. |
| Probability distribution | **unsupported** | Topology, pools, weights, replacement, treatments, and dependencies are unresolved, so no normalized outcome distribution is derivable. |

No category is classified `confirmed`, `corroborated`, `conflicting`, or
`inferred` by this handoff. There is no preserved source conflict to adjudicate;
absence of a detected conflict is not evidence of agreement.

## 4. Architectural-fit assessment

The current relation is:

```text
Product -> Slot -> Print Sheet -> Printing -> Card
```

It can represent the already-supported facts: one Product identity and bounded
Printing membership. Because no selection behavior was acquired, fit for the
complete product remains **indeterminate**. In particular:

* a logical event that draws from one weighted pool appears structurally
  compatible, but this is a model observation, not an MB2 finding;
* no evidence establishes that every MB2 event maps to exactly one Print Sheet;
* no evidence establishes whether conditions, mutual exclusions, correlated
  selections, event order, or cross-pack sequences exist; and
* therefore this package neither approves nor proposes a Tier 0 redesign.

Codex must repeat the fit decision only after artifacts establish the actual
selection graph. Any evidenced behavior not representable by the current
single-sheet Slot contract is a stop condition requiring separate review.

## 5. Minimum-evidence sufficiency

| Decision | Result | Reason |
| --- | --- | --- |
| Determine pack topology | **No** | Total count, complete events, purposes, and reconciled draw counts are absent. |
| Determine replacement semantics | **No** | Every possible multi-draw and cross-event scope is unresolved. |
| Determine Tier 0 architectural fit | **No** | Outcome-affecting conditional, correlated, exclusive, or sequenced behavior is unknown. |
| Ready for canonical Slot population | **No** | Complete event definitions, pool mappings, replacement, treatments, and dependencies are absent. |
| Ready for canonical Print Sheet population | **No** | Complete event-specific entries and evidenced weight/frequency semantics are absent. |

The Phase 66 minimum viable evidence threshold is not met. Canonical population,
probability work, simulation, and Tier 0 changes remain blocked.

## 6. Artifact acquisition plan

These are exact files a human researcher should supply. Filenames are stable
recommendations; after download, the manifest must record the actual byte size,
SHA-256, media type, acquisition method, version scope, claims, and locators.

| Recommended filename | Media type | Original source | Why needed | Expected locator | Redistribution/copyright concerns |
| --- | --- | --- | --- | --- | --- |
| `wizards-mb2-product-page-20260730.html` | `text/html` | https://magic.wizards.com/en/products/mystery-booster | Preserve first-party product wording and page metadata. | Contents/product-details headings and exact paragraphs; capture date. | Wizards copyrighted page; retain for research/audit, avoid republishing beyond necessary access. |
| `wizards-mb2-product-page-20260730.pdf` | `application/pdf` | Same | Preserve rendered/lazy-loaded content and visual relationships omitted from raw HTML. | PDF page numbers plus headings. | Same; generated PDF should retain source URL/date. |
| `wizards-mb2-card-gallery-20260730.html` | `text/html` | https://magic.wizards.com/en/products/mystery-booster/card-image-gallery | Preserve official enumeration shell, filters, and embedded data references. | Gallery headings, filters, card tiles, pagination. | Card images and page are copyrighted; restrict redistribution. |
| `wizards-mb2-card-gallery-20260730.pdf` | `application/pdf` | Same | Give reviewers stable visual locators for rendered gallery entries. | Page and card tile/collector number. | Potentially large copyrighted image compilation; internal evidentiary use only. |
| `wizards-mb2-card-gallery-data-20260730.json` | `application/json` | Exact gallery data endpoint discovered in browser developer tools | Preserve complete machine-readable entries and pagination boundary if the gallery uses an API. | JSON Pointers; response URL; request parameters; page count. | Respect site terms; do not bypass access controls. Preserve response headers separately. |
| `wizards-mb2-collecting-article-20260730.html` | `text/html` | Exact Wizards news URL, once located | Candidate first-party detail on treatments, frequency classes, replacements, and versions. | Publication/update date and exact relevant headings/paragraphs. | Wizards copyrighted article; archive for audit, quote minimally. |
| `wizards-mb2-collecting-article-20260730.pdf` | `application/pdf` | Same | Stable rendered reference and page locators. | PDF pages corresponding to relevant headings. | Same. |
| `wizards-mb2-booster-front.jpg` | `image/jpeg` | Physical English booster | Establish visible SKU/version and front claims. | Entire front, color target/ruler in frame. | Packaging art copyrighted; original photo ownership and internal use should be recorded. |
| `wizards-mb2-booster-back.jpg` | `image/jpeg` | Physical English booster | Capture card-count, contents, legal, barcode, and odds text. | Entire back at readable resolution. | Avoid personal/location metadata; retain original EXIF only if needed and disclose it. |
| `wizards-mb2-display-panels.zip` | `application/zip` | Physical sealed display | Capture every display panel, barcode, SKU, and lot/production codes. | Manifest listing each photo and panel. | Packaging art copyrighted; ZIP must not hide undocumented files or personal metadata. |
| `wayback-wizards-mb2-product.warc.gz` | `application/warc` | Internet Archive replay of product page | Preserve dated first-party page plus archive provenance and dependent resources. | WARC target URI/date records and replay timestamp. | Internet Archive and Wizards terms apply; redistribution review required. |
| `scryfall-mb2-set-20260730.json` | `application/json` | https://api.scryfall.com/cards/search?q=set%3Amb2&unique=prints | Community Printing enumeration and attributes for comparison, not official collation. | Response pages and each `data` row; headers; `total_cards`. | Scryfall data/license and bulk-data guidelines apply; record retrieval headers/date. |
| `mb2-opening-observations.csv` | `text/csv` | Identified pack-opening corpus | Permit bounded tests of co-occurrence and frequency while retaining sample limits. | Defined columns and one row per observed card with pack/box/order identifiers. | Obtain dataset permission; avoid participant personal data; videos remain copyrighted. |
| `mb2-opening-methodology.md` | `text/markdown` | Dataset author/researcher | Make sampling, transcription, exclusions, ambiguity, and uncertainty reviewable. | Headings for sampling unit, version, QC, missingness, analysis. | Prefer author-written methodology; attribute third-party text. |

A researcher should also preserve HTTP response headers, request URLs/parameters,
redirect chain, and capture logs where practicable. Screenshots alone are not a
substitute for downloadable structured data or complete contextual pages.

## 7. Failed leads and access failures

1. Direct HTTPS requests to the Wizards product page, likely article paths, and
   gallery returned proxy `403 Forbidden`; no bytes were captured.
2. The integrated web search/retrieval service returned `401 Unauthorized`; no
   search results were used as evidence.
3. Direct GitHub/raw GitHub access returned proxy `403 Forbidden`, preventing an
   independent review of the public repository beyond the checked-out files.
4. Internet Archive replay/WARC material was not accessible from this
   environment.
5. No content-complete official packaging photographs were available locally.
6. No reproducible community collation study with raw observations, methods, and
   version metadata was identified or acquired.
7. No opening dataset suitable for testing dependencies or frequency estimates
   was acquired.

## 8. Unresolved questions

All twelve evidence questions in the acquisition packet remain open, including:

* exact card total per product version;
* complete logical event count, identity, purpose, and draw count;
* pool-to-event mapping and pool completeness;
* eligible Printing identities and treatment/frame attributes;
* relative weights, rarity bands, odds, and meaning of any frequency language;
* replacement scope within and across events;
* whether a treatment is a dedicated event, a replacement, or an attribute of
  an eligible Printing;
* conditions, mutual exclusions, correlations, order, and cross-pack sequencing;
* differences by channel, packaging, region, language, SKU, or production run;
* whether an advertised component list describes logical selection events or
  only consumer-facing categories; and
* whether any complete evidenced behavior exceeds the current single-sheet Slot
  contract.

## 9. Manual completion and verification instructions

1. Acquire the highest-priority official files first without bypassing access
   controls. Record the exact final URL, redirects, UTC acquisition timestamp,
   and product/SKU scope.
2. Save original response bytes and a rendered PDF where dynamic content makes
   both useful. Never edit source bytes to improve readability.
3. Compute `wc -c` and `sha256sum` for every supplied file and insert the exact
   results into `intake-manifest.json`.
4. Add one artifact entry per file. State only claims visible in that file and
   use independently resolvable locators. A companion PDF and HTML may
   corroborate one another but must remain separate artifacts.
5. For packaging, photograph every panel and include SKU, barcode, language,
   region, and lot identifiers. Retain original files; disclose or remove
   personal EXIF only through a documented derivative workflow.
6. For galleries/API exports, capture all pagination and query parameters.
   Separate Printing membership/attributes from event eligibility.
7. For community/opening data, require raw observations, sampling unit, product
   version, box/pack order when known, transcription QC, exclusions, and methods.
8. Retain conflicts rather than selecting a preferred account. Narrow scope if a
   later correction, packaging version, or production run explains a difference.
9. Have an independent reviewer open every file, verify each locator and digest,
   and fill `reviewed_by` / `reviewed_at`.
10. Place files only in this handoff's `artifacts/` directory. Do not write to
    `data/sources/`, `data/intermediate/`, or `data/canonical/`. Codex must verify
    the intake before any later evidence registration or processing.

## 10. Required separation at handoff completion

* **Evidence directly acquired:** none.
* **Evidence located but not preserved:** the official product page, official
  gallery, an official collecting/product article still needing an exact URL,
  official packaging, archived first-party captures, Scryfall export, and a
  qualifying community/opening corpus.
* **Conclusions supported by evidence:** no new rule conclusion; only existing
  repository product identity and four bounded membership examples remain.
* **Unresolved claims:** every pack topology and selection-semantics category.
* **Files still manually required:** every file in the artifact acquisition
  table, prioritized from official product page/article/gallery/packaging down
  to documented community research and raw opening observations.
