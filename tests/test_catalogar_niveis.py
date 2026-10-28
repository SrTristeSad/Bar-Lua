from __future__ import annotations
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from catalogar_niveis import build_tables,parse_hero,lua_export,SLOTS
from catalogar_habilidades import parse_table

class HeroLevels(unittest.TestCase):
    def test_real_apk_tables(self):
        summary,catalog=build_tables(ROOT/'assets_original')
        self.assertEqual(summary['hero_records'],1239)
        self.assertEqual(summary['entity_records'],2734)
        self.assertEqual(summary['slots'],list(SLOTS))
        self.assertGreater(summary['groups_with_multiple_levels'],0)
        barb=next(g for g in catalog['groups'] if g['base_id']==210001)
        self.assertEqual(barb['entity_id'],210000)
        self.assertEqual([r['values']['0x38'] for r in barb['levels'][:3]],[195,200,205])
        self.assertEqual([r['id'] for r in barb['levels'][:3]],[210001,220001,230001])
        self.assertNotIn('HP',lua_export(catalog))
        self.assertNotIn('ataque',lua_export(catalog))
        self.assertIn('33402fa701f4fd425779',summary['source_sha256']['config.hero.heroconfig.txt'])
    def test_invalid_record(self):
        with self.assertRaisesRegex(ValueError,'numéricos'):
            parse_hero({'payload':'10080 hello 1 2 3 4 5 6 7'})
        with self.assertRaisesRegex(ValueError,'int32'):
            parse_hero({'payload':'10080 99999999999 2 3 4 5 6 7 8 0'})
    def test_utf8_record_length(self):
        entry=parse_table('210001 9 巴巴六 10080 195 59 76 240 150 10000 29 8 0 \n'.encode(),'test')
        self.assertEqual(parse_hero(entry[210001])['values']['0x38'],195)
    def test_modified_config_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'configdata'
            dest.mkdir()
            for name in ('config.hero.heroconfig.txt','config.hero.entityconfig.txt'):
                shutil.copy2(ROOT/'assets_original/configdata'/name,dest/name)
            name=dest/'config.hero.heroconfig.txt'
            name.write_bytes(name.read_bytes()+b'\nchanged')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                build_tables(Path(tmp))
    def test_wrong_source_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                build_tables(Path(tmp))
