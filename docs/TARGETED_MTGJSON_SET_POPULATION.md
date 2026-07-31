# Phase 105 — Targeted MTGJSON Set Population

> **Status: Stopped at the source gate — 2026-07-31. No supplied AllPrintings
> artifact was available.**

## Baseline and architecture assessment

The repository is based on merged Phase 104 commit `79dbfe5` (merge of bounded MTGJSON
canonical promotion). The Phase 104 implementation, its tests, typed projection, and governed
promotion boundary are present.

Architecture v12 remains unchanged and no frozen-contract defect was found. The Canonical
Repository remains the sole source of truth; MTGJSON remains non-canonical reference evidence;
canonical writes remain restricted to the existing governed Promotion Engine; and Typed
Canonical Projection remains the required bridge to downstream consumers. Phase 105 is intended
to target real records without product-specific runtime logic, automatic approval, unattended
promotion, standalone Set entities, or standalone Language entities.

## Source gate and discovery result

The task environment was searched for a caller-supplied `AllPrintings` artifact under
`/workspace` and `/tmp`. None was present. Repository JSON files are retained project data or
small test fixtures, not a caller-supplied immutable MTGJSON AllPrintings dataset. They must not
be substituted for the required real source.

Consequently, no source path, source SHA-256, MTGJSON generation metadata, licensing metadata,
artifact registration, or dataset registration exists for Phase 105. Discovery could not run,
so matching names, set codes, release dates, set types, card/Printing counts, languages,
finishes, identifiers, ambiguities, and actual dataset membership are **not determined** for
either requested target.

| Requested target | Discovery state | Selected set code | Extracted candidates |
| --- | --- | --- | ---: |
| Mystery Booster 2 | unavailable — source artifact missing | none | 0 |
| Marvel Super Heroes | unavailable — source artifact missing | none | 0 |

No deterministic selection rule is needed until discovery produces one or more matches. If
multiple records match a requested name, Phase 105 must require an explicit deterministic rule
before extraction; it must not guess a set code.

## Exact artifact request

Supply the immutable source as follows:

- **Accepted format:** uncompressed JSON (not a URL or archive).
- **Expected filename/path:**
  `/workspace/MTG-Lab/data/local/mtgjson/AllPrintings.json`; alternatively pass the local path
  as the positional `SOURCE` argument.
- **Expected schema:** MTGJSON AllPrintings-style JSON with top-level `meta` and `data` objects.
  `meta.version` must be semantic-version text (schema major 5 or a later compatible
  AllPrintings shape), `meta.date` must be an ISO-8601 generation date, and each set must have a
  matching non-empty `code`, non-empty `name`, and `cards` array.
- **Required metadata:** generation version/date in `meta`; caller-supplied expected SHA-256;
  and licensing/attribution metadata sufficient to register MTGJSON reference use under the
  repository's supported CC BY 4.0 policy. The file must be the immutable bytes to be reviewed,
  not regenerated or edited during execution.
- **Validation command:**
  `PYTHONPATH=src python -m mtglab provider mtgjson validate /workspace/MTG-Lab/data/local/mtgjson/AllPrintings.json --sha256 <LOWERCASE_SHA256> --format json`

The caller should create `data/local/mtgjson/` locally if needed. The supplied artifact must not
be committed. Phase 105 can resume only after the validation command succeeds.

## Governed outcome

The stop condition was applied before generic importer work or canonical mutation. Candidate,
review, promotion, projection, and downstream-verification counts are all zero for this phase:

| Outcome | Mystery Booster 2 | Marvel Super Heroes |
| --- | ---: | ---: |
| Accepted candidates | 0 | 0 |
| Rejected candidates | 0 | 0 |
| Unresolved candidates | 0 | 0 |
| Duplicate/conflicting candidates | 0 | 0 |
| Unsupported mappings / explicit unknowns | 0 | 0 |
| Promoted Cards | 0 | 0 |
| Promoted Printings | 0 | 0 |

These zeroes mean **no Phase 105 batch existed**, not that either target has an empty card list.
No unrelated set was extracted or promoted. Existing canonical records are unchanged; therefore
there are no Phase 105 canonical or typed digests, replay results, Query/Analytics/Semantic/
Reasoning results, or `AIModelRequest` to report.

## Bounded completeness declarations

### Mystery Booster 2

- MTGJSON dataset membership: **incomplete / not assessed** because the artifact is absent.
- Canonical promotion: **incomplete; zero Phase 105 Cards and Printings promoted**.
- Product packaging, pack topology, print sheets, collation, probabilities, and market data:
  **unresolved**.

### Marvel Super Heroes

- MTGJSON dataset membership: **incomplete / not assessed** because the artifact is absent.
- Canonical promotion: **incomplete; zero Phase 105 Cards and Printings promoted**.
- Product packaging, pack topology, print sheets, collation, probabilities, and market data:
  **unresolved**.

## Remaining evidence requirements

Both targets require the requested immutable artifact, verified hash, compatible generation
metadata, licensing review, deterministic discovery, and independent per-candidate decisions.
Mystery Booster 2 additionally still requires qualifying evidence for membership and all
outcome-affecting packaging/collation claims. Marvel Super Heroes likewise requires discovered
dataset membership plus independent evidence for product packaging and any topology,
print-sheet, collation, probability, or market claims. MTGJSON membership alone would not prove
those product facts.

No target is marked populated. Implementation and merge are withheld; after a future resumed
implementation, merge must remain withheld until GitHub Actions are green.
