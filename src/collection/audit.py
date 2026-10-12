"""Read-only, source-bound collection audits over the existing snapshot contract."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

from reasoning.models import freeze as _freeze, thaw as _plain

from .intelligence import (CollectionIntelligenceError, SNAPSHOT_VERSION,
                           build_snapshot, canonical_json, digest, read_import)


AUDIT_VERSION = "collection-audit-v1"
ORGANIZATION_VERSION = "collection-organization-v1"
STORAGE_CLASSES = {"sleeved", "separated", "bulk", "binder", "deck", "other"}
REVIEW_STATES = ("reviewed", "pending", "unresolved", "reassessment_needed")


class CollectionAuditError(CollectionIntelligenceError):
    """Audit inputs do not reproduce their retained evidence."""


@dataclass(frozen=True, init=False)
class CollectionAuditDossier(Mapping):
    """An immutable calculation; serialization returns independent JSON values."""

    _document: Mapping

    def __init__(self, document, *, resolver, snapshot, source_path, source_root, assessments=()):
        """Reconstruct a retained document only by replaying its original inputs."""
        value = _plain(document)
        if not isinstance(value, dict) or value.get("schema_version") != AUDIT_VERSION:
            raise CollectionAuditError("unsupported collection audit schema")
        try:
            expected_total = value["quantity_census"]["expected_total"]
            candidates = [item["printing_id"] for item in value["ownership_coverage"]["candidates"]]
        except (KeyError, TypeError) as error:
            raise CollectionAuditError("collection audit reconstruction inputs are missing") from error
        replay = CollectionAudit(resolver).build(snapshot, source_path=source_path, source_root=source_root,
                                                assessments=assessments, expected_total=expected_total,
                                                candidate_printing_ids=candidates)
        if canonical_json(value) != canonical_json(replay.to_dict()):
            raise CollectionAuditError("collection audit does not reproduce its original inputs")
        object.__setattr__(self, "_document", replay._document)

    @classmethod
    def reconstruct(cls, document, **bound_inputs):
        return cls(document, **bound_inputs)

    @classmethod
    def _from_verified(cls, document):
        result = object.__new__(cls)
        object.__setattr__(result, "_document", _freeze(_plain(document)))
        return result

    def __getitem__(self, key):
        return self._document[key]

    def __iter__(self):
        return iter(self._document)

    def __len__(self):
        return len(self._document)

    def as_dict(self):
        return _plain(self._document)

    def to_dict(self):
        return self.as_dict()

    def to_json(self):
        return canonical_json(self.as_dict()).decode("utf-8")

    def reasoning_context(self, *, max_bytes=65536, max_holdings=20, max_cards=20,
                          max_assessments=20):
        """Bound a manual handoff while accounting for every omitted source row."""
        if type(max_bytes) is not int or not 1 <= max_bytes <= 65536 or any(
                type(limit) is not int or limit < 0 for limit in (max_holdings, max_cards, max_assessments)):
            raise CollectionAuditError("invalid collection reasoning context limit")
        holdings = [{key: _plain(item[key]) for key in
                     ("holding_ref", "owned_lot_id", "resolution_status", "exclusion", "reported_quantity",
                      "quantity_state", "printing_id", "card_id", "storage_location", "organization")}
                    for item in self["holdings"][:max_holdings]]
        cards = [{**{key: _plain(item[key]) for key in
                     ("card_id", "card_name", "quantity", "review_status", "ever_reviewed", "assessment_id",
                      "review_basis", "new_discovery_eligible", "unreviewed_bulk_eligible")},
                  "canonical_context_reference": {"canonical_snapshot_id": self["bindings"]["canonical_snapshot_id"],
                                                  "card_id": item["card_id"],
                                                  "printing_ids": _plain(item["printing_ids"]),
                                                  "query_operation": "card"}}
                 for item in self["cards"][:max_cards]]
        assessments = [{key: _plain(item[key]) for key in
                        ("assessment_id", "card_id", "status", "purpose", "outcome", "reason", "human_review")}
                       for item in self["assessment_history"][:max_assessments]]
        context = {"schema_version": "collection-audit-reasoning-context-v1", "audit_id": self["audit_id"],
                   "audit_digest": self["audit_digest"], "collection_id": self["collection_id"],
                   "bindings": {key: _plain(self["bindings"][key]) for key in
                                ("snapshot_id", "snapshot_digest", "source_import_digest", "canonical_snapshot_id", "source")},
                   "quantity_census": _plain(self["quantity_census"]),
                   "identity_census": _plain(self["identity_census"]),
                   "review_census": {"unit": self["review_census"]["unit"],
                                     "counts": _plain(self["review_census"]["counts"]),
                                     "review_basis_counts": _plain(self["review_census"]["review_basis_counts"])},
                   "source_classification": _plain(self["source_classification"]),
                   "holdings": holdings, "cards": cards, "assessment_history": assessments,
                   "boundaries": _plain(self["boundaries"]), "limitations": _plain(self["limitations"])}
        if self["review_census"].get("nonoperative_assessment_ids"):
            context["review_census"]["nonoperative_assessment_ids"] = _plain(
                self["review_census"]["nonoperative_assessment_ids"])
        while True:
            context["omissions"] = {name: {"total": len(self[key]), "included": len(context[key]),
                                            "omitted": len(self[key]) - len(context[key])}
                                    for name, key in (("holdings", "holdings"), ("cards", "cards"),
                                                      ("assessments", "assessment_history"))}
            context["serialized_byte_count"] = 0
            for _ in range(4):
                count = len(canonical_json(context))
                if count == context["serialized_byte_count"]:
                    break
                context["serialized_byte_count"] = count
            if len(canonical_json(context)) <= max_bytes:
                return context
            for key in ("holdings", "assessment_history", "cards"):
                if context[key]:
                    context[key].pop()
                    break
            else:
                raise CollectionAuditError("collection reasoning context exceeds byte limit")


def _positive(quantity):
    return type(quantity) is int and quantity > 0


def _known_text(value):
    return isinstance(value, str) and value.strip().casefold() not in {"", "unknown", "null"}


def _snapshot_document(snapshot):
    value = _plain(snapshot)
    if not isinstance(value, dict) or value.get("schema_version") != SNAPSHOT_VERSION:
        raise CollectionAuditError("unsupported collection snapshot schema")
    claimed = value.pop("snapshot_digest", None)
    if claimed != digest(value):
        raise CollectionAuditError("collection snapshot digest mismatch")
    value["snapshot_digest"] = claimed
    if not _known_text(value.get("snapshot_id")):
        raise CollectionAuditError("collection snapshot identity is missing")
    return value


def _organization(row):
    provenance = row.get("provenance", {})
    if not isinstance(provenance, dict):
        raise CollectionAuditError("row provenance must be an object")
    organization = provenance.get("organization")
    if organization is None:
        return {"schema_version": ORGANIZATION_VERSION, "storage_classification": None}
    if not isinstance(organization, dict) or organization.get("schema_version") != ORGANIZATION_VERSION:
        raise CollectionAuditError("unsupported collection organization schema")
    classification = organization.get("storage_classification")
    if classification is not None and (not isinstance(classification, str) or classification not in STORAGE_CLASSES):
        raise CollectionAuditError("unsupported storage classification")
    return {"schema_version": ORGANIZATION_VERSION, "storage_classification": classification}


class CollectionAudit:
    """Project ownership assertions, organization and separately recorded reviews."""

    def __init__(self, resolver):
        self.resolver = resolver

    def _verified_snapshot(self, snapshot, *, source_path, source_root):
        """Use one source/resolver replay boundary for current and historical inputs."""
        root = Path(source_root).resolve()
        path = Path(source_path)
        path = (path if path.is_absolute() else root / path).resolve()
        if not path.is_relative_to(root):
            raise CollectionAuditError("collection source path escapes source root")
        original = path.read_bytes()
        imported = read_import(path)
        if hashlib.sha256(original).hexdigest() != imported["source_import_digest"]:
            raise CollectionAuditError("collection source changed during verification")
        value = _snapshot_document(snapshot)
        if imported["source_import_digest"] != value.get("source_import_digest"):
            raise CollectionAuditError("collection source byte digest mismatch")
        if value.get("canonical_digest") != self.resolver.canonical_digest or \
                value.get("canonical_snapshot_id") != self.resolver.canonical_snapshot_id:
            raise CollectionAuditError("collection canonical snapshot changed; retain an explicit new snapshot")
        resolution = self.resolver.resolve(imported)
        reconstructed = build_snapshot(imported, resolution, value["snapshot_id"])
        if canonical_json(reconstructed) != canonical_json(value):
            raise CollectionAuditError("collection snapshot does not reproduce retained source resolution")
        return value, imported, original, path, root

    def verify_source_snapshot(self, snapshot, *, source_path, source_root):
        """Verify retained ownership evidence before a separately authorized write."""
        return self._verified_snapshot(snapshot, source_path=source_path, source_root=source_root)[0]

    def build(self, snapshot, *, source_path, source_root, assessments=(),
              expected_total=None, candidate_printing_ids=()):
        value, imported, original, path, root = self._verified_snapshot(
            snapshot, source_path=source_path, source_root=source_root)
        if expected_total is not None and (type(expected_total) is not int or expected_total < 0):
            raise CollectionAuditError("expected total must be a nonnegative integer or null")
        candidates = tuple(candidate_printing_ids)
        if len(set(candidates)) != len(candidates) or any(pid not in self.resolver.printings for pid in candidates):
            raise CollectionAuditError("candidate Printing identities must be distinct exact canonical IDs")

        states, histories = self._reviews(assessments, value, root)
        results = sorted(value["resolved_holdings"] + value["unresolved_holdings"],
                         key=lambda item: item["row"]["row_number"])
        aliases = defaultdict(list)
        for item in results:
            row = item["row"]
            provenance = row.get("provenance", {})
            if not isinstance(provenance, dict):
                raise CollectionAuditError("row provenance must be an object")
            alias = provenance.get("owned_lot_id")
            if alias is not None and not _known_text(alias):
                raise CollectionAuditError("owned lot alias must be explicit text or null")
            if alias and item["status"] != "duplicate_input_row":
                aliases[alias].append(row["row_number"])
        conflicts = {number for numbers in aliases.values() if len(numbers) > 1 for number in numbers}
        quantities = Counter()
        counts = Counter()
        by_card = defaultdict(list)
        by_printing = Counter()
        holdings = []
        unknown_quantity_rows = []
        for item in results:
            row = item["row"]
            number, quantity, status = row["row_number"], row.get("quantity"), item["status"]
            positive = _positive(quantity)
            if positive:
                quantities["source_valid_positive_quantity"] += quantity
            if not positive and not (type(quantity) is int and quantity <= 0):
                unknown_quantity_rows.append(number)
            exclusion = ("duplicate_input" if status == "duplicate_input_row" else
                         "invalid" if status == "invalid" else
                         "conflicting_lot" if number in conflicts else None)
            if exclusion:
                counts["excluded_" + exclusion + "_rows"] += 1
                if positive:
                    quantities["excluded_" + exclusion + "_quantity"] += quantity
            elif status in {"resolved", "ambiguous", "unresolved"} and positive:
                quantities[status + ("_quantity" if status == "resolved" else "_reported_quantity")] += quantity
            else:
                raise CollectionAuditError("unsupported resolution outcome or quantity")
            organization = _organization(row)
            ref = {"snapshot_id": value["snapshot_id"], "snapshot_digest": value["snapshot_digest"],
                   "source_import_digest": value["source_import_digest"], "row_number": number}
            holding = {"holding_ref": ref, "owned_lot_id": row.get("provenance", {}).get("owned_lot_id"),
                       "resolution_status": status, "reason": item["reason"], "exclusion": exclusion,
                       "reported_quantity": quantity, "quantity_state": "known_positive" if positive else "invalid_or_unknown",
                       "printing_id": item.get("printing_id"), "card_id": item.get("card_id"),
                       "candidate_printing_ids": item["candidate_printing_ids"],
                       "identity_evidence": item["evidence"], "dimension_conflicts": item.get("dimension_conflicts", []),
                       "canonical_reference": item.get("canonical_reference"), "row": row,
                       "storage_location": row.get("storage_location"), "organization": organization}
            holdings.append(holding)
            if status == "resolved" and not exclusion:
                by_card[item["card_id"]].append(holding)
                by_printing[item["printing_id"]] += quantity

        reported_total = sum(quantities[name] for name in
                             ("resolved_quantity", "ambiguous_reported_quantity", "unresolved_reported_quantity"))
        total_known = not unknown_quantity_rows and not conflicts and not quantities["excluded_invalid_quantity"]
        census = {name: quantities[name] for name in
                  ("source_valid_positive_quantity", "resolved_quantity", "ambiguous_reported_quantity",
                   "unresolved_reported_quantity", "excluded_duplicate_input_quantity", "excluded_invalid_quantity",
                   "excluded_conflicting_lot_quantity")}
        census.update({name: counts[name] for name in
                       ("excluded_duplicate_input_rows", "excluded_invalid_rows", "excluded_conflicting_lot_rows")})
        census.update(reported_total_quantity=reported_total,
                      confirmed_total_quantity=reported_total if total_known else None,
                      total_state="known_reported_total" if total_known else "incomplete_or_conflicting",
                      unknown_quantity_rows=unknown_quantity_rows, expected_total=expected_total,
                      expected_total_matches=(reported_total == expected_total) if total_known and expected_total is not None else None)
        census["conflicting_owned_lot_ids"] = [{"owned_lot_id": alias, "row_numbers": numbers}
                                              for alias, numbers in sorted(aliases.items()) if len(numbers) > 1]
        cards = []
        for card_id, items in sorted(by_card.items()):
            state = states.get(card_id, {"status": "pending", "ever_reviewed": False,
                                       "assessment_id": None, "history_ids": [], "review_basis": None})
            ever = state["ever_reviewed"]
            bulk = any(x["organization"]["storage_classification"] == "bulk" for x in items)
            cards.append({"card_id": card_id, "card_name": self.resolver.cards[card_id]["name"],
                          "quantity": sum(x["reported_quantity"] for x in items),
                          "printing_ids": sorted({x["printing_id"] for x in items}),
                          "review_status": state["status"], "ever_reviewed": ever,
                          "assessment_id": state["assessment_id"], "history_ids": state["history_ids"],
                          "review_basis": state["review_basis"], "new_discovery_eligible": not ever,
                          "unreviewed_bulk_eligible": bulk and not ever,
                          "holding_refs": [x["holding_ref"] for x in items],
                          "canonical_reference": items[0]["canonical_reference"]["card"]})
        review_census = {status: sorted(x["card_id"] for x in cards if x["review_status"] == status)
                        for status in REVIEW_STATES}
        review_census["unit"] = "unique_resolved_cards"
        review_census["counts"] = {status: len(review_census[status]) for status in REVIEW_STATES}
        review_census["review_basis_counts"] = {
            "synthetic_mock_assessments": sum(x["human_review"]["kind"] == "synthetic_mock" for x in histories),
            "approved_human_assessments": sum(x["status"] == "reviewed" and x["human_review"]["kind"] == "human" and x["human_review"]["approved"]
                                              for x in histories),
            "reviewed_cards_by_basis": dict(sorted(Counter(x["review_basis"] for x in cards
                                                            if x["review_status"] == "reviewed").items()))}
        from .assessments import assessment_inventory_compatible
        nonoperative = [record["assessment_id"] for record in histories
                        if not assessment_inventory_compatible(record, source=value["source"])]
        if nonoperative:
            review_census["nonoperative_assessment_ids"] = nonoperative
        organization = self._organization_groups(holdings)
        organization["new_discovery_card_ids"] = [x["card_id"] for x in cards if x["new_discovery_eligible"]]
        organization["unreviewed_bulk_card_ids"] = [x["card_id"] for x in cards if x["unreviewed_bulk_eligible"]]
        document = {"schema_version": AUDIT_VERSION, "collection_id": value["collection_id"],
                    "source_classification": self._source_classification(imported["source"]),
                    "bindings": {"snapshot_id": value["snapshot_id"], "snapshot_digest": value["snapshot_digest"],
                                 "source_import_digest": value["source_import_digest"],
                                 "canonical_snapshot_id": value["canonical_snapshot_id"],
                                 "source": {"relative_path": path.relative_to(root).as_posix(),
                                            "sha256": imported["source_import_digest"], "byte_count": len(original)},
                                 "assessment_ids": [x["assessment_id"] for x in histories]},
                    "quantity_census": census,
                    "identity_census": {"unique_cards": len(cards), "unique_printings": len(by_printing),
                                        "row_status_counts": dict(sorted(Counter(x["status"] for x in results).items()))},
                    "review_census": review_census, "holdings": holdings, "cards": cards,
                    "assessment_history": histories,
                    "duplicates": [{"printing_id": pid, "quantity": q, "copies_beyond_first": q - 1}
                                   for pid, q in sorted(by_printing.items()) if q > 1],
                    "organization": organization,
                    "ownership_coverage": self._ownership_coverage(candidates, holdings, by_printing),
                    "boundaries": {"canonical_write": False, "ownership_write": False,
                                   "automatic_reassessment": False, "acquisition_input_ready": False,
                                   "role_approval": False, "purchase_advice": False, "purchase_execution": False},
                    "limitations": ["Quantities are retained source declarations, not independently verified physical inventory.",
                                    "Storage classification and location do not establish strategic suitability or review status.",
                                    "Copies beyond the first are frequency facts, not surplus or disposition recommendations.",
                                    "Ownership coverage is informational; complete buyer-reviewed acquisition scope is not established."]}
        document["audit_id"] = digest(document)[:24]
        document["audit_digest"] = digest(document)
        return CollectionAuditDossier._from_verified(document)

    def _reviews(self, assessments, snapshot, source_root):
        from .assessments import (CollectionAssessment, assessment_review_states,
                                  validate_assessment_history)
        history = validate_assessment_history(tuple(assessments))
        documents = []
        for assessment in history:
            if not isinstance(assessment, CollectionAssessment):
                raise CollectionAuditError("assessment history requires validated source-bound records")
            record = assessment.to_dict()
            if record["collection_id"] != snapshot["collection_id"]:
                raise CollectionAuditError("assessment belongs to another collection")
            binding = record["snapshot_binding"]
            source_reference = binding["source_import_reference"]
            if source_reference["sha256"] != binding["source_import_digest"]:
                raise CollectionAuditError("assessment original import digest mismatch")
            original = snapshot
            if binding["snapshot_id"] != snapshot["snapshot_id"]:
                snapshots_root = (self.resolver.data_root / "collections" / "snapshots").resolve()
                path = (snapshots_root / (binding["snapshot_id"] + ".json")).resolve()
                if not path.is_relative_to(snapshots_root):
                    raise CollectionAuditError("assessment snapshot reference escapes collection snapshots")
                original = _snapshot_document(json.loads(path.read_bytes()))
            original, _, _, _, _ = self._verified_snapshot(
                original, source_path=source_reference["relative_path"], source_root=source_root)
            # A validated immutable record cannot gain human approval here; re-read
            # its retained bytes and original subject binding before using it.
            CollectionAssessment(record, source_root=source_root, snapshot=original,
                                 trusted_human_review=assessment.trusted_human_review)
            documents.append(record)
        return assessment_review_states(history, collection_id=snapshot["collection_id"],
                                        inventory_source=snapshot["source"]), documents

    @staticmethod
    def _source_classification(source):
        if not isinstance(source, dict):
            raise CollectionAuditError("collection source metadata must be an object")
        if any(source.get(name) is not None and not isinstance(source[name], str) for name in ("type", "mode", "notice")):
            raise CollectionAuditError("source classification text is invalid")
        synthetic = source.get("synthetic")
        declared_synthetic = source.get("mode") == "synthetic_demonstration" or source.get("type") in {"synthetic", "synthetic_fixture"}
        if synthetic is False and declared_synthetic:
            raise CollectionAuditError("contradictory collection source classification")
        if synthetic is None and declared_synthetic:
            synthetic = True
        real = source.get("real_user_inventory")
        if any(value is not None and type(value) is not bool for value in (synthetic, real)) or synthetic is True and real is True:
            raise CollectionAuditError("contradictory or invalid collection source classification")
        return {"type": source.get("type"), "mode": source.get("mode"), "synthetic": synthetic,
                "real_user_inventory": real, "notice": source.get("notice"),
                "metadata": source}

    @staticmethod
    def _organization_groups(holdings):
        groups = defaultdict(list)
        for item in holdings:
            if item["exclusion"]:
                continue
            key = (item["organization"]["storage_classification"], item["storage_location"])
            if key[1] is not None and not isinstance(key[1], str):
                raise CollectionAuditError("storage location must be text or null")
            groups[key].append(item)
        return {"groups": [{"storage_classification": key[0], "storage_location": key[1],
                            "reported_quantity": sum(x["reported_quantity"] for x in items),
                            "holding_refs": [x["holding_ref"] for x in items]}
                           for key, items in sorted(groups.items(), key=lambda pair: (str(pair[0][0]), str(pair[0][1])))]}

    @staticmethod
    def _ownership_coverage(candidates, holdings, by_printing):
        unresolved = [x["holding_ref"] for x in holdings
                      if x["resolution_status"] != "resolved" or x["exclusion"]]
        return {"schema_version": "collection-ownership-coverage-v1", "scope_complete": None,
                "acquisition_input_ready": False,
                "candidates": [{"printing_id": pid, "resolved_reported_quantity": by_printing[pid],
                                "owned_quantity": None, "ownership_state": "incomplete_scope",
                                "unresolved_evidence": unresolved}
                               for pid in sorted(candidates)]}

    def query(self, dossier, *, card_id=None, printing_id=None, card_name=None):
        """Expose exact identity requests and explicit name ambiguity without inference."""
        if not isinstance(dossier, CollectionAuditDossier):
            raise CollectionAuditError("queries require a validated immutable collection audit")
        if dossier["bindings"]["canonical_snapshot_id"] != self.resolver.canonical_snapshot_id:
            raise CollectionAuditError("collection query canonical snapshot changed")
        if sum(value is not None for value in (card_id, printing_id, card_name)) != 1:
            raise CollectionAuditError("provide one exact Card ID, Printing ID or Card name")
        if not _known_text(next(value for value in (card_id, printing_id, card_name) if value is not None)):
            raise CollectionAuditError("collection query identity must be explicit text")
        cards = _plain(dossier["cards"])
        matches = [x for x in cards if (x["card_id"] == card_id if card_id is not None else
                   printing_id in x["printing_ids"] if printing_id is not None else
                   x["card_name"].casefold() == str(card_name).casefold())]
        unresolved = []
        for item in dossier["holdings"]:
            if item["resolution_status"] == "resolved" and not item["exclusion"]:
                continue
            row = item["row"]
            possible_printings = {pid for pid in item["candidate_printing_ids"]
                                  if pid in self.resolver.printings}
            # Invalid quantities bypass ownership resolution. Preserve an exact
            # source Printing assertion for query relevance, without resolving
            # the lot or treating its unsupported quantity as owned copies.
            explicit_printing = row.get("printing_id")
            if isinstance(explicit_printing, str) and explicit_printing in self.resolver.printings:
                possible_printings.add(explicit_printing)
            possible_cards = {self.resolver.printings[pid]["card_id"] for pid in possible_printings}
            explicit_card = row.get("identity_constraints", {}).get("card_id")
            if isinstance(explicit_card, str) and explicit_card in self.resolver.cards:
                possible_cards.add(explicit_card)
            relevant = (card_id in possible_cards or row.get("identity_constraints", {}).get("card_id") == card_id
                        if card_id is not None else
                        printing_id in possible_printings or row.get("printing_id") == printing_id
                        if printing_id is not None else
                        (bool(row.get("card_name")) and str(row["card_name"]).casefold() == str(card_name).casefold()) or
                        any(self.resolver.cards[cid]["name"].casefold() == str(card_name).casefold()
                            for cid in possible_cards))
            if relevant:
                unresolved.append(item["holding_ref"])
        result = {"schema_version": "collection-audit-query-v1", "audit_id": dossier["audit_id"],
                "audit_digest": dossier["audit_digest"], "bindings": _plain(dossier["bindings"]),
                "source_classification": _plain(dossier["source_classification"]),
                "boundaries": _plain(dossier["boundaries"]),
                "review_basis_counts": _plain(dossier["review_census"]["review_basis_counts"]),
                "query": {"card_id": card_id, "printing_id": printing_id, "card_name": card_name},
                "identity_state": "ambiguous" if len(matches) > 1 or (card_name is not None and unresolved) else
                                  "resolved" if matches else "unresolved",
                "cards": matches, "unresolved_holding_refs": [_plain(ref) for ref in unresolved],
                "ownership_scope_complete": None,
                "ownership_state": "incomplete_or_conflicting" if unresolved else "reported_resolved_holdings_only"}
        if dossier["review_census"].get("nonoperative_assessment_ids"):
            result["nonoperative_assessment_ids"] = _plain(dossier["review_census"]["nonoperative_assessment_ids"])
        return result
