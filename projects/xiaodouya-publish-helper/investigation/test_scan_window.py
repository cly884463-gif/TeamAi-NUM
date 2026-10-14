import unittest
from pathlib import Path
from package_modules import install
install(runtime_root=next(Path('build/candidate-r6').glob('*/_internal')))
from xcl_publish import subtitle_scan as s

class Picture:
    width=100;height=100
    def __init__(self,t):self.t=t
    def crop(self,box):return self

class Tests(unittest.TestCase):
    def scan(self,**kw):
        seen=[]
        def frame(path,t):seen.append(t);return Picture(t)
        def text(im,root):return '如何低成本改造' if im.t<1.5 else '一套老旧二手房'
        result=s.scan_opening_sentence('fake',Path('build'),frame_reader=frame,text_reader=text,**kw)
        return result,seen
    def test_default_window_and_merge(self):
        result,seen=self.scan()
        self.assertEqual(result,'如何低成本改造一套老旧二手房')
        self.assertEqual(s.DEFAULT_SCAN_SECONDS,2)
        self.assertEqual(seen,[.25,.5,.75,1,1.25,1.5,1.75,1.99])
    def test_manual_end_respected(self):
        _,seen=self.scan(end_seconds=3.0)
        self.assertGreater(max(seen),2);self.assertLess(max(seen),3)
    def test_no_automatic_extension(self):
        seen=[]
        class Decision:status='need_more';text=''
        result=s.scan_opening_sentence('fake',Path('build'),frame_reader=lambda p,t:(seen.append(t) or Picture(t)),text_reader=lambda im,r:'待核对字幕',boundary_selector=lambda text:Decision(),allow_extend=True)
        self.assertEqual(result,'待核对字幕')
        self.assertLess(max(seen),2)
    def test_uncertain_or_rewritten_output_still_blocked(self):
        from types import SimpleNamespace
        for status,text in [('uncertain',''),('complete','模型新编文案'),('need_more','不应出现的文字')]:
            with self.subTest(status=status),self.assertRaises(ValueError):
                self.scan(boundary_selector=lambda source:SimpleNamespace(status=status,text=text))
    def test_complete_prefix_and_review_gate(self):
        from types import SimpleNamespace
        from xcl_publish.domain import Draft
        result,_=self.scan(boundary_selector=lambda source:SimpleNamespace(status='complete',text=source))
        draft=Draft(path='fake.mp4',stamp=[1,1]);draft.finish_preprocess(result,'test','hash')
        self.assertEqual(draft.description,result)
        self.assertFalse(draft.confirmed)
    def test_damaged_adjacent_frame_consensus(self):
        self.assertEqual(s.merge_candidates(['如何低成本改造']*5+['一套老旧二手房']*2+['套老旧二手房']),'如何低成本改造一套老旧二手房')
if __name__=='__main__':unittest.main()
