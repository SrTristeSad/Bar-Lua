#!/usr/bin/env python3
"""F17: auditoria dos filtros Box2D no ELF ARM64 BarbarQ 1.0.1811.
Não executa biblioteca Android e não redistribui o código nativo.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

FUNCTIONS = [
 ("Entity::setCollidable(bool)",0xe49cb4,132, {
  "body_fixture":r"ldr\s+x0,\s*\[x8,\s*#0x70\]",
  "branch_false":r"tbz\s+w8,\s*#0x0,\s*0xe49d00",
  "calls_filter_api":r"bl\s+[^\n]*b2Fixture13SetFilterData",
  "disabled_category_zero":r"strh\s+wzr,\s*\[sp,\s*#0x10\]",
  "disabled_group_zero":r"strh\s+wzr,\s*\[sp,\s*#0x14\]",
  "disabled_mask_1":r"orr\s+w8,\s*wzr,\s*#0x1[\s\S]*?strh\s+w8,\s*\[sp,\s*#0x12\]",
  "enabled_category_1":r"strh\s+w9,\s*\[sp,\s*#0x8\]",
  "enabled_group_zero":r"strh\s+wzr,\s*\[sp,\s*#0xc\]",
  "enabled_mask_3":r"orr\s+w8,\s*wzr,\s*#0x3[\s\S]*?strh\s+w8,\s*\[sp,\s*#0xa\]",
  "flag_low_bit":r"and\s+w8,\s*w1,\s*#0x1"
 }),
 ("b2ContactFilter::ShouldCollide(b2Fixture*, b2Fixture*)",0x1b72260,88, {
  "both_directions_required":r"tst\s+w8,\s*#0xffff[\s\S]*?cset\s+w0,\s*ne",
  "category_a":r"ldrh\s+w8,\s*\[x1,\s*#0x34\]",
  "category_b":r"ldrh\s+w9,\s*\[x2,\s*#0x34\]",
  "group_compare":r"cmp\s+w10,\s*w9",
  "group_read_a":r"ldrsh\s+w8,\s*\[x1,\s*#0x38\]",
  "group_read_b":r"ldrh\s+w9,\s*\[x2,\s*#0x38\]",
  "mask_a":r"ldrh\s+w8,\s*\[x1,\s*#0x36\]",
  "mask_b":r"ldrh\s+w9,\s*\[x2,\s*#0x36\]",
  "positive_group":r"cset\s+w0,\s*gt"
 }),
 ("b2Fixture::SetFilterData(b2Filter const&)",0x1b6f4d0,184, {
  "copy_category_mask":r"ldr\s+w9,\s*\[x1\][\s\S]*?str\s+w9,\s*\[x19,\s*#0x34\]",
  "read_group":r"ldrh\s+w8,\s*\[x1,\s*#0x4\]",
  "touch_proxies":r"bl\s+[^\n]*b2BroadPhase10TouchProxy",
  "write_group":r"strh\s+w8,\s*\[x19,\s*#0x38\]"
 }),
 ("config::hero::CollisionConfig::load(tms::xconf::DataLine&)",0x18679f8,236, {
  "optional_objects":r"bl\s+[^\n]*Decoder9hasObject",
  "read_shape_type":r"bl\s+[^\n]*Decoder9decodeInt",
  "store_optional_circle":r"str\s+x0,\s*\[x20,\s*#0x10\]",
  "store_optional_custom":r"str\s+x0,\s*\[x20,\s*#0x20\]",
  "store_optional_rect":r"str\s+x0,\s*\[x20,\s*#0x18\]",
  "store_type":r"str\s+w0,\s*\[x20,\s*#0x8\]"
 })
]
INSTR = re.compile(r"^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+([a-z][\w.]*)\b",re.M|re.I)

def audit(so, manifest):
    so,manifest=Path(so),Path(manifest)
    expected=next(x["sha256"] for x in json.loads(manifest.read_text(encoding="utf-8"))["libraries"] if x["name"]=="libcocos2dcpp.so")
    digest=hashlib.sha256(so.read_bytes()).hexdigest()
    if digest!=expected: raise ValueError("SHA-256 divergente")
    lines=subprocess.run(["readelf","-Ws",str(so)],check=True,capture_output=True,text=True,timeout=45).stdout.splitlines()
    symbols={}
    addresses={(va,size) for _,va,size,_ in FUNCTIONS}
    for line in lines:
        fields=line.split()
        if len(fields)>=8 and fields[3]=="FUNC" and fields[6]!="UND":
            va,size=int(fields[1],16),int(fields[2])
            if (va,size) in addresses:
                dem=subprocess.run(["c++filt",fields[7].split("@")[0]],check=True,capture_output=True,text=True,timeout=15).stdout.strip()
                symbols[dem]=(va,size)
    if {k:symbols.get(k) for k,_,_,_ in FUNCTIONS}!={name:(va,size) for name,va,size,_ in FUNCTIONS}:
        raise ValueError("Símbolos/endereço/tamanho divergentes")
    entries=[]
    for name,va,size,checks in FUNCTIONS:
        out=subprocess.run(["llvm-objdump","-d","--demangle",f"--start-address=0x{va:x}",f"--stop-address=0x{va+size:x}",str(so)],
                           check=True,capture_output=True,text=True,timeout=45).stdout
        pcs=[int(m.group(1),16) for m in INSTR.finditer(out)]
        if pcs!=list(range(va,va+size,4)): raise ValueError("Trecho ARM64 incompleto: "+name)
        missing=[key for key,pattern in checks.items() if re.search(pattern,out) is None]
        if missing: raise ValueError("Padrões divergentes: "+name+" "+str(missing))
        entries.append({"name":name,"address":hex(va),"size_bytes":size,"instructions":size//4,"checks":sorted(checks)})
    return {
        "phase":17,"apk_version":"1.0.1811","library_sha256":digest,
        "notes":"Metadados de análise estática: não executa física nem prova contatos em uma partida.",
        "entity_setCollidable":{
            "true":{"categoryBits":1,"maskBits":3,"groupIndex":0},
            "false":{"categoryBits":0,"maskBits":1,"groupIndex":0},
            "fixture_selection":"primeiro fixture do corpo em Entity +0x28 (acesso +0x70 no corpo)",
            "scope":"somente a função auditada: não extrapolar aos demais fixtures ou entidades"
        },
        "filter_rule":{
            "group":"mesmo groupIndex não zero: permitir somente se positivo",
            "masks":"(A.mask & B.category)!=0 e (B.mask & A.category)!=0",
            "result":"decisão de criar contato, não resposta de colisão"
        },
        "functions":entries
    }

def export_lua(r):
    lines=["-- F17: somente catálogo de metadados auditados do ELF.","return {"]
    for f in r["functions"]:
        lines.append(f'  {{name={json.dumps(f["name"],ensure_ascii=False)},address={json.dumps(f["address"])},instructions={f["instructions"]},checks={len(f["checks"])} }},')
    return "\n".join(lines+["}",""])+"\n"

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--so",type=Path,default=Path("lib/arm64-v8a/libcocos2dcpp.so"))
    ap.add_argument("--manifest",type=Path,default=Path("reports/native_arm64.json"))
    ap.add_argument("--out",type=Path,default=Path("reports/native_filters.json"))
    ap.add_argument("--lua",type=Path,default=Path("reports/native_filters.lua"))
    args=ap.parse_args()
    result=audit(args.so,args.manifest)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    args.lua.write_text(export_lua(result),encoding="utf-8")
    print(f'F17: {len(result["functions"])} funções e {sum(f["instructions"] for f in result["functions"])} instruções verificadas')
