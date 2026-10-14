"""Recovered original upload control flow with simulated platform transport."""
import hashlib, json, marshal, types, unittest, uuid
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).parent
def find(code,name):
    if code.co_name==name:return code
    for value in code.co_consts:
        if isinstance(value,types.CodeType):
            result=find(value,name)
            if result:return result

class Error(ValueError):
    def __init__(self,message,code='unknown'):super().__init__(message);self.code=code
class Unknown(Error):pass

class Clock:
    value=0
    def monotonic(self):return self.value
    def sleep(self,n):self.value+=n

class FlowTests(unittest.TestCase):
    def run_flow(self,ready=1,blank=False,existing=False,change_account=False,bad_hash=False):
        source=ROOT/'fixture.mp4';digest=hashlib.sha256(source.read_bytes()).hexdigest()
        payload=types.SimpleNamespace(source_path=str(source),source_sha256='bad' if bad_hash else digest,description='' if blank else '完整测试文案',topics=['装修'],short_title='')
        expected=types.SimpleNamespace(page_id='target',account='test-account')
        model={'uploads':0,'description_calls':0,'text':'已有内容' if existing else '', 'title':'','topics':[]}
        self.model=model
        class Page:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def _call(self,method,params):
                if method=='DOM.setFileInputFiles':model['uploads']+=1;return {}
                if method=='Runtime.evaluate' and 'crypto.subtle' in params['expression']:
                    return {'result':{'value':{'sha256':digest,'size':source.stat().st_size}}}
                if method=='Runtime.evaluate':return {'result':{'objectId':'file-input'}}
                raise AssertionError(method)
            def _evaluate(self,expression):
                if expression.startswith('delete window['):return True
                raise AssertionError(expression)
        def state(page):
            return {'route':'/creator-micro/content/post/video' if model['uploads'] else '/creator-micro/content/upload',
                'inputs':1,'editors':1,'files':model['uploads'],'videos':model['uploads'],
                'text':model['text'],'title':'','topics':model['topics'],'pending':False,'ready':ready if model['uploads'] else 0}
        def verify(target):
            if change_account and model['uploads']:raise Error('账号已切换',code='invalid_page_identity')
        def description(page,text,topics,verify_target):
            verify_target();model['description_calls']+=1;model['text']=text;model['topics']=topics;return state(page)
        module=marshal.loads((ROOT/'recovered/xcl_publish.integrations.native_douyin.marshal').read_bytes())
        env={'Path':Path,'file_sha256':lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),
            'XiaodouyaError':Error,'NativeSubmissionUnknown':Unknown,'_verify_target':verify,
            '_targets':lambda:[{'id':'target','url':'https://creator.douyin.com/creator-micro/content/upload'}], '_open':lambda t:Page(),'_state':state,'urlparse':urlparse,
            'json':json,'uuid':uuid,'time':Clock(),'POST':'/creator-micro/content/post/video',
            'UPLOAD':'/creator-micro/content/upload','fill_description':description,
            '_planned_value':lambda p:'2026-10-20 17:05',
            '_fill_schedule':lambda page,value,verify_target:state(page)}
        env['_ensure_empty']=types.FunctionType(find(module,'_ensure_empty'),env)
        env['is_douyin_page']=types.FunctionType(find(module,'is_douyin_page'),env)
        fill=types.FunctionType(find(module,'fill_native'),env)
        return fill(payload,expected,2)
    def test_original_preview_gate_stops_before_copy(self):
        with self.assertRaises(Unknown) as caught:self.run_flow(ready=0)
        self.assertEqual(self.model['uploads'],1);self.assertEqual(self.model['description_calls'],0)
        self.assertEqual(caught.exception.cause_code,'preview_timeout')
    def test_compatible_preview_reaches_copy_once(self):
        result=self.run_flow(ready=1)
        self.assertEqual(self.model['uploads'],1);self.assertEqual(self.model['description_calls'],1)
        self.assertEqual(result['description'],'完整测试文案');self.assertFalse(result['published'])
    def test_existing_content_not_overwritten(self):
        with self.assertRaises(Error):self.run_flow(existing=True)
        self.assertEqual(self.model['uploads'],0)
    def test_blank_description_not_uploaded(self):
        with self.assertRaises(Error):self.run_flow(blank=True)
        self.assertEqual(self.model['uploads'],0)
    def test_wrong_file_not_uploaded(self):
        with self.assertRaises(Error):self.run_flow(bad_hash=True)
        self.assertEqual(self.model['uploads'],0)
    def test_account_switch_after_upload_stops_no_replay(self):
        with self.assertRaises(Unknown):self.run_flow(change_account=True)
        self.assertEqual(self.model['uploads'],1);self.assertEqual(self.model['description_calls'],0)

if __name__=='__main__':unittest.main()
