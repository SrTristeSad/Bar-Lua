import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import analisar_colisores as M

class ColliderAuditTests(unittest.TestCase):
    def test_static_report(self):
        report=json.loads((ROOT/'reports/native_colliders.json').read_text())
        self.assertEqual(report['phase'],16)
        self.assertEqual(report['version'],'1.0.1811')
        self.assertEqual(len(report['functions']),2)
        self.assertEqual(sum(x['instructions'] for x in report['functions']),297)
        self.assertEqual([x['size_bytes'] for x in report['functions']],[204,984])
        self.assertEqual(report['constants']['body_position_divisor'],100.0)
        self.assertEqual(len(report['functions'][0]['checks']),6)
        self.assertGreaterEqual(len(report['functions'][1]['checks']),12)
        self.assertEqual(report['library_sha256'],next(x['sha256'] for x in json.loads((ROOT/'reports/native_arm64.json').read_text())['libraries'] if x['name']=='libcocos2dcpp.so'))
    def test_report_generated_from_original_library(self):
        tools=['llvm-objdump','readelf','c++filt']
        if any(shutil.which(x) is None for x in tools): self.skipTest('Ferramenta ARM64 ausente')
        r=M.audit(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',ROOT/'reports/native_arm64.json')
        self.assertEqual(r,json.loads((ROOT/'reports/native_colliders.json').read_text()))
        self.assertEqual(M.export_lua(r),(ROOT/'reports/native_colliders.lua').read_text())
    def test_rejects_foreign_binary(self):
        with tempfile.TemporaryDirectory() as d:
            altered=Path(d)/'lib.so'
            b=bytearray((ROOT/'lib/arm64-v8a/libcocos2dcpp.so').read_bytes())
            b[2000]^=1
            altered.write_bytes(b)
            with self.assertRaisesRegex(ValueError,'Hash divergente'):
                M.audit(altered,ROOT/'reports/native_arm64.json')
    def test_elf_va_bounds(self):
        with self.assertRaises(ValueError): M.elf_va_float(b'anything',0)
        with self.assertRaises(ValueError): M.elf_va_float((ROOT/'lib/arm64-v8a/libcocos2dcpp.so').read_bytes(),0xffffffffffff)
    def test_lua_panel(self):
        if not shutil.which('luatex'): self.skipTest('LuaTeX indisponível')
        p=subprocess.run(['luatex','--luaonly','tests/test_collider_view.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        self.assertIn('collider view OK',p.stdout)
    def test_lua_syntax(self):
        if not shutil.which('luatex'): self.skipTest('LuaTeX indisponível')
        p=subprocess.run(['luatex','--luaonly','tests/test_f16_syntax.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        self.assertIn('F16 syntax OK',p.stdout)
