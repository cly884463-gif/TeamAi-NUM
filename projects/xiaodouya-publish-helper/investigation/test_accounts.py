import json, marshal, os, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
from package_modules import install
install()
from xcl_publish.integrations import native_account_navigation as n

class Clock:
    def __init__(self): self.now = 0
    def monotonic(self): return self.now
    def sleep(self, delay): self.now += delay

class Main:
    def __enter__(self): return self
    def __exit__(self, *args): pass

class Accounts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.clock = Clock()
        for p in [patch.object(n, 'time', self.clock), patch.object(n, '_targets', return_value=[]),
                  patch.object(n, '_select_main_page', return_value={}), patch.object(n, '_open', return_value=Main()),
                  patch.object(n, '_clear_search_filter'), patch.dict(os.environ, XCL_PUBLISH_DATA_DIR=self.tmp.name)]:
            p.start(); self.addCleanup(p.stop)
        self.platform = next(iter(n.PLATFORM_LABELS))

    def test_original_scanner_two_slow_complete_passes(self):
        clock = self.clock
        class Pages(Main):
            def __init__(self): self.count = 0; self.restores = 0
            def _evaluate(self, js):
                if 'delete window.__xclAccountScan' in js:
                    self.restores += 1; return True
                if 'processed:new WeakSet()' in js:
                    self.count = 0; return {'ok': True}
                clock.sleep(.35)
                self.count += 1
                return {'rows': [{'name': 'private-account-'+str(self.count), 'id': str(self.count)}],
                        'top': self.count*100, 'max': 10000, 'done': self.count == 100, 'expanded': 0}
        code = marshal.loads((Path(__file__).parent/'recovered/xcl_publish.integrations.native_account_navigation.marshal').read_bytes())
        old = types.FunctionType(next(c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name=='list_logged_accounts'), n.__dict__, argdefs=(60,))
        main = Pages()
        with patch.object(n, '_open', return_value=main):
            with self.assertRaises(n.XiaodouyaError) as caught: old(self.platform)
            self.assertIn('超时', str(caught.exception))
            self.assertEqual(main.restores, 2)
            clock.now = 0
            result = n.list_logged_accounts(self.platform)
            self.assertEqual(len(result), 100)
            self.assertGreater(clock.now, 60)
            self.assertLess(clock.now, 120)
            self.assertEqual(main.restores, 4)

    def test_changed_then_stable_and_never_partial(self):
        with patch.object(n, '_scan_account_inventory', side_effect=[(('A',),()), (('A','B'),()), (('A','B'),())]) as scan:
            self.assertEqual(n.list_logged_accounts(self.platform), ('A','B')); self.assertEqual(scan.call_count, 3)
        with patch.object(n, '_scan_account_inventory', side_effect=[(('A',),()), (('B',),()), (('C',),())]) as scan:
            with self.assertRaises(n.XiaodouyaError): n.list_logged_accounts(self.platform)
            self.assertEqual(scan.call_count, 3)

    def test_duplicate_empty_disconnect_and_diagnostic_privacy(self):
        cases = [([(('secret-account',), ('secret-account',))], 'target_account_ambiguous', 1),
                 ([((),()), ((),())], 'target_account_missing', 2),
                 ([n.XiaodouyaError('模拟断线', code='cdp_disconnected')], 'cdp_disconnected', 1),
                 ([(('secret-account',),()), n.XiaodouyaError('模拟超时',code='account_list_unstable')], 'account_list_unstable', 2)]
        for responses, code, calls in cases:
            with self.subTest(code=code), patch.object(n, '_scan_account_inventory', side_effect=responses) as scan:
                with self.assertRaises(n.XiaodouyaError) as caught: n.list_logged_accounts(self.platform)
                self.assertEqual(caught.exception.code, code); self.assertEqual(scan.call_count, calls)
        paths = list(Path(self.tmp.name).rglob('*.json')); self.assertEqual(len(paths), 4)
        for path in paths:
            text = path.read_text(encoding='utf-8'); self.assertNotIn('secret-account', text)
            report=json.loads(text); self.assertFalse(report['partial_results_returned']); self.assertEqual(report['version'],'v0.5.44-r13')

    def test_filter_failure_does_not_scan(self):
        with patch.object(n, '_clear_search_filter', side_effect=n.XiaodouyaError('failed',code='account_filter_unavailable')), patch.object(n, '_scan_account_inventory') as scan:
            with self.assertRaises(n.XiaodouyaError): n.list_logged_accounts(self.platform)
            scan.assert_not_called()

if __name__ == '__main__': unittest.main()
