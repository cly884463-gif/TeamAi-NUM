"""Disassemble recovered code without importing or executing it (Python 3.11)."""
import dis, marshal, types
from pathlib import Path

root = Path(__file__).parent / 'recovered'
def walk(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from walk(value)

for path in root.glob('xcl_publish*.marshal'):
    code = marshal.loads(path.read_bytes())
    with path.with_suffix('.dis.txt').open('w', encoding='utf-8') as target:
        dis.dis(code, file=target)
    with path.with_suffix('.strings.txt').open('w', encoding='utf-8') as target:
        for item in walk(code):
            target.write('\nFUNCTION ' + item.co_qualname + '\n')
            for value in item.co_consts:
                if isinstance(value, str):
                    target.write(value + '\n')
print('Static disassembly and string extraction complete')
