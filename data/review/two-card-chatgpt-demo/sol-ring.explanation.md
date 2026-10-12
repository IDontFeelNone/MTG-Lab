# Sol Ring — retained-evidence explanation

Dossier: `sha256:0ef171213e50ed386cdd2bcec0a39fe5c396505f311a4a0c4c194d8a3521913d`. References below are JSON pointers into this dossier.

Verified facts

- Exact production Card: `6ad8011d-3471-4369-9d68-b264cc027487`; mana cost {1} (`/card_identity`, `/canonical_entity/canonical_values`).
- Retained Oracle text: {T}: Add {C}{C}. (`/evidence_sections/rules/oracle_text`).
- Retained printing coverage: 136 Printings; this is a bounded repository count (`/evidence_counts/retained_printings`).
- Scryfall supplied EDHREC ordinal rank 1 at 2026-08-04T21:10:15.879000Z. It is not a deck count (`/evidence_sections/demand_usage_evidence`).
- MTGJSON represented this Card in 241 of 3004 decoded provider deck files at 2026-08-10T22:23:35Z; this provider population is not global usage (`/evidence_sections/deck_usage_evidence`).
- 4 historical market observations cover 1 Printing, from 2026-08-02T09:09:45.851000Z to 2026-08-04T21:10:15.879000Z. They are provider market fields, not completed sales or current offers (`/evidence_sections/observed_price_evidence/summary`).

Deterministic descriptive calculations

- scryfall MB2 #233, foil, en, USD market: 64.18 → 64.04; absolute change -0.14, percentage change -0.218136%, over 216030 seconds (`/evidence_sections/historical_price_evidence/descriptive_movement_entries/0`).
- scryfall MB2 #233, nonfoil, en, USD market: 3.98 → 3.63; absolute change -0.35, percentage change -8.793970%, over 216030 seconds (`/evidence_sections/historical_price_evidence/descriptive_movement_entries/1`).

Supported interpretations

- These exact market dimensions support description of the retained historical movement only; their scope does not establish a forecast (`/evidence_sections/historical_price_evidence/history_readiness_state`).
- The two demand providers describe independent metrics and populations. An ordinal rank and provider-curated deck-file inclusion cannot be combined into global demand (`/evidence_sections/demand_usage_evidence/metric_semantics`, `/evidence_sections/deck_usage_evidence/population_semantics`).

Unknown or unsupported conclusions

- Current buyer offers and transaction costs, competitive rankings, best-in-slot comparisons, verified combos, forecasts, investment value, and acquisition recommendations are unsupported by this dossier (`/limitations`, `/permissions`).
- Printing and deck samples omit entries explicitly counted in `/omitted_item_counts`; complete raw provider corpora are not retained (`/input_integrity`).

This is a read-only manual explanation example. No model executed and no readiness or acquisition decision was authorized.
