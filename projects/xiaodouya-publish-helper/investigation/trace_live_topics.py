import json,time
from pathlib import Path
from package_modules import install
install()
from xcl_publish.integrations import native_douyin as d
from xcl_publish.integrations.native_wechat import _targets,_open
t=d.discover_active();assert t.account=='早睡';d._verify_target(t)
p=_open(next(x for x in _targets() if x.get('id')==t.page_id))
trace=[]
def observe(stage):
    s=d._state(p)
    selection=p._evaluate("(()=>{const s=getSelection();return {anchor:s.anchorNode?.nodeName,offset:s.anchorOffset,focus:document.hasFocus(),collapsed:s.isCollapsed}})()")
    trace.append({'stage':stage,'state':s,'selection':selection})
try:
    s=d._state(p)
    assert ' '.join(s['text'].split())=='发布助手功能验证，请勿发布 #生活记录 #日常' and s['topics']==['#日常']
    d._focus_editor_end(p)
    for key,code,vk,mods in [('a','KeyA',65,2),('Backspace','Backspace',8,0)]:
        for kind in ('keyDown','keyUp'):p._call('Input.dispatchKeyEvent',{'type':kind,'key':key,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mods})
    time.sleep(.5);assert d._state(p)['text']==''
    d._focus_editor_end(p);d._insert(p,'发布助手功能验证，请勿发布');observe('description')
    for topic in ('生活记录','日常'):
        d._verify_target(t);d._focus_editor_end(p);observe(topic+' focus')
        d._insert(p,' #'+topic);observe(topic+' inserted')
        deadline=time.monotonic()+12
        while d._topic_candidates(p,topic)!=1:
            assert time.monotonic()<deadline;time.sleep(.25)
        d._verify_target(t);assert d._topic_candidates(p,topic,click=True)==1
        observe(topic+' clicked')
        for i in range(5):time.sleep(.3);observe(topic+' settled '+str(i))
finally:
    Path('build/live-douyin-validation/topic_trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(trace,ensure_ascii=False));p.close()
