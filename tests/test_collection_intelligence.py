import json
import hashlib
import copy
import itertools
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

from query.engine import CanonicalQueryEngine

from collection.intelligence import (CanonicalCollectionResolver, CollectionIntelligenceError,
    acquisition_priorities, collection_summary, compare_deck, create_snapshot, read_import,
    verify_snapshot)


ROOT = Path(__file__).parents[1]


# Finite test-only successor. No runtime or historical package pins are changed.
ALLOCATION_SOURCE_SHA256 = '275e3fec83618fc71569e505f35df03a0ba389cdff43936d6951b9bf816717b6'
ALLOCATION_OLD_SHA256 = 'ca09a2e622c45fe3ff4a8ad884ed2543ac7846b6f43fd88fe6424f69f5d9f13b'
ALLOCATION_OLD_FUNCTION = b'def compare_deck(snapshot: Mapping[str, Any], deck: Mapping[str, Any], resolver: CanonicalCollectionResolver) -> dict:\n    if deck.get("schema_version") != DECK_VERSION: raise CollectionIntelligenceError("unsupported deck requirement schema")\n    by_printing, by_card = Counter(), Counter()\n    for item in snapshot["resolved_holdings"]:\n        q=item["row"]["quantity"]; pid=item["printing_id"]; by_printing[pid]+=q; by_card[resolver.printings[pid]["card_id"]]+=q\n    remaining_printing, remaining_card = by_printing.copy(), by_card.copy()\n    results=[]; required_total=owned_total=0\n    for req in sorted(deck["requirements"], key=lambda x:(x.get("section","main"),x["card_id"],x.get("printing_id", ""))):\n        required=int(req["quantity"]); policy=req.get("acceptable_printing_policy", deck.get("acceptable_printing_policy","any"))\n        available=remaining_card[req["card_id"]] if policy=="any" else remaining_printing[req.get("printing_id")]\n        used=min(available,required); missing=required-used; required_total+=required; owned_total+=used\n        if policy=="any": remaining_card[req["card_id"]]-=used\n        else: remaining_printing[req.get("printing_id")]-=used\n        total_owned=by_card[req["card_id"]] if policy=="any" else by_printing[req.get("printing_id")]\n        results.append({**req,"section":req.get("section","main"),"owned_quantity":used,"required_quantity":required,\n                        "missing_quantity":missing,"excess_copies":max(0,total_owned-required),\n                        "reusable_owned_copies":max(0,available-used),\n                        "status":"complete" if not missing else "partial" if used else "missing"})\n    return {"schema_version":"deck-comparison-v1","deck_id":deck["deck_id"],"snapshot_id":snapshot["snapshot_id"],\n            "completion_percentage": "100.00" if not required_total else format(Decimal(owned_total*100)/required_total,".2f"),\n            "requirements":results,"complete_cards":sum(x["status"]=="complete" for x in results),\n            "partially_complete_cards":sum(x["status"]=="partial" for x in results),\n            "missing_cards":sum(x["status"]=="missing" for x in results),\n            "unresolved_may_affect_result": [x for x in snapshot["unresolved_holdings"] if x["status"] in {"ambiguous","unresolved"}]}\n'


def allocation_preceding_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    if name != 'src/collection/intelligence.py': return raw
    digest=hashlib.sha256(raw).hexdigest()
    if digest==ALLOCATION_OLD_SHA256:return raw
    if digest!=ALLOCATION_SOURCE_SHA256:raise AssertionError('unreviewed allocation implementation')
    start=raw.index(b'def compare_deck(');end=raw.index(b'\n\ndef acquisition_priorities',start)
    old=raw[:start]+ALLOCATION_OLD_FUNCTION+raw[end:]
    if hashlib.sha256(old).hexdigest()!=ALLOCATION_OLD_SHA256:
        raise AssertionError('historical collection source not reproduced')
    return old


