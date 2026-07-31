# MTGJSON Import Execution

> **Phase 100 — implemented. Architecture v12 remains unchanged.**

## Architecture assessment

Merged Phase 99 (`5410619`) is the verified baseline. The Canonical Repository remains the sole
source of truth. MTGJSON is the approved structured reference provider, and this milestone only
executes that provider against a caller-supplied local dataset. Candidates stop in a pending human
review queue: there is no canonical writer, automatic approval, or automatic promotion. Promotion
continues to require completed validation and independent review through the existing controlled
promotion boundary. No architectural defect requiring Project Architect approval was found.

## Execution workflow

```text
local AllPrintings JSON -> provider validation -> artifact registration
 -> dataset registration -> parsing -> deterministic mapping -> candidate generation
 -> candidate validation -> pending review queue -> STOP
```

`mtg-lab provider mtgjson import SOURCE --format json` performs the workflow. It never uses the
network and never downloads data. `SOURCE` must be an unmodified local MTGJSON AllPrintings JSON
artifact. A missing path reports that exact requirement and exits without creating evidence or
canonical state. Document validation also completes before any registration write.

## Validation and supported datasets

The executor validates semantic schema version text, ISO-8601 generation date, the AllPrintings
`data` object, Set and Card/Printing required fields, set-code consistency, unique printing UUIDs,
unique external printing identifiers, completeness, candidate uniqueness, deterministic hashes,
provenance, supported licensing, and dataset/artifact consistency. MTGJSON schema major 5 is the
minimum; later schema majors are accepted when they retain the validated AllPrintings shape, while
unknown fields are preserved by mapping. Malformed, empty, older, non-JSON, or structurally
incompatible datasets are rejected before state changes.

Unsupported scenarios include URLs, network acquisition, automatic downloads, archives, partial
per-set files lacking the AllPrintings shape, canonical creation, automatic review or approval,
promotion, simulation, AI providers, and product- or MB2-specific behavior.

## Candidate generation

Mapping deterministically emits Card, Printing, Set, Language, Rarity, Finish, and Identifier
candidates. Each record contains a deterministic identifier and SHA-256 hash, mapped and retained
unknown fields, provider/artifact provenance, source dataset, `validated` validation state,
`pending` review status, deterministic confidence, and acquisition metadata. Dataset and artifact
identities are content-addressed, so importing identical bytes is repeatable.

## Review lifecycle and promotion boundary

`mtg-lab provider mtgjson candidates [--dataset ID] --format json` reads generated candidates.
`mtg-lab provider mtgjson review [--dataset ID] --format json` reads the pending review queue.
Import never changes a status from `pending`; all candidates have zero automatic approvals.
Independent reviewers must use the separately governed review and promotion processes. This
executor exposes no promotion operation and writes nothing below `data/canonical`.
