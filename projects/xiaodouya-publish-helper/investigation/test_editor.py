"""Safety regressions against compiled functions in the candidate ZIP (mock transport)."""
import unittest
from unittest.mock import patch
from package_modules import install
install()
from xcl_publish.integrations import native_douyin as d
from xcl_publish.integrations.xiaodouya import XiaodouyaError

class Page:
    def __init__(self,focus=True,mode='ok'):
        self.focus=focus;self.mode=mode;self.text='已有前缀';self.calls=[]
    def _evaluate(self,expression):return self.focus
    def _call(self,method,params):
        self.calls.append((method,params))
        if self.mode=='error':raise XiaodouyaError('unknown result',code='cdp_response_timeout')
        if self.mode=='ok':self.text+=params['text']
        if self.mode=='duplicate':self.text+=params['text']*2

class Tests(unittest.TestCase):
    def test_native_input_once(self):
        p=Page()
        with patch.object(d,'_state',lambda p:{'text':p.text}):d._insert(p,'中文正文')
        self.assertEqual(p.calls,[('Input.insertText',{'text':'中文正文'})])
        self.assertEqual(p.text,'已有前缀中文正文')
    def test_lost_focus_sends_nothing(self):
        p=Page(False)
        with self.assertRaises(XiaodouyaError):d._insert(p,'正文')
        self.assertEqual(p.calls,[])
    def test_incomplete_or_duplicate_does_not_retry(self):
        for mode in ('missing','duplicate','error'):
            with self.subTest(mode=mode):
                p=Page(mode=mode)
                with patch.object(d,'_state',lambda p:{'text':p.text}):
                    with self.assertRaises(XiaodouyaError):d._insert(p,'正文')
                self.assertEqual(len(p.calls),1)
    def test_other_active_page_stops_before_container_focus(self):
        p=Page(False)
        target=type('Target',(),{'origin':123})()
        with patch.object(d,'discover_active',return_value=target),patch.object(d,'_verify_target'):
            with self.assertRaises(XiaodouyaError):d._focus_editor_end(p)
        self.assertEqual(p.calls,[])

if __name__=='__main__':unittest.main()
