"""Rebuild the original PyInstaller archive, changing only eight known modules."""
import hashlib, json, marshal, struct, types, zipfile, zlib
from pathlib import Path
package = Path('E:/xwechat_files/wxid_v9ec9lecbv1w22_2fec/msg/file/2026-10/新材联发布助手_v0.5.44_视频号时间与抖音标题修复验证版.zip')

BASE = Path(__file__).parent
OUT = BASE.parent / 'deliverables'
OUT.mkdir(exist_ok=True)
LABEL = '新材联发布助手_v0.5.44-r13_账号加载验收修正版'

def version_code(code):
    values=[]
    for value in code.co_consts:
        if isinstance(value,types.CodeType): value=version_code(value)
        elif isinstance(value,str):
            value=value.replace('v0.5.44','v0.5.44-r13（候选验证）')
            value=value.replace('开头字幕 · 自动只保留前20字，后续内容不进入发布文案','开头字幕 · 默认识别前2秒；未完整时定位句尾，点击“首句到此结束”')
            value=value.replace('开头字幕已生成并只保留前20字。请播放原视频核对文字是否正确。','开头前2秒字幕候选已生成，请核对；句子未结束时定位句尾，点击“首句到此结束，重新识别”。')
            value=value.replace('描述使用开头20字以内短句','描述使用核对后的开场表达')
        values.append(value)
    return code.replace(co_consts=tuple(values))

def read_pyz(blob):
    offset=struct.unpack('!I',blob[8:12])[0]
    toc=dict(marshal.loads(blob[offset:]))
    return {name:(typ,zlib.decompress(blob[pos:pos+size])) for name,(typ,pos,size) in toc.items()}

def rebuild_pyz(blob):
    original=read_pyz(blob)
    changes={
        'xcl_publish.integrations.native_account_navigation':(BASE/'recovered/native_account_navigation.fixed.marshal').read_bytes(),
        'xcl_publish.subtitle_scan':(BASE/'recovered/subtitle_scan.fixed.marshal').read_bytes(),
        'xcl_publish.domain':(BASE/'recovered/domain.fixed.marshal').read_bytes(),
        'xcl_publish.dates':(BASE/'recovered/dates.fixed.marshal').read_bytes(),
        'xcl_publish.integrations.native_douyin':(BASE/'recovered/native_douyin.fixed.marshal').read_bytes(),
        'xcl_publish.integrations.xiaodouya':(BASE/'recovered/xiaodouya.fixed.marshal').read_bytes(),
        'xcl_publish.integrations.diagnostics':(BASE/'recovered/diagnostics.fixed.marshal').read_bytes(),
        'xcl_publish.ui':marshal.dumps(version_code(marshal.loads(original['xcl_publish.ui'][1])))
    }
    data=bytearray(blob[:12]); toc=[]
    for name,(typ,content) in original.items():
        packed=zlib.compress(changes.get(name,content),6)
        toc.append((name,(typ,len(data),len(packed))));data.extend(packed)
    offset=len(data);data.extend(marshal.dumps(toc));data[8:12]=struct.pack('!I',offset)
    result=bytes(data)
    rebuilt=read_pyz(result)
    changed=[n for n in original if original[n]!=rebuilt[n]]
    assert set(changed)==set(changes),changed
    return result,changed

def rebuild_exe(data):
    cookie=data.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
    magic,size,offset,toc_size,version,library=struct.unpack('!8sIIII64s',data[cookie:cookie+88])
    assert version==311 and cookie+88==len(data)
    start=cookie+88-size;toc=data[start+offset:start+offset+toc_size]
    payload=bytearray(); table=bytearray();changes=[]
    while toc:
        length,pos,packed,unpacked,compressed,kind=struct.unpack('!iIIIBc',toc[:18])
        name=toc[18:length]
        content=data[start+pos:start+pos+packed]
        if kind==b'z':
            raw=zlib.decompress(content) if compressed else content
            raw,changes=rebuild_pyz(raw);unpacked=len(raw)
            content=zlib.compress(raw) if compressed else raw
        table.extend(struct.pack('!iIIIBc',length,len(payload),len(content),unpacked,compressed,kind)+name)
        payload.extend(content);toc=toc[length:]
    cookie_new=struct.pack('!8sIIII64s',magic,len(payload)+len(table)+88,len(payload),len(table),version,library)
    return data[:start]+payload+table+cookie_new,changes

