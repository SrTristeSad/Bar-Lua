#!/usr/bin/env python3
"""F45: robust, conservative direct-branch xref scanner for BarbarQ ARM64.

Needs original ELF with verified digest and llvm-objdump. Does not claim
virtual BLR resolution or establish the attack 4010020 damage path.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SHA256="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
TARGETS={"Entity::addSkill(skillPtr)":0xe48744,"CSkill::Release":0xe65034,
         "CSelfSkill::HasFunctions":0xe65a90,"CSelfSkill::Update":0xe65924,
         "CSelfSkill::Init":0xe657b0}
HEADER=re.compile(r"^\\s*[0-9a-f]+\\s+<([^>]+)>:\\s*$",re.I)
OP=re.compile(
 r"^\\s*([0-9a-f]+):\\s+(?:(?:[0-9a-f]{8}|(?:[0-9a-f]{2}\\s+){3}[0-9a-f]{2})\\s+)?"
 r"(bl|b)\\s+(?:#?0x)?([0-9a-f]+)(?=\\s|$)",re.I)

def parse(lines):
    result={k:[] for k in TARGETS}
    targets={v:k for k,v in TARGETS.items()}
    caller=None
    for line in lines:
        h=HEADER.match(line)
        if h:
            caller=h.group(1)
            continue
        m=OP.match(line)
        if not m:continue
        va=int(m.group(1),16)
        dest=int(m.group(3),16)
        if dest in targets:
            result[targets[dest]].append({
                "caller":caller,"instruction_va":hex(va),"branch":m.group(2).lower()})
    return result

def scan(elf):
    if hashlib.sha256(Path(elf).read_bytes()).hexdigest()!=SHA256:
        raise ValueError("ELF hash mismatch: expected original BarbarQ 1.0.1811 arm64")
    process=subprocess.run(["llvm-objdump","-d",str(elf)],check=True,
                           capture_output=True,text=True,timeout=240)
    result=parse(process.stdout.splitlines())
    return {"phase":45,"elf_sha256":SHA256,"direct_branches":result,
            "unresolved":["indirect BLR calls","calls through vtables",
                          "per-skill dispatch for 4010020","attack animation and damage linkage"],
            "gameplay_enabled":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--elf",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("reports/skill_xrefs45.json"))
    args=ap.parse_args()
    result=scan(args.elf)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps({name:len(entries) for name,entries
                      in result["direct_branches"].items()},indent=2))
if __name__=="__main__":main()
