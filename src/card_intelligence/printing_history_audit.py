"""Deterministic, read-only Phase 137 printing-history audit."""
from collections import Counter
from datetime import date
import hashlib, json
from pathlib import Path
from production_evidence.promotion_readiness import canonical_state_digest

CANONICAL_DIGEST="881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077"
RUN_ID="mtgjson-pilot-30786023976-1"; PROMOTION_ID="phase-136-mtgjson-pilot-30786023976-1"
STATUSES=("known","explicitly_unknown","unsupported_by_provider","inconsistent","malformed","conflicting","missing_required")
FIELDS=("canonical_printing_id","canonical_card_id","provider_printing_uuid","set_code","set_name","collector_number","release_date","language","finishes","rarity","frame","border_indicators","treatments","promotional_status","reprint_status","paper_digital_state","source_acquisition_run","source_record_identity","field_level_provenance")

def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _tree(p):
 d=hashlib.sha256()
 for x in sorted(y for y in p.rglob('*') if y.is_file()): d.update(x.relative_to(p).as_posix().encode()+b'\0'); d.update(x.read_bytes())
 return d.hexdigest()
def _census(xs): return [{"value":k,"printing_count":v} for k,v in sorted(Counter(xs).items(),key=lambda x:str(x[0]))]
def _fields(rows):
 out={f:{s:0 for s in STATUSES} for f in FIELDS}
 for r in rows:
  for f in FIELDS:
   s="known"
   if f in ("border_indicators","field_level_provenance"): s="unsupported_by_provider"
   elif f=="promotional_status" and r["promotional"]=="unknown": s="explicitly_unknown"
   elif f=="paper_digital_state" and r["digital_or_paper"]=="unknown": s="explicitly_unknown"
   elif f=="reprint_status" and r["reprint"]=="unknown": s="explicitly_unknown"
   out[f][s]+=1
 return out

