# Phase 135C MTGJSON checksum-sidecar repair

The official MTGJSON `AllPrintings.json.gz.sha256` response observed by the hosted pilot uses the
digest-only convention: one 64-hex SHA-256 value with an optional final newline, not a
filename-bearing record. Phase 135B required exactly two whitespace fields, so it misreported the
genuine one-field response as an unexpected filename. That run made one checksum request, zero
source requests, and no production write.

The bounded parser accepts digest-only, GNU text (`digest  AllPrintings.json.gz`), GNU binary
(`digest *AllPrintings.json.gz`), and BSD (`SHA256 (AllPrintings.json.gz) = digest`) forms. A
presented filename must be exactly `AllPrintings.json.gz`; URLs, credentials, absolute paths,
relative prefixes (including `./`), traversal, and alternate basenames are rejected. UTF-8 is
strict, the maximum is 1,024 bytes, and controls, NUL, extra lines, multiple digests, and malformed
syntax fail closed. Diagnostics retain only byte count, sidecar SHA-256, detected syntax, bounded
escaped text, candidate filename, and reason code—never corpus bytes. Source download remains after
parsing, and streamed source bytes must match the parsed SHA-256 before processing or retention.

---

# Phase 108B Scryfall identifier-collision policy

The official Phase 108A rerun advanced past Deckbox validation and reported `scryfallId` `0001e77a-7fff-49d2-a55c-42f6fdf6db08` more than once. The official artifact and its records are not available in this environment (direct access returned HTTP 403), so the only verified corpus evidence here is the workflow's namespace and value. Consequently, the collision is **classification 4: ambiguous or unsupported**, not a demonstrated exception to Scryfall global printing identity.

Validation still treats `scryfallId` as globally unique. A collision across different set-code, collector-number, or language coordinates remains fatal and now serializes every colliding record into the diagnostic. When distinct MTGJSON UUID rows share all three coordinates, validation cannot safely decide whether they are faces, aliases, duplicate rows, or supersession: it quarantines only their printing and identifier candidate closure, retains the raw artifact and a content hash plus full source inventory for each row, and requires review. No value is special-cased and no row is silently overwritten or deduplicated. MTGJSON UUID uniqueness remains fatal.

Each finding reports count, byte-identity by canonical source-record bytes, UUID difference, set/name/collector/language/rarity/finishes/layout/side/face/other-face fields, the complete identifiers object, source JSON path, hashes, disposition, and rationale. The next official dry run is the evidence gate for the actual records and may refine the classification in a later phase.

---

# MTGJSON Reference Dataset Provider v1

**Status:** Phase 108A identifier-scope validation implemented; local reference evidence only
**Architecture:** v12, unchanged

## Architecture and authority

The provider in `src/providers/mtgjson` is the first concrete implementation of the
Multi-Source Evidence Acquisition Framework. It discovers, validates, parses, maps, inspects,
and plans around a caller-supplied local JSON artifact. It performs no networking, download,
review, promotion, or canonical write. MTGJSON remains a Reference Dataset; the Canonical
Repository remains the only source of truth.

The provider reports the Phase 98 registration, planning, artifact-validation, and
dataset-validation capabilities. A plan expressly reports that networking, automatic download,
and canonical writes are disabled and independent review is required.

## Supported schema and entities

Version 1 accepts MTGJSON major-version 5, AllPrintings-style documents containing `meta` and
`data` objects. `meta.version` must be semantic-version text, `meta.date` must be ISO 8601, and
each set must contain matching `code`, non-empty `name`, and a `cards` array. The provider
prepares candidate records for Cards, Printings, Sets, Languages, Rarities, Finishes, and
Identifiers.

Product, sealed-product, booster, collation, price, rulings, legality, token, deck, inventory,
and product-specific entities are unsupported. They are neither inferred nor promoted.

## Deterministic mapping

