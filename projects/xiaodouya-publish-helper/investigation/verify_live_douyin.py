"""One authorized live upload through the delivered package; never clicks publish."""
import json,os,re,sys
from pathlib import Path
from package_modules import install
package=install()
from xcl_publish.integrations.base import PublishPayload,TargetPlatform
from xcl_publish.integrations import native,native_douyin
from xcl_publish.domain import file_sha256

root=Path(__file__).parent.parent/'build'/'live-douyin-validation'
root.mkdir(parents=True,exist_ok=True)
run_id=sys.argv[2] if len(sys.argv)>2 else 'initial'
if not re.fullmatch(r'[a-zA-Z0-9_-]+',run_id):raise SystemExit('Invalid run id')
journal=root/('live_upload_result_'+run_id+'.json')
if journal.exists():raise SystemExit('Prior live attempt exists. Inspect result before any further action; no automatic replay.')
expected_account=sys.argv[1]
target=native_douyin.discover_active()
if not native.account_matches(TargetPlatform.DOUYIN,expected_account,target.account):
    raise SystemExit('Current account does not match explicit test target')
source=Path(__file__).parent.parent/'build'/'live-test-do-not-publish.mp4'
payload=PublishPayload(source_path=str(source.resolve()),description='发布助手功能验证，请勿发布',topics=('生活记录','日常'),city='',scheduled_at='2026-10-13T17:05:00+08:00',contains_ai=False,draft_id='isolated-live-verification',draft_revision=1,source_sha256=file_sha256(str(source.resolve())),short_title='')
report={'package':package.name,'status':'attempt_started','published':False,'synthetic_video':True}
journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    result=native.fill_native(payload,target)
    report.update(status='filled_pending_manual_review',receipt=result)
except Exception as exc:
    report.update(status='failed_or_unknown_do_not_retry',error_type=type(exc).__name__,code=getattr(exc,'code',None),stage=getattr(exc,'stage',None),cause_code=getattr(exc,'cause_code',None),message=str(exc))
finally:
    journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
