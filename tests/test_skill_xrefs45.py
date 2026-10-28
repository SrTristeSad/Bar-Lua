"""F45 parser fixtures: both common llvm-objdump AArch64 layouts."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from rastrear_xrefs45 import parse

class Xref45Tests(unittest.TestCase):
    def test_words_bytes_and_ignored_indirect(self):
        lines=[
            "0000000000e48744 <Entity::tick>:",
            "  e48748: 94012345 bl 0xe65a90 <CSelfSkill::HasFunctions>",
            "  e4874c: 00 00 00 14 b #0xe65034 <CSkill::Release>",
            "  e48750: d63f0120 blr x9",
        ]
        result=parse(lines)
        self.assertEqual(result["CSelfSkill::HasFunctions"][0]["caller"],"Entity::tick")
        self.assertEqual(result["CSkill::Release"][0]["instruction_va"],"0xe4874c")
        self.assertEqual(len(result["CSkill::Release"]),1)
        self.assertEqual(result["CSelfSkill::Update"],[])
    def test_no_false_positive_from_other_destinations(self):
        result=parse(["  f00: 94000000 bl 0xe65a94",
                      "  f04: 94000000 bl 0xe65920"])
        self.assertTrue(all(not records for records in result.values()))
if __name__=="__main__":unittest.main()
