"""Synthetic-only fixed-content Product Intelligence contract tests."""
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

from decision_intelligence import DomainAnalysisEnvelope
from market.intelligence import MarketObservation
from product_intelligence import (ComponentValuationInput, FixedContentProductManifest,
    GuaranteedComponent, ProductAcquisitionOffer, ProductValidationError,
    analyze_fixed_content, to_decision_analysis)
from decision_intelligence import EvidenceReference

NOW=datetime(2026,8,15,tzinfo=timezone.utc)
E=EvidenceReference('synthetic-manifest','synthetic-fixture','sha256:'+'a'*64)
O=EvidenceReference('synthetic-offer','synthetic-fixture','sha256:'+'b'*64)

def component(cid='piece-a',quantity=1,printing='edition-a',finish='standard',language='zz'):
    return GuaranteedComponent(cid,'collectible-piece',quantity,printing,finish,language,evidence_ids=('synthetic-manifest',))

def manifest(components=None, completeness='complete'):
    return FixedContentProductManifest('product-a','synthetic-game','fixed-collection',tuple(components or (component(),component('piece-b',2,'edition-b'))),completeness,(E,),date(2026,9,1),NOW,unknowns=() if completeness=='complete' else ('contents may be incomplete',),limitations=('synthetic only',))

def offer(currency='USD'):
    return ProductAcquisitionOffer('offer-a','product-a','synthetic-shop',NOW,currency,Decimal('20.10'),(O,),shipping=Decimal('1.20'),tax=Decimal('0.70'),transaction_fees=Decimal('.30'),discounts=Decimal('.30'))

def valuation(c,price,**kw):
    provider=kw.get('provider','synthetic-market'); currency=kw.get('currency','USD'); price_type=kw.get('price_type','market'); observed=kw.get('observed_at',NOW)
    obs=MarketObservation('printing',c.printing_id,provider,observed,NOW,price,currency,price_type,c.finish,provenance={'language':c.language,'fixture':'synthetic'})
    return ComponentValuationInput(c.component_id,obs,c.printing_id,c.finish,c.language,c.treatment)

