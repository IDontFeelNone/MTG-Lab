import json,tempfile,unittest
from pathlib import Path
from repository import SourceLoadError,load_source_record,load_acquisition_manifest
from validation import SchemaValidationError,validate_document
def source(): return {"schema_version":"v1","id":"source","title":"Source","source_classification":"official","provider":"Provider","source_location":"https://example.com","access_date":"2026-07-29","verification_status":"confirmed","claims":["claim"],"record_version":"1"}
class SourcesTests(unittest.TestCase):
 def test_mb2_loads(self): self.assertEqual(load_acquisition_manifest("magic","mystery_booster_2","mystery_booster_2_product_overview")["acquisition_status"],"acquired")
 def test_invalid_schema(self):
  bad=source();bad["source_classification"]="bad"
  with self.assertRaises(SchemaValidationError):validate_document(bad,"source-record")
 def test_missing_reference(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"magic/products/p/sources/m.manifest.json";p.parent.mkdir(parents=True);m={"schema_version":"v1","id":"m","product_id":"p","source_ids":["missing"],"raw_destination":"x","acquisition_method":"manual","acquisition_status":"planned","processing_status":"unprocessed"};p.write_text(json.dumps(m))
   with self.assertRaises(SourceLoadError):load_acquisition_manifest("magic","p","m",games_root=root)
