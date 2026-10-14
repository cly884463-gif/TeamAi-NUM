import marshal,types
from pathlib import Path
root=Path(__file__).parent/'recovered'
code=marshal.loads((root/'xcl_publish.subtitle_scan.marshal').read_bytes())
original=next(c for c in code.co_consts if isinstance(c,types.CodeType) and c.co_name=='scan_opening_sentence')
compiled=compile(Path(__file__).with_name('scan_replacement.py').read_text(encoding='utf-8'),'xcl_publish/subtitle_scan.py','exec')
wrapper=next(c for c in compiled.co_consts if isinstance(c,types.CodeType))
wrapper=wrapper.replace(co_consts=tuple(original if isinstance(c,types.CodeType) and c.co_name=='original' else c for c in wrapper.co_consts))
seen=0;constants=[]
for c in code.co_consts:
    if isinstance(c,float) and c==12.0:c=2.0;seen+=1
    if isinstance(c,types.CodeType) and c.co_name=='scan_opening_sentence':c=wrapper
    constants.append(c)
assert seen==1
(root/'subtitle_scan.fixed.marshal').write_bytes(marshal.dumps(code.replace(co_consts=tuple(constants))))
print('Default scan is bounded to first two seconds; denser adjacent-frame evidence')
