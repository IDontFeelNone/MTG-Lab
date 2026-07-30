"""Canonical repository access."""

from .cards import (
    CardRepositoryError,
    canonical_repository_bytes,
    card_record_path,
    load_card,
    load_card_repository,
    load_printing,
    printing_record_path,
)
from .canonical import (
    CanonicalRepository, CanonicalRepositoryError, load_canonical_repository,
)
from .evidence import (
    ArchivedEvidence,
    EvidenceBundle,
    EvidenceRepositoryError,
    evidence_manifest_path,
    load_evidence_bundle,
)
from .products import ProductLoadError, load_product, product_record_path
from .sources import SourceLoadError, load_acquisition_manifest, load_source_record
from .promotion import (
    CandidatePromotionService,
    CandidateReview,
    PromotionConflict,
    PromotionValidationError,
    ReviewDecision,
)
from .rule_research import RuleResearchError, load_rule_research, rule_research_bytes
from .rules import (
    RulesRepositoryError,
    canonical_rules_repository_bytes,
    load_print_sheet,
    load_rules_repository,
    load_slot,
    print_sheet_record_path,
    slot_record_path,
)

__all__ = [
    "CardRepositoryError",
    "CanonicalRepository",
    "CanonicalRepositoryError",
    "ArchivedEvidence",
    "CandidatePromotionService",
    "CandidateReview",
    "EvidenceBundle",
    "EvidenceRepositoryError",
    "ProductLoadError",
    "PromotionConflict",
    "PromotionValidationError",
    "ReviewDecision",
    "RuleResearchError",
    "RulesRepositoryError",
    "SourceLoadError",
    "canonical_repository_bytes",
    "canonical_rules_repository_bytes",
    "card_record_path",
    "evidence_manifest_path",
    "load_acquisition_manifest",
    "load_card",
    "load_canonical_repository",
    "load_card_repository",
    "load_evidence_bundle",
    "load_printing",
    "load_print_sheet",
    "load_product",
    "load_source_record",
    "load_rule_research",
    "load_rules_repository",
    "load_slot",
    "print_sheet_record_path",
    "printing_record_path",
    "product_record_path",
    "rule_research_bytes",
    "slot_record_path",
]
