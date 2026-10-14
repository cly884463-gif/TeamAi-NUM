"""Controlled experiment on the already uploaded synthetic test, never uploads/publishes."""
import json, time
from package_modules import install
install()
from xcl_publish.integrations import native_douyin as d
from xcl_publish.integrations.native_wechat import _targets, _open
t=d.discover_active()
assert t.account == '早睡'
d._verify_target(t)
main=_open(next(x for x in _targets() if x.get('id')==t.main_id))
try:
    assert main._evaluate("(() => {const vs=Array.from(document.querySelectorAll('webview')).filter(x=>x.getClientRects().length&&new URL(x.src).hostname==='creator.douyin.com');if(vs.length!==1)return false;vs[0].focus();return document.activeElement===vs[0]})()") is True
finally:main.close()
p=_open(next(x for x in _targets() if x.get('id')==t.page_id))
try:
    s=d._state(p)
    assert s['text']=='发布助手功能发布助手功能验证，请勿发布' and s['ready']==1 and not s['topics'] and not s['title'],s
    d._focus_editor_end(p)
    for kind in ('keyDown','keyUp'):
        p._call('Input.dispatchKeyEvent',{'type':kind,'key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2})
    for kind in ('keyDown','keyUp'):
        p._call('Input.dispatchKeyEvent',{'type':kind,'key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8})
    time.sleep(.5)
    assert d._state(p)['text']=='',d._state(p)
    d._verify_target(t)
    p._call('Input.insertText',{'text':'发布助手功能验证，请勿发布'})
    time.sleep(1)
    print(json.dumps(d._state(p),ensure_ascii=False))
finally:p.close()
