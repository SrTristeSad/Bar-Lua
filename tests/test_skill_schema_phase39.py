import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_esquema_skill import audit, record_tail, lua_report

class Schema39(unittest.TestCase):
    def test_original_library(self):
        r=audit(ROOT)
        self.assertEqual(r['phase'],39)
        self.assertEqual(r['verified_instructions'],382)
        self.assertEqual(r['checkpoints'],18)
        self.assertEqual(r['records'],31119)
    def test_basic_skill_tail(self):
        tail=record_tail('6 攻击 18 SkillPanel/axe.png 6 攻击 6 攻击 0  - 0 10050 0 0 -1 ')
        self.assertEqual(tail['last_four_numeric'],[10050,0,0,-1])
    def test_no_invented_condition_ids(self):
        r=json.loads((ROOT/'reports/hero_skill_schema.json').read_text())
        self.assertFalse(r['basic_skill']['condition_lists_verified'])
        self.assertEqual(r['binding']['skill_id'],4010020)
        self.assertEqual([x['table'] for x in r['token_occurrences']],
          ['config.skill.functionbindskill.txt','config.skill.heroskillconfig.txt'])
    def test_only_metadata_public(self):
        txt=lua_report(json.loads((ROOT/'reports/hero_skill_schema.json').read_text()))
        self.assertNotIn('攻击',txt)
        self.assertIn('gameplay_enabled=false',txt)
    def test_main_integration(self):
        main=(ROOT/'main.lua').read_text()
        self.assertIn('lists[29][1]',main)
        self.assertIn('heroSkillSchemaView.draw',main)
        self.assertIn('setMode(29)',main)

if __name__=='__main__':unittest.main()
