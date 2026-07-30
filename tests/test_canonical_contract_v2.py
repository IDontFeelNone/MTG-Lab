"""Contract and compatibility coverage for canonical reconciliation v2."""
from __future__ import annotations
import json, shutil, tempfile, unittest
from pathlib import Path
from canonical import ProductComponent
from repository.canonical import CanonicalRepository, CanonicalRepositoryError
from validation import SchemaValidationError, validate_document

ROOT = Path(__file__).parents[1] / "data/canonical/games"
PROV = [{"source_id":"fixture", "field_paths":["id"], "claim":"fixture"}]

def write(root: Path, relative: str, value: dict) -> None:
    path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value))

class CanonicalContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)/"games"
        shutil.copytree(ROOT/"magic", self.root/"magic")
    def tearDown(self): self.temp.cleanup()

    def graph(self, *, recursive=False):
        product={"schema_version":"v2","id":"fixture","game":"magic","name":"Fixture","product_type":"box","lifecycle_status":"validated","version_ids":["fixture.box"],"provenance":PROV}
        components=[{"component_type":"product_version" if recursive else "pack_definition","component_id":"fixture.box" if recursive else "fixture.pack","quantity":2}]
        version={"schema_version":"v2","id":"fixture.box","game":"magic","product_id":"fixture","name":"Box","components":components,"provenance":PROV}
        pack={"schema_version":"v2","id":"fixture.pack","game":"magic","product_version_id":"fixture.box","name":"Pack","slot_ids":["fixture.slot"],"provenance":PROV}
        slot={"schema_version":"v2","id":"fixture.slot","game":"magic","name":"Slot","print_sheet_id":"fixture.sheet","draw_count":1,"replacement":False,"provenance":PROV}
        sheet={"schema_version":"v2","id":"fixture.sheet","game":"magic","name":"Sheet","entries":[{"printing_id":"magic.mb2.1.en","weight":2}],"provenance":PROV}
        write(self.root/"magic","products/fixture/product.json",product)
        write(self.root/"magic","product_versions/fixture.box/product-version.json",version)
        write(self.root/"magic","packs/fixture.pack/pack-definition.json",pack)
        write(self.root/"magic","slots/fixture.slot/slot.json",slot)
        write(self.root/"magic","print_sheets/fixture.sheet/print-sheet.json",sheet)

    def test_v2_graph_loads_as_one_immutable_typed_projection(self):
        self.graph(); repo=CanonicalRepository("magic",games_root=self.root)
        self.assertEqual(repo.get_product("fixture").schema_version,"v2")
        self.assertEqual(repo.product_versions[-1].components,(ProductComponent("pack_definition","fixture.pack",2),))
        self.assertFalse(next(x for x in repo.pack_slots if x.id=="fixture.slot").replacement)
        with self.assertRaises(AttributeError): repo.product_versions[-1].components=()

    def test_recursive_composition_cycles_fail_closed(self):
        self.graph(recursive=True)
        with self.assertRaisesRegex(CanonicalRepositoryError,"composition cycle"):
            CanonicalRepository("magic",games_root=self.root)

    def test_v1_product_slots_project_to_synthetic_v2_graph_without_rewrite(self):
        self.graph()
        path=self.root/"magic/products/fixture/product.json"
        legacy={"schema_version":"v1","id":"fixture","game":"magic","name":"Fixture","product_type":"booster","lifecycle_status":"validated","slot_ids":["fixture.slot"],"provenance":[{"claim":"fixture","source_classification":"internal","source_location":"test","verification_status":"confirmed"}]}
        original=json.dumps(legacy); path.write_text(original)
        (self.root/"magic/product_versions/fixture.box/product-version.json").unlink()
        (self.root/"magic/packs/fixture.pack/pack-definition.json").unlink()
        repo=CanonicalRepository("magic",games_root=self.root)
        self.assertEqual(repo.get_product("fixture").version_ids,("fixture.legacy-version",))
        self.assertEqual(next(x for x in repo.pack_definitions if x.id=="fixture.legacy-pack").slot_ids,("fixture.slot",))
        self.assertEqual(path.read_text(),original)

    def test_declared_schema_version_dispatch_and_invalid_component(self):
        self.graph(); document=json.loads((self.root/"magic/product_versions/fixture.box/product-version.json").read_text())
        validate_document(document,"product-version")
        document["components"][0]["quantity"]=0
        with self.assertRaises(SchemaValidationError): validate_document(document,"product-version")
