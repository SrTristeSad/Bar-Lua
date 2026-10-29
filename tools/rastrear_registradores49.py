#!/usr/bin/env python3
"""F49: conservative local ARM64 BLR register provenance analysis.

Recognizes a contiguous LDR vptr -> LDR method-slot -> BLR chain.
Reports a slot offset, never a concrete target/class. Rejects register clobbers,
branch boundaries and ambiguous sequences. Requires original matching ELF.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SHA="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
RANGES={"CSelfSkill::CSelfSkill":(0xe6555c,596),
        "CSelfSkill::Init":(0xe657b0,372),
        "CSelfSkill::Update":(0xe65924,364),
        "Entity::addSkill(skillPtr)":(0xe48744,552)}
INS=re.compile(r"^\s*([0-9a-f]+):\s+(?:(?:[0-9a-f]{8}|(?:[0-9a-f]{2}\s+){3}[0-9a-f]{2})\s+)?([a-z][\w.]*)\s*(.*?)\s*$",re.I)
LOAD=re.compile(r"^(x\d+),\s*\[(x\d+)(?:,\s*#?(0x[0-9a-f]+|\d+))?\]$",re.I)
CALL=re.compile(r"^(x\d+)\b",re.I)
BARRIERS={"ret","br","b","bl","blr","cbz","cbnz","tbz","tbnz"}
def records(text):
    return [(int(m[1],16),m[2].lower(),m[3].split("//",1)[0].strip())
            for line in text.splitlines() if (m:=INS.match(line))]
def identify(rows):
    result=[]
    for idx,(address,op,args) in enumerate(rows):
        if op!="blr":continue
        call=CALL.match(args)
        if not call:continue
        reg=call[1].lower()
        prev=rows[max(0,idx-8):idx]
        if not prev:continue
        if any(x[1] in BARRIERS or x[1].startswith("b.") for x in prev):continue
        # A deliberately narrow pattern: immediately preceding instructions
        # must load method pointer and then vptr. No assumed alias analysis.
        if len(prev)<2 or prev[-1][1]!="ldr" or prev[-2][1]!="ldr":continue
        meth=LOAD.match(prev[-1][2])
        vptr=LOAD.match(prev[-2][2])
        if not meth or not vptr:continue
        dst,base,offset=meth.groups()
        vdst,receiver,receiver_offset=vptr.groups()
        if dst.lower()!=reg or base.lower()!=vdst.lower():continue
        if receiver_offset not in (None,"0","0x0"):continue
        slot=int(offset or "0",0)
        if slot%8:continue
        result.append({"callsite_va":hex(address),"receiver_register":receiver.lower(),
                       "vptr_register":vdst.lower(),"target_register":reg,
                       "slot_offset":slot,"classification":"local_load_pattern_only",
                       "resolved_target":None})
    return result
def scan(elf):
    if hashlib.sha256(Path(elf).read_bytes()).hexdigest()!=SHA:
        raise ValueError("Original ELF hash mismatch")
    data={}
    for name,(va,size) in RANGES.items():
        res=subprocess.run(["llvm-objdump","-d","--start-address="+hex(va),
                            "--stop-address="+hex(va+size),str(elf)],check=True,
                           capture_output=True,text=True,timeout=60)
        data[name]=identify(records(res.stdout))
    return {"phase":49,"elf_sha256":SHA,"candidate_local_patterns":data,
            "confirmed_virtual_targets":0,"gameplay_enabled":False,
            "limits":["Only adjacent LDR-LDR-BLR idiom is recognized.",
                      "Receiver's dynamic class remains unidentified.",
                      "A vtable slot offset is not proof of destination.",
                      "No link to damage or animation for 4010020 is established."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elf",required=True,type=Path)
    p.add_argument("--out",type=Path,default=Path("reports/register_provenance49.json"))
    a=p.parse_args()
    result=scan(a.elf)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print({k:len(v) for k,v in result["candidate_local_patterns"].items()})
if __name__=="__main__":main()
