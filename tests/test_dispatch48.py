"""F48: ensure correlations never overclaim unresolved virtual call targets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from correlacionar_despacho48 import correlate, EXPECTED_SHA

def fixture():
    a={"phase":46,"library_sha256":EXPECTED_SHA,"sites":{
        "CSelfSkill::Update":[{"va":"0xe6596c","operand":"x8","resolution":"unresolved_indirect_call"}]}}
    b={"phase":47,"library_sha256":EXPECTED_SHA,"vtable_candidates":[
        {"vtable_symbol":"_ZTV10CSelfSkill","entries":[{"slot_offset":24,"referenced_symbol":"_ZN10CSelfSkill6UpdateEf"}]}]}
    return a,b

class Dispatch48Tests(unittest.TestCase):
    def test_unproven_dispatch_stays_unproven(self):
        a,b=fixture()
        report=correlate(a,b)
        self.assertEqual(report["indirect_sites"],1)
        self.assertEqual(report["candidate_vtables"],1)
        self.assertEqual(report["candidate_relocation_entries"],1)
        self.assertEqual(report["confirmed_virtual_edges"],0)
        self.assertIsNone(report["work_queue"][0]["destination_symbol"])
        self.assertFalse(report["gameplay_enabled"])
    def test_wrong_hash_rejected(self):
        a,b=fixture()
        b["library_sha256"]="wrong"
        with self.assertRaises(ValueError):correlate(a,b)
    def test_unexpected_resolution_rejected(self):
        a,b=fixture()
        a["sites"]["CSelfSkill::Update"][0]["resolution"]="resolved"
        with self.assertRaises(ValueError):correlate(a,b)

if __name__=="__main__":unittest.main()
