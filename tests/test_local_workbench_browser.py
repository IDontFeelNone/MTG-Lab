"""Actual Chromium acceptance. Optional tools are not runtime dependencies."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest

from probability.supplied_deck import assess_supplied_decks
from workbench.server import create_server

BROWSER = shutil.which('chromium') or shutil.which('google-chrome')
AVAILABLE = importlib.util.find_spec('playwright') is not None and BROWSER is not None


@unittest.skipUnless(AVAILABLE, 'actual browser acceptance requires optional Playwright and Chromium')
class WorkbenchBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.server=create_server();cls.origin='http://127.0.0.1:'+str(cls.server.server_port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);cls.thread.start()
        cls.play=sync_playwright().start()
        cls.browser=cls.play.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.play.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join(5)

    def setUp(self):
        self.context=self.browser.new_context(accept_downloads=True)
        self.addCleanup(self.context.close);self.page=self.context.new_page();self.external=[];self.errors=[]
        self.page.on('request',lambda r:self.external.append(r.url) if not r.url.startswith(self.origin+'/') and not r.url.startswith('blob:') else None)
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto(self.origin);self.page.get_by_role('button',name='Load fictional example (replaces inputs)').click()

    def calculate(self):
        with self.page.expect_response(lambda r:r.url==self.origin+'/assess') as response:
            self.page.get_by_role('button',name='Calculate exact access').click()
        value=response.value.json();self.page.wait_for_function("!document.getElementById('calculate').disabled")
        return value

    def download(self):
        with self.page.expect_download() as info:self.page.get_by_role('button',name='Download current report (JSON)').click()
        return json.loads(Path(info.value.path()).read_text())

    def test_actual_duplicate_benchmark_exact_delta_and_explicit_download(self):
        self.page.get_by_role('button',name='Duplicate as alternative').click()
        candidate=self.page.get_by_role('region',name='Alternative deck')
        candidate.get_by_label('Copies',exact=True).nth(0).fill('4');candidate.get_by_label('Copies',exact=True).nth(1).fill('56')
        r=self.calculate();self.assertEqual(r['analysis'],assess_supplied_decks(r['input']['analysis']))
        self.assertIn('5397/17110',self.page.locator('#results').inner_text());self.assertIn('38962/97527',self.page.locator('#results').inner_text())
        self.assertIn('81991/975270',self.page.locator('#results').inner_text());self.assertIn('8.407005239575 percentage points',self.page.locator('#results').inner_text())
        self.assertEqual(self.download(),r);self.assertFalse(self.errors);self.assertFalse(self.external)
        self.page.get_by_role('region',name='Baseline deck').get_by_label('Card label',exact=True).nth(0).fill('Shared display label')
        self.assertEqual(candidate.get_by_label('Card label',exact=True).nth(0).input_value(),'Shared display label')

    def test_manual_entry_groups_observations_sections_and_completeness(self):
        self.page.reload();deck=self.page.get_by_role('region',name='Baseline deck')
        for _ in range(3):deck.get_by_role('button',name='Add new card',exact=True).click()
        labels=deck.get_by_label('Card label',exact=True);labels.nth(0).fill('My declared target');labels.nth(1).fill('Other cards');labels.nth(2).fill('Sideboard only')
        qty=deck.get_by_label('Copies',exact=True);qty.nth(0).fill('4');qty.nth(1).fill('56');qty.nth(2).fill('15')
        deck.get_by_label('Section',exact=True).nth(2).fill('sideboard');deck.get_by_label('Section',exact=True).nth(2).press('Tab')
        deck.get_by_role('checkbox',name='Group 1 member local-card-1',exact=True).check()
        refused=self.calculate();self.assertEqual(refused['status'],'REFUSED');self.assertTrue(self.page.locator('#download').is_disabled())
        deck.get_by_label('I have listed the complete selected population.').check()
        deck.get_by_role('button',name='Add observation',exact=True).click()
        deck.get_by_label('Observation label',exact=True).nth(1).fill('Nine seen assumption');deck.get_by_label('Cards seen',exact=True).nth(1).fill('9')
        report=self.calculate();self.assertEqual(report['analysis']['configurations'][0]['deck_size'],60)
        self.assertEqual(report['analysis']['configurations'][0]['derived_groups'][0]['copies'],4)
        self.assertEqual(len(report['analysis']['configurations'][0]['results']),2)
        deck.get_by_role('button',name='Remove observation').nth(1).click();deck.get_by_role('button',name='Remove entry').nth(2).click()
        self.assertEqual(self.calculate()['analysis']['configurations'][0]['deck_size'],60)

    def test_three_groups_joint_result_overlap_and_valid_impossible_event(self):
        deck=self.page.get_by_role('region',name='Baseline deck')
        deck.get_by_label('Copies',exact=True).nth(1).fill('56')
        deck.get_by_role('button',name='Add new card',exact=True).click()
        for _ in range(2):deck.get_by_role('button',name='Add group',exact=True).click()
        self.assertTrue(deck.get_by_role('button',name='Add group',exact=True).is_disabled())
        deck.get_by_role('checkbox',name='Group 2 member local-card-2',exact=True).check();deck.get_by_role('checkbox',name='Group 3 member local-card-3',exact=True).check()
        r=self.calculate();self.assertEqual(r['analysis'],assess_supplied_decks(r['input']['analysis']))
        deck.get_by_role('checkbox',name='Group 2 member local-card-1',exact=True).check()
        self.assertEqual(self.calculate()['status'],'REFUSED')
        deck.get_by_role('checkbox',name='Group 2 member local-card-1',exact=True).uncheck()
        deck.get_by_label('Minimum cards required',exact=True).nth(0).fill('4')
        r=self.calculate();self.assertEqual(r['analysis']['configurations'][0]['status'],'IMPOSSIBLE_POPULATION_REQUIREMENT')
        self.assertIn('Valid deck, impossible requirement',self.page.locator('#results').inner_text())
        deck.get_by_role('button',name='Remove group',exact=True).nth(0).click()
        deck.get_by_role('button',name='Add group',exact=True).click()
        group_labels=deck.get_by_label('Group label',exact=True).evaluate_all('(rows)=>rows.map(r=>r.value)')
        self.assertEqual(len(set(group_labels)),3)
        deck.get_by_role('checkbox',name='Group 3 member local-card-1',exact=True).check()
        self.assertEqual(self.calculate()['status'],'ASSESSED')
        for _ in range(2):deck.get_by_role('button',name='Add observation',exact=True).click()
        deck.get_by_role('button',name='Remove observation',exact=True).nth(0).click()
        deck.get_by_role('button',name='Add observation',exact=True).click()
        observation_labels=deck.get_by_label('Observation label',exact=True).evaluate_all('(rows)=>rows.map(r=>r.value)')
        self.assertEqual(len(set(observation_labels)),3)

    def test_non_equivalent_questions_abstain_and_identity_survives_duplication(self):
        self.page.get_by_role('button',name='Duplicate as alternative').click()
        c=self.page.get_by_role('region',name='Alternative deck');c.get_by_label('Minimum cards required',exact=True).fill('2')
        r=self.calculate();self.assertEqual(r['analysis']['comparison']['status'],'ABSTAINED')
        self.assertIn('No direct improvement claim',self.page.locator('#results').inner_text())
        a,b=r['input']['analysis']['decks'];self.assertEqual(a['entries'],b['entries'])
        c.get_by_label('Minimum cards required',exact=True).fill('1');c.get_by_label('Observation label',exact=True).fill('Different')
        self.assertEqual(self.calculate()['analysis']['comparison']['status'],'ABSTAINED')

    def test_every_analytical_edit_invalidates_and_cannot_export_old_results(self):
        self.calculate();deck=self.page.get_by_role('region',name='Baseline deck')
        changes=[lambda:deck.get_by_label('Card label',exact=True).nth(0).fill('Edited label'),
            lambda:deck.get_by_label('Copies',exact=True).nth(0).fill('3'),
            lambda:deck.get_by_label('Selected draw section',exact=True).fill('main'),
            lambda:deck.get_by_label('Group label',exact=True).fill('Edited group'),
            lambda:deck.get_by_label('Minimum cards required',exact=True).fill('1'),
            lambda:deck.get_by_label('Observation label',exact=True).fill('Edited observation'),
            lambda:deck.get_by_label('Cards seen',exact=True).fill('8'),
            lambda:deck.get_by_label('I have listed the complete selected population.').uncheck()]
        for change in changes:
            change();self.assertTrue(self.page.locator('#download').is_disabled());self.assertEqual(self.page.locator('#results').inner_text(),'')
            self.page.get_by_role('button',name='Load fictional example (replaces inputs)').click();self.calculate()
        deck.get_by_role('checkbox',name='Group 1 member local-card-1',exact=True).uncheck();self.assertTrue(self.page.locator('#download').is_disabled())
        self.page.get_by_role('button',name='Load fictional example (replaces inputs)').click();self.calculate()
        self.page.get_by_role('button',name='Duplicate as alternative').click();self.assertTrue(self.page.locator('#download').is_disabled())
        self.calculate();self.page.get_by_role('button',name='Remove alternative',exact=True).click();self.assertTrue(self.page.locator('#download').is_disabled())

    def test_inflight_response_after_an_edit_never_becomes_current(self):
        pending=[]
        self.page.route('**/assess',lambda route:pending.append(route))
        self.page.get_by_role('button',name='Calculate exact access').click();self.page.wait_for_timeout(100)
        self.assertEqual(len(pending),1)
        self.page.get_by_label('Card label',exact=True).nth(0).fill('Changed while calculating')
        pending[0].continue_();self.page.wait_for_function("!document.getElementById('calculate').disabled")
        self.assertTrue(self.page.locator('#download').is_disabled());self.assertEqual(self.page.locator('#results').inner_text(),'')
        self.page.unroute('**/assess');r=self.calculate();self.assertEqual(self.download(),r)

    def test_script_labels_are_text_and_no_external_traffic_or_storage(self):
        text='<img src="https://invalid.test/x" onerror="window.injected=1">'
        self.page.get_by_label('Card label',exact=True).nth(0).fill(text)
        self.calculate();self.assertIn(text,self.page.locator('#results').inner_text())
        self.assertEqual(self.page.locator('#results img, #results script').count(),0)
        self.assertIsNone(self.page.evaluate('window.injected'))
        self.assertEqual(self.page.evaluate('localStorage.length'),0);self.assertEqual(self.page.evaluate('sessionStorage.length'),0)
        self.assertFalse(self.external);self.assertFalse(self.errors)
        self.page.reload();self.assertEqual(self.page.locator('[data-entry-id]').count(),0);self.assertTrue(self.page.locator('#download').is_disabled())

    def test_mobile_layout_has_no_horizontal_page_overflow(self):
        self.page.set_viewport_size({'width':390,'height':844});self.calculate()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))


if __name__=='__main__':unittest.main()
