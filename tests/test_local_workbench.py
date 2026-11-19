"""Real local transport, strict presentation inputs and unchanged analytical owners."""
import copy
import http.client
import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from probability.supplied_deck import assess_supplied_decks
from workbench.adapter import (INPUT_VERSION, MAX_INPUT_BYTES, WorkbenchError,
                               assess_workbench, parse_workbench, _percent)
from workbench.server import Handler, LocalServer, create_server

ROOT = Path(__file__).resolve().parents[1]


def request(two=False):
    deck = dict(deck_id='baseline', identity_authority='CALLER_DECLARED', complete=True,
        draw_population=dict(section='main', declared_size=60),
        entries=[dict(card_id='local-card-1', section='main', quantity=3),
                 dict(card_id='local-card-2', section='main', quantity=57)],
        groups=[dict(group_id='Key cards', members=['local-card-1'], minimum=1)],
        schedule=[dict(label='Opening hand assumption', cards_seen=7)],
        assumptions=dict(sampling='uniform-without-replacement', group_disjointness='caller_declared'))
    decks=[deck]
    if two:
        other=copy.deepcopy(deck);other['deck_id']='candidate'
        other['entries'][0]['quantity']=4;other['entries'][1]['quantity']=56;decks.append(other)
    return dict(schema_version=INPUT_VERSION, labels=[
        dict(card_id='local-card-1',label='Fictional target'),
        dict(card_id='local-card-2',label='Fictional remainder')],
        analysis=dict(schema_version='supplied-deck-consistency-input-v1',decks=decks))


