"""F40: vetores contados e vínculos verificados no ELF e nas tabelas originais."""
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
from decodificar_skill_xconf import decode_absent_object_suffix,audit,lua_report,CHECKS

class SkillXconf40(unittest.TestCase):
    def test_real_elf_and_table(self):
        out=audit(ROOT)
        self.assertEqual(out['phase'],40)
        self.assertEqual(out['records_total'],31119)
        self.assertEqual(out['records_decoded'],31013)
        self.assertEqual(out['records_skipped_optional_object'],106)
        self.assertEqual(out['verified_instructions'],382)
        self.assertEqual(out['new_checkpoints'],19)
        self.assertEqual(out['basic_skill']['skill_kind'],10050)
        self.assertEqual(out['basic_skill']['creator_conditions'],[])
        self.assertEqual(out['basic_skill']['target_conditions'],[])
        self.assertEqual(out['basic_skill']['third_vector'],[])
        self.assertFalse(out['basic_skill']['damage_chain_verified'])
    def test_report_deterministic_and_no_original_strings(self):
        out=json.loads((ROOT/'reports/skill_xconf40.json').read_text('utf-8'))
        self.assertEqual(out,audit(ROOT))
        exported=lua_report(out)
        self.assertEqual(exported,(ROOT/'reports/skill_xconf40.lua').read_text('utf-8'))
        self.assertNotIn('攻击',exported)
        self.assertIn('gameplay_enabled=false',exported)
        self.assertIn('31013',exported)
    def test_vector_count_and_scalar_layout(self):
        f=decode_absent_object_suffix
        a=f('6 teste 0  - 2 101 202 10050 1 303 3 5 6 7 -1')
        self.assertEqual(a['creator_condition_ids'],[101,202])
        self.assertEqual(a['kind'],10050)
        self.assertEqual(a['target_condition_ids'],[303])
        self.assertEqual(a['third_vector_ids'],[5,6,7])
        self.assertEqual(a['enhancement_id'],-1)
        self.assertEqual(f('dummy - 0 10050 0 0 -1')['third_vector_ids'],[])
    def test_corrupt_lengths_rejected(self):
        for payload in ('test - 2 11 10050 0 0 -1',
                        'test - -1 10050 0 0 -1',
                        'test - 0 10050 0 0 -1 999',
                        'test - 1 OOPS 10050 0 0 -1',
                        'test @ object 0 10050 0 0 -1'):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):decode_absent_object_suffix(payload)
    def test_signature_refuses_bad_library(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'lib/arm64-v8a').mkdir(parents=True)
            (root/'reports').mkdir()
            for name in ('skill_condition_gate.json','skill_catalog_summary.json'):
                shutil.copyfile(ROOT/'reports'/name,root/'reports'/name)
            (root/'lib/arm64-v8a/libcocos2dcpp.so').write_bytes(b'wrong')
            with self.assertRaises((ValueError,KeyError)):
                audit(root)
    def test_lua_view_and_main_integration(self):
        exe=shutil.which('luatex')
        if exe:
            result=subprocess.run([exe,'--luaonly','tests/test_skill_xconf40.lua'],cwd=ROOT,
                                  capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
            self.assertIn('F40 XCONF LUA OK',result.stdout)
        main=(ROOT/'main.lua').read_text('utf-8')
        for text in ('lists[30][1]','skillXconfView.draw(skillXconfReport',
                     'setMode(30)','skillXconfView.keypressed','skill_xconf40.lua'):
            self.assertIn(text,main)
        self.assertIn('setMode(14)',main)
        self.assertGreaterEqual(main.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),30)

if __name__=='__main__':unittest.main()
