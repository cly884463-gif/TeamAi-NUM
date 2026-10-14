"""Read-only inspection of the supplied executable; never executes package code."""
import json, marshal, struct, zipfile, zlib
from pathlib import Path

package = Path('E:/xwechat_files/wxid_v9ec9lecbv1w22_2fec/msg/file/2026-10/新材联发布助手_v0.5.44_视频号时间与抖音标题修复验证版.zip')
out = Path(__file__).parent / 'recovered'
out.mkdir(exist_ok=True)
with zipfile.ZipFile(package) as archive:
    exe_name = next(n for n in archive.namelist() if n.endswith('/新材联发布助手.exe'))
    data = archive.read(exe_name)
cookie = data.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
if cookie < 0:
    raise ValueError('No PyInstaller cookie')
_, size, offset, toc_size, version, library = struct.unpack('!8sIIII64s', data[cookie:cookie+88])
start = cookie + 88 - size
toc = data[start+offset:start+offset+toc_size]
entries = []
while toc:
    length, pos, packed, unpacked, compressed, kind = struct.unpack('!iIIIBc', toc[:18])
    name = toc[18:length].rstrip(b'\0').decode()
    entries.append({'name': name, 'type': kind.decode(), 'size': unpacked})
    blob = data[start+pos:start+pos+packed]
    if compressed:
        blob = zlib.decompress(blob)
    if kind == b's':
        (out / (name.replace('/', '_') + '.marshal')).write_bytes(blob)
    if kind == b'z':
        pyz_offset = struct.unpack('!I', blob[8:12])[0]
        modules = dict(marshal.loads(blob[pyz_offset:]))
        selected = {k: v for k, v in modules.items() if any(s in k.lower() for s in ['xincai', 'publish', 'douya']) or k == 'websocket' or k.startswith('websocket.')}
        print('Candidate modules:', json.dumps(selected, ensure_ascii=False))
        (out / 'module_names.json').write_text(json.dumps(list(modules), ensure_ascii=False, indent=2), encoding='utf-8')
        for name, (typ, pos, size) in selected.items():
            (out / (name + '.marshal')).write_bytes(zlib.decompress(blob[pos:pos+size]))
    toc = toc[length:]
print('Python version:', version)
print(json.dumps(entries, ensure_ascii=False, indent=2))