class WorkbenchAdapterTests(unittest.TestCase):
    def test_exact_owner_report_and_three_four_copy_benchmark(self):
        value=request(True);report=assess_workbench(value)
        self.assertEqual(report['analysis'],assess_supplied_decks(value['analysis']))
        rows=report['analysis']['configurations']
        self.assertEqual([(r['results'][0]['probability']['numerator'],r['results'][0]['probability']['denominator']) for r in rows], [('5397','17110'),('38962','97527')])
        p=report['analysis']['comparison']['differences'][0]['candidate_minus_baseline']
        self.assertEqual((p['numerator'],p['denominator']),('81991','975270'))
        self.assertEqual(report['presentation']['differences'][0]['percentage_points'],'8.407005239575')

    def test_generic_three_group_joint_case_and_multiple_observations(self):
        value=request();d=value['analysis']['decks'][0]
        d['entries']=[dict(card_id=str(i),section='main',quantity=q) for i,q in enumerate([2,3,4,51])]
        value['labels']=[dict(card_id=str(i),label='Declared '+str(i)) for i in range(4)]
        d['groups']=[dict(group_id='group'+str(i),members=[str(i)],minimum=1) for i in range(3)]
        d['schedule']=[dict(label=str(i),cards_seen=i) for i in (0,3,7,20)]
        self.assertEqual(assess_workbench(value)['analysis'],assess_supplied_decks(value['analysis']))

    def test_impossible_is_valid_and_not_malformed(self):
        value=request();value['analysis']['decks'][0]['groups'][0]['minimum']=4
        report=assess_workbench(value);d=report['analysis']['configurations'][0]
        self.assertEqual(d['status'],'IMPOSSIBLE_POPULATION_REQUIREMENT')
        self.assertEqual(d['results'][0]['probability']['numerator'],'0')

    def test_comparison_abstention_is_preserved(self):
        for key in ('members','minimum','schedule','section'):
            value=request(True);d=value['analysis']['decks'][1]
            if key=='members':d['groups'][0]['members']=['local-card-2']
            elif key=='minimum':d['groups'][0]['minimum']=2
            elif key=='schedule':d['schedule'][0]['label']='Different assumption'
            else:
                d['draw_population']['section']='sideboard'
                for e in d['entries']:e['section']='sideboard'
            report=assess_workbench(value)
            self.assertEqual(report['analysis']['comparison']['status'],'ABSTAINED')
            self.assertEqual(report['presentation']['differences'],[])

    def test_input_output_ownership_reordering_and_identities(self):
        value=request(True);old=copy.deepcopy(value);a=assess_workbench(value)
        self.assertEqual(value,old);self.assertEqual(a,assess_workbench(value))
        value['labels'].reverse()
        for d in value['analysis']['decks']:d['entries'].reverse()
        self.assertEqual(a,assess_workbench(value))
        a['input']['labels'][0]['label']='mutated'
        self.assertEqual(assess_workbench(old),assess_workbench(value))
        value['labels'][0]['label']='changed label'
        b=assess_workbench(value);self.assertNotEqual(b['report_id'],assess_workbench(old)['report_id'])
        self.assertEqual(b['analysis'],assess_workbench(old)['analysis'])

    def test_label_bindings_are_closed_unique_and_not_canonical_admission(self):
        for alter in (lambda v:v.update(verified=True),lambda v:v.update(schema_version='future'),
            lambda v:v['labels'].append(dict(card_id='other',label='Unrelated')),
            lambda v:v['labels'].pop(),lambda v:v['labels'].append(v['labels'][0]),
            lambda v:v['labels'][0].update(label=''),lambda v:v['labels'][0].update(label='x'*129),
            lambda v:v['labels'][0].update(canonical=True)):
            value=request();alter(value)
            with self.assertRaises(WorkbenchError):assess_workbench(value)
        value=request();value['labels'][1]['label']=value['labels'][0]['label']
        self.assertEqual(len(assess_workbench(value)['input']['labels']),2)

    def test_malformed_decks_groups_schedules_and_quantities_refuse(self):
        for alter in (lambda d:d.update(complete=False),lambda d:d['entries'][0].update(quantity=-1),
            lambda d:d['entries'][0].update(quantity=True),lambda d:d['entries'][0].update(quantity=1.5),
            lambda d:d['entries'][0].update(quantity='3'),lambda d:d['draw_population'].update(declared_size=61),
            lambda d:d.update(groups=[]),lambda d:d['groups'].append(d['groups'][0]),
            lambda d:d['groups'][0].update(members=['unknown']),lambda d:d['groups'][0].update(minimum=-1),
            lambda d:d['schedule'][0].update(cards_seen=21),lambda d:d['schedule'].append(dict(label='later',cards_seen=1)),
            lambda d:d['draw_population'].update(section='library')):
            value=request();alter(value['analysis']['decks'][0])
            with self.subTest(value=value),self.assertRaises(WorkbenchError):assess_workbench(value)

    def test_nonselected_sections_and_valid_aggregation_remain_native(self):
        value=request();d=value['analysis']['decks'][0]
        d['entries'][0]['quantity']=1;d['entries'].append(dict(card_id='local-card-1',quantity=2,section='main'))
        for s in ('sideboard','commander','companion','other:test'):
            d['entries'].append(dict(card_id='local-card-1',quantity=4,section=s))
        r=assess_workbench(value)['analysis']['configurations'][0]
        self.assertEqual(r['derived_groups'][0]['copies'],3);self.assertEqual(r['deck_size'],60)

    def test_strict_json_and_computation_output_budgets(self):
        for raw in (b'{"x":1,"x":2}',b'NaN',b'\xff',b'['*1500,b' '* (MAX_INPUT_BYTES+1)):
            with self.assertRaises(WorkbenchError):
                value=parse_workbench(raw);assess_workbench(value)
        with patch('workbench.adapter.MAX_REPORT_BYTES',100),self.assertRaises(WorkbenchError):assess_workbench(request())
        value=request();value['analysis']['decks'][0]['entries']*=513
        with self.assertRaises(WorkbenchError):assess_workbench(value)

    def test_percentage_formatting_uses_exact_values_and_half_even(self):
        self.assertEqual(_percent(dict(numerator='1',denominator='3')),'33.333333333333')
        self.assertEqual(_percent(dict(numerator='-1',denominator='3')),'-33.333333333333')
        self.assertEqual(_percent(dict(numerator='1',denominator=str(10**20))),'0.000000000000')

    def test_delegation_is_single_and_no_file_or_collection_access(self):
        value=request()
        with patch('workbench.adapter.assess_supplied_decks',wraps=assess_supplied_decks) as owner:
            with patch('builtins.open',side_effect=AssertionError('unexpected file access')):
                assess_workbench(value)
            owner.assert_called_once_with(value['analysis'])

    def test_existing_probability_cli_matches_embedded_analysis(self):
        value=request(True)
        run=subprocess.run([sys.executable,'-B','-m','probability','deck-consistency','--input','-'],
            input=json.dumps(value['analysis']),text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout),assess_workbench(value)['analysis'])


