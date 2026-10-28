#!/usr/bin/env python3
"""F43: audit documented lifecycle evidence; optionally disassemble original ELF.

Source-only mode uses committed reports and never interprets missing CFunction IDs
as proof of absent gameplay. Native mode requires user's own original ELF.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
SLICES = {
    "Entity::addSkill(skillPtr)": (0xe48744, 552),
    "CSkill::Release": (0xe65034, 128),
    "CSelfSkill::Init": (0xe657b0, 372),
    "CSelfSkill::Update": (0xe65924, 364),
    "CSelfSkill::HasFunctions": (0xe65a90, 16),
}

def read(name, root=ROOT):
    return json.loads((root / "reports" / name).read_text(encoding="utf-8"))

def audit(root=ROOT, elf=None):
    native = read("native_skill_flow.json", root)
    functions = read("self_skill_flow.json", root)
    f40 = read("skill_xconf40.json", root)
    f42 = read("basic_attack_trace42.json", root)
    assert len({native["library_sha256"], functions["elf_sha256"],
                f40["elf_sha256"], f42["original_elf_sha256"], SHA}) == 1
    assert f42["basic_skill"]["id"] == 4010020
    assert f42["basic_skill"]["function_ids"] == []
    assert functions["basic_skill"]["third_vector_function_ids"] == []
    assert f40["basic_skill"]["skill_kind"] == 10050
    assert native["functions"]["CSkill::Update(float)"]["instruction_count"] == 1
    assert "empty_base_update" in native["functions"]["CSkill::Update(float)"]["checks"]
    known = {
        "Entity::addSkill(skillPtr)": native["functions"]["Entity::addSkill(skillPtr)"]["virtual_address"],
        "CSkill::Release": native["functions"]["CSkill::Release"]["virtual_address"],
        **{x["name"]: x["va"] for x in functions["native_functions"] if x["name"] in SLICES}
    }
    for name, (va, size) in SLICES.items():
        assert int(known[name], 16) == va, name
    details = {}
    if elf is not None:
        elf = Path(elf)
        assert hashlib.sha256(elf.read_bytes()).hexdigest() == SHA, "original ELF hash mismatch"
        for name, (va, size) in SLICES.items():
            out = subprocess.run(["llvm-objdump", "-d", "--start-address="+hex(va),
                                  "--stop-address="+hex(va+size), str(elf)],
                                 capture_output=True, text=True, check=True, timeout=30).stdout
            # Keep only compact metadata; full instructions and proprietary ELF not committed.
            lines = [line for line in out.splitlines() if
                     line.strip().split(":")[0].strip().lower() in
                     {format(x, "x") for x in range(va, va+size, 4)}]
            assert len(lines) == size // 4, "incomplete disassembly: "+name
            details[name] = {"va": hex(va), "instruction_count": len(lines),
                             "disassembled": True}
    return {
        "phase": 43, "apk_version": "1.0.1811", "source_mode": "original_elf" if elf else "committed_reports",
        "elf_sha256": SHA, "basic_skill": f42["basic_skill"],
        "lifecycle": {
            "factory": "Selector 10050 chooses CSelfSkill (verified F41)",
            "construction": "Third vector is empty for 4010020; no functions created by that vector",
            "init": "Known code sets context on instantiated functions; zero-functions branch outcome still requires tracing",
            "update": "CSelfSkill::Update processes its active function collection; behavior of an empty collection in host lifecycle unproven",
            "has_functions": "Compares start/end pointers in vector at CSelfSkill+0x1b0",
            "release": "Release entry point known; relation to no-function skills not proved",
            "entity_handoff": "Entity::addSkill(skillPtr) known; disposal condition not yet proved"
        },
        "native_slices": {n: {"va": hex(v), "bytes": s, "disassembled": n in details}
                          for n, (v, s) in SLICES.items()},
        "open_questions": [
            "Does Entity::addSkill(skillPtr) discard an empty CSelfSkill, and on which condition?",
            "Does CSelfSkill::Init assign a terminal state for zero-function skills?",
            "Who invokes HasFunctions and Release? Recover native caller references.",
            "Does a separate animation/event route initiate the physical attack?"
        ],
        "gameplay_enabled": False, "new_native_claims_verified": False
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--elf", type=Path, help="Original user-provided arm64 libcocos2dcpp.so")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = audit(args.root, args.elf)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
