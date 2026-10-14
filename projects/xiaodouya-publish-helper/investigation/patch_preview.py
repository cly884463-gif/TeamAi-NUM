"""Python 3.11: narrowly patch one recovered JavaScript constant."""
import marshal, types
from pathlib import Path

ROOT = Path(__file__).parent / 'recovered'
OLD = "v.currentSrc.startsWith('https:')"
NEW = "(v.currentSrc.startsWith('https:')||(v.currentSrc.startsWith('blob:')&&new URL(v.currentSrc).origin===location.origin))"

def patch(code):
    changes = 0
    consts = []
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            value, count = patch(value)
            changes += count
        elif code.co_name == '_state' and isinstance(value, str) and OLD in value:
            assert value.count(OLD) == 1
            (ROOT / 'preview_original.js').write_text(value, encoding='utf-8')
            value = value.replace(OLD, NEW)
            (ROOT / 'preview_fixed.js').write_text(value, encoding='utf-8')
            changes += 1
        consts.append(value)
    return code.replace(co_consts=tuple(consts)), changes

if __name__ == '__main__':
    original = marshal.loads((ROOT / 'xcl_publish.integrations.native_douyin.marshal').read_bytes())
    fixed, count = patch(original)
    assert count == 1, count
    (ROOT / 'native_douyin.fixed.marshal').write_bytes(marshal.dumps(fixed))
    print('Patched exactly one _state JavaScript constant')
