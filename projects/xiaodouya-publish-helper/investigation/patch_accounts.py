import marshal, types
from pathlib import Path

base = Path(__file__).parent
code = marshal.loads((base / 'recovered/xcl_publish.integrations.native_account_navigation.marshal').read_bytes())
replacement = compile((base / 'account_replacement.py').read_text(encoding='utf-8'), 'xcl_publish/integrations/native_account_navigation.py', 'exec')
function = next(c for c in replacement.co_consts if isinstance(c, types.CodeType) and c.co_name == 'list_logged_accounts')
matches = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == function.co_name]
assert len(matches) == 1
code = code.replace(co_consts=tuple(function if c is matches[0] else c for c in code.co_consts))

# Preserve account extraction, name/ID ambiguity checks and target switching.
# Narrowly repair the scanner's JS state machine and clean up its observer.
scan = next(c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == '_scan_account_inventory')
def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)
constants=[]
for value in scan.co_consts:
    if isinstance(value, str) and 'processed:new WeakSet()' in value:
        value=replace_once(value, 'if(node.scrollHeight<=node.clientHeight+4)continue;', '// Keep dormant overflow containers: expansion may create overflow later.')
        value=replace_once(value, 'processed:new WeakSet(),processedKeys:new Set()};', '''processed:new WeakSet(),processedKeys:new Set(),pending:new Set(),
        changedAt:performance.now(),lastExpansion:0};
      const state=window.__xclAccountScan;
      state.observer=new MutationObserver(()=>{state.changedAt=performance.now();});
      state.observer.observe(root,{subtree:true,childList:true,characterData:true,attributes:true});''')
    elif isinstance(value, str) and 'const inScanViewport=' in value:
        value=replace_once(value,'if(!state||!state.root)return null;', 'if(!state||!state.root||!state.root.isConnected||!visible(state.root))return null;')
        value=replace_once(value,'item.switcher.click();expanded++;','''state.pending.add(item.switcher.closest('.ant-tree-treenode,[role="treeitem"]')||item.switcher.parentElement);
                item.switcher.click();expanded++;state.lastExpansion=performance.now();''')
    elif isinstance(value, str) and 'const s=state.scroller;' in value:
        value=replace_once(value,'const s=state.scroller;', '''const s=state.scroller;
              for(const group of state.pending){
                if(!group.isConnected)return null;
                if(!group.classList.contains('ant-tree-treenode-switcher-close')&&group.getAttribute('aria-expanded')!=='false')state.pending.delete(group);
              }
              const loadingSelector='[aria-busy="true"],.ant-spin-spinning,.ant-tree-switcher-loading';
              const loading=(state.root.matches(loadingSelector)?1:0)+Array.from(state.root.querySelectorAll(loadingSelector)).filter(visible).length;
              const settling=performance.now()-state.changedAt<800||performance.now()-state.lastExpansion<800;
              if(state.pending.size||loading||settling)return {rows,duplicateNames,
                top:s?s.scrollTop:0,max:s?Math.max(0,s.scrollHeight-s.clientHeight):0,
                done:false,expanded:1,waiting:true,pendingCount:state.pending.size,loadingCount:loading};''')
    elif isinstance(value, str) and 'delete window.__xclAccountScan' in value:
        value=replace_once(value,'if(state?.scroller)', 'state?.observer?.disconnect();\n          if(state?.scroller)')
    elif type(value) is int and value==200:
        # Waiting for actual loading must not consume the old 200-page cap.
        # The existing monotonic deadline remains the primary bound.
        value=1000
    constants.append(value)
scan=scan.replace(co_consts=tuple(constants))
probe=compile((base/'account_scan_probe.py').read_text(encoding='utf-8'),'xcl_publish/integrations/native_account_navigation.py','exec')
wrapper=next(c for c in probe.co_consts if isinstance(c,types.CodeType) and c.co_name=='_scan_account_inventory')
scan=wrapper.replace(co_consts=tuple(scan if isinstance(c,types.CodeType) and c.co_name=='original' else c for c in wrapper.co_consts))
code=code.replace(co_consts=tuple(scan if isinstance(c,types.CodeType) and c.co_name==scan.co_name else c for c in code.co_consts))
(base / 'recovered/native_account_navigation.fixed.marshal').write_bytes(marshal.dumps(code))
print('Patched scan loading/overflow completion; identity and switching unchanged')
