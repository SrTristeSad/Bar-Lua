from __future__ import annotations
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_escopo_setor import audit,parse_sectors,SECTOR_SHA,as_lua

class SectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        cls.manifest=ROOT/'reports/native_arm64.json'
        cls.sector=ROOT/'assets_original/configdata/config.skill.selectsector.txt'
        cls.combat=ROOT/'reports/hero_combat_fields.json'
    def test_audit_original(self):
        result=audit(self.library,self.manifest,self.sector,self.combat)
        self.assertEqual(result['verified_instructions'],615)
        self.assertEqual(result['sector_records'],84)
        self.assertEqual(result['scope3_count'],18)
        self.assertEqual(result['query_aabb_divisor'],100.0)
        self.assertEqual(len(result['verified_functions']),6)
    def test_report_consistency(self):
        expected=json.loads((ROOT/'reports/sector_scope.json').read_text('utf8'))
        self.assertEqual(expected['sector_records'],84)
        self.assertEqual(expected['scope3_count'],18)
        self.assertEqual(expected['samples'][0]['id'],10052)
        self.assertIn('return {phase=33',as_lua(expected))
    def test_reject_invalid_library(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'lib.so';p.write_bytes(b'ELF falso')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(p,self.manifest,self.sector,self.combat)
    def test_reject_invalid_table(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.txt';p.write_text('10052 1 X 1 1 1',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(self.library,self.manifest,p,self.combat)
    def test_static_payload_checks(self):
        sample=b'10052 1 A 1 1 0 0 0 120 @ 3 100 - @ x'
        rows,counts,scoped=parse_sectors(sample)
        self.assertEqual(len(rows),1)
        self.assertEqual(counts[3],1)
        self.assertTrue(scoped[0]['operation_absent'])
    def test_lua(self):
        lua=shutil.which('luatex')
        if not lua:self.skipTest('LuaTeX indisponivel')
        r=subprocess.run([lua,'--luaonly','tests/test_sector_scope.lua'],cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('F33 SECTOR SCOPE LUA OK',r.stdout)
    def test_main_integration(self):
        main=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('"Escopo de setor (AABB)"',main)
        self.assertIn('setMode(23)',main)
        self.assertIn('sectorScopeView.draw(sectorScopeReport',main)
        self.assertIn('sectorScopeView.keypressed',main)
        lists_line=re.search(r'^local lists = (.+)$',main,re.M)
        self.assertIsNotNone(lists_line)
        self.assertGreaterEqual(lists_line.group(1).count('{}'),24)

if __name__=='__main__':unittest.main()
