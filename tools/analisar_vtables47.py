#!/usr/bin/env python3
"""F47: recover candidate vtable entries from original ARM64 ELF relocations.

Only entries with a known vtable symbol, bounded symbol size and a relocation
naming a code symbol are reported. This does not resolve a BLR call site.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SHA="8199604d199b57ebe329725c9a624b85517f495f78c1dad745449684750e4677"
SYMBOL=re.compile(r"^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(.+)$",re.I)
RELOC=re.compile(r"^\s*([0-9a-f]+)\s+[0-9a-f]+\s+(R_AARCH64_[A-Z0-9_]+)\s+([0-9a-f]+)\s+(.+)$",re.I)

def parse_symbols(txt):
    result=[]
    for line in txt.splitlines():
        m=SYMBOL.match(line)
        if m and int(m.group(2))>0:
            result.append({"va":int(m.group(1),16),"size":int(m.group(2)),"name":m.group(3).strip().split(" @",1)[0]})
    return result

def parse_relocations(txt):
    result=[]
    for line in txt.splitlines():
        m=RELOC.match(line)
        if m:
            result.append({"offset":int(m.group(1),16),"type":m.group(2),"symbol":m.group(4).strip()})
    return result

def candidates(symbols, relocations):
    vt=[s for s in symbols if s["name"].startswith("_ZTV") and s["size"]>=8]
    result=[]
    for table in vt:
        entries=[]
        for r in relocations:
            delta=r["offset"]-table["va"]
            if 0<=delta<table["size"] and delta%8==0:
                entries.append({"slot_offset":delta,"relocation_type":r["type"],
                                "referenced_symbol":r["symbol"],
                                "classification":"relocation_reference_not_proven_call_target"})
        if entries:
            result.append({"vtable_symbol":table["name"],"va":hex(table["va"]),
                           "size_bytes":table["size"],"entries":sorted(entries,key=lambda x:x["slot_offset"])})
    return sorted(result,key=lambda x:x["vtable_symbol"])

def audit(elf):
    elf=Path(elf)
    if hashlib.sha256(elf.read_bytes()).hexdigest()!=SHA:
        raise ValueError("Original BarbarQ 1.0.1811 arm64 ELF hash mismatch")
    syms=subprocess.run(["readelf","-Ws",str(elf)],check=True,capture_output=True,text=True,timeout=60)
    rels=subprocess.run(["readelf","-rW",str(elf)],check=True,capture_output=True,text=True,timeout=60)
    tables=candidates(parse_symbols(syms.stdout),parse_relocations(rels.stdout))
    return {"phase":47,"apk_version":"1.0.1811","library_sha256":SHA,
            "vtable_candidates":tables,
            "resolved_blr_calls":0,"skill_4010020_effect_verified":False,
            "limits":["Relocations may be absent for statically linked slots or use relative encodings.",
                      "ELF relocation offsets and symbol VAs must be comparable; check load bias.",
                      "A relocation within a vtable is not proof a BLR reaches that entry.",
                      "Further callsite register dataflow and class attribution required."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elf",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("reports/vtables47.json"))
    args=p.parse_args()
    result=audit(args.elf)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("F47 candidate vtables:",len(result["vtable_candidates"]))

if __name__=="__main__":main()
