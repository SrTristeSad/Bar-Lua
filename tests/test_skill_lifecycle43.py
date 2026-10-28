"""F43: source-evidence regression tests (no proprietary assets required)."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from analisar_ciclo_skill43 import audit

class SkillLifecycle43Tests(unittest.TestCase):
    def test_known_lifecycle_without_inventing_damage(self):
        report = audit(ROOT)
        self.assertEqual(report["phase"], 43)
        self.assertEqual(report["source_mode"], "committed_reports")
        self.assertEqual(report["basic_skill"]["id"], 4010020)
        self.assertEqual(report["basic_skill"]["function_ids"], [])
        self.assertFalse(report["new_native_claims_verified"])
        self.assertFalse(report["gameplay_enabled"])
        self.assertEqual(report["native_slices"]["CSelfSkill::HasFunctions"]["va"], "0xe65a90")
        self.assertEqual(report["native_slices"]["Entity::addSkill(skillPtr)"]["va"], "0xe48744")

if __name__ == "__main__":
    unittest.main()
