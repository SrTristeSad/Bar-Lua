import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from analisar_fluxo import (TARGETS, catalog_symbols, parse_disassembly,
                          report_to_lua, verify_elf_header)


class FlowTests(unittest.TestCase):
    def test_catalog_matches_expected_signatures(self):
        entries = catalog_symbols(ROOT / 'reports/native_symbols.csv')
        self.assertEqual(set(entries), set(TARGETS))
        self.assertTrue(all(0 < e['size'] <= 16384 for e in entries.values()))

    def test_parse_static_branch_and_direct_call(self):
        sample = '''
        00001000 <func>:
        1000: 94000002  bl 0x1008 <_ZN4Hero6updateEf@plt>
        1004: 54000040  b.eq 0x100c <func+0xc>
        1008: d63f0040  blr x2
        100c: d65f03c0  ret
        '''
        stats = parse_disassembly(sample, start=0x1000, size=16)
        self.assertEqual(stats['instruction_count'], 4)
        self.assertEqual(stats['direct_calls'], 1)
        self.assertEqual(stats['indirect_calls'], 1)
        self.assertEqual(stats['branch_instructions'], 1)
        self.assertTrue(stats['targets'][0]['external_plt'])
        self.assertEqual(stats['targets'][0]['address'], '0x1008')

    def test_reject_incomplete_disassembly(self):
        with self.assertRaises(ValueError):
            parse_disassembly('1000: d65f03c0 ret', start=0x1000, size=8)

    def test_bad_header(self):
        with self.assertRaises(ValueError):
            verify_elf_header(b'broken')

    def test_lua_data_has_no_instructions(self):
        report = {'functions': [{'signature': 'Hero::setStickDir(int)', 'address': '0xe5983c',
                  'bytes': 8, 'instruction_count': 2, 'direct_calls': 0,
                  'indirect_calls': 0, 'branch_instructions': 0, 'comparisons': 0,
                  'targets': []}]}
        lua = report_to_lua(report)
        self.assertIn('Hero::setStickDir(int)', lua)
        self.assertNotIn('0xb9032401', lua)

    def test_report_hash_and_size(self):
        path = ROOT / 'reports/native_flow.json'
        if not path.is_file():
            self.skipTest('Relatório gerado localmente, não distribuído no pacote apenas com código')
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(len(data['functions']), len(TARGETS))
        self.assertEqual(sum(f['instruction_count'] for f in data['functions']), 1576)
        self.assertTrue(all(f['instruction_count'] * 4 == f['bytes'] for f in data['functions']))
        self.assertEqual(data['sha256_libcocos2dcpp'],
                         '8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677')
        self.assertEqual(data['functions'][0]['instruction_count'], 2)
        self.assertEqual(data['functions'][-1]['instruction_count'], 1)

if __name__ == '__main__':
    unittest.main()