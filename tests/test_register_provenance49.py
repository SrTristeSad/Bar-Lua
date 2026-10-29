"""F49: local register provenance fixtures."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from rastrear_registradores49 import records, identify
class Register49Tests(unittest.TestCase):
    def test_adjacent_vptr_slot_blr(self):
        asm="""  e65960: f9400029 ldr x9, [x1]
  e65964: f9400d28 ldr x8, [x9, #24]
  e65968: d63f0100 blr x8
"""
        result=identify(records(asm))
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["slot_offset"],24)
        self.assertEqual(result[0]["receiver_register"],"x1")
        self.assertIsNone(result[0]["resolved_target"])
    def test_wrong_register_rejected(self):
        asm="""e65960: f9400029 ldr x9, [x1]
e65964: f9400d28 ldr x8, [x10, #24]
e65968: d63f0100 blr x8
"""
        self.assertEqual(identify(records(asm)),[])
    def test_branch_rejected(self):
        asm="""e65960: f9400029 ldr x9, [x1]
e65964: f9400d28 ldr x8, [x9, #24]
e65966: 14000000 b 0xe65968
e65968: d63f0100 blr x8
"""
        self.assertEqual(identify(records(asm)),[])
if __name__=="__main__":unittest.main()
