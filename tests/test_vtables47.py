"""F47: test conservative vtable relocation association."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from analisar_vtables47 import parse_symbols, parse_relocations, candidates

class Vtables47(unittest.TestCase):
    def test_candidate_slot_and_boundary(self):
        symbols=parse_symbols("   17: 0000000000010000    32 OBJECT  GLOBAL DEFAULT  24 _ZTV10CSelfSkill\n")
        reloc=parse_relocations("0000000000010010  0000000000000403 R_AARCH64_ABS64  0000000000020000 _ZN10CSelfSkill6UpdateEf + 0\n"
                                "0000000000010030  0000000000000403 R_AARCH64_ABS64  0000000000020000 _ZN6Other6UpdateEf + 0\n")
        result=candidates(symbols,reloc)
        self.assertEqual(len(result),1)
        self.assertEqual([x["slot_offset"] for x in result[0]["entries"]],[16])
        self.assertEqual(result[0]["entries"][0]["classification"],"relocation_reference_not_proven_call_target")
    def test_empty_no_proof(self):
        self.assertEqual(candidates([],[]),[])
        self.assertEqual(candidates(parse_symbols(""),parse_relocations("")),[])

if __name__=="__main__":unittest.main()
