# Bounded fixed-content identity review — partial pending subset

Canonical baseline: `4420686d3ee53d921563c41a889f51ba51d7b203` (merged GitHub PR #163).
The exact GitHub commit/tree was reconciled locally before preparation. PR numbers and project
phases are independent; no new phase number or Architecture v12 change is assigned.

The authorized target is Commander Collection: Black, non-premium. The bounded
[review bundle](../data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12/bundle.json)
contains original licensed source bytes, native Source Records/Parsed Artifacts, one native Product
candidate, explicit unresolved identities, an incomplete versioned manifest, and exact references
to existing CC2 records. It is pending human identity review, not approved or promoted, and not a
production acquisition evidence packet or READY review.

## Source evidence and candidate census

Three files were retrieved through the connected GitHub integration from
[MTGJSON's sealed-content repository at commit 6bde64122026eb7e65c21db028e34f4cb42b5305](https://github.com/mtgjson/mtg-sealed-content/tree/6bde64122026eb7e65c21db028e34f4cb42b5305):

| Original source | Bytes | SHA-256 |
| --- | ---: | --- |
| `data/products/CC2.yaml` | 1,011 | `87216b73a77118fa45f3069b370e55f918c79ae7b4d07d00b3fc82763f10caab` |
| `outputs/token_products_mappings/CC2.json` | 1,238 | `56ff9fb31b47b2c42be1da203d94c96c05c85d2dd66d549765e87327ab6fd193` |
| `LICENSE.txt` | 1,079 | `a78bab0667e57b25b91b3e037f6856fe20fbe01a091c7c525be292d8a834283b` |

Original UTF-8 bytes, including terminal-newline state, match the provider Git blob SHA-1 and
independent connector readback. The original MIT notice is retained. Each existing `RawSnapshotStore`
snapshot preserves bytes, SHA-256, byte length, retrieval time, commit pin and source locator.
[Source inventory](../data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12/source-inventory.json)
and native Source Records distinguish original-byte integrity from interpreted claims.
The measured retrieval time is `2026-10-12T09:49:44Z`; publication timestamps remain unknown.
These are retrieval times, not invented provider observation or market timestamps.

| Candidate/identity scope | Prepared result |
| --- | --- |
| Non-premium Product | One schema-valid native candidate, `requires_review`, lifecycle `draft` |
| Liliana, Heretical Healer // Liliana, Defiant Necromancer | Card/Printing pair unresolved and excluded from valid subset |
| Ghoulcaller Gisa | Card/Printing pair unresolved and excluded |
| Ophiomancer | Card/Printing pair unresolved and excluded |
| Phyrexian Arena | Card/Printing pair unresolved and excluded |
| Reanimate | Card/Printing pair unresolved and excluded |
| Toxic Deluge | Card/Printing pair unresolved and excluded |
| Snake/Zombie physical double-sided token | Provider pairing supported; exact Card/Printing pair unresolved and excluded |
| Sol Ring and Command Tower | Two existing CC2 Printings referenced; zero replacement candidates |

The proposed local Product ID `product-tcgplayer-247519` is explicitly derived from the supplied
provider namespace/value, not a guessed provider UUID. The regular product source separates
TCGplayer `247519` from premium `247520`, reports nine physical cards, and identifies the regular deck.
It also supplies release date and provider IDs, including SCG `SLD-MTG-BXS-CC2-EN-NONFOIL`.
Product v2 uses an empty version list; fixed content remains in the separate Product Intelligence
manifest, without inventing pack topology.

Parsed Product fields were prepared offline from the licensed YAML record. Exact source excerpt,
field provenance, source-supplied values and computed local identity/game/type/workflow metadata are
retained separately for review. The verification command does not parse provider feeds or create
candidates. Confidence fields express extraction consistency within these pending artifacts; they
are not human approval, probability estimates, or guarantees of upstream completeness.

## Remaining identity and content blockers

The token source proves physical product TCGplayer `247541` pairs these provider UUIDs:
`4b3f0527-7e70-5d24-a8e4-6e7ae3b0ec35` and `72cbd16d-49b7-5095-bddf-a65d7fe995ed`.
It does not assign verified face names, collector coordinates, language, finish or treatment to them.
No combined provider UUID or canonical token ID was invented. Although existing Card v3 supports
`double_faced_token`, that representation cannot be populated honestly from pairing alone.

The native CC2 export request returned `CONNECT tunnel failed, response 403`; that destination path
was stopped without bypass. The connected web reader could not supply full native CC2/deck bytes.
No unlicensed mirror, large LFS corpus, artwork, or full official article was retained.

All six ordinary pairs still require actual provider IDs, exact collector/namespace and variant
fields; Liliana also needs the complete face relationship. The prior
[official/retailer research](FIRST_FIXED_CONTENT_PILOT.md) is cited as corroboration, not relabeled
as an original provider export. The pending nine-component
[manifest](../data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12/manifest.json)
retains quantity-one research leads and explicit unknowns. Its completeness is **incomplete**:
a reported total of nine does not prove the exact nine guaranteed items/quantities/variants.
No complete guaranteed-content manifest is claimed. The retained Product source is separately
bound in manifest evidence for the Product identity, release date and reported total; it does not
replace the per-component research evidence or prove item membership.

Existing references bind canonical record hashes and full expected values in `data/canonical/state.json`:
Sol Ring Printing `c57a0dff-d056-5f28-9914-6f5766ee6b7c` and Command Tower Printing
`0bd7bca4-2839-5824-a392-c38178dc16b3`, plus their existing Card links. They are not recreated in the
typed game tree or another state store. Nonfoil is the intended regular-edition selection;
The canonical `frame_or_treatment=2015` value is preserved in the references; manifest treatment
remains null because a separate treatment value has not been verified.

## Validation and review procedure

Run the read-only verifier with the existing repository import path:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python scripts/verify_identity_review_bundle.py --bundle data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12 --data-root data
```

It composes existing raw snapshot, candidate, payload-schema and collision validators with explicit
cross-source provenance, canonical-reference and relationship checks. Artifact hash pins preserve
the exact manually prepared parsed fields and candidates; replay checks do not independently
recompute the YAML extraction or authenticate its interpretation. Changing preparation bytes
requires new pins and renewed human semantic review. It has no network retrieval,
import, approval, promotion or persistence operation. The deterministic
[review report](../data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12/review-report.json)
records the valid Product subset, unresolved pairs, sources, exact reused identities and approval
blockers. Passing structural checks does not resolve the missing source evidence or grant approval.
Human review can assess the Product subset and its manual extraction separately. The seven
missing pairs and incomplete contents prevent approval of a full identity/content bundle.
Market evidence in the report is a future acquisition-readiness blocker, not a requirement
to acquire markets or to review this identity-only subset.

Focused regressions exercise real-bundle replay and mutations to integrity/provenance, faces,
relationships, aliases/coordinates and reused records, with production writers forbidden.
The full hosted-style test result and protected inventory are recorded in the review PR.
Existing canonical data, historical market observations, knowledge facts, Architecture v12,
schemas, dependencies and workflows remain unchanged.

The next action is human review of the partial identity bundle and provision of the permitted native
CC2/deck records needed to resolve the seven excluded pairs and complete the manifest. Promotion,
market acquisition/admission, human READY attestation and sealed-versus-singles evaluation remain
separately unauthorized. Competitive and Deck Intelligence remain parked/unauthorized.
