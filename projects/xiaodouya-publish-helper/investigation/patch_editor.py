import marshal, types
from pathlib import Path
from patch_preview import patch, ROOT
base=marshal.loads((ROOT/'xcl_publish.integrations.native_douyin.marshal').read_bytes())
base,count=patch(base)
assert count==1
source=compile(Path(__file__).with_name('editor_replacement.py').read_text(encoding='utf-8'),'xcl_publish/integrations/native_douyin.py','exec')
replacements={c.co_name:c for c in source.co_consts if isinstance(c,types.CodeType)}
assert set(replacements)=={'_insert','_focus_editor_end','fill_description','_ensure_empty','prepare_active'}
original_prepare=next(c for c in base.co_consts if isinstance(c,types.CodeType) and c.co_name=='prepare_active')
wrapper=replacements['prepare_active']
assert sum(isinstance(c,types.CodeType) and c.co_name=='original' for c in wrapper.co_consts)==1
replacements['prepare_active']=wrapper.replace(co_consts=tuple(original_prepare if isinstance(c,types.CodeType) and c.co_name=='original' else c for c in wrapper.co_consts))
seen=[]
wheel_changes=0
values=[]
for c in base.co_consts:
    if isinstance(c,types.CodeType) and c.co_name in replacements:
        seen.append(c.co_name);c=replacements[c.co_name]
    elif isinstance(c,types.CodeType) and c.co_name=='_select_schedule_picker':
        consts=[]
        for v in c.co_consts:
            if isinstance(v,str) and "items[0].scrollIntoView({block:'center'});" in v:
                assert v.count("items[0].scrollIntoView({block:'center'});")==1
                v=v.replace("items[0].scrollIntoView({block:'center'});",'')
                wheel_changes+=1
            consts.append(v)
        c=c.replace(co_consts=tuple(consts))
    values.append(c)
assert set(seen)==set(replacements)
assert wheel_changes==1
(ROOT/'native_douyin.fixed.marshal').write_bytes(marshal.dumps(base.replace(co_consts=tuple(values))))
print('Patched preview, two native editor functions and removed competing schedule scroll')
