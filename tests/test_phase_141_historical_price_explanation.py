import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone
from jsonschema import Draft202012Validator, FormatChecker
from card_intelligence import CardValueExplanationEngine, explanation_bytes, render_historical_explanation
from market.intelligence import MarketObservation
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
def obs(price, stamp, **kw):
 return MarketObservation(entity_type='printing',entity_id='p',provider=kw.get('provider','scryfall'),observed_at=datetime.fromisoformat(stamp),recorded_at=datetime(2026,1,3,tzinfo=timezone.utc),price=price,currency=kw.get('currency','USD'),price_type=kw.get('price_type','market'),finish=kw.get('finish','nonfoil'),provenance={'language':kw.get('language','en'),'acquisition_run_id':kw.get('run','r1'),'source_provider_identifier':'pid','source_sha256':'a'*64,'normalized_sha256':'b'*64})
def test_production_baseline_pilot_census():
 e=CardValueExplanationEngine(DATA); assert len(e.observations)==956
 reports=[e.explain(card_id=i,include_historical_movement=True)['evidence_sections']['historical_price_evidence'] for i in e.pilot_ids]
 assert sum(x['comparable_dimension_count'] for x in reports)==17
 assert all((x['history_readiness_state'],x['acquisition_count'],x['distinct_source_timestamp_count'],x['noncomparable_dimension_count'],x['explicit_missing_price_dimension_count'])==('multiple_snapshots_descriptive_only',2,2,0,0) for x in reports)
def test_isolation_decimal_classification_missing():
 e=CardValueExplanationEngine(DATA); p=[{'values':{'uuid':'p','set_id':'mb2','collector_number':'1'}}]
 v=[obs('1','2026-01-01T00:00:00+00:00'),obs('1.5','2026-01-02T00:00:00+00:00',run='r2'),obs('3','2026-01-01T00:00:00+00:00',finish='foil'),obs('2','2026-01-02T00:00:00+00:00',finish='foil',run='r2'),obs('4','2026-01-01T00:00:00+00:00',language='fr'),obs('4','2026-01-02T00:00:00+00:00',language='fr',run='r2'),obs(None,'2026-01-01T00:00:00+00:00',currency='EUR'),obs('9','2026-01-02T00:00:00+00:00',currency='EUR',run='r2'),obs('8','2026-01-02T00:00:00+00:00',price_type='retail',run='r2')]
 r=e._historical_price_evidence('c',p,v); assert sorted(x['classification'] for x in r['descriptive_movement_entries'])==['decreased','increased','unchanged']; inc=next(x for x in r['descriptive_movement_entries'] if x['classification']=='increased'); assert (inc['absolute_change'],inc['percentage_change'])==('0.5','50.000000'); assert (r['noncomparable_dimension_count'],r['explicit_missing_price_dimension_count'])==(2,1)
def test_schema_determinism_renderer_cli_and_backcompat():
 e=CardValueExplanationEngine(DATA); r=e.explain(name='Sol Ring',include_historical_movement=True); schema=json.loads((ROOT/'src/schemas/v1/card-value-explanation-v2.schema.json').read_text()); assert not list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(r)); assert explanation_bytes(r)==explanation_bytes(e.explain(name='Sol Ring',include_historical_movement=True)); text=render_historical_explanation(r).lower(); assert all(x in text for x in ['retained descriptive history','not a prediction','completed-sales evidence','recommendation','fair value']); assert 'historical_price_evidence' not in e.explain(name='Sol Ring',include_observed_prices=True)['evidence_sections']; assert e.explain(name='Sol Ring')['schema_version'].endswith('v1')
 env={**os.environ,'PYTHONPATH':'src:.'}; cmd=['python','-m','card_intelligence.cli','explain','Sol Ring','--include-historical-movement']; out=subprocess.run(cmd,cwd=ROOT,env=env,check=True,capture_output=True,text=True).stdout; cid=json.loads(out)['card_identity']['card_id']; out2=subprocess.run(['python','-m','card_intelligence.cli','explain','--card-id',cid,'--include-historical-movement'],cwd=ROOT,env=env,check=True,capture_output=True,text=True).stdout; assert out==out2
def test_provenance_and_prohibited_fields():
 e=CardValueExplanationEngine(DATA); r=e.explain(name='Brainstorm',include_historical_movement=True); x=r['evidence_sections']['historical_price_evidence']['descriptive_movement_entries'][0]; assert len(x['acquisition_run_ids'])==len(x['source_digests'])==len(x['normalized_digests'])==2; text=explanation_bytes(r).decode().lower(); assert not any(('"'+k+'":') in text for k in ['value_score','ranking','prediction','recommendation','momentum','bullish','bearish','demand','popularity','scarcity'])
