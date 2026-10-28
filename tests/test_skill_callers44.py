"""F44 test: direct branch extraction without proprietary binaries."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rastrear_chamadores_skill44 import analyse_lines, TARGETS

class Callers44Tests(unittest.TestCase):
    def test_direct_calls_are_attributed(self):
        example = [
            "0000000000e48744 <Entity::addSkill>:",
            "  e48748: 94012345 bl 0xe65a90 <CSelfSkill::HasFunctions>",
            "  e48750: 14012345 b 0xe65034 <CSkill::Release>",
            "  e48754: d63f0120 blr x9",
        ]
        result = analyse_lines(example)
        self.assertEqual(len(result["CSelfSkill::HasFunctions"]), 1)
        self.assertEqual(result["CSelfSkill::HasFunctions"][0]["caller_symbol"], "Entity::addSkill")
        self.assertEqual(result["CSkill::Release"][0]["instruction_va"], "0xe48750")
        self.assertEqual(result["CSelfSkill::Update"], [])
        self.assertEqual(set(result), set(TARGETS))
    def test_only_exact_target(self):
        data = analyse_lines(["f00: 94000000 bl 0xe65a94", "f04: d63f0100 blr x8"])
        self.assertTrue(all(not x for x in data.values()))

if __name__ == "__main__":
    unittest.main()