class MixedPrintingAllocationTests(unittest.TestCase):
    def test_one_physical_copy_cannot_satisfy_any_and_exact(self):
        resolver=SimpleNamespace(printings={'fixture-printing-a':{'card_id':'fixture-card'}})
        snapshot={'snapshot_id':'fictional-allocation','resolved_holdings':[
            {'printing_id':'fixture-printing-a','row':{'quantity':1}}],'unresolved_holdings':[]}
        deck={'schema_version':'deck-requirement-v1','deck_id':'fictional-mixed','requirements':[
            {'card_id':'fixture-card','quantity':1,'acceptable_printing_policy':'any'},
            {'card_id':'fixture-card','printing_id':'fixture-printing-a','quantity':1,'acceptable_printing_policy':'exact'}]}
        report=compare_deck(snapshot,deck,resolver)
        self.assertEqual(sum(r['owned_quantity'] for r in report['requirements']),1)
        self.assertEqual(sum(r['missing_quantity'] for r in report['requirements']),1)
        self.assertEqual(report['completion_percentage'],'50.00')


    def case(self, counts, requirements, unresolved=None):
        resolver=SimpleNamespace(printings={p:{'card_id':'fixture-card'} for p in ('a','b')})
        snapshot={'snapshot_id':'fictional','resolved_holdings':[{'printing_id':p,'row':{'quantity':q}} for p,q in counts.items() if q], 'unresolved_holdings':unresolved or []}
        deck={'schema_version':'deck-requirement-v1','deck_id':'fictional','requirements':requirements}
        before=copy.deepcopy((snapshot,deck));result=compare_deck(snapshot,deck,resolver)
        self.assertEqual((snapshot,deck),before)
        rows=result['requirements'];self.assertLessEqual(sum(x['owned_quantity'] for x in rows),sum(counts.values()))
        for p in counts:self.assertLessEqual(sum(x['owned_quantity'] for x in rows if x.get('acceptable_printing_policy')=='exact' and x.get('printing_id')==p),counts[p])
        # Match each reported allocation to distinct physical tokens. This checks
        # Printing conservation for flexible rows without adding report fields.
        tokens=tuple(p for p in sorted(counts) for _ in range(counts[p]))
        def feasible(index,left):
            if index==len(rows):return True
            row=rows[index];eligible=[i for i in left if row.get('acceptable_printing_policy','any')=='any' or tokens[i]==row.get('printing_id')]
            return any(feasible(index+1,tuple(i for i in left if i not in selected)) for selected in itertools.combinations(eligible,row['owned_quantity']))
        self.assertTrue(feasible(0,tuple(range(len(tokens)))))
        for row in rows:
            self.assertGreaterEqual(row['owned_quantity'],0);self.assertEqual(row['owned_quantity']+row['missing_quantity'],row['required_quantity'])
        return result

    def row(self, policy='any',quantity=1,printing=None,section='main'):
        value=dict(card_id='fixture-card',quantity=quantity,acceptable_printing_policy=policy,section=section)
        if printing is not None:value['printing_id']=printing
        return value

    def test_exact_priority_preserves_scarce_match_in_either_input_order(self):
        rows=[self.row(),self.row('exact',printing='a',section='sideboard')]
        first=self.case({'a':1,'b':1},rows)
        self.assertEqual(first,self.case({'b':1,'a':1},list(reversed(rows))))
        self.assertEqual(first['completion_percentage'],'100.00')
        self.assertEqual([x['owned_quantity'] for x in first['requirements']],[1,1])

    def test_repeated_exact_and_flexible_quantities_across_sections(self):
        for policy in ('any','exact'):
            rows=[self.row(policy,2,'a' if policy=='exact' else None),self.row(policy,2,'a' if policy=='exact' else None,'sideboard')]
            r=self.case({'a':3,'b':0},rows)
            self.assertEqual([x['owned_quantity'] for x in r['requirements']],[2,1]);self.assertEqual(r['completion_percentage'],'75.00')
            self.assertEqual([x['status'] for x in r['requirements']],['complete','partial'])
            self.assertTrue(all(x['excess_copies']==x['reusable_owned_copies']==0 for x in r['requirements']))

    def test_surplus_is_final_unallocated_eligible_inventory_not_prior_allocations(self):
        rows=[self.row(),self.row('exact',printing='a')]
        r=self.case({'b':3,'a':1},rows)
        any_row=next(x for x in r['requirements'] if x['acceptable_printing_policy']=='any')
        exact=next(x for x in r['requirements'] if x['acceptable_printing_policy']=='exact')
        self.assertEqual((any_row['excess_copies'],any_row['reusable_owned_copies']),(2,2));self.assertEqual(exact['excess_copies'],0)

    def test_small_inventory_conservation_sufficiency_and_order_permutations(self):
        for a,b in itertools.product(range(3),repeat=2):
            for exact in (1,2):
                rows=[self.row('exact',exact,'a'),self.row('any',2),self.row('any',1,section='sideboard')]
                r=self.case({'a':a,'b':b},rows)
                expected=min(a,exact)+min(max(0,a-exact)+b,3)
                self.assertEqual(sum(x['owned_quantity'] for x in r['requirements']),expected)
                for shuffled in itertools.permutations(rows):self.assertEqual(r,self.case({'b':b,'a':a},list(shuffled)))
        self.assertEqual(self.case({'a':2,'b':3},rows)['completion_percentage'],'100.00')

    def test_unresolved_and_ambiguous_rows_never_supply_copies(self):
        unknown=[dict(status=s,row={'quantity':100}) for s in ('unresolved','ambiguous','duplicate_input_row','invalid')]
        r=self.case({'a':0,'b':0},[self.row(),self.row('exact',printing='a')],unknown)
        self.assertEqual(r['completion_percentage'],'0.00');self.assertEqual([x['status'] for x in r['unresolved_may_affect_result']],['unresolved','ambiguous'])

    def test_duplicate_requirements_and_canonical_tie_breaker(self):
        rows=[self.row(quantity=2),self.row(quantity=1),self.row(quantity=1)]
        r=self.case({'a':2,'b':0},rows)
        self.assertEqual(r,self.case({'a':2,'b':0},list(reversed(rows))))
        self.assertEqual(r['completion_percentage'],'50.00')

    def test_acquisition_priority_uses_corrected_missing_quantity(self):
        r=self.case({'a':1,'b':0},[self.row(),self.row('exact',printing='a')])
        priority=acquisition_priorities([r])['priorities'][0]
        self.assertEqual(priority['components']['missing_copy_points'],1)
        self.assertEqual(priority['components']['completion_unlock_points'],'50.00')

    def test_foreign_card_exact_printing_does_not_borrow_inventory(self):
        resolver=SimpleNamespace(printings={'a':{'card_id':'other-card'}})
        snapshot={'snapshot_id':'fictional','resolved_holdings':[{'printing_id':'a','row':{'quantity':2}}],'unresolved_holdings':[]}
        deck={'schema_version':'deck-requirement-v1','deck_id':'fictional','requirements':[self.row('exact',printing='a')]}
        self.assertEqual(compare_deck(snapshot,deck,resolver)['completion_percentage'],'0.00')

    def test_invalid_quantities_and_policies_cannot_allocate_negative_copies(self):
        for quantity in (-1,0,True,1.5,'2'):
            with self.assertRaises(CollectionIntelligenceError):self.case({'a':1},[self.row(quantity=quantity)])
        with self.assertRaises(CollectionIntelligenceError):self.case({'a':1},[self.row('foreign')])
        for quantity in (-1,True,1.5):
            with self.assertRaises(CollectionIntelligenceError):self.case({'a':quantity},[self.row()])

    def test_flexible_allocation_uses_ascending_printing_ids(self):
        rows=[self.row(),self.row('exact',printing='a')]
        r=self.case({'b':1,'a':2},rows)
        exact=next(x for x in r['requirements'] if x['acceptable_printing_policy']=='exact')
        self.assertEqual(exact['excess_copies'],0)  # flexible consumed the second a, leaving b
        self.assertEqual(r,self.case({'a':2,'b':1},list(reversed(rows))))

    def test_single_uniform_requirement_retains_correct_surplus(self):
        for policy in ('any','exact'):
            row=self.case({'a':3},[self.row(policy,2,'a' if policy=='exact' else None)])['requirements'][0]
            self.assertEqual((row['owned_quantity'],row['missing_quantity'],row['excess_copies'],row['reusable_owned_copies']),(2,0,1,1))

    def test_multiple_cards_do_not_share_physical_inventory(self):
        resolver=SimpleNamespace(printings={'a':{'card_id':'fixture-card'},'b':{'card_id':'other-card'}})
        snapshot={'snapshot_id':'fictional','resolved_holdings':[{'printing_id':p,'row':{'quantity':1}} for p in ('b','a')],'unresolved_holdings':[]}
        rows=[self.row(quantity=2),dict(card_id='other-card',quantity=2)]
        report=compare_deck(snapshot,dict(schema_version='deck-requirement-v1',deck_id='fictional',requirements=rows),resolver)
        self.assertEqual([r['owned_quantity'] for r in report['requirements']],[1,1])
        self.assertEqual(report['completion_percentage'],'50.00')

    def test_preservation_adapter_accepts_only_exact_successor_and_original(self):
        name='src/collection/intelligence.py';raw=(ROOT/name).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),ALLOCATION_SOURCE_SHA256)
        old=allocation_preceding_bytes(name,raw)
        self.assertEqual(hashlib.sha256(old).hexdigest(),ALLOCATION_OLD_SHA256)
        self.assertEqual(allocation_preceding_bytes(name,old),old)
        for changed in (raw+b'future',b'X'+raw[1:],raw.replace(b'used=min(',b'used=max(',1),bytearray(raw)):
            with self.assertRaises(AssertionError):allocation_preceding_bytes(name,changed)


class CollectionIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.resolver = CanonicalCollectionResolver("magic", ROOT / "data")
        self.pid = "magic.lea.161.en"; self.card = self.resolver.printings[self.pid]["card_id"]

    def tearDown(self): self.temp.cleanup()

    def write_json(self, entries):
        path=self.root/"import.json"; path.write_text(json.dumps({"schema_version":"collection-import-v1",
            "collection_id":"mine","source":{"type":"fixture","name":"synthetic"},"entries":entries}))
        return path

    def test_json_csv_resolution_unknowns_duplicates_and_invalid(self):
        self.resolver.by_name["synthetic ambiguous"]=[self.pid,"magic.lea.232.en"]
        path=self.write_json([
            {"printing_id":self.pid,"quantity":2,"finish":"nonfoil","language":"en","condition":"near_mint"},
            {"printing_id":self.pid,"quantity":2,"finish":"nonfoil","language":"en","condition":"near_mint"},
            {"printing_id":"missing","quantity":1}, {"card_name":"Synthetic Ambiguous","quantity":1},
            {"printing_id":self.pid,"quantity":0}])
        imported=read_import(path); resolved=self.resolver.resolve(imported)
        self.assertEqual([x["status"] for x in resolved["results"]],
                         ["resolved","duplicate_input_row","unresolved","ambiguous","invalid"])
        self.assertIn("acquisition_price", resolved["results"][0]["row"]["unknown_fields"])
        csv_path=self.root/"import.csv"; csv_path.write_text("printing_id,quantity,finish,language\n%s,1,foil,fr\n"%self.pid)
        csv_result=self.resolver.resolve(read_import(csv_path))["results"][0]
        self.assertEqual((csv_result["status"],csv_result["row"]["finish"],csv_result["row"]["language"]),("resolved","foil","fr"))

    def test_exact_external_identifier_and_name_fallback(self):
        self.resolver.by_name["synthetic ambiguous"]=[self.pid,"magic.lea.232.en"]
        imported={"entries":[{"external_identifiers":{"set_collector_number":"LEA:161"},"quantity":1},
                             {"card_name":"Synthetic Ambiguous","quantity":1}]}
        results=self.resolver.resolve(imported)["results"]
        self.assertEqual(results[0]["printing_id"],self.pid)
        self.assertEqual(results[1]["status"],"ambiguous")

    def snapshot(self):
        imported=read_import(self.write_json([{"printing_id":self.pid,"quantity":3,"finish":"nonfoil",
            "language":"en","condition":"good","acquisition_price":"1.25"},
            {"printing_id":"unknown","quantity":1,"card_name":"Maybe"}]))
        return create_snapshot(imported,self.resolver.resolve(imported),self.root/"snapshots","stable")

    def test_snapshot_replay_conflict_verify_summary_and_no_canonical_write(self):
        before=(ROOT/"data/canonical/state.json").read_bytes(); snapshot=self.snapshot()
        disk=(self.root/"snapshots/stable.json").read_bytes()
        imported=read_import(self.write_json([{"printing_id":self.pid,"quantity":3,"finish":"nonfoil",
            "language":"en","condition":"good","acquisition_price":"1.25"},
            {"printing_id":"unknown","quantity":1,"card_name":"Maybe"}]))
        # Raw import digest changes with serialization, so replay the stored contract inputs directly.
        imported["source_import_digest"]=snapshot["source_import_digest"]
        replay=create_snapshot(imported,self.resolver.resolve(imported),self.root/"snapshots","stable")
        self.assertEqual(replay["replay"],"exact_replay"); self.assertEqual(disk,(self.root/"snapshots/stable.json").read_bytes())
        self.assertTrue(verify_snapshot(self.root/"snapshots/stable.json")["valid"])
        summary=collection_summary(snapshot,self.resolver)
        self.assertEqual((summary["total_owned_quantity"],summary["duplicate_count"],summary["acquisition_cost"]["known_total"]),(3,2,"3.75"))
        self.assertEqual(summary["acquisition_cost"]["missing_quantity"],0)
        with self.assertRaises(CollectionIntelligenceError):
            changed=dict(imported); changed["source_import_digest"]="different"
            create_snapshot(changed,self.resolver.resolve(changed),self.root/"snapshots","stable")
        self.assertEqual(before,(ROOT/"data/canonical/state.json").read_bytes())

    def test_deck_completion_policies_sideboard_excess_and_priorities(self):
        snapshot=self.snapshot()
        deck={"schema_version":"deck-requirement-v1","deck_id":"synthetic-one","format":"fixture",
              "version":"1","snapshot_date":"2026-08-01","acceptable_printing_policy":"any",
              "substitution_policy":"none","source":{"type":"repository_fixture"},
              "requirements":[{"card_id":self.card,"quantity":2,"section":"main"},
                              {"card_id":self.card,"quantity":2,"section":"sideboard"},
                              {"card_id":"magic.missing","quantity":1,"section":"main"}]}
        result=compare_deck(snapshot,deck,self.resolver)
        by_section={x["section"]:x for x in result["requirements"] if x["card_id"]==self.card}
        self.assertEqual(sum(x["owned_quantity"] for x in by_section.values()),3)
        self.assertEqual(result["partially_complete_cards"],1); self.assertTrue(result["unresolved_may_affect_result"])
        exact=dict(deck); exact["deck_id"]="synthetic-exact"; exact["requirements"]=[{
            "card_id":self.card,"printing_id":"magic.mb2.1.en","quantity":1,"section":"main",
            "acceptable_printing_policy":"exact"}]
        self.assertEqual(compare_deck(snapshot,exact,self.resolver)["requirements"][0]["missing_quantity"],1)
        report=acquisition_priorities([result,compare_deck(snapshot,{**deck,"deck_id":"synthetic-two"},self.resolver)])
        self.assertTrue(report["price_independent"]); self.assertEqual(report["priorities"][0]["components"]["shared_deck_points"],20)
        self.assertEqual(report,acquisition_priorities([result,compare_deck(snapshot,{**deck,"deck_id":"synthetic-two"},self.resolver)]))


    def test_public_deck_cli_reports_mixed_missing_copy_and_priorities(self):
        from mtglab.__main__ import main
        imported=read_import(self.write_json([{'printing_id':self.pid,'quantity':1}]))
        snapshot=create_snapshot(imported,self.resolver.resolve(imported),self.root/'collections/snapshots','cli-mixed')
        deck={'schema_version':'deck-requirement-v1','deck_id':'fictional-cli-mixed','requirements':[
            {'card_id':self.card,'quantity':1,'acceptable_printing_policy':'any'},
            {'card_id':self.card,'printing_id':self.pid,'quantity':1,'acceptable_printing_policy':'exact'}]}
        path=self.root/'deck.json';path.write_text(json.dumps(deck))
        for command in ('compare','missing','acquisition-priorities'):
            output=io.StringIO()
            # Reuse the real admitted resolver; only its CLI construction is
            # injected so all retained snapshot/deck IO stays in the temp root.
            with patch('mtglab.__main__.CanonicalCollectionResolver',return_value=self.resolver),redirect_stdout(output):
                self.assertEqual(main(['--data-root',str(self.root),'deck',command,'--snapshot',snapshot['snapshot_id'],'--deck',str(path)]),0)
            value=json.loads(output.getvalue())
            if command=='compare':self.assertEqual(value['completion_percentage'],'50.00')
            elif command=='missing':self.assertEqual(sum(x['missing_quantity'] for x in value['requirements']),1)
            else:self.assertEqual(value['priorities'][0]['components']['missing_copy_points'],1)



