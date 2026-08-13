"""Safe AI-facing projection: ChatGPT explains, and never reconstructs, a decision."""
from .models import StructuredRecommendation

def recommendation_reasoning_context(recommendation: StructuredRecommendation) -> dict:
    """Return the complete deterministic recommendation in a bounded versioned envelope."""
    return {"schema_version":"decision-reasoning-context-v1",
            "instruction":"Explain this repository-produced result without changing the outcome, calculating a new outcome, or inventing evidence.",
            "recommendation":recommendation.to_dict()}
