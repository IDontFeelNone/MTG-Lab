# Handoff

> **Phase 89 MTGJSON Provider Adapter v1 is implemented and awaiting review/green CI.**

The adapter is confined to `src/external_ingestion/mtgjson.py`; it detects and validates
MTGJSON v5 AllPrintings-style files, generates governed manifests, maps the approved bounded
field set, and composes the unchanged Phase 88 ingestion pipeline. The three `adapter` CLI
commands and a ten-card synthetic fixture cover successful, malformed, conflict, unsupported,
deterministic, and retry paths. Review `docs/MTGJSON_PROVIDER_ADAPTER.md` and the Phase 89
tests. No canonical data or full provider corpus was imported. Architecture v12 is unchanged.
Do not recommend merge until GitHub Actions are green.
