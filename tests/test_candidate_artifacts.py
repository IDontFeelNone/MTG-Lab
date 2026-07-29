import tempfile,unittest
from pathlib import Path
from ingestion.candidates import *
from ingestion.intermediate_storage import IntermediateArtifactStorage
from ingestion.normalizers import CandidateNormalizer
from ingestion.normalization import CandidateNormalizationService
from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.errors import ConflictingStoredContent,InvalidEvidencePath
from validation import SchemaValidationError,validate_document

H="a"*64
def parsed():
 return ParsedArtifact("parsed","product","source","target",H,"fixture.parser","1","2026-07-29T00:00:00Z","text/plain",ArtifactStatus.SUCCEEDED,(ParsedRecord("record","catalog",{"name":"Example Item","external_id":"example-001"}),))
def candidate():
 p=FieldProvenance("name","raw","source","target",H,"parsed","record","fixture.normalizer","1","official",1)
 return NormalizedCandidate("candidate","catalog_item",{"name":"Example Item"},("record",),(p,),1)
def artifact():
 return NormalizedCandidateArtifact("candidate-artifact","product","source","target",H,"parsed","fixture.normalizer","1","2026-07-29T00:00:00Z","catalog_item",ArtifactStatus.SUCCEEDED,(candidate(),))
class FixtureNormalizer(CandidateNormalizer):
 normalizer_id="fixture.normalizer";normalizer_version="1";supported_record_types=("catalog",);output_candidate_type="catalog_item"
 def normalize(self,p):return CandidateNormalizationResult(artifact(),ArtifactStatus.SUCCEEDED)
class PartialNormalizer(FixtureNormalizer):
 def normalize(self,p):return CandidateNormalizationResult(artifact(),ArtifactStatus.PARTIAL,warnings=("incomplete fixture",))
class FailingNormalizer(FixtureNormalizer):
 def normalize(self,p):raise RuntimeError("fixture failure")
class CandidateTests(unittest.TestCase):
 def test_schemas_reject_invalid_states_confidence_and_metadata(self):
  validate_document(parsed().to_dict(),"parsed-record-artifact")
  bad=parsed().to_dict();bad["parse_status"]="bad"
  with self.assertRaises(SchemaValidationError):validate_document(bad,"parsed-record-artifact")
  validate_document(artifact().to_dict(),"normalized-candidate-artifact")
  bad=artifact().to_dict();bad["candidates"][0]["confidence"]=2
  with self.assertRaises(SchemaValidationError):validate_document(bad,"normalized-candidate-artifact")
 def test_validation_rejects_duplicate_and_missing_references(self):
  d=artifact().to_dict();d["candidates"].append(d["candidates"][0]|{"id":"candidate-two","parsed_record_ids":["missing"]})
  self.assertEqual(validate_candidate_artifact(d,parsed().to_dict()).state,CandidateValidationState.INVALID)
 def test_storage_is_idempotent_loadable_and_conflict_safe(self):
  with tempfile.TemporaryDirectory() as x:
   s=IntermediateArtifactStorage(Path(x));p=s.store_parsed(parsed().to_dict());self.assertEqual(p,s.store_parsed(parsed().to_dict()))
   self.assertEqual(s.load_parsed("product","source","target","parsed")["id"],"parsed")
   bad=parsed().to_dict()|{"warnings":["different"]}
   with self.assertRaises(ConflictingStoredContent):s.store_parsed(bad)
   with self.assertRaises(InvalidEvidencePath):s.load_parsed("../x","source","target","parsed")
 def test_normalization_success_partial_and_failure_preserve_parsed(self):
  with tempfile.TemporaryDirectory() as x:
   s=IntermediateArtifactStorage(Path(x));service=CandidateNormalizationService(s,(FixtureNormalizer(),))
   r=service.normalize(parsed());self.assertEqual(r.status,ArtifactStatus.SUCCEEDED);self.assertEqual(s.load_candidates("product","source","target","candidate-artifact")["id"],"candidate-artifact")
   r=CandidateNormalizationService(s,(PartialNormalizer(),)).normalize(parsed());self.assertEqual(r.status,ArtifactStatus.PARTIAL)
   r=CandidateNormalizationService(s,(FailingNormalizer(),)).normalize(parsed());self.assertEqual(r.status,ArtifactStatus.FAILED);self.assertTrue(s.load_parsed("product","source","target","parsed"))
if __name__=="__main__":unittest.main()
