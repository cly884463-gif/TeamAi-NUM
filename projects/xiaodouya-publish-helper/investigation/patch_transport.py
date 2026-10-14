import marshal, types
from pathlib import Path
from transport_replacement import _call

ROOT = Path(__file__).parent / 'recovered'
CODES = ('cdp_connection_unusable', 'cdp_send_timeout', 'cdp_response_timeout',
         'cdp_disconnected', 'cdp_invalid_response', 'cdp_command_rejected')

def replace(code, qualified, replacement):
    count=0;values=[]
    for value in code.co_consts:
        if isinstance(value,types.CodeType):
            if value.co_qualname==qualified:
                assert value.co_argcount==replacement.co_argcount
                assert not value.co_freevars and not replacement.co_freevars
                value=replacement.replace(co_qualname=qualified,co_filename=value.co_filename)
                count+=1
            else:
                value,n=replace(value,qualified,replacement);count+=n
        values.append(value)
    return code.replace(co_consts=tuple(values)),count

def extend_codes(code):
    values=[];count=0
    for value in code.co_consts:
        if isinstance(value,types.CodeType): value,n=extend_codes(value);count+=n
        elif isinstance(value,tuple) and 'endpoint_unavailable' in value and 'socket_timeout' in value:
            value=value+CODES;count+=1
        values.append(value)
    return code.replace(co_consts=tuple(values)),count

if __name__=='__main__':
    source=marshal.loads((ROOT/'xcl_publish.integrations.xiaodouya.marshal').read_bytes())
    fixed,count=replace(source,'CdpDraftPage._call',_call.__code__)
    assert count==1
    (ROOT/'xiaodouya.fixed.marshal').write_bytes(marshal.dumps(fixed))
    source=marshal.loads((ROOT/'xcl_publish.integrations.diagnostics.marshal').read_bytes())
    fixed,count=extend_codes(source);assert count==1
    (ROOT/'diagnostics.fixed.marshal').write_bytes(marshal.dumps(fixed))
    print('Replaced exactly CdpDraftPage._call; extended diagnostics cause allowlist')
