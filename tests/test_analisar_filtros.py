import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import analisar_filtros as A

class FilterAuditTests(unittest.TestCase):
    def test_static_metadata(self):
        r=json.loads((ROOT/'reports/native_filters.json').read_text(encoding='utf-8'))
        self.assertEqual(r['phase'],17)
        self.assertEqual([f['instructions'] for f in r['functions']],[33,22,46,59])
        self.assertEqual(r['entity_setCollidable']['true'],{'categoryBits':1,'maskBits':3,'groupIndex':0})
        self.assertEqual(r['entity_setCollidable']['false'],{'categoryBits':0,'maskBits':1,'groupIndex':0})
    def test_report_reproducible(self):
        if any(not shutil.which(c) for c in ['readelf','c++filt','llvm-objdump']):
            self.skipTest('Ferramenta ARM64 ausente')
        r=A.audit(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',ROOT/'reports/native_arm64.json')
        expected=json.loads((ROOT/'reports/native_filters.json').read_text(encoding='utf-8'))
        self.assertEqual(r,expected)
        self.assertEqual(A.export_lua(r).strip(),(ROOT/'reports/native_filters.lua').read_text(encoding='utf-8').strip())
    def test_other_library_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            so=Path(tmp)/'wrong.so'
            data=bytearray((ROOT/'lib/arm64-v8a/libcocos2dcpp.so').read_bytes())
            data[4001]^=1
            so.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'SHA-256 divergente'):
                A.audit(so,ROOT/'reports/native_arm64.json')
    def test_lua_filter_view(self):
        if not shutil.which('luatex'):self.skipTest('LuaTeX indisponível')
        p=subprocess.run(['luatex','--luaonly','tests/test_contact_filter.lua'],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_lua_syntax(self):
        if not shutil.which('luatex'):self.skipTest('LuaTeX indisponível')
        p=subprocess.run(['luatex','--luaonly','tests/test_f17_syntax.lua'],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
