from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_morte import audit,verify_function,FUNCS,resolve_virtual,lua_catalog
class DeathAuditTests(unittest.TestCase):
    def test_slot_validation(self):
        vtables={'_ZTV4Hero':0x24be6c0,'_ZTV6Entity':0x24bdae0}
        reloc={0x24be718:'_ZN6Entity6onDiedEv',0x24be768:'_ZN4Hero8dieLogicEv',
               0x24bdb38:'_ZN6Entity6onDiedEv',0x24bdb88:'_ZN6Entity8dieLogicEv'}
        slots=resolve_virtual(vtables,reloc)
        self.assertEqual(slots['Hero']['damage_callback_relocation'],'0x24be718')
        bad=reloc.copy();bad[0x24be718]='_ZN4Hero8dieLogicEv'
        with self.assertRaisesRegex(ValueError,'slot virtual'):resolve_virtual(vtables,bad)
    def test_disassembly_missing(self):
        with self.assertRaisesRegex(ValueError,'faltando'):
            verify_function('Entity::onDied',{})
    def test_disassembly_corrupted(self):
        _,start,size=FUNCS['Entity::onDied']
        bad={x:('nop','') for x in range(start,start+size,4)}
        with self.assertRaisesRegex(ValueError,'checkpoint'):verify_function('Entity::onDied',bad)
    def test_hash_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'wrong.so';p.write_bytes(b'other')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                audit(p,ROOT/'reports/native_arm64.json')
    def test_real(self):
        elf=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not elf.exists():self.skipTest('Biblioteca original não distribuída')
        report=audit(elf,ROOT/'reports/native_arm64.json')
        self.assertEqual(len(report['functions']),4)
        self.assertEqual(report['total_instructions'],377)
        self.assertEqual(report['total_checks'],29)
        self.assertIn('Entity::onDied',lua_catalog(report))
        self.assertIn('Hero::dieLogic',lua_catalog(report))
