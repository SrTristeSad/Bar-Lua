"""F38: regressões do fluxo de condições do CSkill original."""
from pathlib import Path
import json
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_gate_habilidades import audit,as_lua

class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',ROOT/'reports/native_arm64.json',ROOT/'reports/compare_conditions.json',ROOT/'assets_original/configdata')
    def test_elf(self):
        r=audit(*self.args)
        self.assertEqual(r['phase'],38)
        self.assertEqual(r['verified_instructions'],266)
        self.assertEqual(r['checkpoints'],43)
        self.assertEqual(len(r['audited']),6)
        self.assertEqual(r['binding']['skill_id'],4010020)
        self.assertIn('CSkill+0x30',r['native_fields']['target_ids'])
    def test_reports_deterministic(self):
        r=json.loads((ROOT/'reports/skill_condition_gate.json').read_text('utf8'))
        self.assertEqual(r,audit(*self.args))
        self.assertEqual(as_lua(r),(ROOT/'reports/skill_condition_gate.lua').read_text('utf8'))
        self.assertIn('nao prova',r['limits'][1].lower())
    def test_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'invalid.so';p.write_bytes(b'invalid')
            with self.assertRaisesRegex(ValueError,'ELF original divergente'):
                audit(p,*self.args[1:])
    def test_previous_phase_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'old.json';p.write_text('{"phase":36}')
            with self.assertRaisesRegex(ValueError,'F37'):
                audit(self.args[0],self.args[1],p,self.args[3])
    def test_lua_rules(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex ausente')
        p=subprocess.run([exe,'--luaonly','tests/test_skill_condition_gate.lua'],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        self.assertIn('F38 SKILL GATES LUA OK',p.stdout)
    def test_ui_integrated(self):
        s=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('setMode(28)',s)
        self.assertIn('skillConditionGateView.draw(skillConditionGateReport',s)
        self.assertIn('lists[28][1]',s)
        self.assertIn('skillConditionGateView.keypressed',s)
        self.assertIn('setMode(14)',s)
        self.assertGreaterEqual(s.split('local lists = ',1)[1].split('\n',1)[0].count('{}'),28)

if __name__=='__main__':unittest.main()
