import json
from pathlib import Path
import unittest
from card_intelligence import build_phase137_audit, report_bytes, CardKnowledgeQuery, KnowledgeRepository

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; REPORT=DATA/'reviews/phase-137/printing-history-audit.json'
COUNTS={'Brainstorm':47,'Command Tower':110,'Counterspell':83,'Goblin Charbelcher':8,'Goblin King':26,'Sol Ring':135,'Swords to Plowshares':96,'Treasure Cruise':14,'Walking Ballista':10,'Wishclaw Talisman':5}
class Phase137AuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.report=json.loads(REPORT.read_bytes())
 def test_exact_scope_and_read_only_boundaries(self):
  r=self.report; self.assertEqual(r['canonical_digest_audited'],'881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077'); self.assertEqual(r['canonical_printing_inventory'],913); self.assertEqual(r['pilot_card_count'],10); self.assertEqual(r['promoted_printing_scope'],534)
  self.assertEqual({x['card_name']:x['promoted_printing_count'] for x in r['per_card']},COUNTS)
  self.assertFalse(any(r[k] for k in ('canonical_write','promotion_performed','external_acquisition_performed','inference_performed')))
  self.assertEqual(r['protected_boundaries'],{'phase135_evidence_tree_sha256':'9057e7761e134d0983f13f26d7840769ebbbf739816d9b2f1221d8a9f2896504','prior_fact_files_sha256':'dd352a9790d77ddcdb110bef6c5f0a4fc43b707e29d1458089fb1c3ac30bc5e4','market_observation_count':478,'market_observations_tree_sha256':'7ecc2c6064856e4921802813e186d34ccafb0ca6daf6a59b0b6c1dd11ad999f8'})
 def test_known_unknown_unsupported_and_normalized_censuses(self):
  c=self.report['field_classification_census']; self.assertEqual(c['promotional_status']['explicitly_unknown'],487); self.assertEqual(c['paper_digital_state']['explicitly_unknown'],500); self.assertEqual(c['reprint_status']['explicitly_unknown'],11); self.assertEqual(c['border_indicators']['unsupported_by_provider'],534); self.assertEqual(c['field_level_provenance']['unsupported_by_provider'],534)
  self.assertTrue(all(sum(v.values())==534 for v in c.values())); self.assertEqual(len(self.report['set_inventory']),154)
  for key in ('set_inventory','finish_census','language_census','treatment_census','promotional_state_census','reprint_state_census','paper_digital_state_census'): self.assertEqual(self.report[key],sorted(self.report[key],key=lambda x:(x.get('code',x.get('value')),x.get('name',''))))
 def test_fact_reconciliation_dates_sets_and_chains(self):
  self.assertTrue(all(x['result']=='matched' and not x.get('mismatched_fields') for x in self.report['fact_to_canonical_reconciliation'])); self.assertTrue(all(x['phases']==['phase132','phase133','phase136'] for x in self.report['supersession_chain_reconciliation']))
  self.assertTrue(all(x['distinct_set_count']==len(x['set_inventory']) and x['earliest_date']<=x['latest_date'] for x in self.report['per_card']))
 def test_bounded_safe_wording_and_query_compatibility(self):
  p=self.report['provider_completeness']; self.assertEqual(p['state'],'bounded_complete_for_retained_phase_135_projection'); self.assertEqual(p['global_state'],'incomplete_global_printing_history'); text=' '.join(self.report['limitations']); self.assertIn('not supply quantity',text); self.assertIn('not proven',text); self.assertIn('No demand',text)
  q=CardKnowledgeQuery(KnowledgeRepository(DATA/'knowledge'))
  for row in self.report['per_card']: self.assertEqual([x['fact_id'].split('-',1)[0] for x in q.printing_history('magic',row['card_id'],include_superseded=True)['facts']],['phase132','phase133','phase136'])
 def test_deterministic_report_bytes(self): self.assertEqual(REPORT.read_bytes(),report_bytes(build_phase137_audit(DATA)))
if __name__=='__main__': unittest.main()
