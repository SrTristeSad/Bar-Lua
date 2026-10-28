from __future__ import annotations
import unittest,sys,shutil,subprocess,hashlib,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_esquema_heroi import audit,decode_value_types,validate_loader,FUNCTIONS

class HeroSchema(unittest.TestCase):
    def test_original_loader_and_dispatch(self):
        lib=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        table=ROOT/'assets_original/configdata/config.hero.heroconfig.txt'
        if not lib.exists() or not table.exists():self.skipTest('ELF/config privados ausentes')
        data=audit(lib,ROOT/'reports/native_arm64.json',table)
        self.assertEqual(data['total_instructions'],586)
        self.assertEqual(len(data['slot_load_order']),8)
        self.assertEqual(data['confirmed_hp_slot'],'0x44')
        self.assertEqual(len(data['value_types']),32)
        by_id={e['value_type']:e for e in data['value_types']}
        self.assertEqual(by_id[5]['hero_offset'],'0x314')
        self.assertEqual(by_id[11]['hero_offset'],'0x310')
        self.assertEqual(data['example_barbarian']['210001']['0x44'],240)
    def test_refuse_wrong_binary_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            fake=Path(directory)/'lib.so'
            fake.write_bytes(b'Not BarbarQ native code')
            with self.assertRaisesRegex(ValueError,'hash'):
                audit(fake,ROOT/'reports/native_arm64.json',ROOT/'assets_original/configdata/config.hero.heroconfig.txt')
    def test_refuse_tampered_loader(self):
        with self.assertRaisesRegex(ValueError,'divergencia'):
            validate_loader({})
    def test_published_report_keeps_other_fields_anonymous(self):
        data=json.loads((ROOT/'reports/hero_schema.json').read_text('utf8'))
        self.assertEqual(data['phase'],30)
        self.assertEqual(data['confirmed_hp_slot'],'0x44')
        self.assertEqual(data['total_instructions'],586)
        self.assertEqual(len(data['value_types']),32)
        self.assertNotIn('attack',data)
    def test_lua_schema_and_view(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex ausente')
        run=subprocess.run([exe,'--luaonly','tests/test_hero_schema.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn('F30 HERO SCHEMA LUA OK',run.stdout)
    def test_integrated_existing_mode(self):
        s=(ROOT/'main.lua').read_text('utf8')
        self.assertIn('heroSchemaReport = readLua("reports/hero_schema.lua")',s)
        self.assertIn('levelAttributesView.draw(item,heroAttrReport',s)
        self.assertIn('},heroSchemaReport)',s)
        self.assertIn('setMode(22)',s)

if __name__=='__main__':unittest.main()
