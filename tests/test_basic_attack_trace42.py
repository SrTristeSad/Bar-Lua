"""F42: cross-check evidence already audited in F20, F21, F40 and F41.

Does not assert the damage, animation or cooldown path of attack 4010020.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))

class BasicAttackTrace42Tests(unittest.TestCase):
    def test_cross_phase_native_chain(self):
        trace = load("basic_attack_trace42.json")
        atk = load("native_attacks.json")
        native = load("native_skill_flow.json")
        selfskill = load("self_skill_flow.json")
        expected = {f["name"]: f["va"] for f in trace["verified_native_entrypoints"]}
        self.assertEqual(expected["Hero::onButtonClicked"], atk["functions"]["Hero::onButtonClicked(config::skill::ButtonType)"]["address"])
        self.assertEqual(expected["Entity::addSkill(configId)"], native["functions"]["Entity::addSkill(configId)"]["virtual_address"])
        self.assertEqual(expected["CSkill::CreateSkillBySkillConfigId"], native["functions"]["CSkill::CreateSkillBySkillConfigId"]["virtual_address"])
        for key in ("CSelfSkill::CSelfSkill", "CSelfSkill::Init", "CSelfSkill::Update"):
            self.assertEqual(expected[key], next(f["va"] for f in selfskill["native_functions"] if f["name"] == key))
        self.assertEqual(trace["original_elf_sha256"], selfskill["elf_sha256"])
        self.assertEqual(trace["original_elf_sha256"], atk["library_sha256"])

    def test_basic_skill_remains_without_function_ids(self):
        trace = load("basic_attack_trace42.json")
        f40 = load("skill_xconf40.json")["basic_skill"]
        f41 = load("self_skill_flow.json")["basic_skill"]
        basic = trace["basic_skill"]
        self.assertEqual(basic["id"], f40["id"])
        self.assertEqual(basic["binding_id"], f40["binding_id"])
        self.assertEqual(basic["button_code"], f40["button_code"])
        self.assertEqual(basic["selector_id"], f41["selector_id"])
        self.assertEqual(basic["selector_id"], f40["skill_kind"])
        self.assertEqual(basic["function_ids"], f41["third_vector_function_ids"])
        self.assertEqual(basic["creator_condition_ids"], f40["creator_conditions"])
        self.assertEqual(basic["target_condition_ids"], f40["target_conditions"])
        self.assertEqual(basic["enhancement_id"], f40["enhancement_id"])
        self.assertEqual(basic["configuration_instantiated_function_count"], 0)
        self.assertFalse(trace["gameplay_enabled"])
        self.assertTrue(trace["evidence_boundary"]["not_confirmed"])

if __name__ == "__main__":
    unittest.main()
