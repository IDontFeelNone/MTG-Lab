# V13 Tier A Card Intelligence & Acquisition Attachment Integration

Status: separately owner-authorized implementation, pending independent Project
Manager inspection. Architecture v13 is ACTIVE APPROVED; Decision 017 is Accepted.
Reviewed canonical main: `4ef94dd704b052a7fbaf15d034fe65c015be256f`.
Stage 3's Tier A compatibility profile is merged in PR #179.

This milestone moves one existing analytical vertical onto the explicit read-side
attachment seam. It changes neither the analytical policy nor the retained
mechanical/acquisition dossier formats. It does not authorize production data
use, provider acquisition, purchase execution or the next milestone.

## Dependency-injection API

```python
from pathlib import Path

from card_intelligence.acquisition import CardAcquisitionAdapter
from card_intelligence.mechanics import MechanicalCardIntelligence
from repository.legacy_profile import attach_legacy_compatibility

catalog = attach_legacy_compatibility(
    Path("/explicit/existing-checkout"),
    control_path="config/catalog_profiles/legacy-public-tier-a.json",
    game="magic",
    expected_profile_id=(
        "sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e"
    ),
)
expected_query = (
    "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"
)
mechanical = MechanicalCardIntelligence.from_attachment(
    catalog,
    data_root=Path("/explicit/mechanical-evidence-root/data"),
    source_directory=Path("/explicit/mechanical-evidence-root/data/market/acquisitions/retained-run"),
    expected_query_snapshot_id=expected_query,
)
acquisition = CardAcquisitionAdapter.from_mechanical(
    mechanical,
    expected_query_snapshot_id=expected_query,
)
assert acquisition.query is mechanical.query
catalog_binding = mechanical.catalog_binding
```

The paths above are explicit caller examples, not discovery locations or new
provider acquisitions. Independently selected configuration supplies the expected
profile/query identities. The mechanical evidence root need not be the catalog
root, but its source directory must satisfy the existing retained-source contract.
Mechanical retained-source references retain their existing interpretation relative
to the explicit mechanical data root's parent, never the attached catalog root.
The returned catalog binding is separate from mechanical dossier bytes.

`CardAcquisitionAdapter.from_attachment(attachment, *, data_root,
expected_query_snapshot_id, source_directory=None)` is a convenience alternative:
it constructs one attached MechanicalCardIntelligence and then uses
`from_mechanical`. It does not construct another independent catalog query.
`from_mechanical` requires an actual attachment-backed MechanicalCardIntelligence;
a dictionary, arbitrary namespace or legacy mechanical reader does not install an
attachment. A failed attachment or mismatched expected snapshot remains blocked.

Existing `MechanicalCardIntelligence(data_root, source_directory=...)` and
`CardAcquisitionAdapter(data_root)` constructors retain their direct-root behavior.
They are not silently converted to the attached mode. A caller must explicitly
choose the new path; failure never falls back to the legacy constructor.

## Catalog and evidence are separate domains

| Domain | Authority/input | Scope and identity |
| --- | --- | --- |
| Catalog | Verified, explicitly selected read-side attachment | Cards, Printings, Identifiers, Finishes, relationships and selected entity provenance; outer profile/closure identity remains separate from query identity |
| Mechanical evidence | Independently selected retained acquisition directory | Existing source manifest, exact retained bytes, provider/source digests and acquisition run; not Tier A content |
| Mechanical dossier | Existing mechanical projection | `mechanical-card-dossier-v1`, exact canonical Card identity, canonical query snapshot and mechanical source references; content identity unchanged |
| Acquisition inputs | Separately supplied source-bound request/context/ownership/offer evidence | Original input and source identities; no catalog authority, no source-policy clearance and no implicit real ownership |
| Decision Intelligence | Existing deterministic policy and evidence-bound analyses | Existing ordered criteria, eligibility and abstention; no new purchase rule or execution action |
| Personal data | Caller-controlled independent inputs | Never written into the shared catalog/profile or mechanical acquisition directory |

The five SourceRecords and two audit-context files selected by Tier A remain
catalog provenance context. They are not a replacement for the mechanical source
manifest, Scryfall acquisition, or acquisition-offer evidence. Source availability
does not establish permission. No source bytes are copied into the catalog.

The existing mechanical source loader continues to require its established
Scryfall-shaped retained-acquisition contract. The fictional test fixture uses
clearly labeled synthetic records compatible with that contract. This milestone
does not introduce a new provider format or claim provider-neutral mechanical
extraction. The catalog attachment itself remains game-neutral.

## One query through the reasoning path

```text
verified catalog attachment
  -> CanonicalQueryEngine.from_attachment(...)
     -> MechanicalCardIntelligence.query
        -> CanonicalSemanticQueryEngine(the same query)
           -> ReasoningContextBuilder
        -> CardAcquisitionAdapter.query (the same query)
```

Mechanical Card Intelligence preserves its admitted-Card selection: exact
`card_reference == canonical_identity` and current supersession state. Typed seed
Cards without that binding do not become production-cohort Cards by name. Exact
provider `oracle_id` matching determines mechanical coverage; no name fallback or
replacement Printing selection is added. Unique, missing and ambiguous source
coverage remain distinct. Missing evidence produces incomplete mechanical status
and the existing acquisition blocked/ABSTAIN result rather than invented facts.

