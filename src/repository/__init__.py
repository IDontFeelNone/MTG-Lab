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
from .sources import SourceLoadError, load_acquisition_manifest, load_source_record

__all__ = [
    "CardRepositoryError",
    "ProductLoadError",
    "SourceLoadError",
    "canonical_repository_bytes",
    "card_record_path",
    "load_acquisition_manifest",
    "load_card",
    "load_card_repository",
    "load_printing",
    "load_product",
    "load_source_record",
    "printing_record_path",
    "product_record_path",
]
