from __future__ import annotations
import copy
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_valores_vida import audit,CHECKS,FUNCTIONS,instructions,check_instructions,lua_catalog

class ValueAndHPTests(unittest.TestCase):
    def test_parser_ret_does_not_eat_next_line(self):
        data='  a000: d65f03c0   ret\n  a004: d503201f   nop\n'
        parsed=instructions(data)
        self.assertEqual(list(parsed),[0xa000,0xa004])
        self.assertEqual(parsed[0xa000],('ret',''))
    def test_partial_disassembly_rejected(self):
        with self.assertRaisesRegex(ValueError,'incompleta'):
            check_instructions('Hero::addHurtFromEnemy',{})
    def test_instruction_substitution_rejected(self):
        label='Hero::addHurtFromEnemy'
        _,start,size=FUNCTIONS[label]
        fake={address:('nop','') for address in range(start,start+size,4)}
        with self.assertRaisesRegex(ValueError,'divergente'):
            check_instructions(label,fake)
    def test_wrong_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'libcocos2dcpp.so'
            file.write_bytes(b'invalid')
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                audit(file,ROOT/'reports/native_arm64.json')
    def test_lua_export_has_no_runtime_side_effects(self):
        report={'total_instructions':269,'total_checks':44,
                'functions':[{'name':'Hero::addHurtFromEnemy','address':'0xe57678','instructions':89,'checks':18}]}
        cat=lua_catalog(report)
        self.assertIn('hp_offset="0x314"',cat)
        self.assertNotIn('love.physics',cat)
    def test_real_original_library(self):
        elf=ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not elf.exists():self.skipTest('ELF não distribuído no repositório')
        report=audit(elf,ROOT/'reports/native_arm64.json')
        self.assertEqual(len(report['functions']),3)
        self.assertEqual(report['total_instructions'],269)
        self.assertEqual(report['total_checks'],sum(map(len,CHECKS.values())))
        self.assertEqual(report['hp_observations']['hp_offset'],'0x314')
        self.assertEqual(report['value_observations']['contextual_special_types'],[1002,1003])
