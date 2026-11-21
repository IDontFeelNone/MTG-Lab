"""Real Chromium research acceptance; optional tools are not runtime dependencies."""
import json
from pathlib import Path
import threading
import unittest

from test_local_workbench_browser import AVAILABLE, BROWSER
from workbench.research import create_research_server
from workbench.investigations import open_investigation


@unittest.skipUnless(AVAILABLE,'actual browser acceptance requires optional Playwright and Chromium')
class ResearchBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.server=create_research_server();cls.origin='http://127.0.0.1:'+str(cls.server.server_port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);cls.thread.start()
        cls.play=sync_playwright().start();cls.browser=cls.play.chromium.launch(executable_path=BROWSER,
            headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.play.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join(5)

    def setUp(self):
        self.context=self.browser.new_context(accept_downloads=True);self.addCleanup(self.context.close)
        self.page=self.context.new_page();self.errors=[];self.external=[];self.downloads=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.on('request',lambda r:self.external.append(r.url) if not r.url.startswith(self.origin+'/') and not r.url.startswith('blob:') else None)
        self.page.on('download',lambda d:self.downloads.append(d))
        self.page.goto(self.origin+'/research')

    def action(self,selector):
        with self.page.expect_response(lambda r:r.url==self.origin+'/research') as info:
            self.page.locator(selector).click()
        self.page.wait_for_function('!researchBusy')
        return info.value.json()

    def example(self):
        self.action('#research-example')
        self.assertIn('Loaded saved revision',self.page.locator('#research-status').inner_text())

    def download(self,selector):
        with self.page.expect_download() as info:self.page.locator(selector).click()
        return Path(info.value.path()).read_bytes()

    def test_full_save_reopen_replay_and_selected_handoff(self):
        self.example();self.assertEqual(len(self.downloads),0)
        raw=self.download('#research-save');artifact=open_investigation(raw)
        self.assertEqual(len(artifact['revisions']),4)
        self.page.get_by_role('button',name='Load revision four-copy-test',exact=True).click()
        self.assertIn('5397/17110',self.page.locator('#results').inner_text())
        self.assertIn('38962/97527',self.page.locator('#results').inner_text())
        self.assertIn('81991/975270',self.page.locator('#results').inner_text())
        text=self.download('#research-export').decode();self.assertIn('81991/975270',text)
        self.page.reload();self.assertEqual(self.page.locator('#research-history').inner_text(),'')
        with self.page.expect_response(lambda r:r.url==self.origin+'/research'):
            self.page.locator('#research-open').set_input_files(dict(name='saved.json',mimeType='application/json',buffer=raw))
        self.page.wait_for_function('!researchBusy')
        self.assertEqual(json.loads(self.download('#research-save')),artifact)
        self.assertEqual(self.action('#research-replay')['calculations_verified'],3)
        self.assertEqual(self.errors,[]);self.assertEqual(self.external,[])

    def test_notes_before_calculation_and_no_injection_execution(self):
        self.page.locator('#research-question').fill('Could a different count help?')
        self.action('#research-new')
        self.page.locator('#research-notes').fill('<script>window.RESEARCH_CANARY=1</script> $(touch /tmp/nope)')
        self.action('#research-record')
        self.assertIsNone(self.page.evaluate('window.RESEARCH_CANARY'))
        v=json.loads(self.download('#research-save'));self.assertIsNone(v['revisions'][0]['result'])
        text=self.download('#research-export').decode();self.assertIn('NOT CALCULATED',text)
        self.assertIn('$(touch',text);self.assertEqual(self.errors,[])

    def test_editing_deck_and_annotations_blocks_stale_save_and_export(self):
        self.example();self.page.get_by_role('button',name='Load revision four-copy-test',exact=True).click()
        candidate=self.page.get_by_role('region',name='Alternative deck')
        candidate.get_by_label('Copies',exact=True).nth(1).fill('5')
        self.assertTrue(self.page.locator('#research-export').is_disabled())
        self.assertTrue(self.page.locator('#research-save').is_disabled())
        self.assertTrue(self.page.locator('#download').is_disabled());self.assertEqual(self.page.locator('#results').inner_text(),'')
        candidate.get_by_label('Copies',exact=True).nth(0).fill('55')
        with self.page.expect_response(lambda r:r.url==self.origin+'/assess'):
            self.page.locator('#calculate').click()
        self.page.wait_for_function('!busy');self.action('#research-record')
        v=json.loads(self.download('#research-save'));self.assertEqual(len(v['revisions']),5)
        self.assertEqual(v['revisions'][2]['analytical_input']['analysis']['decks'][1]['entries'][1]['quantity'],4)
        self.page.locator('#research-notes').fill('New unrecorded thought')
        self.assertTrue(self.page.locator('#research-export').is_disabled())

    def test_new_branch_is_independent_and_references_survive(self):
        self.example();self.page.get_by_role('button',name='Load revision baseline',exact=True).nth(1).click()
        self.page.locator('#research-branch').fill('independent-test')
        self.page.locator('#research-notes-only').check()
        self.page.locator('#research-hypothesis').fill('Another competing idea')
        self.page.locator('#research-reference').fill('user:manual-observation')
        self.action('#research-record')
        v=json.loads(self.download('#research-save'));self.assertEqual(len(v['revisions']),5)
        self.assertEqual(v['revisions'][-1]['parent_id'],v['revisions'][1]['revision_id'])
        self.assertEqual(v['revisions'][-1]['metadata']['evidence_references'][0]['reference'],'user:manual-observation')

    def test_tampered_import_retains_current_history(self):
        self.example();old=json.loads(self.download('#research-save'));bad=json.loads(json.dumps(old));bad['question']='tampered'
        with self.page.expect_response(lambda r:r.url==self.origin+'/research'):
            self.page.locator('#research-open').set_input_files(dict(name='bad.json',mimeType='application/json',buffer=json.dumps(bad).encode()))
        self.page.wait_for_function('!researchBusy')
        self.assertIn('REFUSED',self.page.locator('#research-status').inner_text())
        self.assertEqual(self.page.evaluate('investigation.artifact_id'),old['artifact_id'])

    def test_unselected_branch_notes_do_not_enter_handoff(self):
        self.example()
        for check in self.page.locator('[data-research-selection]').all():check.uncheck()
        self.page.locator('[data-research-selection]').nth(2).check()
        text=self.download('#research-export').decode()
        self.assertIn('38962/97527',text)
        self.assertNotIn('Two copies could improve access',text)
        self.assertEqual(self.errors,[]);self.assertEqual(self.external,[])

    def test_invalid_utf8_file_is_refused_without_replacement_decoding(self):
        self.page.locator('#research-open').set_input_files(dict(name='bad.json',mimeType='application/json',buffer=b'{"note":"\xff"}'))
        self.page.wait_for_function('!researchBusy')
        self.assertIn('REFUSED',self.page.locator('#research-status').inner_text())
        self.assertIsNone(self.page.evaluate('investigation'))

    def test_narrow_viewport_keeps_history_within_page(self):
        self.page.set_viewport_size(dict(width=390,height=844));self.example()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'))


if __name__=='__main__':unittest.main()