with zipfile.ZipFile(package) as source:
    name=next(n for n in source.namelist() if n.endswith('/新材联发布助手.exe'))
    original=source.read(name);fixed,changed=rebuild_exe(original)
    result=OUT/(LABEL+'.zip')
    with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED) as dest:
        for item in source.infolist():
            relative=item.filename.split('/',1)[1]
            dest.writestr(LABEL+'/'+relative,fixed if item.filename==name else source.read(item))
        dest.writestr(LABEL+'/本次候选验证说明.txt',
            '进入上传页后等待上传控件就绪再交给上传流程；区分抖音保留未发布视频、当前已有内容、未进入上传页和上传控件未就绪，避免统一误报不是空白页；不自动丢弃未完成内容。\n'
            '文案不再机械截取前20字；优先开头招呼句、明确句末或重复起句，无法确定时保留候选供核对，超过40字须人工精简。不会自动改写已有人工文案。\n'
            '默认取视频前2秒字幕（原为12秒），每0.25秒采样并用相邻帧共识去重；不自动扩大范围。旧任务须点击重新读取此视频，不能仅重置旧文字。句子超过2秒可定位句尾后点击首句到此结束。\n'
            '修复前2秒识别成功但智能断句返回need_more时任务失败的问题；保留已识别候选等待人工核对，不自动延长，不自动确认。模型不确定、改写和真实OCR失败仍停止。\n'
            '修复分组仍在加载就结束扫描，以及展开后列表变长但没有识别滚动容器的问题。同时检查账号列表本身和子节点的加载标记；等待展开与可见加载状态结束、DOM稳定后继续扫描；持续加载超时停止，保留两轮完整结果一致检查。新增扫描等待次数、滚动位置和加载计数诊断。运营现场尚未验收。\n'
            '账号读取改为每轮独立60秒预算，最多三轮完整扫描，连续两轮一致才返回。扫描中超时或断线立即停止，不自动重试，不返回部分账号。失败自动保存账号读取诊断，只含阶段、数量与耗时。该修复针对已复现的两轮共用预算不足，运营现场原因尚未确认。\n'
            '版本：v0.5.44-r13 候选验证版，非正式交付。\n'
            '修改抖音预览判定：增加同源 blob 视频兼容，保留原有文件指纹、账号核对、唯一预览和文案读回要求。\n'
            '修正把断线和解析失败统一误报为超时的问题；连接异常自动保存脱敏 JSON，异常连接不再继续发送指令。不会自动重试上传。\n'
            '修复抖音实际编辑器中 execCommand 输入重复的问题；先核对内嵌页面焦点，再使用原生 Input.insertText，保留完整读回和失败停止。\n'
            '2026-10-12 本机真实小豆芽抖音测试：测试视频上传，修复函数正确填写正文和两个话题；未点击最终发布。未验证视频号或运营电脑。\n'
            '历史运营截图的具体原因尚未证实；本机实际复现正文重复并修复。多账号与其他配置仍须验收。\n'
            '支持从视频所属文件夹读取发布日期；文件名/文件夹多日期或冲突时留空核对。话题逐个等待实际标签稳定生效，禁止把普通井号文字当成成功。\n'
            '同时去掉时间滚轮选择前的额外滚动，避免与控件内部动画竞争。保留时间精确读回；不自动发布。\n'
            '模拟测试、本地浏览器组件和本机抖音实测分别记录；运营电脑、多账号规模、视频号及 GUI 拖放/OCR 闭环仍未验收。\n'
            '同包其他说明是 v0.5.44 历史资料，其测试数字不能算本次验证。\n'
            '完整解压到新目录，先核对窗口版本，勿覆盖常用版；同一时间只开一个助手。\n'
            '先备份 %LOCALAPPDATA%\\Xincailian\\PublishHelper 中现有数据。\n'
            '现场用一条获授权的新素材核对：账号正确、文案预先非空、只上传一次、正文与话题完整、独立标题为空、最终人工确认。\n'
            '已有视频的页面不要重新上传。失败保留底部提示及 diagnostics 中 JSON，不重复提交。\n'
            '退出验证版后可回到原版；程序回退不能撤销平台上已经上传的内容。\n')
    with zipfile.ZipFile(result) as check:
        assert check.testzip() is None
        for item in source.infolist():
            if item.filename!=name:
                assert check.read(LABEL+'/'+item.filename.split('/',1)[1])==source.read(item)
    report={'baseline_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
            'candidate_sha256':hashlib.sha256(result.read_bytes()).hexdigest(),
            'changed_modules':changed,'other_original_zip_entries_byte_identical':True,
            'live_platform_verified':False,'package':str(result.resolve())}
    (OUT/'build_report_r13.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
