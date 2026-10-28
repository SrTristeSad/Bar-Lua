from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_renascimento import audit, validate, verify_slots, FUNCS, CHECKS, lua_catalog


class RebornAuditTests(unittest.TestCase):
    def test_real_arm64_if_present(self):
        lib=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not lib.exists(): self.skipTest('APK original não distribuído no pacote de código')
        report=audit(lib,ROOT/'reports/native_arm64.json')
        self.assertEqual(report['total_instructions'],391)
        self.assertEqual(report['total_checks'],39)
        self.assertEqual(len(report['functions']),4)
        self.assertIn('Hero::reborn',lua_catalog(report))
        self.assertIn('Hero::update',lua_catalog(report))
        self.assertEqual(report['virtual_slots']['hero_reborn']['symbol'],'_ZN4Hero6rebornEb')

    def test_bad_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'libcocos2dcpp.so'
            fake.write_bytes(b'teste de arquivo incorreto')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                audit(fake,ROOT/'reports/native_arm64.json')

    def test_missing_opcode(self):
        with self.assertRaisesRegex(ValueError,'incompletas'):
            validate('Entity::reborn',{})
        _,va,size=FUNCS['Entity::reborn']
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            validate('Entity::reborn',{va:('nop','')})

    def test_wrong_virtual_slot(self):
        vt={'_ZTV4Hero':0x24be6c0,'_ZTV6Entity':0x24bdae0}
        rel={
            0x24be6e0:'_ZN4Hero6updateEf',
            0x24be720:'_ZN4Hero6rebornEb',
            0x24be768:'_ZN4Hero8dieLogicEv',
            0x24bdb40:'_ZN6Entity6rebornEb',
        }
        result=verify_slots(vt,rel)
        self.assertEqual(len(result),4)
        tampered=rel.copy()
        tampered[0x24be720]='_ZN4Hero8dieLogicEv'
        with self.assertRaisesRegex(ValueError,'slot virtual'):
            verify_slots(vt,tampered)

    def test_checkpoint_bad_operand(self):
        _,va,byte_len=FUNCS['Hero::update']
        wrong={addr:('nop','') for addr in range(va,va+byte_len,4)}
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            validate('Hero::update',wrong)
