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
from .products import ProductLoadError, load_product, product_record_path
from .promotion import (
    CandidatePromotionService,
    CandidateReview,
    PromotionConflict,
    PromotionValidationError,
    ReviewDecision,
)
from .rules import (
    RulesRepositoryError,
    canonical_rules_repository_bytes,
    load_print_sheet,
    load_rules_repository,
    load_slot,
    print_sheet_record_path,
    slot_record_path,
)
from .sources import SourceLoadError, load_acquisition_manifest, load_source_record

__all__ = [
    "CardRepositoryError",
    "CandidatePromotionService",
    "CandidateReview",
    "ProductLoadError",
    "PromotionConflict",
    "PromotionValidationError",
    "ReviewDecision",
    "RulesRepositoryError",
    "SourceLoadError",
    "canonical_repository_bytes",
    "canonical_rules_repository_bytes",
    "card_record_path",
    "load_acquisition_manifest",
    "load_card",
    "load_card_repository",
    "load_printing",
    "load_print_sheet",
    "load_product",
    "load_source_record",
    "load_rules_repository",
    "load_slot",
    "print_sheet_record_path",
    "printing_record_path",
    "product_record_path",
    "slot_record_path",
]
