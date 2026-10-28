#!/usr/bin/env python3
"""F44: find direct ARM64 branch callers for skill lifecycle functions.

Requires original user-supplied ELF and llvm-objdump. Reports only direct BL/B
references confirmed in disassembly. Indirect/virtual calls are NOT resolved.
Does not commit binaries, assembly, or copyrighted game assets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

EXPECTED_SHA = "8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
TARGETS = {
    "Entity::addSkill(skillPtr)": 0xe48744,
    "CSkill::Release": 0xe65034,
    "CSelfSkill::HasFunctions": 0xe65a90,
    "CSelfSkill::Update": 0xe65924,
    "CSelfSkill::Init": 0xe657b0,
}
# objdump AArch64: 00e1234: d63f0120 bl 0xe65a90 <symbol>
INST = re.compile(r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{8}\s+)?(bl|b)\s+(?:0x)?([0-9a-f]+)(?:\s|$)", re.I)
FUNC = re.compile(r"^\s*([0-9a-f]+)\s+<([^>]+)>:\s*$", re.I)

def analyse_lines(lines):
    hits = {k: [] for k in TARGETS}
    current = None
    addresses = {value: key for key, value in TARGETS.items()}
    for line in lines:
        head = FUNC.match(line)
        if head:
            current = head.group(2)
            continue
        ins = INST.match(line)
        if not ins:
            continue
        address, operation, target = int(ins[1], 16), ins[2].lower(), int(ins[3], 16)
        if target in addresses:
            hits[addresses[target]].append({
                "caller_symbol": current, "instruction_va": hex(address),
                "operation": operation
            })
    for candidates in hits.values():
        candidates.sort(key=lambda c: int(c["instruction_va"], 16))
    return hits

def run(elf: Path):
    if hashlib.sha256(elf.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise ValueError("ELF does not match verified BarbarQ 1.0.1811 arm64 SHA256")
    proc = subprocess.Popen(["llvm-objdump", "-d", str(elf)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1)
    try:
        hits = analyse_lines(proc.stdout)
        stderr = proc.stderr.read()
        status = proc.wait(timeout=60)
        if status:
            raise RuntimeError(stderr[-2000:])
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    return {
        "phase": 44, "apk_version": "1.0.1811",
        "elf_sha256": EXPECTED_SHA,
        "scan": "ARM64 direct branch cross-references from ELF disassembly",
        "direct_calls": hits,
        "limitations": [
            "Direct BL/B references only; virtual calls via BLR and function-pointer dispatch are unresolved.",
            "A missing direct call does not mean the target is unused.",
            "Address references or branch references do not prove a particular skill ID reaches a function.",
            "No direct link from 4010020 to animation, collision, damage or cooldown has been shown."
        ],
        "gameplay_enabled": False
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("reports/skill_callers44.json"))
    opts = ap.parse_args()
    data = run(opts.elf)
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: len(v) for k,v in data["direct_calls"].items()}, indent=2))

if __name__ == "__main__":
    main()
