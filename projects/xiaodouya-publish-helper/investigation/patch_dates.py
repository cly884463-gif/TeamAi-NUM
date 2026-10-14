import marshal,types
from pathlib import Path
root=Path(__file__).parent/'recovered'
code=marshal.loads((root/'xcl_publish.dates.marshal').read_bytes())
compiled=compile(Path(__file__).with_name('date_replacement.py').read_text(encoding='utf-8'),'xcl_publish/dates.py','exec')
replacement=next(c for c in compiled.co_consts if isinstance(c,types.CodeType))
seen=0;consts=[]
for c in code.co_consts:
    if isinstance(c,types.CodeType) and c.co_name=='detect_date_from_filename':
        c=replacement;seen+=1
    consts.append(c)
assert seen==1
(root/'dates.fixed.marshal').write_bytes(marshal.dumps(code.replace(co_consts=tuple(consts))))
print('Patched direct-parent delivery date detection')
