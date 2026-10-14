"""Authorized single live test of the user's imported draft. Never publishes/replays."""
import json,time
from pathlib import Path
from package_modules import install
package=install()
from xcl_publish.integrations import native,native_douyin as d
from xcl_publish.integrations.native_wechat import _targets,_open
from xcl_publish.integrations.base import PublishPayload,TargetPlatform
from xcl_publish.domain import file_sha256,topics_from_text
root=Path('build/live-douyin-validation')
journal=root/'actual_draft_r6.json'
assert not journal.exists(),'Prior attempt exists; inspect, do not replay'
draft=json.loads(Path('build/gui-r4-validation/drafts.json').read_text(encoding='utf-8'))['drafts'][0]
assert draft['date']=='2026-10-13' and draft['clock']=='17:10' and draft['confirmed']
assert file_sha256(draft['path'])==draft['source_sha256']
t=d.discover_active();assert t.account=='早睡';d._verify_target(t)
p=_open(next(x for x in _targets() if x.get('id')==t.page_id))
try:
    d._ensure_empty(d._state(p))
    # Test navigation from a non-upload account page only after proving no active work.
    p._evaluate("location.assign('https://creator.douyin.com/creator-micro/home')")
finally:p.close()
time.sleep(1)
target=native.prepare_active(TargetPlatform.DOUYIN,'早睡')
payload=PublishPayload(source_path=draft['path'],description=draft['description'],topics=tuple(topics_from_text(draft['topics'])),city=draft['city'],scheduled_at=draft['date']+'T'+draft['clock']+':00+08:00',contains_ai=draft['ai']=='含AI内容',draft_id=draft['id'],draft_revision=draft['revision'],source_sha256=draft['source_sha256'],short_title='')
report={'package':package.name,'status':'attempt_started','published':False,'auto_navigation_completed':True}
journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    receipt=native.fill_native(payload,target)
    report.update(status='filled_pending_manual_review',receipt=receipt)
except Exception as e:
    report.update(status='failed_or_unknown_do_not_retry',error_type=type(e).__name__,code=getattr(e,'code',None),stage=getattr(e,'stage',None),cause_code=getattr(e,'cause_code',None),message=str(e))
finally:
    journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