class ProductIntelligenceTests(unittest.TestCase):
    def test_versioned_schema_determinism_immutability_and_provenance(self):
        m=manifest(); a=analyze_fixed_content(m,offer(),tuple(valuation(c,Decimal('4.20') if c.component_id=='piece-a' else Decimal('5.05')) for c in m.components))
        self.assertEqual(m.to_json(),manifest(tuple(reversed(m.components))).to_json())
        self.assertEqual(a.to_json(),analyze_fixed_content(m,offer(),tuple(reversed(tuple(valuation(c,Decimal('4.20') if c.component_id=='piece-a' else Decimal('5.05')) for c in m.components)))).to_json())
        with self.assertRaises(FrozenInstanceError): m.product_id='changed'
        with self.assertRaises(TypeError): a.payload['state']='changed'
        with self.assertRaises(TypeError): a.payload['unsupported_dimensions']['liquidity']='known'
        self.assertIn('synthetic-manifest',[x['evidence_id'] for x in a.to_dict()['evidence']])
        root=Path('src/schemas/v1')
        Draft202012Validator(json.loads((root/'fixed-content-product-manifest-v1.schema.json').read_text())).validate(m.to_dict())
        Draft202012Validator(json.loads((root/'product-acquisition-offer-v1.schema.json').read_text())).validate(offer().to_dict())
        Draft202012Validator(json.loads((root/'component-valuation-input-v1.schema.json').read_text())).validate(valuation(m.components[0],Decimal('1')).to_dict())
        Draft202012Validator(json.loads((root/'fixed-content-product-analysis-v1.schema.json').read_text())).validate(a.to_dict())

    def test_manifest_validation_multiple_copies_and_game_neutral_fixture(self):
        m=manifest(); self.assertEqual(m.components[1].quantity,2); self.assertEqual(m.game_id,'synthetic-game')
        with self.assertRaises(ProductValidationError): manifest((component(),component()))
        for q in (0,-1,True):
            with self.assertRaises(ProductValidationError): component(quantity=q)
        with self.assertRaises(ProductValidationError): component(cid='')
        with self.assertRaises(ProductValidationError): FixedContentProductManifest('', 'game','kind',(component(),),'complete',(E,))

    def test_exact_economics_transaction_delta_contribution_and_concentration(self):
        m=manifest(); vals=(valuation(m.components[0],Decimal('4.20')),valuation(m.components[1],Decimal('5.05')))
        d=analyze_fixed_content(m,offer(),vals,top_n=2).to_dict()
        self.assertEqual(d['known_component_value_subtotal'],'14.30')
        self.assertEqual(d['total_guaranteed_component_acquisition_value'],'14.30')
        self.assertEqual(d['sealed_acquisition_cost'],'22.00'); self.assertEqual(d['transaction_cost_impact'],'1.90')
        self.assertEqual(d['sealed_minus_components'],'7.70'); self.assertEqual(d['components_minus_sealed'],'-7.70')
        self.assertEqual(d['largest_value_driving_component']['component_id'],'piece-b')
        self.assertEqual(Decimal(d['largest_component_percentage']),Decimal('10.10')*100/Decimal('14.30'))
        self.assertEqual(d['top_n_component_value'],'14.30'); self.assertEqual(d['top_n_percentage'],'100')
        self.assertEqual(d['coverage']['valued_quantity'],3)

    def test_unknown_partial_and_explicit_unsupported_states(self):
        m=manifest(); d=analyze_fixed_content(m,offer(),(valuation(m.components[0],None),)).to_dict()
        self.assertEqual(d['state'],'incomplete'); self.assertIsNone(d['total_guaranteed_component_acquisition_value'])
        self.assertEqual(d['known_component_value_subtotal'],'0'); self.assertEqual(d['coverage']['unknown_unpriced_component_count'],2)
        self.assertEqual(d['coverage']['unknown_unpriced_quantity'],3)
        self.assertEqual(d['unsupported_dimensions']['sealed_collectible_premium'],'not_evaluated')
        d=analyze_fixed_content(manifest(completeness='unknown'),offer(),()).to_dict(); self.assertEqual(d['state'],'incomplete')

    def test_fail_closed_comparability_currency_dimensions_and_conflicts(self):
        m=manifest(); first=valuation(m.components[0],Decimal('1'))
        second=valuation(m.components[1],Decimal('2'),provider='other')
        d=analyze_fixed_content(m,offer(),(first,second)).to_dict()
        self.assertIn('incompatible_market_dimensions',d['comparability_issues']); self.assertIsNone(d['sealed_minus_components'])
        d=analyze_fixed_content(m,offer('EUR'),(first,)).to_dict(); self.assertIn('incompatible_currencies',d['comparability_issues'])
        with self.assertRaises(ProductValidationError): analyze_fixed_content(m,offer(),(first,first))
        with self.assertRaises(ProductValidationError): ComponentValuationInput('piece-a',first.observation,'wrong','standard','zz')

    def test_decision_envelope_compatibility_without_recommendation_formula(self):
        m=manifest(); a=analyze_fixed_content(m,offer(),tuple(valuation(c,Decimal('2')) for c in m.components)); envelope=to_decision_analysis(a,'buy-synthetic')
        self.assertIsInstance(envelope,DomainAnalysisEnvelope); self.assertEqual(envelope.domain_id,'fixed-content-product-intelligence')
        self.assertEqual({x.metric_id for x in envelope.metrics},{'product.components_acquisition_value','product.sealed_acquisition_cost','product.sealed_minus_components','product.anchor_concentration_percentage'})
        self.assertNotIn('recommendation',a.to_dict()); self.assertNotIn('objective',a.to_dict())
        schema=json.loads(Path('src/schemas/v1/decision-analysis-v1.schema.json').read_text()); Draft202012Validator(schema).validate(envelope.to_dict())

    def test_protected_production_data_non_mutation_and_no_named_special_case(self):
        before={p:p.read_bytes() for p in Path('data').rglob('*') if p.is_file()}
        m=manifest(); analyze_fixed_content(m,offer(),tuple(valuation(c,Decimal('1')) for c in m.components))
        after={p:p.read_bytes() for p in Path('data').rglob('*') if p.is_file()}; self.assertEqual(before,after)
        source='\n'.join(p.read_text() for p in Path('src/product_intelligence').glob('*.py')).lower()
        for name in ('crack the plates','the hobbit','scene box','secret lair','commander deck'): self.assertNotIn(name,source)

if __name__=='__main__': unittest.main()