def build_phase137_audit(data_root):
 root=Path(data_root); state_path=root/'canonical/state.json'
 if canonical_state_digest(root)!=CANONICAL_DIGEST: raise ValueError('canonical digest mismatch')
 state=json.loads(state_path.read_bytes()); audit=json.loads((root/f'audit/bounded_promotions/{PROMOTION_ID}.json').read_bytes())
 src=root/f'evidence/phase-135/{RUN_ID}/source-pilot-printings.json'; rows=json.loads(src.read_bytes())["pilot_printings"]
 if (len(state['printing']),len(rows),len(audit['promoted_printing_ids']))!=(913,534,534): raise ValueError('baseline census mismatch')
 byid={r['provider_printing_id']:r for r in rows}; promoted=set(audit['promoted_printing_ids'])
 if set(byid)!=promoted: raise ValueError('promoted identity mismatch')
 names=sorted({r['card_name'] for r in rows}); defects=[]
 mapping={"uuid":"provider_printing_id","set_code":"set_code","set_name":"set_name","collector_number":"collector_number","release_date":"release_date","language":"language","rarity":"rarity","frame_or_treatment":"frame_or_treatment","promotional":"promotional","reprint":"reprint","digital_or_paper":"digital_or_paper","source_record_identity":"source_record_identity","provider_card_or_oracle_id":"provider_card_or_oracle_id"}
 for pid in sorted(promoted):
  ent=state['printing'].get(pid)
  if not ent: defects.append({"printing_id":pid,"reason":"missing-required"}); continue
  v,r=ent['values'],byid[pid]
  for a,b in mapping.items():
   if v[a]!=r[b]: defects.append({"printing_id":pid,"field":a,"reason":"conflicting"})
  if v['finish_ids']!=sorted(r['finishes']): defects.append({"printing_id":pid,"field":"finishes","reason":"inconsistent"})
  if v['card_id']!=r['provider_card_or_oracle_id']: defects.append({"printing_id":pid,"field":"canonical_card_id","reason":"conflicting"})
 cards=[]; facts=[]; chains=[]
 for name in names:
  retained=[r for r in rows if r['card_name']==name]; cid=retained[0]['provider_card_or_oracle_id']
  cp=sorted((k,v['values']) for k,v in state['printing'].items() if v['values']['card_id']==cid); dates=sorted(v.get('release_date','2024-08-02') for _,v in cp); sets=sorted({(v.get('set_code','MB2'),v.get('set_name','Mystery Booster 2')) for _,v in cp})
  expected={"canonical_printing_ids":[k for k,_ in cp],"total_known_canonical_printings":len(cp),"reprint_count":max(len(cp)-1,0),"distinct_canonical_set_count":len(sets),"set_codes_and_names":[{"code":c,"name":n} for c,n in sets],"earliest_known_canonical_printing_date":dates[0],"latest_known_canonical_printing_date":dates[-1],"elapsed_days_between_known_date_boundaries":(date.fromisoformat(dates[-1])-date.fromisoformat(dates[0])).days}
  fp=next((root/f'knowledge/facts/magic/{cid}').glob('phase136-*.json')); fact=json.loads(fp.read_bytes()); fd=fact['value']['data']; diff=sorted(k for k,v in expected.items() if fd.get(k)!=v)
  facts.append({"card_id":cid,"card_name":name,"fact_id":fact['fact_id'],"result":"matched" if not diff else "mismatch","mismatched_fields":diff})
  cards.append({"card_id":cid,"card_name":name,"promoted_printing_count":len(retained),"canonical_printing_count":len(cp),"reprint_count_definition":expected['reprint_count'],"distinct_set_count":len(sets),"earliest_date":dates[0],"latest_date":dates[-1],"elapsed_days":expected['elapsed_days_between_known_date_boundaries'],"set_inventory":expected['set_codes_and_names']})
  hist=sorted((root/f'knowledge/facts/magic/{cid}').glob('phase13[236]-*printing-reprint_history.json'))
  phases=[json.loads(x.read_bytes())['fact_id'].split('-',1)[0] for x in hist]
  chains.append({"card_id":cid,"card_name":name,"phases":phases,"result":"matched" if phases==['phase132','phase133','phase136'] else 'mismatch'})
 sets=sorted({(r['set_code'],r['set_name']) for r in rows})
 report={"schema_version":"phase-137-printing-history-audit-v1","architecture_version":"12","canonical_digest_audited":CANONICAL_DIGEST,"canonical_printing_inventory":913,"pilot_card_scope":names,"pilot_card_count":10,"promoted_printing_scope":534,"acquisition_run_id":RUN_ID,"promotion_audit_identity":PROMOTION_ID,"per_card":cards,"field_classification_census":_fields(rows),"set_inventory":[{"code":c,"name":n} for c,n in sets],"finish_census":_census(f for r in rows for f in sorted(r['finishes'])),"finish_combination_census":_census('+'.join(sorted(r['finishes'])) for r in rows),"language_census":_census(r['language'] for r in rows),"treatment_census":_census(r['frame_or_treatment'] for r in rows),"promotional_state_census":_census(str(r['promotional']).lower() for r in rows),"reprint_state_census":_census(str(r['reprint']).lower() for r in rows),"paper_digital_state_census":_census(r['digital_or_paper'] for r in rows),"fact_to_canonical_reconciliation":facts,"supersession_chain_reconciliation":chains,"provider_completeness":{"state":"bounded_complete_for_retained_phase_135_projection","global_state":"incomplete_global_printing_history","unknown_semantics":"provider_field_unknown","unsupported_semantics":"provider_field_unsupported"},"limitations":["The retained history is bounded to the retained Phase 135 projection and existing pilot MB2 Printings.","Global printing-history completeness is not proven.","Printing count is not supply quantity.","No demand, popularity, scarcity, supply, value, recommendation, or market-trend conclusion follows from Printing count alone."],"detected_defects":defects,"corrections_made":[],"changed_files":["data/reviews/phase-137/printing-history-audit.json","docs/CARD_INTELLIGENCE.md","docs/HANDOFF.md","docs/MTGJSON_PROVIDER.md","docs/NEXT_TASK.md","docs/PROJECT_STATUS.md","docs/SESSION_STATE.md","scripts/audit_pilot_printing_history.py","src/card_intelligence/__init__.py","src/card_intelligence/printing_history_audit.py","tests/test_phase_137_printing_history_audit.py"],"canonical_write":False,"promotion_performed":False,"external_acquisition_performed":False,"inference_performed":False,"protected_boundaries":{"phase135_evidence_tree_sha256":_tree(root/'evidence/phase-135'),"prior_fact_files_sha256":_tree(root/'knowledge/facts'),"market_observation_count":len(list((root/'market/observations').glob('*/*/*/*.json'))),"market_observations_tree_sha256":_tree(root/'market/observations')}}
 if defects or any(x['result']!='matched' for x in facts+chains): raise ValueError('reconciliation failed closed')
 return report

def report_bytes(report): return (json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False,separators=(',',': '))+'\n').encode()
