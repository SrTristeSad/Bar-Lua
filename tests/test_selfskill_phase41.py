"""F41: prova estática de CFunction criada a partir do terceiro vetor."""
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
from analisar_fluxo_selfskill import audit, lua_report, FUNCTIONS, CHECKS

class SelfSkillTests(unittest.TestCase):
    def test_original_elf_and_catalog(self):
        report=audit(ROOT)
        self.assertEqual(report['phase'],41)
        self.assertEqual(report['total_native_functions'],8)
        self.assertEqual(report['verified_arm64_instructions'],532)
        self.assertEqual(report['checkpoints'],39)
        self.assertEqual(report['skill_records_decoded'],31013)
        self.assertEqual(report['skill_records_pending_optional_object'],106)
        self.assertEqual(report['third_vector_total_entries'],62722)
        self.assertEqual(report['third_vector_distinct_ids'],61555)
        self.assertEqual(report['unmatched_distinct_function_ids'],0)
        self.assertEqual(report['basic_skill']['third_vector_function_ids'],[])
        self.assertEqual(report['basic_skill']['selector_id'],10050)
        self.assertIn('GetSelectById',report['native_links']['selector'])
    def test_category_counts_consistent(self):
        report=json.loads((ROOT/'reports/self_skill_flow.json').read_text('utf8'))
        self.assertEqual(sum(report['function_id_occurrences_by_table'].values()),62722)
        self.assertEqual(report['skills_with_function_ids']+report['skills_without_function_ids'],31013)
        self.assertGreater(report['function_id_occurrences_by_table']['functiondamage'],0)
        self.assertGreater(report['function_id_occurrences_by_table']['functionanimation'],0)
        self.assertEqual(report, audit(ROOT))
        self.assertEqual(lua_report(report),(ROOT/'reports/self_skill_flow.lua').read_text('utf8'))
    def test_bad_elf_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'lib/arm64-v8a').mkdir(parents=True)
            (p/'reports').mkdir()
            shutil.copy(ROOT/'reports/skill_condition_gate.json',p/'reports/skill_condition_gate.json')
            (p/'lib/arm64-v8a/libcocos2dcpp.so').write_bytes(b'incorrect')
            with self.assertRaises((ValueError,KeyError)):
                audit(p)
    def test_lua_model_and_view(self):
        tex=shutil.which('luatex')
        if not tex:self.skipTest('luatex indisponivel')
        result=subprocess.run([tex,'--luaonly','tests/test_selfskill_flow.lua'],cwd=ROOT,
                             capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('F41 SELF SKILL LUA OK',result.stdout)
    def test_main_integration_preserves_previous_tabs(self):
        main=(ROOT/'main.lua').read_text('utf8')
        for needle in ('lists[31][1]', 'setMode(31)',
          'selfSkillFlowView.draw(selfSkillFlowReport','reports/self_skill_flow.lua',
          'selfSkillFlowView.keypressed', 'setMode(14)', 'setMode(30)'):
            self.assertIn(needle,main)
        self.assertGreaterEqual(main.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),31)
        self.assertIn('src/self_skill_flow_view',main.replace('.','/'))
if __name__=='__main__':unittest.main()
