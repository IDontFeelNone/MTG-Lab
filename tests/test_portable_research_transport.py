"""Actual loopback HTTP boundaries; no external provider or private collection."""
import http.client
import json
import threading
import unittest

from workbench.research import MAX_REQUEST_BYTES, create_research_server


class ResearchTransportTests(unittest.TestCase):
    def setUp(self):
        self.server=create_research_server();self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        self.thread.start();self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown();self.server.server_close();self.thread.join(5)

    def request(self,path='/research',body=None,**overrides):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        headers={'Host':f'127.0.0.1:{self.port}'}
        if body is not None:
            headers.update({'Origin':f'http://127.0.0.1:{self.port}','Content-Type':'application/json',
                            'X-MTG-Lab-Token':self.server.capability})
        headers.update(overrides)
        c.request('GET' if body is None else 'POST',path,body=body,headers=headers)
        r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result

    def test_local_routes_and_unchanged_editor_available(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        for path in ('/research','/research.js','/research.css','/','/app.js'):
            status,headers,raw=self.request(path);self.assertEqual(status,200)
            self.assertEqual(headers['Cache-Control'],'no-store')
            self.assertEqual(headers['X-Frame-Options'],'DENY')
            self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])

    def test_host_origin_and_cross_origin_rejection(self):
        body=b'{"operation":"example"}'
        for bad in ({'Host':'evil.example'},{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'},
                    {'Origin':'null'},{'X-MTG-Lab-Token':'wrong'}):
            self.assertEqual(self.request(body=body,**bad)[0],403)

    def test_oversized_and_wrong_content_type(self):
        self.assertEqual(self.request(body=b'{}',**{'Content-Type':'text/plain'})[0],415)
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        c.putrequest('POST','/research');c.putheader('Origin',f'http://127.0.0.1:{self.port}')
        c.putheader('Content-Type','application/json');c.putheader('X-MTG-Lab-Token',self.server.capability)
        c.putheader('Content-Length',str(MAX_REQUEST_BYTES+1));c.endheaders()
        response=c.getresponse();self.assertEqual(response.status,413);response.read();c.close()

    def test_original_example_round_trip_and_export(self):
        status,_,raw=self.request(body=b'{"operation":"example"}');self.assertEqual(status,200)
        artifact=json.loads(raw)['artifact']
        status,_,raw=self.request(body=json.dumps(dict(operation='open',artifact=json.dumps(artifact))).encode())
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['artifact'],artifact)
        status,_,raw=self.request(body=json.dumps(dict(operation='export',artifact=artifact,
            revision_ids=[r['revision_id'] for r in artifact['revisions']])).encode())
        self.assertEqual(status,200);self.assertIn('81991/975270',json.loads(raw)['handoff'])

    def test_no_filesystem_endpoint_or_executable_dispatch(self):
        for path in ('/../../etc/passwd','/research?path=/etc/passwd','/save','/collection','/research-panel.html'):
            self.assertEqual(self.request(path)[0],404)
        for body in (b'{"operation":"exec","command":"touch /tmp/x"}',b'{"operation":"example","path":"/etc/passwd"}',
                     b'{"operation":"example","operation":"exec"}'):
            self.assertEqual(self.request(body=body)[0],422)

    def test_malformed_artifact_is_structured_refusal(self):
        status,_,raw=self.request(body=b'{"operation":"open","artifact":{"approved":true}}')
        self.assertEqual(status,422);self.assertEqual(json.loads(raw)['status'],'REFUSED')
        self.assertNotIn('/workspace',raw.decode())


if __name__=='__main__':unittest.main()