Sets map code, name, and release date. Cards map normalized name, layout, colors, and mana cost;
Printings map UUID, card reference, set code, collector number, language, rarity, finishes, and
sorted identifiers. Languages, rarities, finishes, and identifiers become explicit reference
candidates. Candidate identifiers are SHA-256 identities over canonical compact JSON natural
keys, and output is sorted by candidate identifier.

Missing optional values remain explicit `{ "status": "unknown" }` values. Every unsupported
source field and its original JSON value is retained in `unknown_fields`; unsupported input is
never silently discarded. These mappings are candidates, not canonical entity mappings.

## Validation and licensing

Validation fails closed for malformed JSON, missing top-level structures, unsupported schema
majors, malformed dates, missing set/card identity fields, malformed identifier maps, duplicate
printing UUIDs, and duplicate printing-scoped external identifiers. Oracle identifiers may
repeat across printings because they identify a shared Card. Artifact contracts require JSON
media type, lowercase SHA-256, MTGJSON provider identity, and supported licensing. Dataset
contracts require MTGJSON major version 5, at least one artifact, supported entity declarations,
and supported licensing. `validate --sha256` verifies supplied bytes against an expected digest.

Provider policy records MTGJSON attribution and CC BY 4.0 assessment while conservatively
declaring local reference use and no redistribution. Operators remain responsible for verifying
the terms applicable to the supplied artifact; incomplete or unsupported framework licensing
metadata fails closed.

### External-identifier scope policy (Phase 108A)

The first official production dry run exposed the invalid former assumption that every non-Oracle
external identifier was globally unique: validation stopped at `deckboxId:2676` after download and
checksum verification, with `canonical_write: false`. Architecture v12 and canonical uniqueness
were not implicated. The provider now treats MTGJSON `uuid` as the strict global Printing identity;
`scryfallId` as an explicitly configured strict global external identity; `scryfallOracleId` and
legacy `oracleId` as Card-scoped identities; and `scryfallIllustrationId` as illustration-scoped.
All other and future namespaces default conservatively to non-unique external references.

Every key below is read dynamically from `cards[].identifiers.<namespace>` and retained on both its
Printing candidate and a distinct identifier candidate:

| Namespace/provider | Source field | Scope/guarantee | Former behavior | Phase 108A behavior |
|---|---|---|---|---|
| MTGJSON | `cards[].uuid` | global Printing; strict | fatal duplicate | fatal duplicate |
| Scryfall | `scryfallId` | global Printing; strict | fatal duplicate | fatal duplicate |
| Scryfall | `scryfallOracleId`, `oracleId` | Card-scoped; repeats across Printings | allowed | allowed within Card semantics |
| Scryfall | `scryfallIllustrationId` | illustration-scoped; art may repeat | fatal duplicate | allowed within illustration semantics |
| Deckbox | `deckboxId` | uniqueness not guaranteed | fatal duplicate | deterministic `review-required` finding |
| Card Kingdom | `cardKingdomId`, `cardKingdomFoilId`, `cardKingdomEtchedId` | uniqueness not guaranteed | fatal duplicate | deterministic `review-required` finding |
| Cardsphere | `cardsphereId` | uniqueness not guaranteed | fatal duplicate | deterministic `review-required` finding |
| Cardmarket | `mcmId`, `mcmMetaId` | uniqueness not guaranteed | fatal duplicate | deterministic `review-required` finding |
| Magic Online | `mtgoId`, `mtgoFoilId` | uniqueness not guaranteed by this adapter | fatal duplicate | deterministic `review-required` finding |
| Gatherer | `multiverseId` | uniqueness not guaranteed by this adapter | fatal duplicate | deterministic `review-required` finding |
| Arena | `mtgArenaId` | uniqueness not guaranteed by this adapter | fatal duplicate | deterministic `review-required` finding |
| TCGplayer | `tcgplayerProductId`, `tcgplayerEtchedProductId` | uniqueness not guaranteed | fatal duplicate | deterministic `review-required` finding |
| Any unlisted third party | `cards[].identifiers.<namespace>` | unknown/not guaranteed | fatal duplicate | fail-safe `review-required` finding |

