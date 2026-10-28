"""F37: garantia de que novas regras e relatórios vêm do ELF original."""
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
from analisar_comparacoes import audit,as_lua,raw32,read_f32

class CompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths=(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',
                   ROOT/'reports/native_arm64.json',ROOT/'reports/concrete_conditions.json',
                   ROOT/'assets_original/configdata')

    def test_real_elf_checks(self):
        r=audit(*self.paths)
        self.assertEqual(r['phase'],37)
        self.assertEqual(len(r['functions']),8)
        self.assertEqual(r['verified_instructions'],336)
        self.assertEqual(r['checkpoints'],52)
        self.assertEqual(r['jump_tables'],4)
        self.assertEqual(r['ratio'],100.0)
        self.assertAlmostEqual(r['compare_epsilon'],0.0001,places=7)
        self.assertEqual(r['config_tables']['conditionskillentitytype']['records'],4)
        self.assertEqual(r['config_tables']['conditionvaluecompare']['records'],1406)
        self.assertEqual([x['mode'] for x in r['config_tables']['conditionskillentitytype']['cases']],[1,3,4,3])

    def test_report_is_deterministic(self):
        report=json.loads((ROOT/'reports/compare_conditions.json').read_text('utf8'))
        self.assertEqual(report,audit(*self.paths))
        self.assertEqual(as_lua(report),(ROOT/'reports/compare_conditions.lua').read_text('utf8'))
        self.assertIn('Nao existe combate real',report['limits'][2])

    def test_elf_hash_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/'wrong.so';fake.write_bytes(b'nao e elf')
            with self.assertRaisesRegex(ValueError,'ELF original divergente'):
                audit(fake,*self.paths[1:])

    def test_old_report_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/'bad.json';fake.write_text('{"phase":35}')
            with self.assertRaisesRegex(ValueError,'F36'):
                audit(self.paths[0],self.paths[1],fake,self.paths[3])

    def test_tables_hash_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            for stem in ('conditionskillentitytype','conditionvaluecompare'):
                src=self.paths[3]/('config.skill.'+stem+'.txt')
                (folder/src.name).write_bytes(src.read_bytes())
            target=folder/'config.skill.conditionskillentitytype.txt'
            target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'tabela original divergente'):
                audit(*self.paths[:3],folder)

    def test_jump_table_and_constants(self):
        raw=self.paths[0].read_bytes()
        self.assertEqual(0xe44d50+raw32(raw,0xe44d50),0xe44cbc)
        self.assertEqual(0xe44f2c+raw32(raw,0xe44f2c),0xe44f0c)
        self.assertEqual(read_f32(raw,0x1e98098),100.0)

    def test_lua_model(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex indisponivel')
        run=subprocess.run([exe,'--luaonly','tests/test_compare_conditions.lua'],cwd=ROOT,
                           capture_output=True,text=True,timeout=25)
        self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
        self.assertIn('F37 COMPARE CONDITIONS LUA OK',run.stdout)

    def test_ui_keeps_previous_modes(self):
        main=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('setMode(27)',main)
        self.assertIn('compareConditionsView.draw(compareConditionsReport',main)
        self.assertIn('lists[27][1]',main)
        self.assertIn('setMode(14)',main)
        self.assertIn('concreteConditionsView.draw(concreteConditionsReport',main)
        self.assertEqual(main.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),27)

if __name__=='__main__':unittest.main()
