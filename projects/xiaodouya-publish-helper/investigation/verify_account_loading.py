import json,sys,time,os
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch
from package_modules import install
version=sys.argv[2];install(version)
from websocket import create_connection
from xcl_publish.integrations.xiaodouya import CdpDraftPage
from xcl_publish.integrations import native_account_navigation as n
target=next(t for t in json.load(urlopen(sys.argv[1])) if t.get('title')=='Isolated account inventory verification')
page=CdpDraftPage(create_connection(target['webSocketDebuggerUrl'],timeout=5,suppress_origin=True),5)
class Context:
    def __enter__(self):return page
    def __exit__(self,*args):pass
report={'version':version,'synthetic_DOM':True,'cases':[]}
try:
 with patch.object(n,'_targets',return_value=[target]),patch.object(n,'_select_main_page',return_value=target),patch.object(n,'_open',return_value=Context()),patch.object(n,'_clear_search_filter'):
  platform=next(k for k,v in n.PLATFORM_LABELS.items() if v=='抖音')
  mode=sys.argv[3] if len(sys.argv)>3 else 'normal'
  page._evaluate('setupProgressive('+('true' if mode=='rootbusy' else 'false')+')');started=time.monotonic()
  try:result=n.list_logged_accounts(platform)
  except n.XiaodouyaError as error:
   if version!='r11':raise
   assert error.code=='account_list_unstable'
   directory=Path(os.environ['XCL_PUBLISH_DATA_DIR'])/'diagnostics'
   evidence=json.loads(max(directory.glob('账号读取诊断_*.json'),key=lambda p:p.stat().st_mtime_ns).read_text(encoding='utf-8'))
   counts=[r['account_count'] for r in evidence['rounds']]
   assert counts==[18,20,23],counts
   result=None
   report['cases'].append({'case':'18_then20_then23','round_counts':counts,'stopped':True,'failure':error.code})
  if version=='r11':
   # This demonstrates unsafe early completion, not the operator's exact DOM.
   if result is not None:
    assert len(result)<23,(len(result),'baseline did not reproduce')
    report['cases'].append({'case':'18_then20_then23','returned':len(result),'premature':True})
  else:
   assert set(result)=={f'递增账号{i}' for i in range(23)}, {'mode':mode,'returned':len(result),'expected':23}
   report['cases'].append({'case':'18_then20_then23','returned':23,'seconds':round(time.monotonic()-started,2)})
   page._evaluate('setupVirtual(80)');started=time.monotonic()
   result=n.list_logged_accounts(platform)
   assert len(result)==80 and set(result)=={f'虚拟账号{i}' for i in range(80)}
   assert page._evaluate('document.querySelector("#scroll").scrollTop')==150
   report['cases'].append({'case':'virtual80','returned':80,'seconds':round(time.monotonic()-started,2)})
   page._evaluate('document.querySelector("#scroll").onscroll=null;setupAccounts(5,false,60000)')
   try:n.list_logged_accounts(platform,timeout=3)
   except n.XiaodouyaError as e:assert e.code=='account_list_unstable'
   else:raise AssertionError('permanent loading accepted')
   assert page._evaluate('typeof window.__xclAccountScan')=='undefined'
   report['cases'].append({'case':'loading_timeout','stopped':True,'scan_state_removed':True})
   page._evaluate('document.querySelector("#dashboard-account-list").style.display="none"')
   try:n.list_logged_accounts(platform,timeout=3)
   except n.XiaodouyaError:pass
   else:raise AssertionError('hidden list accepted')
   report['cases'].append({'case':'hidden_root','stopped':True})
   if version=='r13' and mode=='normal':
    page._evaluate('document.querySelector("#dashboard-account-list").style="";setupAccounts(5)')
    expected={f'测试账号{i}-{j}' for i in range(5) for j in range(2)}
    for i in range(10):
     assert set(n.list_logged_accounts(platform))==expected
     assert page._evaluate('typeof window.__xclAccountScan')=='undefined'
    report['cases'].append({'case':'recover_then_repeat','cycles':10,'exact_accounts':10,'scan_state_removed':True})
    page._evaluate('document.querySelector("#dashboard-account-list").setAttribute("aria-busy","true")')
    try:n.list_logged_accounts(platform,timeout=2)
    except n.XiaodouyaError as e:assert e.code=='account_list_unstable'
    else:raise AssertionError('root loading timeout accepted')
    report['cases'].append({'case':'root_loading_timeout','stopped':True})
 print(json.dumps(report,ensure_ascii=False),flush=True)
 Path('build/account-loading-'+version+'-'+mode+'.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
finally:page.close()