class ProductionCollectionResolutionTests(unittest.TestCase):
    PRINTINGS = {
        "5c8d3bc4-32fc-5b26-84bf-9921e5884d43": ("02090581-61aa-4348-ad57-451be8ee91c2", "Ponder", "34"),
        "72783a15-4847-5448-8f1d-0c40379594d3": ("3d6fa57a-aa53-4b5c-b8af-a7612c823117", "Faithless Looting", "57"),
        "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade": ("dc0593c2-ccb4-4648-a592-c5bcd121dc72", "Greater Good", "207"),
    }

    @classmethod
    def setUpClass(cls):
        from historical_catalog import historical_data
        cls.data = historical_data()
        cls.resolver = CanonicalCollectionResolver("magic", cls.data)

    def test_exact_promoted_printings_preserve_card_dimensions_and_provenance(self):
        protected = (self.data / "canonical/state.json").read_bytes()
        result = self.resolver.resolve({"entries": [{"printing_id": pid, "quantity": 1,
            "language": "English", "finish": "nonfoil"} for pid in self.PRINTINGS]})
        self.assertEqual((len(self.resolver.cards), len(self.resolver.printings)), (399, 928))
        self.assertEqual(len(self.resolver.production_printing_ids), 913)
        for resolved in result["results"]:
            pid = resolved["printing_id"]
            card_id, name, collector_number = self.PRINTINGS[pid]
            self.assertEqual((resolved["status"], resolved["card_id"]), ("resolved", card_id))
            self.assertEqual(self.resolver.cards[card_id]["name"], name)
            printing = self.resolver.printings[pid]
            self.assertEqual((printing["set_id"], printing["collector_number"], printing["language"]),
                             ("mb2", collector_number, "English"))
            self.assertIn("nonfoil", printing["finish_ids"])
            self.assertNotIn("treatment_ids", printing)
            reference = resolved["canonical_reference"]
            self.assertEqual(reference["snapshot_id"], result["canonical_snapshot_id"])
            self.assertEqual(reference["printing"]["canonical_identity"], pid)
            self.assertEqual(reference["card"]["canonical_identity"], card_id)
            for entity in (reference["printing"], reference["card"]):
                self.assertTrue(entity["source_ids"])
                self.assertTrue(entity["evidence_reference_ids"])
                self.assertTrue(entity["promotion_references"][0]["audit_reference"]["sha256"])
                self.assertNotIn("review_artifact_digests", entity["promotion_references"][0])
        self.assertEqual(protected, (self.data / "canonical/state.json").read_bytes())

    def test_external_identity_resolves_production_without_seed_name_fallback(self):
        pid = next(iter(self.PRINTINGS))
        scryfall_id = self.resolver.printings[pid]["identifiers"]["scryfallId"]
        results = self.resolver.resolve({"entries": [
            {"external_identifiers": {"scryfallId": scryfall_id}, "quantity": 1},
            {"external_identifiers": {"set_collector_number": "MB2:34"}, "quantity": 1},
            {"card_name": "Sol Ring", "quantity": 1},
        ]})["results"]
        self.assertEqual([result["printing_id"] for result in results[:2]], [pid, pid])
        self.assertEqual(results[2]["status"], "ambiguous")
        self.assertTrue(set(results[2]["candidate_printing_ids"]) & self.resolver.production_printing_ids)
        self.assertTrue(set(results[2]["candidate_printing_ids"]) - self.resolver.production_printing_ids)
        self.assertGreater(len(results[2]["candidate_printing_ids"]), 1)

    def test_known_dimension_and_identifier_conflicts_are_unresolved(self):
        pid = next(iter(self.PRINTINGS))
        other_pid = list(self.PRINTINGS)[1]
        other_scryfall_id = self.resolver.printings[other_pid]["identifiers"]["scryfallId"]
        for field, bad_value in (("card_id", self.PRINTINGS[other_pid][0]),
                                 ("card_name", "Faithless Looting"), ("set_code", "LEA"),
                                 ("collector_number", "57"), ("language", "fr"),
                                 ("finish", "foil"), ("treatment", "borderless"),
                                 ("external_identifiers", {"scryfallId": other_scryfall_id}),
                                 ("external_identifiers", {"unsupported_identity": "unknown-id"})):
            with self.subTest(field=field, bad_value=bad_value):
                result = self.resolver.resolve({"entries": [
                    {"printing_id": pid, "quantity": 1, field: bad_value}]})["results"][0]
                self.assertEqual(result["status"], "unresolved")
                self.assertTrue(result["dimension_conflicts"])
                self.assertEqual(result["candidate_printing_ids"], [pid])
                self.assertNotIn("printing_id", result)
                if field in {"card_id", "set_code", "collector_number", "treatment"}:
                    self.assertEqual(result["row"]["identity_constraints"][field], bad_value)

    def test_unknown_physical_attributes_remain_unknown(self):
        pid = next(iter(self.PRINTINGS))
        result = self.resolver.resolve({"entries": [{"printing_id": pid, "quantity": 1}]})["results"][0]
        self.assertEqual(result["status"], "resolved")
        self.assertIsNone(result["row"]["finish"])
        self.assertIsNone(result["row"]["language"])
        self.assertIn("finish", result["row"]["unknown_fields"])
        self.assertIn("language", result["row"]["unknown_fields"])

    def test_promoted_snapshot_replay_and_identity_drift_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = root / "data/canonical"
            shutil.copytree(ROOT / "data/canonical/games", canonical / "games")
            shutil.copyfile(ROOT / "data/canonical/state.json", canonical / "state.json")
            resolver = CanonicalCollectionResolver("magic", root / "data")
            query = CanonicalQueryEngine("magic", games_root=canonical / "games", data_root=root / "data")
            self.assertEqual(resolver.canonical_snapshot_id, query.snapshot().snapshot_id)
            self.assertEqual(resolver.canonical_digest, query.snapshot().snapshot_id.removeprefix("sha256:"))
            pid = next(iter(self.PRINTINGS))
            imported = {"schema_version": "collection-import-v1", "collection_id": "synthetic-pilot",
                        "source": {"type": "fixture", "name": "synthetic"}, "source_import_digest": "synthetic",
                        "entries": [{"printing_id": pid, "quantity": 1}]}
            resolution = resolver.resolve(imported)
            snapshot = create_snapshot(imported, resolution, root / "snapshots", "immutable")
            original = (root / "snapshots/immutable.json").read_bytes()
            self.assertEqual(snapshot["canonical_snapshot_id"], query.snapshot().snapshot_id)
            replay = create_snapshot(imported, resolution, root / "snapshots", "immutable")
            self.assertEqual(replay["replay"], "exact_replay")
            self.assertEqual(original, (root / "snapshots/immutable.json").read_bytes())
            state = json.loads((canonical / "state.json").read_bytes())
            state["printing"][pid]["values"]["language"] = "French"
            (canonical / "state.json").write_text(json.dumps(state))
            changed = CanonicalCollectionResolver("magic", root / "data")
            self.assertNotEqual(resolver.canonical_digest, changed.canonical_digest)
            with self.assertRaises(CollectionIntelligenceError):
                create_snapshot(imported, changed.resolve(imported), root / "snapshots", "immutable")
            state["printing"][pid]["values"]["language"] = "English"
            state["printing"][pid]["provenance"]["artifact_identifier"] = "changed-source"
            (canonical / "state.json").write_text(json.dumps(state))
            changed_source = CanonicalCollectionResolver("magic", root / "data")
            self.assertNotEqual(resolver.canonical_digest, changed_source.canonical_digest)
            state["printing"][pid]["superseded_status"] = True
            (canonical / "state.json").write_text(json.dumps(state))
            superseded = CanonicalCollectionResolver("magic", root / "data")
            self.assertEqual(superseded.resolve(imported)["results"][0]["status"], "unresolved")

    def test_promoted_state_is_not_reinterpreted_as_another_game(self):
        with self.assertRaisesRegex(CollectionIntelligenceError, "game scope"):
            CanonicalCollectionResolver("unrelated-game", ROOT / "data")


if __name__ == "__main__": unittest.main()