The context builder is constructed over the same attached query. Contexts bind
the existing `canonical_snapshot_id`; no second query is constructed for reasoning.
The outer catalog binding is exposed separately through `catalog_binding` on the
live mechanical/acquisition instances. It is not inserted into retained dossier
schemas or used to repin historical content identities.

Attached reads revalidate the selected catalog, expected query snapshot and
independent mechanical source bindings. A changed catalog, changed source,
retargeted reader/root, different query or acquisition input/reconstruction
snapshot cannot silently reuse a previous binding. Content hashes establish
integrity; they do not authenticate a reviewer or confer processing permission.

## Distinct identities

| Identity | Meaning |
| --- | --- |
| Catalog profile/control ID | Stage 3 authored capability, namespace, permission and selected-file contract |
| Catalog closure ID | Exact selected 40 in-place file bindings |
| Canonical query snapshot ID | Existing serialized query-result identity; unchanged by this integration |
| Mechanical acquisition/source IDs | Independent retained run, manifest and provider/retained-source digests |
| Mechanical dossier ID | Existing mechanical projection and source/query bindings |
| Acquisition input/dossier/Decision IDs | Existing request, separately supplied source evidence, bounded reconstruction and deterministic evaluation |
| Reasoning-context ID | Existing structured context and canonical snapshot binding; no model call |

Reconstruction of a retained acquisition dossier remains an offline check of its
original bounded proof. It does not reinstall a live attachment, authorize new
catalog reads or convert simulated acquisition inputs into owner evidence.

## Tier A remains bounded

This vertical needs entity reads, exact Printing relationships and entity-local
provenance. It does not need full promotion history, rejected/validation-failure
history, aggregate validation statistics or historical admission replay. Those
Tier B/C operations still fail through the existing Stage 3 capability gates
before excluded I/O. No additional audit or SourceRecord is selected.

Tier B Audit-Context Capability Design Review is deliberately **DEFERRED**.
No current integration requirement makes it a prerequisite for this vertical.
Unexpected future Tier B use must be reviewed explicitly rather than silently
expanding the catalog profile.

Stage 3's fixed flags remain `production_eligible=false`,
`approval_state=not_granted`, `source_policy_clearance=not_granted` and
`data_processing_permission_established=false`. All seven mixed-content operation
permissions remain **NOT_ESTABLISHED**: local private processing, private operator
retention, existing-public-Git compatibility permission, new public redistribution,
free public service, commercial service and AI/model export. Successful reasoning,
manifest verification and existing public Git history do not change those states.

## Compatibility characterization and public tests

New integration tests use original fictional catalog and mechanical/acquisition
records, with separate evidence and collection roots. They exercise the real
existing analytical path, exact identities/relationships, deterministic results or
honest abstention, shared semantic/reasoning query, independent source/catalog
drift, root retargeting, unsupported audit operations and no network fallback.
They need no credentials, private mount or protected provider data.

A narrow in-place check of already-tracked current public data compares the
explicit-root legacy path with the attachment-backed path. At the reviewed
baseline their query identity is
`sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7`.
Equivalent catalog and retained source inputs must preserve mechanical dossier
bytes and acquisition policy/result semantics. This is compatibility
characterization, not processing, redistribution, service or export clearance.
In expanded-writer tests this fixed baseline attachment must reject changed
catalog bytes; current operations never substitute an old fixture to hide drift.

Legacy constructors, `mechanical-card-dossier-v1`, acquisition dossier/proof
formats, contextual comparison, functional-role proposals and retained pilot
artifacts remain unchanged. Card Acquisition historical replay continues binding
its original Architecture-v12 dependency and protected identity:
`sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53`.

The milestone PR reports actual focused/full-suite and expanded-publication
regression commands, counts, tested revision and exit statuses. Hosted CI results
are reported separately. No test success is source permission or owner admission.

## Limits and next candidate — NOT AUTHORIZED

This milestone does not migrate Product/Market/Decision consumers generally,
KnowledgeRepository, functional-role or contextual-comparison constructors. It
does not implement Rules, Deck, Competitive Intelligence, simulation, SQL,
AI/model transport, provider acquisition, protected data or production snapshots.
Writer/admission/OIDC, source-policy registry, MB2 810 pending inputs and nine holds
remain unchanged. Owner spelling proposals stay unapplied and physical Printing
verification remains unresolved.

Recommended next candidate: **V13 Functional-Role and Contextual-Comparison
Attachment Integration — NOT AUTHORIZED**. `FunctionalRolePilot` still constructs
a legacy MechanicalCardIntelligence, and `ContextualCardComparisonPilot` uses that
pilot. Passing the existing attachment through those established readers would
extend structured explanatory value with a small, testable dependency change;
pending roles and unverified context must remain pending/ABSTAIN.

Alternatives considered: Gameplay Rules & Interaction Intelligence needs its own
evidence/model foundation; simulation needs separately approved product/rules and
randomness contracts; Deck Intelligence needs reviewed contextual/legality inputs.
Each offers future product value but introduces a larger unapproved domain than
the remaining existing-consumer attachment gap. Tier B review is warranted only
when a concrete consumer needs excluded audit history. No next candidate begins
automatically, and none confers source-policy clearance.

The new verified factory accepts integrity-bound fictional or Tier A attachment
handles. The unrestricted `LegacyPublicAttachment` only checks root existence and
cannot promise drift detection; use the unchanged legacy MCI constructor for that
compatibility behavior. It is not accepted as a verified immutable input.
