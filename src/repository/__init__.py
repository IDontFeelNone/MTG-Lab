"""MTG Lab repository package.

Provides the canonical repository layer responsible for managing
normalized datasets, metadata, schemas, and repository access.
"""

from .products import ProductLoadError, load_product, product_record_path

__all__ = ["ProductLoadError", "load_product", "product_record_path"]
