#!/usr/bin/env python3
"""F48: correlate F46 indirect call sites with F47 vtable candidates.

Produces research work queues, NOT resolved virtual calls. Matching a slot
offset without register provenance or receiver type is insufficient evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EXPECTED_SHA="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
def validate(f46,f47):
    if f46.get("phase")!=46 or f47.get("phase")!=47:
        raise ValueError("Expected reports from phases 46 and 47")
    if f46.get("library_sha256")!=EXPECTED_SHA or f47.get("library_sha256")!=EXPECTED_SHA:
        raise ValueError("Input reports do not share verified original ELF digest")
    if not isinstance(f46.get("sites"),dict) or not isinstance(f47.get("vtable_candidates"),list):
        raise ValueError("Incomplete input reports")

def correlate(f46,f47):
    validate(f46,f47)
    tables=f47["vtable_candidates"]
    work=[]
    for routine,sites in sorted(f46["sites"].items()):
        for site in sites:
            if site.get("resolution")!="unresolved_indirect_call":
                raise ValueError("Unexpected F46 call resolution")
            # No guessed vtable class or slot: the F46 report stores only opcode
            # and register, not the dataflow needed to link these entries.
            work.append({
                "routine":routine,"callsite_va":site["va"],
                "register":site.get("operand"),
                "classification":"indirect_call_requires_provenance",
                "vtable_symbol":None,"slot_offset":None,"destination_symbol":None,
                "next_evidence":["full disassembly operands and reaching register definition",
                                 "receiver dynamic type or vptr initialization",
                                 "exact table slot offset for indirect load"]
            })
    return {
        "phase":48,"apk_version":"1.0.1811","library_sha256":EXPECTED_SHA,
        "indirect_sites":len(work),"candidate_vtables":len(tables),
        "candidate_relocation_entries":sum(len(t["entries"]) for t in tables),
        "confirmed_virtual_edges":0,"work_queue":work,
        "scope_note":"Cross-referenced inventories only; no virtual dispatch edges are established.",
        "gameplay_enabled":False,"damage_chain_verified":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--calls",type=Path,default=Path("reports/skill_indirect46.json"))
    p.add_argument("--vtables",type=Path,default=Path("reports/vtables47.json"))
    p.add_argument("--out",type=Path,default=Path("reports/skill_dispatch48.json"))
    a=p.parse_args()
    result=correlate(json.loads(a.calls.read_text(encoding="utf-8")),
                     json.loads(a.vtables.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"F48: {result['indirect_sites']} indirect sites; {result['confirmed_virtual_edges']} confirmed edges")

if __name__=="__main__":main()
