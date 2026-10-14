import dis,marshal,types
from pathlib import Path
root=Path(__file__).parent/'recovered'
code=marshal.loads((root/'xcl_publish.domain.marshal').read_bytes())
source=compile(Path(__file__).with_name('copy_replacement.py').read_text(encoding='utf-8'),'xcl_publish/domain.py','exec')
replacements={c.co_name:c for c in source.co_consts if isinstance(c,types.CodeType)}
assert set(replacements)=={'opening_prefix','publish_text_defaults'}
values=list(code.co_consts)
instructions=list(dis.get_instructions(code))
indices=[]
for i,op in enumerate(instructions):
    if op.opname=='STORE_NAME' and op.argval=='OPENING_PREFIX_MAX_CHARS':
        previous=instructions[i-1];assert previous.opname=='LOAD_CONST' and previous.argval==20
        indices.append(previous.arg)
assert len(indices)==1
values[indices[0]]=40
seen=[]
for i,c in enumerate(values):
    if isinstance(c,types.CodeType) and c.co_name in replacements:
        seen.append(c.co_name);values[i]=replacements[c.co_name]
assert set(seen)==set(replacements)
(root/'domain.fixed.marshal').write_bytes(marshal.dumps(code.replace(co_consts=tuple(values))))
print('Patched source boundaries and 40-character validation, no silent slicing')
