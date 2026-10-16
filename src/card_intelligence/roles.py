"""Bounded functional-role review preparation, never canonical fact admission.

The shared candidate envelope is game-neutral. Role semantics and the exact pilot
are supplied as versioned data. No keyword, text search, or model assigns roles.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from reasoning.models import freeze, thaw

from .mechanics import MechanicalCardIntelligence, content_identity, stable_json
from .models import Evidence


CANDIDATE_VERSION = "functional-role-candidate-v1"
DOSSIER_VERSION = "functional-role-dossier-v1"
MAXIMUM_BYTES = 65536
ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/card_intelligence"
_VALIDATOR = Draft202012Validator(json.loads(
    (ROOT / "src/schemas/v1/functional-role-candidate-v1.schema.json").read_bytes()))


class FunctionalRoleError(ValueError):
    """A proposal lacks its exact evidence binding or violates the review boundary."""


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise FunctionalRoleError("retained UTC timestamp required")
    return datetime.fromisoformat(value[:-1] + "+00:00")


@dataclass(frozen=True)
class FunctionalRoleCandidate:
    """Immutable proposed assertion, deliberately incompatible with KnowledgeFact."""

    payload: Mapping[str, Any]

    def __post_init__(self):
        body = thaw(freeze(self.payload))
        errors = sorted(_VALIDATOR.iter_errors(body), key=lambda e: str(e.path))
        if errors:
            raise FunctionalRoleError(errors[0].message)
        identity = body.pop("candidate_id")
        if content_identity(body) != identity:
            raise FunctionalRoleError("candidate content identity mismatch")
        state, basis = body["value"]["status"], body["basis"]
        if basis == "direct_mechanical" and state != "known":
            raise FunctionalRoleError("direct functionality requires known mechanical support")
        if basis == "contextual_interpretation" and state not in {"incomplete", "unknown"}:
            raise FunctionalRoleError("strategic interpretation must remain incomplete or unknown")
        if (basis == "unsupported_claim") != (state == "unsupported"):
            raise FunctionalRoleError("unsupported claims cannot become positive roles")
        if (state in {"unknown", "unsupported"}) != (body["value"]["data"] is None):
            raise FunctionalRoleError("unknown and unsupported functions must be null")
        if basis == "contextual_interpretation" and not body["context_dependencies"]:
            raise FunctionalRoleError("contextual interpretations require explicit dependencies")
        if identity in body["supersedes"] or len(body["supersedes"]) != len(set(body["supersedes"])):
            raise FunctionalRoleError("invalid candidate supersession references")
        prepared = _time(body["prepared_at"])
        for evidence in [*body["evidence"], *body["prominence"]["context_evidence"]]:
            retained = Evidence(**{**evidence, "observed_at": _time(evidence["observed_at"])})
            if retained.observed_at > prepared:
                raise FunctionalRoleError("preparation cannot precede its supplied evidence")
        binding = body["mechanical_binding"]
        lines = binding["source_field_value"].splitlines()
        indices = binding["ability_line_indices"]
        if any(i >= len(lines) for i in indices) or binding["ability_lines"] != [lines[i] for i in indices]:
            raise FunctionalRoleError("ability evidence must retain complete source lines")
        object.__setattr__(self, "payload", freeze({**body, "candidate_id": identity}))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    def to_json(self) -> str:
        return stable_json(self.to_dict())


def validate_role_supersession(candidate: FunctionalRoleCandidate,
                              previous: tuple[FunctionalRoleCandidate, ...]) -> None:
    """Validate a replacement proposal without storing or approving either record."""
    document = candidate.to_dict()
    by_id = {old.to_dict()["candidate_id"]: old.to_dict() for old in previous}
    for identifier in document["supersedes"]:
        if identifier not in by_id:
            raise FunctionalRoleError("missing superseded role candidate")
        old = by_id[identifier]
        if (old["subject"], old["role_reference"]) != (document["subject"], document["role_reference"]):
            raise FunctionalRoleError("supersession must preserve subject and role definition")
        if _time(old["prepared_at"]) >= _time(document["prepared_at"]):
            raise FunctionalRoleError("supersession must advance preparation time")


class FunctionalRolePilot:
    """Validate explicitly authored proposals for exactly the configured pilot IDs."""

    def __init__(self, data_root: Path, *, plan_path: Path | None = None,
                 vocabulary_path: Path | None = None):
        self._initialize(MechanicalCardIntelligence(data_root), plan_path=plan_path,
                         vocabulary_path=vocabulary_path)

    @classmethod
    def from_mechanical(cls, mechanical: MechanicalCardIntelligence, *,
                        plan_path: Path | None = None,
                        vocabulary_path: Path | None = None) -> FunctionalRolePilot:
        """Reuse one verified attachment-backed mechanical/query chain.

        The outer catalog binding stays outside the historical v1 artifacts.
        This construction path neither approves proposals nor admits facts.
        """
        if not isinstance(mechanical, MechanicalCardIntelligence) or mechanical.catalog_binding is None:
            raise FunctionalRoleError("attachment-backed MechanicalCardIntelligence required")
        result = cls.__new__(cls)
        try:
            result._initialize(mechanical, plan_path=plan_path, vocabulary_path=vocabulary_path)
        except OSError:
            raise FunctionalRoleError("role plan or vocabulary dependency unavailable") from None
        result._attached_mechanical = mechanical
        result._attached_query = mechanical.query
        result._bound_catalog = freeze(mechanical.catalog_binding)
        result._expected_snapshot_id = mechanical.snapshot_id
        result._bound_plan_path = result.plan_path
        result._bound_vocabulary_path = result.vocabulary_path
        result._bound_files = result._loaded_files
        result._bound_state = result._state_identity()
        result.verify_inputs()
        return result

    def _initialize(self, mechanical, *, plan_path=None, vocabulary_path=None):
        self._attached_mechanical = None
        self.mechanical = mechanical
        self.plan_path = Path(plan_path or CONFIG / "functional-role-pilot-v1.json")
        self.vocabulary_path = Path(vocabulary_path or CONFIG / "functional-role-vocabulary-v1.json")
        plan_bytes = self.plan_path.read_bytes()
        vocabulary_bytes = self.vocabulary_path.read_bytes()
        self._loaded_files = tuple(hashlib.sha256(raw).hexdigest()
                                   for raw in (plan_bytes, vocabulary_bytes))
        self.plan = json.loads(plan_bytes)
        self.vocabulary = json.loads(vocabulary_bytes)
        if self.plan["schema_version"] != "functional-role-pilot-plan-v1" or \
                self.vocabulary["schema_version"] != "functional-role-vocabulary-v1":
            raise FunctionalRoleError("unsupported role preparation contract")
        for definition in self.vocabulary["roles"].values():
            if set(definition) != {"label", "definition", "evidence_requirements", "allowed_bases"} or \
                    not definition["evidence_requirements"] or \
                    any(not isinstance(v, str) or not v.strip() for v in
                        [definition["label"], definition["definition"], *definition["evidence_requirements"]]) or \
                    not set(definition["allowed_bases"]) <= {"direct_mechanical", "contextual_interpretation", "unsupported_claim"}:
                raise FunctionalRoleError("role definition needs explicit semantics and evidence requirements")
        if self.plan["vocabulary_id"] != self.vocabulary["vocabulary_id"]:
            raise FunctionalRoleError("pilot vocabulary identity mismatch")
        if self.plan["canonical_snapshot_id"] != self.mechanical.snapshot_id:
            raise FunctionalRoleError("pilot canonical snapshot mismatch")
        if self.plan["game_id"] != self.mechanical.query.game or self.vocabulary["game_id"] != self.plan["game_id"]:
            raise FunctionalRoleError("pilot game identity mismatch")
        _time(self.plan["prepared_at"])
        self.plan_identity = content_identity(self.plan)
        self.vocabulary_identity = content_identity(self.vocabulary)
        records = self.plan["cards"]
        if not 10 <= len(records) <= 15:
            raise FunctionalRoleError("role preparation is limited to a 10–15 Card pilot")
        self.cards = {c["card_id"]: c for c in records}
        if len(self.cards) != len(records) or not set(self.cards) <= set(self.mechanical.cards):
            raise FunctionalRoleError("duplicate or nonproduction pilot Card identity")
        if not set(self.plan["comparison_card_ids"]) <= set(self.cards) or \
                not 2 <= len(set(self.plan["comparison_card_ids"])) <= 3:
            raise FunctionalRoleError("comparison requires two or three distinct pilot Cards")
        self._dossiers = {}
        for card_id in sorted(self.cards):
            self._dossiers[card_id] = freeze(self._build(card_id))

    def _input_fingerprint(self) -> tuple[str, str]:
        try:
            return tuple(hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (self.plan_path, self.vocabulary_path))
        except OSError:
            raise FunctionalRoleError("role plan or vocabulary dependency unavailable") from None

    def _state_identity(self) -> str:
        return content_identity({"plan": self.plan, "vocabulary": self.vocabulary,
            "plan_identity": self.plan_identity, "vocabulary_identity": self.vocabulary_identity,
            "cards": self.cards, "dossiers": thaw(freeze(self._dossiers))})

    def verify_inputs(self) -> None:
        """Fail closed on attached input drift; historical construction is unchanged."""
        mechanical = self._attached_mechanical
        if mechanical is None:
            return
        if self.mechanical is not mechanical or mechanical.query is not self._attached_query:
            raise FunctionalRoleError("attached role mechanical/query binding changed")
        # The binding property validates the mechanical source and catalog once.
        binding = mechanical.catalog_binding
        if (not isinstance(self.plan, Mapping)
                or mechanical.snapshot_id != self._expected_snapshot_id
                or self.plan.get("canonical_snapshot_id") != self._expected_snapshot_id
                or mechanical.query.game != self.plan.get("game_id")
                or binding != thaw(self._bound_catalog)):
            raise FunctionalRoleError("attached role catalog snapshot binding changed")
        try:
            intact = not (self.plan_path != self._bound_plan_path
                or self.vocabulary_path != self._bound_vocabulary_path
                or self._input_fingerprint() != self._bound_files
                or self._state_identity() != self._bound_state)
        except (ValueError, TypeError, AttributeError):
            intact = False
        if not intact:
            raise FunctionalRoleError("attached role plan, vocabulary or dossier binding changed")

    @property
    def catalog_binding(self) -> dict[str, Any] | None:
        """Defensive outer binding, deliberately absent from retained artifacts."""
        if self._attached_mechanical is None:
            return None
        self.verify_inputs()
        return thaw(self._bound_catalog)

    def _build(self, card_id: str) -> dict[str, Any]:
        annotation = self.cards[card_id]
        mechanical = self.mechanical.dossier(card_id).to_dict()
        if annotation["name"] != mechanical["card_identity"]["name"] or \
                annotation["mechanical_dossier_id"] != mechanical["dossier_id"]:
            raise FunctionalRoleError("exact Card/mechanical dossier binding changed")
        if mechanical["source"]["resolution"] != "unique":
            raise FunctionalRoleError("unique source binding required for role preparation")
        candidates = []
        roles = annotation["roles"]
        if not roles or len({r["role_id"] for r in roles}) != len(roles):
            raise FunctionalRoleError("missing or duplicated proposed role")
        for role in sorted(roles, key=lambda r: r["role_id"]):
            definition = self.vocabulary["roles"].get(role["role_id"])
            if not definition or role["basis"] not in definition["allowed_bases"]:
                raise FunctionalRoleError("unknown role or unsupported evidence basis")
            field = mechanical["fields"]["oracle_text"]
            if field["status"] != "known" or annotation["oracle_text"] != field["value"]:
                raise FunctionalRoleError("complete literal Oracle evidence binding required")
            indices = role["evidence_lines"]
            lines = field["value"].splitlines()
            if not indices or any(isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(lines) for i in indices):
                raise FunctionalRoleError("invalid complete ability-line selection")
            selected = [lines[i] for i in indices]
            # The entire Oracle field is also supplied. Selecting an outcome
            # substring cannot hide a cost, condition, or later sentence.
            evidence = Evidence(source_id=mechanical["source"]["acquisition_run_id"],
                source_type="retained_dataset", observed_at=_time(mechanical["source"]["source_timestamp"]),
                reference=mechanical["source"]["retained_source_reference"] +
                    f"#/{mechanical['source']['source_record_index']}{field['source_pointer']}",
                claim="Retained provider Oracle assertion: " + "\n".join(selected))
            payload = {"schema_version": CANDIDATE_VERSION,
                "subject": {"game_id": self.plan["game_id"], "card_id": card_id},
                "role_reference": {"vocabulary_id": self.vocabulary["vocabulary_id"],
                    "vocabulary_content_identity": self.vocabulary_identity, "role_id": role["role_id"]},
                "basis": role["basis"], "value": {"status": role["state"], "data": role["function"]},
                "basis_explanation": role["explanation"],
                "prominence": {"status": "unknown", "designation": None,
                    "reason": "No deck objective or human role-priority assessment is retained.", "context_evidence": []},
                "qualifiers": {key: role[key] for key in ("costs", "conditions", "timing", "restrictions")},
                "context_dependencies": role["context_dependencies"], "limitations": role["limitations"],
                "evidence": [evidence.to_dict()],
                "mechanical_binding": {"dossier_id": mechanical["dossier_id"],
                    "canonical_snapshot_id": mechanical["canonical_snapshot_id"],
                    "record_content_identity": mechanical["source"]["record_content_identity"],
                    "retained_source_sha256": mechanical["source"]["retained_source_sha256"],
                    "source_pointer": field["source_pointer"], "source_field_name": "oracle_text",
                    "source_field_value": field["value"],
                    "ability_line_indices": indices, "ability_lines": selected,
                    "context_metadata": {"card_mana_cost": mechanical["fields"]["mana_cost"],
                                         "card_type_line": mechanical["fields"]["type_line"]}},
                "preparation": {"method": "engineer-authored interpretation; deterministic source binding",
                    "annotation_plan_identity": self.plan_identity}, "prepared_at": self.plan["prepared_at"],
                "supersedes": role["supersedes"],
                "review": {"status": "requires_review", "human_attestation": None,
                           "canonical_admission": False}}
            payload["candidate_id"] = content_identity(payload)
            candidate = FunctionalRoleCandidate(payload)
            validate_role_supersession(candidate, ())
            candidates.append(candidate.to_dict())
        dossier = {"schema_version": DOSSIER_VERSION, "card_identity": mechanical["card_identity"],
            "canonical_snapshot_id": mechanical["canonical_snapshot_id"],
            "mechanical_dossier_id": mechanical["dossier_id"], "source": mechanical["source"],
            "canonical_provenance": mechanical["canonical_provenance"],
            "selection_reason": annotation["selection_reason"], "role_candidates": candidates,
            "review_status": "requires_review", "human_attestation": None,
            "omissions": {"pilot_role_candidates_omitted": 0,
                "unassessed_roles": "Vocabulary roles absent from this dossier are unassessed, not known absent.",
                "mechanical_fields": "The complete immutable mechanical dossier is referenced, not duplicated."},
            "unsupported_dimensions": ["canonical_role_admission", "automatic_full_cohort_classification",
                "universal_role_priority", "net_card_advantage", "verified_rules_interactions",
                "verified_combos", "synergy_strength", "competitive_rankings", "best_in_slot",
                "deck_optimization", "acquisition_decisions"],
            "protection_boundary": {"canonical_writes": False, "knowledge_fact_writes": False,
                                    "market_admission": False, "approval_performed": False}}
        dossier["dossier_id"] = content_identity(dossier)
        if len(stable_json(dossier).encode()) > MAXIMUM_BYTES:
            raise FunctionalRoleError("role dossier exceeds its byte bound")
        return dossier

    def dossier(self, card_id: str) -> dict[str, Any]:
        self.verify_inputs()
        if card_id not in self._dossiers:
            raise FunctionalRoleError("exact authorized pilot Card ID required; no cohort classifier")
        result = thaw(self._dossiers[card_id])
        self.verify_inputs()
        return result

    def report(self) -> dict[str, Any]:
        self.verify_inputs()
        documents = [self.dossier(i) for i in sorted(self.cards)]
        census = []
        frequencies, states = Counter(), Counter()
        for d in documents:
            claims = d["role_candidates"]
            for c in claims:
                states[c["value"]["status"]] += 1
                if c["value"]["status"] == "known": frequencies[c["role_reference"]["role_id"]] += 1
            census.append({"card_identity": d["card_identity"], "dossier_id": d["dossier_id"],
                "known_function_roles": [c["role_reference"]["role_id"] for c in claims if c["value"]["status"] == "known"],
                "other_proposals": [{"role_id": c["role_reference"]["role_id"], "state": c["value"]["status"]}
                                    for c in claims if c["value"]["status"] != "known"],
                "review_status": "requires_review"})
        report = {"schema_version": "functional-role-pilot-report-v1", "pilot_card_count": len(documents),
            "production_cohort_card_count": len(self.mechanical.cards),
            "canonical_snapshot_id": self.mechanical.snapshot_id, "annotation_plan_identity": self.plan_identity,
            "vocabulary_content_identity": self.vocabulary_identity,
            "candidate_count": sum(states.values()), "candidate_state_counts": dict(states),
            "known_function_role_frequencies": dict(frequencies), "per_card_census": census,
            "human_review": {"status": "requires_review", "attestation": None,
                "canonical_admission_eligible": False, "required_review": [
                    "Review role definitions and the exact source-bound ability text.",
                    "Verify qualifiers, benefits, costs, targeting, conditions and restrictions.",
                    "Resolve contextual interpretations and prominence using separately retained context.",
                    "Approve any later knowledge admission separately; this pilot has no admission function."]},
            "limitations": self.plan["coverage_limitations"],
            "scope": "bounded proposed functionality; no strength, combo correctness, or complete-cohort claim"}
        report["report_id"] = content_identity(report)
        self.verify_inputs()
        return report

    def comparison(self) -> dict[str, Any]:
        self.verify_inputs()
        rows = []
        for card_id in sorted(set(self.plan["comparison_card_ids"])):
            d = self.dossier(card_id)
            rows.append({"card_identity": d["card_identity"], "dossier_id": d["dossier_id"],
                         "role_candidates": d["role_candidates"]})
        role_sets = [{c["role_reference"]["role_id"] for c in r["role_candidates"]
                      if c["value"]["status"] == "known"} for r in rows]
        report = {"schema_version": "functional-role-comparison-v1", "cards": rows,
            "shared_known_function_roles": sorted(set.intersection(*role_sets)),
            "review_status": "requires_review", "canonical_snapshot_id": self.mechanical.snapshot_id,
            "interpretation": "Compare proposed outcomes and explicit restrictions. No ranking, substitute verdict, net advantage, or verified interaction is computed."}
        report["comparison_id"] = content_identity(report)
        self.verify_inputs()
        return report

    def reasoning_context(self, card_id: str):
        self.verify_inputs()
        dossier = self.dossier(card_id)
        base = self.mechanical.reasoning_context(card_id)
        b = base.to_dict()
        analytics = [*b["analytics_results"],
                     {"projection": "functional_role_review_pilot_manual_handoff", "dossier": dossier}]
        warnings = sorted(set([*b["warnings"],
            "Functional roles are engineer-authored review candidates; no human approval or canonical admission."]))
        truncation = {**b["truncation"], "role_supplement": {"maximum_serialized_bytes": MAXIMUM_BYTES,
                        "role_candidates_omitted": 0, "review_status": "requires_review"}}
        content = {"canonical_snapshot_id": b["canonical_snapshot_id"], "analytics_snapshot_id": None,
            "request": b["normalized_request"], "entities": b["entities"], "relationships": b["relationships"],
            "analytics": analytics, "provenance": b["provenance_references"], "evidence": b["evidence_references"],
            "omitted": b["omitted_item_counts"], "truncation": truncation, "warnings": warnings}
        result = replace(base, context_id=content_identity(content), analytics_results=analytics,
                         truncation=truncation, warnings=warnings, analytics_snapshot_id=None)
        if len(result.to_json().encode()) > MAXIMUM_BYTES:
            raise FunctionalRoleError("role reasoning context exceeds its byte bound")
        self.verify_inputs()
        return result
