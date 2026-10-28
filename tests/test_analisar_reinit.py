from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_reinit import FUNCTIONS,CHECKS,audit,validate,lua_report

class ReinitAudit(unittest.TestCase):
    def test_library(self):
        binary=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not binary.exists():self.skipTest('ELF não incluído no pacote público')
        result=audit(binary,ROOT/'reports/native_arm64.json')
        self.assertEqual(result['total_instructions'],447)
        self.assertEqual(result['total_checks'],46)
        self.assertEqual(len(result['simple_delta_fields']),9)
        self.assertEqual(result['constants']['config_level_stride'],10000)
        self.assertIn('Hero::reInit',lua_report(result))
    def test_wrong_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'bad.so'
            f.write_bytes(b'not the original')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                audit(f,ROOT/'reports/native_arm64.json')
    def test_incomplete(self):
        with self.assertRaisesRegex(ValueError,'incompletas'):
            validate('Hero::reInit',{})
    def test_tamper_opcode(self):
        _,start,size=FUNCTIONS['Hero::InitSkillAndAttri']
        bogus={addr:('nop','') for addr in range(start,start+size,4)}
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            validate('Hero::InitSkillAndAttri',bogus)
    def test_bad_operand(self):
        _,start,size=FUNCTIONS['Hero::PlayerRestartGame']
        bogus={addr:('str','x0, [x0]') for addr in range(start,start+size,4)}
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            validate('Hero::PlayerRestartGame',bogus)
