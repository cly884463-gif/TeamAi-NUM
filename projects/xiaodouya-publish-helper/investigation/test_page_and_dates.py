import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
from package_modules import install
install()
from xcl_publish import dates
from xcl_publish.integrations import native_douyin as d
from xcl_publish.integrations.xiaodouya import XiaodouyaError

class Tests(unittest.TestCase):
    def state(self,**changes):
        return dict(route=d.UPLOAD,inputs=1,files=0,videos=0,text='',title='',pending=False,**{})|changes
    def test_empty_allowed(self):d._ensure_empty(self.state())
    def test_reasons_and_protection(self):
        for change,code,word in [({'pending':True},'existing_content','上次未发布'),({'files':1},'existing_content','已有'),({'videos':1},'existing_content','已有'),({'title':'existing'},'existing_content','已有'),({'route':'/home'},'wrong_page','尚未进入'),({'inputs':0},'page_loading','未就绪'),({'inputs':2},'page_loading','不唯一')]:
            with self.subTest(change=change),self.assertRaises(XiaodouyaError) as c:d._ensure_empty(self.state(**change))
            self.assertEqual(c.exception.code,code);self.assertIn(word,str(c.exception))
    def test_navigation_waits_for_input(self):
        target=SimpleNamespace(page_id='test',account='test')
        page=SimpleNamespace()
        class Context:
            def __enter__(self):return page
            def __exit__(self,*a):pass
        with patch.object(d,'discover_account',return_value=target),patch.object(d,'_targets',return_value=[{'id':'test','url':'https://creator.douyin.com'+d.UPLOAD}]),patch.object(d,'_verify_target'),patch.object(d,'_open',return_value=Context()),patch.object(d,'_state',side_effect=[self.state(inputs=0),self.state()]) as read,patch.object(d.time,'sleep'):
            self.assertIs(d.prepare_active(),target);self.assertEqual(read.call_count,2)
    def test_folder_dates_and_conflicts(self):
        cases={
          '广东珠海_刘天鹏_3_10月13日/广东珠海_刘天鹏_旧房翻新.mp4':'2026-10-13',
          '10月13日/10月14日.mp4':'',
          '10月13日_10月14日/视频.mp4':'',
          '客户/视频.mp4':'',
          '客户/2026-10-13.mp4':'2026-10-13',
          '10月13日/10月13日.mp4':'2026-10-13'}
        for path,expected in cases.items():
            with self.subTest(path=path):self.assertEqual(dates.detect_date_from_filename(path,date(2026,10,12)),expected)
if __name__=='__main__':unittest.main()
