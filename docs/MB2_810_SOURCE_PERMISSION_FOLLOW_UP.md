# MB2 810 source-permission evidence requirements

This document records questions for a later permission review. No provider was
contacted, no permission is inferred, and no source-policy gate is cleared.
All questions concern the exact fields/dependencies in the field-admission matrix,
not access to an API or a license to unrelated software. Existing policy receipts
are at `reference-reviews/mb2-810-source-policy/2026-10-14/source-receipts.json`.

| Rights layer | Established narrow evidence | Additional evidence or decision needed |
| --- | --- | --- |
| MTGJSON-controlled material | Current official MIT notice permits use/distribution/commercial reuse within MTGJSON's rights, with copyright and permission notice preservation. | Identify which retained fields and compilation contributions it controls; whether any specific upstream sublicensing applies. Bind the answer to the exact projection, operation and current policy version. Keep the full MIT notice. |
| Scryfall-controlled material | First-party access FAQ supports local bulk processing and identifies underlying Wizards rights. | Current authoritative API/data-reuse terms or direct permission applicable to Oracle IDs, Printing IDs, illustration/back IDs, catalog encodings and the exact factual projection. Distinguish private processing, public GitHub retention/PR redistribution, free services and paid/commercial use. State attribution, downstream licensing and retention conditions. Inaccessible terms are unresolved evidence, not refusal or permission. |
| Wizards/third-party Magic content | Personal website/service use and conditional original free fan content, subject to General Terms and Fan Content Policy. | Establish applicability or obtain explicit permission for exact Card names, printed/foreign names, rules/mechanical/type/mana descriptions, flavor text and rulings, separately from images. Address database retention/republication and provider-derived transformations. The fan policy's exclusion of verbatim copying/reposting must be resolved; original free websites are not automatic database permission. |
| EDHREC and marketplace/upstream material | MTGJSON definitions identify EDHREC metrics and provider namespaces; no operation-complete upstream grant is retained. | Identify original issuer/authorship and applicable permissions for rank/saltiness metrics, identifier compilations, SKU/product data and any other retained provider contribution. Distinguish bare identifiers/links/credit facts from provider-authored content. If excluded, verify none survives in nested metadata or dependencies. No market evidence is invented or acquired. |

Evaluate each proposed operation independently:

- **Private processing:** determine whether the complete retained content mix can
  be transformed/analyzed privately under applicable grants. Scryfall's bulk
  operational guidance does not establish all underlying rights or collection-API
  redistribution terms. Private processing and public retention are separate.
- **Public repository/data PR:** establish permission for the exact canonical
  fields and every payload, projection, parsed context, receipt, audit and replay
  dependency that publication would include. Public availability of old evidence
  does not establish a new redistribution grant. URLs/hashes do not replace
  required bytes or establish the right to distribute them.
- **Future free/public application:** specify actual features, exposed data,
  access/registration conditions, required unofficial notices, sponsorship/ads
  and takedown obligations. Verify that the creation and field use qualify under
  applicable grants and upstream terms; do not assume a free service qualifies.
- **Future commercial/paid application:** specify access fees, sales/licensing
  and exposed data. Establish appropriate commercial permission across every
  required rights layer. Allowed donations/ads for qualifying free fan content
  do not establish a general paid-service/database license.

The smallest immediate evidence question is whether unchanged required Oracle
identities, Scryfall alias identities, Card names and required Printing relationship
facts may be publicly retained with the needed source/replay dependencies. If
these remain unresolved, optional prose filtering cannot make the exact 810 safe.

An adequate retained answer must identify its authoritative issuer, exact URL or
other verifiable origin, retrieval/decision time, operation and field scope,
requirements, limits, hash and permissible retention form. A digest binds the
answer; it does not authenticate a reviewer or create an admission decision.
Clearance and owner admission approval remain separate future actions.
