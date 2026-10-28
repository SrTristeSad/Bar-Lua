"""F36: confere predicados concretos no ELF original e isolados em Lua."""
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
from analisar_condicoes_concretas import audit,as_lua,raw32

class ConcreteConditionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths=(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',
                   ROOT/'reports/native_arm64.json', ROOT/'reports/condition_flow.json',
                   ROOT/'assets_original/configdata')

    def test_original_elf(self):
        report=audit(*self.paths)
        self.assertEqual(report['phase'],36)
        self.assertEqual(report['jump_tables_checked'],2)
        self.assertEqual(len(report['functions']),6)
        self.assertEqual(report['verified_instructions'],204)
        self.assertEqual(report['checkpoints'],31)
        self.assertEqual(report['config_tables']['conditionbuff']['count'],3544)
        self.assertEqual(report['config_tables']['conditioncamp']['count'],16)
        self.assertEqual(report['config_tables']['conditionentitytype']['count'],12)

    def test_report_unchanged(self):
        expected=json.loads((ROOT/'reports/concrete_conditions.json').read_text('utf8'))
        self.assertEqual(expected,audit(*self.paths))
        self.assertEqual((ROOT/'reports/concrete_conditions.lua').read_text('utf8'),as_lua(expected))
        self.assertIn('Nenhum dano',expected['limitations'][2])

    def test_wrong_elf_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'wrong.so'; file.write_bytes(b'wrong ELF')
            with self.assertRaisesRegex(ValueError,'divergente'):
                audit(file,*self.paths[1:])

    def test_incorrect_f35_report_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'wrong.json'; file.write_text('{"phase":30}')
            with self.assertRaisesRegex(ValueError,'F35'):
                audit(self.paths[0],self.paths[1],file,self.paths[3])

    def test_jump_table_lookup(self):
        data=self.paths[0].read_bytes()
        self.assertEqual(raw32(data,0xe4468c),-140)
        self.assertEqual(raw32(data,0xe447b8),-140)

    def test_lua_simulator(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex indisponivel')
        result=subprocess.run([exe,'--luaonly','tests/test_concrete_conditions.lua'],cwd=ROOT,
                              capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('F36 CONCRETE CONDITIONS LUA OK',result.stdout)

    def test_ui_preserved(self):
        main=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('local concreteConditionsView',main)
        self.assertIn('concreteConditionsView.draw(concreteConditionsReport',main)
        self.assertIn('setMode(26)',main)
        self.assertIn('lists[26][1]',main)
        self.assertIn('conditionView.draw(conditionReport',main)
        self.assertIn('setMode(14)',main)
        self.assertEqual(main.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),26)

if __name__=='__main__':unittest.main()
