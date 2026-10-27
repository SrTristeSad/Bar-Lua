"""Testes artificiais do leitor ELF sem depender do APK."""
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from auditar_elf import parse_dynamic_symbols, parse_needed, verify_elf_header, write_reports, CLASSES

class NativeAuditTests(unittest.TestCase):
    def test_elf_header(self):
        data = bytearray(64)
        data[:6] = b'\x7fELF\x02\x01'
        data[18:20] = (183).to_bytes(2, 'little')
        verify_elf_header(data)
        data[18:20] = (62).to_bytes(2, 'little')
        with self.assertRaises(ValueError): verify_elf_header(data)
        with self.assertRaises(ValueError): verify_elf_header(b'garbage')

    def test_parse_realdynsym_shape(self):
        fixture = """Symbol table '.dynsym' contains 3 entries:
     0: 0000000000000000 0 NOTYPE LOCAL DEFAULT UND
     1: 00000000011baac0 964 FUNC GLOBAL DEFAULT 7 _ZN16CPetFightingIdleD2Ev
     2: 0000000000000000 0 FUNC GLOBAL DEFAULT UND malloc
"""
        syms = parse_dynamic_symbols(fixture)
        self.assertEqual(len(syms), 2)
        self.assertEqual(syms[0]['address'], '0x11baac0')
        self.assertEqual(syms[1]['section'], 'UND')
        self.assertEqual(parse_needed('0x1 (NEEDED) Shared library: [libfmod.so]'), ['libfmod.so'])

    def test_reports_are_limited_to_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            report = {'focus_classes': {cl: {'count':0, 'sample':[]} for cl in CLASSES}}
            sample = {'signature':'Hero::setEnergy(int)','address':'0x20',
                      'bytes':28,'mangled':'_ZN4Hero9setEnergyEi'}
            report['focus_classes']['Hero'] = {'count':1,'sample':[sample]}
            write_reports(Path(directory),report,{'Hero':[sample]})
            self.assertIn('Hero::setEnergy', (Path(directory)/'native_findings.lua').read_text())
            self.assertIn('Hero::setEnergy', (Path(directory)/'native_symbols.csv').read_text())
