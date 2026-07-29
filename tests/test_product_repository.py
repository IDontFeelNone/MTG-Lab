"""Tests for generic canonical product loading and lifecycle integrity."""
from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from repository import ProductLoadError, load_product
from validation import SchemaValidationError, validate_document

def product(status: str, slots: list[str]) -> dict:
    return {"schema_version":"v1","id":"example_product","game":"magic","name":"Example","product_type":"sealed_product","lifecycle_status":status,"slot_ids":slots,"provenance":[{"claim":"Example claim","source_classification":"internal","source_location":"test fixture","verification_status":"unverified"}]}

class ProductRepositoryTests(unittest.TestCase):
    def test_foundation_and_draft_allow_empty_slots(self) -> None:
        validate_document(product("foundation", []), "product")
        validate_document(product("draft", []), "product")
    def test_validated_requires_slots(self) -> None:
        with self.assertRaises(SchemaValidationError): validate_document(product("validated", []), "product")
        validate_document(product("validated", ["main_slot"]), "product")
    def test_unknown_status_and_invalid_provenance_fail(self) -> None:
        with self.assertRaises(SchemaValidationError): validate_document(product("unknown", []), "product")
        invalid=product("foundation", []); del invalid["provenance"][0]["verification_status"]
        with self.assertRaises(SchemaValidationError): validate_document(invalid, "product")
    def test_loads_mb2_and_provenance(self) -> None:
        record=load_product("magic","mystery_booster_2")
        self.assertEqual(record["lifecycle_status"],"foundation"); self.assertEqual(record["slot_ids"],[])
        self.assertEqual(record["provenance"][0]["source_classification"],"official")
    def test_missing_invalid_and_path_mismatch_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(ProductLoadError): load_product("magic","missing",games_root=root)
            path=root/"magic"/"products"/"example_product"/"product.json"; path.parent.mkdir(parents=True)
            path.write_text(json.dumps(product("foundation", [])),encoding="utf-8"); self.assertEqual(load_product("magic","example_product",games_root=root)["id"],"example_product")
            path.write_text(json.dumps(product("foundation", [] )|{"id":"other_product"}),encoding="utf-8")
            with self.assertRaises(ProductLoadError): load_product("magic","example_product",games_root=root)
if __name__=="__main__": unittest.main()
