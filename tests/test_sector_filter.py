from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_filtro_setor import audit,as_lua

class SectorFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        cls.manifest=ROOT/'reports/native_arm64.json'
        cls.previous=ROOT/'reports/sector_scope.json'
    def test_original_elf(self):
        r=audit(self.library,self.manifest,self.previous)
        self.assertEqual(r['verified_instructions'],396)
        self.assertEqual(r['checkpoints'],45)
        self.assertEqual(len(r['verified_functions']),4)
        self.assertEqual(r['callback']['entity_shape_type_offset'],'0x1a8')
        self.assertEqual(r['vtable_dimension_relocations']['0x24bdb18'],'_ZNK6Entity17getPhysicalRadiusEv')
        self.assertTrue(0.000099<r['angular_epsilon']<0.000101)
        self.assertEqual(len(r['post_filter']['calls']),5)
    def test_reports_match(self):
        saved=json.loads((ROOT/'reports/sector_filter.json').read_text('utf8'))
        self.assertEqual(saved['phase'],34)
        self.assertFalse('damage' in saved)
        self.assertEqual((ROOT/'reports/sector_filter.lua').read_text('utf8'),as_lua(saved))
        self.assertIn('CSelectTargetSector::Filter',saved['confirmed_order'][2])
    def test_reject_other_elf(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'invalid.so';p.write_bytes(b'not an ELF')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(p,self.manifest,self.previous)
    def test_reject_wrong_prior(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'prior.json';p.write_text('{"phase":12}')
            with self.assertRaisesRegex(ValueError,'catalogo'):
                audit(self.library,self.manifest,p)
    def test_lua_model(self):
        runtime=shutil.which('luatex')
        if not runtime:self.skipTest('luatex indisponivel')
        run=subprocess.run([runtime,'--luaonly','tests/test_sector_filter.lua'],cwd=ROOT,text=True,capture_output=True,timeout=25)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn('F34 SECTOR FILTER LUA OK',run.stdout)
    def test_ui_integrated(self):
        main=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('"Filtro de alvos (ARM64)"',main)
        self.assertIn('sectorFilterView.draw(sectorFilterReport',main)
        self.assertIn('setMode(24)',main)
        self.assertIn('sectorFilterView.keypressed',main)
        self.assertIn('lists[24][1]',main)
        self.assertGreaterEqual(main.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),24)

if __name__=='__main__':unittest.main()
