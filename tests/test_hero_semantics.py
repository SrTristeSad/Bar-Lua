from __future__ import annotations
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_semantica_heroi import audit,CHECKS,validate_checks

class HeroSemanticsTests(unittest.TestCase):
    def test_original_binary_and_config(self):
        lib=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        table=ROOT/'assets_original/configdata/config.hero.heroconfig.txt'
        if not lib.exists():self.skipTest('Biblioteca do APK nao montada')
        data=audit(lib,ROOT/'reports/native_arm64.json',table)
        self.assertEqual(data['verified_instruction_count'],648)
        self.assertEqual(data['confirmed_hp_slot'],'0x44')
        self.assertEqual(data['confirmed_speed_slot'],'0x48')
        self.assertEqual(data['speed_value_type'],19)
        self.assertEqual(data['speed_divisor'],100.0)
        self.assertEqual(data['barbarian_level1_raw_speed'],150)
        self.assertEqual(data['barbarian_level1_movement_component'],1.5)
        self.assertEqual(len(data['config_slots']),8)
        self.assertEqual(sum(x['confirmed'] for x in data['config_slots']),2)
    def test_fails_on_binary_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'lib.so';fake.write_bytes(b'not original')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(fake,ROOT/'reports/native_arm64.json',ROOT/'assets_original/configdata/config.hero.heroconfig.txt')
    def test_fails_on_broken_opcode(self):
        with self.assertRaisesRegex(ValueError,'divergente'):
            validate_checks({},CHECKS['Hero::setSpeed(int)'])
    def test_catalog_does_not_invent_attack_or_defense(self):
        data=json.loads((ROOT/'reports/hero_semantics.json').read_text('utf8'))
        self.assertEqual([s['meaning'] for s in data['config_slots'] if s['confirmed']],['HP inicial','velocidade-base'])
        self.assertEqual(len([s for s in data['config_slots'] if not s['confirmed']]),6)
    def test_lua_ui_and_values(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex ausente')
        r=subprocess.run([exe,'--luaonly','tests/test_hero_semantics.lua'],cwd=ROOT,text=True,capture_output=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('F31 HERO SEMANTICS LUA OK',r.stdout)
    def test_main_loads_native_catalog(self):
        src=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('heroSemanticReport = readLua("reports/hero_semantics.lua")',src)
        self.assertIn('heroSchemaReport,heroSemanticReport)',src)
        self.assertIn('setMode(22)',src)

if __name__=='__main__':unittest.main()
