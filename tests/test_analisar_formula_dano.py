import copy
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_formula_dano import audit,OPERATIONS,parse_instructions,verify_operations,find_file_offset,export_lua
class DamageAuditTests(unittest.TestCase):
    def test_parser_ignores_multiline(self):
        s='  10: 11111111      ret\n  14: 11111111      mov x0,x1\n'
        result=parse_instructions(s)
        self.assertEqual(len(result),2)
        self.assertEqual(result[0x14][0],'mov')
    def test_missing_instruction_refused(self):
        with self.assertRaisesRegex(ValueError, 'instrução esperada'):
            verify_operations({})
    def test_bad_mapping(self):
        with self.assertRaisesRegex(ValueError, 'fora dos segmentos'):
            find_file_offset(1,'')
    def test_no_executable_payload_in_catalog(self):
        lua=export_lua({'address':'0xe52950','function_instructions':332,'percent_ratio':100,'verified_operations':len(OPERATIONS)})
        self.assertNotIn('love.physics',lua)
        self.assertNotIn('os.execute',lua)
    def test_bad_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'libcocos2dcpp.so'
            fake.write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                audit(fake,ROOT/'reports/native_arm64.json')
    def test_real_elf(self):
        lib=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not lib.exists():self.skipTest('ELF original não distribuído no GitHub')
        data=audit(lib,ROOT/'reports/native_arm64.json')
        self.assertEqual(data['percent_ratio'],100)
        self.assertEqual(data['function_instructions'],332)
        self.assertEqual(data['verified_operations'],len(OPERATIONS))
        self.assertEqual(data['parameter_offsets'],['0x38','0x40','0x48','0x58','0x50','0x60'])
        self.assertTrue(data['map_type_seven_special_branch'])
