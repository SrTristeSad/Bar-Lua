from __future__ import annotations
import unittest,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_atributos import audit,FUNCTIONS,CHECKS,validate,lua_report
class AttributesArm64(unittest.TestCase):
    def test_original_binary(self):
        lib=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not lib.exists():self.skipTest('ELF não incluído no pacote público')
        data=audit(lib,ROOT/'reports/native_arm64.json')
        self.assertEqual(data['total_instructions'],696)
        self.assertEqual(data['total_checks'],34)
        self.assertEqual(len(data['functions']),3)
        self.assertIn('getValueByType',lua_report(data))
    def test_wrong_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.so'
            path.write_bytes(b'ARM64 falso')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                audit(path,ROOT/'reports/native_arm64.json')
    def test_missing_opcodes(self):
        with self.assertRaisesRegex(ValueError,'incompleta'):
            validate('Hero::init',{})
    def test_tampered_opcode(self):
        _,addr,size=FUNCTIONS['Hero::getValueByType']
        bogus={a:('nop','') for a in range(addr,addr+size,4)}
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            validate('Hero::getValueByType',bogus)
