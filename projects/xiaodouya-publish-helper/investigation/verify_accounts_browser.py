"""Actual delivered scanner against synthetic grouped HTML in real Chrome/CDP."""
import json,sys,time
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch
from package_modules import install
version=sys.argv[2] if len(sys.argv)>2 else 'r11'
install(version)
from websocket import create_connection
from xcl_publish.integrations.xiaodouya import CdpDraftPage
from xcl_publish.integrations import native_account_navigation as n

target=next(t for t in json.load(urlopen(sys.argv[1])) if t.get('title')=='Isolated account inventory verification')
page=CdpDraftPage(create_connection(target['webSocketDebuggerUrl'],timeout=10,suppress_origin=True),10)
class Context:
    def __enter__(self):return page
    def __exit__(self,*a):pass
results=[]
try:
    # Only target selection and filter dialog are fixtures. The actual scanner,
    # JS group expansion/scrolling/card extraction and duplicate checks execute.
    with patch.object(n,'_targets',return_value=[target]),patch.object(n,'_select_main_page',return_value=target),patch.object(n,'_open',return_value=Context()),patch.object(n,'_clear_search_filter'):
        platform=next(k for k,v in n.PLATFORM_LABELS.items() if v=='抖音')
        for groups,delay in ((8,2000),(5,0),(40,0),(80,0)):
            page._evaluate('setupAccounts('+str(groups)+',false,'+str(delay)+')')
            before=page._evaluate('document.querySelector("#scroll").scrollTop')
            begin=time.monotonic();accounts=n.list_logged_accounts(platform)
            expected={f'测试账号{i}-{j}' for i in range(groups) for j in range(2)}
            assert len(accounts)==len(expected) and set(accounts)==expected,(groups,len(accounts))
            assert page._evaluate('document.querySelector("#scroll").scrollTop')==before
            assert page._evaluate('typeof window.__xclAccountScan')=='undefined'
            results.append({'groups':groups,'delay_ms':delay,'accounts':len(accounts),'seconds':round(time.monotonic()-begin,2),'all_names_exact':True,'scroll_restored':True})
            print(results[-1],flush=True)
        page._evaluate('setupAccounts(5,true)')
        try:n.list_logged_accounts(platform)
        except n.XiaodouyaError as e:assert e.code=='target_account_ambiguous'
        else:raise AssertionError('duplicate names accepted')
    report={'version':version,'component':'real Chrome and delivered scanner; synthetic grouped DOM; filter/target selection mocked', 'cases':results,'duplicates_rejected':True,'operations_computer_verified':False}
    path=Path('build/account-browser-result-'+version+'.json');path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
finally:page.close()
