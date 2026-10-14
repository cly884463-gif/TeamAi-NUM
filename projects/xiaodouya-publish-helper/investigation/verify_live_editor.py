"""Resume only our exact synthetic form, with no upload or publish operations."""
import json,time
from pathlib import Path
from package_modules import install
package=install()
from xcl_publish.integrations import native_douyin as d
from xcl_publish.integrations.native_wechat import _targets,_open
t=d.discover_active();assert t.account=='早睡';d._verify_target(t)
p=_open(next(x for x in _targets() if x.get('id')==t.page_id))
try:
    s=d._state(p)
    assert ' '.join(s['text'].split())=='发布助手功能验证，请勿发布 #生活记录 #日常' and s['ready']==1 and s['topics']==['#生活记录','#日常'] and not s['title'],s
    main=_open(next(x for x in _targets() if x.get('id')==t.main_id))
    try:
        main._evaluate("document.activeElement.blur()")
    finally:main.close()
    assert p._evaluate('document.hasFocus()') is False
    d._focus_editor_end(p)
    for kind in ('keyDown','keyUp'):
        p._call('Input.dispatchKeyEvent',{'type':kind,'key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2})
    for kind in ('keyDown','keyUp'):
        p._call('Input.dispatchKeyEvent',{'type':kind,'key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8})
    time.sleep(.5)
    assert d._state(p)['text']=='',d._state(p)
    d.fill_description(p,'发布助手功能验证，请勿发布',('生活记录','日常'),lambda:d._verify_target(t))
    time.sleep(2)
    result=d._state(p)
    try:
        d.fill_description(p,'不应覆盖',(),lambda:d._verify_target(t))
    except Exception as e:
        assert getattr(e,'code',None)=='existing_content'
    else:raise AssertionError('Existing content guard did not stop')
    assert d._state(p)==result
    d._fill_schedule(p,'2026-10-13 17:05',lambda:d._verify_target(t))
    result=d._state(p)
    assert result['schedule_values']==['2026-10-13 17:05']
    result['package']=package.name
    result['embedded_focus_recovered']=True
    result['existing_content_protected']=True
    result['published']=False
    Path('build/live-douyin-validation/editor_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
finally:p.close()
