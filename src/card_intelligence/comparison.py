"""One read-only contextual comparison over existing evidence and decision contracts.

The MTG adapter validates a bounded, authored scenario. It neither interprets
arbitrary Oracle text nor approves roles, evaluates decks, or implements policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Mapping

from decision_intelligence import (AcquisitionDecisionOrchestrator, AnalysisMetric,
    DecisionAlternative, DecisionPolicy, DecisionRequest, DomainAnalysisEnvelope,
    EvidenceReference, MetricCriterion, recommendation_reasoning_context)
from decision_intelligence.models import identity as decision_identity
from jsonschema import Draft202012Validator
from reasoning import ReasoningContextRequest
from reasoning.models import freeze, thaw
from semantic import SemanticRequest

from .mechanics import content_identity, stable_json
from .roles import FunctionalRoleCandidate, FunctionalRolePilot


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "config/card_intelligence/contextual-comparison-pilot-v1.json"
VERSION = "contextual-card-comparison-v1"
MAXIMUM_BYTES = 65536
SELECTED_FIELDS = ("oracle_text", "mana_cost", "mana_value", "type_line", "color_identity")
REVIEW = {"status": "requires_review", "human_attestation": None, "canonical_admission": False}
_VALIDATOR = Draft202012Validator(json.loads(
    (ROOT / "src/schemas/v1/contextual-card-comparison-v1.schema.json").read_bytes()))


class ContextualComparisonError(ValueError):
    """The bounded comparison cannot preserve its evidence or review boundary."""


@dataclass(frozen=True)
class ContextualComparisonDossier:
    """Game-neutral, immutable result; deliberately not a canonical KnowledgeFact."""

    payload: Mapping[str, Any]

    def __post_init__(self):
        document = thaw(freeze(self.payload))
        errors = sorted(_VALIDATOR.iter_errors(document), key=lambda e: str(e.path))
        if errors:
            raise ContextualComparisonError(errors[0].message)
        body = dict(document)
        identity = body.pop("comparison_id")
        if identity != content_identity(body):
            raise ContextualComparisonError("comparison content identity mismatch")
        evidence_ids = [e["evidence_id"] for e in document["evidence"]]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ContextualComparisonError("duplicate evidence identity")
        context = document["context"]
        if document["context_identity"] != content_identity(context):
            raise ContextualComparisonError("context content identity mismatch")
        assumptions = {a["assumption_id"]: a for a in context["assumptions"]}
        if len(assumptions) != len(context["assumptions"]):
            raise ContextualComparisonError("duplicate context assumption")
        candidates = document["candidates"]
        ids = [c["card_identity"]["card_id"] for c in candidates]
        if len(set(ids)) != len(ids):
            raise ContextualComparisonError("duplicate comparison subject")
        for candidate in candidates:
            for role in candidate["pending_roles"]:
                FunctionalRoleCandidate(role)
                if role["subject"] != {k: candidate["card_identity"][k] for k in ("game_id", "card_id")}:
                    raise ContextualComparisonError("role belongs to another comparison subject")
                if role["mechanical_binding"]["dossier_id"] != candidate["mechanical_dossier_id"] or \
                        role["mechanical_binding"]["canonical_snapshot_id"] != document["canonical_snapshot_id"]:
                    raise ContextualComparisonError("role/mechanical snapshot mismatch")
            for hypothesis in candidate["strategic_hypotheses"]:
                if not set(hypothesis["evidence_ids"]) <= set(evidence_ids) or \
                        not set(hypothesis["assumption_ids"]) <= set(assumptions):
                    raise ContextualComparisonError("hypothesis references absent evidence or assumptions")
        for calculation in document["deterministic_comparisons"]:
            if not set(calculation["evidence_ids"]) <= set(evidence_ids) or \
                    not set(calculation["assumption_ids"]) <= set(assumptions) or \
                    not set(calculation["card_ids"]) <= set(ids):
                raise ContextualComparisonError("comparison references absent evidence, assumptions or subjects")
            if (calculation["state"] == "known") != (calculation["value"] is not None):
                raise ContextualComparisonError("unknown calculation must remain null")
        decision = document["decision_intelligence"]
        recommendation = decision["reasoning_context"]["recommendation"]
        content = {k: v for k, v in recommendation.items() if k != "recommendation_id"}
        if recommendation["recommendation_id"] != decision_identity("recommendation-sha256:", content):
            raise ContextualComparisonError("decision contract content identity mismatch")
        if recommendation["request_id"] != decision["request_id"] or \
                recommendation["outcome"] != "abstain" or recommendation["selected_alternative_id"] is not None or \
                not recommendation["abstention_reasons"]:
            raise ContextualComparisonError("pending comparison must abstain under the existing decision contract")
        if len(stable_json(document).encode()) > MAXIMUM_BYTES:
            raise ContextualComparisonError("comparison exceeds its byte bound")
        object.__setattr__(self, "payload", freeze(document))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    def to_json(self) -> str:
        return stable_json(self.to_dict())


class ContextualCardComparisonPilot:
    """Source-bound descriptive adapter; the existing engine owns abstention."""

    def __init__(self, data_root: Path, *, plan_path: Path | None = None):
        self.roles = FunctionalRolePilot(data_root)
        self.plan_path = Path(plan_path or PLAN)
        self.plan = json.loads(self.plan_path.read_bytes())
        p = self.plan
        if p["schema_version"] != "contextual-card-comparison-plan-v1":
            raise ContextualComparisonError("unsupported comparison plan")
        if p["game_id"] != self.roles.mechanical.query.game or \
                p["canonical_snapshot_id"] != self.roles.mechanical.snapshot_id:
            raise ContextualComparisonError("comparison canonical/game snapshot mismatch")
        ids = [c["card_id"] for c in p["cards"]]
        if not 2 <= len(ids) <= 3 or len(set(ids)) != len(ids) or not set(ids) <= set(self.roles.cards):
            raise ContextualComparisonError("two or three exact pending-pilot production IDs required")
        prepared = self._time(p["prepared_at"])
        if p["context"]["kind"] != "hypothetical_deck_context" or p["context"]["format_legality"]["status"] != "unknown":
            raise ContextualComparisonError("hypothetical context cannot establish format legality")
        assumptions = p["context"]["assumptions"]
        self.assumptions = {a["assumption_id"]: a for a in assumptions}
        if len(self.assumptions) != len(assumptions) or any(a["state"] != "supplied_assumption" for a in assumptions):
            raise ContextualComparisonError("context assumptions must be explicit, distinct supplied inputs")
        if self.assumptions.get("resolved_instructions", {}).get("value") is not True:
            raise ContextualComparisonError("instruction arithmetic requires an explicit resolution illustration")
        self.context_identity = content_identity(p["context"])
        self.plan_identity = content_identity(p)
        self.cards, self.evidence = [], []
        for annotation in sorted(p["cards"], key=lambda c: c["card_id"]):
            mechanical = self.roles.mechanical.dossier(annotation["card_id"]).to_dict()
            roles = self.roles.dossier(annotation["card_id"])
            if (annotation["name"], annotation["mechanical_dossier_id"], annotation["role_dossier_id"]) != \
                    (mechanical["card_identity"]["name"], mechanical["dossier_id"], roles["dossier_id"]):
                raise ContextualComparisonError("exact Card/mechanical/pending-role binding changed")
            if annotation["oracle_text"] != mechanical["fields"]["oracle_text"].get("value") or \
                    mechanical["source"]["resolution"] != "unique" or mechanical["faces"]:
                raise ContextualComparisonError("complete unique root Oracle evidence required; faces are outside this pilot")
            if prepared < self._time(roles["role_candidates"][0]["prepared_at"]):
                raise ContextualComparisonError("comparison preparation precedes pending evidence")
            if any(mechanical["fields"][f]["status"] != "known" for f in SELECTED_FIELDS):
                raise ContextualComparisonError("required mechanical comparison field is unknown")
            effect = annotation["literal_instruction_annotation"]
            # Literal quantities are authored and reviewed with the complete
            # bound passage; these checks do not claim semantic entailment.
            for key in ("draw_count", "mandatory_discard_count"):
                value = effect[key]
                if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                    raise ContextualComparisonError("instruction counts require nonnegative integers or explicit unknowns")
            parameter = effect["draw_parameter_assumption"]
            if (effect["draw_count"] is None) != (parameter is not None):
                raise ContextualComparisonError("variable draw must name an explicit supplied parameter")
            if parameter is not None:
                value = self.assumptions.get(parameter, {}).get("value")
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ContextualComparisonError("illustrative draw parameter is missing or unsupported")
            source = mechanical["source"]
            reference = EvidenceReference(mechanical["dossier_id"], source["acquisition_run_id"],
                source["record_content_identity"], source["source_timestamp"],
                source["retained_source_reference"] + f"#/{source['source_record_index']}")
            self.evidence.append(reference)
            self.evidence.extend(EvidenceReference(c["candidate_id"], "pending-functional-role-pilot",
                c["candidate_id"], c["prepared_at"], "data/review/functional-role-pilot/dossiers.jsonl")
                for c in roles["role_candidates"])
            self.cards.append({"card_identity": mechanical["card_identity"],
                "mechanical_dossier_id": mechanical["dossier_id"], "role_dossier_id": roles["dossier_id"],
                "mechanical_facts": {f: mechanical["fields"][f] for f in SELECTED_FIELDS},
                "source": source, "canonical_provenance": mechanical["canonical_provenance"],
                "pending_roles": roles["role_candidates"],
                "literal_instruction_annotation": {**effect, "review_status": "requires_review",
                    "basis": "source-bound engineer-authored reading, not automated rules interpretation"},
                "strategic_hypotheses": annotation["strategic_hypotheses"],
                "counterarguments": annotation["counterarguments"]})
        self.evidence.append(EvidenceReference(self.context_identity, "supplied-hypothetical-context",
            self.context_identity, p["prepared_at"], self.plan_path.name + "#/context"))
        self.policy = DecisionPolicy("pending-contextual-comparison-review-boundary", "1.0.0",
            (MetricCriterion("human_reviewed_context_match", "maximize"),), require_analysis_state_known=False)
        self._dossier = self._build()

    @staticmethod
    def _time(value: str) -> datetime:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ContextualComparisonError("retained UTC preparation timestamp required")
        return datetime.fromisoformat(value[:-1] + "+00:00")

    def _calculations(self) -> list[dict[str, Any]]:
        rows = []
        for index, left in enumerate(self.cards):
            for right in self.cards[index + 1:]:
                a, b = (Decimal(c["mechanical_facts"]["mana_value"]["value"]) for c in (left, right))
                difference = a - b
                rows.append({"calculation_id": "mana-value:" + left["card_identity"]["card_id"] + ":" + right["card_identity"]["card_id"],
                    "category": "deterministic_description", "operation": "left_minus_right_mana_value",
                    "card_ids": [c["card_identity"]["card_id"] for c in (left, right)],
                    "state": "known", "value": format(difference, "f"), "unit": "mana_value",
                    "evidence_ids": [c["mechanical_dossier_id"] for c in (left, right)], "assumption_ids": [],
                    "limitations": "Mana value is not actual payment, castability, total resource cost, or universal efficiency."})
        for card in self.cards:
            effect = card["literal_instruction_annotation"]
            parameter = effect["draw_parameter_assumption"]
            draw = self.assumptions[parameter]["value"] if parameter else effect["draw_count"]
            discard = effect["mandatory_discard_count"]
            rows.append({"calculation_id": "draw-minus-discard:" + card["card_identity"]["card_id"],
                "category": "conditional_instruction_arithmetic", "operation": "draw_count_minus_mandatory_discard_count",
                "card_ids": [card["card_identity"]["card_id"]],
                "state": "known" if discard is not None else "unknown",
                "value": draw - discard if discard is not None else None, "unit": "instruction_count_difference",
                "inputs": {"draw_count": draw, "mandatory_discard_count": discard},
                "evidence_ids": [card["mechanical_dossier_id"], self.context_identity],
                "assumption_ids": ["resolved_instructions", *([parameter] if parameter else [])],
                "limitations": "Conditional on the pending literal annotation and supplied illustration. Not net card advantage: casting-card expenditure, creature sacrifice, setup, resolution, hand/library availability and opportunity cost are excluded."})
        return rows

    def _build(self) -> ContextualComparisonDossier:
        alternatives = tuple(DecisionAlternative(c["card_identity"]["card_id"], "COMPARE_IN_DECLARED_CONTEXT",
            (c["card_identity"]["card_id"],), {"mechanical_dossier_id": c["mechanical_dossier_id"],
                "role_dossier_id": c["role_dossier_id"], "review_status": "requires_review"}) for c in self.cards)
        request = DecisionRequest(self.plan["context"]["objective"], alternatives,
            {"winner_requires_human_reviewed_context_match": True, "selection_authorized": False},
            {}, {"context_identity": self.context_identity, "comparison_plan_identity": self.plan_identity},
            tuple(self.evidence), self.policy.policy_id, self.policy.version,
            {"context": "hypothetical", "role_approval": "pending", "strategic_suitability": "unknown"},
            (self.roles.mechanical.snapshot_id, self.plan_identity, self.context_identity))
        analyses = []
        for card in self.cards:
            evidence = tuple(e for e in self.evidence if e.evidence_id in
                {card["mechanical_dossier_id"], self.context_identity})
            analyses.append(DomainAnalysisEnvelope("card-intelligence-contextual-comparison", "1.0.0",
                card["card_identity"]["card_id"], (
                    AnalysisMetric("human_reviewed_context_match", "unknown", uncertainty={
                        "reason": "No human role attestation, verified deck state, suitability result or approved selection policy is available."},
                        evidence_ids=tuple(e.evidence_id for e in evidence)),),
                evidence, state="incomplete", assumptions=tuple(a["description"] for a in self.assumptions.values()),
                limitations=tuple(self.plan["context"]["unknowns"]), input_snapshot_ids=request.input_snapshot_ids))
        recommendation = AcquisitionDecisionOrchestrator().evaluate(request, analyses, self.policy)
        self._decision_inputs = freeze({"request": request.to_dict(), "policy": self.policy.to_dict(),
                                        "analyses": [a.to_dict() for a in analyses]})
        document = {"schema_version": VERSION, "canonical_main_baseline": self.plan["canonical_main_baseline"],
            "canonical_snapshot_id": self.roles.mechanical.snapshot_id, "prepared_at": self.plan["prepared_at"],
            "plan_identity": self.plan_identity, "context_identity": self.context_identity,
            "context": self.plan["context"], "criteria": self.plan["criteria"], "candidates": self.cards,
            "evidence": [e.to_dict() for e in sorted(self.evidence, key=lambda e: e.evidence_id)],
            "deterministic_comparisons": self._calculations(),
            "decision_intelligence": {"request_id": request.request_id, "policy": self.policy.to_dict(),
                "input_reference": "data/review/contextual-card-comparison/decision-inputs.json",
                "input_content_identity": content_identity(thaw(self._decision_inputs)),
                "reasoning_context": recommendation_reasoning_context(recommendation)},
            "review": REVIEW,
            "omissions": {"selected_cards_omitted": 0, "selected_role_candidates_omitted": 0,
                "mechanical_fields": "Only five root fields are repeated; complete mechanical dossiers and full source-record hashes are referenced.",
                "unselected_cards": "The other production Cards and unlisted roles are unassessed, not inferior or absent."},
            "unsupported_dimensions": ["net_card_advantage", "format_legality", "verified_rules_timing",
                "competitive_superiority", "universal_best_in_slot", "combo_strength", "synergy_correctness",
                "automatic_deck_optimization", "market_or_acquisition_recommendations"],
            "protection_boundary": {"canonical_writes": False, "knowledge_fact_writes": False,
                "market_admission": False, "approval_performed": False}}
        document["comparison_id"] = content_identity(document)
        return ContextualComparisonDossier(document)

    def dossier(self) -> ContextualComparisonDossier:
        return self._dossier

    def decision_inputs(self) -> dict[str, Any]:
        """Complete existing contracts retained separately to avoid duplication."""
        return thaw(self._decision_inputs)

    def reasoning_context(self) -> dict[str, Any]:
        # The full comparison supplies compact canonical lineage and exact
        # source bindings for all three subjects. Bound the generic retrieval
        # copies at zero rather than duplicate large entity audit projections.
        # Existing contracts report every omitted item; no request is altered.
        contexts = [self.roles.mechanical.context_builder.build(ReasoningContextRequest(
            SemanticRequest("find_identifier", {"identifier": c["card_identity"]["card_id"], "entity_type": "card"}),
            requested_entity_types=("card",), maximum_entities=0, maximum_relationships=0,
            maximum_evidence_items=0)).to_dict() for c in self.cards]
        if any(c["canonical_snapshot_id"] != self.roles.mechanical.snapshot_id for c in contexts):
            raise ContextualComparisonError("manual handoff snapshot mismatch")
        result = {"schema_version": "contextual-card-comparison-handoff-v1",
            "instruction": "Explain this manual repository comparison. Keep provider facts, pending interpretations, supplied assumptions and conditional arithmetic separate. Preserve abstention; add no facts, legality, rankings or recommendations.",
            "canonical_contexts": contexts, "comparison": self._dossier.to_dict(),
            "retrieval_scope": "Three unchanged exact-identity retrieval contracts verify the common snapshot. Generic entity/evidence copies are deliberately omitted; the manual comparison carries every selected Card identity, compact canonical lineage, source binding and pending role candidate.",
            "omissions": {"comparison_candidates_omitted": 0, "comparison_role_candidates_omitted": 0,
                "canonical_contexts": [c["omitted_item_counts"] for c in contexts],
                "generic_canonical_projection": "Entire generic entity/evidence copies are omitted to avoid repeating large audit projections. Complete source/dossier content identities and compact canonical provenance are retained in the comparison."},
            "maximum_serialized_bytes": MAXIMUM_BYTES, "live_model_or_transport": False}
        result["handoff_id"] = content_identity(result)
        if len(stable_json(result).encode()) > MAXIMUM_BYTES:
            raise ContextualComparisonError("comparison reasoning handoff exceeds its byte bound")
        return result


def comparison_explanation(dossier: ContextualComparisonDossier) -> str:
    """Manual example rendering only facts, proposals and caveats in the dossier."""
    d = dossier.to_dict()
    lines = ["# Contextual Card comparison — manual explanation example", "",
        "Comparison: `" + d["comparison_id"] + "`. Human review is pending; no canonical admission or live ChatGPT integration.", "",
        "## Declared hypothetical context", "", d["context"]["description"], "",
        "Objective: " + d["context"]["objective"], ""]
    lines.extend("- Supplied assumption: " + a["description"] for a in d["context"]["assumptions"])
    for c in d["candidates"]:
        fields = c["mechanical_facts"]
        lines.extend(["", "## " + c["card_identity"]["name"], "",
            "Exact production Card: `" + c["card_identity"]["card_id"] + "`.", "",
            "Source-verified provider assertions: mana cost `" + fields["mana_cost"]["value"] +
            "`, mana value `" + fields["mana_value"]["value"] + "`, type `" + fields["type_line"]["value"] + "`.",
            "Source observation: `" + c["source"]["source_timestamp"] + "`; retrieval: `" + c["source"]["retrieved_at"] + "`.", "",
            "Retained Oracle text:", ""])
        lines.extend("> " + text for text in fields["oracle_text"]["value"].splitlines())
        lines.extend(["", "Pending functional interpretations:", ""])
        for role in c["pending_roles"]:
            lines.append("- " + role["role_reference"]["role_id"] + " (" + role["value"]["status"] +
                         "; requires_review): " + (role["value"]["data"] or role["basis_explanation"]))
            for key in ("costs", "conditions", "restrictions"):
                lines.extend("  - " + key + ": " + text for text in role["qualifiers"][key])
            lines.append("  - timing: " + role["qualifiers"]["timing"]["description"])
        for h in c["strategic_hypotheses"]:
            lines.extend(["", "Unverified strategic hypothesis: " + h["statement"], "",
                          "Counterargument: " + h["counterargument"]])
        lines.extend(["", "Evidence: `" + c["mechanical_dossier_id"] + "`; pending dossier `" + c["role_dossier_id"] + "`."])
    lines.extend(["", "## Deterministic descriptions and conditional arithmetic", ""])
    names = {c["card_identity"]["card_id"]: c["card_identity"]["name"] for c in d["candidates"]}
    for calc in d["deterministic_comparisons"]:
        label = " / ".join(names[i] for i in calc["card_ids"])
        lines.extend(["- " + label + ": `" + calc["operation"] + "` = `" + str(calc["value"]) +
            "` (" + calc["state"] + ", " + calc["unit"] + "). " + calc["limitations"]])
    lines.extend(["", "## Unknowns and abstention", ""])
    lines.extend("- " + text for text in d["context"]["unknowns"])
    recommendation = d["decision_intelligence"]["reasoning_context"]["recommendation"]
    lines.extend(["", "Existing Decision Intelligence outcome: **" + recommendation["outcome"].upper() + "**. No Card is selected.", ""])
    lines.extend("- " + reason for reason in recommendation["abstention_reasons"])
    lines.extend(["", "This example preserves the mechanical / pending-interpretation / supplied-assumption boundary. It cannot establish net card advantage, format legality, a superior choice or a verified interaction."])
    return "\n".join(lines).rstrip("\n") + "\n"
