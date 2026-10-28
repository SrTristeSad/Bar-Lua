"""Regressoes da Fase 35: ELF verdadeiro, tabelas originais e simulador isolado."""
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
from analisar_condicoes import audit,parse_lines,as_lua

class ConditionsPhase35Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',ROOT/'reports/native_arm64.json',
                  ROOT/'reports/sector_filter.json',ROOT/'assets_original/configdata')

    def test_real_elf(self):
        result=audit(*self.args)
        self.assertEqual(result['verified_instructions'],233)
        self.assertEqual(result['checkpoints'],37)
        self.assertEqual(len(result['verified_functions']),5)
        self.assertEqual(result['table_summaries']['conditiontargetscount']['count'],7)
        self.assertEqual(result['table_summaries']['conditioncamp']['count'],16)
        self.assertEqual(sum(v['count'] for v in result['table_summaries'].values()),5002)
        self.assertIn('ordem dos alvos nao preservada',result['confirmed_rules'][1])

    def test_reports_identical(self):
        report=json.loads((ROOT/'reports/condition_flow.json').read_text('utf8'))
        self.assertEqual(report['phase'],35)
        self.assertEqual((ROOT/'reports/condition_flow.lua').read_text('utf8'),as_lua(report))
        self.assertFalse('source_names' in report)

    def test_bad_elf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.so';p.write_bytes(b'bad ELF')
            with self.assertRaisesRegex(ValueError,'divergente'):
                audit(p,*self.args[1:])

    def test_missing_old_report_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'old.json';p.write_text('{"phase":33}')
            with self.assertRaisesRegex(ValueError,'F34'):
                audit(self.args[0],self.args[1],p,self.args[3])

    def test_parse_utf8_byte_length(self):
        text='Mãe de ação'.encode('utf8')
        one=b'100 '+str(len(text)).encode()+b' '+text+b' 3 2 \n'
        self.assertEqual(parse_lines(one)[0],{'id':100,'name':'Mãe de ação','parameters':'3 2'})
        with self.assertRaises(ValueError):parse_lines(b'100 3 abcd 1\n')
        with self.assertRaises(ValueError):parse_lines(b'100 2 aa\n100 2 ab\n')
        with self.assertRaises(ValueError):parse_lines(b'bad data')

    def test_ui(self):
        src=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('"Condicoes ARM64"',src)
        self.assertIn('setMode(25)',src)
        self.assertIn('conditionView.draw(conditionReport',src)
        self.assertIn('conditionView.keypressed',src)
        self.assertIn('lists[25][1]',src)
        self.assertGreaterEqual(src.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),25)

    def test_lua(self):
        runtime=shutil.which('luatex')
        if not runtime:self.skipTest('luatex ausente')
        run=subprocess.run([runtime,'--luaonly','tests/test_condition_rules.lua'],cwd=ROOT,
                           capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn('F35 CONDITIONS LUA OK',run.stdout)

if __name__=='__main__':unittest.main()
