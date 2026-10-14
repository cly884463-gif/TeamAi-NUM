"""Real matching operator media/OCR with injected recorded need_more decision, no API keys."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
from package_modules import install
version=sys.argv[1]
package=install(version,runtime_root=next(Path('build/candidate-r6').glob('*/_internal')))
from xcl_publish import subtitle_scan as s,domain as d
records=json.loads(Path('E:/xwechat_files/wxid_v9ec9lecbv1w22_2fec/msg/file/2026-10/drafts.json').read_text(encoding='utf-8'))['drafts']
out=Path('build/operator-repro');out.mkdir(exist_ok=True)
rows=[]
for old in records[:3]:
    p=Path('F:/共享本公司/视频发布/张艺/遵义陶姐  隔日更')/old['path'].split('\\')[-1]
    assert d.file_sha256(str(p))==old['source_sha256']
    row={'file':p.name,'fingerprint_matches':True,'ocr':'real packaged local engine','boundary_decision':'injected need_more from recorded failure, not live model call'}
    try:
        text=s.scan_opening_sentence(str(p),out,boundary_selector=lambda _:SimpleNamespace(status='need_more',text=''))
        draft=d.Draft(path=str(p),stamp=d.file_stamp(str(p)))
        draft.finish_preprocess(text,old['media_summary'],old['source_sha256'])
        row.update(text=text,status=draft.preprocess_status,confirmed=draft.confirmed)
        assert version!='r9' and text and not draft.confirmed
    except ValueError as e:
        row.update(error=str(e));assert version=='r9'
    rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
(out/(version+'_result.json')).write_text(json.dumps({'package':package.name,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
