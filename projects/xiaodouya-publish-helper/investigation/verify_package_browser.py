import hashlib,json,os,sys,time
from pathlib import Path
from urllib.request import urlopen
from package_modules import install
package=install()
from websocket import create_connection
from xcl_publish.integrations.xiaodouya import CdpDraftPage,XiaodouyaError
from xcl_publish.integrations import native_douyin as native

ROOT=Path(__file__).parent
endpoint=sys.argv[1]
targets=json.load(urlopen(endpoint))
target=next(t for t in targets if t.get('title')=='PublishHelper isolated verification')
def connect(timeout=5):return CdpDraftPage(create_connection(target['webSocketDebuggerUrl'],timeout=timeout,suppress_origin=True),timeout)
page=connect()
def verify():
    assert page._evaluate('window.fixtureNonce')=='isolated-publish-verification'
verify()
video=ROOT/'fixture.mp4'
obj=page._call('Runtime.evaluate',{'expression':'document.querySelector("input[type=file]")','returnByValue':False})['result']['objectId']
page._call('DOM.setFileInputFiles',{'objectId':obj,'files':[str(video.resolve())]})
deadline=time.monotonic()+10
while native._state(page)['ready']!=1:
    if time.monotonic()>deadline:raise AssertionError('blob preview not ready')
    time.sleep(.1)
actual=page._call('Runtime.evaluate',{'expression':'(async()=>{const f=document.querySelector("input[type=file]").files[0];return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",await f.arrayBuffer()))).map(x=>x.toString(16).padStart(2,"0")).join("")})()','awaitPromise':True,'returnByValue':True})['result']['value']
assert actual==hashlib.sha256(video.read_bytes()).hexdigest()
try:
    result=native.fill_description(page,'厨房翻新测试文案',['厨房翻新','本地装修'],verify)
except Exception:
    print('Fixture diagnostics:',page._evaluate('({text:document.querySelector("#editor").innerText,candidates:document.querySelector("#candidates").innerHTML})'))
    print('Candidate count:',native._topic_candidates(page,'厨房翻新'))
    raise
assert result['text']=='厨房翻新测试文案 #厨房翻新 #本地装修',result
assert result['topics']==['#厨房翻新','#本地装修'],result
assert result['title']==''
assert page._evaluate('window.inputCount')==1
try:native.fill_description(page,'不应覆盖',[],verify)
except XiaodouyaError as e:assert e.code=='existing_content'
else:raise AssertionError('Existing content overwritten')
assert native._state(page)['text']==result['text']
page.close()
# Real browser sends a late response; failed connection must not replay a command.
slow=connect(.1)
try:
    slow._call('Runtime.evaluate',{'expression':'window.slowCalls=(window.slowCalls||0)+1;new Promise(r=>setTimeout(()=>r(true),700))','awaitPromise':True,'returnByValue':True})
except XiaodouyaError as e:
    assert e.code=='cdp_response_timeout';diagnostic=Path(e.diagnostic_path)
else:raise AssertionError('Expected timeout')
try:slow._call('Runtime.evaluate',{'expression':'window.slowCalls++'})
except XiaodouyaError as e:assert e.code=='cdp_connection_unusable'
else:raise AssertionError('Failed connection reused')
check=connect();assert check._evaluate('window.slowCalls')==1
check.socket.close()
try:check._call('Runtime.evaluate',{'expression':'1'})
except XiaodouyaError as e:assert e.code=='cdp_disconnected'
else:raise AssertionError('Expected real closed socket failure')
report={'package':package.name,'actual_components':['delivered PYZ modules','bundled websocket-client','Chrome CDP','file input and SHA256','blob video preview','contenteditable insertion and topic DOM readback'],
        'fixture_limitations':'Local synthetic HTML, not real Douyin Slate editor or Xiaodouya account navigation.',
        'description':result['text'],'topics':result['topics'],'upload_count':1,
        'existing_content_protected':True,'real_timeout_classified':True,'no_replay_after_timeout':True,'real_disconnect_classified':True,'live_platform_verified':False}
(ROOT/'package_browser_result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS delivered package: real CDP + local file + SHA256 + blob preview + text/topics + failures')
