"""Load verification modules from the actual delivered ZIP, not working source."""
import importlib.abc, importlib.util, marshal, struct, sys, zipfile, zlib
from pathlib import Path

def install(version="r13", runtime_root=None):
    package=next((Path(__file__).parent.parent/'deliverables').glob('*'+version+'*.zip'))
    with zipfile.ZipFile(package) as archive:
        data=archive.read(next(n for n in archive.namelist() if n.endswith('/新材联发布助手.exe')))
    cookie=data.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
    _,size,offset,toc_size,version,_=struct.unpack('!8sIIII64s',data[cookie:cookie+88])
    assert version==311 and sys.version_info[:2]==(3,11)
    start=cookie+88-size;toc=data[start+offset:start+offset+toc_size]
    while toc:
        length,pos,packed,_,compressed,kind=struct.unpack('!iIIIBc',toc[:18])
        if kind==b'z':
            blob=data[start+pos:start+pos+packed]
            if compressed:blob=zlib.decompress(blob)
            break
        toc=toc[length:]
    index=dict(marshal.loads(blob[struct.unpack('!I',blob[8:12])[0]:]))
    if runtime_root:
        runtime_root=Path(runtime_root).resolve()
        sys.path.insert(0,str(runtime_root))
    class Finder(importlib.abc.MetaPathFinder,importlib.abc.Loader):
        def find_spec(self,name,path=None,target=None):
            if name in index and (name=='xcl_publish' or name.startswith('xcl_publish.') or name=='websocket' or name.startswith('websocket.') or runtime_root and name.split('.')[0] not in sys.stdlib_module_names):
                return importlib.util.spec_from_loader(name,self,is_package=index[name][0]==1)
        def create_module(self,spec):return None
        def exec_module(self,module):
            _,pos,length=index[module.__name__]
            if runtime_root:
                location=runtime_root.joinpath(*module.__name__.split('.'))
                module.__file__=str(location/'__init__.py' if index[module.__name__][0]==1 else location.with_suffix('.py'))
                if index[module.__name__][0]==1:module.__path__=[str(location)]
            exec(marshal.loads(zlib.decompress(blob[pos:pos+length])),module.__dict__)
        def get_data(self,path):return Path(path).read_bytes()
        def get_resource_reader(self,name):
            if runtime_root:
                from importlib.resources.readers import FileReader
                from types import SimpleNamespace
                return FileReader(SimpleNamespace(path=str(runtime_root.joinpath(*name.split('.'),'__init__.py'))))
    sys.meta_path.insert(0,Finder())
    return package
