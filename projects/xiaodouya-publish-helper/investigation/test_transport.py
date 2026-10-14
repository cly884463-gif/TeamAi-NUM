import importlib.util, json, marshal, os, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).parent
# Use the websocket library shipped in the original package, not the developer PC's install.
LIB=ROOT.parent/'build'/'testlib'
for source in (ROOT/'recovered').glob('websocket*.marshal'):
    parts=source.name.removesuffix('.marshal').split('.')
    target=LIB.joinpath(*parts,'__init__.pyc') if len(parts)==1 else LIB.joinpath(*parts).with_suffix('.pyc')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(importlib.util.MAGIC_NUMBER+b'\0'*12+source.read_bytes())
sys.path.insert(0,str(LIB))
from websocket import WebSocketTimeoutException
from transport_replacement import _call

class Error(ValueError):
    def __init__(self,message,code='unknown'):
        super().__init__(message);self.code=code

_call.__globals__['XiaodouyaError']=Error

class Socket:
    def __init__(self,items=(),send_error=None):self.items=iter(items);self.sent=[];self.closed=False;self.send_error=send_error
    def settimeout(self,value):self.timeout=value
    def send(self,value):
        self.sent.append(value)
        if self.send_error:raise self.send_error
    def recv(self):
        value=next(self.items)
        if isinstance(value,Exception):raise value
        return value
    def close(self):self.closed=True

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        p=patch.dict(os.environ,{'XCL_PUBLISH_DATA_DIR':self.tmp.name});p.start();self.addCleanup(p.stop)
    def page(self,socket):return types.SimpleNamespace(socket=socket,timeout=2,sequence=0)
    def test_success_and_events(self):
        s=Socket(['{"method":"event"}','{"id":9,"result":{}}','{"id":1,"result":{"value":42}}'])
        self.assertEqual(_call(self.page(s),'Runtime.evaluate',{}),{'value':42})
        self.assertEqual(len(s.sent),1);self.assertFalse(s.closed)
        self.assertEqual(list(Path(self.tmp.name).rglob('*.json')),[])
    def test_failure_classification_and_no_replay(self):
        for raw,expected in [(TimeoutError('secret'),'cdp_response_timeout'),
            (WebSocketTimeoutException('secret'),'cdp_response_timeout'),
            (ConnectionResetError('secret'),'cdp_disconnected'),('', 'cdp_disconnected'),
            ('{secret','cdp_invalid_response'),('[]','cdp_invalid_response'),
            ('{"id":1,"error":{"message":"secret"}}','cdp_command_rejected'),
            ('{"id":1}','cdp_invalid_response')]:
            with self.subTest(expected=expected,raw=type(raw).__name__):
                s=Socket([raw]);page=self.page(s)
                with self.assertRaises(Error) as caught:_call(page,'Runtime.evaluate',{'expression':'secret credentials customer'})
                self.assertEqual(caught.exception.code,expected)
                report=Path(caught.exception.diagnostic_path).read_text(encoding='utf-8')
                self.assertNotIn('secret',report);self.assertNotIn('credentials',report)
                self.assertNotIn('secret',str(caught.exception));self.assertTrue(s.closed)
                with self.assertRaises(Error):_call(page,'DOM.setFileInputFiles',{})
                self.assertEqual(len(s.sent),1)
    def test_send_failure_unknown(self):
        for error,code in [(TimeoutError(),'cdp_send_timeout'),(ConnectionResetError(),'cdp_disconnected')]:
            s=Socket(send_error=error)
            with self.assertRaises(Error) as caught:_call(self.page(s),'DOM.setFileInputFiles',{})
            report=json.loads(Path(caught.exception.diagnostic_path).read_text(encoding='utf-8'))
            self.assertEqual(report['cause_code'],code);self.assertTrue(report['send_attempted'])
            self.assertEqual(len(s.sent),1)
    def test_save_failure_keeps_original_error(self):
        with patch('pathlib.Path.mkdir',side_effect=OSError('secret')):
            with self.assertRaises(Error) as caught:_call(self.page(Socket([TimeoutError()])),'Runtime.evaluate',{})
        self.assertEqual(caught.exception.code,'cdp_response_timeout')
        self.assertIn('诊断文件未能保存',str(caught.exception))
    def test_deadline_is_bounded(self):
        with patch('time.monotonic',side_effect=[0,3,3]):
            with self.assertRaises(Error) as caught:_call(self.page(Socket()),'Runtime.evaluate',{})
        self.assertEqual(caught.exception.code,'cdp_response_timeout')
    def test_old_code_mislabels_disconnect(self):
        code=marshal.loads((ROOT/'recovered/xcl_publish.integrations.xiaodouya.marshal').read_bytes())
        def find(c):
            if c.co_qualname=='CdpDraftPage._call':return c
            for value in c.co_consts:
                if isinstance(value,types.CodeType):
                    result=find(value)
                    if result:return result
        import time
        old=types.FunctionType(find(code),{'time':time,'json':json,'XiaodouyaError':Error})
        with self.assertRaises(Error) as caught:old(self.page(Socket([ConnectionResetError()])),'Runtime.evaluate',{})
        self.assertIn('超时',str(caught.exception))

if __name__=='__main__':unittest.main()
