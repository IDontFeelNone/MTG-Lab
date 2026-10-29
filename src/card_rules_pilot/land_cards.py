"""Finite, authored retained-land correspondence through the actual catalog.

This additive adapter admits six existing Cards and nine complete local review
subjects. Names are display assertions after canonical-ID selection. No provider
mana annotation, punctuation splitter or gameplay parser selects a subject.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from card_intelligence.mechanics import (
    MechanicalCardIntelligence, DOSSIER_VERSION, FIELD_NAMES, _field,
    content_identity,
)
from repository.legacy_profile import attach_legacy_compatibility
from .cards import (
    PROFILE_ID, QUERY_ID, SOURCE_SHA256, SOURCE_BYTES, ACQUISITION,
    DOSSIER_REFERENCE, MANIFEST_REFERENCE, MANIFEST_SHA256, DOSSIERS_SHA256,
    CardBindingError, _strict, _read,
)

# Own dossier identities independently reproduced from actual retained records.
CARD_BINDINGS = (
    ("46a07b53-ff58-4bd6-80dd-ded2eb0e29a3", "Snow-Covered Wastes", "sha256:025c47309f73d623564ef6aa3b1ba6a646ea9e5acc84df9089387269345b6d91"),
    ("f3e8dc56-2810-474e-a6a7-9c3555f94ae9", "Rishadan Port", "sha256:f9005aafb851dca207caae815fd24e1a50acdf0c28f7e9150ee3f6c55b553060"),
    ("f25351e3-539b-4bbc-b92d-6480acf4d722", "City of Brass", "sha256:838daa12cfb53634aa9699e1109863d19ed8a3937406bd9f080021ba7ff356f2"),
    ("66ae2562-68e9-4c77-ba0a-57f8ff37f656", "Tarnished Citadel", "sha256:1868941a00d266732bee18943a07a2f566f537fd99b8d2357b8a63accf6a917b"),
    ("7358e164-5704-4e78-9b21-6a9bf2a968ce", "Cabal Coffers", "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2"),
    ("0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "Command Tower", "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432"),
)

# Complete boundaries are authored against exact retained fields, including
# retained "this land" wording. These are not canonical ability identities.
SUBJECTS = (
    ("snow-wastes-mana", CARD_BINDINGS[0][0], "{T}: Add {C}.", "host_card",
     "Its complete explicit activation only; the retained Basic Snow Land type line supplies no snow-payment, intrinsic-ability or land-play semantics."),
    ("port-mana", CARD_BINDINGS[1][0], "{T}: Add {C}.", "host_card",
     "The separately owned targeted paid land-tapping activation remains unselected surrounding context; its target and cost do not belong to this subject."),
    ("port-utility", CARD_BINDINGS[1][0], "{1}, {T}: Tap target land.", "host_card",
     "The complete paid targeted activation only; the separate mana activation supplies no output to this subject. Payment feasibility and target legality are unassessed."),
    ("city-mana", CARD_BINDINGS[2][0], "{T}: Add one mana of any color.", "host_card",
     "The damage trigger remains a separately owned subject. Its becomes-tapped relationship is not imported as an additional effect of this activation."),
    ("city-damage-trigger", CARD_BINDINGS[2][0], "Whenever this land becomes tapped, it deals 1 damage to you.", "host_card",
     "The complete damage-triggered ability only. The separate activation supplies no mana output to this subject; becomes tapped is preserved without detecting any event or implying a tap-for-mana relationship."),
    ("citadel-colorless", CARD_BINDINGS[3][0], "{T}: Add {C}.", "host_card",
     "The color-choice activation and its damage sentence belong to another subject. Neither is imported into this colorless activation."),
    ("citadel-color-choice", CARD_BINDINGS[3][0], "{T}: Add one mana of any color. This land deals 3 damage to you.", "host_card",
     "Both sentences belong to this complete activation. Its additional damage effect is not a separate triggered subject. No actual damage, prevention, life total or fine-grained ordering is calculated."),
    ("coffers-mana", CARD_BINDINGS[4][0], "{2}, {T}: Add {B} for each Swamp you control.", "host_card",
     "The complete written cost and stated Swamp-count output dependency remain attached. No count, subtype recognition, net output, break-even calculation or executable sequence is supplied."),
    ("tower-mana", CARD_BINDINGS[5][0], "{T}: Add one mana of any color in your commander's color identity.", "host_card",
     "The complete commander-color-identity restriction remains attached. No commander, palette or actual output is inferred from Card color identity or provider annotations; unknown context is not an empty palette."),
)


def read_cards(*, catalog_root: Path, mechanical_root: Path,
               expected_profile_id: str, expected_query_snapshot_id: str) -> dict:
    """Verify current independent roots once, then bind privately owned evidence.

    ``mechanical_root`` is the evidence repository root (its ``data`` child is
    passed to MCI). Fixed expected identities must be supplied independently by
    the caller. Changing or expanding the live catalog is a rejection, never a
    reason to select historical catalog fixtures. No data is written.
    """
    if expected_profile_id != PROFILE_ID or expected_query_snapshot_id != QUERY_ID:
        raise CardBindingError("exact land profile and query identities required")
    catalog_root, mechanical_root = Path(catalog_root).absolute(), Path(mechanical_root).absolute()
    attachment = attach_legacy_compatibility(
        catalog_root, control_path="config/catalog_profiles/legacy-public-tier-a.json",
        game="magic", expected_profile_id=expected_profile_id)
    mechanical = MechanicalCardIntelligence.from_attachment(
        attachment, data_root=mechanical_root / "data",
        source_directory=mechanical_root / "data/market/acquisitions" / ACQUISITION,
        expected_query_snapshot_id=expected_query_snapshot_id)
    # MCI has executed its real manifest, file and report checks. These are
    # independent fixed land expectations, additional to manifest consistency.
    source = json.loads(json.dumps(mechanical.source))
    if (source["acquisition_run_id"] != ACQUISITION
            or source["retained_source_sha256"] != SOURCE_SHA256
            or source["source_timestamp"] != "2026-08-02T09:09:45.851000Z"
            or source["retrieved_at"] != "2026-08-02T15:34:06Z"):
        raise CardBindingError("land retained acquisition identity mismatch")
    source_meta = {name: (length, digest) for name, length, digest in mechanical._source_files}
    if source_meta.get("source-mb2.json") != (SOURCE_BYTES, SOURCE_SHA256):
        raise CardBindingError("land retained source bytes mismatch")
    manifest_raw = _read(mechanical_root, MANIFEST_REFERENCE, 131072)
    raw = _read(mechanical_root, DOSSIER_REFERENCE, 2400000)
    manifest = _strict(manifest_raw)
    if (hashlib.sha256(manifest_raw).hexdigest() != MANIFEST_SHA256
            or manifest["schema_version"] != "mechanical-cohort-review-manifest-v1"
            or manifest["files"]["dossiers.jsonl"] != {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            or hashlib.sha256(raw).hexdigest() != DOSSIERS_SHA256):
        raise CardBindingError("retained dossier collection integrity mismatch")
    wanted = {card_id: (name, dossier_id) for card_id, name, dossier_id in CARD_BINDINGS}
    selected, seen = {}, set()
    for index, line in enumerate(raw.splitlines()):
        if len(line) > 65536:
            raise CardBindingError("retained mechanical dossier exceeds schema byte bound")
        dossier = _strict(line)
        card_id = dossier["card_identity"]["card_id"]
        if card_id in seen:
            raise CardBindingError("duplicate retained mechanical Card identity")
        seen.add(card_id)
        if card_id in wanted:
            selected[card_id] = (index, dossier)
    if set(selected) != set(wanted):
        raise CardBindingError("missing exact retained land dossier")
    manifest_ids = {row["card_id"]: row["dossier_id"] for row in manifest["dossiers"]}
    if len(manifest_ids) != len(manifest["dossiers"]):
        raise CardBindingError("duplicate mechanical manifest Card identity")
    cards = {}
    for card_id, (name, expected_id) in wanted.items():
        index, dossier = selected[card_id]
        own = dossier.get("dossier_id")
        body = {key: value for key, value in dossier.items() if key != "dossier_id"}
        if (dossier["schema_version"] != DOSSIER_VERSION or own != expected_id
                or own != content_identity(body) or manifest_ids.get(card_id) != own
                or dossier["canonical_snapshot_id"] != expected_query_snapshot_id):
            raise CardBindingError("schema-specific mechanical dossier identity mismatch")
        canonical = mechanical.cards.get(card_id)
        matches = mechanical.rows.get(card_id, [])
        if canonical is None or len(matches) != 1:
            raise CardBindingError("missing or ambiguous exact mechanical Card binding")
        row_index, row = matches[0]
        ds = dossier["source"]
        if (dossier["card_identity"] != {"game_id": "magic", "card_id": card_id, "name": name}
                or dossier["canonical_values"] != dict(canonical.canonical_values)
                or canonical.canonical_values.get("card_reference") != card_id
                or canonical.supersession_state != "current"
                or ds["resolution"] != "unique" or ds["source_record_index"] != row_index
                or ds["provider_record_id"] != row["id"] or ds["oracle_id"] != card_id
                or ds["record_content_identity"] != content_identity(row)
                or any(ds.get(key) != value for key, value in source.items())
                or dossier["fields"] != {field: _field(row, field) for field in FIELD_NAMES}):
            raise CardBindingError("retained dossier disagrees with live attached Card/source evidence")
        cards[card_id] = {
            "card_identity": dossier["card_identity"], "canonical_snapshot_id": dossier["canonical_snapshot_id"],
            "canonical_values": dossier["canonical_values"],
            "mechanical_dossier_id": own, "mechanical_dossier_version": DOSSIER_VERSION,
            "retained_dossier_reference": DOSSIER_REFERENCE, "retained_dossier_line_index": index,
            "source": ds, "fields": {field: dossier["fields"][field] for field in ("oracle_text", "type_line")},
        }
    subjects = {}
    for subject_id, card_id, passage, owner, limitation in SUBJECTS:
        card = cards[card_id]
        oracle = card["fields"]["oracle_text"]
        type_line = card["fields"]["type_line"]
        if (oracle["status"] != "known" or type_line["status"] != "known"
                or oracle["value"].count(passage) != 1):
            raise CardBindingError("authored complete passage no longer uniquely matches exact field")
        start = oracle["value"].index(passage)
        # Equality against the fixed complete passage is correspondence only.
        # The offsets are not language analysis or canonical ability identities.
        subjects[subject_id] = {
            "subject_id": subject_id, "identity_scope": "local_review_subject_only",
            "card_id": card_id, "mechanical_dossier_id": card["mechanical_dossier_id"],
            "owner": owner, "source_field_pointer": oracle["source_pointer"],
            "source_record_pointer": "/" + str(card["source"]["source_record_index"]) + oracle["source_pointer"],
            "source_field_identity": content_identity(oracle), "complete_field_value": oracle["value"],
            "selected_passage": passage, "passage_start": start, "passage_end": start + len(passage),
            "surrounding_before": oracle["value"][:start], "surrounding_after": oracle["value"][start + len(passage):],
            "unselected_context_assessment": "outside_this_subject", "ownership_and_context_limitations": limitation,
            "type_line": {**type_line, "field_identity": content_identity(type_line)},
        }
    # Mandatory current checks at the end of this read boundary guard changes
    # during evidence preparation. No mutable reader escapes into subject loops.
    catalog_binding = mechanical.catalog_binding
    if (_read(mechanical_root, MANIFEST_REFERENCE, 131072) != manifest_raw
            or _read(mechanical_root, DOSSIER_REFERENCE, 2400000) != raw):
        raise CardBindingError("retained dossier collection changed during read")
    return json.loads(json.dumps({"catalog_binding": catalog_binding,
        "canonical_snapshot_id": expected_query_snapshot_id, "acquisition": source,
        "cards": cards, "subjects": subjects}))
