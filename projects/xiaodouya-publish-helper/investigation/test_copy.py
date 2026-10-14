import json,unittest
from pathlib import Path
from package_modules import install
package=install()
from xcl_publish import domain as d

class Tests(unittest.TestCase):
    def test_putian_reported_opening(self):
        expected='在莆田厨房卫生间想要改造的朋友注意了'
        raw=expected+'莆田阿明带着他的黑科技改造了无数个卫生间以及厨房别人翻新又拆又砸而他做翻新不拆不砸不扰民在老旧瓷砖上'
        for suffix in ('','。'):
            with self.subTest(suffix=suffix):
                self.assertEqual(d.publish_text_defaults(raw+suffix),(expected,''))
        self.assertEqual(d.opening_prefix(expected),expected)
        draft=d.Draft(path='putian.mp4',stamp=[1,1])
        draft.finish_preprocess(raw,'test','hash')
        self.assertEqual(draft.sentence,expected)
        self.assertEqual(draft.description,expected)
    def test_callouts_not_customer_specific(self):
        for first in ('在厦门准备装修的朋友们注意啦','想要翻新卫生间的业主看过来','各位准备装修的老板听好了'):
            self.assertEqual(d.opening_prefix(first+'接下来介绍我们的服务'),first)
    def test_callout_false_positives(self):
        for source in ('在莆田装修的朋友注意了哪些问题','我提醒朋友注意了施工细节','他说“在莆田装修的朋友注意了”然后离开','在莆田装修的朋友注意防水施工'):
            self.assertEqual(d.opening_prefix(source),source)
    def test_actual_reported_caption(self):
        raw='在珠海做旧改我们真正做到不拆不砸真正做到'
        expected='在珠海做旧改，我们真正做到不拆不砸。'
        self.assertEqual(d.publish_text_defaults(raw),(expected,''))
        self.assertEqual(d.opening_prefix(expected),expected)
    def test_long_complete_sentence_not_cut(self):
        raw='我们用三天时间完成这套老房的厨房和卫生间翻新。后面介绍施工过程。'
        expected=raw.split('。')[0]+'。'
        self.assertGreater(len(expected),20)
        self.assertEqual(d.opening_prefix(raw),expected)
    def test_unknown_boundary_not_invented(self):
        for text in ('准备把住了三十年的老房墙面','我们每天每天认真施工','在这里不仅真正做到省钱而且真正做到省心','在这里真正做到好真正做到'):
            self.assertEqual(d.opening_prefix(text),text)
    def test_limit_is_validation_not_slicing(self):
        text='没有标点的待人工核对原文'*5
        self.assertGreater(len(text),40)
        self.assertEqual(d.opening_prefix(text),text)
        self.assertEqual(d.publish_text_defaults(text),(text,''))
        self.assertEqual(d.OPENING_PREFIX_MAX_CHARS,40)
        self.assertEqual(d.DESCRIPTION_MAX_CHARS,40)
        self.assertEqual(d.SHORT_TITLE_MAX_CHARS,16)
    def test_generated_draft_and_manual_copy(self):
        draft=d.Draft(path='isolated.mp4',stamp=[1,1])
        draft.finish_preprocess('在珠海做旧改我们真正做到不拆不砸真正做到','test','hash')
        self.assertEqual(draft.description,'在珠海做旧改，我们真正做到不拆不砸。')
        draft.update(sentence='人工核对的首句',description='人工改好的文案')
        draft.finish_preprocess('其他内容','test','hash')
        self.assertEqual(draft.description,'人工改好的文案')

if __name__=='__main__':unittest.main()
