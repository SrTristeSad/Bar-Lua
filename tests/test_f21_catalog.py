import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from catalogar_habilidades import TABLES, collect, lua_export, parse_table
from analisar_habilidades import audit


class SkillCatalogTests(unittest.TestCase):
    def test_utf8_byte_prefix_and_control_escaping(self):
        obj = parse_table('123 6 攻击 1 2 9 \n'.encode(), 'fixture')
        self.assertEqual(obj[123]['description'], '攻击')
        self.assertIn('123', str(obj))
        self.assertIn('\\010', lua_export({'links': [{'id':1, 'name':'"', 'kind':1,'button':2,'skill_id':3, 'skill_name':'\n'}], 'summary': {'tables':{'heroskillconfig':1}}}))
        with self.assertRaisesRegex(ValueError,'comprimento'):
            parse_table('123 5 攻击 1 2 9\n'.encode(), 'fixture')
        with self.assertRaisesRegex(ValueError,'duplicado'):
            parse_table(b'1 0  \n1 0  \n', 'fixture')
        with self.assertRaisesRegex(ValueError,'UTF-8'):
            parse_table(b'123 1 \xff xxx\n', 'fixture')

    def test_real_catalog_and_provenance(self):
        summary, catalog = collect(ROOT / 'assets_original')
        from_disk = json.loads((ROOT / 'reports/skill_catalog_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary, from_disk)
        self.assertEqual(summary['tables']['heroskillconfig'], 31119)
        self.assertEqual(summary['tables']['functionbindskill'], 566)
        self.assertEqual(summary['tables']['functiondamage'], 687)
        self.assertEqual(summary['button_links'], 566)
        link = next(x for x in catalog['links'] if x['id'] == 10039)
        self.assertEqual((link['button'], link['skill_id']), (2, 4010020))
        self.assertEqual((link['name'], link['skill_name']), ('巴巴六攻击按钮与攻击绑定', '攻击'))
        self.assertEqual((ROOT/'cache/skill_catalog.lua').read_text(encoding='utf-8'), lua_export(catalog))

    def test_native_audit_matches_report(self):
        lib = ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        report = audit(lib, ROOT/'reports/native_arm64.json')
        self.assertEqual(report, json.loads((ROOT/'reports/native_skill_flow.json').read_text(encoding='utf-8')))
        self.assertEqual(len(report['functions']), 7)
        self.assertEqual(report['total_instructions'], 494)
        with tempfile.TemporaryDirectory() as t:
            wrong = Path(t)/'wrong.so'
            wrong.write_bytes(b'invalid')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                audit(wrong, ROOT/'reports/native_arm64.json')

    def test_lua_panel_and_syntax(self):
        for file in ('tests/test_skill_view.lua', 'tests/test_skill_catalog.lua'):
            p=subprocess.run(['luatex','--luaonly',file],capture_output=True,text=True,cwd=ROOT,timeout=40)
            self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
            self.assertIn(' OK',p.stdout)


if __name__ == '__main__': unittest.main()
