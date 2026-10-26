"""Exact retained Card evidence for seven authored review subjects.

Selection is a finite table of complete authored passages. This module has no
ability parser, classifier, gameplay semantics or fallback identity resolution.
One local attachment-backed mechanical reader is used for each call; no live
reader or mutable input is returned to callers.
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


PROFILE_ID = "sha256:71b8879ced8fe7203aa69755bec411f0160a7c0011fdc768976c2113df600d3e"
QUERY_ID = "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"
SOURCE_SHA256 = "c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47"
SOURCE_BYTES = 2278127
ACQUISITION = "scryfall-mb2-30754638264-1"
DOSSIER_REFERENCE = "data/review/mechanical-card-cohort/dossiers.jsonl"
MANIFEST_REFERENCE = "data/review/mechanical-card-cohort/manifest.json"
MANIFEST_SHA256 = "8405fc5b88b8eabb16d5596d567c27bc749b63e68a33af792ef6f287001c3e58"
DOSSIERS_SHA256 = "108d269bc77a36e076028c67169e351f8b5328ad27a6b060ba69f74ead2c11bf"

# Exact canonical IDs and independently pinned existing dossier own identities.
CARD_BINDINGS = (
    ("6ad8011d-3471-4369-9d68-b264cc027487", "Sol Ring", "sha256:e413ea823970a9a367d21bb4fb4cf896d0c331ad4c318899f5424b46cd3d951e"),
    ("6b8cf2a0-b045-4d91-9d91-c602d40c6237", "Basalt Monolith", "sha256:b697c0e59a7f2d351038d2ab8182777dba75c7df893052fbfb6f3fe42eff01ce"),
    ("22f1a4a4-c423-4d1c-8775-0ed604a9fa51", "Deathrite Shaman", "sha256:59c4d6eb4c450df43e2edf6c3df604029e5ad73c3082dc07d852c6bd29a5bdbd"),
    ("53f7c868-b03e-4fc2-8dcf-a75bbfa3272b", "Dark Ritual", "sha256:7308ce0e1922c58b8821f4e8924eb7978b755bacf8450ab45d52ca256165916e"),
    ("97159138-c34b-416e-b079-5c952383a243", "Mana Flare", "sha256:c5eecdd1f22ab500e84827105a6baa12130eb0981bf7d375d8bfb2f399c3f744"),
    ("a784481f-eccb-4112-bb38-04a659319660", "Pitiless Plunderer", "sha256:c223fb6ab55294730b951d4449970ee3e823c221a9be83721193e8a6da93da40"),
)

# This table authors passage boundaries against exact retained field contents.
# None of the selections is discovered from punctuation, symbols or keywords.
SUBJECTS = (
    ("sol-ring-tap", CARD_BINDINGS[0][0], "{T}: Add {C}{C}.",
     "host_card", "Its single tap-for-mana ability; no additional subject."),
    ("basalt-monolith-tap", CARD_BINDINGS[1][0], "{T}: Add {C}{C}{C}.",
     "host_card", "The static untap restriction and paid untap activation remain surrounding context, outside this subject."),
    ("basalt-monolith-untap", CARD_BINDINGS[1][0], "{3}: Untap this artifact.",
     "host_card", "The static untap restriction and separate tap-for-mana activation remain surrounding context, outside this subject."),
    ("deathrite-shaman-first", CARD_BINDINGS[2][0],
     "{T}: Exile target land card from a graveyard. Add one mana of any color.",
     "host_card", "The complete first ability is selected. Its other two abilities remain source context and are outside this pilot's assessment."),
    ("dark-ritual-spell", CARD_BINDINGS[3][0], "Add {B}{B}{B}.",
     "host_spell", "The retained type line is separately bound. This selects the spell instruction, without creating a canonical ability identity."),
    ("mana-flare-trigger", CARD_BINDINGS[4][0],
     "Whenever a player taps a land for mana, that player adds one mana of any type that land produced.",
     "host_card", "Qualifying-trigger relationship is an authored pending interpretation; no event detection, causality or resolution is performed."),
    ("pitiless-plunderer-host-trigger", CARD_BINDINGS[5][0],
     "Whenever another creature you control dies, create a Treasure token.",
     "host_card", "The parenthetical describes an activation belonging to the created Treasure, not this host Card. It remains unassessed source context; no token entity or semantics is constructed."),
)


class CardBindingError(ValueError):
    """Exact retained Card correspondence could not be established."""


def _strict(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CardBindingError("duplicate retained JSON key")
            result[key] = value
        return result
    def reject(value):
        raise CardBindingError("nonfinite retained JSON value")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise CardBindingError("invalid retained JSON") from None


def _read(root: Path, relative: str, limit: int) -> bytes:
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise CardBindingError("retained evidence symlink rejected")
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError:
        raise CardBindingError("retained Card evidence unavailable") from None
    if len(raw) > limit:
        raise CardBindingError("retained Card evidence exceeds byte bound")
    return raw


def read_cards(*, catalog_root: Path, mechanical_root: Path,
               expected_profile_id: str, expected_query_snapshot_id: str) -> dict:
    """Verify current independent roots once, then bind privately owned evidence.

    ``mechanical_root`` is the evidence repository root (its ``data`` child is
    passed to MCI). Fixed expected identities must be supplied independently by
    the caller. Changing or expanding the live catalog is a rejection, never a
    reason to select historical catalog fixtures. No data is written.
    """
    if expected_profile_id != PROFILE_ID or expected_query_snapshot_id != QUERY_ID:
        raise CardBindingError("exact pilot profile and query identities required")
    catalog_root, mechanical_root = Path(catalog_root).absolute(), Path(mechanical_root).absolute()
    attachment = attach_legacy_compatibility(
        catalog_root, control_path="config/catalog_profiles/legacy-public-tier-a.json",
        game="magic", expected_profile_id=expected_profile_id)
    mechanical = MechanicalCardIntelligence.from_attachment(
        attachment, data_root=mechanical_root / "data",
        source_directory=mechanical_root / "data/market/acquisitions" / ACQUISITION,
        expected_query_snapshot_id=expected_query_snapshot_id)
    # MCI has executed its real manifest, file and report checks. These are
    # independent fixed pilot expectations, additional to manifest consistency.
    source = json.loads(json.dumps(mechanical.source))
    if (source["acquisition_run_id"] != ACQUISITION
            or source["retained_source_sha256"] != SOURCE_SHA256
            or source["source_timestamp"] != "2026-08-02T09:09:45.851000Z"
            or source["retrieved_at"] != "2026-08-02T15:34:06Z"):
        raise CardBindingError("pilot retained acquisition identity mismatch")
    source_meta = {name: (length, digest) for name, length, digest in mechanical._source_files}
    if source_meta.get("source-mb2.json") != (SOURCE_BYTES, SOURCE_SHA256):
        raise CardBindingError("pilot retained source bytes mismatch")
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
        raise CardBindingError("missing exact retained pilot dossier")
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
