"""F50: candidate association does not establish virtual-call targets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from correlacionar_vtables50 import correlate,SHA

class Candidate50Tests(unittest.TestCase):
    def fixture(self):
        f47={"phase":47,"library_sha256":SHA,"vtable_candidates":[{
            "vtable_symbol":"_ZTV10CSelfSkill",
            "entries":[{"slot_offset":40,"referenced_symbol":"CSelfSkill::Update"}]}]}
        f49={"phase":49,"elf_sha256":SHA,"candidate_local_patterns":{
            "Entity::addSkill(skillPtr)":[{
                "callsite_va":"0xe48788","slot_offset":24,
                "receiver_register":"x1",
                "classification":"local_load_pattern_only","resolved_target":None}]}}
        return f47,f49
    def test_candidate_does_not_imply_proof(self):
        a,b=self.fixture()
        r=correlate(a,b)
        self.assertEqual(r["candidate_match_count"],1)
        self.assertEqual(r["confirmed_destinations"],0)
        self.assertFalse(r["basic_attack_4010020_effect_verified"])
        self.assertFalse(r["callsite_candidates"][0]["candidates"][0]["verified_destination"])
    def test_absent_slot_is_empty(self):
        a,b=self.fixture()
        b["candidate_local_patterns"]["Entity::addSkill(skillPtr)"][0]["slot_offset"]=32
        self.assertEqual(correlate(a,b)["candidate_match_count"],0)
    def test_mismatched_hash_rejected(self):
        a,b=self.fixture()
        b["elf_sha256"]="different"
        with self.assertRaises(ValueError):correlate(a,b)
    def test_unverified_pattern_only(self):
        a,b=self.fixture()
        b["candidate_local_patterns"]["Entity::addSkill(skillPtr)"][0]["resolved_target"]="guess"
        with self.assertRaises(ValueError):correlate(a,b)

if __name__=="__main__": unittest.main()
