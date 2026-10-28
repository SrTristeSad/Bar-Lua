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
from analisar_campos_combate import audit,validate,CHECKS

class CombatFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        cls.manifest=ROOT/'reports/native_arm64.json'
        cls.table=ROOT/'assets_original/configdata/config.hero.heroconfig.txt'
    def test_original_elf_and_configs(self):
        if not self.library.exists():self.skipTest('Biblioteca ARM64 original ausente')
        a=audit(self.library,self.manifest,self.table)
        self.assertEqual(a['phase'],32)
        self.assertEqual(a['verified_instruction_count'],1010)
        self.assertEqual(a['verified_function_count'],9)
        self.assertEqual(a['extra_checks'],18)
        self.assertEqual([s['config_offset'] for s in a['config_slots'] if s['confirmed']],['0x3c','0x40','0x44','0x48'])
        self.assertEqual(a['damage']['value_type'],2)
        self.assertEqual(a['damage_scope']['value_type'],3)
        self.assertEqual(len([s for s in a['config_slots'] if not s['confirmed']]),4)
    def test_rejects_bad_binary_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'lib.so';fake.write_bytes(b'no elf')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(fake,self.manifest,self.table)
    def test_rejects_bad_opcode(self):
        with self.assertRaises(ValueError):
            validate({},CHECKS['Hero::setDamage(int)'],'Hero::setDamage(int)')
    def test_public_report_avoids_inventing_defense(self):
        r=json.loads((ROOT/'reports/hero_combat_fields.json').read_text('utf-8'))
        self.assertEqual(r['damage']['hero_offset'],'0x32c')
        self.assertEqual(r['damage_scope']['hero_offset'],'0x330')
        self.assertEqual(r['config_slots'][1]['meaning'],'dano-base (Hero::setDamage)')
        self.assertIn('Nao identificado aqui nenhum campo de defesa.',r['limits'])
        self.assertEqual(len(r['config_slots']),8)
    def test_lua_interface(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('LuaTeX indisponivel')
        result=subprocess.run([exe,'--luaonly','tests/test_combat_fields.lua'],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('F32 COMBAT FIELDS LUA OK',result.stdout)
    def test_legacy_f31_artifacts_unchanged(self):
        a=json.loads((ROOT/'reports/hero_semantics.json').read_text('utf-8'))
        self.assertEqual(a['phase'],31)
        self.assertEqual(a['verified_instruction_count'],648)
        self.assertEqual(sum(s['confirmed'] for s in a['config_slots']),2)