class WorkbenchTransportTests(unittest.TestCase):
    def setUp(self):
        self.server=create_server();self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);self.thread.start()
        self.addCleanup(self.close)
        self.origin='http://127.0.0.1:'+str(self.server.server_port)

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(5)

    def send(self,method='POST',path='/assess',body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        h={'Origin':self.origin,'X-MTG-Lab-Token':self.server.capability,'Content-Type':'application/json'}
        h.update(headers or {});raw=json.dumps(request()).encode() if body is None else body
        try:
            c.request(method,path,raw if method=='POST' else None,h);r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
        finally:c.close()

    def test_only_loopback_binding_and_valid_port_contract(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        with self.assertRaises(ValueError):LocalServer(('0.0.0.0',0),Handler)
        for port in (True,-1,65536,'8000',None):
            with self.assertRaises(ValueError):create_server(port)

    def test_real_transport_delegates_and_no_store_security_headers(self):
        status,headers,body=self.send();self.assertEqual(status,200)
        self.assertEqual(json.loads(body),assess_workbench(request()))
        self.assertEqual(headers['Cache-Control'],'no-store');self.assertIn("default-src 'none'",headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff');self.assertNotIn('Access-Control-Allow-Origin',headers)

    def test_fixed_assets_and_no_arbitrary_files_paths_or_download_route(self):
        for path in ('/','/app.js','/app.css'):
            status,_,body=self.send('GET',path);self.assertEqual(status,200)
            if path=='/':self.assertIn(self.server.capability.encode(),body);self.assertNotIn(b'__TOKEN__',body)
        for path in ('/../README.md','/%2e%2e/README.md','/?path=/etc/passwd','/download','/collection','/favicon.ico'):
            self.assertEqual(self.send('GET',path)[0],404)

    def test_host_origin_fetch_site_and_token_reject(self):
        for h in ({'Host':'evil.test'},{'Host':'localhost:'+str(self.server.server_port)},
            {'Origin':'null'},{'Origin':'https://evil.test'},{'Origin':self.origin+'/'},
            {'Sec-Fetch-Site':'cross-site'},{'X-MTG-Lab-Token':'bad'},{'X-MTG-Lab-Token':'é'}):
            with self.subTest(headers=h):self.assertEqual(self.send(headers=h)[0],403)
        self.assertEqual(self.send('GET','/',headers={'Host':'evil.test'})[0],403)
        self.assertEqual(self.send('GET','/app.js',headers={'Origin':'https://evil.test'})[0],403)

    def test_missing_origin_token_and_duplicate_header_ambiguity_reject(self):
        for field in ('Host','Origin','X-MTG-Lab-Token','Content-Length','Content-Type'):
            c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
            try:
                raw=json.dumps(request()).encode();h={'Host':self.origin[7:],'Origin':self.origin,
                    'X-MTG-Lab-Token':self.server.capability,'Content-Length':str(len(raw)),'Content-Type':'application/json'}
                c.putrequest('POST','/assess',skip_host=True)
                for k,v in h.items():c.putheader(k,v)
                c.putheader(field,h[field]);c.endheaders(raw);r=c.getresponse();self.assertNotEqual(r.status,200);r.read()
            finally:c.close()
        for excluded in ('Origin','X-MTG-Lab-Token'):
            c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
            try:
                h={'Origin':self.origin,'X-MTG-Lab-Token':self.server.capability,'Content-Type':'application/json'};del h[excluded]
                c.request('POST','/assess',json.dumps(request()),h);r=c.getresponse();self.assertEqual(r.status,403);r.read()
            finally:c.close()

    def test_bad_content_type_body_oversize_and_transfer_encoding_reject(self):
        self.assertEqual(self.send(headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.send(body=b'{}')[0],422)
        self.assertEqual(self.send(body=b' '* (MAX_INPUT_BYTES+1))[0],413)
        self.assertEqual(self.send(headers={'Transfer-Encoding':'chunked'})[0],400)
        self.assertEqual(self.send(headers={'Content-Length':'-1'})[0],400)
        self.assertEqual(self.send('OPTIONS','/assess')[0],501)
        self.assertEqual(self.send('POST','/not-an-api')[0],404)

    def test_untrusted_request_cannot_cause_outbound_traffic(self):
        # The accepted socket already exists; analysis must never initiate another connection.
        import socket
        original=socket.socket.connect
        permitted=('127.0.0.1',self.server.server_port)
        def local_only(sock,address):
            if address!=permitted:raise AssertionError('outbound analytical traffic')
            return original(sock,address)
        with patch('socket.socket.connect',local_only):self.assertEqual(self.send()[0],200)

    def test_label_injection_remains_json_data_without_logging(self):
        value=request();value['labels'][0]['label']='<img src=x onerror=alert(1)>'
        status,_,body=self.send(body=json.dumps(value).encode());self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['input']['labels'][0]['label'],value['labels'][0]['label'])

    def test_launcher_real_start_and_no_public_host_option(self):
        run=subprocess.Popen([sys.executable,'-B','-m','workbench'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            line=run.stdout.readline();self.assertIn('http://127.0.0.1:',line)
        finally:run.terminate();run.communicate(timeout=10)
        run=subprocess.run([sys.executable,'-B','-m','workbench','--host','0.0.0.0'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(run.returncode,2)


if __name__=='__main__':unittest.main()