Malformed names or values remain fatal. A non-fatal collision retains every value, Printing UUID,
set code, collector number, and JSON source location. Findings carry severity, code, namespace,
value, scope, affected records, dataset, explanation, and disposition. They are copied into the
review queue and delivery reports. They never authorize ambiguous resolution or canonical mapping.

## CLI and future promotion

All commands emit deterministic JSON:

```text
mtg-lab provider mtgjson validate PATH [--sha256 DIGEST] [--format json]
mtg-lab provider mtgjson inspect PATH [--format json]
mtg-lab provider mtgjson plan PATH [--format json]
```

Future promotion, if separately authorized, must register immutable artifacts and datasets,
complete validation and independent review, create a promotion candidate, and use the existing
Canonical Promotion Engine. Provider output can never promote itself.

## Phase 135 bounded pilot retention

The approved Phase 135 source is the official `https://mtgjson.com/api/v5/AllPrintings.json.gz`
publication (MTGJSON v5, gzip, `application/gzip` or `application/octet-stream`). MTGJSON is
attributed and assessed as CC BY 4.0; retaining the small attributed projection is compatible,
while the complete downloaded corpus remains staging-only and must not enter Git. The target is
exactly the ten names in `PILOT`, resolved with provider printing UUIDs and oracle identifiers;
MB2 and unrelated records are excluded.

Phase 135B repairs the production transport without changing that retention boundary. The client
identifies `MTG-Lab/Phase-135B (GitHub-Actions bounded printing acquisition)`, requests gzip or
octet-stream source bytes with identity content encoding, and separately requests the small
official `AllPrintings.json.gz.sha256` text sidecar once. It permits at most five HTTPS redirects
and only between `mtgjson.com` and `www.mtgjson.com`, then revalidates the final URL, HTTP 200,
media type, nonempty gzip framing, and SHA-256. The large dataset is requested exactly once and is
never included in diagnostics or artifacts; malformed sidecars, unsafe redirects, mismatch, 403,
timeout, and transport failures stop the run with bounded structured metadata.

Run from a provider-accessible environment, substituting an independently computed canonical
snapshot identity and the actual UTC acquisition instant:

```bash
PYTHONPATH=src python scripts/retain_pilot_printings.py \
  --run-id phase-135-mtgjson-YYYYMMDD-DIGEST \
  --canonical-snapshot sha256:DIGEST \
  --acquired-at YYYY-MM-DDTHH:MM:SSZ
```

The run retains exactly `acquisition-report.json`, `manifest.json`, and
`source-pilot-printings.json` under `data/evidence/phase-135/<run-id>/`. Publication uses staging
and atomic rename. Exact replay is accepted without overwriting; changed bytes under an existing
identity fail closed. Download, parse, validation, or publication failure removes staging and
leaves an existing directory untouched. This evidence does not authorize promotion: Phase 134
must be retried separately through its bounded review and promotion controls.

## Phase 135A hosted execution

After this implementation is merged, an operator manually dispatches **Pilot printing acquisition**
on `main` exactly once. The workflow uses run identity `mtgjson-pilot-<github-run-id>-<attempt>`,
invokes the Phase 135 CLI once, and never retains the complete `AllPrintings.json.gz` corpus in Git
or artifacts. Temporary provider bytes live outside the working tree and are removed by the
retention component. Durable output is only `acquisition-report.json`, `manifest.json`, and
`source-pilot-printings.json` beneath that run directory.

Before pushing, the workflow verifies ten-name scope, positive coverage for every name, non-MB2
rows, stable provider Printing UUIDs, zero missing/ambiguous/malformed/unsupported census values,
and false canonical-write, promotion, and fact-creation flags. It pushes a deterministic branch
without force, safely accepts only a byte-identical replay, and creates or reuses one exact open PR.
The PR remains open for manual census review and merge. Hosted network execution is intentionally
separate from Codex Cloud implementation; inability of the task shell to reach the provider does
not weaken or invalidate these controls. Merging retained evidence does not authorize promotion.
