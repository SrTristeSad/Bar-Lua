#!/usr/bin/env python3
"""F46: inventory indirect ARM64 calls in verified skill-function ranges.

A BLR register is not an identified destination. This tool records call sites
and a small preceding disassembly window for manual vtable/dataflow review.
No proprietary ELF or disassembly is committed to the repository.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from collections import deque
from pathlib import Path

EXPECTED_SHA="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
RANGES={
 "CSkill::CreateSkillBySkillConfigId":(0xe650b4,320),
 "Entity::addSkill(skillPtr)":(0xe48744,552),
 "CSelfSkill::CSelfSkill":(0xe6555c,596),
 "CSelfSkill::Init":(0xe657b0,372),
 "CSelfSkill::Update":(0xe65924,364),
 "CSelfSkill::HasFunctions":(0xe65a90,16),
}
LINE=re.compile(r"^\s*([0-9a-f]+):\s+(?:(?:[0-9a-f]{8}|(?:[0-9a-f]{2}\s+){3}[0-9a-f]{2})\s+)?([a-z][a-z0-9.]*)\s*(.*)$",re.I)
INDIRECT={"blr","blraa","blrab","blraaz","blrabz"}

def parse(text, start, size, window=5):
    history=deque(maxlen=window)
    sites=[]
    for line in text.splitlines():
        match=LINE.match(line)
        if not match:continue
        va=int(match.group(1),16)
        if not(start<=va<start+size):continue
        opname=match.group(2).lower()
        operands=match.group(3).split("//",1)[0].strip()
        if opname in INDIRECT:
            sites.append({"va":hex(va),"instruction":opname,
                          "operand":operands.split()[0].rstrip(",") if operands else None,
                          "preceding":[{"va":hex(a),"opcode":op} for a,op in history],
                          "resolution":"unresolved_indirect_call"})
        history.append((va,opname))
    return sites

def run(elf):
    elf=Path(elf)
    if hashlib.sha256(elf.read_bytes()).hexdigest()!=EXPECTED_SHA:
        raise ValueError("ELF SHA256 mismatch for BarbarQ 1.0.1811 arm64")
    results={}
    for name,(start,size) in RANGES.items():
        proc=subprocess.run(["llvm-objdump","-d",
                             "--start-address="+hex(start),
                             "--stop-address="+hex(start+size),str(elf)],
                            check=True,capture_output=True,text=True,timeout=45)
        results[name]=parse(proc.stdout,start,size)
    return {"phase":46,"library_sha256":EXPECTED_SHA,"sites":results,
            "resolved_virtual_targets":0,
            "limitations":["BLR call targets cannot be inferred from register name alone",
                           "Disassembly windows show opcodes only, not full dataflow",
                           "No evidence yet links indirect calls to basic skill 4010020"],
            "gameplay_enabled":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--elf",required=True,type=Path)
    ap.add_argument("--out",type=Path,default=Path("reports/skill_indirect46.json"))
    args=ap.parse_args()
    result=run(args.elf)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({name:len(sites) for name,sites in result["sites"].items()},indent=2))

if __name__=="__main__":main()
