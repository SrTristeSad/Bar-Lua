import json
import struct
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_movimento import CONSTANTS, EXPECTED, load_symbols, verify_asm, report_to_lua, read_float_va
class TestAnalisarMovimento(unittest.TestCase):
    def test_report_verified(self):
        report=json.loads((ROOT/'reports/native_movement.json').read_text())
        self.assertEqual(len(report['functions']),5)
        self.assertEqual(sum(x['patterns_verified'] for x in report['functions']),23)
        self.assertEqual(report['constants']['speed_divisor'],100)
        self.assertEqual(report['constants']['degrees_multiplier'],180)
        self.assertEqual(report['sha256_libcocos2dcpp'],'8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677')
        lua=report_to_lua(report)
        self.assertIn('Hero::move_update(float)',lua)
        self.assertNotIn('0xbd432a60',lua)
    def test_symbols(self):
        catalog=load_symbols(ROOT/'reports/native_symbols.csv')
        self.assertEqual(set(catalog),set(EXPECTED))
    def test_reject_asm_incomplete(self):
        with self.assertRaises(ValueError):
            verify_asm('Hero::setSpeed(int)','ret')
        self.assertEqual(len(verify_asm('Hero::setSpeed(int)','str w1, [x0, #0x328]')),1)
    def test_reject_elf_invalid(self):
        with self.assertRaises(ValueError):
            read_float_va(b'junk',0x100)
        data=bytearray(100)
        data[:6]=b'\x7fELF\x02\x01'
        struct.pack_into('<Q',data,0x20,64)
        struct.pack_into('<HH',data,0x36,56,200)
        with self.assertRaises(ValueError):
            read_float_va(data,0x100)
if __name__=='__main__':unittest.main()