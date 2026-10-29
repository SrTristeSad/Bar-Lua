"""F46 test fixtures for indirect-call inventory."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from rastrear_despacho_virtual46 import parse

class VirtualDispatch46Tests(unittest.TestCase):
    def test_blr_sites_without_false_targets(self):
        sample="""0000000000e65924 <CSelfSkill::Update>:
  e65924: f9400108 ldr x8, [x8]
  e65928: f9400d08 ldr x8, [x8, #24]
  e6592c: d63f0100 blr x8
  e65930: 94000001 bl 0xe65934
  e65934: d65f03c0 ret
"""
        sites=parse(sample,0xe65924,40)
        self.assertEqual(len(sites),1)
        self.assertEqual(sites[0]["va"],"0xe6592c")
        self.assertEqual(sites[0]["operand"],"x8")
        self.assertEqual(sites[0]["resolution"],"unresolved_indirect_call")
        self.assertEqual([x["opcode"] for x in sites[0]["preceding"]],["ldr","ldr"])
    def test_byte_format_and_range(self):
        sample="""  e65920: 00 01 3f d6 blr x8
  e65924: 00 01 3f d6 blr x8
  e65928: 00 00 00 94 bl 0xe65930
"""
        self.assertEqual(len(parse(sample,0xe65924,8)),1)

if __name__=="__main__":unittest.main()
