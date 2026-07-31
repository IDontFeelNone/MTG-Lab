> **Phase 109 records the first successful production dry run (`30649546787`).** Verified summary evidence records exact MB2/MSH discovery, 862 cards, 10,940 eligible candidates, 117 review-required identifier findings, 11 bounded batches, zero rejected/unresolved, and no canonical write or promotion. Missing candidate shards and streaming review-index packages make the batches non-reconstructable. The minimal workflow retention fix is present; another targeted dry run and green Actions are required. Stop after Phase 109 and do not approve or promote.

> **Phase 108B implemented over merged Phase 108A (`69b4feb`), official verification pending.** The reported Scryfall UUID collision cannot be classified from the unavailable corpus, so it is conservatively ambiguous/unsupported. Generic full-row diagnostics and narrow quarantine preserve all evidence and let unaffected planning continue. Architecture v12 and strict internal identities are unchanged. Merge/promotion are withheld pending green CI and an official dry run.

# Session State

> **Phase 108A implemented over merged Phase 107 (`4c7794d`).** Official download and checksum
> verification succeeded externally, but provider validation safely stopped at `deckboxId:2676`.
> The over-broad uniqueness assumption is corrected with deterministic scope-aware findings.
> Architecture v12, canonical contracts, promotion governance, and strict identities are unchanged.
> The official source artifact is unavailable in this environment, so the workflow rerun is pending.

> **Phase 107 implemented over merged Phase 106 (`456f2df`).** Architecture v12 and canonical
> authority are unchanged. A checksum-gated local command and manual workflow now deliver runner-
> temporary AllPrintings bytes into existing production preparation, reporting, one-batch reviewed
> promotion, projection, verification, and rollback. Hosted Codex again received HTTP 403, so the
> first real corpus run remains an explicit workflow operation and no substitute is claimed.

> **Phase 105 Official Reference Dataset Acquisition is implemented over merged Phase 104.**

MTGJSON AllPrintings can now be downloaded, resumed, verified, and registered beneath ignored
`data/local/` through JSON CLI commands. Tests mock all networking; no downloaded corpus is
committed. No provider import, candidate review, promotion, projection, downstream execution, or
canonical mutation is performed by this subsystem.

The deterministic five-entity MTGJSON-derived corpus has completed acquisition, validation,
independent review, promotion, typed projection, four read-layer consumers, non-executed AI
request, replay, rollback, and restore. Architecture v12 and promotion governance remain
unchanged; the rejected conflict remains outside canonical storage.

Architecture v12 is unchanged. A deterministic five-entity test corpus validates the
governed provider-to-canonical-to-AI-request path, including unknown, conflict, failure,
review, supersession, replay, and rollback behavior. No feature, canonical data, provider,
networking, model execution, or schema was added.

The repository should stop after this validation. Future work requires explicit milestone
approval; the recommended next boundary is a non-promoting large-corpus operational,
batching, performance, and recovery rehearsal.
